import asyncio
import base64
import typing
from asyncio import Task
from typing import Optional, AsyncIterator, Union, Type

import httpx
from betterproto import Message
from websockets.legacy.client import WebSocketClientProtocol

from TikTokLive.client.logger import TikTokLiveLogHandler
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.client.ws.ws_connect import WebcastProxyConnect, WebcastConnect, WebcastProxy, WebcastIterator
from TikTokLive.proto import WebcastPushFrame, WebcastResponse


class WebcastWSClient:
    """Websocket client responsible for connections to TikTok"""

    DEFAULT_PING_INTERVAL: float = 1.0
    PING_MESSAGE: bytes = base64.b64decode(b'MgJwYjoCaGI=')  # Used to be '3A026862' aka ':\x02hb', now is '2\x02pb:\x02hb'.

    def __init__(
            self,
            ws_kwargs: Optional[dict] = None,
            ws_proxy: Optional[WebcastProxy] = None
    ):
        """
        Initialize WebcastWSClient

        :param ws_kwargs: Overrides for the websocket connection

        """

        self._ws_kwargs: dict = ws_kwargs or {}
        self._logger = TikTokLiveLogHandler.get_logger()
        self._ping_loop: Optional[Task] = None
        self._ws_proxy: Optional[WebcastProxy] = ws_proxy or ws_kwargs.get("proxy")
        self._connect_generator_class: Union[Type[WebcastConnect], Type[WebcastProxyConnect]] = WebcastProxyConnect if self._ws_proxy else WebcastConnect
        self._connection_generator: Optional[WebcastConnect] = None

    @property
    def ws(self) -> Optional[WebSocketClientProtocol]:
        """
        Get the current WebSocketClientProtocol

        :return: WebSocketClientProtocol

        """

        # None because there's no generator
        if not self._connection_generator:
            return None

        # Optional[WebSocketClientProtocol]
        return self._connection_generator.ws

    @property
    def connected(self) -> bool:
        """
        Check if the WebSocket is open

        :return: WebSocket status

        """

        return self.ws and self.ws.open

    async def send(self, message: Union[bytes, Message]) -> None:
        """
        Send a message to the WebSocket

        :param message: Message to send to the WebSocket connection

        """

        # Can't send a message to a disconnected WebSocket
        if not self.connected:
            self._logger.warning("Attempted to send a message without an open WebSocket connection.")
            return

        # Log outbound data
        self._logger.debug(f"Sending data to Webcast Server... {message}")

        # Send the data (+ Serialize the data if it's a protobuf message)
        await self.ws.send(
            message=bytes(message) if isinstance(message, Message) else message
        )

    async def send_ack(
            self,
            webcast_response: WebcastResponse,
            webcast_push_frame: WebcastPushFrame
    ) -> None:
        """
        Acknowledge the receipt of a WebcastResponse message from TikTok, if necessary

        :param webcast_response: The WebcastResponse to acknowledge
        :param webcast_push_frame: The WebcastPushFrame containing the WebcastResponse
        :return: None

        """

        # Can't ack a dead websocket...
        if not self.connected:
            return

        # Send the ack
        await self.send(
            message=WebcastPushFrame(
                payload_type="ack",
                # ID of the WebcastPushMessage for the acknowledgement
                log_id=webcast_push_frame.log_id,
                # [Unknown] Hypothesized to be an acknowledgement of the WebcastResponse (& its messages) within the WebcastPushMessage
                payload=(webcast_response.internal_ext or "-").encode()
            )
        )

    async def disconnect(self) -> None:
        """
        Request to stop the websocket connection & wait
        :return: None

        """

        if not self.connected:
            return

        await self.ws.close()

    def get_ws_cookie_string(self, cookies: httpx.Cookies, authenticate_websocket: bool) -> str:
        """
        Get the cookie string for the WebSocket connection.

        :param cookies: Cookies to pass to the WebSocket connection
        :param authenticate_websocket: Whether the WebSocket is authenticated
        :return: Cookie string
        """

        cookie_values = []
        session_id: str | None = cookies.get("sessionid")

        # If session_id is None and authentication is required, raise an error or handle appropriately
        if authenticate_websocket and session_id is None:
            self._logger.error("Session ID is required for WebSocket authentication, but none was found.")
            raise ValueError("Session ID is required for WebSocket authentication.")

        # Exclude all session ID's if session_id exists and authentication is not required
        for key, value in cookies.items():
            if session_id and not authenticate_websocket and session_id in value:
                continue
            cookie_values.append(f"{key}={value};")

        cookie_string = " ".join(cookie_values)

        # Handle session_id presence and create redacted cookie string
        if session_id:
            redacted_sid = session_id[:8] + "*" * (len(session_id) - 8)
            redacted_cookie_string = cookie_string.replace(session_id, redacted_sid)

            # Log that we're creating a cookie string for a logged-in session
            if authenticate_websocket:
                self._logger.warning(
                    f"Created WS Cookie string for a LOGGED IN TikTok LIVE WebSocket session (Session ID: {redacted_sid}). "
                    f"Cookies: {redacted_cookie_string}"
                )
            else:
                self._logger.debug(
                    f"Created WS Cookie string for an ANONYMOUS TikTok Live WebSocket session. Cookies: {redacted_cookie_string}"
                )
        else:
            self._logger.debug(
                f"Created WS Cookie string for an ANONYMOUS TikTok Live WebSocket session. Cookies: {cookie_string}"
            )

        return cookie_string

    async def connect(
            self,
            room_id: int,
            cookies: httpx.Cookies,
            authenticate_websocket: bool,
            user_agent: str,
            initial_webcast_response: WebcastResponse,
            process_connect_events: bool = True,
            compress_ws_events: bool = True
    ) -> AsyncIterator[WebcastResponse]:
        """
        Connect to the Webcast server & iterate over response messages.

        --- Message 1 ---

        The iterator exits normally when the connection is closed with close code
        1000 (OK) or 1001 (going away) or without a close code. It raises
        a :exc:`~websockets.exceptions.ConnectionClosedError` when the connection
        is closed with any other code.

        --- Message 2 ---

        DEVELOP SANITY NOTE:

        When ping_timeout is set (i.e. not None), the client waits for a pong for N seconds.
        TikTok DO NOT SEND pongs back. Unfortunately the websockets client after N seconds assumes the server is dead.
        It then throws the following infamous exception:

        websockets.exceptions.ConnectionClosedError: sent 1011 (unexpected error) keepalive ping timeout; no close frame received

        If you set ping_timeout to None, it doesn't wait for a pong. Perfect, since TikTok don't send them.

        --- Parameters --

        :param initial_webcast_response: The Initial WebcastResponse from the sign server - NOT a PushFrame
        :param room_id: The room ID to connect to
        :param user_agent: The user agent to pass to the WebSocket connection
        :param cookies: The cookies to pass to the WebSocket connection
        :param authenticate_websocket: Whether to authenticate the WebSocket connection
        :param process_connect_events: Whether to process the initial events sent in the first fetch
        :param compress_ws_events: Whether to ask TikTok to gzip the WebSocket events
        :return: Yields WebcastResponseMessage, the messages within WebcastResponse.messages

        """

        # Copy as to not affect the internal state
        ws_kwargs: dict = self._ws_kwargs.copy()

        if self._ws_proxy is not None:
            ws_kwargs["proxy_conn_timeout"] = ws_kwargs.get("proxy_conn_timeout", 10.0)
            ws_kwargs["proxy"] = self._ws_proxy

        # If we don't want to process these, remove them
        if not process_connect_events:
            initial_webcast_response.messages = []

        # Initialize the WebcastConnect class
        self._connection_generator: WebcastConnect = self._connect_generator_class(
            initial_webcast_response=initial_webcast_response,
            subprotocols=ws_kwargs.pop("subprotocols", ["echo-protocol"]),
            logger=self._logger,
            uri=ws_kwargs.pop('uri', None),  # Always *should* be none as we build this internally
            base_uri_append_str=(ws_kwargs.pop("base_uri_append_str", WebDefaults.ws_client_params_append_str)),

            # Base URI parameters
            base_uri_params={
                **WebDefaults.ws_client_params,
                **ws_kwargs.pop("base_uri_params", {}),
                "room_id": room_id,
                "compress": "gzip" if compress_ws_events else "",
            },

            # Extra headers
            extra_headers={
                # Must pass cookies to connect to the WebSocket
                "Cookie": self.get_ws_cookie_string(cookies=cookies, authenticate_websocket=authenticate_websocket),
                "User-Agent": user_agent,

                # Optional override for the headers
                **ws_kwargs.pop("extra_headers", {})
            },

            # Pass any extra  kwargs
            **{
                **ws_kwargs,
                "ping_timeout": None,
                "ping_interval": None,
            }
        )

        # Open a connection & yield WebcastResponse items
        async for webcast_push_frame, webcast_response in typing.cast(WebcastIterator, self._connection_generator):

            # The first message does NOT need an ack since we perform the ack with the actual WebSocket connect URI
            if webcast_response.is_first:
                self.restart_ping_loop()

            # Ack when necessary
            if webcast_response.needs_ack:
                await self.send_ack(webcast_response=webcast_response, webcast_push_frame=webcast_push_frame)

            # Yield the response
            yield webcast_response

            # If not connected, break
            if not self.connected:
                break

        # Cancel the ping loop if it hasn't started to
        if not self._ping_loop.done() and not self._ping_loop.cancelling():
            self._ping_loop.cancel()

        if not self._ping_loop.done():
            await self._ping_loop

        # Reset internal state
        self._ping_loop = None
        self._connection_generator = None

    def restart_ping_loop(self) -> None:
        """
        Restart the WebSocket ping loop

        """

        if self._ping_loop:
            self._ping_loop.cancel()

        self._ping_loop = asyncio.create_task(self._ping_loop_fn())

    async def _ping_loop_fn(self) -> None:
        """
        Send a ping every 10 seconds to keep the connection alive

        """

        # Must be connected to loop as ping_interval requires the WS be instantiated
        if not self.connected:
            return

        # Ping Loop
        try:
            while self.connected:
                # Send the ping
                await self.send(message=self.PING_MESSAGE)

                # Every 10 seconds
                await asyncio.sleep(self.DEFAULT_PING_INTERVAL)

        except asyncio.CancelledError:
            self._logger.debug("Ping loop cancelled.")
