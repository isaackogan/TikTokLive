---
title: Gifts and goals
description: GiftEvent with streak handling and the ExtendedGift helpers, goal updates, boost cards, gift broadcasts, restrictions, panel updates, and gift prompts.
sidebar:
  order: 3
---

A sent gift arrives as `GiftEvent`; the other events on this page describe the gift panel, goals, and notices around gifting and are not gifts themselves. Envelopes (treasure chests) are on [subscriptions and super fans](/events/subscriptions-and-fans/#envelopeevent) with the super-fan box derived from them.

Each section names the Webcast message and links its schema page, which lists every field. Replace `@isaackogz` with a creator who is live. Each example registers its listener before connecting.

## GiftEvent

A gift was sent (see Gift handling below). Message: [`WebcastGiftMessage`](/schema/webcast/model/message/webcastgiftmessage/).

Key fields: `gift`, an `ExtendedGift` with the schema's `id`, `name`, `type`, `diamond_count`, `image`, and `describe` plus the `streakable` property (`type == 1`); `gift_id`; `repeat_count`, the number of this gift sent so far in the streak; `repeat_end`, `1` on the final message of a streak; `combo_count` and `group_count`; `user`, the sender, and `to_user`, the recipient in a multi-host room; `fan_ticket_count` and `room_fan_ticket_count`; `is_first_sent`; `send_type`; `order_id`; `display_text_for_audience`; `gifts_in_box` for box gifts; and `user_identity`. The 6.x names `gift_name`, `gift_type`, and `gift_image` remain as read-only aliases on `ExtendedGift`; mypy does not see them, so prefer the schema names.

Gift handling: a streakable gift (`gift.type == 1`) produces one `GiftEvent` per step as the viewer holds the button, with `repeat_count` climbing, and a final one with `repeat_end == 1`. The property `streaking` is `True` for the intermediate messages and `False` for the final one and for every non-streakable gift, so a handler that returns while `event.streaking` counts each gift once. The property `value` is `repeat_count * gift.diamond_count * 0.005`, an estimate in USD, and is `None` mid-streak for the same reason. `user_is_super_fan` reads `user_identity.is_subscriber_of_anchor`.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import GiftEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(GiftEvent)
async def on_gift(event: GiftEvent) -> None:
    gift = event.gift
    if gift is None or event.user is None:
        return

    # A streakable gift sends one event per step; act on the final one only
    if event.streaking:
        return

    total = event.repeat_count * gift.diamond_count
    print(f"{event.user.unique_id} sent {event.repeat_count}x \"{gift.name}\" ({total} diamonds)")


if __name__ == "__main__":
    client.run()
```

Static metadata for every gift in the room is fetched once on connect with `fetch_gift_info=True` on `run()`, `start()`, or `connect()` and cached on `client.gift_info`. See [gift streaks](/guides/gifts/) for a complete walkthrough.

## GoalUpdateEvent

Subscriber/follow goal updated. Message: [`WebcastGoalUpdateMessage`](/schema/webcast/model/gift/model/webcastgoalupdatemessage/).

Key fields: `goal`, a `LiveStreamGoal` with `id`, `type`, `status`, `description`, `sub_goals`, `contributors`, `start_time`, and `expire_time`; `indicator`; `contribute_subgoal`, the `LiveStreamSubGoal` this update advanced, with `progress`, `target`, and the `gift` it counts; `contribute_count` and `contribute_score`; `contributor_id`, `contributor_display_id`, and `contributor_avatar`; `gift_repeat_count`; `pin_info`; and `update_source`. A goal update accompanies a gift or follow and is not a second gift.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import GoalUpdateEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(GoalUpdateEvent)
async def on_goal(event: GoalUpdateEvent) -> None:
    subgoal = event.contribute_subgoal
    if event.goal is None or subgoal is None:
        return
    print(f"{event.goal.description}: {subgoal.progress}/{subgoal.target} (+{event.contribute_count} from {event.contributor_display_id})")


if __name__ == "__main__":
    client.run()
```

## BoostCardEvent

Boost cards delivered to the room. Message: [`WebcastBoostCardMessage`](/schema/webcast/model/message/webcastboostcardmessage/).

Key fields: `cards`, a list of `BoostCard` with `m_card_id`, `task_source`, and `task_id`. Boost cards are a room promotion feature, not the battle Power-Ups of `LinkMicBattleItemCardEvent`.

## GiftBroadcastEvent

Big gift broadcast notice across rooms. Message: [`WebcastGiftBroadcastMessage`](/schema/webcast/model/message/webcastgiftbroadcastmessage/).

Key fields: `from_user_id`; `left_icon`; and `notify`, a nested `WebcastRoomNotifyMessage` whose `content` holds the banner text and whose `schema` links the originating room. The notice is informational and is not a `GiftEvent` for this room.

## GiftDynamicRestrictionEvent

Dynamic gift restriction update. Message: [`WebcastGiftDynamicRestrictionMessage`](/schema/webcast/model/message/webcastgiftdynamicrestrictionmessage/).

Key fields: `dynamic_restriction`, with `scenes` and `receivers` describing where and to whom gifting is currently restricted.

## GiftPanelUpdateEvent

Gift panel content update. Message: [`WebcastGiftPanelUpdateMessage`](/schema/webcast/model/message/webcastgiftpanelupdatemessage/).

Key fields: `room_id`; `timestamp`; `gallery_data`, with `progress`, `period`, and `end_time_in_ms` for the gift gallery; `goal_data`, with `status` and `goal_progress`; `room_based_gift_data`; and `strategy_context`.

## GiftPromptEvent

Anti-addiction / spending-limit prompt before gifting. Message: [`WebcastGiftPromptMessage`](/schema/webcast/model/message/webcastgiftpromptmessage/).

Key fields: `title` and `body`, the prompt text; `block_num_days`; `order_id` and `order_timestamp`; `in_user_gifting_addiction_expr`; and `pop_up_schema`. A prompt is shown to the viewer before a gift and does not mean a gift was sent.
