import asyncio

from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import ConnectEvent

client = TikTokLiveClient("@bifiana_star")


@client.on("connect")
async def on_connect(_: ConnectEvent):
    """
    Download the livestream video from TikTok directly!

    """

    client.download(
        path="stream.avi",  # File path to save the download to
        duration=None,  # Download FOREVER. Set to any integer above 1 to download for X seconds
        quality=None  # Select video quality. In this case, Ultra-High Definition
    )

    # Stop downloading after 10 seconds.
    await asyncio.sleep(2)
    client.stop_download()


if __name__ == '__main__':
    """
    Note: "ffmpeg" MUST be installed on your machine to run this program
    
    """

    # Run the client and block the main thread
    # await client.start() to run non-blocking
    client.run()
