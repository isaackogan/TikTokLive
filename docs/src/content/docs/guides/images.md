---
title: Download images
description: Fetch avatars, gift icons, and badges from TikTok's CDN with fetch_image_data, from an ImageModel on an event or from a plain URL.
sidebar:
  order: 5
---

Images on events are `ImageModel` messages, not bytes. An `ImageModel` carries `url_list`, one or more CDN URLs for the same picture; `uri`, TikTok's identifier for it; `width`, `height`, `avg_color`, and `is_animated`. The route `client.web.fetch_image_data(image)` downloads one: it accepts an `ImageModel`, from which it takes `url_list[0]`, or a URL `str`, and returns the bytes. The request uses the client's HTTP session, so a configured `web_proxy` and headers apply. This guide is a tightened version of the repository's `examples/images.py`.

Images appear on `user` as `avatar_thumb`, `avatar_medium`, and `avatar_large`, each `Optional`; events commonly populate only `avatar_thumb`. `user.badge_image_list` holds badge icons, `gift.image` and `gift.icon` the gift artwork, and `LikeEvent.icons` the like icons.

## Save a commenter's avatar

```python
from pathlib import PurePosixPath
from urllib.parse import urlparse

from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(CommentEvent)
async def on_comment(event: CommentEvent) -> None:
    user = event.user
    if user is None or user.avatar_thumb is None or not user.avatar_thumb.url_list:
        return

    image_bytes: bytes = await client.web.fetch_image_data(image=user.avatar_thumb)

    # The CDN URL's path carries the format, usually .webp or .jpeg
    suffix = PurePosixPath(urlparse(user.avatar_thumb.url_list[0]).path).suffix or ".webp"
    path = f"{user.unique_id or user.id}{suffix}"
    with open(path, "wb") as file:
        file.write(image_bytes)

    print(f"Saved {path} ({len(image_bytes)} bytes)")


if __name__ == "__main__":
    client.run(process_connect_events=False)
```

`process_connect_events=False` skips the comments bundled into the first signed response, so connecting does not download a backlog of avatars at once. The guard on `url_list` matters: an `ImageModel` can be present with no URLs, and the route indexes `url_list[0]`.

## Save each gift's artwork once

The same gift arrives many times in a busy room, and a streak sends one event per step. Download by `gift.id` and remember what you have:

```python
from pathlib import PurePosixPath
from typing import Set
from urllib.parse import urlparse

from TikTokLive import TikTokLiveClient
from TikTokLive.events import GiftEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
saved: Set[int] = set()


@client.on(GiftEvent)
async def on_gift(event: GiftEvent) -> None:
    gift = event.gift
    if gift is None or gift.image is None or not gift.image.url_list or gift.id in saved:
        return
    saved.add(gift.id)

    image_bytes: bytes = await client.web.fetch_image_data(gift.image)
    suffix = PurePosixPath(urlparse(gift.image.url_list[0]).path).suffix or ".webp"
    with open(f"gift-{gift.id}{suffix}", "wb") as file:
        file.write(image_bytes)


if __name__ == "__main__":
    client.run()
```

## Download from a URL

`client.get_avatar_url()` returns the creator's profile avatar as a URL, or `None`; see [checking live status](/guides/check-live/). Pass the string straight to `fetch_image_data`:

```python
import asyncio

from TikTokLive import TikTokLiveClient

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


async def main() -> None:
    try:
        url = await client.get_avatar_url()
        if url is None:
            print("No avatar found on the profile page")
            return

        image_bytes: bytes = await client.web.fetch_image_data(url)
        with open(f"{client.unique_id}-avatar.jpeg", "wb") as file:
            file.write(image_bytes)
    finally:
        await client.web.close()


if __name__ == "__main__":
    asyncio.run(main())
```

`client.web.fetch_image` is the 6.x name for this route. It still works and logs a deprecation warning on each use unless `SEND_DEPRECATION_WARNINGS` is turned off; see [debugging events](/guides/debugging-events/).
