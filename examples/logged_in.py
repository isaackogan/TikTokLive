from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.client.logger import LogLevel
from TikTokLive.events import ConnectEvent

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@tv_asahi_news"
)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    client.logger.info(f"Connected to @{event.unique_id}!")


if __name__ == '__main__':
    # Enable download info
    client.logger.setLevel(LogLevel.INFO.value)

    # Set the login session ID token BEFORE connecting. Both the
    # `sessionid` cookie and the `tt-target-idc` cookie (data-center hint)
    # are required — you can read both off your browser's TikTok cookies.
    client.web.set_session("session-id-here", "tt-target-idc-here")

    # Connect
    client.run()
