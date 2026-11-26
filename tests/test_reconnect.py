import asyncio
from typing import Any, List, Optional
from unittest.mock import AsyncMock

import httpx
import pytest
from websockets.exceptions import ConnectionClosedError

from IgniteLiveAPI import IgniteLiveClient
from IgniteLiveAPI.client.errors import (
    IdleTimeoutError,
    ReconnectFailedError,
    SignatureRateLimitError,
    WebcastBlockedError,
)
from IgniteLiveAPI.client.reconnect import ReconnectPolicy
from IgniteLiveAPI.events import ConnectEvent, DisconnectEvent, ReconnectEvent
from IgniteLiveAPI.proto import ProtoMessageFetchResult

FAST = ReconnectPolicy(max_attempts=3, base_delay=0, max_delay=0, jitter=0)


def _closed() -> ConnectionClosedError:
    return ConnectionClosedError(None, None)


# ------------------------------------------------------------------ ReconnectPolicy


def test_delay_grows_exponentially_and_is_capped() -> None:
    policy = ReconnectPolicy(base_delay=2, multiplier=2, max_delay=10, jitter=0)

    assert [policy.delay(n) for n in (1, 2, 3, 4, 5)] == [2, 4, 8, 10, 10]


def test_delay_jitter_stays_within_bounds() -> None:
    policy = ReconnectPolicy(base_delay=10, max_delay=10, jitter=0.25)

    assert policy.delay(1, rand=lambda: 0.0) == pytest.approx(7.5)
    assert policy.delay(1, rand=lambda: 0.5) == pytest.approx(10.0)
    assert policy.delay(1, rand=lambda: 1.0) == pytest.approx(12.5)


def test_exhausted_respects_max_attempts_and_none_means_forever() -> None:
    assert not ReconnectPolicy(max_attempts=2).exhausted(2)
    assert ReconnectPolicy(max_attempts=2).exhausted(3)
    assert not ReconnectPolicy(max_attempts=None).exhausted(10 ** 9)


