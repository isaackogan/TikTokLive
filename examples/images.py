from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.client.logger import LogLevel
from TikTokLive.events import ConnectEvent, CommentEvent

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@tv_asahi_news"
)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    client.logger.info(f"Connected to @{event.unique_id}!")


@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    client.logger.info("Received a comment!")

    # Download the image
    image_bytes: bytes = await client.web.fetch_image_data(
        image=event.user.avatar_thumb
    )

    # Write to bytes
    with open(f"{event.user.unique_id}.webp", "wb") as file:
        file.write(image_bytes)

    client.logger.info("Downloaded an image!")


if __name__ == '__main__':
    # Enable debug info
    client.logger.setLevel(LogLevel.INFO.value)

    # Connect
    client.run(process_connect_events=False)
