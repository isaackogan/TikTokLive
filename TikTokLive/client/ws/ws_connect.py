from typing import Optional, AsyncIterator

from httpx import Proxy
from websockets import WebSocketClientProtocol
from websockets.legacy.client import Connect
from websockets_proxy.websockets_proxy import ProxyConnect

from TikTokLive.client.logger import TikTokLiveLogHandler


class WebcastConnect(Connect):

    async def __aiter__(self) -> AsyncIterator[WebSocketClientProtocol]:
        """Custom implementation of async iterator that disables exception"""

        while True:
            async with self as protocol:
                yield protocol


class WebcastProxyConnect(ProxyConnect):

    def __init__(self, uri: str, *, proxy: Optional[Proxy], **kwargs):
        self.logger = kwargs.get("logger", TikTokLiveLogHandler.get_logger())
        super().__init__(uri, proxy=proxy, **kwargs)

    async def __aiter__(self) -> AsyncIterator[WebSocketClientProtocol]:
        """Custom implementation of async iterator that disables exception"""

        while True:
            async with self as protocol:
                yield protocol

