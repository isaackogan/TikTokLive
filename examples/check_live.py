import asyncio

from TikTokLive import TikTokLiveClient
from TikTokLive.client.logger import LogLevel
from TikTokLive.events import ConnectEvent

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@tv_asahi_news"
)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    client.logger.info(f"Connected to @{event.unique_id}!")


async def check_loop():
    # Run 24/7
    while True:

        # Check if they're live
        while not await client.is_live():
            client.logger.info("Client is currently not live. Checking again in 60 seconds.")
            await asyncio.sleep(60)  # Spamming the endpoint will get you blocked

        # Connect once they become live
        client.logger.info("Requested client is live!")
        await client.connect()


if __name__ == '__main__':
    client.logger.setLevel(LogLevel.INFO.value)
    asyncio.run(check_loop())
