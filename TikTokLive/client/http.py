import urllib.parse
from typing import Dict, Union, Optional

from aiohttp import ClientSession

from TikTokLive.client.proxy import ProxyContainer
from TikTokLive.proto.utilities import deserialize_message


class TikTokHTTPClient:
    """
    Client for making HTTP requests to TikTok's Webcast API

    """

    TIKTOK_URL_WEB: str = 'https://www.tiktok.com/'
    TIKTOK_URL_WEBCAST: str = 'https://webcast.tiktok.com/webcast/'
    TIKTOK_HTTP_ORIGIN: str = 'https://www.tiktok.com'

    DEFAULT_CLIENT_PARAMS: Dict[str, Union[int, bool, str]] = {
        "aid": 1988, "app_name": 'tiktok_web', "browser_name": 'Mozilla',
        "browser_online": True, "browser_platform": 'Win32', "version_code": 180800,
        "browser_version": '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
        "cookie_enabled": True, "cursor": '', "device_platform": 'web', "did_rule": 3, "fetch_rule": 1, "identity": 'audience', "internal_ext": '',
        "last_rtt": 0, "live_id": 12, "resp_content_type": 'protobuf', "screen_height": 1152, "screen_width": 2048, "tz_name": 'Europe/Berlin',
        "browser_language": "en", "priority_region": "US", "region": "US",
    }

    DEFAULT_REQUEST_HEADERS: Dict[str, str] = {
        "Connection": 'keep-alive', "Cache-Control": 'max-age=0', "Accept": 'text/html,application/json,application/protobuf',
        "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
        "Referer": 'https://www.tiktok.com/', "Origin": 'https://www.tiktok.com', "Accept-Language": 'en-US,en;q=0.9', "Accept-Encoding": 'gzip, deflate',
    }

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout_ms: Optional[int] = None, proxy_container: Optional[ProxyContainer] = None, trust_env: bool = True) -> None:
        """
        Initialize HTTP client

        :param headers: Headers to use to make HTTP requests
        :param timeout_ms: Timeout for HTTP requests
        :param proxy_container: Proxy container to hold proxies for request usage
        :param trust_env: Whether to trust the environment when it comes to proxy usage

        """

        self.timeout: int = int((timeout_ms if isinstance(timeout_ms, int) else 10000) / 1000)
        self.proxy_container: ProxyContainer = proxy_container if proxy_container is not None else ProxyContainer(enabled=False)
        self.headers: Dict[str, str] = {
            **self.DEFAULT_REQUEST_HEADERS,
            **(headers if isinstance(headers, dict) else dict())
        }
        self.cookies: dict = dict()

    async def __aiohttp_get_bytes(self, url: str, params: dict = None) -> bytes:
        """
        Get bytes from a given URL with parameters

        :param url: URL to request data from
        :param params: Custom Parameters
        :return: bytearray containing request data
        :raises: asyncio.TimeoutError

        """
        request_url: str = f"{url}?{urllib.parse.urlencode(params if params is not None else dict())}"

        async with ClientSession() as session:
            async with session.get(request_url, headers=self.headers, timeout=self.timeout, proxy=self.proxy_container.get()) as request:
                return await request.read()

    async def __aiohttp_get_json(self, url: str, params: dict) -> dict:
        """
        Get json (dict form) from a given URL with parameters

        :param url: URL to request data from
        :param params: Custom Parameters
        :return: bytearray containing request data
        :raises: asyncio.TimeoutError

        """

        request_url: str = f"{url}?{urllib.parse.urlencode(params if params is not None else dict())}"

        async with ClientSession() as session:
            async with session.get(request_url, headers=self.headers, timeout=self.timeout, proxy=self.proxy_container.get()) as request:
                return await request.json()

    async def __aiohttp_post_json(self, url: str, params: dict, json: Optional[dict] = None) -> dict:
        """
        Post JSON given a URL with parameters

        :param url: URL to request data from
        :param params: Custom Parameters
        :param json: JSON Payload as Dict
        :return: JSON Result

        :raises: asyncio.TimeoutError

        """
        request_url: str = f"{url}?{urllib.parse.urlencode(params if params is not None else dict())}"

        async with ClientSession(cookies=self.cookies) as session:
            async with session.post(request_url, data=json, headers=self.headers, timeout=self.timeout, proxy=self.proxy_container.get()) as request:
                return await request.json()

    async def get_livestream_page_html(self, unique_id: str) -> str:
        """
        Get livestream page HTML given a unique id

        :param unique_id: Unique ID of the streamer
        :return: HTML string containing page data
        :raises: asyncio.TimeoutError

        """

        response: bytes = await self.__aiohttp_get_bytes(f"{TikTokHTTPClient.TIKTOK_URL_WEB}@{unique_id}/live")
        return response.decode(encoding="utf-8")

    async def get_deserialized_object_from_webcast_api(self, path: str, params: dict, schema: str) -> dict:
        """
        Retrieve and deserialize an object from the Webcast API

        :param path: Webcast path
        :param params: Parameters to encode into URL
        :param schema: Proto schema to decode from
        :return: Deserialized data from API in dictionary format
        :raises: asyncio.TimeoutError

        """

        response: bytes = await self.__aiohttp_get_bytes(self.TIKTOK_URL_WEBCAST + path, params)
        return deserialize_message(schema, response)

    async def get_json_object_from_webcast_api(self, path: str, params: dict) -> dict:
        """
        Retrieve JSON formatted data from the Webcast API

        :param path: Webcast path
        :param params: Parameters to encode into URL
        :return: JSON data from Webcast API
        :raises: asyncio.TimeoutError

        """

        response: dict = await self.__aiohttp_get_json(self.TIKTOK_URL_WEBCAST + path, params)
        return response.get("data")

    async def post_json_to_webcast_api(self, path: str, params: dict, json: Optional[dict] = None):
        """
        Post JSON to the Webcast API

        :param path: Path to POST
        :param params: URLEncoded Params
        :param json: JSON Data
        :return: Result

        """

        response: dict = await self.__aiohttp_post_json(self.TIKTOK_URL_WEBCAST + path, params, json)
        return response
