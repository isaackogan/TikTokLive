---
title: Room messages and display
description: Announcements, captions, polls, pins, banners, toasts, and the other presentation messages a room sends, with their fields.
sidebar:
  order: 6
---

These events carry what TikTok draws in the room besides chat: the welcome banner, auto-captions, polls, pinned messages, prompts, and notices. Several carry a `Text` message rather than a string; its `default_pattern` is the rendered text and its `key` names the template. Barrage banners are on [subscriptions and super fans](/events/subscriptions-and-fans/#barrageevent).

Each section names the Webcast message and links its schema page, which lists every field. Replace `@isaackogz` with a creator who is live. Each example registers its listener before connecting.

## LiveIntroEvent

Live-intro message appears. Message: [`WebcastLiveIntroMessage`](/schema/webcast/model/message/webcastliveintromessage/).

Key fields: `id`; `content`, the creator's intro text; `user`; `intro_mode`; `audit_status`; `badges`; and `content_language`. It can arrive during the session, not only at connect.

## SystemEvent

A plain-text system message from TikTok. Message: [`WebcastSystemMessage`](/schema/webcast/im/webcastsystemmessage/).

Key fields: `message`, the text. It is not an error from the client; those are raised as exceptions.

## RoomEvent

Broadcast message to all room users (e.g. "Welcome to TikTok LIVE!"). Message: [`WebcastRoomMessage`](/schema/webcast/model/message/webcastroommessage/).

Key fields: `content`, the text; `is_welcome`, set on the welcome notice; `source`, `scene`, and `sub_scene`; `icon`; `show_duration_ms`; `schema`; and `supprot_landscape` (the schema's spelling).

## CaptionEvent

Auto-caption update from the host's audio. Message: [`WebcastCaptionMessage`](/schema/webcast/model/message/webcastcaptionmessage/).

Key fields: `content`, a list of `CaptionContent` with `lang` and `content`, one per language; `timestamp_ms` and `duration_ms`; `sentence_id` and `sequence_id`; and `definite`, `True` once the sentence is final. Interim captions for the same `sentence_id` are replaced by later ones.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CaptionEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(CaptionEvent)
async def on_caption(event: CaptionEvent) -> None:
    if not event.definite:
        return
    for caption in event.content:
        print(f"[{caption.lang}] {caption.content}")


if __name__ == "__main__":
    client.run()
```

## InRoomBannerEvent

In-room banner notice. Message: [`WebcastInRoomBannerMessage`](/schema/webcast/model/message/webcastinroombannermessage/).

The installed v3 schema defines only `common` for this message; the 6.x `json_data` field is gone.

## PollEvent

The creator launched / updated a poll. Message: [`WebcastPollMessage`](/schema/webcast/model/message/webcastpollmessage/).

Key fields: `message_type` and `poll_id`; `poll_kind`; `poll_basic_info`, with `title`, `poll_duration`, `time_remain`, `user_cnt`, and `gift_id`; `start_content`, with `start_time`, `end_time`, `option_list`, `title`, and `operator`; `update_votes_content`, with the current `option_list`; `end_content`; and `template_content`. The client keeps no poll state; read the option list from each update.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import PollEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(PollEvent)
async def on_poll(event: PollEvent) -> None:
    info = event.poll_basic_info
    if info is not None:
        print(f"Poll: {info.title} ({info.time_remain}s left)")
    if event.update_votes_content is not None:
        print(f"Options: {event.update_votes_content.option_list}")


if __name__ == "__main__":
    client.run()
```

## RoomPinEvent

A message was pinned. Message: [`WebcastRoomPinMessage`](/schema/webcast/model/message/webcastroompinmessage/).

Key fields: `action`, a `PinMessageActionType` of `PIN` or `PIN_CANCEL`; `operator`, the `ExtendedUser` who pinned it; `method`, the pinned message's method name; `pin_msg_id`, `pin_time`, and `display_duration`; and the pinned message itself in one of `chat_message`, `social_message`, `gift_message`, `member_message`, or `like_message`, which are plain v3 messages rather than events.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import RoomPinEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(RoomPinEvent)
async def on_pin(event: RoomPinEvent) -> None:
    who = event.operator.unique_id if event.operator is not None else "someone"
    if event.chat_message is not None:
        print(f"{who} pinned: {event.chat_message.content}")
    else:
        print(f"{who} {event.action.name} a {event.method}")


if __name__ == "__main__":
    client.run()
```

## BottomEvent

Bottom-of-screen notice (often a punishment or violation banner). Message: [`WebcastBottomMessage`](/schema/webcast/model/message/webcastbottommessage/).

Key fields: `content`, the text; `show_type`, `text_type`, and `biz_type`; `duration`; `violation_user_id` and `punish_info`, with `punish_type`, `punish_reason`, `duration`, and `end_time`; `style` and `float_style`; `detail_url`; and `float_icon_type`.

## CapsuleEvent

In-room capsule / promotional pill notice. Message: [`WebcastCapsuleMessage`](/schema/webcast/model/message/webcastcapsulemessage/).

Key fields: `icon`; `desc` and `button_text`, both `Text`; `schema`, the deep link the button opens; `type`, `scene`, `sub_scene`, and `style`; `biz_params`, with one nested message per capsule kind (`cohost`, `random_gift`, `multi_guest_invite_guide`, `anchor_pin_perk`, `ecom`, and others); `skip_fc`; and `report_action`. The 6.x `event.type` alias was removed because it collided with this message's `type` field.

## GuideEvent

In-room guide / tooltip prompt. Message: [`WebcastGuideMessage`](/schema/webcast/model/message/webcastguidemessage/).

Key fields: `guide_type`; `gift_id`, when the guide promotes a gift; `description`; `duration`; `display_style`; `scene`; and `frequency_rule`, with `room_show_count` and `day_show_count`. Receiving a guide does not mean the viewer followed it.

## MarqueeAnnouncementEvent

Marquee announcement scrolling across the room. Message: [`WebcastMarqueeAnnouncementMessage`](/schema/webcast/model/message/webcastmarqueeannouncementmessage/).

Key fields: `message_scene` and `message_entity`, a list of `MessageEntity` each with a `notify`.

## NoticeEvent

Generic notice / system tip in the room. Message: [`WebcastNoticeMessage`](/schema/webcast/model/message/webcastnoticemessage/).

Key fields: `content`, a string; `notice_type` and `style`; `title`, `notice_title`, `notice_content`, and `display_text`, all `Text`; `violation_reason`; `tips_title` and `tips_url`; and `scene`.

## RoomNotifyEvent

Room-wide notification banner. Message: [`WebcastRoomNotifyMessage`](/schema/webcast/model/message/webcastroomnotifymessage/).

Key fields: `content`, the text; `notify_type` and `notify_class`; `schema`, a deep link; `source`; `from_user_id` and `to_anchor_id`; `user`; `extra`, with `duration`, `background`, and `content_list`; `flex_setting`; and `privilege_log_extra`. `GiftBroadcastEvent` nests one of these messages.

## ToastEvent

Transient toast notification. Message: [`WebcastToastMessage`](/schema/webcast/model/message/webcasttoastmessage/).

Key fields: `display_duration_millisecond`, `delay_display_duration_millisecond`, and `scene`. The text, when present, is in `common.display_text`.

## ViewerPicksUpdateEvent

Viewer-picks (audience-driven prompt) update. Message: [`WebcastViewerPicksUpdateMessage`](/schema/webcast/model/message/webcastviewerpicksupdatemessage/).

Key fields: `update_type` and `info`, a `ViewerPicksInfo` with `viewer_picks_id`, `gift_pick_list`, `status`, `round_duration_sec`, `start_time_ms`, `end_time_ms`, `display_mode`, `scene`, and the auto-restart flags.
