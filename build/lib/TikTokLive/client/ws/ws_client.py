import asyncio
from typing import Optional, AsyncIterator, List, Dict, Any, Callable, Tuple

from httpx import Proxy
from python_socks import parse_proxy_url, ProxyType
from websockets import WebSocketClientProtocol
from websockets.legacy.client import Connect
from websockets_proxy import websockets_proxy
from websockets_proxy.websockets_proxy import ProxyConnect

from TikTokLive.client.logger import TikTokLiveLogHandler
from TikTokLive.proto import WebcastPushFrame, WebcastResponse, WebcastResponseMessage


class WebcastProxyConnect(ProxyConnect):

    def __init__(self, uri: str, *, proxy: Optional[Proxy], **kwargs):
        self.logger = kwargs.get("logger", TikTokLiveLogHandler.get_logger())
        super().__init__(uri, proxy=proxy, **kwargs)


class WebcastWSClient:
    """Websocket client responsible for connections to TikTok"""

    def __init__(
            self,
            ws_kwargs: dict = {},
            proxy: Optional[Proxy] = None
    ):
        """
        Initialize WebcastWSClient

        :param ws_kwargs: Overrides for the websocket connection

        """

        self._ws_kwargs: dict = ws_kwargs
        self._ws_cancel: Optional[asyncio.Event] = None
        self._ws: Optional[WebSocketClientProtocol] = None
        self._ws_proxy: Optional[Proxy] = proxy
        self._logger = TikTokLiveLogHandler.get_logger()

    async def send_ack(
            self,
            log_id: int,
            internal_ext: str
    ) -> None:
        """
        Acknowledge incoming messages from TikTok

        :param log_id: ID for the acknowledgement
        :param internal_ext: [unknown] Outbound data
        :return: None

        """

        # Can't ack a dead websocket...
        if not self.connected:
            return

        message: WebcastPushFrame = WebcastPushFrame(
            payload_type="ack",
            log_id=log_id,
            payload=internal_ext.encode()
        )

        self._logger.debug(f"Sending ack... {message}")
        await self._ws.send(bytes(message))

    async def disconnect(self) -> None:
        """
        Request to stop the websocket connection & wait
        :return: None

        """

        if not self.connected:
            return

        self._ws_cancel = asyncio.Event()
        await self._ws_cancel.wait()
        self._ws_cancel = None

    def build_connection_args(
            self,
            uri: str,
            headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Build the `websockets` library connection arguments dictionary

        :param uri: URI to connect to TikTok
        :param headers: Headers to send to TikTok on connecting
        :return: Connection dictionary

        """

        base_config: dict = (
            {
                "subprotocols": ["echo-protocol"],
                "ping_timeout": 10.0,
                "ping_interval": 10.0,
                "logger": self._logger,
                "uri": self._ws_kwargs.pop("uri", uri),
                "extra_headers": {**headers, **self._ws_kwargs.pop("headers", {})},
                **self._ws_kwargs
            }
        )

        if self._ws_proxy is not None:
            base_config["proxy_conn_timeout"] = 10.0
            base_config["proxy"] = self._convert_proxy()

        return base_config

    def _convert_proxy(self) -> websockets_proxy.Proxy:

        # (proxy_type, host, port, username, password)
        parsed: Tuple[ProxyType, str, int, Optional[str], Optional[str]] = parse_proxy_url(str(self._ws_proxy.url))
        parsed: list = list(parsed)

        # Add auth back
        parsed[3] = self._ws_proxy.auth[0]
        parsed[4] = self._ws_proxy.auth[1]

        return websockets_proxy.Proxy(*parsed)

    async def connect(
            self,
            uri: str,
            headers: Dict[str, str]
    ) -> AsyncIterator[WebcastResponseMessage]:
        """
        Connect to the Webcast websocket server & handle cancellation

        :param uri:
        :param headers:
        :return:
        """

        # Reset the cancel var
        self._ws_cancel = None

        # Yield while existent
        async for webcast_message in self.connect_loop(uri, headers):
            yield webcast_message

        # After loop breaks, gracefully shut down & send the cancellation event
        if self._ws_cancel is not None:
            await self._ws.close()
            self._ws_cancel.set()

    async def connect_loop(
            self,
            uri: str,
            headers: Dict[str, str]
    ) -> AsyncIterator[WebcastResponseMessage]:
        """
        Connect to the Webcast server & iterate over response messages.

        The iterator exits normally when the connection is closed with close code
        1000 (OK) or 1001 (going away) or without a close code. It raises
        a :exc:`~websockets.exceptions.ConnectionClosedError` when the connection
        is closed with any other code.

        :param uri: URI to connect to
        :param headers: Headers used for the connection
        :return: Yields WebcastResponseMessage

        """

        connect: Callable = WebcastProxyConnect if self._ws_proxy else Connect

        # Run connection loop
        async for websocket in connect(**self.build_connection_args(uri, headers)):

            # Update the stored websocket
            self._ws = websocket

            # Each time we receive a message, process it
            async for message in websocket:

                # Yield processed messages
                for webcast_message in await self.process_recv(message):
                    yield webcast_message

                # Handle cancellation request
                if self._ws_cancel is not None:
                    return

            if self._ws_cancel is not None:
                return

    async def process_recv(self, data: bytes) -> List[WebcastResponseMessage]:
        """
        Handle push frames received as websocket data

        :param data: Protobuf bytestream
        :return: List of contained messages for handling

        """

        # Extract push frame
        push_frame: WebcastPushFrame = WebcastPushFrame().parse(data)

        # Only deal with messages
        if push_frame.payload_type != "msg":
            self._logger.debug(f"Received payload of type '{push_frame.payload_type}', not 'msg': {push_frame}")
            return []

        # Extract response
        webcast_response: WebcastResponse = WebcastResponse().parse(push_frame.payload)

        # Acknowledge messages
        if webcast_response.needs_ack:
            await self.send_ack(
                internal_ext=webcast_response.internal_ext,
                log_id=push_frame.log_id
            )

        return webcast_response.messages

    @property
    def connected(self) -> bool:
        """
        Check if the websocket is currently connected

        :return: Connection status

        """

        return self._ws and self._ws.open
