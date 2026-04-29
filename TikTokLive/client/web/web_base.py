import logging
import random
from abc import ABC
from typing import Any, Dict, Literal, Optional

import httpx
from httpx import Cookies, AsyncClient, Proxy, URL

from TikTokLive.client.logger import TikTokLiveLogHandler
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.client.web.web_signer import TikTokSigner, SignData


class TikTokHTTPClient:
    """
    HTTP client for interacting with the various APIs

    """

    def __init__(
            self,
            web_proxy: Optional[Proxy] = None,
            httpx_kwargs: Optional[dict] = None,
            signer_kwargs: Optional[dict] = None
    ):
        """
        Create an HTTP client for interacting with the various APIs

        :param web_proxy: An optional proxy for the HTTP client
        :param httpx_kwargs: Additional httpx kwargs
        :param signer_kwargs: Additional signer kwargs

        """

        # The HTTP client
        self._httpx: AsyncClient = self._create_httpx_client(
            proxy=web_proxy,
            httpx_kwargs=httpx_kwargs or dict()
        )

        # The URL signer
        self._tiktok_signer: TikTokSigner = TikTokSigner(**(signer_kwargs or dict()))

    @property
    def httpx_client(self) -> AsyncClient:
        """
        Get the underlying `httpx.AsyncClient` instance

        :return: The `httpx.AsyncClient` instance

        """

        return self._httpx

    @property
    def signer(self) -> TikTokSigner:
        """
        Get the TikTok signer for the HTTP client

        :return: The TikTok signer

        """

        return self._tiktok_signer

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
        self.cookies = Cookies({
            **WebDefaults.web_client_cookies,
            **httpx_kwargs.pop("cookies", {})
        })

        # Create the headers
        self.headers = {
            **WebDefaults.web_client_headers,
            **httpx_kwargs.pop("headers", {})
        }

        # Create the params
        self.params: Dict[str, Any] = {
            **WebDefaults.web_client_params,
            **httpx_kwargs.pop("params", dict())
        }

        return AsyncClient(
            proxy=proxy,
            cookies=self.cookies,
            **httpx_kwargs
        )

    async def close(self) -> None:
        """
        Close the HTTP client gracefully

        :return: None

        """

        await self._httpx.aclose()

    def set_session(self, session_id: str | None, tt_target_idc: str | None) -> None:
        """
        Set the session id cookies for the HTTP client and Websocket connection

        :param session_id: The (must be valid) session ID
        :param tt_target_idc: The tt-target-idc cookie, i.e. the data center holding the user's account credentials. (e.g. eu-ttp2)
        :return: None

        """

        # Set the target datacenter
        self.cookies.set("tt-target-idc", tt_target_idc)

        # Set the cookies
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

    def build_url(
            self,
            url: str | URL,
            extra_params: Optional[dict] = None,
            base_params: bool = True
    ) -> URL:

        # Built the dict of URL params that were PASSED
        try:
            url_params = url.split("?")[1].split("&")
            url_params = {param.split("=")[0]: param.split("=")[1] for param in url_params}
        except IndexError:
            url_params = {}

        try:
            url_base = url.split("?")[0]
        except IndexError:
            url_base = url

        # If base_params is True, include them, but make sure the current url_params override
        if base_params:
            url_params = {**(self.params if base_params else {}), **url_params}

        # Now include extra params
        url_params = {**url_params, **(extra_params or dict())}

        # Rebuild the URL
        url = url_base + "?" + "&".join([f"{key}={value}" for key, value in url_params.items()])
        return httpx.URL(url)

    async def build_request(
            self,
            url: str | URL,
            method: str,
            httpx_client: Optional[httpx.AsyncClient] = None,
            extra_params: Optional[Dict] = None,
            extra_headers: Optional[Dict] = None,
            base_params: bool = True,
            base_headers: bool = True,
            sign_url: bool = False,
            sign_url_method: Optional[str] = None,
            sign_url_type: Optional[Literal["xhr", "fetch"]] = None,
            sign_url_payload: Optional[str] = None,
            **kwargs
    ) -> httpx.Request:
        """
       BUILD a request to call the httpx client

       :param url: The URL to request
       :param sign_url: Whether to sign the URL before requesting
       :param method: The HTTP method to use
       :param extra_params: Extra parameters to append to the globals
       :param extra_headers: Extra headers to append to the globals
       :param httpx_client: An optional override for the `httpx.AsyncClient` client
       :param kwargs: Optional keywords for the `httpx.AsyncClient.get` method
       :param sign_url_method: The HTTP method to sign with
       :param base_params: Whether to include the base params
       :param base_headers: Whether to include the base headers
       :param sign_url_type: The type of signing to use
       :param sign_url_payload: The payload to use for signing
       :return: An `httpx.Response` object

       """

        # Generate a device ID
        self.params["device_id"] = self.generate_device_id()

        # Use the provided client or the default one
        client = httpx_client or self._httpx

        # Build the request object
        request: httpx.Request = client.build_request(
            method=method,
            url=self.build_url(url, extra_params, base_params),
            cookies=self.cookies,
            headers={**(self.headers if base_headers else {}), **(extra_headers or dict())},
            **kwargs
        )

        # Sign the URL & update the request accordingly
        if sign_url:
            sign_data: SignData = (
                await self._tiktok_signer.webcast_sign(
                    url=request.url,
                    method=sign_url_method or method,
                    sign_url_type=sign_url_type if sign_url_type else "xhr",
                    payload=sign_url_payload,
                    user_agent=self.headers['User-Agent'],
                    session_id=self.cookies.get('sessionid'),
                    tt_target_idc=self.cookies.get('tt-target-idc'),
                )
            )['response']
            request.headers['User-Agent'] = sign_data['userAgent']
            request.url = httpx.URL(url=sign_data['signedUrl'])

        return request

    async def request(
            self,
            url: str,
            method: str,
            http_client: Optional[httpx.AsyncClient] = None,
            extra_params: Optional[Dict] = None,
            extra_headers: Optional[Dict] = None,
            base_params: bool = True,
            base_headers: bool = True,
            sign_url: bool = False,
            sign_url_method: Optional[str] = None,
            sign_url_type: Optional[Literal["xhr", "fetch"]] = None,
            **kwargs
    ) -> httpx.Response:
        """
        Request a response from the underlying `httpx.AsyncClient` client.

        :param url: The URL to request
        :param sign_url: Whether to sign the URL before requesting
        :param method: The HTTP method to use
        :param extra_params: Extra parameters to append to the globals
        :param extra_headers: Extra headers to append to the globals
        :param http_client: An optional override for the `httpx.AsyncClient` client
        :param kwargs: Optional keywords for the `httpx.AsyncClient.get` method
        :param base_params: Whether to include the base params
        :param base_headers: Whether to include the base headers
        :param sign_url_method: The HTTP method to sign with
        :param sign_url_type: The type of signing to use
        :return: An `httpx.Response` object

        """

        # Build the request
        request: httpx.Request = await self.build_request(
            url=url,
            method=method,
            extra_params=extra_params,
            extra_headers=extra_headers,
            base_params=base_params,
            base_headers=base_headers,
            sign_url=sign_url,
            httpx_client=http_client,
            sign_url_method=sign_url_method,
            sign_url_type=sign_url_type,
            **kwargs
        )

        http_client = http_client or self._httpx
        return await http_client.send(request)

    async def get(
            self,
            url: str,
            extra_params: Optional[Dict] = None,
            extra_headers: Optional[Dict] = None,
            http_client: Optional[httpx.AsyncClient] = None,
            base_params: bool = True,
            base_headers: bool = True,
            sign_url: bool = False,
            sign_url_method: Optional[str] = None,
            sign_url_type: Optional[Literal["xhr", "fetch"]] = None,
            **kwargs
    ) -> httpx.Response:
        return await self.request(
            method="GET",
            url=url,
            extra_params=extra_params,
            extra_headers=extra_headers,
            http_client=http_client,
            base_params=base_params,
            base_headers=base_headers,
            sign_url=sign_url,
            sign_url_method=sign_url_method,
            sign_url_type=sign_url_type,
            **kwargs
        )

    async def post(
            self,
            url: str,
            extra_params: Optional[Dict] = None,
            extra_headers: Optional[Dict] = None,
            http_client: Optional[httpx.AsyncClient] = None,
            base_params: bool = True,
            base_headers: bool = True,
            sign_url: bool = False,
            sign_url_method: Optional[str] = None,
            sign_url_type: Optional[Literal["xhr", "fetch"]] = None,
            **kwargs
    ) -> httpx.Response:
        return await self.request(
            method="POST",
            url=url,
            extra_params=extra_params,
            extra_headers=extra_headers,
            http_client=http_client,
            base_params=base_params,
            base_headers=base_headers,
            sign_url=sign_url,
            sign_url_method=sign_url_method,
            sign_url_type=sign_url_type,
            **kwargs
        )


class ClientRoute(ABC):
    """
    Base class for callable API routes. Provides dependency injection of the
    shared ``TikTokHTTPClient`` and a logger; each subclass defines its own
    ``__call__`` signature with concrete parameter and return types.

    """

    def __init__(self, web: TikTokHTTPClient):
        """
        Instantiate a route

        :param web: An instance of the HTTP client the route belongs to

        """

        self._web: TikTokHTTPClient = web
        self._logger: logging.Logger = TikTokLiveLogHandler.get_logger()
