"""Render TikTokLive/events/proto_events.py from events.yaml + TikTokLiveProto.v2.

This is a pure spec-driven generator: it does NOT read the existing
proto_events.py. The YAML is the only source of customizations; the v2 proto
package is the only source of message classes. Output is fully reproducible.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Type, get_type_hints

import betterproto
import jinja2
import yaml

from TikTokLiveProto.v2 import CommonMessageData
import TikTokLiveProto.v2 as v2


logger = logging.getLogger("transcribe")
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
    f = message_cls.__dataclass_fields__.get(field_name)
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
        for fname, dfield in obj.__dataclass_fields__.items():
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
            "events.yaml references proto messages not present in TikTokLiveProto.v2:\n  - "
            + "\n  - ".join(sorted(yaml_only))
        )

    return discovered


def render(events: List[EventClass], template_path: Path) -> str:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_path.parent)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    template = env.get_template(template_path.name)
    return template.render(events=events)


def load_spec(spec_path: Path) -> dict:
    with open(spec_path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}
