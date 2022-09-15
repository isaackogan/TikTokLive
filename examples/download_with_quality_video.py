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
        quality="hd"  #Quality of the video. This is string you can use sd, ld, hd, or uhd.
        #sd = 480p vbrate = 800000
        #ld = 480p vbrate = 500000
        #hd = 540p vbrate = 1000000
        #uhd = 720p vbrate = 1000000
    )

    # Stop downloading after 10 seconds.
    await asyncio.sleep(2)
    client.stop_download()


if __name__ == '__main__':
    """
    NOTE: You must have ffmpeg installed on your machine for this program to run!
    
    """

    client.run()
