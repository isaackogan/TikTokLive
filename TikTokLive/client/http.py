import json as json_parse
import urllib.parse
from typing import Dict, Optional

import httpx

from TikTokLive.client import config
from TikTokLive.proto.utilities import deserialize_message


class TikTokHTTPClient:
    """
    Client for making HTTP requests to TikTok's Webcast API

    """

    def __init__(
            self,
            headers: Optional[Dict[str, str]] = None,
            timeout_ms: Optional[int] = None,
            proxies: Optional[Dict[str, str]] = None,
            trust_env: bool = True,
            params: Optional[Dict[str, str]] = dict(),
    ):
        """
        Initialize HTTP client for TikTok-related requests

        :param headers: Headers to use to make HTTP requests
        :param timeout_ms: Timeout for HTTP requests
        :param proxies: Enable proxied requests by turning on forwarding for the HTTPX "proxies" argument
        :param trust_env: Whether to trust the environment when it comes to proxy usage

        """

        self.timeout: int = int((timeout_ms if isinstance(timeout_ms, int) else 10000) / 1000)
        self.proxies: Optional[Dict[str, str]] = proxies
        self.headers: Dict[str, str] = {**config.DEFAULT_REQUEST_HEADERS, **(headers if isinstance(headers, dict) else dict())}
        self.params: dict = params if params else dict()

        self.trust_env: bool = trust_env
        self.client = httpx.AsyncClient(trust_env=trust_env, proxies=proxies)
        self.__tokens: dict = {}

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

    async def __get_signed_url(self, url: str) -> str:
        """
        Sign a URL via external signing agent to authenticate against TikTok's Webcast API.
        This is an API made *for* this library, NOT by TikTok.

        :param url: The URL to sign
        :return: The signed URL

        """

        # Get the signed URL
        response: httpx.Response = await self.client.get(
            url=f"{config.TIKTOK_SIGN_API}webcast/sign_url?client=ttlive-python&url={urllib.parse.quote(url)}",
            timeout=self.timeout
        )

        # Update client information
        tokens: dict = response.json()
        self.headers["User-Agent"] = tokens.get("User-Agent")
        return tokens.get("signedUrl")

    async def __httpx_get_bytes(self, url: str, params: dict = None, sign_url: bool = False) -> bytes:
        """
        Get byte data from the Webcast API
        
        :param url: The URL to request
        :param params:  Parameters to include in the URL
        :param sign_url: Whether to sign the URL (for authenticated endpoints)
        :return: The result of the request (a bytearray)
        :raises: httpx.TimeoutException
        """

        url: str = self.update_url(url, params if params else dict())
        response: httpx.Response = await self.client.get(await self.__get_signed_url(url) if sign_url else url, headers=self.headers, timeout=self.timeout)
        return response.read()

    async def __aiohttp_get_json(self, url: str, params: dict, sign_url: bool = False) -> dict:
        """
        Get json (dict) from a given URL with parameters from the Webcast API

        :param url: URL to request data from
        :param params: Custom Parameters
        :return: bytearray containing request data
        :raises: httpx.TimeoutException

        """

        return json_parse.loads((await self.__httpx_get_bytes(url=url, params=params, sign_url=sign_url)).decode(encoding="utf-8"))

    async def __aiohttp_post_json(self, url: str, params: dict, json: Optional[dict] = None, sign_url: bool = False) -> dict:
        """
        Post JSON given a URL with parameters

        :param url: URL to request data from
        :param params: Custom Parameters
        :param json: JSON Payload as Dict
        :param sign_url: Whether to sign the URL (for authenticated endpoints)
        :return: JSON Result
        :raises: httpx.TimeoutException

        """

        url: str = self.update_url(url, params if params else dict())
        response: httpx.Response = await self.client.post(await self.__get_signed_url(url) if sign_url else url, data=json, headers=self.headers, timeout=self.timeout)
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

    async def get_deserialized_object_from_webcast_api(self, path: str, params: dict, schema: str, sign_url: bool = False) -> dict:
        """
        Retrieve and deserialize an object from the Webcast API

        :param sign_url: Whether to sign the URL (if it's an authenticated request)
        :param path: Webcast path
        :param params: Parameters to encode into URL
        :param schema: Proto schema to decode from
        :return: Deserialized data from API in dictionary format
        :raises: httpx.TimeoutException

        """

        response: bytes = await self.__httpx_get_bytes(config.TIKTOK_URL_WEBCAST + path, params, sign_url=sign_url)
        return deserialize_message(schema, response)

    async def get_json_object_from_webcast_api(self, path: str, params: dict) -> dict:
        """
        Retrieve JSON formatted data from the Webcast API

        :param path: Webcast path
        :param params: Parameters to encode into URL
        :return: JSON data from Webcast API
        :raises: httpx.TimeoutException

        """

        response: dict = await self.__aiohttp_get_json(config.TIKTOK_URL_WEBCAST + path, params)
        return response.get("data")

    async def post_json_to_webcast_api(self, path: str, params: dict, json: Optional[dict] = None, sign_url: bool = False) -> dict:
        """
        Post JSON to the Webcast API

        :param sign_url: Whether to sign the URL (if it's an authenticated request)
        :param path: Path to POST
        :param params: URLEncoded Params
        :param json: JSON Data
        :return: Result from the Webcast API POST request
        :raises: httpx.TimeoutException

        """

        response: dict = await self.__aiohttp_post_json(config.TIKTOK_URL_WEBCAST + path, params, json, sign_url=sign_url)
        return response
