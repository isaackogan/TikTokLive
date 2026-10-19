# Starlight Documentation Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Sphinx docs of the Python `TikTokLive` library with a Starlight site, generated API and proto schema references, content-coverage and SEO gates, hosted on Cloudflare Workers at `https://ttl.docs.isaackogan.com/` and deployed from GitHub Actions, with the old GitHub Pages URLs redirecting to it.

**Architecture:** `docs/` becomes a self-contained pnpm project (Astro + Starlight + lucode theme) whose `build` script runs three Python scripts before `astro build`: `check_content.py` (coverage and example gates), `gen_api.py` (griffe → Markdown for `api/` and `schema/`), then Astro. A rewritten `docs.yml` validates on pull requests and, on pushes to `master`, deploys the static output with `wrangler deploy` and publishes a generated redirect shell to GitHub Pages. The Node.js site in `/Users/isaackogan/Documents/WebstormProjects/TikTok-Live-Connector/docs` is the reference implementation; copy its structure and prose register, not its TypeScript specifics.

**Tech Stack:** Python 3.12 in CI (floor 3.10), griffe, mypy, pytest; Node 24, pnpm 10.34.2, astro 7.4.1, @astrojs/starlight 0.42.6, lucode-starlight 1.0.0, starlight-links-validator 0.27.0, wrangler 4.151.2; Cloudflare Workers static assets; GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-19-starlight-docs-design.md`

## Global Constraints

- Public hostname is exactly `ttl.docs.isaackogan.com`; no other public name may contain "tiktok". Worker name `tiktoklive-docs` (internal only).
- Exact dependency pins, no ranges: `astro 7.4.1`, `@astrojs/starlight 0.42.6`, `lucode-starlight 1.0.0`, `starlight-links-validator 0.27.0`, `wrangler 4.151.2`, `pnpm@10.34.2` (`packageManager` field), Node `>=22.22.0` in `engines`, Node 24 in CI.
- Nothing documentation-related enters `[project].dependencies` or `[project.optional-dependencies]` in `pyproject.toml`. Python docs tooling lives only in `docs/requirements.txt`.
- Generated content (`docs/src/content/docs/api/`, `docs/src/content/docs/schema/`, `docs/dist/`, `docs/redirects/`, `docs/node_modules/`, `docs/.astro/`) is never committed.
- No `discord.com` / `discord.gg` link in any authored Markdown page. The only Discord link is the header social button `https://discord.gg/uja6SajDxd`.
- Every `eulerstream.com` link is dofollow. Every built page carries at least one; the homepage carries at least three with distinct anchor texts.
- Package version comes from `TikTokLive/__version__.py` (`PACKAGE_VERSION: str = "..."`), proto version from `importlib.metadata.version("TikTokLiveProto")`.
- Shell commands in docs use ```` ```sh ````; Python examples use ```` ```python ```` and must be complete modules that parse and type-check.
- Work on branch `docs/starlight-site` off `master`. Nothing is force-pushed. Deploys from a developer machine use the existing wrangler OAuth login; CI uses the Worker-scoped token.

## Review Focus

1. A proto event added later by `generate.yml` (new class in `TikTokLive/events/proto_events.py`) with no docs entry: the build must fail naming the event. Pinned in Task 3 (`test_check_events_reports_missing_event`).
2. An event whose proto parent is not re-exported by `TikTokLive.proto` (`GoalUpdateEvent` → `WebcastGoalUpdateMessage` in `model.gift.model`): the schema page must exist and the event page link to it must validate. Pinned in Task 2 (`test_schema_covers_non_reexported_message`) and Task 6 (links validator run).
3. A class or function with no docstring, or a Sphinx `:param:` docstring with a missing parameter: the generator must still emit a page and never crash. Pinned in Task 2 (`test_page_for_object_without_docstring`).
4. A Python example in the docs that parses but fails type-checking (for example `event.comment` on `GiftEvent`): the build must fail with the page name and example number. Pinned in Task 3 (`test_compile_examples_reports_type_error`).
5. A request for an old Sphinx URL that is not in the redirect map (for example `/search.html?q=x` or `/_static/x.css`): GitHub Pages must still answer with a page that forwards to the site root. Pinned in Task 11 (`test_unknown_old_path_falls_back_to_root` via `404.html`).

---

### Task 1: Scaffold the Starlight project and retire Sphinx

**Files:**
- Delete: `docs/src/` (whole Sphinx tree), `docs/dist/` is untracked (ignored by `dist`)
- Create: `docs/package.json`, `docs/pnpm-workspace.yaml`, `docs/tsconfig.json`, `docs/astro.config.mjs`, `docs/src/content.config.ts`, `docs/src/content/docs/index.md` (placeholder), `docs/src/content/docs/404.md`, `docs/public/favicon.png`, `docs/public/robots.txt`, `docs/public/google93ecefd594fb7167.html`, `docs/requirements.txt`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `pnpm --dir docs build` runs `python3 scripts/check_content.py && python3 scripts/gen_api.py && astro build` (scripts arrive in Tasks 2–3; until then the scripts are absent and `build` fails, so this task verifies with `pnpm --dir docs exec astro build`). Sidebar groups fixed here are consumed by every content task.

- [ ] **Step 1: Remove the Sphinx tree and move the verification file**

```bash
git mv docs/src/extra/google93ecefd594fb7167.html /tmp/google93ecefd594fb7167.html 2>/dev/null || cp docs/src/extra/google93ecefd594fb7167.html /tmp/
git rm -r -q docs/src
mkdir -p docs/public docs/src/content/docs docs/scripts
mv /tmp/google93ecefd594fb7167.html docs/public/
```

- [ ] **Step 2: Create `docs/package.json`**

