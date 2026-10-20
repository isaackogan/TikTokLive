---
title: Protocol types
description: How TikTokLive's events and messages come from the TikTokLiveProto v3 schema, how to decode and inspect a message, the compatibility aliases, and the difference between a schema definition and verified behaviour.
sidebar:
  order: 4
---

TikTokLive does not define the Webcast protocol itself. The message classes come from the [TikTokLiveProto](https://pypi.org/project/TikTokLiveProto/) package, pinned in `pyproject.toml`, whose `v3` schema is generated with betterproto2. `TikTokLive.proto` re-exports its messages and enums: `webcast.im`, `webcast.shared.message`, `webcast.model` and its `message`, `base`, `base.user`, and `data` subpackages, plus the aliases and extended types described below. The [schema reference](/schema/) is generated from the TikTokLiveProto version installed with this checkout, and the [API reference](/api/) from the checkout's own source.

## Events are generated from the schema

`TikTokLive/events/proto_events.py` is not written by hand. `scripts/proto/gen_events.py` walks every module of `TikTokLiveProto.v3` and makes an event class of every `Webcast*` message that has a `common` field of type `CommonMessageData`. The class name strips `Webcast` and `Message` and appends `Event`, so `WebcastGiftMessage` becomes `GiftEvent`, unless `scripts/proto/resources/events.yaml` names it, as it does for `WebcastChatMessage` and `CommentEvent`. The YAML also adds the hand-written properties, such as `CommentEvent.comment`, `GiftEvent.streaking`, and `user_is_super_fan`, and declares that fields typed `User` become `ExtendedUser` and fields typed `Gift` become `ExtendedGift`, except inside lists, where the schema's own type stays.

The generator also writes `EVENT_MAPPINGS`, a dict from message name to event class, and `ProtoEvent`, the union of the generated classes. When a message arrives, the client looks up its `method`, `WebcastGiftMessage` for example, in `EVENT_MAPPINGS` and parses the payload with that class; a method with no entry is emitted as `UnknownEvent`. The 12 custom events in `TikTokLive.events.custom_events` are hand-written and derived in `handle_custom_event`; see the [event catalog](/events/).

`.github/workflows/generate.yml` reruns the generators on every push to `master` that changes `scripts/proto/`, `pyproject.toml`, or the workflow, and commits the result, so bumping the pinned TikTokLiveProto version regenerates the events. `python scripts/proto/gen_events.py --check` reports whether the committed file is current. The project's `CONTRIBUTING.md` covers the generated files.

## Decode a message

Every message is a betterproto2 dataclass. `Message().parse(data)` fills an instance from bytes and returns it, `bytes(message)` serializes one, and `to_dict()` gives a plain dict. An event class is its message class with extra properties, so the same payload parses as either:

```python
from TikTokLive.events import CommentEvent
from TikTokLive.proto import WebcastChatMessage

# Build a message, serialize it, and parse the bytes back as the event class
message: WebcastChatMessage = WebcastChatMessage(content="hello")
payload: bytes = bytes(message)

event: CommentEvent = CommentEvent().parse(payload)
print(event.get_type(), event.content, event.user)
print(event.to_dict())
```

A payload captured from a live session is decoded the same way. `WebsocketResponseEvent.raw.messages` holds each message's `method` and `payload`; `EVENT_MAPPINGS[method]().parse(payload)` gives the event, and a method missing from the mapping is what `UnknownEvent` reports. The [debugging guide](/guides/debugging-events/) shows how to capture payloads as base64 for a report.

Nested messages are `Optional` in v3: `event.user`, `event.gift`, `event.common`, and similar are `None` when absent, and mypy reports an unguarded access. Fields keep their schema types, so IDs are `int`, timestamps are `int` in the unit the schema states, and enums are the schema's enum classes, such as `ControlAction` on `ControlEvent.action`.

## Transport messages

The WebSocket layer uses four messages from `webcast.im` and `webcast.shared.message`, all re-exported from `TikTokLive.proto`:

| Message | Fields | Role |
| --- | --- | --- |
| `WebcastPushFrame` | `seq_id`, `log_id`, `service`, `method`, `headers`, `payload_encoding`, `payload_type`, `payload` | One WebSocket message in either direction. |
| `ProtoMessageFetchResult` | `messages`, `cursor`, `fetch_interval`, `now`, `internal_ext`, `fetch_type`, `route_params`, `heartbeat_duration`, `need_ack`, `push_server`, `is_first`, `history_comment_cursor`, `history_no_more` | A batch of messages: the signing provider's first response, and the payload of every `msg` frame. `WebsocketResponseEvent.raw` is one of these. |
| `BaseProtoMessage` | `method`, `payload`, `msg_id`, `msg_type`, `offset`, `is_history`, `sample_flag` | One message in a batch. Also exported as `ProtoMessageFetchResultBaseProtoMessage`, its 6.x name. |
| `WebcastImEnterRoomMessage`, `HeartBeatMessage` | `room_id`, `live_id`, `identity`, `cursor`, and others; `room_id`, `send_packet_seq_id` | The room-entry and heartbeat payloads the client sends. |

The [WebSocket client page](/advanced/websocket/) describes when each is sent and received; the signing provider that returns the first batch is [Euler Stream](https://www.eulerstream.com/) by default.

## Extended types and aliases

`TikTokLive.proto.custom_proto` subclasses two schema messages with helpers, using the `proto_extension` decorator so betterproto2 serializes them with the parent's metadata:

- `ExtendedUser` extends `User` with `unique_id` (the `display_id`), `is_friend`, `has_badge(badge_type, level=None)`, `get_all_badges`, `is_moderator`, `is_top_gifter`, `member_level`, `member_rank`, and `gifter_level`, and the class method `from_user(user)`.
- `ExtendedGift` extends `Gift` with `streakable`, true when `type` is `1`.

`TikTokLive/proto/_aliases.py` is generated by `scripts/proto/gen_aliases.py` from `scripts/proto/resources/aliases.yaml`. It attaches read-only properties for names from earlier versions: `username`, `nick_name`, and `badges` on `ExtendedUser` for `display_id`, `nickname`, and `badge_list`; `gift_type`, `gift_name`, and `gift_image` on `ExtendedGift` for `type`, `name`, and `image`. The file is excluded from mypy, so the aliases are invisible to type checking; use the schema names in new code. `ControlAction` is the schema's enum, re-exported from `custom_proto` for imports written against 6.x. See the [migration guide](/getting-started/migration/).

`TikTokLive.proto.proto_utils` has `common_display_type(common)`, which reads `common.display_text.key` through the optional chain and is what the follow, share, and super-fan-box matching uses, and `badge_match(badge, pattern)` and `badge_match_user(user, pattern)`, which search a badge's text or image URLs with a regular expression.

## Schema definitions and verified behaviour

A message in the schema proves that TikTok's protocol can carry it and that this version can decode it. It does not prove that every room, region, or stream type sends it, that the message is sent at the moment its name suggests, or what an undocumented integer field means. This checkout defines 62 proto events; the grouped event pages state what has been observed and mark what has not. A field that is always zero or empty in your rooms may be populated elsewhere, and a message that never arrives may need a feature the room does not use.

Keep values as they are decoded. IDs are Python `int` and keep their full 64-bit value, so serialize them as strings when the consumer is JavaScript or JSON that cannot. Read enum fields by name rather than by number in your own code, since the schema can renumber or rename them between versions, as `ControlAction` was between 6.x and 7.

For a protocol report, include the message `method`, the output of `pip show TikTokLive TikTokLiveProto`, what was happening in the stream, and a base64 payload or a sanitized fixture. Base64 is an encoding, not anonymization: a payload can contain usernames, IDs, and other personal data, so review it before posting. See [troubleshooting](/troubleshooting/) for where to report.
