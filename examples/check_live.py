import asyncio

from TikTokLive import TikTokLiveClient
from TikTokLive.client.logger import LogLevel


# Replace with any username you want to monitor
client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@tv_asahi_news"
)


async def main():
    # Run forever
    while True:
        is_live = await client.is_live()

        if not is_live:
            client.logger.info(
                "Client is currently not live. "
                "Checking again in 60 seconds."
            )
            await asyncio.sleep(60)
            continue

        # User is live – fetch avatar URL via profile HTML
        avatar_url = await client.get_avatar_url()
        client.logger.info("Requested client is LIVE!")
        client.logger.info(f"Avatar URL: {avatar_url!r}")

        # Optionally connect to the livestream (same behavior as original example)
        await client.connect()

        # Once the stream ends, loop back and keep polling
        client.logger.info("Stream ended. Checking again in 60 seconds.")
        await asyncio.sleep(60)


if __name__ == "__main__":
    client.logger.setLevel(LogLevel.INFO.value)
    asyncio.run(main())
