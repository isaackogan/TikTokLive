from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.client.logger import LogLevel
from TikTokLive.events import ConnectEvent, GiftEvent

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@tv_asahi_news"
)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    client.logger.info(f"Connected to @{event.unique_id}!")


@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    client.logger.info("Received a gift!")

    # Can have a streak and streak is over
    if event.gift.streakable and not event.streaking:
        print(f"{event.user.unique_id} sent {event.repeat_count}x \"{event.gift.name}\"")

    # Cannot have a streak
    elif not event.gift.streakable:
        print(f"{event.user.unique_id} sent \"{event.gift.name}\"")


if __name__ == '__main__':
    # Enable debug info
    client.logger.setLevel(LogLevel.INFO.value)

    # Connect
    client.run()
