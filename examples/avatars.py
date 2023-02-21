import io

from PIL import Image

from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import CommentEvent

# Instantiate the client with the user's username
client: TikTokLiveClient = TikTokLiveClient(unique_id="@example")


@client.on("comment")
async def on_comment(event: CommentEvent):
    """

    Downloading an avatar to bytes is very easy.
    It uses the instance of TikTokLiveClient that the event belongs to.
    Specifically, it borrows the TikTokLiveClient's HTTP Client.

    This example downloads an image and displays it via Pillow (PIL)
    whenever a user comments on the TikTok LIVE.

    """

    image_data: bytes = await event.user.avatar.download()
    image: Image = Image.open(io.BytesIO(image_data))
    image.show()


if __name__ == '__main__':
    # Run the client and block the main thread
    # await client.start() to run non-blocking
    client.run()
