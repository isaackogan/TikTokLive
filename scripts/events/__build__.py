"""Regenerate TikTokLive/events/proto_events.py from scripts/events/events.yaml.

The generator is pure: input is (events.yaml, TikTokLiveProto.v2), output is
proto_events.py. It does not read the previous proto_events.py — drift between
the spec and what's checked in is therefore impossible.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from transcribe import discover_events, load_spec, render


logger = logging.getLogger("events-build")
logging.basicConfig(level=logging.INFO, format="[%(name)s] %(levelname)s — %(message)s")


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
SPEC_PATH = SCRIPT_DIR / "events.yaml"
TEMPLATE_PATH = SCRIPT_DIR / "events_template.jinja2"
OUTPUT_PATH = REPO_ROOT / "TikTokLive" / "events" / "proto_events.py"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify the generated file is up to date; exit 1 if stale.",
    )
    args = parser.parse_args()

    spec = load_spec(SPEC_PATH)
    events = discover_events(spec)
    rendered = render(events, TEMPLATE_PATH)

    logger.info("Generated %d events from %s", len(events), SPEC_PATH.name)

    if args.check:
        existing = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        if existing != rendered:
            print(f"{OUTPUT_PATH} is stale. Run scripts/events/__build__.py.", file=sys.stderr)
            return 1
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    logger.info("Wrote %s", OUTPUT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
