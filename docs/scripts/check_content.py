#!/usr/bin/env python3
"""Fail the docs build when the authored pages drift from the code.

Runs first in ``pnpm --dir docs build``. The code surface is read statically with ``ast``
(nothing is imported) and compared with the authored Markdown under
``docs/src/content/docs/``; the generated ``api/`` and ``schema/`` trees are skipped.
Nine sections are reported in a fixed order, each ``PASS <section>`` or
``FAIL <section>: <first three failures>``, and the exit status is 1 if any failed:

- ``events``: every event class is named in backticks on some page.
- ``catalog``: ``events/index.md`` has a row per event carrying its proto message name,
  or ``custom`` for an event without one.
- ``client``, ``web-defaults``, ``routes``, ``env``: every ``TikTokLiveClient``
  parameter and public member, ``_WebDefaults`` field, route module, and environment
  variable read under ``TikTokLive/`` is named in backticks on some page.
- ``discord``: no page links to Discord; the header button is the one Discord link.
- ``readme``: README event descriptions equal the catalog's, so the PyPI landing page
  and the site do not drift.
- ``examples``: every ``python`` fence, indented or not, parses and type-checks with mypy
  against the installed package; a known-bad canary in the same run proves mypy sees it.
"""

from __future__ import annotations

import argparse
import ast
import html
import re
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTENT_ROOT = REPO_ROOT / "docs" / "src" / "content" / "docs"
GENERATED_DIRS = {"api", "schema"}  # written by gen_api.py on every build, never authored
PAGE_SUFFIXES = {".md", ".mdx"}

PACKAGE_DIR = "TikTokLive"
EVENT_MODULES = ("TikTokLive/events/custom_events.py", "TikTokLive/events/proto_events.py")
CLIENT_MODULE = "TikTokLive/client/client.py"
CLIENT_CLASS = "TikTokLiveClient"
WEB_SETTINGS_MODULE = "TikTokLive/client/web/web_settings.py"
WEB_DEFAULTS_CLASS = "_WebDefaults"  # WebDefaults is a module-level instance of it
ROUTES_DIR = "TikTokLive/client/web/routes"
CATALOG_PAGE = "events/index.md"
README = "README.md"

MYPY_ARGS = ("--python-version", "3.10", "--ignore-missing-imports", "--follow-imports=silent")

# A known type error. If mypy does not flag it, the interpreter it inspects lacks TikTokLive's
# dependencies, every proto-derived base is Any, and the examples are not really checked.
CANARY_FILE = "canary.py"
CANARY = "from TikTokLive.events import GiftEvent\n\ndef f(e: GiftEvent) -> str:\n    return e.comment\n"

# os.environ.get("X"), os.environ["X"], os.getenv("X"), environ.get("X"): the quoted
# upper-case name within 40 characters after the access word, on the same line.
ENV_READ = re.compile(r"\b(?:environ|getenv)\b.{0,40}?(['\"])([A-Z][A-Z0-9_]+)\1")

# | `EventName` | `WebcastXMessage` or `custom` | description |
CATALOG_ROW = re.compile(r"^\|\s*`(\w+)`\s*\|\s*`?(\w+)`?\s*\|\s*(.*?)\s*\|\s*$", re.MULTILINE)

# <li><code>Name</code> - description</li>; the name may be wrapped in <a …>…</a> and
# the description may be absent.
README_ITEM = re.compile(
    r"<li>\s*(?:<a\b[^>]*>)?\s*<code>(\w+)</code>\s*(?:</a>)?(?:\s*-\s*(.*?))?\s*</li>", re.DOTALL
)

# ```python … ``` at any indentation (list items, <Steps>); the closer must share the opener's indent.
PYTHON_FENCE = re.compile(r"^([ \t]*)```(?:python|py)\b[^\n]*\n(.*?)^\1```[ \t]*$", re.MULTILINE | re.DOTALL)
PYTHON_FENCE_OPENER = re.compile(r"^[ \t]*```(?:python|py)\b", re.MULTILINE)
DISCORD_LINK = re.compile(r"discord\.(?:gg|com)", re.IGNORECASE)
MYPY_ERROR = re.compile(r"^(?P<path>.+?\.py):(?P<line>\d+):(?:\d+:)? error: (?P<message>.*)$")

MARKDOWN_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
MARKUP = re.compile(r"<[^>]+>|`")


@dataclass
class Page:
    """An authored page: its path relative to the content root, and its full text."""

    path: Path
    text: str


# --- Reading the docs and the code -----------------------------------------------------


def collect_pages(content_root: Path) -> list[Page]:
    """Authored pages under ``content_root``, skipping the generated ``api/`` and ``schema/``."""
    pages = []
    for path in sorted(content_root.rglob("*")):
        if path.suffix not in PAGE_SUFFIXES or not path.is_file():
            continue
        relative = path.relative_to(content_root)
        if relative.parts[0] in GENERATED_DIRS:
            continue
        pages.append(Page(relative, path.read_text(encoding="utf-8")))
    return pages


