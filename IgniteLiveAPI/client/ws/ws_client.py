import asyncio
import time
import typing
from asyncio import Task
from typing import Optional, AsyncIterator, Union, Type

import httpx
from betterproto2 import Message
from websockets.legacy.client import WebSocketClientProtocol

from IgniteLiveAPI.client.errors import IdleTimeoutError
from IgniteLiveAPI.client.logger import IgniteLiveLogHandler
from IgniteLiveAPI.client.web.web_settings import WebDefaults
from IgniteLiveAPI.client.ws.ws_connect import WebcastProxyConnect, WebcastConnect, WebcastProxy, WebcastIterator
from IgniteLiveAPI.proto import ProtoMessageFetchResult, WebcastPushFrame, HeartBeatMessage, WebcastImEnterRoomMessage


class WebcastWSClient:
    """Websocket client responsible for connections to TikTok"""

    DEFAULT_PING_INTERVAL: float = 5.0

    def __init__(
            self,
            ws_kwargs: Optional[dict] = None,
            ws_proxy: Optional[WebcastProxy] = None
    ):
        """
        Initialize WebcastWSClient

        :param ws_kwargs: Overrides for the websocket connection

        """

        self._seq_id: int = 1
        self._ws_kwargs: dict = ws_kwargs or {}
        self._logger = IgniteLiveLogHandler.get_logger()
        self._ping_loop: Optional[Task] = None
        self._ws_proxy: Optional[WebcastProxy] = ws_proxy or self._ws_kwargs.get("proxy")
        self._connect_generator_class: Union[Type[WebcastConnect], Type[WebcastProxyConnect]] = WebcastProxyConnect if self._ws_proxy else WebcastConnect
        self._connection_generator: Optional[WebcastConnect] = None

        # Idle watchdog state
        self._watchdog: Optional[Task] = None
        self._last_frame_at: float = time.monotonic()
        self._idle_timed_out: bool = False

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

        return bool(self.ws and self.ws.open)

    async def send(self, message: Union[bytes, Message]) -> None:
        """
        Send a message to the WebSocket

        :param message: Message to send to the WebSocket connection

        """

        # Can't send a message to a disconnected WebSocket
        if not self.connected:
            self._logger.warning("Attempted to send a message without an open WebSocket connection.")
            return

        # Log outbound data (use !r for bytes so we get the literal repr)
        self._logger.debug(f"Sending data to Webcast Server... {message!r}")

        # Send the data (+ Serialize the data if it's a protobuf message).
        # ``connected`` above guarantees self.ws is not None at this point;
        # mypy can't follow the property-based guard.
        assert self.ws is not None
        await self.ws.send(
            message=bytes(message) if isinstance(message, Message) else message
        )

    async def send_ack(
            self,
            webcast_response: ProtoMessageFetchResult,
            webcast_push_frame: WebcastPushFrame
    ) -> None:
        """
        Acknowledge the receipt of a ProtoMessageFetchResult message from TikTok, if necessary

        :param webcast_response: The ProtoMessageFetchResult to acknowledge
        :param webcast_push_frame: The WebcastPushFrame containing the ProtoMessageFetchResult
        :return: None

        """

        # Can't ack a dead websocket...
        if not self.connected:
            return

        # Send the ack
        await self.send(
            message=WebcastPushFrame(
                payload_type="ack",
                payload_encoding="pb",
                # ID of the WebcastPushMessage for the acknowledgement
                log_id=webcast_push_frame.log_id,
                # [Unknown] Hypothesized to be an acknowledgement of the ProtoMessageFetchResult (& its messages) within the WebcastPushMessage
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

        # ``connected`` guarantees self.ws is not None; mypy can't follow.
        assert self.ws is not None
        await self.ws.close()

    def get_ws_cookie_string(self, cookies: httpx.Cookies) -> str:
        """
        Get the cookie string for the WebSocket connection.

        :param cookies: Cookies to pass to the WebSocket connection
        :return: Cookie string
        """

        cookie_values = []
        session_id: str | None = cookies.get("sessionid")

        # Exclude all session ID's if session_id exists and authentication is not required
        for key, value in cookies.items():
            cookie_values.append(f"{key}={value};")

        cookie_string = " ".join(cookie_values)

        # Handle session_id presence and create redacted cookie string
        if session_id:
            redacted_sid = session_id[:8] + "*" * (len(session_id) - 8)
            redacted_cookie_string = cookie_string.replace(session_id, redacted_sid)

            # Log that we're creating a cookie string for a logged-in session
            self._logger.warning(
                f"Created WS Cookie string for a LOGGED IN TikTok LIVE WebSocket session (Session ID: {redacted_sid}). "
                f"Cookies: {redacted_cookie_string}"
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
            user_agent: str,
            initial_webcast_response: ProtoMessageFetchResult,
            process_connect_events: bool = True,
            compress_ws_events: bool = True,
            idle_timeout: Optional[float] = None
    ) -> AsyncIterator[ProtoMessageFetchResult]:
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

        :param initial_webcast_response: The Initial ProtoMessageFetchResult from the sign server - NOT a PushFrame
        :param room_id: The room ID to connect to
        :param user_agent: The user agent to pass to the WebSocket connection
        :param cookies: The cookies to pass to the WebSocket connection
        :param process_connect_events: Whether to process the initial events sent in the first fetch
        :param compress_ws_events: Whether to ask TikTok to gzip the WebSocket events
        :param idle_timeout: If set, close the connection and raise :exc:`IdleTimeoutError` after this many seconds
                             without receiving ANY frame (heartbeats included). ``None`` disables the watchdog.
        :return: Yields ProtoMessageFetchResultMessage, the messages within ProtoMessageFetchResult.messages

        """

        if idle_timeout is not None and idle_timeout <= 0:
            raise ValueError("idle_timeout must be a positive number of seconds, or None to disable the watchdog")

        # Copy as to not affect the internal state
        ws_kwargs: dict = self._ws_kwargs.copy()
        self._idle_timed_out = False
        self._last_frame_at = time.monotonic()

        if self._ws_proxy is not None:
            ws_kwargs["proxy_conn_timeout"] = ws_kwargs.get("proxy_conn_timeout", 10.0)
            ws_kwargs["proxy"] = self._ws_proxy

        # If we don't want to process these, remove them
        if not process_connect_events:
            initial_webcast_response.messages = []

        # Initialize the WebcastConnect class
        self._connection_generator = self._connect_generator_class(
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
                "Cookie": self.get_ws_cookie_string(cookies=cookies),
                "User-Agent": user_agent,

                # Optional override for the headers
                **ws_kwargs.pop("extra_headers", {})
            },

            # Any inbound frame proves the connection is alive
            on_frame=self._touch,

            # Pass any extra  kwargs
            **{
                **ws_kwargs,
                "ping_timeout": None,
                "ping_interval": None,
            }
        )

        try:
            # Open a connection & yield ProtoMessageFetchResult items
            async for webcast_push_frame, webcast_response in typing.cast(WebcastIterator, self._connection_generator):

                # The first message does NOT need an ack since we perform the ack with the actual WebSocket connect URI
                if webcast_response.is_first:
                    await self.switch_rooms(room_id=room_id)

                    if idle_timeout is not None:
                        self._touch()
                        self.restart_watchdog(idle_timeout)

                # Ack when necessary. The very first iteration yields the initial
                # response from the sign server with ``webcast_push_frame=None`` -
                # there's nothing to ack against in that case.
                if webcast_response.need_ack and webcast_push_frame is not None:
                    await self.send_ack(webcast_response=webcast_response, webcast_push_frame=webcast_push_frame)

                # Yield the response
                yield webcast_response

                # If not connected, break
                if not self.connected:
                    break

        finally:
            # Runs on normal exit AND on failure (e.g. ConnectionClosedError), so a supervisor can safely
            # open a new connection afterwards without leaked ping / watchdog tasks or stale state.
            await self._cancel_task(self._ping_loop)
            await self._cancel_task(self._watchdog)

            # Reset internal state
            self._ping_loop = None
            self._watchdog = None
            self._connection_generator = None

        if self._idle_timed_out:
            raise IdleTimeoutError(f"No data received from TikTok for {idle_timeout} seconds; the connection was dropped.")

    @staticmethod
    async def _cancel_task(task: Optional[Task]) -> None:
        """Cancel a background task and wait for it to finish"""

        if task is None or task.done():
            return

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    def _touch(self) -> None:
        """Record that a frame was just received"""

        self._last_frame_at = time.monotonic()

    def restart_watchdog(self, idle_timeout: float) -> None:
        """
        (Re)start the idle watchdog

        :param idle_timeout: Seconds without any inbound frame before the connection is considered dead

        """

        if self._watchdog:
            self._watchdog.cancel()

        self._watchdog = asyncio.create_task(self._watchdog_fn(idle_timeout))

    async def _watchdog_fn(self, idle_timeout: float) -> None:
        """
        Close the connection when nothing has been received for ``idle_timeout`` seconds.

        TikTok never answers protocol-level pings, so the ``websockets`` keepalive is disabled and a half-open
        socket (network gone, no FIN/RST) would otherwise block the receive loop forever.

        """

        check_every: float = min(max(idle_timeout / 4, 0.05), 5.0)

        try:
            while self.connected:
                await asyncio.sleep(check_every)
                idle_for: float = time.monotonic() - self._last_frame_at

                if idle_for >= idle_timeout:
                    self._logger.warning(
                        f"No data from TikTok for {idle_for:.1f}s (idle_timeout={idle_timeout}s); closing the connection."
                    )
                    self._idle_timed_out = True
                    await self.disconnect()
                    return

        except asyncio.CancelledError:
            self._logger.debug("Idle watchdog cancelled.")

    def restart_ping_loop(self, room_id: int) -> None:
        """
        Restart the WebSocket ping loop

        """

        if self._ping_loop:
            self._ping_loop.cancel()

        self._seq_id = 1
        self._ping_loop = asyncio.create_task(self._ping_loop_fn(room_id))

    async def switch_rooms(self, room_id: int) -> None:

        im_enter_room_message = WebcastImEnterRoomMessage(
            room_id=room_id,
            room_tag="",
            live_id=12,
            identity="audience",
            cursor="",
            account_type=0,
            enter_unique_id=0,
            filter_welcome_msg="0",
            is_anchor_continue_keep_msg=False
        )

        webcast_push_frame: WebcastPushFrame = WebcastPushFrame(
            payload_type="im_enter_room",
            payload_encoding="pb",
            payload=bytes(im_enter_room_message)
        )

        await self.send(message=webcast_push_frame)
        self.restart_ping_loop(room_id=room_id)

    async def _ping_loop_fn(self, room_id: int) -> None:
        """
        Send a ping every 10 seconds to keep the connection alive

        """

        try:
            # Must be connected to loop as ping_interval requires the WS be instantiated
            if not self.connected:
                return

            # Calculate the ping interval
            ping_interval: float = self.DEFAULT_PING_INTERVAL
            if self._connection_generator is not None and self._connection_generator.ws_options is not None:
                ping_interval = float(self._connection_generator.ws_options.get("ping-interval", ping_interval))

        except:
            self._logger.error("Failed to start ping loop!", exc_info=True)
            return

        # Ping Loop
        try:
            self._logger.debug(f"Starting ping loop with interval of {ping_interval} seconds.")
            while self.connected:
                # Create the heartbeat message (it is always the same)
                hb_message = HeartBeatMessage(room_id=room_id, send_packet_seq_id=self._seq_id)
                self._seq_id += 1

                webcast_push_frame: WebcastPushFrame = WebcastPushFrame(
                    payload_encoding="pb",
                    payload_type="hb",
                    payload=bytes(hb_message),
                    headers=[]
                )

                # Send the ping
                await self.send(message=webcast_push_frame)

                # Every 10 seconds
                await asyncio.sleep(ping_interval)

        except asyncio.CancelledError:
            self._logger.debug("Ping loop cancelled.")
