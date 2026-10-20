#!/usr/bin/env python3
"""Generate the GitHub Pages redirect shell for the old Sphinx docs.

The documentation moved from ``https://isaackogan.github.io/TikTokLive/`` to
``https://ttl.docs.isaackogan.com/``. GitHub Pages stays on but serves only the
small pages this script writes, so every old URL forwards to its new equivalent:

- one page per entry in ``REDIRECT_MAP`` (every page the Sphinx site had);
- ``404.html``, which GitHub Pages serves for any unknown path (old ``_static/...``,
  ``search.html?q=...``) and which forwards to the new site's root;
- ``.nojekyll`` so Pages serves the files verbatim;
- ``google93ecefd594fb7167.html``, the Search Console verification file, copied
  from ``docs/public/`` so the old property stays verified.

Usage: ``python docs/scripts/gen_redirects.py docs/redirects``. The output
directory is wiped and recreated.
"""

from __future__ import annotations

import html
import shutil
import sys
from pathlib import Path

NEW_BASE = "https://ttl.docs.isaackogan.com/"

# Old Sphinx page -> path under NEW_BASE.
REDIRECT_MAP: dict[str, str] = {
    "index.html": "",
    "TikTokLive.html": "api/",
    "modules.html": "api/",
    "TikTokLive.client.html": "api/tiktoklive/client/",
    "TikTokLive.client.web.html": "api/tiktoklive/client/web/",
    "TikTokLive.client.web.routes.html": "api/tiktoklive/client/web/routes/",
    "TikTokLive.client.ws.html": "api/tiktoklive/client/ws/",
    "TikTokLive.events.html": "events/",
    "TikTokLive.proto.html": "schema/",
    "genindex.html": "api/",
    "py-modindex.html": "api/",
    "search.html": "",
}

VERIFICATION_FILE = "google93ecefd594fb7167.html"
PUBLIC_DIR = Path(__file__).resolve().parent.parent / "public"


def redirect_page(target: str) -> str:
    """Return a minimal HTML page that forwards to ``target`` and is never indexed."""
    href = html.escape(target, quote=True)
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f'<meta http-equiv="refresh" content="0; url={href}">\n'
        f'<link rel="canonical" href="{href}">\n'
        '<meta name="robots" content="noindex">\n'
        "<title>TikTokLive documentation has moved</title>\n"
        "</head>\n"
        "<body>\n"
        f'<p>The TikTokLive documentation has moved to <a href="{href}">{href}</a>.</p>\n'
        "</body>\n"
        "</html>\n"
    )


def main(out_dir: str) -> int:
    out = Path(out_dir).resolve()
    if out in Path(__file__).resolve().parents:
        print(f"refusing to wipe {out}: it contains this script", file=sys.stderr)
        return 2

    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    for old, new in REDIRECT_MAP.items():
        (out / old).write_text(redirect_page(NEW_BASE + new), encoding="utf-8")
    (out / "404.html").write_text(redirect_page(NEW_BASE), encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    shutil.copyfile(PUBLIC_DIR / VERIFICATION_FILE, out / VERIFICATION_FILE)

    print(f"Wrote {len(REDIRECT_MAP) + 1} redirect pages to {out}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} OUT_DIR", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
