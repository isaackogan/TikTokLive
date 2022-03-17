import urllib.parse
from typing import Dict, Union, Optional

import aiohttp as aiohttp

from TikTokLive.proto.utilities import deserialize_message


class TikTokHTTPClient:
    """
    Client for making HTTP requests to TikTok's Webcast API

    """

    TIKTOK_URL_WEB: str = 'https://www.tiktok.com/'
    TIKTOK_URL_WEBCAST: str = 'https://webcast.tiktok.com/webcast/'
    TIKTOK_HTTP_ORIGIN: str = 'https://www.tiktok.com'

    DEFAULT_CLIENT_PARAMS: Dict[str, Union[int, bool, str]] = {
        "aid": 1988, "app_language": 'en-US', "app_name": 'tiktok_web', "browser_language": 'en', "browser_name": 'Mozilla',
        "browser_online": True, "browser_platform": 'Win32', "version_code": 180800,
        "browser_version": '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
        "cookie_enabled": True, "cursor": '', "device_platform": 'web', "did_rule": 3, "fetch_rule": 1, "identity": 'audience', "internal_ext": '',
        "last_rtt": 0, "live_id": 12, "resp_content_type": 'protobuf', "screen_height": 1152, "screen_width": 2048, "tz_name": 'Europe/Berlin',
    }

    DEFAULT_REQUEST_HEADERS: Dict[str, str] = {
        "Connection": 'keep-alive', "'Cache-Control'": 'max-age=0', "Accept": 'text/html,application/json,application/protobuf',
        "'User-Agent'": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36',
        "Referer": 'https://www.tiktok.com/', "Origin": 'https://www.tiktok.com', "Accept-Language": 'en-US,en;q=0.9', "Accept-Encoding": 'gzip, deflate',
    }

    def __init__(self, headers: Optional[Dict[str, str]] = None, timeout_ms: Optional[int] = None) -> None:
        """
        Initialize TikTok HTTP Client

        :param headers: Custom Headers
        :param timeout_ms: Custom Polling Timeout

        """

        self.timeout: int = int((timeout_ms if isinstance(timeout_ms, int) else 10000) / 1000)
        self.headers: Dict[str, str] = {
            **self.DEFAULT_REQUEST_HEADERS,
            **(headers if isinstance(headers, dict) else dict())
        }

    async def __aiohttp_get_bytes(self, url: str, params: dict = None) -> bytes:
        """
        Get bytes from a given URL with parameters

        :param url: URL to request data from
        :param params: Custom Parameters
        :return: bytearray containing request data
        :raises: asyncio.TimeoutError

        """

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}?{urllib.parse.urlencode(params if params is not None else dict())}", timeout=self.timeout) as request:
                return await request.read()

    async def __aiohttp_get_json(self, url: str, params: dict) -> dict:
        """
        Get json (dict form) from a given URL with parameters

        :param url: URL to request data from
        :param params: Custom Parameters
        :return: bytearray containing request data
        :raises: asyncio.TimeoutError

        """

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}?{urllib.parse.urlencode(params if params is not None else dict())}", timeout=self.timeout) as request:
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
