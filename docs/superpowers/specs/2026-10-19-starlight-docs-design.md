# Starlight Documentation Site for TikTokLive (Python)

**Date:** 2026-10-19
**Status:** Draft, awaiting approval
**Repo:** `isaackogan/TikTokLive`, local checkout `/Users/isaackogan/Documents/PycharmProjects/TikTokLive`
**Reference implementation:** `zerodytrash/TikTok-Live-Connector` branch `docs/cloudflare-workers` (PR #336), live at https://ttlc.docs.isaackogan.com/

## 1. Intent

Give the Python library the same documentation site the Node.js library now has: an Astro Starlight
site with the lucode theme, a generated API reference and protobuf schema reference, content-coverage
checks that fail the build when the docs drift from the code, hosted on Cloudflare Workers static
assets at **https://ttl.docs.isaackogan.com/**, deployed automatically from GitHub Actions.

The maintainer's words: "copy what we did in this repo and add the same docs, end-to-end, for the
TikTokLive python repo. Same scope, just for the Python repo instead."

## 2. Current state (verified 2026-10-19)

- Docs are Sphinx + Furo in `docs/src/` (autodoc `.rst` per module, `index.rst` that includes the
  README), built by `.github/workflows/docs.yml` and deployed to **GitHub Pages at
  https://isaackogan.github.io/TikTokLive/** (returns 200).
- An August 2026 SEO effort (`docs/superpowers/specs/2026-08-17-seo-backlink-design.md`) added
  canonical URLs, `sitemap.xml`, Open Graph tags, dofollow links to eulerstream.com, a Google Search
  Console verification file (`docs/src/extra/google93ecefd594fb7167.html`), and a CI gate
  `scripts/seo/verify_seo.py` that asserts those invariants against the built HTML.
- README (356 lines) documents Getting Started, Parameters, Methods, Properties, WebDefaults, the
  event list (12 custom events, 62 proto events generated from TikTokLiveProto v3), GiftEvent streaks,
  `is_live`, FAQ, Contributors. Its "Documentation" link points at the GitHub Pages URL.
- Public surface: `TikTokLiveClient` (`unique_id`, `platform`, `web_proxy`, `ws_proxy`, `web_kwargs`,
  `ws_kwargs`, `is_user_id`; methods `run`, `start`, `connect`, `disconnect`, `close`, `on`,
  `add_listener`, `has_listener`, `is_live`, `get_avatar_url`, `send_room_chat`, `parse_unique_id`;
  properties `unique_id`, `room_id`, `web`, `connected`, `logger`, `gift_info`, `room_info`),
  11 web routes in `TikTokLive/client/web/routes/`, env vars `SIGN_API_KEY`, `SIGN_API_URL`,
  `SIGN_SERVER_MESSAGE_DISABLED`, `SEND_DEPRECATION_WARNINGS`, `WHITELIST_AUTHENTICATED_SESSION_ID_HOST`
  (the content check must discover these by scanning for every `os.environ` access form, not from
  this list), and `WebDefaults`, a module-level
  instance of the private dataclass `_WebDefaults` in `TikTokLive/client/web/web_settings.py` (the
  content check must read the class's fields, not look for a `WebDefaults` class).
- Version is stamped by `release.yml` into `TikTokLive/__version__.py` and `pyproject.toml`.
- Tooling: Python floor 3.10, mypy in CI, pytest, setuptools. No Node tooling in the repo yet.
- Hostname `ttl.docs.isaackogan.com` has no DNS record. Zone `isaackogan.com` is on Cloudflare in the
  maintainer's account, which already hosts the Node docs Worker.

## 3. Goals

1. A Starlight site in `docs/` that mirrors the Node site's structure, theme, and behaviour.
2. Generated **API reference** (from Python docstrings and signatures) and **Proto schema** reference
   (from the `TikTokLive.proto` bindings), regenerated on every build, never committed.
3. A **content check** that fails the build if any event class, client parameter, public client
   member, `WebDefaults` field, web route, or environment variable is undocumented, and that compiles
   every Python example in the docs.
4. **Hosting** on Cloudflare Workers static assets at `https://ttl.docs.isaackogan.com/`, deployed
   from `docs.yml` on pushes to `master`, validated on pull requests.
5. **README** links point at the hosted site; no repo-relative links remain.
6. **SEO continuity**: the August invariants (canonical, sitemap, Open Graph, dofollow eulerstream
   links, Search Console verification) survive the move, and the old GitHub Pages URLs redirect to
   their new equivalents.
7. Same header affordances as the Node site: GitHub link, Discord link
   (`https://discord.gg/uja6SajDxd`), favicon, "Getting Started" as the root page.

## 4. Non-goals

- Changing library behaviour. Docstring improvements are in scope only where the generator output is
  unreadable without them.
- Internationalisation, blog, versioned docs, or a redesign of the landing page beyond the Getting
  Started page.
- Rewriting `examples/` or the `examples/web-ui` app.
- Touching `release.yml`, `generate.yml`, `lint.yml`, `test.yml`.

## 5. Anti-goals

- **No "tiktok" in any public hostname.** TikTok takes down subdomains containing the mark via
  automated sweeps. `ttl.docs.isaackogan.com` is the only public name. The Worker name is internal.
- **No docs dependencies in the wheel.** Nothing documentation-related enters
  `[project].dependencies` in `pyproject.toml`.
- **No silent SEO regression.** If a canonical tag, sitemap, or dofollow link disappears, the build
  must fail, as it does today.
- **No generated content in Git.** `docs/src/content/docs/api/` and `.../schema/` are build outputs.

## 6. Constraints

- Python 3.10 floor; the docs build in CI uses 3.12 like the existing workflow.
- Node 24, pnpm 10.34.2, and the same pinned versions as the Node site: `astro 7.4.1`,
  `@astrojs/starlight 0.42.6`, `lucode-starlight 1.0.0`, `starlight-links-validator 0.27.0`,
  `wrangler 4.151.2`. Exact pins, no ranges.
- `docs/` must be a self-contained pnpm workspace (own `package.json`, `pnpm-lock.yaml`,
  `pnpm-workspace.yaml`), as in the Node repo.
- The repository `.gitignore` already ignores `dist`; add `docs/node_modules/`, `docs/.astro/`, and the
  generated content directories.
- `docs/superpowers/` stays where it is.

## 7. Design

### 7.1 Site structure (mirrors the Node site)

Sidebar groups and pages:

- **Start here**: Getting Started (root `/`), Connection lifecycle, Migration (v6 → v7: event
  renames, `Gift` field names, removed events, `platform`, `is_user_id`).
- **Configuration**: Client parameters, `WebDefaults`, Environment variables, Signing (Euler Stream,
  `SIGN_API_KEY`, `SIGN_API_URL`), Proxies, Authentication / logged-in sessions.
- **Guides**: Gifts and streaks, Checking if a user is live, Sending chat, Recording streams
  (ffmpeg), Images and avatars, Debugging unknown events (`WebsocketResponseEvent`, `UnknownEvent`).
- **Events**: an index with the full catalog table (event class, proto message, custom vs proto),
  then grouped pages using the Node site's groupings: Chat and audience, Gifts and goals, Battles
  and cohosting, Subscriptions and fans, Room and display, Rankings, Moderation and access, Games and
  commerce, Stream control, Control (connect/disconnect/live end/pause). Each event gets a heading
  whose slug is stable so the README can deep-link to it.
- **Advanced**: Web client and routes, WebSocket layer, Protocol types (schema definition vs
  verified behaviour).
- **Troubleshooting**, **Contributing to the docs**, **Hosting**.
- **API reference** (generated), **Protobuf schema** (generated).

Header: nav links Docs (`/`), Events (`/events/`), API (`/api/`); social links GitHub
(`https://github.com/isaackogan/TikTokLive`) and Discord (`https://discord.gg/uja6SajDxd`).
Footer text: unofficial / not affiliated disclaimer with a GitHub link, as on the Node site.
Favicon: the same `favicon.png` used on the Node site.

### 7.2 API and schema generation (my call)

A Python script `docs/scripts/gen_api.py` uses **griffe** (the static loader behind mkdocstrings,
Sphinx-style docstring parsing) to load `TikTokLive` and `TikTokLive.proto` without importing them,
and renders Starlight Markdown:

- `src/content/docs/api/`: one page per public module, class, and function under `TikTokLive.client`,
  `TikTokLive.events`, and the package root. Page title is the qualified name; sections for signature,
  docstring, parameters, attributes, methods, bases, and "Source" links to GitHub at the stamped
  version's tree. Private members (`_x`) are excluded.
- `src/content/docs/schema/`: one page per protobuf message and enum in the **whole installed
  `TikTokLiveProto.v3` tree**, not only the seven modules `TikTokLive.proto` re-exports (my call).
  This matches the Node site, whose schema section is the full `v3.d.ts`, and guarantees every event
  page can deep-link its proto message (two event parents and many nested field types are not
  reachable through `TikTokLive.proto`). Each page states its import path: `TikTokLive.proto` when
  re-exported there, otherwise the `TikTokLiveProto.v3.<module>` path. Section title
  `TikTok Webcast v3 schema (<TikTokLiveProto version>)` like the Node site.
- Both directories are gitignored and regenerated by `pnpm build` before `astro build`.
- The API reference title carries the package version read from `TikTokLive/__version__.py`.

Why griffe rather than Sphinx-to-Markdown or pydoc-markdown: it handles the proto events
(dataclass multiple inheritance), async methods, and overloads cleanly, needs no import of the
package in the build container, and gives full control over the page layout so the output matches
what `starlight-typedoc` produced for the Node site. The builder may replace it with pydoc-markdown if
griffe's docstring parsing proves unsuitable, but the output contract above stays.

Python dependencies for generation and checking live in `docs/requirements.txt` (griffe, mypy),
installed only in the docs job.

### 7.3 Content check (`docs/scripts/check_content.py`)

Runs before the Astro build and exits non-zero on the first failure:

- Every class in `TikTokLive/events/custom_events.py` and `proto_events.py` appears in backticks
  somewhere in the authored pages, and every proto event appears in the catalog table with its proto
  message name.
- Every parameter of `TikTokLiveClient.__init__`, every public method and property of
  `TikTokLiveClient`, and every field of `WebDefaults` is mentioned in its configuration page.
- Every route module in `TikTokLive/client/web/routes/` is mentioned in the routes page.
- Every `os.environ` key used under `TikTokLive/` is in the environment variables page.
- Every ```` ```python ```` fence in authored pages parses (`ast.parse`) and type-checks with mypy
  against the installed package, matching the Node site's compiled TypeScript examples.
- Proto event descriptions in the catalog are checked against the README's event list so the two do
  not drift (the README stays the PyPI landing page).

### 7.4 Hosting and deployment

- `docs/wrangler.jsonc`: Worker name `tiktoklive-docs`, `assets.directory ./dist`,
  `html_handling auto-trailing-slash`, `not_found_handling 404-page`, `workers_dev false`, custom
  domain route `ttl.docs.isaackogan.com`.
- First deploy from the maintainer's machine with the existing wrangler OAuth login, which attaches
  the custom domain and issues its certificate.
- CI token: a new account-owned Cloudflare token scoped to Editor on `tiktoklive-docs` only, stored as
  `CLOUDFLARE_API_TOKEN` with `CLOUDFLARE_ACCOUNT_ID` in the repo's Actions secrets. The maintainer
  owns this repo, so secrets are set with `gh secret set`.
- Operational steps are performed by the builder, not handed over, with the maintainer's
  confirmation before each consent-bearing action (my call, matching how the Node site was shipped):
  the maintainer creates the scoped token in the Cloudflare dashboard and pastes nothing into chat
  beyond what `gh secret set` needs; the builder sets the secrets, runs the first deploy from the
  maintainer's machine, and publishes the redirect shell; the maintainer adds the Search Console
  property.
- `.github/workflows/docs.yml` is rewritten: on `pull_request` and `push` to `master` with docs/library
  path filters, set up Python 3.12 (`pip install -e .` plus `docs/requirements.txt`), Node 24, pnpm
  10.34.2, run `pnpm --dir docs build`, run the SEO gate against `docs/dist`, upload the artifact, and
  on pushes to `master` deploy with `cloudflare/wrangler-action@v4`. The existing `pages: write` job is
  replaced by the redirect publication in 7.5.

### 7.5 SEO continuity and the old site (my call, see open question 1)

- Starlight's `site` is `https://ttl.docs.isaackogan.com`, giving canonical tags and `sitemap-index.xml`
  for free. Open Graph and Twitter card tags are added through Starlight `head` config with the same
  image and copy as the Sphinx site.
- **Euler Stream link profile (open question, see section 10).** Today's gate requires at least three
  dofollow eulerstream.com links on every page and three distinct anchor texts on the homepage, across
  roughly nine Sphinx pages. The new site has roughly 1,800 pages, most of them generated reference
  pages. Recommended profile: one sitewide dofollow link in the footer (lucode `footerText` accepts
  Markdown, so this is configuration only), plus contextual links on the Getting Started page and the
  signing page, with three distinct anchor texts on the homepage. The gate then asserts one dofollow
  link on every page and three on the homepage, instead of three everywhere.
- `scripts/seo/verify_seo.py` is adapted to the Starlight output: new base URL, sitemap file name,
  canonical on every page, OG tags, no `rel="nofollow"` on eulerstream links, the Search Console file
  present at the root. It stays a required step in `docs.yml`.
- `docs/public/google93ecefd594fb7167.html` is served from the new site so the existing verification
  method works when the maintainer adds the new property in Search Console.
- The GitHub Pages site becomes a redirect shell: `docs/scripts/gen_redirects.py` emits one HTML page
  per old Sphinx URL (`/`, `/TikTokLive.html`, `/TikTokLive.client.html`, ..., `/genindex.html`) with
  `<meta http-equiv="refresh" content="0; url=...">`, a `<link rel="canonical">` to the new URL, and a
  visible link, published to GitHub Pages by the same workflow. Old URLs map to the closest new page
  (module pages to `/api/<module>/`, everything else to `/`).

### 7.6 README

- "Documentation" link and a line under the intro point at `https://ttl.docs.isaackogan.com/`.
- Event names in the README event lists link to their hosted event pages and anchors.
- `LICENSE`, `examples/`, and source links become absolute GitHub URLs; no relative links remain.
- Structure and SEO copy of the README are otherwise unchanged; it remains the PyPI landing page.

### 7.7 Repository changes

- `docs/src/` (Sphinx) is removed. `docs/` becomes the Starlight project: `astro.config.mjs`,
  `package.json`, `pnpm-lock.yaml`, `pnpm-workspace.yaml`, `tsconfig.json`, `wrangler.jsonc`,
  `requirements.txt`, `public/` (favicon, `_redirects`, Search Console file), `scripts/`
  (`gen_api.py`, `check_content.py`, `gen_redirects.py`), `src/content/docs/**`, `README.md`.
- `docs/superpowers/` is kept.
- `.gitignore` gains `docs/node_modules/`, `docs/.astro/`, `docs/src/content/docs/api/`,
  `docs/src/content/docs/schema/`.
- `CONTRIBUTING.md` gains a short "Documentation" section pointing at the docs README.

## 8. Left to the builder

- Exact griffe renderer layout and how overloads, properties, and inherited proto fields render.
- Prose for every authored page, sourced from the README, `examples/`, docstrings, and the Sphinx
  `index.rst`, written in the same register as the Node site.
- Grouping of the 62 proto events into the event pages, using the Node site's groupings as the map.
- Migration guide content (v6 → v7), derived from the README's "New in 7.X.X" list, the Gift alias
  notes, and `git log` for the 7.0.0 release.
- Whether the lucode `docs.includeAiUtilities` option is enabled (off on the Node site).

## 9. Maintainer decisions (2026-10-19)

1. **Sphinx is removed completely.** No Sphinx anywhere in the repo or the build. The existing
   Sphinx pages (`docs/src/index.rst` and the module `.rst` files) and the Node repo's docs are the
   two content sources for the authored prose. The GitHub Pages redirect shell in 7.5 is plain
   generated HTML and does not depend on Sphinx. (Assumption, pending confirmation: GitHub Pages stays
   on, serving only those redirects.)
2. **Worker name** `tiktoklive-docs` is accepted; it is internal.
3. **Discord only in the header button.** The content check carries over the Node rule: no
   `discord.com` / `discord.gg` links in any authored page. The single Discord link is the header
   social button next to GitHub (`https://discord.gg/uja6SajDxd`), configured in `astro.config.mjs`.
4. **Schema scope** (builder's call, 7.2): the full `TikTokLiveProto.v3` tree, with import paths shown.
5. **Operational steps** (builder's call, 7.4): performed by the builder with confirmation before each
   consent-bearing action.

6. **Euler Stream link profile** (maintainer, 2026-10-19): the footer-plus-contextual profile in 7.5.
   The three-per-page sitewide rule is dropped.
7. **Sitemap and robots.** Starlight emits `sitemap-index.xml` and `sitemap-0.xml` for every page and
   links the index from each page head. The site ships `public/robots.txt` with `User-agent: *`,
   `Allow: /`, and a `Sitemap:` line; Cloudflare merges its own content-signals block into it. The SEO
   gate asserts both files exist and that `robots.txt` names the sitemap.
8. **GitHub Pages redirect shell**: kept permanently (builder's default; it costs nothing and keeps the
   old URLs and inbound links working). The maintainer can withdraw this.

## 10. Status

All reviewer questions are resolved. Awaiting the maintainer's approval of this document before the
implementation plan is written.
