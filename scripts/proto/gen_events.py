"""Render TikTokLive/events/proto_events.py from events.yaml + TikTokLiveProto.generated.v2.

Pure spec-driven generator: input is (events.yaml, TikTokLiveProto.generated.v2), output
is proto_events.py. Does not read the existing proto_events.py — drift between
the spec and what's checked in is therefore impossible.

Same shape as ``gen_aliases.py`` so the proto pipeline has one consistent
entrypoint pattern.
"""

from __future__ import annotations

import argparse
import dataclasses
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Type, get_type_hints

import betterproto
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

from TikTokLiveProto.generated.v2 import CommonMessageData  # noqa: E402
import TikTokLiveProto.generated.v2 as v2  # noqa: E402


logger = logging.getLogger("gen-events")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="[%(name)s] %(levelname)s — %(message)s")


@dataclass
class EventClass:
    """Resolved event-class spec ready to hand to the jinja template."""

    proto_name: str
    class_name: str
    annotations: Dict[str, str] = field(default_factory=dict)
    fields: Dict[str, Dict[str, str]] = field(default_factory=dict)
    properties: List[Dict[str, str]] = field(default_factory=list)


def is_proto_event(name: str, instance: Type[object]) -> bool:
    """A v2 message qualifies as an event when it embeds CommonMessageData."""
    try:
        if not issubclass(instance, betterproto.Message):
            return False
    except TypeError:
        return False
    if not name.startswith("Webcast"):
        return False
    common_hint = get_type_hints(instance).get("common")
    if not common_hint:
        return False
    return issubclass(common_hint, CommonMessageData)


def default_event_name(proto_name: str) -> str:
    """``WebcastFooMessage`` → ``FooEvent``; otherwise strip ``Webcast`` and append ``Event``."""
    if proto_name.endswith("Message"):
        return proto_name.removeprefix("Webcast").removesuffix("Message") + "Event"
    return proto_name.removeprefix("Webcast") + "Event"


def _proto_field_type(message_cls: Type[betterproto.Message], field_name: str) -> Optional[str]:
    """Return the proto type-name for a betterproto field, or None."""
    # ``betterproto.Message`` subclasses are all ``@dataclass``-decorated by
    # the generated code, but mypy can't see the decorator on the parent so
    # rejects the call. Safe at runtime.
    fields = {f.name: f for f in dataclasses.fields(message_cls)}  # type: ignore[arg-type]
    f = fields.get(field_name)
    if f is None:
        return None
    # ``f.type`` is the python source string (e.g. ``"User"`` or ``List["User"]``).
    return str(f.type).strip("\"' ")


def discover_events(spec: dict) -> List[EventClass]:
    """Walk v2 once, materialise an EventClass per qualifying message."""

    field_type_overrides: Dict[str, str] = spec.get("field_type_overrides", {}) or {}
    per_event: Dict[str, dict] = spec.get("events", {}) or {}

    discovered: List[EventClass] = []

    for proto_name, obj in vars(v2).items():
        if not is_proto_event(proto_name, obj):
            continue

        cfg = per_event.get(proto_name, {}) or {}
        class_name = cfg.get("name") or default_event_name(proto_name)

        # Auto-substitute annotations on every field whose proto type matches
        # the override map (e.g. ``user: User`` → ``user: ExtendedUser``).
        annotations: Dict[str, str] = {}
        for fname in obj.__dataclass_fields__:
            ftype = _proto_field_type(obj, fname)
            if ftype and ftype in field_type_overrides:
                annotations[fname] = field_type_overrides[ftype]

        ev = EventClass(
            proto_name=proto_name,
            class_name=class_name,
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
        )
        discovered.append(ev)

    discovered.sort(key=lambda e: e.class_name)

    # Validate: every YAML-listed proto message must actually exist in v2,
    # otherwise the spec is stale and we want to know loudly.
    yaml_only = set(per_event) - {e.proto_name for e in discovered}
    if yaml_only:
        raise SystemExit(
            "events.yaml references proto messages not present in TikTokLiveProto.generated.v2:\n  - "
            + "\n  - ".join(sorted(yaml_only))
        )

    return discovered


def render(events: List[EventClass]) -> str:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env.get_template(TEMPLATE_NAME).render(events=events)


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
    events = discover_events(spec)
    rendered = render(events)

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
