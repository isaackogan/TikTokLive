---
title: Control events
description: The four events the client emits itself, connect, disconnect, the raw WebSocket response, and unknown messages, with their fields and when they fire.
sidebar:
  order: 1
---

Control events come from the client rather than from a Webcast message. They mark the connection's lifecycle and expose the raw traffic that every other event is parsed from. They are separate from TikTok's `ControlEvent`, which reports stream pauses and ends; see [stream control](/events/stream-control/).

Replace `@isaackogz` with a creator who is live. Each example registers its listener before connecting.

## ConnectEvent

The client connected to the room and parsed the first signed response. Custom event, defined in `TikTokLive.events.custom_events`.

The WebSocket URL is signed by the signing provider, [Euler Stream](https://www.eulerstream.com/) by default, and the first response it returns is parsed like any other batch. `ConnectEvent` is emitted before the messages in that batch, so `client.room_id` and `client.connected` are already set in the handler.

Fields: `unique_id` (the creator's `@`-handle as the client cleaned it) and `room_id` (the numeric room ID the client resolved).

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent) -> None:
    print(f"Connected to @{event.unique_id}, room {event.room_id}")


if __name__ == "__main__":
    client.run()
```

## DisconnectEvent

The WebSocket loop exited and the client disconnected from the room. Custom event, defined in `TikTokLive.events.custom_events`.

It is emitted once when the loop ends normally: the stream ended, you called `client.disconnect()`, or TikTok closed the socket with close code 1000 or 1001. A close with any other code raises `ConnectionClosedError` from `connect()` or from the task that `start()` returned instead, and no `DisconnectEvent` is emitted. The event has no fields and does not by itself say why the connection ended; pair it with `LiveEndEvent` to tell a finished stream from a disconnect you requested.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import DisconnectEvent, LiveEndEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
stream_ended: bool = False


@client.on(LiveEndEvent)
async def on_live_end(event: LiveEndEvent) -> None:
    global stream_ended
    stream_ended = True


@client.on(DisconnectEvent)
async def on_disconnect(event: DisconnectEvent) -> None:
    print("Stream ended" if stream_ended else "Disconnected")


if __name__ == "__main__":
    client.run()
```

See [connection lifecycle](/getting-started/connection/) for reconnecting.

## WebsocketResponseEvent

Any Webcast message was received (carries the raw fetch result it came from). Custom event, defined in `TikTokLive.events.custom_events`.

The client emits one `WebsocketResponseEvent` per message in a batch, before the message's own event, whether or not the message has an event class and even when its payload fails to parse. The field `raw` is the whole `ProtoMessageFetchResult` the message arrived in, so every event from the same batch carries the same `raw`.

Fields on `raw`: `messages` (the batch, each with a `method` name and a `payload` of bytes), `cursor`, `fetch_interval`, `heartbeat_duration`, `now`, `is_first` (true for the signed response that produced `ConnectEvent`), `need_ack`, `push_server`, `route_params`, and `internal_ext`. In 6.x these fields were on the event itself; `event.cursor` is now `event.raw.cursor`, as the [migration guide](/getting-started/migration/) notes.

## UnknownEvent

A Webcast message arrived that TikTokLive has no event class for yet, useful for debugging. Custom event, defined in `TikTokLive.events.custom_events`.

`UnknownEvent` subclasses `WebsocketResponseEvent` and has the same `raw` field. It is emitted after the `WebsocketResponseEvent` for the same message when the message's `method` has no entry in the event mappings, which happens when TikTok adds a message type or when the installed TikTokLiveProto schema predates one. The method name is on the message inside `raw.messages`; the batch can hold other messages too, so print every method rather than assuming the first one is the unknown one.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import UnknownEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(UnknownEvent)
async def on_unknown(event: UnknownEvent) -> None:
    methods = sorted({message.method for message in event.raw.messages})
    print(f"Batch with an untracked message: {methods}")


if __name__ == "__main__":
    client.run()
```

A message that has an event class but whose payload fails to parse is logged instead; `ignore_broken_payload` and `parse_error_ignorelist` on the client control that logging. See [client options](/configuration/options/).
