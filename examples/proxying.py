from httpx import Proxy

from IgniteLiveAPI.client.client import IgniteLiveClient
from IgniteLiveAPI.client.logger import LogLevel
from IgniteLiveAPI.events import ConnectEvent

# Create the client
client: IgniteLiveClient = IgniteLiveClient(
    unique_id="@tv_asahi_news",

    # You can configure a proxy for web requests
    web_proxy=Proxy("http://hostname:port", auth=("username", "password")),

    # You can also configure a proxy for the websocket connection
    ws_proxy=Proxy("socks5://hostname:port", auth=("username", "password")),
)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    client.logger.info(f"Connected to {event.unique_id}!")


if __name__ == '__main__':
    client.logger.setLevel(LogLevel.INFO.value)
    client.run()
