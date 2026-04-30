"""Render TikTokLive/events/proto_events.py from events.yaml + TikTokLiveProto.v3.

Pure spec-driven generator: input is (events.yaml, TikTokLiveProto.v3), output
is proto_events.py. Does not read the existing proto_events.py — drift between
the spec and what's checked in is therefore impossible.

Same shape as ``gen_aliases.py`` so the proto pipeline has one consistent
entrypoint pattern.
"""

from __future__ import annotations

import argparse
import collections
import dataclasses
import importlib
import logging
import pkgutil
import sys
import types
import typing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Type, Union, get_args, get_origin, get_type_hints

import betterproto2
import jinja2
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
EVENTS_YAML = SCRIPT_DIR / "resources" / "events.yaml"
TEMPLATE_DIR = SCRIPT_DIR / "templates"
TEMPLATE_NAME = "events.py.j2"
OUTPUT_PATH = REPO_ROOT / "TikTokLive" / "events" / "proto_events.py"

# events.yaml validation imports from TikTokLiveProto, not the in-repo
# TikTokLive package, so we don't need to put REPO_ROOT on sys.path here. We
# do so only to keep parity with gen_aliases.py and tolerate future refs.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import TikTokLiveProto.v3 as v3  # noqa: E402
from TikTokLiveProto.v3.webcast.shared.message import CommonMessageData  # noqa: E402


logger = logging.getLogger("gen-events")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="[%(name)s] %(levelname)s — %(message)s")


@dataclass
class EventClass:
    """Resolved event-class spec ready to hand to the jinja template."""

    proto_name: str
    class_name: str
    module_path: str
    annotations: Dict[str, str] = field(default_factory=dict)
    fields: Dict[str, Dict[str, str]] = field(default_factory=dict)
    properties: List[Dict[str, str]] = field(default_factory=list)
    # Explicit field re-declarations so static analyzers (PyCharm in
    # particular) can see every inherited proto field on the generated
    # subclass. Maps field-name → resolved type string (e.g. ``"Optional[User]"``).
    inherited_fields: Dict[str, str] = field(default_factory=dict)


# ``typing`` constructs that need to be importable from the generated module
# regardless of which event references them. Always imported.
_BUILTIN_TYPING_NAMES = {"Optional", "List", "Dict", "Union", "Any", "Tuple"}


def _stringify_type(tp: Any, imports: Set[Tuple[str, str]]) -> str:
    """Render a Python type as a source-code annotation string.

    Mutates ``imports`` to record every (module, name) pair the rendered
    string references, so the generator can emit a deterministic import
    block at the top of the output module.

    Forward refs are dereferenced via ``get_type_hints`` upstream of this
    helper, so by the time we get here, ``tp`` is a real Python object
    (a class, a typing alias, or a ``types.UnionType``).
    """

    # ``None`` itself doesn't appear inside a Union — ``NoneType`` does.
    if tp is type(None):
        return "None"

    origin = get_origin(tp)
    args = get_args(tp)

    # Optional[X] / Union[...] — both ``typing.Union`` and the PEP 604 ``X | Y``
    # form (``types.UnionType``) need to be handled.
    if origin is Union or origin is types.UnionType:
        non_none = [a for a in args if a is not type(None)]
        has_none = len(non_none) != len(args)
        rendered = [_stringify_type(a, imports) for a in non_none]
        if has_none and len(rendered) == 1:
            return f"Optional[{rendered[0]}]"
        if has_none:
            return f"Optional[Union[{', '.join(rendered)}]]"
        return f"Union[{', '.join(rendered)}]"

    if origin is list or tp is list:
        if not args:
            return "list"
        return f"List[{_stringify_type(args[0], imports)}]"

    if origin is dict or tp is dict:
        if not args:
            return "dict"
        k = _stringify_type(args[0], imports)
        v = _stringify_type(args[1], imports)
        return f"Dict[{k}, {v}]"

    if origin is tuple or tp is tuple:
        if not args:
            return "tuple"
        return f"Tuple[{', '.join(_stringify_type(a, imports) for a in args)}]"

    # Plain class.
    if isinstance(tp, type):
        module = tp.__module__
        name = tp.__name__
        if module == "builtins":
            return name
        imports.add((module, name))
        return name

    # Fallback (Any, ParamSpec, weird typing constructs).
    return "Any"


