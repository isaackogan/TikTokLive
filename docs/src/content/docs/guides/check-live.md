---
title: Check if a user is live
description: Poll live status with is_live without signing or connecting, check by room ID or in batches, fetch the creator's avatar, and connect once the stream starts.
sidebar:
  order: 2
---

Connecting to find out whether a creator is live is the slow way: it resolves the room, spends a signing request, and raises `UserOfflineError` when they are offline. `await client.is_live()` asks TikTok's HTTP API directly and returns a `bool`. It needs no signing and no session, and opens no WebSocket. This guide is a tightened version of the repository's `examples/check_live.py`.

## Check once

```python
import asyncio

from TikTokLive import TikTokLiveClient

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


async def main() -> None:
    if await client.is_live():
        print(f"@{client.unique_id} is live")
    else:
        print(f"@{client.unique_id} is offline")
    await client.web.close()


if __name__ == "__main__":
    asyncio.run(main())
```

`is_live(unique_id)` checks another creator with the same client. It also re-targets the client: `client.unique_id` changes, and a later `connect()` connects to that creator. To watch several creators, use one client per creator or the batch route below.

## Poll until live, then connect

A loop that checks every minute, connects when the creator goes live, and resumes polling when the stream ends. `connect()` blocks until the connection closes, so the loop body runs once per stream. Register the handlers once, outside the loop.

```python
import asyncio

from TikTokLive import TikTokLiveClient
from TikTokLive.client.errors import UserOfflineError
from TikTokLive.client.logger import LogLevel
from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
POLL_SECONDS: int = 60


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent) -> None:
    avatar_url = await client.get_avatar_url()
    client.logger.info(f"Connected to @{event.unique_id}; avatar: {avatar_url}")


@client.on(CommentEvent)
async def on_comment(event: CommentEvent) -> None:
    if event.user is None:
        return
    print(f"{event.user.unique_id}: {event.content}")


@client.on(DisconnectEvent)
async def on_disconnect(event: DisconnectEvent) -> None:
    client.logger.info("Disconnected")


async def main() -> None:
    while True:
        if not await client.is_live():
            client.logger.info(f"@{client.unique_id} is offline; checking again in {POLL_SECONDS}s")
            await asyncio.sleep(POLL_SECONDS)
            continue

        try:
            # Returns when the stream ends or the client disconnects
            await client.connect()
        except UserOfflineError:
            # The creator went offline between the check and the connection
            pass

        client.logger.info(f"Stream over; checking again in {POLL_SECONDS}s")
        await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    client.logger.setLevel(LogLevel.INFO.value)
    asyncio.run(main())
```

Each `is_live` call is one HTTP request to TikTok from your address. A minute between checks is the interval the repository's example uses; polling much faster gains little, because a stream rarely starts and ends within a minute. `connect()` repeats the live check itself while `fetch_live_check` is on, which is why `UserOfflineError` is still possible after a positive poll.

When the stream ends normally, `connect()` returns and `DisconnectEvent` fires. A socket that drops abnormally raises `websockets.exceptions.ConnectionClosedError` from `connect()` instead; the [connection lifecycle](/getting-started/connection/) page shows a loop that handles both.

## Check by room ID or in batches

`is_live` is a thin wrapper over the route `client.web.fetch_is_live`, which accepts either `unique_id` or `room_id` and raises `InvalidFetchIsLiveRequest` when given neither. The route's `fetch_is_live_room_ids(*room_ids)` method checks several rooms in one request and returns a list of `bool` in the order given. A room ID comes from `client.room_id` after a connection, or from `client.web.fetch_room_id_from_api(unique_id)`.

```python
import asyncio
from typing import List

from TikTokLive import TikTokLiveClient

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


async def main() -> None:
    room_id: int = await client.web.fetch_room_id_from_api(client.unique_id)
    print(f"@{client.unique_id} has room {room_id}")

    room_ids: List[int] = [room_id]
    statuses: List[bool] = await client.web.fetch_is_live.fetch_is_live_room_ids(*room_ids)
    for checked_id, live in zip(room_ids, statuses):
        print(checked_id, "live" if live else "offline")

    await client.web.close()


if __name__ == "__main__":
    asyncio.run(main())
```

A room ID that returns no entry raises `MissingRoomIdInResponse`; the error text notes that this happens for a nonexistent room and when TikTok blocks the request.

## Avatar URL

`await client.get_avatar_url()` returns the creator's profile avatar URL as a `str`, or `None` when the profile page does not contain one. It reads the public profile HTML with the client's HTTP session and takes an optional `unique_id` like `is_live`. The result is a URL, not image bytes; the [images guide](/guides/images/) shows how to download it with `client.web.fetch_image_data`.
