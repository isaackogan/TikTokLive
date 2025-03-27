import logging
from typing import Optional, Tuple, Union, Type, AsyncIterator, Dict, Any

import httpx
from python_socks import ProxyType, parse_proxy_url
from websockets import InvalidStatusCode
from websockets.legacy.client import Connect, WebSocketClientProtocol
from websockets_proxy import websockets_proxy
from websockets_proxy.websockets_proxy import ProxyConnect

from TikTokLive.client.errors import WebcastBlocked200Error
from TikTokLive.client.ws.ws_utils import extract_webcast_response_message, build_webcast_uri, extract_websocket_options
from TikTokLive.proto import ProtoMessageFetchResult
from TikTokLive.proto.custom_extras import WebcastPushFrame

"""Type hint for a WebcastProxy, which can be either an HTTPX Proxy or a Websockets Proxy"""
WebcastProxy: Type = Union[httpx.Proxy, websockets_proxy.Proxy]

"""
Type hint for a WebcastIterator, which yields a tuple of WebcastPushFrame and ProtoMessageFetchResult.
WebcastPushFrame is Optional because the first yielded item is from the initial response
which is from /im/fetch (from the sign server), so it is not encapsulated by a WebcastPushFrame.
"""
WebcastIterator: Type = AsyncIterator[Tuple[Optional[WebcastPushFrame], ProtoMessageFetchResult]]


class WebcastConnect(Connect):

    def __init__(
            self,
            initial_webcast_response: ProtoMessageFetchResult,
            logger: logging.Logger,
            base_uri_params: Dict[str, Any],
            base_uri_append_str: str,
            uri: Optional[str] = None,
            **kwargs
    ):

        # If uri is provided (it should normally never be), bypass the construction
        if uri is None:
            uri: str = build_webcast_uri(
                initial_webcast_response=initial_webcast_response,
                base_uri_params=base_uri_params,
                base_uri_append_str=base_uri_append_str
            )

        super().__init__(uri, logger=logger, **kwargs)
        self.logger = self._logger = logger
        self.logger.debug(f"Built Webcast URI: {uri}")
        self._ws: Optional[WebSocketClientProtocol] = None
        self._ws_options: Optional[dict[str, str]] = None
        self._initial_response: ProtoMessageFetchResult = initial_webcast_response

    @property
    def ws(self) -> Optional[WebSocketClientProtocol]:
        """Get the current WebSocketClientProtocol"""

        return self._ws

    @property
    def ws_options(self) -> Optional[dict[str, str]]:
        """Get the WebSocket options as returned via the Handshake-Options header"""

        return self._ws_options

    async def __aiter__(self) -> WebcastIterator:
        """
        Custom implementation of async iterator that disables exception ignoring & handles messages.
        We must disable the retry mechanism because websockets are signed and only work once, so reconnecting wouldn't work anyways.
        Also, the mechanism by the websockets library ignores the '200' error code and retries, even though this is a 'detected by TikTok' error & thus
        retrying is useless.

        """

        first_connect: bool = True

        while True:
            try:

                # "async with" yields a WebsocketClientProtocol
                # The connection happens in the "async with", so if you enter the loop, that means it connected to the WebSocket
                async with self as protocol:
                    self._ws = protocol
                    self._ws_options = extract_websocket_options(self._ws.response_headers)

                    # Yield the first ProtoMessageFetchResult
                    if first_connect:
                        first_connect = False
                        yield None, self._initial_response

                    # "async for" yields "WebcastPushFrame" payloads as unparsed bytes
                    async for payload_bytes in protocol:

                        # Extract push frame
                        webcast_push_frame: WebcastPushFrame = WebcastPushFrame().parse(payload_bytes)

                        # Only deal with messages
                        if webcast_push_frame.payload_type != "msg":
                            webcast_push_frame.payload = extract_webcast_response_message(webcast_push_frame, logger=self._logger)
                            self._logger.debug(f"Received payload of type '{webcast_push_frame.payload_type}', not 'msg': {webcast_push_frame}")
                            continue

                        # If it is of type msg, we can extract the ProtoMessageFetchResult item within
                        webcast_response: ProtoMessageFetchResult = extract_webcast_response_message(webcast_push_frame, logger=self._logger)
                        yield webcast_push_frame, webcast_response

            except InvalidStatusCode as ex:
                if ex.status_code == 200:
                    # Note from Isaac post-insanity...
                    # IF the WebSockets are >>SIGNED<< WITH A SESSION ID
                    # and you DO NOT pass a sessionid cookie in the header, it will reject for "illegal secret key"
                    raise WebcastBlocked200Error(
                        f"WebSocket rejected by TikTok due to \"{ex.headers.get('Handshake-Msg', 'an unknown reason')}\"."
                    ) from ex
                raise

            finally:
                self._ws = None
                self._ws_options = None


class WebcastProxyConnect(ProxyConnect, WebcastConnect):
    """
    Add Proxy support to the WebcastConnect class

    """

    def __init__(
            self,
            proxy: Optional[WebcastProxy],
            **kwargs
    ):
        super().__init__(
            proxy=self._convert_proxy(proxy) if isinstance(proxy, httpx.Proxy) else proxy,
            **kwargs
        )

    @classmethod
    def _convert_proxy(cls, proxy: httpx.Proxy) -> websockets_proxy.Proxy:
        """Convert an HTTPX proxy to a websockets_proxy Proxy"""
        parsed: Tuple[ProxyType, str, int, Optional[str], Optional[str]] = parse_proxy_url(str(proxy.url))
        parsed: list = list(parsed)

        # Add auth back
        parsed[3] = proxy.auth[0]
        parsed[4] = proxy.auth[1]

        return websockets_proxy.Proxy(*parsed)