def _collect_inherited_fields(
    parent_cls: Type[betterproto2.Message],
    field_type_overrides: Dict[str, str],
    imports: Set[Tuple[str, str]],
) -> Dict[str, str]:
    """For one event's parent message, render every dataclass field as an
    annotation string. Applies the YAML ``field_type_overrides`` map
    (e.g. ``User`` → ``ExtendedUser``) only to direct/Optional references —
    not inside invariant containers like ``List[User]`` (where substituting
    a subclass would create a Liskov violation that mypy correctly rejects).

    Imports for any class encountered are accumulated into ``imports``.
    """

    rendered: Dict[str, str] = {}
    # ``include_extras=False`` strips ``typing.Annotated[..., ...]`` validators
    # so the resulting string is the bare type the IDE actually wants.
    hints = get_type_hints(parent_cls, include_extras=False)
    for f in dataclasses.fields(parent_cls):  # type: ignore[arg-type]
        hint = hints.get(f.name)
        if hint is None:
            continue
        type_str = _stringify_type(hint, imports)
        # Only substitute when the type is the bare class or Optional[Class].
        # ``List[User]`` keeps the original type because Python lists are
        # invariant, so ``List[ExtendedUser]`` is *not* a subtype of
        # ``List[User]`` — the override would create a Liskov violation.
        if "List[" not in type_str and "Dict[" not in type_str and "Tuple[" not in type_str:
            for original, replacement in field_type_overrides.items():
                type_str = _re_replace_identifier(type_str, original, replacement)
        rendered[f.name] = type_str
    return rendered


def _re_replace_identifier(text: str, old: str, new: str) -> str:
    """Replace ``old`` with ``new`` only when it appears as a whole identifier."""
    import re
    return re.sub(rf"\b{re.escape(old)}\b", new, text)


def is_proto_event(name: str, instance: Type[object]) -> bool:
    """A v3 message qualifies as an event when it embeds CommonMessageData."""
    try:
        if not issubclass(instance, betterproto2.Message):
            return False
    except TypeError:
        return False
    if not name.startswith("Webcast"):
        return False

    # betterproto2 fields are annotated as ``CommonMessageData | None``
    # (proto3 implicit-optional). Unwrap the union before testing.
    common_hint = get_type_hints(instance).get("common")
    if common_hint is None:
        return False
    candidates = [t for t in get_args(common_hint) if isinstance(t, type)] or (
        [common_hint] if isinstance(common_hint, type) else []
    )
    return any(issubclass(t, CommonMessageData) for t in candidates)


def iter_v3_messages() -> Iterator[Tuple[str, str, Type[betterproto2.Message]]]:
    """Walk every v3 submodule and yield (proto_name, module_path, cls).

    v3's top-level ``__init__.py`` is empty — generated message classes live
    in nested submodules under ``webcast/``. Recurse with ``pkgutil`` so new
    upstream submodules are picked up without code changes here.
    """
    seen: set[Tuple[str, str]] = set()
    for info in pkgutil.walk_packages(v3.__path__, v3.__name__ + "."):
        try:
            mod = importlib.import_module(info.name)
        except Exception:  # pragma: no cover - surface upstream import bugs loudly
            logger.exception("failed to import %s", info.name)
            raise
        for attr_name, obj in vars(mod).items():
            if not isinstance(obj, type):
                continue
            # The same class may be re-exported from multiple modules; key on
            # (defining-module, name) so we only emit each class once.
            key = (getattr(obj, "__module__", info.name), attr_name)
            if key in seen:
                continue
            seen.add(key)
            yield attr_name, info.name, obj


def default_event_name(proto_name: str) -> str:
    """``WebcastFooMessage`` → ``FooEvent``; otherwise strip ``Webcast`` and append ``Event``."""
    if proto_name.endswith("Message"):
        return proto_name.removeprefix("Webcast").removesuffix("Message") + "Event"
    return proto_name.removeprefix("Webcast") + "Event"