def _parse(repo: Path, relative: str) -> ast.Module:
    return ast.parse((repo / relative).read_text(encoding="utf-8"), filename=relative)


def _class_def(module: ast.Module, name: str) -> ast.ClassDef:
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    raise LookupError(f"class {name} is not defined at module level")


def _base_name(base: ast.expr) -> str:
    """``proto.WebcastChatMessage`` and ``WebcastChatMessage`` both give ``WebcastChatMessage``."""
    return base.attr if isinstance(base, ast.Attribute) else ast.unparse(base)


def event_classes(repo: Path) -> dict[str, str | None]:
    """Every class in the event modules, mapped to its direct ``Webcast*`` base or ``None``.

    Proto events subclass their message (``CommentEvent(BaseEvent, WebcastChatMessage)``);
    custom events subclass ``BaseEvent`` or another event and map to ``None``.
    """
    events: dict[str, str | None] = {}
    for relative in EVENT_MODULES:
        for node in _parse(repo, relative).body:
            if isinstance(node, ast.ClassDef):
                protos = [name for name in map(_base_name, node.bases) if name.startswith("Webcast")]
                events[node.name] = protos[0] if protos else None
    return events


def client_surface(repo: Path) -> tuple[list[str], list[str]]:
    """``TikTokLiveClient.__init__`` parameters without ``self``, and its public methods and properties.

    Members keep definition order and appear once each: ``@overload`` stubs repeat a name.
    """
    cls = _class_def(_parse(repo, CLIENT_MODULE), CLIENT_CLASS)
    params: list[str] = []
    members: list[str] = []
    for node in cls.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name == "__init__":
            args = node.args
            ordered = [*args.posonlyargs, *args.args, args.vararg, *args.kwonlyargs, args.kwarg]
            params = [arg.arg for arg in ordered if arg is not None and arg.arg != "self"]
        elif not node.name.startswith("_") and node.name not in members:
            members.append(node.name)
    return params, members


def web_defaults_fields(repo: Path) -> list[str]:
    """Fields of the ``_WebDefaults`` dataclass, from its annotated assignments."""
    cls = _class_def(_parse(repo, WEB_SETTINGS_MODULE), WEB_DEFAULTS_CLASS)
    return [
        node.target.id
        for node in cls.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    ]


def route_modules(repo: Path) -> list[str]:
    """Module stems under ``TikTokLive/client/web/routes/`` except ``__init__``."""
    return sorted(path.stem for path in (repo / ROUTES_DIR).glob("*.py") if path.stem != "__init__")


def env_vars(repo: Path) -> set[str]:
    """Environment variable names read anywhere under ``TikTokLive/``."""
    names: set[str] = set()
    for path in (repo / PACKAGE_DIR).rglob("*.py"):
        names.update(match.group(2) for match in ENV_READ.finditer(path.read_text(encoding="utf-8")))
    return names


# --- Checks ------------------------------------------------------------------------------


def _documented(pages: list[Page], name: str) -> bool:
    """True when the backticked ``name`` appears on any page."""
    needle = f"`{name}`"
    return any(needle in page.text for page in pages)


def _missing(pages: list[Page], names: Iterable[str], what: str) -> list[str]:
    return [f"Missing {what} documentation: {name}" for name in names if not _documented(pages, name)]


def check_events(pages: list[Page], events: dict[str, str | None]) -> list[str]:
    return _missing(pages, events, "event")


def check_catalog(catalog_text: str, events: dict[str, str | None]) -> list[str]:
    """Every event has a catalog row whose second cell is its proto message name, or ``custom``."""
    rows = {name: proto for name, proto, _ in CATALOG_ROW.findall(catalog_text)}
    failures = []
    for name, proto in events.items():
        if name not in rows:
            failures.append(f"Event catalog row missing: {name}")
        elif rows[name] != (proto or "custom"):
            failures.append(f"Event catalog row is stale: {name}")
    return failures


def check_client(pages: list[Page], params: list[str], members: list[str]) -> list[str]:
    return _missing(pages, params, "client parameter") + _missing(pages, members, "client member")


def check_web_defaults(pages: list[Page], fields: list[str]) -> list[str]:
    return _missing(pages, fields, "WebDefaults field")


def check_routes(pages: list[Page], routes: list[str]) -> list[str]:
    return _missing(pages, routes, "route")


def check_env(pages: list[Page], names: set[str]) -> list[str]:
    return _missing(pages, sorted(names), "environment variable")


def check_discord(pages: list[Page]) -> list[str]:
    return [
        f"{page.path}: published pages must not reference Discord"
        for page in pages
        if DISCORD_LINK.search(page.text)
    ]


def plain_text(description: str) -> str:
    """A description with HTML tags, backticks, and Markdown link targets removed, whitespace-normalised.

    README items are HTML and catalog cells are Markdown, so only the wording is compared.
    """
    description = MARKDOWN_LINK.sub(r"\1", description)
    description = MARKUP.sub("", html.unescape(description))
    return " ".join(description.split())


