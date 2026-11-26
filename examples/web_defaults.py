from IgniteLiveAPI.client.client import IgniteLiveClient
from IgniteLiveAPI.client.logger import LogLevel
from IgniteLiveAPI.client.web.web_settings import WebDefaults
from IgniteLiveAPI.events import ConnectEvent

# *Before* creating a client, you can override the default HTTP settings
WebDefaults.tiktok_sign_url = "https://my-sign-server.com"
WebDefaults.web_client_headers['my_new_header'] = "my-new-value"

# Create the client
client: IgniteLiveClient = IgniteLiveClient(
    unique_id="@tv_asahi_news",
)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    client.logger.info(f"Connected to {event.unique_id}!")


if __name__ == '__main__':
    client.logger.setLevel(LogLevel.INFO.value)
    client.run()
