---
title: Client options
description: Every TikTokLiveClient constructor parameter, method, property, and attribute, and the keys accepted by web_kwargs and ws_kwargs.
sidebar:
  order: 1
---

Construct a client with `TikTokLiveClient(unique_id, ...)`. Everything after `unique_id` is optional. The constructor builds the HTTP client and the WebSocket client at once, so parameters are applied at construction; changing a dict you passed in afterwards does not reconfigure the client. Options that apply to one connection, such as `fetch_room_info`, belong to `run`, `connect`, and `start`; see [connection lifecycle](/getting-started/connection/).

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.routes.fetch_signed_websocket import WebcastPlatform

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@isaackogz",
    platform=WebcastPlatform.WEB,
    web_proxy=None,
    ws_proxy=None,
    web_kwargs={"httpx_kwargs": {"timeout": 30.0}},
    ws_kwargs={},
    is_user_id=False,
)
```

## Parameters

| Parameter | Type | Default | Behavior |
| --- | --- | --- | --- |
| `unique_id` | `str` or `int` | Required | The creator to connect to: `@username`, the bare username, or a profile or live URL. `parse_unique_id` strips `https://www.tiktok.com/`, `/live`, the first `@`, and surrounding whitespace. An `int` is kept as a numeric string; see `is_user_id`. |
| `platform` | `WebcastPlatform` | `WebcastPlatform.WEB` | Which WebSocket endpoint the signing provider returns. `WebcastPlatform.MOBILE` requires a `sessionid` cookie and raises `ValueError` at connect time without one; see [authentication](/configuration/authentication/). Import the enum from `TikTokLive.client.web.routes.fetch_signed_websocket`. |
| `web_proxy` | `httpx.Proxy` | `None` | Proxy for the HTTP client's requests to TikTok. See [proxies](/configuration/proxies/). |
| `ws_proxy` | `WebcastProxy` | `None` | Proxy for the WebSocket connection: an `httpx.Proxy` or a `websockets_proxy.Proxy`. See [proxies](/configuration/proxies/). |
| `web_kwargs` | `dict` | `None` | Keyword arguments for the HTTP client. Only the three keys below are accepted. |
| `ws_kwargs` | `dict` | `None` | Overrides for the WebSocket connection; see below. |
| `is_user_id` | `bool` | `False` | Treat a numeric `unique_id` as a TikTok user ID and resolve it to the username from the profile page when connecting or calling `is_live` or `get_avatar_url`. Raises `FailedResolveUserId` when the page yields no username. |

### `web_kwargs`

The HTTP client is `TikTokWebClient`, available as `client.web`. `web_kwargs` is unpacked into its constructor, which accepts exactly three keys; any other key, such as `cookies` at the top level, raises `TypeError`.

| Key | Behavior |
| --- | --- |
| `httpx_kwargs` | A `dict`. Its `cookies`, `headers`, and `params` entries are taken out and merged over `WebDefaults.web_client_cookies`, `web_client_headers`, and `web_client_params`; cookies are stored for the `.tiktok.com` domain. Every remaining entry, such as `timeout` or `verify`, is passed to `httpx.AsyncClient`. |
| `signer_kwargs` | A `dict` passed to the signer: `sign_api_key` and `sign_api_base`. See [signing](/configuration/signing/). |
| `web_proxy` | Used only when the `web_proxy` parameter is `None`. |

```python
from TikTokLive import TikTokLiveClient

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@isaackogz",
    web_kwargs={
        "httpx_kwargs": {
            "headers": {"Accept-Language": "en-GB,en;q=0.9"},
            "timeout": 30.0,
        },
        "signer_kwargs": {"sign_api_key": "your-api-key"},
    },
)
```

### `ws_kwargs`

The dict is copied each time a connection opens. These keys are consumed by the client:

| Key | Default | Behavior |
| --- | --- | --- |
| `proxy` | `None` | Used only when the `ws_proxy` parameter is `None`. |
| `proxy_conn_timeout` | `10.0` | Seconds to wait for the proxy connection. Applied only when a proxy is set. |
| `subprotocols` | `["echo-protocol"]` | WebSocket subprotocols offered in the handshake. |
| `base_uri_params` | `{}` | Merged over `WebDefaults.ws_client_params` to form the WebSocket URL's query. `room_id` and `compress` are set by the client afterwards and cannot be overridden here. |
| `base_uri_append_str` | `WebDefaults.ws_client_params_append_str` | Raw string appended to the WebSocket URL after the query. |
| `extra_headers` | `{}` | Merged over the `Cookie` and `User-Agent` headers the client builds. |
| `uri` | `None` | Replaces the WebSocket URL built from the signed response. Normally unset. |

