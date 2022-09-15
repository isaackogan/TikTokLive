import asyncio

from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import ConnectEvent

client = TikTokLiveClient("@script_kiddiez")


@client.on("connect")
async def on_connect(_: ConnectEvent):
    """
    Download the livestream video from TikTok directly!
    """

    client.download(
        path="stream.avi",  # File path to save the download to
        duration=None,  # Download FOREVER. Set to any integer above 1 to download for X seconds
        quality="hd"  #Quality of the video. This is string you can use sd, ld, hd, or uhd
    )

    # Stop downloading after 10 seconds.
    await asyncio.sleep(2)
    client.stop_download()


if __name__ == '__main__':
    """
    NOTE: You must have ffmpeg installed on your machine for this program to run!
    
    """

    client.run()
