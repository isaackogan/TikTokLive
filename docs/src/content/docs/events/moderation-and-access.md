---
title: Moderation and access
description: Message deletions, unauthorized viewers, delivery probes, room verification, access control, access recall, and perception warnings.
sidebar:
  order: 8
---

These are notifications the room receives. Listening to them grants no moderation permission and performs no action; a `client` connected as a viewer sees what a viewer sees.

Each section names the Webcast message and links its schema page, which lists every field. Replace `@isaackogz` with a creator who is live. Each example registers its listener before connecting.

## ImDeleteEvent

A viewer's messages were deleted by a moderator. Message: [`WebcastImDeleteMessage`](/schema/webcast/model/message/webcastimdeletemessage/).

Key fields: `delete_msg_ids`, the message IDs to remove, and `delete_user_ids`, users whose messages were removed. A comment's ID is `event.common.msg_id` on the `CommentEvent` that delivered it.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ImDeleteEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
comments: dict[int, str] = {}


@client.on(CommentEvent)
async def on_comment(event: CommentEvent) -> None:
    if event.common is not None:
        comments[event.common.msg_id] = event.content


@client.on(ImDeleteEvent)
async def on_delete(event: ImDeleteEvent) -> None:
    for msg_id in event.delete_msg_ids:
        print(f"Deleted: {comments.pop(msg_id, '<unknown>')}")


if __name__ == "__main__":
    client.run()
```

## UnauthorizedMemberEvent

An unauthorized viewer entered the room (nickname and entry text only, no user object). Message: [`WebcastUnauthorizedMemberMessage`](/schema/webcast/model/message/webcastunauthorizedmembermessage/).

Key fields: `action`; `nick_name` and `nick_name_prefix`, a `Text`; `enter_text`, a `Text`; and `public_area_common`. There is no `user` field.

## MessageDetectEvent

Message-delivery probe carrying detection flags and timing information. Message: [`WebcastMsgDetectMessage`](/schema/webcast/model/message/webcastmsgdetectmessage/).

Key fields: `d_type`; `t_condition`, with the flags `uplink_detect_http`, `uplink_detect_websocket`, `detect_p2p_msg`, `detect_room_msg`, and `http_optimize`; `t_info`, with `client_start_ms`, `api_recv_time_ms`, and `api_send_to_goim_ms`; `trigger_by`; and `from_region`. It is diagnostic and does not describe a moderation outcome.

## RoomVerifyEvent

Room verification action (e.g. forced verify / close). Message: [`WebcastRoomVerifyMessage`](/schema/webcast/model/message/webcastroomverifymessage/).

Key fields: `action`; `content`, the text; `notice_type`; and `close_room`, `True` when the room is being closed.

## AccessControlEvent

Access-control update for the room (e.g. CAPTCHA challenge issued to a viewer). Message: [`WebcastAccessControlMessage`](/schema/webcast/model/message/webcastaccesscontrolmessage/).

Key fields: `captcha`, with `captcha_record_id`, `room_id`, and `verify_duration_in_sec`. The client does not solve a CAPTCHA.

## AccessRecallEvent

Access restriction lifted / recalled for a viewer. Message: [`WebcastAccessRecallMessage`](/schema/webcast/model/game/webcastaccessrecallmessage/).

Key fields: `status`; `duration` and `end_time`; `scene`; `notice` and `content`, both `Text`; and `punish_info`.

## PerceptionEvent

Perception dialog (warning / violation surfaced to a viewer). Message: [`WebcastPerceptionMessage`](/schema/webcast/model/message/webcastperceptionmessage/).

Key fields: `dialog`, a `PerceptionDialogInfo` with `title`, `sub_title`, `scene`, `target_user_id`, `target_room_id`, `count_down_time`, `policy_tip`, and `violation_detail_url`; `punish_info`; `end_time`; `show_violation_warning`; `toast` and `float_text`, both `Text`; `float_style` and `float_icon_type`; and `sheet`.
