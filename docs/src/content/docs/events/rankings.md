---
title: Rankings
description: Hourly rank rewards, leaderboard entrance updates, rank text, and game-rank notifications.
sidebar:
  order: 7
---

Ranking messages describe the room's position on TikTok's leaderboards and viewers' positions in the room's contributor list. They accompany gifts rather than replacing `GiftEvent`, and none of them carries a complete leaderboard.

Each section names the Webcast message and links its schema page, which lists every field. Replace `@isaackogz` with a creator who is live. Each example registers its listener before connecting.

## HourlyRankRewardEvent

Hourly rank reward delivered. Message: [`WebcastHourlyRankRewardMessage`](/schema/webcast/model/message/webcasthourlyrankrewardmessage/).

Key fields: `winners`, a list of `HourlyRankRewardInfo` with `user_id`, `asset_id`, `notify`, and `avatar_border`.

## RankUpdateEvent

Room ranking entrance updated (rank types, current rank, and tabs). Message: [`WebcastRankUpdateMessage`](/schema/webcast/model/message/webcastrankupdatemessage/).

Key fields: `updates`, a list of `RankUpdate` with `rank_type`, `own_rank`, `current_score`, `default_content`, `prompt`, `countdown`, `class_info`, and `list_schema`; `group_type`; `op_type`, an `OpType` of `ADD`, `REMOVE`, `RELOAD`, or `BASIC_EFFECT`; `rank_priority`; `tabs` and `tab_info`; `union_animation`; `is_animation_loop_play`; and `valid_ranks`.

## RankTextEvent

Gift count made a viewer enter the top three. Message: [`WebcastRankTextMessage`](/schema/webcast/model/message/webcastranktextmessage/).

Key fields: `scene`, a `RankTextMessageRankTestMessageScene` such as `ONLINE_AUDIENCE_TOP_N_UPDATE_PUBLIC_SCREEN`; `owner_idx_before_update` and `owner_idx_after_update`, the viewer's position before and after; `cur_user_id`; `content`, `self_get_badge_msg`, and `other_get_badge_msg`, `Text` messages for the viewer and for everyone else; `left_icon`; `rank_type`; and `user_enigma_info`.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import RankTextEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(RankTextEvent)
async def on_rank_text(event: RankTextEvent) -> None:
    text = event.content.default_pattern if event.content is not None else ""
    print(f"User {event.cur_user_id}: #{event.owner_idx_before_update} -> #{event.owner_idx_after_update} {text}")


if __name__ == "__main__":
    client.run()
```

## GameRankNotifyEvent

Game-rank notification. Message: [`WebcastGameRankNotifyMessage`](/schema/webcast/model/message/webcastgameranknotifymessage/).

Key fields: `msg_type`, a `GameRankNotifyMessageMsgType` of `MSG_TYPE_RANK_IN_OUT`, `MSG_TYPE_RANK_CHANGE`, or `MSG_TYPE_ANCHOR_ENCOURAGE`; and `notify_text`, a `Text`.
