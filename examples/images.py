from IgniteLiveAPI.client.client import IgniteLiveClient
from IgniteLiveAPI.client.logger import LogLevel
from IgniteLiveAPI.events import ConnectEvent, CommentEvent

client: IgniteLiveClient = IgniteLiveClient(
    unique_id="@tv_asahi_news"
)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    client.logger.info(f"Connected to @{event.unique_id}!")


@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    client.logger.info("Received a comment!")

    # Download the user's avatar (only avatar_thumb is populated on comment events)
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
