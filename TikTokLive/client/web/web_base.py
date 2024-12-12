import logging
import os
import random
from abc import ABC, abstractmethod
from typing import Optional, Any, Awaitable, Dict

import httpx
from httpx import Cookies, AsyncClient, Response, Proxy

from TikTokLive.client.logger import TikTokLiveLogHandler
from TikTokLive.client.web.web_settings import WebDefaults


class TikTokHTTPClient:
    """
    HTTP client for interacting with the various APIs

    """

    __uuc: int = 0

    def __init__(
            self,
            proxy: Optional[Proxy] = None,
            httpx_kwargs: Optional[dict] = None
    ):
        """
        Create an HTTP client for interacting with the various APIs

        :param proxy: An optional proxy for the HTTP client
        :param httpx_kwargs: Additional httpx k

        """

        self._httpx: AsyncClient = self._create_httpx_client(
            proxy=proxy,
            httpx_kwargs=httpx_kwargs or dict()
        )

        self._sign_api_key: Optional[str] = WebDefaults.tiktok_sign_api_key or os.environ.get("SIGN_API_KEY")
        self.__uuc += 1

    def _create_httpx_client(
            self,
            proxy: Optional[Proxy],
            httpx_kwargs: Dict[str, Any]
    ) -> AsyncClient:
        """
        Initialize a new `httpx.AsyncClient`, called internally on object creation

        :param proxy: An optional HTTP proxy to initialize the client with
        :return: An instance of the `httpx.AsyncClient`

        """

        # Create the cookie jar
        self.cookies = httpx_kwargs.pop("cookies", Cookies())

        # Create the headers
        self.headers = {**httpx_kwargs.pop("headers", {}), **WebDefaults.client_headers}

        # Create the params
        self.params: Dict[str, Any] = {
            **httpx_kwargs.pop("params", {}),
            **WebDefaults.client_params
        }

        return AsyncClient(
            proxy=proxy,
            cookies=self.cookies,
            **httpx_kwargs
        )

    async def get_response(
            self,
            url: str,
            extra_params: Optional[Dict] = None,
            extra_headers: Optional[Dict] = None,
            client: Optional[httpx.AsyncClient] = None,
            base_params: bool = True,
            base_headers: bool = True,
            **kwargs
    ) -> Response:
        """
        Get a response from the underlying `httpx.AsyncClient` client.

        :param url: The URL to request
        :param extra_params: Extra parameters to append to the globals
        :param extra_headers: Extra headers to append to the globals
        :param client: An optional override for the `httpx.AsyncClient` client
        :param kwargs: Optional keywords for the `httpx.AsyncClient.get` method
        :param base_params: Whether to include the base params
        :param base_headers: Whether to include the base headers
        :return: An `httpx.Response` object

        """

        # Update UUC param
        self.params["uuc"] = self.__uuc
        self.params["device_id"] = self.generate_device_id()

        params = '&'.join(f"{key}={value}" for key, value in {**(self.params if base_params else {}), **(extra_params or dict())}.items())

        # Make the request
        return await (client or self._httpx).get(
            url=url + "?" + params,
            cookies=self.cookies,
            headers={**(self.headers if base_headers else {}), **(extra_headers or dict())},
            **kwargs
        )

    async def close(self) -> None:
        """
        Close the HTTP client gracefully

        :return: None

        """

        await self._httpx.aclose()

    def __del__(self) -> None:
        """
        Decrement the UUC on object deletion

        :return: None

        """

        self.__uuc = max(0, self.__uuc - 1)

    def set_session_id(self, session_id: str) -> None:
        """
        Set the session id cookies for the HTTP client and Websocket connection

        :param session_id: The (must be valid) session ID
        :return: None

        """

        self.cookies.set("sessionid", session_id)
        self.cookies.set("sessionid_ss", session_id)
        self.cookies.set("sid_tt", session_id)

        # Set logged in status
        self.params['user_is_login'] = "true" if session_id else "false"

    @classmethod
    def generate_device_id(cls) -> int:
        """
        Generate a spoofed device ID for the TikTok API call

        :return: Device ID number

        """

        return random.randrange(10000000000000000000, 99999999999999999999)


class ClientRoute(ABC):
    """
    A callable API route for TikTok

    """

    def __init__(self, web: TikTokHTTPClient):
        """
        Instantiate a route

        :param web: An instance of the HTTP client the route belongs to

        """

        self._web: TikTokHTTPClient = web
        self._logger: logging.Logger = TikTokLiveLogHandler.get_logger()

    @abstractmethod
    def __call__(self, **kwargs: Any) -> Awaitable[Any]:
        """
        Method used for calling the route as a function

        :param kwargs: Arguments to be overridden
        :return: Return to be overridden

        """

        raise NotImplementedError
