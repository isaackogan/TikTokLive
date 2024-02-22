from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.client.logger import LogLevel
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.events import ConnectEvent

# *Before* creating a client, you can override the default HTTP settings
WebDefaults.tiktok_sign_url = "https://my-sign-server.com"
WebDefaults.client_headers['my_new_header'] = "my-new-value"

# Create the client
client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@tv_asahi_news",
)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    client.logger.info(f"Connected to {event.unique_id}!")


if __name__ == '__main__':
    client.logger.setLevel(LogLevel.INFO.value)
    client.run()
