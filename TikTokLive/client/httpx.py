import json as json_parse
import urllib.parse
from asyncio import AbstractEventLoop
from http.cookies import SimpleCookie
from typing import Dict, Optional

import httpx
from httpx import Cookies

from TikTokLive.client import config
from TikTokLive.proto.utilities import deserialize_message
from TikTokLive.types import SignatureRateLimitReached


class TikTokHTTPClient:
    """
    Client for making HTTP requests to TikTok's Webcast API

    """

    _uuc = 0
    _identity = "ttlive-python"

    def __init__(
            self,
            loop: AbstractEventLoop,
            headers: Optional[Dict[str, str]] = None,
            timeout: Optional[float] = None,
            proxies: Optional[Dict[str, str]] = None,
            trust_env: bool = True,
            params: Optional[Dict[str, str]] = dict(),
            sign_api_key: Optional[str] = None
    ):
        """
        Initialize HTTP client for TikTok-related requests

        :param headers: Headers to use to make HTTP requests
        :param timeout: Timeout for HTTP requests
        :param proxies: Enable proxied requests by turning on forwarding for the HTTPX "proxies" argument
        :param trust_env: Whether to trust the environment when it comes to proxy usage
        :param sign_api_key: API key to increase rate limits on the sign server API for bulk usage of the library

        """

        self.loop: AbstractEventLoop = loop
        self.timeout: float = timeout or 10.0
        self.proxies: Optional[Dict[str, str]] = proxies
        self.headers: Dict[str, str] = {**config.DEFAULT_REQUEST_HEADERS, **(headers if isinstance(headers, dict) else dict())}
        self.params: dict = params if params else dict()
        self.sign_api_key: str = sign_api_key or ""
        self.trust_env: bool = trust_env
        self.cookies = Cookies()
        TikTokHTTPClient._uuc += 1

    def __del__(self):
        """
        Internal utility method
        
        """

        TikTokHTTPClient._uuc -= 1

    @classmethod
    def update_url(cls, url: str, params: dict) -> str:
        """
        Update a URL with given parameters by breaking it into components, adding new ones, and rebuilding it

        :param url: The URL we are updating
        :param params: The parameters to update it with
        :return: The updated URL

        """

        parsed = list(urllib.parse.urlparse(url))
        query = {**params, **dict(urllib.parse.parse_qsl(parsed[4]))}
        parsed[4] = urllib.parse.urlencode(query)
        return urllib.parse.urlunparse(parsed)

    async def __httpx_get_bytes(self, url: str, params: dict = None, sign_api: bool = False) -> bytes:
        """
        Get byte data from the Webcast API
        
        :param url: The URL to request
        :param params:  Parameters to include in the URL
        :return: The result of the request (a bytearray)
        :raises: httpx.TimeoutException
        """

        url: str = self.update_url(url, params or dict())

        async with httpx.AsyncClient(trust_env=self.trust_env, proxies=self.proxies, cookies=self.cookies) as client:
            response: httpx.Response = await client.get(url, headers=self.headers, timeout=self.timeout)

        # If requesting the sign api
        if sign_api:
            # Rate Limit
            if response.status_code == 429:
                raise SignatureRateLimitReached(
                    response.headers.get("RateLimit-Reset"),
                    response.headers.get("X-RateLimit-Reset"),
                    "You have hit the rate limit for starting connections. Try again in %s seconds. "
                    "Catch this error & access its attributes (retry_after, reset_time) for data on when you can request next."
                )

            self.__set_tt_cookies(cookies=response.headers.get("X-Set-TT-Cookie"))

        return response.read()

    def __set_tt_cookies(self, cookies: str) -> None:
        """
        Utility method to set TikTok.com cookies from a cookie string received from the Signing API

        :param cookies: X-Set-TT-Cookie string
        :return: None

        """

        # Must be valid
        if not cookies:
            return

        # Convert to k-v
        cookie_jar: SimpleCookie = SimpleCookie()
        cookie_jar.load(cookies)
        cookies: Dict[str, str] = {key: value.value for key, value in cookie_jar.items()}

        for key, value in cookies.items():
            self.cookies.set(key, value, ".tiktok.com")

    async def __httpx_get_json(self, url: str, params: dict) -> dict:
        """
        Get json (dict) from a given URL with parameters from the Webcast API

        :param url: URL to request data from
        :param params: Custom Parameters
        :return: bytearray containing request data
        :raises: httpx.TimeoutException

        """

        return json_parse.loads((await self.__httpx_get_bytes(url=url, params=params)).decode(encoding="utf-8"))

    async def __httpx_post_json(self, url: str, params: dict, json: Optional[dict] = None) -> dict:
        """
        Post JSON given a URL with parameters

        :param url: URL to request data from
        :param params: Custom Parameters
        :param json: JSON Payload as Dict
        :return: JSON Result
        :raises: httpx.TimeoutException

        """

        url: str = self.update_url(url, params or dict())

        async with httpx.AsyncClient(trust_env=self.trust_env, proxies=self.proxies, cookies=self.cookies) as client:
            response: httpx.Response = await client.post(
                url=url,
                data=json,
                headers=self.headers,
                timeout=self.timeout
            )

            return response.json()

    async def get_livestream_page_html(self, unique_id: str) -> str:
        """
        Get livestream page HTML given a unique id

        :param unique_id: Unique ID of the streamer
        :return: HTML string containing page data
        :raises: httpx.TimeoutException

        """

        response: bytes = await self.__httpx_get_bytes(f"{config.TIKTOK_URL_WEB}@{unique_id}/live")
        return response.decode(encoding="utf-8")

    async def get_deserialized_object_from_signing_api(self, path: str, params: dict, schema: str) -> dict:
        """
        Retrieve and deserialize an object from the Webcast API

        :param path: Webcast path
        :param params: Parameters to encode into URL
        :param schema: Proto schema to decode from
        :return: Deserialized data from API in dictionary format
        :raises: httpx.TimeoutException

        """

        params: dict = {**params, **{"client": TikTokHTTPClient._identity, "uuc": TikTokHTTPClient._uuc, "apiKey": self.sign_api_key}}
        response: bytes = await self.__httpx_get_bytes(config.TIKTOK_SIGN_API + path, params, sign_api=True)
        return deserialize_message(schema, response)

    async def get_deserialized_object_from_webcast_api(self, path: str, params: dict, schema: str) -> dict:
        """
        Retrieve and deserialize an object from the Webcast API

        :param path: Webcast path
        :param params: Parameters to encode into URL
        :param schema: Proto schema to decode from
        :return: Deserialized data from API in dictionary format
        :raises: httpx.TimeoutException

        """

        response: bytes = await self.__httpx_get_bytes(config.TIKTOK_URL_WEBCAST + path, params)
        return deserialize_message(schema, response)

    async def get_image_from_tiktok_api(self, url: str, params: dict) -> Optional[bytes]:
        """
        Retrieve an image resource from TikTok's API as bytes

        :param url: URL of the image
        :param params: Extra parameters
        :return: Hopefully, the image, in bytes

        """

        response: bytes = await self.__httpx_get_bytes(url, params)
        return response

    async def get_json_object_from_webcast_api(self, path: str, params: dict) -> dict:
        """
        Retrieve JSON formatted data from the Webcast API

        :param path: Webcast path
        :param params: Parameters to encode into URL
        :return: JSON data from Webcast API
        :raises: httpx.TimeoutException

        """

        response: dict = await self.__httpx_get_json(config.TIKTOK_URL_WEBCAST + path, params)
        return response.get("data")

    async def post_json_to_webcast_api(self, path: str, params: dict, json: Optional[dict] = None) -> dict:
        """
        Post JSON to the Webcast API

        :param path: Path to POST
        :param params: URLEncoded Params
        :param json: JSON Data
        :return: Result from the Webcast API POST request
        :raises: httpx.TimeoutException

        """

        response: dict = await self.__httpx_post_json(config.TIKTOK_URL_WEBCAST + path, params, json)
        return response

    async def post_json_to_url(self, url: str, headers: dict, json: Optional[dict] = None) -> dict:
        """
        Post JSON given an already-defined URL, headers, and JSON

        :param url: URL to request data from
        :param headers: Custom Headers
        :param json: JSON Payload as Dict
        :return: JSON Result
        :raises: httpx.TimeoutException

        """

        async with httpx.AsyncClient(trust_env=self.trust_env, proxies=self.proxies, cookies=self.cookies) as client:
            response: httpx.Response = await client.post(
                url=url,
                data=json,
                headers=headers,
                timeout=self.timeout
            )

            return response.json()
