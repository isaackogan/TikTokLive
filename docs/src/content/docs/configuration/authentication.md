---
title: Authentication
description: When a TikTok session is needed, how to give the client your session cookies, the host allowlist that guards them, and the risks of sending them.
sidebar:
  order: 5
---

Reading a public livestream needs no TikTok account. A session is required for:

- `client.send_room_chat`, which raises `ValueError` without one.
- `platform=WebcastPlatform.MOBILE`, which raises `ValueError` at connect time without a `sessionid` cookie.
- Age-restricted rooms: connecting with `fetch_room_info=True` raises `AgeRestrictedError` when TikTok withholds the room info, and the error suggests logging in with a session.

## Session cookies

TikTok identifies a logged-in session by the `sessionid` cookie together with `tt-target-idc`, the data center that holds the account. Copy both from your browser's cookies for `tiktok.com` while logged in, and set them before connecting:

```python
import os

from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent) -> None:
    print(f"Connected to @{event.unique_id}")


if __name__ == "__main__":
    client.web.set_session(os.environ["TIKTOK_SESSION_ID"], os.environ["TIKTOK_TARGET_IDC"])
    client.run()
```

`set_session` stores `sessionid`, `sessionid_ss`, and `sid_tt` with the session value and `tt-target-idc` with the data center, all for `.tiktok.com`, and sets the `user_is_login` request parameter to `true`. `set_session(None, None)` clears them. `TIKTOK_SESSION_ID` and `TIKTOK_TARGET_IDC` are names this example reads itself; the library does not read them.

The cookies can also be given at construction. This seeds the cookie jar but does not set `user_is_login`:

```python
from TikTokLive import TikTokLiveClient

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@isaackogz",
    web_kwargs={
        "httpx_kwargs": {
            "cookies": {"sessionid": "your-session-id", "tt-target-idc": "useast1a"},
        },
    },
)
```

`WebDefaults.web_client_cookies` seeds `tt-target-idc` with `useast1a`, so a session given with only `sessionid` is sent with that data center; use the value from your own browser. A `sessionid` with no `tt-target-idc` at all raises `ValueError`.

## Where the session goes

With a session set, three operations send it beyond TikTok itself:

- `fetch_signed_websocket`, the signing step of every connection, forwards `sessionid` and `tt-target-idc` to the signing provider so that the connection it returns is signed for your account. The client logs a warning when it does.
- `send_room_chat` sends them to the provider's chat endpoint.
- `client.web.get(..., sign_url=True)`, used by custom routes, includes them in the signing request.

The WebSocket handshake also sends the whole cookie jar, session included, to TikTok. The client logs that cookie string at `WARNING` with the session ID redacted.

## Host allowlist

Before any of those requests, the client checks `WHITELIST_AUTHENTICATED_SESSION_ID_HOST`. It must be set and equal to the part of `WebDefaults.tiktok_sign_url` after `://`, `api.eulerstream.com` by default. Otherwise the request raises `AuthenticatedWebSocketConnectionError` and nothing is sent.

```sh
export WHITELIST_AUTHENTICATED_SESSION_ID_HOST="api.eulerstream.com"
```

The comparison uses `WebDefaults.tiktok_sign_url`, not `SIGN_API_URL`. If you point the client at another provider, set `WebDefaults.tiktok_sign_url` to its URL and the variable to the text after `://`, including any port. See [signing](/configuration/signing/) and [environment variables](/configuration/environment/).

## Risks

A TikTok session ID grants full access to the account it belongs to. Setting the allowlist variable is your acknowledgement of the points the library's own error message makes:

- The provider receives the session ID. The message states that Euler Stream does not store it and that third-party signing servers may; treat any other host as able to read and keep it.
- A connection signed with your session is made through the provider, whose addresses other users share. The message notes that no ban has been attributed to this, and that the possibility exists.
- Keep the values out of source control and logs. Read them from the environment or a secret store, as the example above does.

If you do not need to act as a user, do not set a session.
