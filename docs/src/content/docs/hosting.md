---
title: Cloudflare Workers hosting
description: Host the static documentation on Cloudflare Workers static assets under a custom domain, deploy it from CI or a checkout, gate it on SEO checks, and redirect the old GitHub Pages site.
---

The site is deployed to Cloudflare Workers as static assets and served at `https://ttl.docs.isaackogan.com/`. Hosting lives in a maintainer's Cloudflare account while the documentation source stays in the public repository. There is no Worker script: `docs/wrangler.jsonc` only declares the asset directory, HTML handling, and the custom domain. The site needs no Pages Functions, no Cloudflare Astro adapter, and no TikTok or signing credentials.

## Configuration

```jsonc
{
  "name": "tiktoklive-docs",
  "compatibility_date": "2026-10-19",
  "assets": {
    "directory": "./dist",
    "html_handling": "auto-trailing-slash",
    "not_found_handling": "404-page"
  },
  "workers_dev": false,
  "routes": [
    { "pattern": "ttl.docs.isaackogan.com", "custom_domain": true }
  ]
}
```

- `html_handling: auto-trailing-slash` matches Astro's `trailingSlash: 'always'`. A request for `/events` redirects to `/events/`, which serves `events/index.html`.
- `not_found_handling: 404-page` serves Starlight's generated `404.html` with a 404 status.
- `workers_dev: false` keeps the site off the `workers.dev` hostname so the custom domain is the only public origin.
- The `routes` entry with `custom_domain: true` makes Cloudflare create the DNS record and the certificate for the hostname on deploy. The `isaackogan.com` zone must be in the same Cloudflare account as the Worker, and the hostname must not already have a DNS record.

`DOCS_SITE` overrides the canonical origin and defaults to the custom domain. `DOCS_BASE` sets the deployment subpath and defaults to `/`. Neither needs to be set for a production build.

See Cloudflare's [static assets](https://developers.cloudflare.com/workers/static-assets/) and [custom domains](https://developers.cloudflare.com/workers/configuration/routing/custom-domains/) documentation for the underlying behaviour.

## Build inputs

The build needs both toolchains, because the reference pages are generated from the installed library and the examples are type-checked against it:

- Python 3.10 or newer with `pip install -e . -r docs/requirements.txt` in the repository's virtual environment (`griffe` and `mypy`).
- Node.js 24 and pnpm 10.34.2 with `pnpm --dir docs install --frozen-lockfile`.

The [contributing page](/contributing/) has the full setup and the commands.

## Deploy from a checkout

Wrangler is pinned in `docs/package.json`, so the documentation install provides it. Run `pnpm --dir docs exec wrangler login` once on a new machine; the login is an OAuth session in the maintainer's account.

```sh
source .venv/bin/activate
pnpm --dir docs install --frozen-lockfile
pnpm --dir docs build
pnpm --dir docs run deploy:cloudflare
```

The first deploy creates the Worker and attaches the custom domain; wrangler reports `Deployed tiktoklive-docs triggers` and `ttl.docs.isaackogan.com (custom domain)`, and the certificate takes a few minutes to issue. Later deploys upload only the files that changed.

## Continuous deployment

`.github/workflows/docs.yml` runs on pull requests and on pushes to `master` that touch `docs/`, `TikTokLive/`, `pyproject.toml`, `README.md`, `scripts/seo/`, or the workflow itself, and can be started by hand with `workflow_dispatch`. One run at a time per ref: the concurrency group is `docs-${{ github.ref }}`.

The `build` job sets up Python 3.12 with `pip install -e . -r docs/requirements.txt`, Node.js 24 with `npm install --global pnpm@10.34.2`, and `pnpm --dir docs install --frozen-lockfile`; then it runs `python -m pytest docs/scripts/tests`, `pnpm --dir docs build`, the SEO gate `python scripts/seo/verify_seo.py docs/dist`, and `python docs/scripts/gen_redirects.py docs/redirects`; uploads `docs/dist` as the `documentation` artifact for review and `docs/redirects` as the Pages artifact; and, on a push to `master`, deploys with `cloudflare/wrangler-action@v4` (`workingDirectory: docs`, `packageManager: pnpm`, `command: deploy`). The deploy step runs only when the repository has two Actions secrets:

| Secret | Value |
| --- | --- |
| `CLOUDFLARE_API_TOKEN` | An account-owned token scoped to Editor on the `tiktoklive-docs` Worker only. |
| `CLOUDFLARE_ACCOUNT_ID` | The hosting account's ID, shown by `wrangler whoami`. |

Without the secrets the deploy step is skipped and the workflow still validates the build, so forks and pull requests are unaffected. The maintainer sets them with `gh secret set CLOUDFLARE_API_TOKEN -R isaackogan/TikTokLive` and `gh secret set CLOUDFLARE_ACCOUNT_ID -R isaackogan/TikTokLive`; a token is verified by running `pnpm --dir docs run deploy:cloudflare` with `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` in the environment.

The `pages` job, after `build` and under the same push-to-`master` condition, publishes the Pages artifact with `actions/deploy-pages@v4` to the `github-pages` environment; that is the redirect shell described below, not the site.

## SEO gate

`scripts/seo/verify_seo.py docs/dist` runs after every build in CI and prints a `PASS` line per check and a `passed, failed` summary; any failure fails the workflow. The checks are the invariants the previous site carried: the homepage `<title>` contains `TikTok LIVE API`; every page has a `rel="canonical"` link on `https://ttl.docs.isaackogan.com/`; the homepage has `og:title`, `og:description`, `og:image`, and a meta description; `sitemap-index.xml` and `sitemap-0.xml` exist, the latter on the custom domain with more than one URL; `robots.txt` names the sitemap; the Search Console verification file `google93ecefd594fb7167.html` is present; no link to [Euler Stream](https://www.eulerstream.com/) is nofollowed, every page has at least one, and the homepage has at least three distinct anchor texts; and every page carries the theme's sidebar marker, so a theme change that drops the navigation is caught. The gate's tests are in `docs/scripts/tests/test_verify_seo.py`.

The Open Graph and Twitter card tags come from `head` in `docs/astro.config.mjs`; `robots.txt` and the verification file are in `docs/public/`; the sitemap is generated from `site`.

## Redirects from the old site

The previous documentation was a Sphinx site on GitHub Pages at `https://isaackogan.github.io/TikTokLive/`. That origin now serves a redirect shell generated by `docs/scripts/gen_redirects.py` into `docs/redirects/`, which is ignored by Git and published by the `pages` job on every deploy. Each old page becomes an HTML file with a `<meta http-equiv="refresh">` to its new URL, a `rel="canonical"` link to the same URL, a `noindex` robots tag, and a visible link:

| Old page | New URL |
| --- | --- |
| `index.html`, `search.html` | `/` |
| `TikTokLive.html`, `modules.html`, `genindex.html`, `py-modindex.html` | `/api/` |
| `TikTokLive.client.html` | `/api/tiktoklive/client/` |
| `TikTokLive.client.web.html` | `/api/tiktoklive/client/web/` |
| `TikTokLive.client.web.routes.html` | `/api/tiktoklive/client/web/routes/` |
| `TikTokLive.client.ws.html` | `/api/tiktoklive/client/ws/` |
| `TikTokLive.events.html` | `/events/` |
| `TikTokLive.proto.html` | `/schema/` |

The shell also has a `404.html` that sends any other old path to the new root, a `.nojekyll` file, and a copy of the Search Console verification file, so the old property stays verified while it redirects. The script's tests are in `docs/scripts/tests/test_gen_redirects.py`.

## Verify a deployment

```sh
curl -I https://ttl.docs.isaackogan.com/events/
curl -I https://ttl.docs.isaackogan.com/events
curl -I https://ttl.docs.isaackogan.com/missing/
```

Expect a 200, a 307 redirect to the trailing-slash form, and a 404 in that order. Then open the site, check an event page and the generated API and schema pages, and search for a gift event. The canonical link in the page head must use the custom domain, and `https://isaackogan.github.io/TikTokLive/TikTokLive.client.html` must land on the new client module page.

## Changing the hostname

Edit `pattern` in `docs/wrangler.jsonc`, change the default `site` in `docs/astro.config.mjs`, update `BASE_URL` in `scripts/seo/verify_seo.py` and `NEW_BASE` in `docs/scripts/gen_redirects.py`, update the hosted links in the repository README and `pyproject.toml`, and deploy. Cloudflare provisions the new hostname on the next deploy. Remove the old one under the Worker's **Settings → Domains & Routes** in the Cloudflare dashboard.