def _proto_field_type(message_cls: Type[betterproto2.Message], field_name: str) -> Optional[str]:
    """Return the proto type-name for a betterproto field, or None."""
    # ``betterproto2.Message`` subclasses are all ``@dataclass``-decorated by
    # the generated code, but mypy can't see the decorator on the parent so
    # rejects the call. Safe at runtime.
    fields = {f.name: f for f in dataclasses.fields(message_cls)}  # type: ignore[arg-type]
    f = fields.get(field_name)
    if f is None:
        return None
    # ``f.type`` is the python source string (e.g. ``"User"`` or ``List["User"]``).
    return str(f.type).strip("\"' ")


def discover_events(spec: dict, type_imports: Set[Tuple[str, str]]) -> List[EventClass]:
    """Walk v3 once, materialise an EventClass per qualifying message.

    ``type_imports`` is mutated in place to collect every (module, name) pair
    referenced by the resolved field types, so the renderer can emit the
    matching import block.
    """

    field_type_overrides: Dict[str, str] = spec.get("field_type_overrides", {}) or {}
    per_event: Dict[str, dict] = spec.get("events", {}) or {}

    discovered: List[EventClass] = []

    for proto_name, module_path, obj in iter_v3_messages():
        if not is_proto_event(proto_name, obj):
            continue

        cfg = per_event.get(proto_name, {}) or {}
        class_name = cfg.get("name") or default_event_name(proto_name)

        # Auto-substitute annotations on every field whose proto type matches
        # the override map (e.g. ``user: User`` → ``user: ExtendedUser``).
        # These run at *runtime* (outside TYPE_CHECKING) so betterproto2's
        # ``_cls_for(field)`` picks up the override and constructs the wrapper
        # class at parse time, not the bare upstream class.
        #
        # v3's forward refs are module-aliased (``_base__user__.User | None``),
        # so we resolve via ``get_type_hints`` and look at the actual class
        # name rather than parsing the raw annotation string.
        resolved_hints = get_type_hints(obj, include_extras=False)
        annotations: Dict[str, str] = {}
        for f in dataclasses.fields(obj):  # type: ignore[arg-type]
            hint = resolved_hints.get(f.name)
            if hint is None:
                continue
            # Strip Optional[X] / Union[X, None] to find the inner class.
            inner = hint
            if get_origin(inner) is Union or get_origin(inner) is types.UnionType:
                non_none = [a for a in get_args(inner) if a is not type(None)]
                if len(non_none) == 1:
                    inner = non_none[0]
            # Skip containers — substituting inside ``List[User]`` would create
            # a Liskov violation (lists are invariant).
            if get_origin(inner) in (list, dict, tuple):
                continue
            if isinstance(inner, type) and inner.__name__ in field_type_overrides:
                # Wrap with Optional[...] to match the parent's nullability.
                replacement = field_type_overrides[inner.__name__]
                if hint is not inner:
                    annotations[f.name] = f"Optional[{replacement}]"
                else:
                    annotations[f.name] = replacement

        # Resolve every parent field's type and emit explicit annotations on
        # the subclass so static analyzers (PyCharm in particular) can see the
        # fields without traversing the betterproto2/pydantic dataclass chain.
        inherited_fields = _collect_inherited_fields(obj, field_type_overrides, type_imports)

        ev = EventClass(
            proto_name=proto_name,
            class_name=class_name,
            module_path=module_path,
            annotations=annotations,
            fields=cfg.get("fields", {}) or {},
            properties=[
                {
                    "name": p["name"],
                    "return_type": p["return_type"],
                    "doc": (p.get("doc") or "").strip(),
                    "body": p["body"].rstrip(),
                }
                for p in (cfg.get("properties") or [])
            ],
            inherited_fields=inherited_fields,
        )
        discovered.append(ev)

    discovered.sort(key=lambda e: e.class_name)

    # Validate: every YAML-listed proto message must actually exist in v3,
    # otherwise the spec is stale and we want to know loudly.
    yaml_only = set(per_event) - {e.proto_name for e in discovered}
    if yaml_only:
        raise SystemExit(
            "events.yaml references proto messages not present in TikTokLiveProto.v3:\n  - "
            + "\n  - ".join(sorted(yaml_only))
        )

    return discovered


