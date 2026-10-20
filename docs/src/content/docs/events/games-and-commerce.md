---
title: Games, commerce, and partnerships
description: Live shopping, live game intros, and partnership drops, game-offline, and punishment notices.
sidebar:
  order: 9
---

These messages announce shop products, live games, and partnership campaigns in the room. The client forwards them as they arrive; it fetches no catalog and completes no purchase.

Each section names the Webcast message and links its schema page, which lists every field. Replace `@isaackogz` with a creator who is live. Each example registers its listener before connecting.

## OecLiveShoppingEvent

Live-shopping signal. Message: [`WebcastOecLiveShoppingMessage`](/schema/webcast/model/message/ext/webcastoecliveshoppingmessage/).

Key fields: `action_type`; `live_product_number`; `pop_product`, the pinned `PopProduct` with `title`, `price`, `image_url`, `open_url`, `product_id`, and `product_status`; `product_snap_shot`; `hot_tags`; `promotion_info` and `voucher`; `billboard_info`; `card_type` and `pin_card_delay_time`; `flash_sale_atmosphere_info`; and `oec_live_shopping_message_v2`.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import OecLiveShoppingEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(OecLiveShoppingEvent)
async def on_shopping(event: OecLiveShoppingEvent) -> None:
    product = event.pop_product
    if product is not None:
        print(f"Pinned product: {product.title} at {product.price}")


if __name__ == "__main__":
    client.run()
```

## LiveGameIntroEvent

Live-game intro message. Message: [`WebcastLiveGameIntroMessage`](/schema/webcast/model/message/webcastlivegameintromessage/).

Key fields: `content`, a `Text`, and `has_rank_info`. Rank changes for the game arrive as `GameRankNotifyEvent` on [rankings](/events/rankings/#gameranknotifyevent).

## PartnershipDropsUpdateEvent

Partnership drops campaign update. Message: [`WebcastPartnershipDropsUpdateMessage`](/schema/webcast/model/message/webcastpartnershipdropsupdatemessage/).

Key fields: `change_mode`, `CHANGE_MODE_SHOW`, `CHANGE_MODE_UPDATE`, or `CHANGE_MODE_CLOSE`; `drops_id`, `task_id`, and `event_id`; and `anchor_uid`. An update is not a claimed reward.

## PartnershipGameOfflineEvent

Partnership game taken offline. Message: [`WebcastPartnershipGameOfflineMessage`](/schema/webcast/model/message/webcastpartnershipgameofflinemessage/).

Key fields: `offline_game_list`, a list of `OfflineGameInfo` with `game_id`, `task_id`, `task_type`, `offline_type`, `toast_title`, and `toast_text`. It concerns the game, not the stream; a stream ending is `LiveEndEvent`.

## PartnershipPunishEvent

Partnership punishment notice. Message: [`WebcastPartnershipPunishMessage`](/schema/webcast/model/message/webcastpartnershippunishmessage/).

Key fields: `punish_info`, with `punish_type`, `punish_reason`, `duration`, and `end_time`. It is distinct from the battle punishment phase of `LinkMicBattlePunishFinishEvent`.
