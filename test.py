from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import CommentEvent

conn: TikTokLiveClient = TikTokLiveClient("saabood")


@conn.on("comment_event")
async def on_comment(event: CommentEvent):
    print(f"{event.user.nickname}: {event.comment}")


if __name__ == '__main__':
    conn.run()
