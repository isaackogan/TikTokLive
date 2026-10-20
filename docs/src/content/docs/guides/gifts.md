---
title: Gift streaks
description: Count a streaked gift once when the streak ends, tell streakable gifts apart, read the room's gift catalog, and use the v3 field names and their aliases.
sidebar:
  order: 1
---

`GiftEvent` fires for every gift message TikTok sends. Its fields include `gift`, the gift's static description; `gift_id`; `repeat_count` and `repeat_end`, which describe a streak; `user`, the sender; and `to_user`, the recipient in a multi-host room. The full field list is on the [gift events page](/events/gifts-and-goals/#giftevent). This guide is a tightened version of the repository's `examples/gifts.py`.

## Count a streak once

A viewer can hold the gift button to send the same gift repeatedly. TikTok reports the streak as a series of `GiftEvent`s: one per step with `repeat_count` climbing, then a final one with `repeat_end == 1` that carries the total. `repeat_count` is cumulative, so adding it up across the series overcounts.

The property `streaking` is `True` for the intermediate messages and `False` for the final one, and always `False` for a gift that cannot streak. A handler that returns while `event.streaking` counts each gift once, at the end of its streak, without checking the gift's type:

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, GiftEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent) -> None:
    print(f"Connected to @{event.unique_id}")


@client.on(GiftEvent)
async def on_gift(event: GiftEvent) -> None:
    gift = event.gift
    if gift is None or event.user is None:
        return

    # One event per step while the streak runs; act on the final one only
    if event.streaking:
        return

    diamonds = event.repeat_count * gift.diamond_count
    print(f"{event.user.unique_id} sent {event.repeat_count}x \"{gift.name}\" ({diamonds} diamonds)")


if __name__ == "__main__":
    client.run()
```

To show a streak while it runs, replace the displayed count with the latest `repeat_count` rather than adding to it. `group_id` and the sender help tell concurrent streaks apart.

## Streakable and non-streakable gifts

Whether a gift can streak is a property of the gift, not of the message: `gift.type == 1` means streakable. `event.gift` is an `ExtendedGift`, which exposes that test as the `streakable` property. A non-streakable gift arrives as a single `GiftEvent` with `streaking` equal to `False`, so the handler above needs no special case; branch on `streakable` only when the two kinds should be reported differently:

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import GiftEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(GiftEvent)
async def on_gift(event: GiftEvent) -> None:
    gift = event.gift
    if gift is None or event.user is None:
        return

    if not gift.streakable:
        print(f"{event.user.unique_id} sent \"{gift.name}\"")
    elif event.streaking:
        print(f"{event.user.unique_id} is streaking \"{gift.name}\": {event.repeat_count} so far")
    else:
        print(f"{event.user.unique_id} sent {event.repeat_count}x \"{gift.name}\"")


if __name__ == "__main__":
    client.run()
```

`event.value` is `repeat_count * gift.diamond_count * 0.005`, an estimate in USD, and is `None` while `streaking` is `True` so that a running total does not double-count. The diamond count is TikTok's price metadata, not a payout; what a creator receives is decided by TikTok's accounting, not by this event.

## The room's gift catalog

`fetch_gift_info=True` on `run()`, `start()`, or `connect()` fetches the room's gift catalog once, before the socket opens, and stores it on `client.gift_info`. It is TikTok's response as a plain `dict`; its `gifts` entry is a list of gift dicts with `id`, `name`, `type`, `diamond_count`, `describe`, and `image`, among other keys. `client.gift_info` is `None` until a connection made with the option, and `disconnect()` resets it to `None`, so copy what you need.

Index the catalog by ID to describe a gift from `gift_id` alone, or to list what a room offers:

```python
from typing import Any, Dict

from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, GiftEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
catalog: Dict[int, Dict[str, Any]] = {}


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent) -> None:
    if client.gift_info is None:
        return
    for gift in client.gift_info.get("gifts", []):
        catalog[int(gift["id"])] = gift
    print(f"{len(catalog)} gifts in this room's catalog")


@client.on(GiftEvent)
async def on_gift(event: GiftEvent) -> None:
    if event.streaking:
        return
    info = catalog.get(event.gift_id)
    name = info["name"] if info else "unknown gift"
    diamonds = int(info["diamond_count"]) if info else 0
    print(f"{event.repeat_count}x {name}, {diamonds} diamonds each")


if __name__ == "__main__":
    client.run(fetch_gift_info=True)
```

The same `dict` is available without connecting from the route `client.web.fetch_gift_list()`. The request is not signed, so it costs no signing-provider quota.

## Field names and aliases

In v3 the `Gift` fields are `id`, `name`, `type`, `image`, `diamond_count`, and `describe`. Code written for 6.x that reads `gift_name`, `gift_type`, or `gift_image` keeps working through read-only aliases on `ExtendedGift`; mypy does not see the aliases, so prefer the canonical names in new code. See the [migration guide](/getting-started/migration/). `gift.image` is an `ImageModel`; the [images guide](/guides/images/) shows how to download it.

## Related events

Goal progress, gift broadcasts, panel updates, prompts, and restrictions have their own events on the [gifts and goals page](/events/gifts-and-goals/). They describe the room's gifting state and are not additional paid gifts.
