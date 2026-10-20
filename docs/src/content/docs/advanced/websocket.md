---
title: WebSocket client
description: The Webcast WebSocket layer under TikTokLiveClient, how the signed URL becomes a connection, the room-entry, heartbeat, and acknowledgement frames, compression, proxies, and how a connection ends.
sidebar:
  order: 3
---

`WebcastWSClient`, from `TikTokLive.client.ws.ws_client`, holds the WebSocket connection to TikTok's Webcast server. `TikTokLiveClient` creates one when it is constructed, from `ws_kwargs` and `ws_proxy` (see [client options](/configuration/options/)), and drives it from the task that `start()` returns. The client does not expose it as a property: `client.connected` reports whether its socket is open, and the connection options on `run`, `connect`, and `start` configure it. This page describes what it does, for reading the traffic or using the layer on its own.

## Connection sequence

1. `start()` resolves the room ID, runs the live check, and calls the `fetch_signed_websocket` route, which returns the first `ProtoMessageFetchResult` from the signing provider, [Euler Stream](https://www.eulerstream.com/) by default. That result carries `push_server`, the WebSocket URL, `route_params`, `cursor`, and often the first `messages`.
2. `WebcastWSClient.connect(room_id, cookies, user_agent, initial_webcast_response, process_connect_events=True, compress_ws_events=True)` builds the connection URL with `build_webcast_uri`: `push_server`, then `route_params` percent-encoded, then `WebDefaults.ws_client_params` with `ws_kwargs["base_uri_params"]` over them, then `room_id` and `compress` (`gzip`, or empty when `compress_ws_events` is off), then `WebDefaults.ws_client_params_append_str`. A result without `cursor` raises `InitialCursorMissingError`, one without `push_server` or `route_params` `WebsocketURLMissingError`. `ws_kwargs["uri"]` replaces the built URL. With `process_connect_events=False` the result's `messages` are cleared first.
3. The handshake sends a `Cookie` header with the whole cookie jar and the client's `User-Agent`, with `ws_kwargs["extra_headers"]` over them, and offers the `echo-protocol` subprotocol. The cookie string is logged at `DEBUG`, or at `WARNING` with the session ID redacted when the jar holds one. `ping_interval` and `ping_timeout` are always `None`: TikTok does not answer protocol-level pings, and a timeout would close a healthy connection.
4. The connection is a `WebcastConnect`, a subclass of the `websockets` legacy `Connect`, from `TikTokLive.client.ws.ws_connect`. Its iterator yields the initial result first, as `(None, initial_response)`, then one `(WebcastPushFrame, ProtoMessageFetchResult)` pair per `msg` frame received. It does not retry or reconnect: the signed URL expires (the source notes 30 seconds), so a new connection needs a new signing request.

The response's `Handshake-Options` header is parsed with `extract_websocket_options` into a dict, available as `ws_options` on the connection, and supplies the heartbeat interval below.

## Frames

Every WebSocket message is a `WebcastPushFrame`, whose fields are `seq_id`, `log_id`, `service`, `method`, `headers` (a list of key/value `PushHeader` messages), `payload_encoding`, `payload_type`, and `payload`. Incoming frames whose `payload_type` is not `msg` are logged at `DEBUG` and dropped; that covers the server's `hb` heartbeats, `ack` receipts, and `im_enter_room_resp`. A `msg` frame's `payload` is a `ProtoMessageFetchResult`; when the frame carries a `compress_type` header of `gzip`, `extract_webcast_response_message` decompresses it first.

The client sends three kinds of frame, all with `payload_encoding` `pb`:

| `payload_type` | Payload | When |
| --- | --- | --- |
| `im_enter_room` | `WebcastImEnterRoomMessage` with `room_id`, `live_id=12`, `identity="audience"`, and an empty `cursor` | Once, by `switch_rooms(room_id)`, when the initial result (`is_first`) is processed. The initial result itself is not acknowledged. |
| `hb` | `HeartBeatMessage` with `room_id` and an increasing `send_packet_seq_id` | Every heartbeat interval, from the ping loop that `switch_rooms` starts. |
| `ack` | The result's `internal_ext`, or `-` when it has none | For each received result whose `need_ack` is set, with the frame's `log_id`. |

`send(message)` sends bytes or any betterproto message and is a no-op with a warning when the socket is not open. `send_ack(webcast_response, webcast_push_frame)` builds the `ack` frame. `switch_rooms(room_id)` sends the room-entry frame and restarts the heartbeat loop; it does not change `TikTokLiveClient.room_id` or re-sign anything, so it is not a way to move a high-level client between rooms.

## Heartbeats

`restart_ping_loop(room_id)` cancels any running loop, resets the sequence to `1`, and starts a task that sends an `hb` frame, then sleeps for the interval, while the socket is connected. The interval is `DEFAULT_PING_INTERVAL`, 5 seconds, unless the handshake's `Handshake-Options` header named a `ping-interval`, in which case that value is used. The loop is cancelled and awaited when `connect` finishes.

## How a connection ends

`disconnect()` closes the socket and returns; it does nothing when the socket is not open. The iterator in `connect` exits normally when the connection closes with code 1000 or 1001 or with no close code, and `TikTokLiveClient` then emits `DisconnectEvent`. A close with any other code raises `websockets.exceptions.ConnectionClosedError` out of the iterator, which propagates from `client.connect()` or from the task `start()` returned, and no `DisconnectEvent` is emitted. See [control events](/events/control/) and [connection lifecycle](/getting-started/connection/).

A handshake that TikTok rejects with status 400 or 200 raises `WebcastBlockedError` with the reason from the response's `Handshake-Msg` header; the source notes that a URL signed with a session, used without the matching `sessionid` cookie, is rejected this way. Any other status raises the `websockets` library's own error. See [troubleshooting](/troubleshooting/).

## Proxies

When `ws_proxy` or `ws_kwargs["proxy"]` is set, the connection is a `WebcastProxyConnect`, which adds `websockets_proxy` support to `WebcastConnect`. An `httpx.Proxy` is converted to a `websockets_proxy.Proxy` when the connection opens, keeping its credentials; a `websockets_proxy.Proxy` is used as it is. `WebcastProxy`, in `ws_connect`, is the union of the two types, and `ws_kwargs["proxy_conn_timeout"]`, `10.0` by default, is the proxy connection timeout. See [proxies](/configuration/proxies/).

## Use the layer directly

The pieces are public, so a program can open the socket without `TikTokLiveClient` parsing the messages into events. This connects and prints the method names in each batch:

```python
import asyncio

from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.routes.fetch_signed_websocket import WebcastPlatform
from TikTokLive.client.ws.ws_client import WebcastWSClient
from TikTokLive.proto import ProtoMessageFetchResult

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


async def main() -> None:
    room_id: int = await client.web.fetch_room_id_from_api(client.unique_id)
    initial: ProtoMessageFetchResult = await client.web.fetch_signed_websocket(
        WebcastPlatform.WEB, room_id=room_id
    )

    ws: WebcastWSClient = WebcastWSClient()
    async for response in ws.connect(
        room_id=room_id,
        cookies=client.web.cookies,
        user_agent=client.web.headers["User-Agent"],
        initial_webcast_response=initial,
    ):
        print([message.method for message in response.messages])

    await client.web.close()


if __name__ == "__main__":
    asyncio.run(main())
```

Each `response` is a `ProtoMessageFetchResult`; its `messages` carry a `method` name and a `payload` of bytes, which `EVENT_MAPPINGS` and the event classes decode as the [protocol page](/advanced/protocol/) describes. The high-level client adds the live check, the event parsing, the custom events, and `DisconnectEvent` on top of this loop.
