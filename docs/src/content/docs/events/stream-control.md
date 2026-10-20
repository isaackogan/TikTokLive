---
title: Stream control
description: ControlEvent and the LiveEndEvent, LivePauseEvent, and LiveUnpauseEvent derived from it, with the ControlAction values and what the client does on each.
sidebar:
  order: 10
---

TikTok reports a stream's pauses, resumes, ends, and suspensions with one message, `WebcastControlMessage`. The client emits it as `ControlEvent` and also derives one of three custom events from its `action`, so a handler can listen for the specific transition or inspect the action itself.

Replace `@isaackogz` with a creator who is live. Each example registers its listener before connecting.

## ControlEvent

Stream action (e.g. start, end, pause, unpause). Message: [`WebcastControlMessage`](/schema/webcast/model/message/webcastcontrolmessage/).

Key fields: `action`, a `ControlAction` with the values `STREAM_PAUSED`, `STREAM_UNPAUSED`, `STREAM_ENDED`, and `STREAM_SUSPENDED` (`FALLBACK_UNKNOWN` is the zero value); `tips`, a string shown to viewers; `extra`; `perception_dialog` and `perception_audience_text`, set when a suspension comes with a policy dialog; `punish_info`; `float_text` and `float_style`.

When `action` is `STREAM_ENDED` or `STREAM_SUSPENDED` the client schedules its own `disconnect()`, so `DisconnectEvent` follows. The derived event is emitted first, then `WebsocketResponseEvent`, then `ControlEvent`.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ControlEvent
from TikTokLive.proto.custom_proto import ControlAction

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(ControlEvent)
async def on_control(event: ControlEvent) -> None:
    if event.action == ControlAction.STREAM_SUSPENDED:
        print(f"Stream suspended: {event.tips}")
    else:
        print(f"Stream action: {event.action.name}")


if __name__ == "__main__":
    client.run()
```

## LiveEndEvent

The livestream ended or was suspended. Custom event, a subclass of `ControlEvent` emitted when `action` is `STREAM_ENDED` or `STREAM_SUSPENDED`; it has the same fields.

The client disconnects itself after emitting it, so a program that uses `client.run()` returns shortly after this handler. Read `event.action` to tell an ordinary end from a suspension.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import LiveEndEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(LiveEndEvent)
async def on_live_end(event: LiveEndEvent) -> None:
    print(f"Stream over: {event.action.name}")


if __name__ == "__main__":
    client.run()
```

## LivePauseEvent

The livestream was paused. Custom event, a subclass of `ControlEvent` emitted when `action` is `STREAM_PAUSED`; it has the same fields. The connection stays open while the stream is paused, and chat messages can still arrive.

## LiveUnpauseEvent

A paused livestream resumed. Custom event, a subclass of `ControlEvent` emitted when `action` is `STREAM_UNPAUSED`; it has the same fields.
