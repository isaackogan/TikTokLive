---
title: Subscriptions and super fans
description: Barrage and envelope messages with the super-fan events derived from them, subscription notifications, and the subscription pin card.
sidebar:
  order: 5
---

Three custom events on this page are derived from two proto events: `SuperFanEvent` and `SuperFanJoinEvent` from `BarrageEvent`, and `SuperFanBoxEvent` from `EnvelopeEvent`. A derived event is emitted before its source, and the source is emitted too, so listen to one or the other. `SubNotifyEvent` and `SubPinEventEvent` are separate messages; not every subscription notification is a new purchase.

Each section names the Webcast message and links its schema page, which lists every field. Replace `@isaackogz` with a creator who is live. Each example registers its listener before connecting.

## BarrageEvent

A "VIP" viewer (based on gifting level) joins the chat room. Message: [`WebcastBarrageMessage`](/schema/webcast/model/message/webcastbarragemessage/).

A barrage is a highlighted banner in the chat: a high-level gifter or fan-club member entering, a subscription, a fan-level upgrade, a gift-gallery milestone. Key fields: `msg_type`, a `BarrageMessageBarrageType` such as `SUBSCRIBE`, `SUBSCRIBE_GIFT`, `USER_UPGRADE`, `GRADE_USER_ENTRANCE_NOTIFICATION`, `FANS_LEVEL_UPGRADE`, `FANS_LEVEL_ENTRANCE`, `GIFT_GALLERY`, or `COMMON_BARRAGE`; `content` and `common_barrage_content`, `Text` messages whose `default_pattern` is the rendered text and whose `key` identifies the template; `user`; `icon`, `right_icon`, and `background`; `duration`; `user_grade_param`, `fans_level_param`, `subscribe_gift_param`, and `gift_gallery_params`, one of which is set per `msg_type`; and `show_type` and `render_type`.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import BarrageEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(BarrageEvent)
async def on_barrage(event: BarrageEvent) -> None:
    text = event.content.default_pattern if event.content is not None else ""
    who = event.user.unique_id if event.user is not None else "someone"
    print(f"[{event.msg_type.name}] {who}: {text}")


if __name__ == "__main__":
    client.run()
```

## SuperFanEvent

A viewer became a super fan of the streamer. Custom event, a subclass of `BarrageEvent` with the same fields.

The client derives it from a barrage whose display text carries the `ttlive_superfan` marker, excluding the join variant below. Read `content` or `common_barrage_content` for the text and `user` for the viewer.

## SuperFanJoinEvent

An existing super fan joined the livestream. Custom event, a subclass of `BarrageEvent` with the same fields.

Derived from a barrage whose display text contains `ttlive_superfan_commentnotif_superfanjoined`. It is emitted instead of `SuperFanEvent`, never alongside it.

## EnvelopeEvent

A treasure chest / envelope was sent. Message: [`WebcastEnvelopeMessage`](/schema/webcast/model/message/redenvelope/webcastenvelopemessage/).

Key fields: `envelope_info`, a `MessageRedEnvelopInfo` with `envelope_id`, `business_type`, `send_user_id`, `send_user_name`, `send_user_avatar`, `diamond_count`, `people_count`, `unpack_at`, `create_at`, `room_id`, and `super_fan_count`; `display`, an `EnvelopeDisplay` value; and `public_area_msg_common`. The envelope is opened later, at `unpack_at`; the message announces it.

## SuperFanBoxEvent

A super-fan envelope (gift box) was delivered. Custom event, a subclass of `EnvelopeEvent` with the same fields.

Derived from an envelope whose `envelope_info.business_type` is the super-fan box value (`19`) or whose display text carries `ttlive_superfanbox`. `super_fan_count` on `envelope_info` is the number of super fans the box is for.

## SubNotifyEvent

Subscription notification (subscribe / renew / gift sub). Message: [`WebcastSubNotifyMessage`](/schema/webcast/model/message/webcastsubnotifymessage/).

Key fields: `user`; `message_type`, a `MessageType` that distinguishes `SUB_SUCCESS` from reminders, goal notices, and the `SUB_GIFT_*` gifted-subscription notices; `subscribe_type` (`ONCE` or `AUTO`); `old_subscribe_status`, `FIRST` for a new subscriber and `RESUB` for a renewal; `subscribing_status`; `sub_month`, the subscriber's month count; `is_send` and `gift_source` for gifted subscriptions; `is_custom`; `exhibition_type`; `message_display_style`; and `package_id`. Check `message_type` before treating the event as a purchase.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import SubNotifyEvent
from TikTokLiveProto.v3.webcast.im import MessageType

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(SubNotifyEvent)
async def on_sub(event: SubNotifyEvent) -> None:
    if event.message_type != MessageType.SUB_SUCCESS or event.user is None:
        return
    print(f"{event.user.unique_id} subscribed ({event.old_subscribe_status.name}, month {event.sub_month})")


if __name__ == "__main__":
    client.run()
```

## SubPinEventEvent

Subscription pin card action. Message: [`WebcastSubPinEventMessage`](/schema/webcast/model/message/webcastsubpineventmessage/).

Key fields: `action_type`, pin or `UNPIN`; `card`, a `SubPinCard` with `title`, `desc`, `image`, `type`, `id`, `time_to_live`, and `action_schema`; and `operator_user_id`. A pinned chat message is `RoomPinEvent` on [room messages and display](/events/room-and-display/#roompinevent) instead.