Every other key is forwarded to the `websockets` client constructor. `ping_timeout` and `ping_interval` are always set to `None`: TikTok does not answer protocol-level pings, and the client keeps the connection alive with its own Webcast heartbeat instead.

## Methods

| Method | Async | Behavior |
| --- | --- | --- |
| `run` | No | Connect with `**options` and block the calling thread until the connection ends; the client runs its own event loop. On `Ctrl+C` it disconnects, cancels pending tasks, and re-raises `KeyboardInterrupt`. Returns the finished `asyncio.Task`. |
| `connect` | Yes | Connect with `**options` and block the calling coroutine until the connection ends. An optional positional `callback`, a function or coroutine, runs once the connection is up. Returns the finished `asyncio.Task`. |
| `start` | Yes | Connect with `**options` and return the running `asyncio.Task` without waiting for it. |
| `disconnect` | Yes | Close the WebSocket, wait for the event loop task, stop a running video recording, and reset `room_id`, `room_info`, and `gift_info`. Safe to call when not connected. `disconnect(close_client=True)` also calls `close`. |
| `close` | Yes | Close the HTTP session of a client you will not reuse. Its cleanup runs the event loop synchronously, so awaiting `close()` or `disconnect(close_client=True)` inside a running coroutine currently raises `RuntimeError: This event loop is already running`. |
| `on` | No | Register `f` as a listener for an event class with `on(event, f)`, or use it as a decorator: `@client.on(CommentEvent)`. Returns the handler. |
| `add_listener` | No | `add_listener(event, f)` registers `f` as a listener for an event class; the plain-call form of `on`. |
| `has_listener` | No | Whether at least one listener is registered for the event class. |
| `is_live` | Yes | Ask TikTok's HTTP API whether the creator is live, without signing. Passing `unique_id` re-targets the client to that creator. |
| `get_avatar_url` | Yes | The avatar URL of the creator, or of an optional `unique_id`, parsed from the public profile page; `None` when it is not found. |
| `send_room_chat` | Yes | Send `content` as a chat message to the connected room through the signing provider's premium chat endpoint. Requires a session; see [authentication](/configuration/authentication/). Returns a `dict` with `code`, `message`, and `data`. |
| `parse_unique_id` | No | Class method. Normalize a username, URL, or numeric ID to the bare `unique_id` string, as the constructor does. |
| `handle_custom_event` | Yes | Derive a custom event (`FollowEvent`, `ShareEvent`, `LiveEndEvent`, `LivePauseEvent`, `LiveUnpauseEvent`, `SuperFanEvent`, `SuperFanJoinEvent`, `SuperFanBoxEvent`) from a parsed proto event and its raw message, or return `None`. Override it in a subclass to add your own. |

`**options` are the keyword-only connection options `process_connect_events`, `compress_ws_events`, `fetch_room_info`, `fetch_gift_info`, `fetch_live_check`, and `room_id`, described in [connection lifecycle](/getting-started/connection/). All three connection methods raise `AlreadyConnectedError` when a connection is already open and `UserOfflineError` when the creator is not live.

## Properties

| Property | Type | Behavior |
| --- | --- | --- |
| `unique_id` | `str` | The normalized username. Updated when `is_live` is given another creator or when `is_user_id` resolution runs. |
| `room_id` | `int` or `None` | The room the client is connected to. `None` before connecting and after `disconnect`. |
| `web` | `TikTokWebClient` | The HTTP client: its routes, cookie jar, headers, params, and signer. `client.web.set_session(...)` sets a login session. |
| `connected` | `bool` | Whether the WebSocket is open. |
| `logger` | `logging.Logger` | The `TikTokLive` logger. Its level starts at `ERROR`; `client.logger.setLevel(LogLevel.INFO.value)` shows connection messages. |
| `gift_info` | `dict` or `None` | The room's gift catalog when connected with `fetch_gift_info=True`. |
| `room_info` | `dict` or `None` | The room's metadata when connected with `fetch_room_info=True`. |

Two plain attributes can be set after construction:

| Attribute | Default | Behavior |
| --- | --- | --- |
| `ignore_broken_payload` | `False` | When `True`, a payload that fails to parse is skipped without an `ERROR` log entry. |
| `parse_error_ignorelist` | `[]` | Substrings of parse error messages to log at `DEBUG` instead of `ERROR`, for known upstream schema bugs. |

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.client.logger import LogLevel
from TikTokLive.events import CommentEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
client.logger.setLevel(LogLevel.INFO.value)
client.ignore_broken_payload = True


@client.on(CommentEvent)
async def on_comment(event: CommentEvent) -> None:
    client.logger.info(event.comment)


if __name__ == "__main__":
    client.run()
```
