"""Render TikTokLive/proto/_aliases.py from scripts/proto/aliases.yaml.

Two kinds of aliases live in the same spec:

* ``module_aliases``  — top-level renames. Validates the new module/name pair
  resolves at generation time.
* ``legacy_aliases``  — class-attribute renames. Validates the class exists and
  that every alias target is a real field on the class.

Both fail loudly if a target is missing so an upstream schema change can't
silently degrade to runtime AttributeError.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import jinja2
import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
ALIASES_YAML = SCRIPT_DIR / "resources" / "aliases.yaml"
TEMPLATE_DIR = SCRIPT_DIR / "templates"
TEMPLATE_NAME = "aliases.py.j2"
OUTPUT_PATH = REPO_ROOT / "TikTokLive" / "proto" / "_aliases.py"

# legacy_aliases targets refer to in-repo modules (e.g. TikTokLive.proto.custom_proto),
# so make the project importable regardless of the caller's CWD or PYTHONPATH.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass
class LegacyClass:
    """One class-level alias group, ready for the template."""

    name: str
    module: str
    properties: Dict[str, Dict[str, str]] = field(default_factory=dict)


def load_spec() -> dict:
    with open(ALIASES_YAML, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def validate_module_aliases(module_aliases: dict) -> None:
    missing: list[str] = []
    for old, target in module_aliases.items():
        mod = importlib.import_module(target["module"])
        if not hasattr(mod, target["name"]):
            missing.append(f"{old} -> {target['module']}.{target['name']}")
    if missing:
        raise SystemExit(
            "module_aliases targets missing in upstream package:\n  - "
            + "\n  - ".join(missing)
        )


def validate_legacy_aliases(legacy_aliases: List[LegacyClass]) -> None:
    missing: list[str] = []
    for cls_spec in legacy_aliases:
        mod = importlib.import_module(cls_spec.module)
        cls = getattr(mod, cls_spec.name, None)
        if cls is None:
            missing.append(f"class {cls_spec.module}.{cls_spec.name} not found")
            continue
        # We're attaching read-only properties whose target must be either a
        # dataclass field on the class or any attribute reachable via getattr
        # on an instance. Instantiating betterproto messages is cheap, so we
        # do that rather than poking at __dataclass_fields__ which misses
        # inherited proto fields.
        try:
            inst = cls()
        except Exception:
            inst = None
        for legacy_name, spec in cls_spec.properties.items():
            target = spec["target"]
            ok = (
                target in getattr(cls, "__dataclass_fields__", {})
                or (inst is not None and hasattr(inst, target))
                or hasattr(cls, target)
            )
            if not ok:
                missing.append(
                    f"{cls_spec.module}.{cls_spec.name}.{legacy_name} -> {target} (no such field)"
                )
    if missing:
        raise SystemExit(
            "legacy_aliases targets missing on classes:\n  - " + "\n  - ".join(missing)
        )


def render(module_aliases: dict, legacy_aliases: List[LegacyClass]) -> str:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env.get_template(TEMPLATE_NAME).render(
        module_aliases=module_aliases,
        legacy_aliases=legacy_aliases,
    )


def parse_legacy(raw: dict) -> List[LegacyClass]:
    out: List[LegacyClass] = []
    for class_name, body in (raw or {}).items():
        out.append(
            LegacyClass(
                name=class_name,
                module=body["module"],
                properties=body.get("properties", {}) or {},
            )
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the generated file is up to date; exit 1 if stale.",
    )
    args = parser.parse_args()

    spec = load_spec()
    module_aliases = spec.get("module_aliases", {}) or {}
    legacy_aliases = parse_legacy(spec.get("legacy_aliases", {}) or {})

    validate_module_aliases(module_aliases)
    validate_legacy_aliases(legacy_aliases)

    rendered = render(module_aliases, legacy_aliases)

    if args.check:
        existing = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        if existing != rendered:
            print(f"{OUTPUT_PATH} is stale. Run scripts/proto/gen_aliases.py.", file=sys.stderr)
            return 1
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(
        f"Wrote {OUTPUT_PATH} "
        f"({len(module_aliases)} module aliases, "
        f"{sum(len(c.properties) for c in legacy_aliases)} legacy property aliases)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
