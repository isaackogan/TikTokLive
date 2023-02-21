from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import GiftEvent

client = TikTokLiveClient("@satisfyy.me")


@client.on("gift")
async def on_gift(event: GiftEvent):
    """
    This is an example for the "gift" LiveEvent to show you how to read gift data properly.

    Important Note:

    Gifts of type 1 can have streaks, so we need to check that the streak has ended
    If the gift type isn't 1, it can't repeat. Therefore, we can go straight to printing

    """

    # Streakable gift & streak is over
    if event.gift.streakable and not event.gift.streaking:
        print(f"{event.user.unique_id} sent {event.gift.count}x \"{event.gift.info.name}\"")

    # Non-streakable gift
    elif not event.gift.streakable:
        print(f"{event.user.unique_id} sent \"{event.gift.info.name}\"")


if __name__ == '__main__':
    # Run the client and block the main thread
    # await client.start() to run non-blocking
    client.run()
