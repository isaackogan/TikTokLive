---
title: Debug events
description: Turn on debug logging, inspect every raw WebSocket message, catch messages the library has no event class for, silence deprecation warnings, and report a new message type.
sidebar:
  order: 6
---

Four tools cover most event debugging: the client's logger, `WebsocketResponseEvent` for the raw traffic, `UnknownEvent` for messages the library cannot name, and the attributes that control how parse failures are logged.

## Debug logging

`client.logger` is the `logging.Logger` named `TikTokLive`. It starts at `ERROR`. At `INFO` the library itself reports recordings and a `Ctrl+C` shutdown; the connection messages in this site's examples come from their own `client.logger.info` calls. At `DEBUG` it logs every event it emits, by type, the room-ID fallback, and other internal steps. Set the level with the standard constants or with the library's `LogLevel` enum:

```python
import logging

from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
client.logger.setLevel(logging.DEBUG)


@client.on(CommentEvent)
async def on_comment(event: CommentEvent) -> None:
    print(event.content)


if __name__ == "__main__":
    client.run()
```

The logger writes to `stderr` through its own handler and does not propagate to the root logger, so `logging.basicConfig` neither duplicates its lines nor captures them. To route them elsewhere, add a handler with `client.logger.addHandler(...)`.

## Every message: WebsocketResponseEvent

The client emits one `WebsocketResponseEvent` per message in a batch, before the message's own proto event, whether or not the message has an event class and even when its payload fails to parse. When a message also produces a custom event, such as `FollowEvent` from a social message or `LiveEndEvent` from a control message, that custom event is emitted first, then the `WebsocketResponseEvent`, then the proto event. Its field `raw` is the whole `ProtoMessageFetchResult` the message arrived in: `messages`, each with a `method` name and a `payload` of bytes; `cursor`; `fetch_interval`; `heartbeat_duration`; `is_first`, true for the signed response that produced `ConnectEvent`; `need_ack`; `push_server`; `route_params`; and `internal_ext`. The field list is on the [control events page](/events/control/#websocketresponseevent).

The event does not say which message of the batch it was emitted for, and every event from one batch carries the same `raw` object. To list each batch once, remember the last `raw` you saw and skip repeats:

```python
from typing import Optional

from TikTokLive import TikTokLiveClient
from TikTokLive.events import WebsocketResponseEvent
from TikTokLive.proto import ProtoMessageFetchResult

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
last_batch: Optional[ProtoMessageFetchResult] = None


@client.on(WebsocketResponseEvent)
async def on_response(event: WebsocketResponseEvent) -> None:
    global last_batch
    if event.raw is last_batch:
        return
    last_batch = event.raw

    for message in event.raw.messages:
        print(f"{message.method} ({len(message.payload)} bytes)")


if __name__ == "__main__":
    client.run()
```

## Messages without an event class: UnknownEvent

`UnknownEvent` subclasses `WebsocketResponseEvent` and is emitted after it when a message's `method` has no entry in `EVENT_MAPPINGS`, the `dict` in `TikTokLive.events.proto_events` that maps method names to event classes. That happens when TikTok adds a message type, or when the installed TikTokLiveProto schema predates one. The batch can hold tracked messages too, so test each method against `EVENT_MAPPINGS` rather than assuming the first one is the stranger. See the [control events page](/events/control/#unknownevent).

This handler prints each untracked method once, with its payload encoded as base64, which is the form a bug report needs:

```python
import base64
from typing import Set

from TikTokLive import TikTokLiveClient
from TikTokLive.events import UnknownEvent
from TikTokLive.events.proto_events import EVENT_MAPPINGS

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
reported: Set[str] = set()


@client.on(UnknownEvent)
async def on_unknown(event: UnknownEvent) -> None:
    for message in event.raw.messages:
        if message.method in EVENT_MAPPINGS or message.method in reported:
            continue
        reported.add(message.method)

        payload_b64 = base64.b64encode(message.payload).decode()
        print(f"Untracked message {message.method}: {payload_b64}")


if __name__ == "__main__":
    client.run()
```

## Payloads that fail to parse

A message with an event class whose payload does not parse is logged at `ERROR` with the method, the payload size, a short preview of the raw bytes, and the traceback; its `WebsocketResponseEvent` is still emitted, its own event is not. Two client attributes change that logging: `client.ignore_broken_payload = True` drops the `ERROR` entry, and substrings appended to `client.parse_error_ignorelist` demote matching errors to `DEBUG`, for schema mismatches you already know about. See [client options](/configuration/options/).

## Deprecation warnings

`client.web.fetch_video` and `client.web.fetch_image` are the 6.x names of `fetch_video_data` and `fetch_image_data`. Each use logs a `WARNING` unless the environment variable `SEND_DEPRECATION_WARNINGS` is set to anything other than `true`, case-insensitive. It is read once when `TikTokLive` is imported, so set it before starting Python. See [environment variables](/configuration/environment/).

```sh
export SEND_DEPRECATION_WARNINGS=false
```

## Report a new message type

The library's events are generated from the TikTokLiveProto schema, so a new message type needs the schema first. Before reporting, upgrade and check whether the type is already known:

```sh
pip install --upgrade TikTokLive
pip show TikTokLive TikTokLiveProto
```

If `UnknownEvent` still fires for it, open an issue on the [TikTokLive GitHub repository](https://github.com/isaackogan/TikTokLive/issues) with the method name, one or more base64 payloads from the handler above, the two version numbers, and what was happening in the stream when the message arrived, such as a gift, a battle, or a poll. The payload is what lets the message be decoded and a field list written; a method name alone is not enough.
