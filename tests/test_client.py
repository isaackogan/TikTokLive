import asyncio
from contextlib import suppress
from unittest.mock import AsyncMock

import pytest

from TikTokLive import TikTokLiveClient
from TikTokLive.client.client import _truncate_payload
from TikTokLive.client.errors import AlreadyConnectedError


@pytest.mark.parametrize("shutdown", ["close", "disconnect"])
async def test_async_shutdown_closes_http_without_stopping_other_tasks(shutdown: str) -> None:
    client = TikTokLiveClient(unique_id="@creator")
    unrelated = asyncio.create_task(asyncio.Event().wait())

    try:
        if shutdown == "close":
            await client.close()
        else:
            await client.disconnect(close_client=True)

        assert client.web.httpx_client.is_closed
        assert not unrelated.done()
        assert asyncio.get_running_loop().is_running()
    finally:
        unrelated.cancel()
        with suppress(asyncio.CancelledError):
            await unrelated
        await client.web.close()


async def test_close_drains_the_clients_websocket_task_and_resets_state() -> None:
    client = TikTokLiveClient(unique_id="@creator")
    disconnected = asyncio.Event()
    client._event_loop_task = asyncio.create_task(disconnected.wait())
    client._room_id = 123
    client._room_info = {"status": 2}
    client._gift_info = {"gifts": []}
    client._ws.disconnect = AsyncMock(side_effect=disconnected.set)
    task = client._event_loop_task

    try:
        await client.close()

        client._ws.disconnect.assert_awaited_once_with()
        assert task.done()
        assert client._event_loop_task is None
        assert client.room_id is None
        assert client.room_info is None
        assert client.gift_info is None
        assert client.web.httpx_client.is_closed
    finally:
        disconnected.set()
        await task
        await client.web.close()


async def test_close_still_closes_http_when_websocket_cleanup_fails() -> None:
    client = TikTokLiveClient(unique_id="@creator")
    client._ws.disconnect = AsyncMock(side_effect=RuntimeError("websocket cleanup failed"))

    with pytest.raises(RuntimeError, match="websocket cleanup failed"):
        await client.close()

    assert client.web.httpx_client.is_closed


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
