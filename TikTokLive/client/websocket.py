from __future__ import annotations

import asyncio
import logging
import traceback
from asyncio import AbstractEventLoop
from typing import TYPE_CHECKING, Optional, Dict, Any

import websockets
from pyee import AsyncIOEventEmitter
from websockets.exceptions import ConnectionClosed
from websockets.legacy.client import WebSocketClientProtocol

from TikTokLive.client.http import TikTokHTTPClient
from TikTokLive.proto.tiktok_schema_pb2 import WebcastWebsocketAck
from TikTokLive.proto.utilities import deserialize_websocket_message, serialize_message

if TYPE_CHECKING:
    from TikTokLive.client.base import BaseClient


class WebcastWebsocket:
    """
    Wrapper class to handle websocket connections to the Webcast API

    """

    def __init__(
            self,
            client: BaseClient,
            ws_url: str,
            ws_params: Dict[str, str],
            client_params: Dict[str, str],
            headers: Dict[str, str],
            cookies: Dict[str, str],
            ping_interval_ms: float,
            loop: AbstractEventLoop,
            **kwargs
    ):
        """
        Initialize Websocket client for Websocket-based Webcast connections

        :param client: The client to emit events back to as they are received
        :param ws_url: The URL of the Websocket to connect to
        :param ws_params: Parameters to be added to the URL that identify the connection to the websocket
        :param client_params: Various regular parameters to be added to the URL
        :param headers: Headers to be added to the websocket connection request for authentication
        :param cookies: Cookies to be added as a "Cookie" header to the websocket connection request for authentication
        :param loop: The main event loop
        :param kwargs: Various optional keyword arguments for the websocket itself
        :param ping_interval_ms: How often to ping the websocket for room data

        """

        # Protected Attributes
        self._connection: Optional[WebSocketClientProtocol] = None
        self._websocket_options: Dict[str, Any] = kwargs
        self._ping_interval: float = ping_interval_ms / 1000

        # Private Attributes
        self.__cookies: Dict[str, str] = cookies
        self.__ws_params: Dict[str, str] = {**client_params, **ws_params}
        self.__headers: Dict[str, str] = {**headers, "Cookie": " ".join(f"{k}={v};" for k, v in cookies.items())}
        self.__ws_url: str = TikTokHTTPClient.update_url(ws_url, self.__ws_params)
        self.__loop: AbstractEventLoop = loop
        self.__client: AsyncIOEventEmitter = client

    async def connect(self) -> bool:
        """
        Attempt to connect to the websocket and return the connection status

        :return: Whether the connection was successfully initiated
        """

        try:
            # Initiate a connection then keep it open in the connection loop
            self._connection = await websockets.connect(uri=self.__ws_url, extra_headers=self.__headers, ssl=True, **self._websocket_options)
            self.__loop.create_task(self.connection_loop())
            return True
        except:
            logging.warning(
                f"WebcastWebsocket connection failed, will attempt long polling instead. Consider disabling websockets if this persists: "
                f"\n{traceback.format_exc()}"
            )
            return False

    async def connection_loop(self) -> None:
        """
        The websocket heartbeat, responsible for making requests to the websocket for room data

        :return: None

        """

        while True:
            try:
                # Get a response
                response: Optional[bytes] = await self._connection.recv()
                decoded: dict = deserialize_websocket_message(response)

                # Send Acknowledgement
                if decoded.get("id", 0) > 0:
                    await self.send_ack(decoded["id"])

                # If valid, send off events to client
                if decoded.get("messages"):
                    self.__client.emit("websocket", decoded)

            except Exception as ex:
                # If the connection closed, close the websocket
                if isinstance(ex, ConnectionClosed):
                    await self._connection.close()
                    self.__client.emit("error", ex)

                logging.warning(traceback.format_exc())

            # Wait until the next ping time
            await asyncio.sleep(self._ping_interval)

    async def send_ack(self, message_id: int) -> None:
        message: WebcastWebsocketAck = serialize_message(
            "WebcastWebsocketAck",
            {
                "type": "ack",
                "id": message_id
            }
        )

        await self._connection.send(message)

    async def is_open(self) -> bool:
        """
        Check whether the websocket connection is open

        :return: The result of the check

        """

        try:
            await self._connection.ensure_open()
        except:
            return False

        return True

    async def close(self) -> None:
        """
        Close the websocket connection

        :return: Nothing, you closed it, you dope

        """

        await self._connection.close()
