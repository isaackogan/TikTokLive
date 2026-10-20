---
title: Send chat messages
description: Post a chat message to the connected room with send_room_chat, what the call needs, what it returns, how to reply to viewers safely, and how to send without connecting.
sidebar:
  order: 3
---

`await client.send_room_chat(content)` posts `content` as a chat message to the room the client is connected to. Reading a public room needs no account; sending does. The message goes to TikTok through the signing provider's chat endpoint, Euler Stream by default, together with your session cookies. Before it is sent, the client checks four things:

- A TikTok session. The `sessionid` and `tt-target-idc` cookies must be set, with `client.web.set_session(...)` or at construction, as [authentication](/configuration/authentication/) describes. Without `sessionid` the call raises `ValueError`; so does `sessionid` without `tt-target-idc`.
- The host allowlist. `WHITELIST_AUTHENTICATED_SESSION_ID_HOST` must equal the signing server's host, `api.eulerstream.com` by default; otherwise `AuthenticatedWebSocketConnectionError` is raised and nothing leaves your machine.
- A room ID. `client.send_room_chat` uses `client.room_id`, which connecting sets; before a connection it raises `ValueError`.
- The provider's permission for its chat endpoint. The request is made with the API key the client is configured with; see [signing](/configuration/signing/).

```sh
export WHITELIST_AUTHENTICATED_SESSION_ID_HOST="api.eulerstream.com"
export TIKTOK_SESSION_ID="your-sessionid-cookie"
export TIKTOK_TARGET_IDC="your-tt-target-idc-cookie"
```

`TIKTOK_SESSION_ID` and `TIKTOK_TARGET_IDC` are names the examples below read themselves; the library reads only the allowlist variable.

## Send on connect

```python
import os

from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent) -> None:
    response = await client.send_room_chat("Hello from TikTokLive!")
    print(response)


if __name__ == "__main__":
    client.web.set_session(os.environ["TIKTOK_SESSION_ID"], os.environ["TIKTOK_TARGET_IDC"])
    client.run()
```

The return value is a `dict` with `code`, `message`, and `data`. When the provider returns a parsed body, `code` and `message` are the body's values and `data` is its payload; when it does not, `code` is the HTTP status and `data` is `None`. It is the provider's response to your request, not the `CommentEvent` the room will receive. Print it while developing to learn the codes your account sees.

## Reply to viewers

A message you send arrives back as a `CommentEvent` like any other, so a reply must never be able to match its own trigger, and every automatic reply needs rate control. The library has no send queue and no moderation policy; TikTok applies its own limits to accounts that post quickly.

```python
import os
import time

from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
COOLDOWN_SECONDS: float = 10.0
last_sent_at: float = 0.0


@client.on(CommentEvent)
async def on_comment(event: CommentEvent) -> None:
    global last_sent_at
    if event.user is None or not event.content.startswith("!hello"):
        return
    if time.monotonic() - last_sent_at < COOLDOWN_SECONDS:
        return

    last_sent_at = time.monotonic()
    # The reply does not start with "!hello", so it cannot trigger itself
    await client.send_room_chat(f"Hello, {event.user.nickname}!")


if __name__ == "__main__":
    client.web.set_session(os.environ["TIKTOK_SESSION_ID"], os.environ["TIKTOK_TARGET_IDC"])
    client.run()
```

## Send without connecting

The route behind the method, `client.web.send_room_chat(content, room_id=None, session_id=None, tt_target_idc=None)`, can be called without a WebSocket. `room_id` falls back to the `room_id` request parameter that connecting sets, and `session_id` and `tt_target_idc` fall back to the cookie jar, so pass the room explicitly when the client has not connected. The room ID comes from `client.web.fetch_room_id_from_api(unique_id)`.

```python
import asyncio
import os

from TikTokLive import TikTokLiveClient

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


async def main() -> None:
    client.web.set_session(os.environ["TIKTOK_SESSION_ID"], os.environ["TIKTOK_TARGET_IDC"])

    room_id: int = await client.web.fetch_room_id_from_api(client.unique_id)
    response = await client.web.send_room_chat("Hello!", room_id=room_id)
    print(response)

    await client.web.close()


if __name__ == "__main__":
    asyncio.run(main())
```

The same session and allowlist rules apply. A session ID grants full access to the account it belongs to; the [authentication](/configuration/authentication/) page explains where it is sent and how to keep it out of source control.