@pytest.mark.parametrize(
    "kwargs",
    [{"max_attempts": 0}, {"base_delay": -1}, {"base_delay": 5, "max_delay": 1}, {"multiplier": 0.5}, {"jitter": 1.0}, {"stable_after": -1}],
)
def test_invalid_policies_are_rejected(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        ReconnectPolicy(**kwargs)


@pytest.mark.parametrize(("value", "expected"), [(False, None), (None, None), (True, ReconnectPolicy())])
def test_reconnect_argument_is_normalised(value: Any, expected: Optional[ReconnectPolicy]) -> None:
    assert IgniteLiveClient._resolve_reconnect_policy(value) == expected


def test_a_custom_policy_is_used_as_given() -> None:
    assert IgniteLiveClient._resolve_reconnect_policy(FAST) is FAST


async def test_start_validates_idle_timeout_before_touching_the_network() -> None:
    client = IgniteLiveClient(unique_id="@creator")
    client._web.fetch_room_id_from_html = AsyncMock()  # type: ignore[method-assign]

    with pytest.raises(ValueError, match="idle_timeout"):
        await client.start(idle_timeout=0)

    client._web.fetch_room_id_from_html.assert_not_called()


# ------------------------------------------------------------------ supervisor


class Harness:
    """A client whose connections are scripted: each entry is an exception to raise, or None for a clean close.
    ``stop_after`` makes the client behave as if ``disconnect()`` was called once that many connections have run."""

    def __init__(self, script: List[Optional[Exception]], live: bool = True, stop_after: Optional[int] = None) -> None:
        self.client = IgniteLiveClient(unique_id="@creator")
        self.client._room_id = 123
        self.client._wake = asyncio.Event()
        self.script = list(script)
        self.run_calls: List[dict] = []
        self.events: List[Any] = []

        async def run_connection(**kwargs: Any) -> None:
            self.run_calls.append(kwargs)
            try:
                outcome = self.script.pop(0)
                if outcome is not None:
                    raise outcome
            finally:
                if stop_after is not None and len(self.run_calls) >= stop_after:
                    self.client._stop_requested = True

        self.client._run_connection = run_connection  # type: ignore[method-assign]
        self.client._web.fetch_is_live = AsyncMock(return_value=live)  # type: ignore[method-assign]
        self.client._web.fetch_signed_websocket = AsyncMock(  # type: ignore[method-assign]
            side_effect=lambda *_: ProtoMessageFetchResult(is_first=True)
        )

        for event_type in (ReconnectEvent, DisconnectEvent, ConnectEvent):
            self.client.on(event_type)(self.events.append)

    async def run(self, policy: Optional[ReconnectPolicy] = FAST, idle_timeout: Optional[float] = None) -> None:
        await self.client._ws_client_loop(
            ProtoMessageFetchResult(is_first=True),
            process_connect_events=True,
            compress_ws_events=True,
            reconnect=policy,
            idle_timeout=idle_timeout,
        )

    def of_type(self, event_type: type) -> list:
        return [e for e in self.events if isinstance(e, event_type)]


async def test_reconnects_after_a_dropped_connection_then_stops_on_request() -> None:
    h = Harness([_closed(), None], stop_after=2)

    await h.run()

    assert len(h.run_calls) == 2
    (reconnect,) = h.of_type(ReconnectEvent)
    assert reconnect.attempt == 1 and "ConnectionClosedError" in reconnect.reason
    assert len(h.of_type(DisconnectEvent)) == 1
    h.client._web.fetch_is_live.assert_awaited_once_with(room_id=123)
    h.client._web.fetch_signed_websocket.assert_awaited_once()


async def test_history_is_not_replayed_on_reconnect() -> None:
    h = Harness([_closed(), None], stop_after=2)

    await h.run()

    assert [call["process_connect_events"] for call in h.run_calls] == [True, False]


async def test_a_clean_close_that_was_not_requested_also_reconnects() -> None:
    h = Harness([None, None], stop_after=2)

    await h.run()

    assert len(h.run_calls) == 2
    assert h.of_type(ReconnectEvent)[0].reason == "connection closed"


async def test_gives_up_after_max_attempts_with_the_last_failure_as_cause() -> None:
    h = Harness([_closed()])
    h.client._web.fetch_signed_websocket = AsyncMock(side_effect=httpx.ConnectError("sign server down"))  # type: ignore[method-assign]

    with pytest.raises(ReconnectFailedError, match="after 3 attempts") as info:
        await h.run()

    assert isinstance(info.value.__cause__, httpx.ConnectError)
    assert [e.attempt for e in h.of_type(ReconnectEvent)] == [1, 2, 3]
    assert h.client._web.fetch_signed_websocket.await_count == 3
    assert h.of_type(DisconnectEvent) == []


async def test_attempt_budget_resets_after_a_stable_connection() -> None:
    # Every connection "stays up" (stable_after=0), so a budget of 1 attempt is never used up by the earlier drops.
    policy = ReconnectPolicy(max_attempts=1, base_delay=0, max_delay=0, jitter=0, stable_after=0)
    h = Harness([_closed(), _closed(), _closed(), None], stop_after=4)

    await h.run(policy)

    assert len(h.run_calls) == 4
    assert [e.attempt for e in h.of_type(ReconnectEvent)] == [1, 1, 1]


@pytest.mark.parametrize("fatal", [WebcastBlockedError("blocked"), ValueError("a bug")])
async def test_failures_that_retrying_cannot_fix_are_raised_immediately(fatal: Exception) -> None:
    h = Harness([fatal])

    with pytest.raises(type(fatal)):
        await h.run()

    assert len(h.run_calls) == 1
    assert h.of_type(ReconnectEvent) == []


async def test_without_a_policy_failures_propagate_and_a_clean_close_disconnects() -> None:
    failing = Harness([_closed()])
    with pytest.raises(ConnectionClosedError):
        await failing.run(policy=None)
    assert failing.of_type(ReconnectEvent) == []

    clean = Harness([None])
    await clean.run(policy=None)
    assert len(clean.run_calls) == 1
    assert len(clean.of_type(DisconnectEvent)) == 1


async def test_ends_quietly_when_the_stream_is_no_longer_live() -> None:
    h = Harness([_closed()], live=False)

    await h.run()

    assert len(h.run_calls) == 1
    h.client._web.fetch_signed_websocket.assert_not_called()  # no signature wasted on an offline room
    assert len(h.of_type(DisconnectEvent)) == 1


async def test_disconnect_interrupts_the_backoff_sleep() -> None:
    slow = ReconnectPolicy(max_attempts=3, base_delay=30, max_delay=30, jitter=0)
    h = Harness([_closed()])
    h.client._ws.disconnect = AsyncMock()  # type: ignore[method-assign]

    task = asyncio.create_task(h.run(slow))
    await asyncio.sleep(0.05)
    assert h.of_type(ReconnectEvent), "should be sleeping between attempts"

    await h.client.disconnect()
    await asyncio.wait_for(task, timeout=2)  # would take 30s if the sleep were not interruptible

    assert len(h.run_calls) == 1
    assert len(h.of_type(DisconnectEvent)) == 1


async def test_rate_limit_responses_extend_the_delay() -> None:
    h = Harness([_closed()], stop_after=2)
    rate_limited = SignatureRateLimitError(
        None, "Try again in %s seconds.", response=httpx.Response(429, headers={"RateLimit-Remaining": "7"})
    )
    h.client._web.fetch_signed_websocket = AsyncMock(  # type: ignore[method-assign]
        side_effect=[rate_limited, ProtoMessageFetchResult(is_first=True)]
    )

    delays: List[float] = []

    async def sleep(delay: float) -> bool:
        delays.append(delay)
        return False

    h.client._sleep_unless_stopped = sleep  # type: ignore[method-assign]
    h.script.append(None)
    await h.run()

    assert delays == [0, 7]  # ordinary backoff after the drop, then the server's requested wait after the 429


# ------------------------------------------------------------------ idle watchdog against a real socket


async def _serve(handler: Any) -> Any:
    from websockets.legacy.server import serve

    server = await serve(handler, "127.0.0.1", 0, subprotocols=["echo-protocol"])
    port = server.sockets[0].getsockname()[1]
    response = ProtoMessageFetchResult(
        cursor="cursor", push_server=f"ws://127.0.0.1:{port}/ws", route_params={"k": "v"}, is_first=True
    )
    return server, response


async def _connect(ws_client: Any, response: ProtoMessageFetchResult, idle_timeout: Optional[float]) -> int:
    count = 0
    async for _ in ws_client.connect(
            room_id=1,
            cookies=httpx.Cookies(),
            user_agent="test",
            initial_webcast_response=response,
            idle_timeout=idle_timeout,
    ):
        count += 1
    return count


async def test_watchdog_drops_a_silent_connection_and_cleans_up() -> None:
    from IgniteLiveAPI.client.ws.ws_client import WebcastWSClient

    async def silent(ws: Any) -> None:
        await ws.wait_closed()  # accepts the connection, then never sends a frame

    server, response = await _serve(silent)
    ws_client = WebcastWSClient()

    try:
        with pytest.raises(IdleTimeoutError):
            await asyncio.wait_for(_connect(ws_client, response, idle_timeout=0.4), timeout=15)
    finally:
        server.close()
        await server.wait_closed()

    assert ws_client._ping_loop is None and ws_client._watchdog is None
    assert not ws_client.connected


async def test_heartbeat_frames_count_as_activity() -> None:
    from IgniteLiveAPI.client.ws.ws_client import WebcastWSClient
    from IgniteLiveAPI.proto import WebcastPushFrame

    async def heartbeats(ws: Any) -> None:
        # Transport-level frames only (no "msg"), for twice the idle timeout, then a normal close
        for _ in range(8):
            await ws.send(bytes(WebcastPushFrame(payload_type="hb", payload_encoding="pb", payload=b"")))
            await asyncio.sleep(0.1)
        await ws.close()

    server, response = await _serve(heartbeats)
    ws_client = WebcastWSClient()

    try:
        # Total lifetime (~0.8s) is twice the idle timeout, so only per-frame activity tracking keeps it alive
        count = await asyncio.wait_for(_connect(ws_client, response, idle_timeout=0.4), timeout=15)
    finally:
        server.close()
        await server.wait_closed()

    assert count == 1  # only the initial response; heartbeats are not events


async def test_watchdog_is_off_by_default() -> None:
    from IgniteLiveAPI.client.ws.ws_client import WebcastWSClient

    async def brief(ws: Any) -> None:
        await asyncio.sleep(0.6)
        await ws.close()

    server, response = await _serve(brief)
    ws_client = WebcastWSClient()

    try:
        await asyncio.wait_for(_connect(ws_client, response, idle_timeout=None), timeout=15)
    finally:
        server.close()
        await server.wait_closed()

    assert ws_client._watchdog is None


async def test_non_positive_idle_timeout_is_rejected_by_the_ws_client() -> None:
    from IgniteLiveAPI.client.ws.ws_client import WebcastWSClient

    with pytest.raises(ValueError, match="idle_timeout"):
        await _connect(WebcastWSClient(), ProtoMessageFetchResult(), idle_timeout=-1)