def check_readme_catalog(readme_text: str, catalog_text: str) -> list[str]:
    """Every described README event has a catalog row with the same description."""
    catalog = {
        name: plain_text(description) for name, _, description in CATALOG_ROW.findall(catalog_text)
    }
    failures = []
    for name, description in README_ITEM.findall(readme_text):
        if not description:  # an item with no description imposes no constraint
            continue
        if name not in catalog:
            failures.append(f"README event missing from catalog: {name}")
        elif catalog[name] != plain_text(description):
            failures.append(f"README description differs from catalog: {name}")
    return failures


# --- Python examples ----------------------------------------------------------------------


def python_examples(pages: list[Page]) -> list[tuple[str, str]]:
    """``(label, code)`` for every ``python`` fence, dedented, labelled ``<page>, example <n>`` per page."""
    examples = []
    for page in pages:
        for number, (_, body) in enumerate(PYTHON_FENCE.findall(page.text), start=1):
            examples.append((f"{page.path}, example {number}", textwrap.dedent(body)))
    return examples


def check_fences(pages: list[Page]) -> list[str]:
    """Every ``python`` fence opener was extracted; a closer at another indentation would hide one."""
    failures = []
    for page in pages:
        openers = len(PYTHON_FENCE_OPENER.findall(page.text))
        extracted = len(PYTHON_FENCE.findall(page.text))
        if openers != extracted:
            failures.append(f"{page.path}: {openers} python fences but {extracted} extracted")
    return failures


def compile_examples(examples: list[tuple[str, str]], repo: Path) -> list[str]:
    """Failures from ``ast.parse`` on each example and one mypy run over all that parse, plus the canary."""
    failures = []
    with tempfile.TemporaryDirectory(prefix="docs-examples-") as tmp:
        directory = Path(tmp)
        labels: dict[str, str] = {}  # file name -> example label
        for number, (label, code) in enumerate(examples, start=1):
            try:
                ast.parse(code)
            except SyntaxError as error:
                failures.append(f"{label}: line {error.lineno}: {error.msg}")
                continue
            file_name = f"example_{number}.py"
            (directory / file_name).write_text(code, encoding="utf-8")
            labels[file_name] = label
        failures.extend(_run_mypy(repo, directory, labels))
    return failures


def _run_mypy(repo: Path, directory: Path, labels: dict[str, str]) -> list[str]:
    """Run mypy once over the example files plus the canary and map each error back to its label.

    The canary's own error is expected and never reported; its absence is.
    """
    (directory / CANARY_FILE).write_text(CANARY, encoding="utf-8")
    files = [*labels, CANARY_FILE]
    command = [sys.executable, "-m", "mypy", *MYPY_ARGS, *(str(directory / name) for name in files)]
    result = subprocess.run(command, cwd=repo, capture_output=True, text=True)
    errors = [match for match in map(MYPY_ERROR.match, result.stdout.splitlines()) if match]
    failures = []
    canary_flagged = False
    for match in errors:
        name = Path(match["path"]).name
        if name == CANARY_FILE:
            canary_flagged = True
            continue
        failures.append(f"{labels.get(name, 'mypy')}: line {match['line']}: {match['message']}")
    if result.returncode not in (0, 1) or (result.returncode == 1 and not errors):
        output = (result.stderr or result.stdout).strip().splitlines()
        detail = output[-1] if output else "no output"
        failures.append(f"mypy exited with status {result.returncode}: {detail}")
    elif not canary_flagged:
        failures.append("mypy canary not flagged: examples are not type-checked against TikTokLive")
    return failures


# --- Entry point -------------------------------------------------------------------------


def _read_optional(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check the authored docs pages against the TikTokLive code."
    )
    parser.parse_args(argv)

    repo = REPO_ROOT
    pages = collect_pages(CONTENT_ROOT)
    events = event_classes(repo)
    params, members = client_surface(repo)
    fields = web_defaults_fields(repo)
    routes = route_modules(repo)
    names = env_vars(repo)
    examples = python_examples(pages)
    catalog_text = _read_optional(CONTENT_ROOT / CATALOG_PAGE)
    readme_text = (repo / README).read_text(encoding="utf-8")

    sections = [
        ("events", check_events(pages, events)),
        ("catalog", check_catalog(catalog_text, events)),
        ("client", check_client(pages, params, members)),
        ("web-defaults", check_web_defaults(pages, fields)),
        ("routes", check_routes(pages, routes)),
        ("env", check_env(pages, names)),
        ("discord", check_discord(pages)),
        ("readme", check_readme_catalog(readme_text, catalog_text)),
        ("examples", check_fences(pages) + compile_examples(examples, repo)),
    ]

    failed = False
    for section, failures in sections:
        if failures:
            failed = True
            print(f"FAIL {section}: " + "; ".join(failures[:3]))
        else:
            print(f"PASS {section}")
    print(
        f"Checked {len(pages)} pages, {len(events)} events, {len(params)} parameters, {len(members)} members, "
        f"{len(fields)} WebDefaults fields, {len(routes)} routes, {len(names)} environment variables, "
        f"{len(examples)} Python examples."
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
