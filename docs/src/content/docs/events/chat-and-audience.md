---
title: Chat and audience
description: Comments, joins, viewer counts, likes, follows, shares, questions, and emotes, with the fields each event carries and examples for the common ones.
sidebar:
  order: 2
---

Chat, membership, reactions, and social activity. The sender is nested under `event.user` as an `ExtendedUser`, which adds helpers to the schema's `User`: `unique_id` (the `@`-handle, an alias of `display_id`), `nickname`, `is_moderator`, `is_top_gifter`, `is_friend`, `member_level`, `gifter_level`, and `has_badge()`. The field is `Optional`, so check it before reading.

Each section names the Webcast message and links its schema page, which lists every field. Replace `@isaackogz` with a creator who is live. Each example registers its listener before connecting.

## CommentEvent

A viewer sent a chat comment. Message: [`WebcastChatMessage`](/schema/webcast/model/message/webcastchatmessage/).

Key fields: `content`, the text (`comment` is a read-only alias from 6.x); `user`; `at_user`, the `ExtendedUser` a reply is addressed to, and `mention_users`, the plain `User` objects mentioned in the text; `emotes`, a list of `EmoteWithIndex` whose `index` is the position in `content` and whose `emote` has an `emote_id` and `image`; `content_language`; `comment_tag`; `user_identity`; and `visible_to_sender`, set when the comment was shown only to its sender. The property `user_is_super_fan` reads `user_identity.is_subscriber_of_anchor`.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(CommentEvent)
async def on_comment(event: CommentEvent) -> None:
    if event.user is None:
        return
    badge = " [mod]" if event.user.is_moderator else ""
    emotes = [emote.emote.emote_id for emote in event.emotes if emote.emote is not None]
    print(f"{event.user.unique_id}{badge}: {event.content} {emotes or ''}")


if __name__ == "__main__":
    client.run()
```

## JoinEvent

A viewer joined the livestream. Message: [`WebcastMemberMessage`](/schema/webcast/model/message/webcastmembermessage/).

Key fields: `user`; `member_count`, the room's member count when the message was sent; `action`, a `MemberMessageAction` (`JOINED` or `SUBSCRIBED`); `action_description`; `operator`, set when the action was performed on the user; `is_top_user`, `top_user_no`, and `rank_score` for ranked viewers; `enter_type`, `client_enter_source`, and `client_enter_type`; `is_set_to_admin` and `admin_permissions`; and `anchor_display_text`. TikTok does not send a join for every viewer, so the number of `JoinEvent`s is not the viewer count; use `RoomUserSeqEvent` for that.

## RoomUserSeqEvent

Current viewer count information. Message: [`WebcastRoomUserSeqMessage`](/schema/webcast/model/message/webcastroomuserseqmessage/).

Key fields: `total`, the viewer count TikTok shows in the room; `ranks`, the top contributors as `Contributor` objects with a plain `user`, a `score`, a `rank`, and a `delta`; `seats`, more `Contributor` objects; and the counters `total_user`, `popularity`, `anonymous`, and `pop_str`. The message arrives periodically, not on every join or leave.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import RoomUserSeqEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(RoomUserSeqEvent)
async def on_viewers(event: RoomUserSeqEvent) -> None:
    print(f"{event.total} viewers")
    for contributor in event.ranks:
        if contributor.user is None:
            continue
        print(f"  #{contributor.rank} {contributor.user.display_id}: {contributor.score}")


if __name__ == "__main__":
    client.run()
```

## LikeEvent

The stream received likes. Message: [`WebcastLikeMessage`](/schema/webcast/model/message/webcastlikemessage/).

Key fields: `count`, the likes in this update; `total`, the room's running total; `user`, the viewer the update is attributed to; `icon` and `icons`; `like_effect`; `specified_display_text`; and `room_message_heat_level`. TikTok batches likes, and busy rooms drop individual updates, so count with `count` and reconcile with `total` rather than assuming one event per tap.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import LikeEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(LikeEvent)
async def on_like(event: LikeEvent) -> None:
    who = event.user.unique_id if event.user is not None else "someone"
    print(f"{who} sent {event.count} likes ({event.total} total)")


if __name__ == "__main__":
    client.run()
```

## SocialEvent

A viewer shared or followed the host (also surfaced as `FollowEvent` / `ShareEvent` custom events). Message: [`WebcastSocialMessage`](/schema/webcast/model/message/webcastsocialmessage/).

Key fields: `user`; `action`; `share_type`, `share_target`, `share_count`, and `share_display_style` for shares; `follow_count` and `follow_type` for follows; `target_user_id`; `scene`; and `show_duration_ms`. The client reads `common.display_text.key` and emits `FollowEvent` when it contains `follow` or `ShareEvent` when it contains `share`, before emitting the `SocialEvent` itself. Listen to `SocialEvent` for everything, or to the two derived events for the cases they cover.

## FollowEvent

A viewer followed the streamer. Custom event, a subclass of `SocialEvent` with the same fields; see above.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import FollowEvent, ShareEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(FollowEvent)
async def on_follow(event: FollowEvent) -> None:
    if event.user is not None:
        print(f"{event.user.unique_id} followed")


@client.on(ShareEvent)
async def on_share(event: ShareEvent) -> None:
    if event.user is not None:
        print(f"{event.user.unique_id} shared the stream, {event.users_joined or 0} joined from it")


if __name__ == "__main__":
    client.run()
```

## ShareEvent

A viewer shared the livestream. Custom event, a subclass of `SocialEvent` with the same fields.

The property `users_joined` parses the number of viewers who joined from the share out of the display-text key, which TikTok writes as `pm_mt_guidance_viewer_<n>_share` for that notice, and returns `None` for an ordinary share.

## QuestionNewEvent

Someone asked a new question via the question feature. Message: [`WebcastQuestionNewMessage`](/schema/webcast/model/message/webcastquestionnewmessage/).

Key fields: `data`, a `Question` with `question_id`, `content`, `user` (a plain `User`), `create_time`, `answer_status`, `create_from`, and `answer_from`. Questions are separate from chat and do not also arrive as `CommentEvent`.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import QuestionNewEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(QuestionNewEvent)
async def on_question(event: QuestionNewEvent) -> None:
    question = event.data
    if question is None or question.user is None:
        return
    print(f"{question.user.display_id} asked: {question.content}")


if __name__ == "__main__":
    client.run()
```

## EmoteChatEvent

A custom emote was sent in chat. Message: [`WebcastEmoteChatMessage`](/schema/webcast/model/message/webcastemotechatmessage/).

Key fields: `user`; `emote_list`, the `EmoteModel` objects sent, each with an `emote_id`, an `image` whose `url_list` holds the picture, an `emote_type`, and a `package_id`; `msg_filter`; and `user_identity`. The message has no text; a comment that mixes text and emotes arrives as `CommentEvent` with `emotes` set.
