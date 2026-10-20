import gen_redirects


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