Name `tiktoklive-docs`, `private: true`, `type: module`, `packageManager: pnpm@10.34.2`, `engines.node >=22.22.0`. Scripts: `dev` (`astro dev --host 127.0.0.1`), `check` (`python3 scripts/check_content.py`), `generate` (`python3 scripts/gen_api.py`), `build` (`python3 scripts/check_content.py && python3 scripts/gen_api.py && astro build`), `preview`, `deploy:cloudflare` (`wrangler deploy`). devDependencies with the exact pins from Global Constraints plus `@astrojs/markdown-remark 7.3.3` and `unist-util-visit 5.0.0` (needed by the base-prefixing remark plugin copied from the Node config).

- [ ] **Step 3: Create `docs/pnpm-workspace.yaml`, `docs/tsconfig.json`, `docs/requirements.txt`**

`pnpm-workspace.yaml`: `packages: [.]`, `onlyBuiltDependencies: [esbuild, sharp, workerd]`. `tsconfig.json`: copy from the Node repo. `requirements.txt`: `griffe==1.14.0` (or the current release; pin exactly) and `mypy>=1.10`.

- [ ] **Step 4: Create `docs/astro.config.mjs`**

Start from the Node repo's `docs/astro.config.mjs`. Keep: `base` handling, `prefixLinks` remark plugin, `trailingSlash: 'always'`, `starlightLinksValidator()`. Change: `site` default `https://ttl.docs.isaackogan.com`; `title: 'TikTokLive'`; `description: 'Unofficial TikTok LIVE API for Python. Guides, events, and generated API reference.'`; `favicon: '/favicon.png'`; `social` GitHub `https://github.com/isaackogan/TikTokLive` and Discord `https://discord.gg/uja6SajDxd`; `editLink.baseUrl` `https://github.com/isaackogan/TikTokLive/edit/master/docs/`; lucode plugin with `navLinks` Docs (`base`), Events (`${base}events/`), API (`${base}api/`) and `footerText` `'Unofficial project, not affiliated with TikTok or ByteDance Ltd. Signing by [Euler Stream](https://www.eulerstream.com/). Source on [GitHub](https://github.com/isaackogan/TikTokLive).'`. Remove `starlight-typedoc`. Sidebar:

```js
sidebar: [
  { label: 'Start here', items: [
    { label: 'Getting Started', slug: '' },
    { label: 'Connection lifecycle', slug: 'getting-started/connection' },
    { label: 'Migration', slug: 'getting-started/migration' },
  ] },
  { label: 'Configuration', items: [{ autogenerate: { directory: 'configuration' } }] },
  { label: 'Guides', items: [{ autogenerate: { directory: 'guides' } }] },
  { label: 'Events', items: [{ autogenerate: { directory: 'events' } }], collapsed: true },
  { label: 'Advanced', items: [{ autogenerate: { directory: 'advanced' } }], collapsed: true },
  { label: 'Troubleshooting', slug: 'troubleshooting' },
  { label: 'Contributing to the docs', slug: 'contributing' },
  { label: 'Hosting', slug: 'hosting' },
  { label: 'API reference', items: [{ autogenerate: { directory: 'api' } }], collapsed: true },
  { label: 'Protobuf schema', items: [{ autogenerate: { directory: 'schema' } }], collapsed: true },
],
```

Add `head` entries: `meta property="og:image"` = `https://raw.githubusercontent.com/isaackogan/TikTokLive/master/.github/SquareLogo.png`, `og:image:alt` = `TikTokLive, TikTok LIVE API for Python`, `name="twitter:card"` = `summary_large_image`.

- [ ] **Step 5: Create `docs/src/content.config.ts`, placeholder pages, public files**

`content.config.ts`: copy from the Node repo (uses `ExtendDocsSchema` from `lucode-starlight/schema`). `index.md`: frontmatter `title: Getting Started`, one paragraph. `404.md`: copy from the Node repo, GitHub link changed. `public/favicon.png`: copy from the Node repo's `docs/public/favicon.png`. `public/robots.txt`: `User-agent: *`, `Allow: /`, blank line, `Sitemap: https://ttl.docs.isaackogan.com/sitemap-index.xml`.

- [ ] **Step 6: Extend `.gitignore`**

Append `docs/node_modules/`, `docs/.astro/`, `docs/src/content/docs/api/`, `docs/src/content/docs/schema/`, `docs/redirects/`. Verify `git check-ignore docs/dist` already matches via `dist`.

- [ ] **Step 7: Install and build**

Run: `npx -y pnpm@10.34.2 --dir docs install` then `npx -y pnpm@10.34.2 --dir docs exec astro build`
Expected: build completes, `docs/dist/index.html` contains `<title>Getting Started | TikTokLive</title>`, `docs/dist/robots.txt` and `docs/dist/google93ecefd594fb7167.html` exist, `grep -c 'discord.gg/uja6SajDxd' docs/dist/index.html` is 1.

- [ ] **Step 8: Commit**

```bash
git add -A docs .gitignore
git commit -m "docs: replace Sphinx with a Starlight project scaffold"
```

### Task 2: API and schema generator

**Files:**
- Create: `docs/scripts/gen_api.py`, `docs/scripts/tests/__init__.py`, `docs/scripts/tests/test_gen_api.py`, `docs/scripts/tests/conftest.py`

**Interfaces:**
- Produces, in `gen_api.py`:
  - `REPO_ROOT: Path` (two levels above `docs/scripts`), `CONTENT_ROOT: Path` (`docs/src/content/docs`)
  - `package_version() -> str` from `TikTokLive/__version__.py`; `proto_version() -> str` via `importlib.metadata`
  - `load_module(name: str) -> griffe.Module` using `griffe.load(name, docstring_parser="sphinx", resolve_aliases=True, search_paths=[REPO_ROOT, <site-packages>])`
  - `reexported_modules() -> set[str]` parsed from the `from X import *` lines of `TikTokLive/proto/__init__.py`
  - `api_slug(path: str) -> str` turning `TikTokLive.client.client.TikTokLiveClient` into `tiktoklive/client/client/tiktokliveclient`
  - `schema_slug(path: str) -> str` turning `TikTokLiveProto.v3.webcast.model.message.WebcastChatMessage` into `webcast/model/message/webcastchatmessage`
  - `page_for(obj: griffe.Object, *, import_path: str, source_url: str | None) -> str` returning Markdown with frontmatter `title`, `description` and sections Signature, Parameters, Attributes, Methods, Bases, Import, Source
  - `render_api(root: griffe.Module, out_dir: Path) -> list[Path]` for public modules, classes and functions under `TikTokLive`, `TikTokLive.client`, `TikTokLive.events`, excluding names starting with `_` and the `TikTokLive.proto` subtree
  - `render_schema(proto_root: griffe.Module, reexported: set[str], out_dir: Path) -> list[Path]` for every class whose bases include `betterproto2.Message` or `Enum` under `TikTokLiveProto.v3`
  - `main(argv: list[str] | None = None) -> int` wiping and regenerating `api/` and `schema/`, writing `api/index.md` titled `TikTokLive <version>` and `schema/index.md` titled `TikTok Webcast v3 schema (<proto version>)`
- Consumed by Task 1's `package.json` `generate`/`build` scripts, Task 6 (event pages link to `/schema/<schema_slug>/`), Task 11 (redirect targets `/api/tiktoklive/client/` etc.).

- [ ] **Step 1: Write failing tests**

In `docs/scripts/tests/test_gen_api.py` (conftest adds `docs/scripts` to `sys.path`):

```python
def test_reexported_modules_lists_star_imports():
    mods = gen_api.reexported_modules()
    assert "TikTokLiveProto.v3.webcast.model.message" in mods
    assert "TikTokLiveProto.v3.webcast.model.gift.model" not in mods

def test_slugs():
    assert gen_api.api_slug("TikTokLive.client.client.TikTokLiveClient") == "tiktoklive/client/client/tiktokliveclient"
    assert gen_api.schema_slug("TikTokLiveProto.v3.webcast.model.message.WebcastChatMessage") == "webcast/model/message/webcastchatmessage"

def test_client_page_has_signature_and_params(tiktoklive_module):
    client = tiktoklive_module["client"]["client"]["TikTokLiveClient"]
    md = gen_api.page_for(client, import_path="TikTokLive", source_url=None)
    assert md.startswith("---\ntitle: TikTokLiveClient\n")
    assert "unique_id" in md and "## Parameters" in md and "## Methods" in md and "is_live" in md

def test_page_for_object_without_docstring(tiktoklive_module):
    obj = tiktoklive_module["client"]["web"]["routes"]  # package with no docstring
    md = gen_api.page_for(obj, import_path="TikTokLive.client.web.routes", source_url=None)
    assert "title: routes" in md

def test_schema_covers_non_reexported_message(tmp_path, proto_module):
    paths = gen_api.render_schema(proto_module, gen_api.reexported_modules(), tmp_path)
    page = tmp_path / "webcast/model/gift/model/webcastgoalupdatemessage/index.md"
    assert page.exists()
    assert "from TikTokLiveProto.v3.webcast.model.gift.model import WebcastGoalUpdateMessage" in page.read_text()
    chat = (tmp_path / "webcast/model/message/webcastchatmessage/index.md").read_text()
    assert "from TikTokLive.proto import WebcastChatMessage" in chat
    assert len(paths) > 300

def test_render_api_excludes_private_and_proto(tmp_path, tiktoklive_module):
    paths = gen_api.render_api(tiktoklive_module, tmp_path)
    names = {p.relative_to(tmp_path).as_posix() for p in paths}
    assert "tiktoklive/client/client/tiktokliveclient/index.md" in names
    assert not any("/proto/" in n or "/_" in n for n in names)
```

Fixtures `tiktoklive_module` and `proto_module` call `gen_api.load_module("TikTokLive")` / `("TikTokLiveProto")` once per session.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pip install -r docs/requirements.txt && .venv/bin/python -m pytest docs/scripts/tests/test_gen_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'gen_api'`.

- [ ] **Step 3: Implement `docs/scripts/gen_api.py`**

Signatures from Interfaces. Frontmatter `description` is the first docstring paragraph or `"<kind> <qualified name>"`. Parameters come from the griffe parsed docstring sections merged with the signature so undocumented parameters still appear with their annotation and default. Methods list links to the method's own page for classes with more than five public methods, otherwise inline. Source links use `https://github.com/isaackogan/TikTokLive/blob/v<version>/<relpath>#L<lineno>`; `source_url=None` for objects from site-packages. Each generated page gets `sidebar: { label: <name> }`; index pages get `sidebar: { order: 0 }`. Wipe `api/` and `schema/` before writing.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest docs/scripts/tests/test_gen_api.py -v`
Expected: 6 passed.

- [ ] **Step 5: Generate and build**

Run: `cd docs && ../.venv/bin/python scripts/gen_api.py && npx -y pnpm@10.34.2 exec astro build 2>&1 | tail -5`
Expected: `All internal links are valid.` and the page count printed by Astro is above 400. Open `docs/dist/api/tiktoklive/client/client/tiktokliveclient/index.html` and confirm the signature block renders.

- [ ] **Step 6: Commit**

```bash
git add docs/scripts/gen_api.py docs/scripts/tests
git commit -m "docs: generate API and proto schema reference with griffe"
```

### Task 3: Content check script

**Files:**
- Create: `docs/scripts/check_content.py`, `docs/scripts/tests/test_check_content.py`

**Interfaces:**
- Produces, in `check_content.py`:
  - `Page = dataclass(path: Path, text: str)`; `collect_pages(content_root: Path) -> list[Page]` excluding `api/` and `schema/`
  - `event_classes(repo: Path) -> dict[str, str | None]` mapping every class defined in `TikTokLive/events/custom_events.py` and `proto_events.py` to its `Webcast*` base name (or `None`), via `ast`
  - `client_surface(repo: Path) -> tuple[list[str], list[str]]` = (`__init__` parameter names except `self`, public method and property names of `TikTokLiveClient`) via `ast`
  - `web_defaults_fields(repo: Path) -> list[str]` from the annotated assignments of class `_WebDefaults`
  - `route_modules(repo: Path) -> list[str]` module stems under `TikTokLive/client/web/routes/` except `__init__`
  - `env_vars(repo: Path) -> set[str]` matching `os.environ.get("X")`, `os.environ["X"]`, `os.getenv("X")`, `environ.get("X")`, and the literal `'WHITELIST_AUTHENTICATED_SESSION_ID_HOST'` form (any quoted `[A-Z][A-Z0-9_]+` following `environ` or `getenv` within 40 characters)
  - `check_events(pages, events) -> list[str]`, `check_catalog(catalog_text, events) -> list[str]`, `check_client(pages, params, members) -> list[str]`, `check_web_defaults(pages, fields) -> list[str]`, `check_routes(pages, routes) -> list[str]`, `check_env(pages, names) -> list[str]`, `check_discord(pages) -> list[str]`, `check_readme_catalog(readme_text, catalog_text) -> list[str]`
  - `python_examples(pages) -> list[tuple[str, str]]` (label, code) from ```` ```python ```` fences; `compile_examples(examples, repo: Path) -> list[str]` running `ast.parse` then one `mypy` invocation over temp files with `--python-version 3.10 --ignore-missing-imports --follow-imports=silent`
  - `main(argv=None) -> int` printing `PASS`/`FAIL <section>: <first three failures>` per section and a summary line `Checked N pages, E events, P parameters, M members, F WebDefaults fields, R routes, V environment variables, X Python examples.`; exit 1 if any section failed
- Catalog contract consumed by Task 6: `events/index.md` has one table row per event of the form ``| `EventName` | `WebcastXMessage` or `custom` | <description> |``.

- [ ] **Step 1: Write failing tests**

```python
def test_event_classes_includes_custom_and_proto():
    events = check_content.event_classes(REPO)
    assert events["CommentEvent"] == "WebcastChatMessage"
    assert events["ConnectEvent"] is None
    assert events["GoalUpdateEvent"] == "WebcastGoalUpdateMessage"
    assert len(events) >= 74

def test_client_surface():
    params, members = check_content.client_surface(REPO)
    assert params == ["unique_id", "platform", "web_proxy", "ws_proxy", "web_kwargs", "ws_kwargs", "is_user_id"]
    assert {"run", "start", "connect", "disconnect", "is_live", "room_id", "web"} <= set(members)
    assert not any(m.startswith("_") for m in members)

def test_web_defaults_fields_and_routes_and_env():
    assert "tiktok_sign_api_key" in check_content.web_defaults_fields(REPO)
    assert "fetch_signed_websocket" in check_content.route_modules(REPO)
    assert {"SIGN_API_KEY", "SIGN_API_URL", "SIGN_SERVER_MESSAGE_DISABLED", "SEND_DEPRECATION_WARNINGS", "WHITELIST_AUTHENTICATED_SESSION_ID_HOST"} <= check_content.env_vars(REPO)

def test_check_events_reports_missing_event():
    pages = [check_content.Page(Path("x.md"), "`CommentEvent` is documented.")]
    failures = check_content.check_events(pages, {"CommentEvent": "WebcastChatMessage", "NewShinyEvent": "WebcastNewShinyMessage"})
    assert failures == ["Missing event documentation: NewShinyEvent"]

def test_check_catalog_requires_row_with_proto_name():
    catalog = "| `CommentEvent` | `WebcastChatMessage` | A viewer sent a chat comment |\n"
    assert check_content.check_catalog(catalog, {"CommentEvent": "WebcastChatMessage"}) == []
    assert check_content.check_catalog(catalog, {"CommentEvent": "WebcastOtherMessage"}) == ["Event catalog row is stale: CommentEvent"]

def test_check_discord():
    pages = [check_content.Page(Path("t.md"), "Join https://discord.gg/abc")]
    assert check_content.check_discord(pages) == ["t.md: published pages must not reference Discord"]

def test_check_readme_catalog_detects_drift():
    readme = "<li><code>CommentEvent</code> - A viewer sent a chat comment</li>"
    assert check_content.check_readme_catalog(readme, "| `CommentEvent` | `WebcastChatMessage` | A viewer sent a chat comment |") == []
    assert check_content.check_readme_catalog(readme, "| `CommentEvent` | `WebcastChatMessage` | Something else |") == ["README description differs from catalog: CommentEvent"]

def test_compile_examples_reports_type_error(tmp_path):
    bad = ("page.md, example 1", "from TikTokLive.events import GiftEvent\n\ndef f(e: GiftEvent) -> str:\n    return e.comment\n")
    good = ("page.md, example 2", "from TikTokLive.events import CommentEvent\n\ndef f(e: CommentEvent) -> str:\n    return e.comment\n")
    failures = check_content.compile_examples([bad, good], REPO)
    assert len(failures) == 1 and failures[0].startswith("page.md, example 1")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest docs/scripts/tests/test_check_content.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'check_content'`.

- [ ] **Step 3: Implement `docs/scripts/check_content.py`**

Signatures from Interfaces. Event presence means the backticked name appears in any authored page. Catalog rows are matched with a regex on the first two cells. README event descriptions are the text after `</code> - ` up to `</li>`, compared after whitespace normalisation to the catalog's third cell.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest docs/scripts/tests -v`
Expected: all tests in both files pass.

- [ ] **Step 5: Run the check against the scaffold**

Run: `cd docs && ../.venv/bin/python scripts/check_content.py; echo "exit=$?"`
Expected: exit 1, with `FAIL events`, `FAIL catalog`, `FAIL client`, `FAIL web-defaults`, `FAIL routes`, `FAIL env`, `FAIL readme`, and `PASS discord`, `PASS examples`. Section names are exactly these nine and are printed in this order. This is the gate the content tasks drive to green.

- [ ] **Step 6: Commit**

```bash
git add docs/scripts/check_content.py docs/scripts/tests/test_check_content.py
git commit -m "docs: add content coverage and example checks"
```

### Task 4: Start here pages

**Files:**
- Modify: `docs/src/content/docs/index.md`
- Create: `docs/src/content/docs/getting-started/connection.md`, `docs/src/content/docs/getting-started/migration.md`

**Interfaces:**
- Consumes: catalog and page contract from Task 3; Node pages `index.md`, `getting-started/connection.md`, `getting-started/migration.md` as structural templates; README `Getting Started`, `Parameters`, `Methods`, `GiftEvent` sections; the old `docs/src/index.rst` text (from git history `git show HEAD~3:docs/src/index.rst`) for the production-use note.
- Produces: heading slugs `#prerequisites`, `#install`, `#listen-to-a-livestream`, `#next-steps` on the root page.

- [ ] **Step 1: Write `index.md` (Getting Started)**

Sections in order: intro paragraph (what the library receives, `TikTokLiveClient`), `## Prerequisites` (Python 3.10 or newer, asyncio, no login for public rooms, signing by Euler Stream with a dofollow link, unofficial disclaimer), `## Install` (`pip install TikTokLive` in a `sh` fence), `## Listen to a livestream` (the README example as a complete module), `## Read event payloads` (`event.user.nickname`, `event.comment`, `event.user.unique_id`, optional fields), `## Signing` (`SIGN_API_KEY`, `WebDefaults.tiktok_sign_api_key`, two more dofollow Euler Stream links with different anchor texts), `## Next steps` (links to connection, events, gifts guide, configuration, API reference), closing paragraphs on the `master` branch, versions, and the Node.js sibling at `https://ttlc.docs.isaackogan.com/`.

- [ ] **Step 2: Write `connection.md` and `migration.md`**

`connection.md`: `run` vs `start` vs `connect`, `fetch_room_info` / `fetch_gift_info` keyword arguments, `ConnectEvent`, `DisconnectEvent`, `LiveEndEvent`, reconnect pattern, `is_live` before connecting, `close()`. `migration.md`: v6 → v7 from `git log v6.6.5..v7.0.0 --oneline` and the README "New in 7.X.X" list: event renames and additions, `Gift` field names (`name`, `type`, `image` with `gift_*` aliases on `ExtendedGift`), removal of the `type` property in favour of `get_type()`, `platform` and `is_user_id` parameters, TikTokLiveProto v3.

- [ ] **Step 3: Verify**

Run: `cd docs && ../.venv/bin/python scripts/check_content.py | grep -E '^(PASS|FAIL) (examples|discord)'` then `npx -y pnpm@10.34.2 exec astro build 2>&1 | grep -E 'links are valid|error'`
Expected: `PASS examples`, `PASS discord`, `All internal links are valid.`

- [ ] **Step 4: Commit**

```bash
git add docs/src/content/docs/index.md docs/src/content/docs/getting-started
git commit -m "docs: write Getting Started, connection lifecycle, and migration pages"
```

### Task 5: Configuration pages

**Files:**
- Create: `docs/src/content/docs/configuration/options.md`, `web-defaults.md`, `environment.md`, `signing.md`, `authentication.md`, `proxies.md`

**Interfaces:**
- Consumes: `client_surface`, `web_defaults_fields`, `env_vars` contracts (Task 3) decide which names must appear; README `Parameters`, `Methods`, `Properties`, `WebDefaults` tables; `examples/web_defaults.py`, `examples/logged_in.py`, `examples/proxying.py`; `TikTokLive/client/web/web_utils.py` for the session-ID host whitelist.
- Produces: `options.md` documents every constructor parameter and every public method and property of `TikTokLiveClient` in backticks; `web-defaults.md` every `_WebDefaults` field; `environment.md` every environment variable in a table `| Variable | Default | Effect |`.

- [ ] **Step 1: Write the six pages**

`options.md` has a parameters table, a methods table (`run`, `start`, `connect`, `disconnect`, `close`, `on`, `add_listener`, `has_listener`, `is_live`, `get_avatar_url`, `send_room_chat`, `parse_unique_id`, `handle_custom_event`) and a properties table. `signing.md` explains Euler Stream signing, `SIGN_API_KEY`, `SIGN_API_URL`, `tiktok_sign_url`, rate limits, with dofollow links. `authentication.md` covers `web_kwargs={"cookies": {...}}`, `sessionid`, `WHITELIST_AUTHENTICATED_SESSION_ID_HOST`, and the risks. `proxies.md` covers `web_proxy`, `ws_proxy`, `httpx.Proxy`, `WebcastProxy`.

- [ ] **Step 2: Verify**

Run: `cd docs && ../.venv/bin/python scripts/check_content.py | grep -E '^(PASS|FAIL)'`
Expected: `PASS client`, `PASS web-defaults`, `PASS env`, `PASS examples`, `PASS discord`; `events`, `catalog`, `routes` still `FAIL`.

- [ ] **Step 3: Commit**

```bash
git add docs/src/content/docs/configuration
git commit -m "docs: write configuration pages"
```

### Task 6: Event catalog and grouped event pages

**Files:**
- Create: `docs/src/content/docs/events/index.md`, `control.md`, `chat-and-audience.md`, `gifts-and-goals.md`, `battles-and-cohosting.md`, `subscriptions-and-fans.md`, `room-and-display.md`, `rankings.md`, `moderation-and-access.md`, `games-and-commerce.md`, `stream-control.md`

**Interfaces:**
- Consumes: `event_classes` (Task 3) for the full list; README event lists for descriptions (these must match verbatim, see `check_readme_catalog`); Node event pages for grouping and page structure; schema slugs from Task 2 for the proto link on each event.
- Produces: one `## <EventName>` heading per event (slug `#<eventname>` lowercase) on exactly one grouped page; each with a one-line description, the proto message link `/schema/<schema_slug>/`, key fields, and a short `python` example where behaviour is non-obvious (`GiftEvent`, `CommentEvent`, `LikeEvent`, `RoomUserSeqEvent`, `ConnectEvent`, `DisconnectEvent`). Catalog rows exactly per the Task 3 contract. README deep links (Task 10) target these slugs.

- [ ] **Step 1: Write `events/index.md`**

Intro on `@client.on(Event)` and `add_listener`, a `python` example, a statement of the counts, then `## Find an event` with the catalog table containing every event from `event_classes`. The 12 custom events use `custom` in the second cell. Descriptions copied from the README lists; events the README leaves undescribed get a description written here and the same text added to the README in Task 10.

- [ ] **Step 2: Write the ten grouped pages**

Assign each event to one group following the Node pages' mapping of the same message names (`WebcastChatMessage` → chat and audience, `WebcastGiftMessage` → gifts and goals, `WebcastLinkMic*` → battles and cohosting, `WebcastSubNotify*`/`Barrage` super-fan events → subscriptions and fans, and so on). `control.md` holds `ConnectEvent`, `DisconnectEvent`, `WebsocketResponseEvent`, `UnknownEvent`; `stream-control.md` holds `ControlEvent`, `LiveEndEvent`, `LivePauseEvent`, `LiveUnpauseEvent`.

- [ ] **Step 3: Verify**

Run: `cd docs && ../.venv/bin/python scripts/check_content.py | grep -E '^(PASS|FAIL)'` then `../.venv/bin/python scripts/gen_api.py && npx -y pnpm@10.34.2 exec astro build 2>&1 | grep -E 'links are valid|error|Invalid'`
Expected: `PASS events`, `PASS catalog`; `All internal links are valid.` (this proves every `/schema/...` link from an event page resolves, including `GoalUpdateEvent`).

- [ ] **Step 4: Commit**

```bash
git add docs/src/content/docs/events
git commit -m "docs: write the event catalog and grouped event pages"
```

### Task 7: Guides

**Files:**
- Create: `docs/src/content/docs/guides/gifts.md`, `check-live.md`, `send-chat.md`, `recording.md`, `images.md`, `debugging-events.md`, `web-ui.md`

**Interfaces:**
- Consumes: `examples/gifts.py`, `check_live.py`, `recording.py`, `images.py`, `web-ui/service.py`; README `GiftEvent` section; Node `guides/gifts.md`, `guides/send-chat.md`, `guides/backend.md` for structure.
- Produces: each guide contains at least one complete `python` example that type-checks.

- [ ] **Step 1: Write the seven guides**

`gifts.md` covers `repeat_count`, `repeat_end`, `streaking`, `fetch_gift_info`, `ExtendedGift`. `debugging-events.md` covers `WebsocketResponseEvent`, `UnknownEvent`, `client.logger.setLevel`, and `SEND_DEPRECATION_WARNINGS`. `web-ui.md` mirrors the Node backend guide: run the client in a process and fan events out over SSE.

- [ ] **Step 2: Verify**

Run: `cd docs && ../.venv/bin/python scripts/check_content.py | grep -E '^(PASS|FAIL) examples'`
Expected: `PASS examples`.

- [ ] **Step 3: Commit**

```bash
git add docs/src/content/docs/guides
git commit -m "docs: write guides"
```

### Task 8: Advanced, troubleshooting, contributing, hosting pages

**Files:**
- Create: `docs/src/content/docs/advanced/web-client.md`, `routes.md`, `websocket.md`, `protocol.md`, `docs/src/content/docs/troubleshooting.md`, `contributing.md`, `hosting.md`, `docs/README.md`
- Modify: `CONTRIBUTING.md` (add a "Documentation" section)

**Interfaces:**
- Consumes: `route_modules` (Task 3) decides the names `routes.md` must contain; Node `advanced/routes.md`, `advanced/websocket.md`, `advanced/protocol.md`, `troubleshooting.md`, `contributing.md`, `hosting.md`, `docs/README.md` as templates; Task 12's workflow and Worker details for `hosting.md`.
- Produces: `pnpm --dir docs build` fully green.

- [ ] **Step 1: Write the pages**

`routes.md` documents all eleven route modules by name with their client method. `hosting.md` is the Node page with the hostname `ttl.docs.isaackogan.com`, Worker `tiktoklive-docs`, secrets, the Python install step, the redirect shell, and the SEO gate. `contributing.md` and `docs/README.md` describe `pnpm --dir docs check`, `generate`, `build`, `dev`, the Python requirements, and the two content sources (README and the retired Sphinx pages in Git history).

- [ ] **Step 2: Verify the full build**

Run: `cd docs && npx -y pnpm@10.34.2 build 2>&1 | grep -E '^(PASS|FAIL)|Checked|links are valid|page\(s\) built|error'`
Expected: every section `PASS`, the `Checked ... pages` summary, `All internal links are valid.`, a page count above 1000.

- [ ] **Step 3: Commit**

```bash
git add docs/src/content/docs docs/README.md CONTRIBUTING.md
git commit -m "docs: write advanced, troubleshooting, contributing, and hosting pages"
```

### Task 9: SEO gate for the Starlight output

**Files:**
- Modify: `scripts/seo/verify_seo.py`
- Create: `docs/scripts/tests/test_verify_seo.py`

**Interfaces:**
- Produces: `verify_seo.main(build_dir: str = "docs/dist") -> int` with `BASE_URL = "https://ttl.docs.isaackogan.com/"`, pages = every `index.html` plus `404.html`; checks: homepage `<title>` contains `TikTok LIVE API`; every page has `rel="canonical"` with `BASE_URL`; homepage has `og:title`, `og:description`, `og:image`, meta description; `sitemap-index.xml` and `sitemap-0.xml` exist, the latter uses `BASE_URL` and has more than one `<loc>`; `robots.txt` contains `Sitemap: https://ttl.docs.isaackogan.com/sitemap-index.xml`; `google93ecefd594fb7167.html` exists; no eulerstream link is nofollowed; every page has at least one eulerstream link; homepage has at least three distinct eulerstream anchor texts; every page contains the lucode sidebar marker chosen from the real build (record the exact string in a module constant `NAV_MARKER`). Remove the Sphinx-only checks (`6.6.5`, `{lang}`, `sidebar-tree`).

- [ ] **Step 1: Write failing tests**

```python
def test_gate_passes_on_fixture_site(tmp_path):
    write_fixture_site(tmp_path)  # helper in the test: homepage + one nested page satisfying every invariant
    assert verify_seo.main(str(tmp_path)) == 0

def test_gate_fails_when_nested_page_lacks_euler_link(tmp_path):
    write_fixture_site(tmp_path, nested_euler_links=0)
    assert verify_seo.main(str(tmp_path)) == 1

def test_gate_fails_when_robots_has_no_sitemap(tmp_path):
    write_fixture_site(tmp_path, robots="User-agent: *\nAllow: /\n")
    assert verify_seo.main(str(tmp_path)) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest docs/scripts/tests/test_verify_seo.py -v`
Expected: FAIL (the fixture passes the old Sphinx checks only by accident or fails on `sitemap.xml`).

- [ ] **Step 3: Rewrite `scripts/seo/verify_seo.py` per Interfaces**

- [ ] **Step 4: Run tests, then the gate against the real build**

Run: `.venv/bin/python -m pytest docs/scripts/tests/test_verify_seo.py -v && .venv/bin/python scripts/seo/verify_seo.py docs/dist`
Expected: 3 passed; the gate prints only `PASS` lines and `N passed, 0 failed`. If the homepage title check fails, set the homepage `<title>` through Starlight `head` on `index.md` (`TikTok LIVE API for Python: TikTokLive Documentation`) rather than renaming the site.

- [ ] **Step 5: Commit**

```bash
git add scripts/seo/verify_seo.py docs/scripts/tests/test_verify_seo.py docs/src/content/docs/index.md docs/astro.config.mjs
git commit -m "docs: adapt the SEO gate to the Starlight site"
```

### Task 10: README, examples README, and package metadata

**Files:**
- Modify: `README.md`, `examples/README.md`, `pyproject.toml` (`[project.urls] Documentation` only)

**Interfaces:**
- Consumes: event heading slugs from Task 6; `check_readme_catalog` (Task 3) keeps README descriptions equal to the catalog.
- Produces: no relative links in `README.md`; every `https://ttl.docs.isaackogan.com/...` link resolves to a page and anchor in `docs/dist`.

- [ ] **Step 1: Edit the README**

Table of contents `Documentation` entry and a line after the intro paragraph point at `https://ttl.docs.isaackogan.com/`. Every `<li><code>XEvent</code>` item becomes `<li><a href="https://ttl.docs.isaackogan.com/events/<group>/#<xevent>"><code>XEvent</code></a> - <description></li>`, keeping descriptions identical to the catalog (add descriptions for the events that had none). `[LICENSE](LICENSE)` becomes the absolute GitHub URL. `examples/README.md` docs link and `pyproject.toml` `Documentation` URL become the new site.

- [ ] **Step 2: Verify links against the build**

Run a Node one-liner (as in the Node repo audit) that extracts every `https://ttl.docs.isaackogan.com` link from `README.md`, maps it to `docs/dist/<path>/index.html`, and asserts the file exists and contains `id="<anchor>"`; also assert `grep -c '](docs/\|](LICENSE)' README.md` is 0.
Expected: `problems: 0`, and `python scripts/check_content.py` still prints `PASS readme`.

- [ ] **Step 3: Commit**

```bash
git add README.md examples/README.md pyproject.toml
git commit -m "docs: point README and package metadata at the hosted documentation"
```

### Task 11: GitHub Pages redirect shell

**Files:**
- Create: `docs/scripts/gen_redirects.py`, `docs/scripts/tests/test_gen_redirects.py`

**Interfaces:**
- Produces: `NEW_BASE = "https://ttl.docs.isaackogan.com/"`; `REDIRECT_MAP: dict[str, str]` = `{"index.html": "", "TikTokLive.html": "api/", "modules.html": "api/", "TikTokLive.client.html": "api/tiktoklive/client/", "TikTokLive.client.web.html": "api/tiktoklive/client/web/", "TikTokLive.client.web.routes.html": "api/tiktoklive/client/web/routes/", "TikTokLive.client.ws.html": "api/tiktoklive/client/ws/", "TikTokLive.events.html": "events/", "TikTokLive.proto.html": "schema/", "genindex.html": "api/", "py-modindex.html": "api/", "search.html": ""}`; `redirect_page(target: str) -> str` (HTML with `<meta http-equiv="refresh" content="0; url=TARGET">`, `<link rel="canonical" href="TARGET">`, `<meta name="robots" content="noindex">`, a visible link); `main(out_dir: str) -> int` writing every mapped file, `404.html` targeting `NEW_BASE`, `.nojekyll`, and `google93ecefd594fb7167.html` copied from `docs/public/`.
- Consumed by Task 12's workflow (`python docs/scripts/gen_redirects.py docs/redirects`).

- [ ] **Step 1: Write failing tests**

```python
def test_every_old_page_is_written(tmp_path):
    gen_redirects.main(str(tmp_path))
    for old in gen_redirects.REDIRECT_MAP:
        assert (tmp_path / old).exists()
    html = (tmp_path / "TikTokLive.client.html").read_text()
    assert 'url=https://ttl.docs.isaackogan.com/api/tiktoklive/client/' in html
    assert 'rel="canonical" href="https://ttl.docs.isaackogan.com/api/tiktoklive/client/"' in html

def test_unknown_old_path_falls_back_to_root(tmp_path):
    gen_redirects.main(str(tmp_path))
    assert 'url=https://ttl.docs.isaackogan.com/' in (tmp_path / "404.html").read_text()
    assert (tmp_path / ".nojekyll").exists() and (tmp_path / "google93ecefd594fb7167.html").exists()
```

- [ ] **Step 2: Run tests to verify they fail**, then **Step 3: implement**, then **Step 4: run tests to verify they pass**

Run: `.venv/bin/python -m pytest docs/scripts/tests/test_gen_redirects.py -v` → first `ModuleNotFoundError`, then `2 passed`.

- [ ] **Step 5: Commit**

```bash
git add docs/scripts/gen_redirects.py docs/scripts/tests/test_gen_redirects.py
git commit -m "docs: generate GitHub Pages redirects to the new site"
```

### Task 12: Worker config, workflow, and first deploy

**Files:**
- Create: `docs/wrangler.jsonc`
- Modify: `.github/workflows/docs.yml`

**Interfaces:**
- Consumes: Tasks 1–11 all green locally.
- Produces: the live site and the CI deploy path. Every step that touches the maintainer's accounts is confirmed with them first.

- [ ] **Step 1: Create `docs/wrangler.jsonc`**

Copy from the Node repo; `name: tiktoklive-docs`, route pattern `ttl.docs.isaackogan.com`, `compatibility_date` today.

- [ ] **Step 2: Rewrite `.github/workflows/docs.yml`**

Triggers: `pull_request` and `push` to `master` with paths `docs/**`, `TikTokLive/**`, `pyproject.toml`, `README.md`, `scripts/seo/**`, `.github/workflows/docs.yml`; `workflow_dispatch`. Permissions `contents: read`, `pages: write`, `id-token: write`. Concurrency `docs-${{ github.ref }}`. Job `build` (env `DEPLOY_ENABLED: ${{ secrets.CLOUDFLARE_API_TOKEN != '' }}`): checkout; `actions/setup-python@v5` 3.12 with pip cache; `pip install -e . -r docs/requirements.txt`; `actions/setup-node@v4` 24; `npm install --global pnpm@10.34.2`; `pnpm --dir docs install --frozen-lockfile`; `python -m pytest docs/scripts/tests`; `pnpm --dir docs build`; `python scripts/seo/verify_seo.py docs/dist`; `python docs/scripts/gen_redirects.py docs/redirects`; `actions/upload-artifact@v4` (`documentation`, `docs/dist`); `actions/upload-pages-artifact@v3` (`docs/redirects`); deploy step `cloudflare/wrangler-action@v4` with `workingDirectory: docs`, `packageManager: pnpm`, `command: deploy`, `if: github.event_name != 'pull_request' && github.ref == 'refs/heads/master' && env.DEPLOY_ENABLED == 'true'`. Job `pages` (`needs: build`, same `if` without the env clause, `environment: github-pages`): `actions/deploy-pages@v4`.

- [ ] **Step 3: Validate the workflow file**

Run: `.venv/bin/python -c "import yaml; d=yaml.safe_load(open('.github/workflows/docs.yml')); print(sorted(d['jobs']))"` (pyyaml is in the `dev` dependency group; `actionlint` if installed is a stronger check)
Expected: `['build', 'pages']`. The pull request run in Step 6 is the real validation.

- [ ] **Step 4: Confirm with the maintainer, then first deploy from this machine**

Run: `cd docs && npx -y pnpm@10.34.2 build && npx -y pnpm@10.34.2 run deploy:cloudflare`
Expected: `Deployed tiktoklive-docs triggers`, `ttl.docs.isaackogan.com (custom domain)`. Then poll until `curl -s -o /dev/null -w '%{http_code}' https://ttl.docs.isaackogan.com/events/` prints `200` (certificate issuance takes a few minutes); also check `/events` → 307 and `/missing/` → 404.

- [ ] **Step 5: Confirm with the maintainer, then set the CI secrets**

The maintainer creates an account-owned token scoped to Editor on `tiktoklive-docs`. Then: `gh secret set CLOUDFLARE_API_TOKEN -R isaackogan/TikTokLive` (value via stdin) and `gh secret set CLOUDFLARE_ACCOUNT_ID -R isaackogan/TikTokLive --body f00699f0017e82344b8bed18c38dab38`. Verify the token with `CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=... npx -y pnpm@10.34.2 --dir docs run deploy:cloudflare` succeeding.

- [ ] **Step 6: Commit and open the pull request**

```bash
git add docs/wrangler.jsonc .github/workflows/docs.yml
git commit -m "docs: deploy the site to Cloudflare Workers and publish redirects to GitHub Pages"
git push -u origin docs/starlight-site
gh pr create --base master --title "docs: Starlight documentation site at ttl.docs.isaackogan.com" --body-file <summary>
```

Expected: the PR's `build` job passes (no deploy on pull requests).

### Task 13: Merge, verify production, and close out

- [ ] **Step 1: Confirm with the maintainer, then merge**

Run: `gh pr merge <n> --merge --delete-branch`, then `gh run watch` the `Documentation` run on `master`.
Expected: `build` and `pages` jobs succeed; `Deploy to Cloudflare Workers` step ran.

- [ ] **Step 2: Verify the live estate**

Run: `curl -sI https://isaackogan.github.io/TikTokLive/TikTokLive.client.html | head -1` and fetch its body
Expected: 200 with `url=https://ttl.docs.isaackogan.com/api/tiktoklive/client/` in the body; `https://ttl.docs.isaackogan.com/sitemap-index.xml` returns 200; `https://ttl.docs.isaackogan.com/robots.txt` contains the `Sitemap:` line; `https://ttl.docs.isaackogan.com/google93ecefd594fb7167.html` returns 200.

- [ ] **Step 3: Hand-offs for the maintainer**

Add the `https://ttl.docs.isaackogan.com/` property in Google Search Console (HTML-file method) and submit `sitemap-index.xml`. Optionally delete the GitHub Pages "Documentation" link in the repository sidebar settings in favour of the new URL.
