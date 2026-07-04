from datetime import datetime

from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.client.logger import LogLevel
from TikTokLive.events import ConnectEvent, CommentEvent

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@tv_asahi_news"
)

# If True, comments TikTok delivers as backlog (posted before this script
# connected) are dropped — only comments posted from here on are printed.
# TikTok still bursts a batch of recent comments right after connecting
# (this isn't something `process_connect_events` filters out), so we
# compare each comment's own timestamp against our connect time instead.
ONLY_NEW_COMMENTS: bool = True
connected_at_ms: int = 0


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    global connected_at_ms
    connected_at_ms = int(datetime.now().timestamp() * 1000)
    client.logger.info(f"Connected to @{event.unique_id}!")


@client.on(CommentEvent)
async def on_comment(event: CommentEvent):
    if ONLY_NEW_COMMENTS and event.common.create_time < connected_at_ms:
        return

    timestamp: str = datetime.fromtimestamp(event.common.create_time / 1000).strftime("%H:%M:%S")
    print(f"[{timestamp}] {event.user.nickname}-> {event.comment}")


if __name__ == '__main__':
    # Enable debug info
    client.logger.setLevel(LogLevel.INFO.value)

    # Connect
    client.run()
