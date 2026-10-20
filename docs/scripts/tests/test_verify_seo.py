"""Exercise the SEO gate against a minimal on-disk Starlight-shaped site.

``write_fixture_site`` writes real HTML, XML and text files that satisfy every
invariant the gate enforces; the keyword overrides break exactly one of them.
"""

from pathlib import Path

import verify_seo

BASE = "https://ttl.docs.isaackogan.com/"
DEFAULT_ROBOTS = f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap-index.xml\n"
EULER_LINK = '<a href="https://www.eulerstream.com/">Euler Stream</a>'


def _page(path_segment: str, title: str, body_links: str, *, head_extra: str = "") -> str:
    return (
        "<!DOCTYPE html><html lang=\"en\"><head>"
        f"<title>{title}</title>"
        f'<link rel="canonical" href="{BASE}{path_segment}"/>'
        f"{head_extra}"
        "</head><body>"
        f'<nav><ul class="sidebar-entries"><li><a href="/">Home</a></li></ul></nav>'
        f"<main>{body_links}</main>"
        "</body></html>"
    )


def write_fixture_site(
    tmp_path: Path,
    *,
    nested_euler_links: int = 1,
    robots: str = DEFAULT_ROBOTS,
) -> Path:
    homepage_head = (
        '<meta property="og:title" content="TikTokLive"/>'
        '<meta property="og:description" content="TikTok LIVE API for Python"/>'
        '<meta property="og:image" content="https://example.com/logo.png"/>'
        '<meta name="description" content="TikTok LIVE API for Python"/>'
    )
    homepage_links = (
        '<a href="https://www.eulerstream.com/">TikTok LIVE signing API</a>'
        '<a href="https://www.eulerstream.com/websockets">TikTok LIVE WebSocket API</a>'
        '<a href="https://www.eulerstream.com/docs">Euler Stream documentation</a>'
        + EULER_LINK
    )
    (tmp_path / "index.html").write_text(
        _page("", "TikTok LIVE API for Python: TikTokLive Documentation", homepage_links,
              head_extra=homepage_head),
        encoding="utf-8",
    )

    nested = tmp_path / "guides" / "x"
    nested.mkdir(parents=True)
    (nested / "index.html").write_text(
        _page("guides/x/", "Guide X | TikTokLive", EULER_LINK * nested_euler_links),
        encoding="utf-8",
    )

    (tmp_path / "404.html").write_text(
        _page("404/", "Page not found | TikTokLive", EULER_LINK), encoding="utf-8"
    )

    (tmp_path / "sitemap-index.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<sitemap><loc>{BASE}sitemap-0.xml</loc></sitemap></sitemapindex>",
        encoding="utf-8",
    )
    (tmp_path / "sitemap-0.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{BASE}</loc></url><url><loc>{BASE}guides/x/</loc></url></urlset>",
        encoding="utf-8",
    )
    (tmp_path / "robots.txt").write_text(robots, encoding="utf-8")
    (tmp_path / "google93ecefd594fb7167.html").write_text(
        "google-site-verification: google93ecefd594fb7167.html", encoding="utf-8"
    )
    return tmp_path


def _fail_lines(captured: str) -> list[str]:
    return [line for line in captured.splitlines() if line.startswith("FAIL")]


def test_gate_passes_on_fixture_site(tmp_path, capsys):
    write_fixture_site(tmp_path)
    assert verify_seo.main(str(tmp_path)) == 0
    assert _fail_lines(capsys.readouterr().out) == []


def test_gate_fails_when_nested_page_lacks_euler_link(tmp_path, capsys):
    write_fixture_site(tmp_path, nested_euler_links=0)
    assert verify_seo.main(str(tmp_path)) == 1
    fails = _fail_lines(capsys.readouterr().out)
    assert len(fails) == 1 and "eulerstream.com linked from every page" in fails[0]
    assert "guides/x/index.html" in fails[0]


def test_gate_fails_when_robots_has_no_sitemap(tmp_path, capsys):
    write_fixture_site(tmp_path, robots="User-agent: *\nAllow: /\n")
    assert verify_seo.main(str(tmp_path)) == 1
    fails = _fail_lines(capsys.readouterr().out)
    assert len(fails) == 1 and "robots.txt" in fails[0]
