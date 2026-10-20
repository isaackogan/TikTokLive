# Contributing to TikTokLive

Thank you for taking the time to contribute. TikTok LIVE changes frequently,
so focused fixes, reproducible reports, and regression tests are especially
valuable.

## Development setup

TikTokLive supports Python 3.10 through 3.12. Create and activate a virtual
environment, then install the package with the test dependencies:

```shell
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
```

Run the test suite before opening a pull request:

```shell
python -m pytest
```

The existing type-checking workflow can be run locally with:

```shell
python -m pip install "mypy>=1.10" types-PyYAML jinja2 pyyaml
python -m mypy --follow-imports=silent TikTokLive scripts/proto
```

## Pull requests

- Keep each pull request focused on one behavior change.
- Add or update a regression test for every bug fix when the behavior can be
  reproduced without contacting TikTok.
- Do not add live account credentials, session cookies, or unredacted request
  headers to source files, tests, issues, or pull request descriptions.
- Explain any behavior that depends on an observed TikTok protocol change and
  include a minimal, sanitized fixture when possible.
- Update the README and the documentation site (see Documentation below)
  when a public API changes.

## Reporting protocol changes

TikTok protocol changes are most useful when reported with the package version,
Python version, operating system, the affected event or route, and a sanitized
stack trace. Avoid attaching complete WebSocket payloads unless all account,
cookie, and personally identifiable data has been removed.

## Generated files

`TikTokLive/events/proto_events.py` and `TikTokLive/proto/_aliases.py` are
generated from the scripts under `scripts/proto/`. If a change affects their
inputs, regenerate both files and include the generated diff in the same pull
request.

## Documentation

The documentation site under `docs/` is a Starlight project whose reference
pages are generated from the library and whose content check fails the build
when a page drifts from the code. Build it from a checkout with the library
installed in the repository's virtual environment:

```shell
pip install -e . -r docs/requirements.txt
npx -y pnpm@10.34.2 --dir docs install --frozen-lockfile
npx -y pnpm@10.34.2 --dir docs build
```

`pnpm --dir docs check` runs only the content check, `generate` only the
reference generator, and `dev` the local server. See `docs/README.md` and the
site's contributing page for the authoring rules: Python examples are complete
modules that type-check, pages carry no Discord links, and the generated
`api/` and `schema/` directories are never committed.
