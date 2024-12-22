import asyncio

from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.client.logger import LogLevel
from TikTokLive.events import ConnectEvent, DisconnectEvent

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@tv_asahi_news"
)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    client.logger.info("Connected!")

    # Start a recording
    client.web.fetch_video_data.start(
        output_fp=f"{event.unique_id}.mp4",
        room_info=client.room_info,
        output_format="mp4"
    )

    await asyncio.sleep(5)

    # Stop the client, we're done!
    await client.disconnect()


@client.on(DisconnectEvent)
async def on_live_end(_: DisconnectEvent):
    """Stop the download when we disconnect"""

    client.logger.info("Disconnected!")

    if client.web.fetch_video_data.is_recording:
        client.web.fetch_video_data.stop()


if __name__ == '__main__':
    # Enable download info
    client.logger.setLevel(LogLevel.INFO.value)

    # Need room info to download stream
    client.run(fetch_room_info=True)
