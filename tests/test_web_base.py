from http.cookiejar import Cookie

from TikTokLive import TikTokLiveClient


def _cookies_named(client: TikTokLiveClient, name: str) -> list[Cookie]:
    return [cookie for cookie in client.web.cookies.jar if cookie.name == name]


def test_default_cookies_are_set_on_the_tiktok_domain() -> None:
    client = TikTokLiveClient(unique_id="@creator")

    (cookie,) = _cookies_named(client, "tt-target-idc")
    assert cookie.domain == ".tiktok.com"
    assert cookie.value == "useast1a"


def test_set_session_overwrites_the_default_tt_target_idc() -> None:
    client = TikTokLiveClient(unique_id="@creator")
    client.web.set_session("session-id", "eu-ttp2")

    (cookie,) = _cookies_named(client, "tt-target-idc")
    assert cookie.value == "eu-ttp2"


def test_httpx_kwargs_cookies_do_not_duplicate_defaults() -> None:
    client = TikTokLiveClient(
        unique_id="@creator",
        web_kwargs={"httpx_kwargs": {"cookies": {"tt-target-idc": "eu-ttp2"}}},
    )

    (cookie,) = _cookies_named(client, "tt-target-idc")
    assert cookie.domain == ".tiktok.com"
    assert cookie.value == "eu-ttp2"