def _events_by_module(events: List[EventClass]) -> List[Tuple[str, List[str]]]:
    """Group event proto-names by source module for the import block.

    Returns a list of ``(module_path, sorted_proto_names)`` tuples, ordered by
    module path so the generated imports are deterministic.
    """
    grouped: Dict[str, List[str]] = {}
    for ev in events:
        grouped.setdefault(ev.module_path, []).append(ev.proto_name)
    return [(mod, sorted(set(names))) for mod, names in sorted(grouped.items())]


def _aggregate_type_imports(
    type_imports: Set[Tuple[str, str]],
    events_by_module: List[Tuple[str, List[str]]],
    collisions: Dict[str, str],
) -> List[Tuple[str, List[Tuple[str, Optional[str]]]]]:
    """Group (module, name) pairs by module for deterministic import rendering.

    Each rendered entry is ``(name, alias)`` where ``alias`` is ``None`` for
    the common case and ``"_proto_<name>"`` when a v3 type-name collides with
    a generated event class (e.g. v3's ``BarrageEvent`` field type vs our
    ``BarrageEvent`` subclass).

    Skips the ``ExtendedUser`` / ``ExtendedGift`` shims (handled by a hand-written
    import in the template) and the parent message classes (already imported via
    ``events_by_module`` so the subclass declaration resolves).
    """
    parent_imports = {(mod, name) for mod, names in events_by_module for name in names}
    grouped: Dict[str, List[Tuple[str, Optional[str]]]] = collections.defaultdict(list)
    for mod, name in type_imports:
        if name in {"ExtendedUser", "ExtendedGift"}:
            continue
        if (mod, name) in parent_imports:
            continue
        alias = collisions.get(name)
        grouped[mod].append((name, alias))
    return [(m, sorted(set(items))) for m, items in sorted(grouped.items())]


def _resolve_collisions(
    events: List[EventClass],
    type_imports: Set[Tuple[str, str]],
    events_by_module: List[Tuple[str, List[str]]],
) -> Dict[str, str]:
    """Find type names that collide with generated event class names and
    return ``{original_name: aliased_name}`` for the renderer.
    """
    event_class_names = {ev.class_name for ev in events}
    parent_names = {name for _, names in events_by_module for name in names}
    collisions: Dict[str, str] = {}
    for _mod, name in type_imports:
        # Parent classes are already imported by their real name; don't alias.
        if name in parent_names:
            continue
        if name in event_class_names:
            collisions[name] = f"_proto_{name}_"
    return collisions


def _apply_collisions_to_annotations(
    events: List[EventClass],
    collisions: Dict[str, str],
) -> None:
    """Rewrite each event's inherited-field annotations so colliding type
    names use the aliased import.
    """
    if not collisions:
        return
    import re
    for ev in events:
        for fname, annotation in list(ev.inherited_fields.items()):
            new = annotation
            for old, alias in collisions.items():
                new = re.sub(rf"\b{re.escape(old)}\b", alias, new)
            ev.inherited_fields[fname] = new


def render(events: List[EventClass], type_imports: Set[Tuple[str, str]]) -> str:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    events_by_module = _events_by_module(events)
    collisions = _resolve_collisions(events, type_imports, events_by_module)
    _apply_collisions_to_annotations(events, collisions)
    return env.get_template(TEMPLATE_NAME).render(
        events=events,
        events_by_module=events_by_module,
        type_imports_by_module=_aggregate_type_imports(type_imports, events_by_module, collisions),
    )


def load_spec() -> dict:
    with open(EVENTS_YAML, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the generated file is up to date; exit 1 if stale.",
    )
    args = parser.parse_args()

    spec = load_spec()
    type_imports: Set[Tuple[str, str]] = set()
    events = discover_events(spec, type_imports)
    rendered = render(events, type_imports)

    logger.info("Generated %d events from %s", len(events), EVENTS_YAML.name)

    if args.check:
        existing = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        if existing != rendered:
            print(f"{OUTPUT_PATH} is stale. Run scripts/proto/gen_events.py.", file=sys.stderr)
            return 1
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    logger.info("Wrote %s", OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
