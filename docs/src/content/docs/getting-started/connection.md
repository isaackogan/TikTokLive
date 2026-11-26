---
title: Connection lifecycle
description: Run, start, or connect a client, fetch room and gift information, handle connect, disconnect, and stream-end events, reconnect, and check live status.
---

## Run, start, or connect

`IgniteLiveClient` offers three ways to open a connection. They perform the same steps and accept the same keyword-only options; they differ in what they block.

| Method | Blocks | Returns | Use it when |
| --- | --- | --- | --- |
| `client.run()` | The calling thread, until the connection ends | The finished `asyncio.Task` | A script whose only job is this connection. `Ctrl+C` disconnects cleanly. |
| `await client.connect()` | The calling coroutine, until the connection ends | The finished `asyncio.Task` | Your own `asyncio` program wants to wait for the stream to end. |
| `await client.start()` | Nothing; it returns once the WebSocket loop is scheduled | The running `asyncio.Task` | Your program keeps working while events arrive. Await the task or call `disconnect()` later. |

`connect()` also takes an optional positional `callback`, a function or coroutine run once the connection is up.

Connecting resolves the room ID from the creator's live page, falling back to TikTok's API, checks that the creator is live, requests a signed WebSocket URL from the signing provider, and opens the socket. The first signed response can already carry messages; they are emitted after `ConnectEvent`. One connection per client: calling any of the three while connected raises `AlreadyConnectedError`, and an offline creator raises `UserOfflineError`.

