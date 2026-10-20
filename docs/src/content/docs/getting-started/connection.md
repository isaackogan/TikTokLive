---
title: Connection lifecycle
description: Run, start, or connect a client, fetch room and gift information, handle connect, disconnect, and stream-end events, reconnect, and check live status.
---

## Run, start, or connect

`TikTokLiveClient` offers three ways to open a connection. They perform the same steps and accept the same keyword-only options; they differ in what they block.

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

## Fetch room and gift information

`fetch_room_info=True` stores the room's metadata on `client.room_info`, and `fetch_gift_info=True` stores the room's gift catalog on `client.gift_info`. Both are plain `dict` objects from TikTok's HTTP API, both are `None` unless requested, and both are reset to `None` by `disconnect()`. Keep your own copy if you need the data after the stream ends.

```python
import asyncio

from TikTokLive import TikTokLiveClient

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


async def main() -> None:
    task: asyncio.Task = await client.start(fetch_room_info=True, fetch_gift_info=True)
    print(client.room_id, client.room_info, client.gift_info)
    await task


if __name__ == "__main__":
    asyncio.run(main())
```

## Connect, disconnect, and stream-end events

Three custom events mark the lifecycle. Register them like any other event.

- `ConnectEvent` is emitted when the first signed response is parsed. It carries `unique_id` and `room_id`; `client.room_id` and `client.connected` are set by then.
- `LiveEndEvent` is emitted when TikTok's `ControlEvent` reports `STREAM_ENDED` or `STREAM_SUSPENDED`. The client then disconnects itself. `LivePauseEvent` and `LiveUnpauseEvent` report pauses the same way.
- `DisconnectEvent` is emitted once when the WebSocket loop exits normally: the stream ended, you called `disconnect()`, or TikTok closed the socket with close code 1000 or 1001. A close with any other code, such as a dropped network connection, raises `ConnectionClosedError` from `connect()` or from the task `start()` returned instead, and no `DisconnectEvent` is emitted. The event carries no payload and does not by itself say why.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, DisconnectEvent, LiveEndEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


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

## Reconnect

The client does not reconnect on its own. When the stream ends, `connect()` returns and `DisconnectEvent` fires; when the socket drops abnormally, `connect()` raises `websockets.exceptions.ConnectionClosedError`. Either way, trying again is up to your program. Use one loop with a delay, and register listeners once rather than on every attempt. Different causes need different handling: a creator who ended the stream stays offline for a while, an [Euler Stream](https://www.eulerstream.com/) rate limit raises `SignatureRateLimitError` whose `retry_after` says how long to wait, and a network drop can be retried sooner. See [troubleshooting](/troubleshooting/).

```python
import asyncio

from websockets.exceptions import ConnectionClosedError

from TikTokLive import TikTokLiveClient
from TikTokLive.client.errors import UserOfflineError
from TikTokLive.events import CommentEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


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
