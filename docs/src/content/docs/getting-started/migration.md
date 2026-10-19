---
title: Migration
description: Update code written for TikTokLive 6.x to 7, which moves to the TikTokLiveProto v3 schema and renames some event fields.
---

TikTokLive 7 replaces the bundled protobuf definitions with the [TikTokLiveProto](https://pypi.org/project/TikTokLiveProto/) v3 package on betterproto2, regenerates every proto event from it, and its source is annotated and type-checked in the project's CI. Most 6.x programs need only the field changes below. Python 3.10 or newer is required.

```sh
pip install -U TikTokLive
```

## Event classes

Proto events are generated from the v3 schema, and only events whose messages exist in v3 are emitted. 6.6.5 defined 221 proto event classes; 7.0.1 defines 62. If an import fails, TikTok removed that message from the schema; `DiggEvent`, `SubscribeEvent`, `CommentsEvent`, `CountdownEvent`, `HashtagEvent`, and `TrayEvent` are examples. Compare your imports with the [event catalog](/events/), which lists every event the installed version defines.

New since 6.6.5: `LinkMicLayoutStateEvent`, `OecLiveShoppingEvent`, `SubNotifyEvent`, `SystemEvent`, and `ViewerPicksUpdateEvent` from the schema, and the custom events `SuperFanJoinEvent` (an existing super fan joins the room) and `SuperFanBoxEvent` (a super-fan gift box is delivered), alongside the existing `SuperFanEvent`.

`WebsocketResponseEvent` and `UnknownEvent` no longer subclass the fetch result. The envelope is on `event.raw`, so `event.cursor` becomes `event.raw.cursor`.

## Event fields

| 6.x | 7 |
| --- | --- |
| `event.type` | Removed. Use `event.get_type()`; the property collided with v3 message fields named `type`, such as `CapsuleEvent.type`. |
| `event.user_info` on `CommentEvent` | `event.user`. |
| `event.comment` | Still works as an alias; the v3 field is `event.content`. |
| `event.user.unique_id`, `event.user.nickname` | Still work. The v3 fields are `display_id` and `nickname`; the older `username`, `nick_name`, and `badges` names remain as read-only aliases for `display_id`, `nickname`, and `badge_list`. |
| `ControlAction.CONTROL_ACTION_STREAM_ENDED` | `ControlAction.STREAM_ENDED`; the other members drop the prefix the same way. `from TikTokLive.proto.custom_proto import ControlAction` still resolves. |
| `event.cursor` on `WebsocketResponseEvent` | `event.raw.cursor`; the whole fetch result is `event.raw`. |

Nested messages are typed `Optional`: `event.user`, `event.gift`, and similar can be `None`, and mypy reports an unguarded access. Check before reading.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(CommentEvent)
async def on_comment(event: CommentEvent) -> None:
    if event.user is None:
        return
    print(event.get_type(), event.user.unique_id, event.content)


if __name__ == "__main__":
    client.run()
```

## Gifts

`Gift` keeps the field names `name`, `type`, and `image`. Code that reads `gift_name`, `gift_type`, or `gift_image` keeps working through read-only aliases on `ExtendedGift`, the class of `GiftEvent.gift`; mypy does not see those aliases, so prefer the canonical names. `event.streaking`, `event.repeat_count`, `event.repeat_end`, and `ExtendedGift.streakable` are unchanged; see [gift streaks](/guides/gifts/).

## Client

The constructor is unchanged: `unique_id`, `platform` (`WebcastPlatform.WEB` or `WebcastPlatform.MOBILE`), `web_proxy`, `ws_proxy`, `web_kwargs`, `ws_kwargs`, and `is_user_id` keep their 6.6.5 meaning. See [options](/configuration/options/).

- `run()`, `connect()`, and `start()` spell out their keyword-only options instead of accepting `**kwargs`. A misspelled option is now a `TypeError` at the call site, and IDEs autocomplete them. See [connection lifecycle](/getting-started/connection/).
- `client.get_avatar_url()` is new: it returns the creator's avatar URL from the public profile page.
- `client.parse_error_ignorelist` is new: a list of substrings; a payload whose parse error matches one is logged at `DEBUG` instead of `ERROR`. `client.ignore_broken_payload` still silences the rest.
- The `send_room_like` and `send_room_gift` routes were removed; `send_room_chat()` remains. The optional `curl_cffi` dependency was dropped.
- `WebcastBlocked200Error` is now `WebcastBlockedError` and also covers blocks returned with status 400; the old name is kept as an alias.

## Signing

The default signing server moved from `tiktok.eulerstream.com` to `api.eulerstream.com`, and requests go through the [Euler Stream](https://www.eulerstream.com/) SDK. Override the host with `WebDefaults.tiktok_sign_url` or the `SIGN_API_URL` environment variable, and set an API key with `WebDefaults.tiktok_sign_api_key` or `SIGN_API_KEY`. See [signing](/configuration/signing/).

## Typing

The source is annotated and type-checked in the project's CI. Annotate handlers with the event they receive, as in the examples, and consult the generated [API reference](/api/) and [schema reference](/schema/) for the installed version's signatures and fields.