| Option | Default | Effect |
| --- | --- | --- |
| `process_connect_events` | `True` | Emit the messages included in the first signed response. |
| `compress_ws_events` | `True` | Request gzip-compressed WebSocket events. |
| `fetch_room_info` | `False` | Fetch room information before connecting; see below. |
| `fetch_gift_info` | `False` | Fetch the room's gift list before connecting; see below. |
| `fetch_live_check` | `True` | Check that the creator is live first and raise `UserOfflineError` if not. Keep it on. |
| `room_id` | `None` | Connect to this room directly and skip scraping the live page. |
| `reconnect` | `False` | `True`, or a `ReconnectPolicy`, to reconnect automatically when the connection drops; see [automatic reconnect](#automatic-reconnect). |
| `idle_timeout` | `None` | Seconds without receiving any frame before the connection is treated as dead; see [automatic reconnect](#automatic-reconnect). |

## Fetch room and gift information

`fetch_room_info=True` stores the room's metadata on `client.room_info`, and `fetch_gift_info=True` stores the room's gift catalog on `client.gift_info`. Both are plain `dict` objects from TikTok's HTTP API, both are `None` unless requested, and both are reset to `None` by `disconnect()`. Keep your own copy if you need the data after the stream ends. Both requests run at the same time as the signed WebSocket request, so a failure in either one is raised after the signing request has already been made and counted against the provider's rate limit.

```python
import asyncio

from IgniteLiveAPI import IgniteLiveClient

client: IgniteLiveClient = IgniteLiveClient(unique_id="@isaackogz")


async def main() -> None:
    task: asyncio.Task = await client.start(fetch_room_info=True, fetch_gift_info=True)
    print(client.room_id, client.room_info, client.gift_info)
    await task


if __name__ == "__main__":
    asyncio.run(main())
```

## Connect, disconnect, and stream-end events

Four custom events mark the lifecycle. Register them like any other event.

- `ConnectEvent` is emitted when the first signed response is parsed. It carries `unique_id` and `room_id`; `client.room_id` and `client.connected` are set by then.
- `ReconnectEvent` is emitted before each reconnect attempt, only when the client was started with `reconnect=`. It carries `attempt`, `delay` and `reason`.
- `LiveEndEvent` is emitted when TikTok's `ControlEvent` reports `STREAM_ENDED` or `STREAM_SUSPENDED`. The client then disconnects itself. `LivePauseEvent` and `LiveUnpauseEvent` report pauses the same way.
- `DisconnectEvent` is emitted once when the WebSocket loop exits normally: the stream ended, you called `disconnect()`, or TikTok closed the socket with close code 1000 or 1001. A close with any other code, such as a dropped network connection, raises `ConnectionClosedError` from `connect()` or from the task `start()` returned instead, and no `DisconnectEvent` is emitted. The event carries no payload and does not by itself say why.

```python
from IgniteLiveAPI import IgniteLiveClient
from IgniteLiveAPI.events import ConnectEvent, DisconnectEvent, LiveEndEvent

client: IgniteLiveClient = IgniteLiveClient(unique_id="@isaackogz")


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent) -> None:
    print(f"Connected to @{event.unique_id}, room {event.room_id}")


@client.on(LiveEndEvent)
async def on_live_end(event: LiveEndEvent) -> None:
    print(f"Stream ended: {event.action.name}")


@client.on(DisconnectEvent)
async def on_disconnect(event: DisconnectEvent) -> None:
    print("Disconnected")


if __name__ == "__main__":
    client.run()
```

`await client.disconnect()` closes the socket, waits for the loop task to finish, and resets `room_id`, `room_info`, and `gift_info`. Calling it when not connected is safe.

## Automatic reconnect

Pass `reconnect=True` to `run()`, `connect()` or `start()` and the client recovers from a dropped connection itself. Pass `idle_timeout=` as well to catch a connection that is open but silent.

```python
from IgniteLiveAPI import IgniteLiveClient

client: IgniteLiveClient = IgniteLiveClient(unique_id="@isaackogz")

if __name__ == "__main__":
    client.run(reconnect=True, idle_timeout=60)
```

A reconnect repeats the connect sequence rather than reopening the old socket, because a signed WebSocket URL expires within about 30 seconds and cannot be reused. Each attempt waits, checks that the room is still live (unless `fetch_live_check=False`), asks the signing provider for a new signed URL, and connects. The room ID is kept. The waiting follows an exponential backoff with jitter, so many clients that dropped together do not retry together; a rate-limited sign request waits at least as long as the provider asks. `ReconnectEvent` fires before each attempt and `ConnectEvent` after each success.

Pass a `ReconnectPolicy`, from `IgniteLiveAPI.client.reconnect`, to tune it:

| Field | Default | Effect |
| --- | --- | --- |
| `max_attempts` | `10` | Consecutive failed attempts before the client raises `ReconnectFailedError`, with the last failure as its cause. `None` retries forever. |
| `base_delay` | `2.0` | Seconds before the first retry. |
| `max_delay` | `60.0` | Cap on the delay before jitter. |
| `multiplier` | `2.0` | The delay is multiplied by this for each consecutive attempt. |
| `jitter` | `0.25` | Fraction the delay is randomised by in either direction. `0` disables it. |
| `stable_after` | `30.0` | A connection that stayed up this many seconds resets the attempt counter. |

What is retried: a socket closed with any code, including a clean close you did not request, a refused or timed-out connection, a proxy failure, an idle timeout, and a failed or rate-limited sign request. What is not: `WebcastBlockedError` (TikTok detected the client, and retrying faster makes that worse), `PremiumEndpointError`, `AuthenticatedWebSocketConnectionError`, and unexpected exceptions. These are raised as they would be without `reconnect`. If the room is no longer live when an attempt starts, or `disconnect()` is called, including by a `LiveEndEvent`, the client stops and emits `DisconnectEvent`. `disconnect()` also cuts a backoff wait short.

Events are not replayed on a reconnect: `process_connect_events` applies to the first connection only, so the recent history TikTok sends on join is not handled twice. Events that happened while the client was disconnected are lost.

`idle_timeout` counts every frame TikTok sends, including the heartbeats the client does not turn into events, so it measures a dead connection, not a quiet chat. When it passes, the client closes the socket and raises `IdleTimeoutError`, which `reconnect` then retries. Without `reconnect` that error propagates like any other failure. TikTok does not answer WebSocket pings, which is why the underlying keepalive is off and a half-open connection is otherwise never noticed. The right value depends on how often TikTok sends frames to your connections; start well above the heartbeat interval, such as 60 seconds, and lower it only after watching real traffic.

## Reconnect yourself

Without `reconnect=`, the client does not reconnect on its own. When the stream ends, `connect()` returns and `DisconnectEvent` fires; when the socket drops abnormally, `connect()` raises `websockets.exceptions.ConnectionClosedError`. Either way, trying again is up to your program. Use one loop with a delay, and register listeners once rather than on every attempt. Different causes need different handling: a creator who ended the stream stays offline for a while, an [Euler Stream](https://www.eulerstream.com/) rate limit raises `SignatureRateLimitError` whose `retry_after` says how long to wait, and a network drop can be retried sooner. See [troubleshooting](/troubleshooting/).

```python
import asyncio

from websockets.exceptions import ConnectionClosedError

from IgniteLiveAPI import IgniteLiveClient
from IgniteLiveAPI.client.errors import UserOfflineError
from IgniteLiveAPI.events import CommentEvent

client: IgniteLiveClient = IgniteLiveClient(unique_id="@isaackogz")


@client.on(CommentEvent)
async def on_comment(event: CommentEvent) -> None:
    print(event.comment)


async def main() -> None:
    while True:
        if not await client.is_live():
            await asyncio.sleep(60)
            continue
        try:
            await client.connect()
        except (UserOfflineError, ConnectionClosedError):
            pass
        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
```

## Check live status before connecting

`is_live` asks TikTok's HTTP API whether the creator is live without signing or opening a WebSocket. It is the right way to poll: connecting just to find out is slower and spends a signing request. Passing a `unique_id` checks that creator and re-targets the client: a later `connect()` connects to it, not to the creator given to the constructor. `connect()` performs the same check itself when `fetch_live_check` is on and raises `UserOfflineError` when the creator went offline in between. The loop above polls every 60 seconds, as the repository's `check_live.py` example does.

## Close the client

`disconnect` leaves the HTTP session open so the same client can connect again. `close` discards that session for a client you will not use again. `run()` cleans up after itself, including on `Ctrl+C`.
