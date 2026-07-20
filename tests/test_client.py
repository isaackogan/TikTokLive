from unittest.mock import AsyncMock

import pytest

from TikTokLive import TikTokLiveClient
from TikTokLive.client.client import _truncate_payload
from TikTokLive.client.errors import AlreadyConnectedError


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("@creator", "creator"),
        ("creator", "creator"),
        ("https://www.tiktok.com/@creator/live", "creator"),
        (123456789, "123456789"),
    ],
)
def test_parse_unique_id(value: str | int, expected: str) -> None:
    assert TikTokLiveClient.parse_unique_id(value) == expected


async def test_is_live_resolves_the_requested_user_id() -> None:
    client = TikTokLiveClient(unique_id="@original")
    client._resolve_user_id = AsyncMock(return_value="resolved_creator")
    client.web.fetch_is_live = AsyncMock(return_value=True)

    assert await client.is_live("@requested") is True
    client._resolve_user_id.assert_awaited_once_with("@requested")
    client.web.fetch_is_live.assert_awaited_once_with(unique_id="resolved_creator")
    assert client.unique_id == "resolved_creator"


async def test_start_rejects_a_second_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TikTokLiveClient(unique_id="@creator")
    monkeypatch.setattr(type(client._ws), "connected", property(lambda _: True))

    with pytest.raises(AlreadyConnectedError, match="one connection"):
        await client.start()


def test_truncate_payload_preserves_short_payloads() -> None:
    assert _truncate_payload(b"payload") == "b'payload'"


def test_truncate_payload_reports_omitted_bytes() -> None:
    payload = b"a" * 33

    assert _truncate_payload(payload) == "b'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'...(+1 more bytes)"
