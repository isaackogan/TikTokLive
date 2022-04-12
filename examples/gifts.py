from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import GiftEvent

client = TikTokLiveClient("@satisfyy.me")


@client.on("gift")
async def on_gift(event: GiftEvent):
    """
    This is an example for the "gift" event to show you how to read gift data properly.

    Important Note:

    Gifts of type 1 can have streaks, so we need to check that the streak has ended
    If the gift type isn't 1, it can't repeat. Therefore, we can go straight to printing

    """

    # Streakable gift & streak is over
    if event.gift.streakable:
        if not event.gift.streaking:
            print(f"{event.user.uniqueId} sent {event.gift.repeat_count}x \"{event.gift.extended_gift.name}\"")

    # Not streakable gift
    else:
        print(f"{event.user.uniqueId} sent \"{event.gift.extended_gift.name}\"")


client.run()
