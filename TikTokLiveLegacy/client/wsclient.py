import asyncio
import random
from typing import Union, AsyncIterator, Any

from websockets.exceptions import ConnectionClosedOK
from websockets.legacy.client import WebSocketClientProtocol, Connect

from TikTokLive.proto.tiktok_schema_pb2 import WebcastWebsocketAck
from TikTokLive.proto.utilities import serialize_message, deserialize_websocket_message


class WebcastWebsocketConnection(WebSocketClientProtocol):
    """
    Manage the websocket connection to TikTok LIVE's Webcast server
    
    """

    def __init__(self, **kwargs: Any):
        """
        Initialize the websocket connection
        
        :param kwargs: Passed to superclass
        """

        super().__init__(**kwargs)
        self._manually_closed: bool = False

    def disconnect(self) -> None:
        """
        Disconnect from the Webcast server
        
        """

        self._manually_closed = True

    @property
    def manually_closed(self) -> bool:
        """
        Whether the connection has been closed by us
        
        """

        return self._manually_closed

    async def __aiter__(self) -> AsyncIterator[dict]:
        """
        Until the client is disconnected, wait for the next message
        
        """
        try:
            while not self._manually_closed:
                yield await self.recv()
        except ConnectionClosedOK:
            return
        except asyncio.CancelledError:
            raise

    async def recv(self) -> dict:
        """
        Override the binary protobuf messages received & decode them
        
        :return: Decoded websocket data
        
        """

        # Receive the message & deserialize it
        result: Union[str, bytes] = await super().recv()
        message: dict = deserialize_websocket_message(result)

        # Send Acks for messages with an ID
        if message.get("id"):
            await self.send_ack(message["id"])

        # Return decoded message
        return message

    async def send_ack(self, message_id: int) -> None:
        """
        Serialize an ack to protobuf & send to the Webcast server
        
        :param message_id: Message ID we are acknowledging
        :return: None
        
        """

        message: WebcastWebsocketAck = serialize_message(
            "WebcastWebsocketAck",
            {
                "type": "ack",
                "id": message_id
            }
        )

        await self.send(message)


class WebcastConnect(Connect):
    """
    A modified connection manager for the websockets library.
    Adds better support for cleanly exiting the async context manager.

    """

    def __init__(self, uri: str, **kwargs: Any):
        """

        :param uri: URI to connect to
        :param kwargs: Connect class kwargs

        """

        super().__init__(uri, **kwargs)
        self._manually_closed: bool = False

    def disconnect(self) -> None:
        """
        Disconnect from the Webcast server

        """

        self._manually_closed = True

    @property
    def manually_closed(self) -> bool:
        """
        Whether the connection has been closed by us

        """

        return self._manually_closed

    async def __aiter__(self) -> AsyncIterator[WebSocketClientProtocol]:
        """
        Continuously reconnect & provide new websocket connections for as long as we can

        """

        backoff_delay = self.BACKOFF_MIN
        while not self.manually_closed:
            try:
                async with self as protocol:
                    yield protocol
            except asyncio.CancelledError:
                raise
            except Exception:
                if backoff_delay == self.BACKOFF_MIN:
                    initial_delay = random.random() * self.BACKOFF_INITIAL
                    self.logger.info(
                        "! connect failed; reconnecting in %.1f seconds",
                        initial_delay,
                        exc_info=True,
                    )
                    await asyncio.sleep(initial_delay)
                else:
                    self.logger.info(
                        "! connect failed again; retrying in %d seconds",
                        int(backoff_delay),
                        exc_info=True,
                    )
                    await asyncio.sleep(int(backoff_delay))
                # Increase delay with truncated exponential backoff.
                backoff_delay = backoff_delay * self.BACKOFF_FACTOR
                backoff_delay = min(backoff_delay, self.BACKOFF_MAX)
                continue
            else:
                # Connection succeeded - reset backoff delay
                backoff_delay = self.BACKOFF_MIN


connect = WebcastConnect
