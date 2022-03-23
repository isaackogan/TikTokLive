import asyncio
import random
from typing import List

import aiohttp

from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import CommentEvent, ConnectEvent

# Instantiate the client with the user's username
client: TikTokLiveClient = TikTokLiveClient(unique_id="@tofy_love1")
queue: List[dict] = []


# Append to queue
@client.on("comment")
async def on_comment(event: CommentEvent):
    queue.append({
        "username": event.user.nickname,
        "avatar_url": event.user.profilePicture.avatar_url,
        "content": event.comment
    })

    print(f"{event.user.nickname} -> {event.comment}")


@client.on("connect")
async def on_connect(event: ConnectEvent):
    # Run through the queue
    while client.connected:
        if len(queue) > 0:
            async with aiohttp.ClientSession() as session:
                await session.post(url=random.choice(webhook_urls), json=queue.pop(0))

        await asyncio.sleep(delay_per_message)


if __name__ == '__main__':
    # Discord rate limits are pretty intense, so create 5 or 6 webhooks
    # in your desired channel & put them in a list to pick from randomly each time
    webhook_urls: List[str] = [
        "https://discord.com/api/webhooks/946268165187440700/H6twuzSYNiG_i2hL2anIlzfe_5YwV9cCNlu2waNaOFv593v5ULolskSfa2GeWc2ILCDC",
        "https://discord.com/api/webhooks/946268157713211422/anVZUmR5o27E6efkPhS0xzmlzhBc3cflghPh1koOQnFMAzZMZSREnrKd0QGIM0qE6032",
        "https://discord.com/api/webhooks/946268190139355208/RdZES-aOVDfLa5fsOV4TYc4PfjkqCBBuUKoCCSSNwojTwgS4cToHevPgOT5YJ_gl9XLM"
    ]
    delay_per_message: int = 3
    client.run()
