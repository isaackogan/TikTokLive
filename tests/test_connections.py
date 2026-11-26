import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from IgniteLiveAPI import IgniteLiveClient
from IgniteLiveAPI.client.errors import UserOfflineError
from IgniteLiveAPI.client.web.web_settings import DEFAULT_HTTP_LIMITS, DEFAULT_HTTP_TIMEOUT
from IgniteLiveAPI.client.web.web_signer import TikTokSigner


def _keepalive_expiry(client: IgniteLiveClient) -> float | None:
    return client.web.httpx_client._transport._pool._keepalive_expiry  # type: ignore[attr-defined]


def test_http_client_keeps_connections_alive_longer_than_httpx_default() -> None:
    client = IgniteLiveClient(unique_id="@creator")

    assert _keepalive_expiry(client) == DEFAULT_HTTP_LIMITS.keepalive_expiry == 30.0
    assert client.web.httpx_client.timeout == DEFAULT_HTTP_TIMEOUT


def test_http_client_limits_and_timeout_can_be_overridden() -> None:
    client = IgniteLiveClient(
        unique_id="@creator",
        web_kwargs={"httpx_kwargs": {"limits": httpx.Limits(keepalive_expiry=2.0), "timeout": httpx.Timeout(3.0)}},
    )

    assert _keepalive_expiry(client) == 2.0
    assert client.web.httpx_client.timeout == httpx.Timeout(3.0)


def test_signer_verifies_tls_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SIGN_API_VERIFY_SSL", raising=False)

    assert TikTokSigner().sdk_client._verify_ssl is True


@pytest.mark.parametrize("value", ["false", "0", "off", "NO"])
def test_signer_tls_verification_can_be_disabled_explicitly(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("SIGN_API_VERIFY_SSL", value)

    assert TikTokSigner().sdk_client._verify_ssl is False


def _stub_start_dependencies(client: IgniteLiveClient) -> None:
    client._web.fetch_room_id_from_html = AsyncMock(return_value="123")  # type: ignore[method-assign]
    client._web.fetch_is_live = AsyncMock(return_value=True)  # type: ignore[method-assign]
    client._ws_client_loop = AsyncMock(return_value=None)  # type: ignore[method-assign]


async def test_start_runs_the_optional_and_signing_fetches_concurrently() -> None:
    client = IgniteLiveClient(unique_id="@creator")
    _stub_start_dependencies(client)

    in_flight: set[str] = set()
    all_in_flight = asyncio.Event()

    def slow(name: str, result: object) -> AsyncMock:
        async def fetch(*_args: object, **_kwargs: object) -> object:
            in_flight.add(name)
            if len(in_flight) == 3:
                all_in_flight.set()
            # Only completes if the other two requests started while this one is pending
            await asyncio.wait_for(all_in_flight.wait(), timeout=2)
            return result

        return AsyncMock(side_effect=fetch)

    client._web.fetch_room_info = slow("room_info", {"id": 1})  # type: ignore[method-assign]
    client._web.fetch_gift_list = slow("gifts", {"gifts": []})  # type: ignore[method-assign]
    client._web.fetch_signed_websocket = slow("sign", "initial-response")  # type: ignore[method-assign]

    task = await client.start(fetch_room_info=True, fetch_gift_info=True)
    await task

    assert client.room_info == {"id": 1}
    assert client.gift_info == {"gifts": []}
    client._ws_client_loop.assert_awaited_once()
    assert client._ws_client_loop.await_args.kwargs["initial_webcast_response"] == "initial-response"


async def test_start_skips_unrequested_fetches() -> None:
    client = IgniteLiveClient(unique_id="@creator")
    _stub_start_dependencies(client)
    client._web.fetch_room_info = AsyncMock()  # type: ignore[method-assign]
    client._web.fetch_gift_list = AsyncMock()  # type: ignore[method-assign]
    client._web.fetch_signed_websocket = AsyncMock(return_value="initial-response")  # type: ignore[method-assign]

    await (await client.start())

    client._web.fetch_room_info.assert_not_called()
    client._web.fetch_gift_list.assert_not_called()
    assert client.room_info is None and client.gift_info is None


async def test_start_raises_the_first_failure_in_sequential_order() -> None:
    client = IgniteLiveClient(unique_id="@creator")
    _stub_start_dependencies(client)
    client._web.fetch_room_info = AsyncMock(side_effect=ValueError("room info"))  # type: ignore[method-assign]
    client._web.fetch_gift_list = AsyncMock(side_effect=KeyError("gifts"))  # type: ignore[method-assign]
    client._web.fetch_signed_websocket = AsyncMock(side_effect=RuntimeError("sign"))  # type: ignore[method-assign]

    with pytest.raises(ValueError, match="room info"):
        await client.start(fetch_room_info=True, fetch_gift_info=True)

    # The signature failing alone is still surfaced
    client._web.fetch_room_info = AsyncMock(return_value={})  # type: ignore[method-assign]
    with pytest.raises(RuntimeError, match="sign"):
        await client.start(fetch_room_info=True)


async def test_start_does_not_fetch_anything_for_an_offline_user() -> None:
    client = IgniteLiveClient(unique_id="@creator")
    _stub_start_dependencies(client)
    client._web.fetch_is_live = AsyncMock(return_value=False)  # type: ignore[method-assign]
    client._web.fetch_signed_websocket = AsyncMock()  # type: ignore[method-assign]

    with pytest.raises(UserOfflineError):
        await client.start()

    client._web.fetch_signed_websocket.assert_not_called()
