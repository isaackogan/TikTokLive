import logging
from abc import ABC, abstractmethod
from typing import Optional, Any, Awaitable, Dict

import httpx
from httpx import Cookies, AsyncClient, Response, Proxy

from TikTokLive.client.logger import TikTokLiveLogHandler
from TikTokLive.client.web.web_settings import WebDefaults


class WebcastHTTPClient:
    __uuc: int = 0
    __lib: str = "ttlive-python"

    def __init__(
            self,
            unique_id: str,
            proxy: Optional[Proxy] = None,
            sign_api_key: Optional[str] = None,
            httpx_kwargs: dict = {}
    ):
        self.__uuc += 1
        self._unique_id: str = unique_id

        self._sign_api_key: str = sign_api_key or WebDefaults.tiktok_sign_api_key
        self._httpx_kwargs: Dict[str, Any] = httpx_kwargs
        self._httpx: AsyncClient = self._create_httpx_client(proxy)

    async def close(self):
        await self._httpx.aclose()

    def _create_httpx_client(self, proxy: Optional[Proxy]) -> AsyncClient:
        self.cookies = self._httpx_kwargs.pop("cookies", Cookies())
        self.headers = {**self._httpx_kwargs.pop("headers", {}), **WebDefaults.client_headers}

        self.params = {
            "apiKey": self._sign_api_key,
            **self._httpx_kwargs.pop("params", {}), **WebDefaults.client_params
        }

        return AsyncClient(
            proxies=proxy,
            cookies=self.cookies,
            params=self.params,
            headers=self.headers,
            **self._httpx_kwargs
        )

    async def get_response(
            self,
            url: str,
            extra_params: dict = {},
            extra_headers: dict = {},
            client: Optional[httpx.AsyncClient] = None,
            **kwargs
    ) -> Response:
        self.params["uuc"] = self.__uuc

        return await (client or self._httpx).get(
            url=url,
            cookies=self.cookies,
            params={**self.params, **extra_params},
            headers={**self.headers, **extra_headers},
            **kwargs
        )

    async def get_json(self, url: str, extra_params: Optional[dict] = None, **kwargs) -> Optional[dict]:
        response: Response = await self.get_response(url, extra_params, **kwargs)
        return response.json()
        # remember to .get("data") when using

    def __del__(self):
        self.__uuc = max(0, self.__uuc - 1)

    @property
    def client_name(self) -> str:
        return self.__lib

    @property
    def unique_id(self) -> str:
        return self._unique_id

    def set_session_id(self, session_id: str) -> None:
        self.cookies.set("sessionid", session_id)
        self.cookies.set("sessionid_ss", session_id)
        self.cookies.set("sid_tt", session_id)


class WebcastRoute(ABC):

    def __init__(self, web: WebcastHTTPClient):
        self._web: WebcastHTTPClient = web
        self._lib: str = self._web.client_name
        self._logger: logging.Logger = TikTokLiveLogHandler.get_logger()

    @abstractmethod
    def __call__(self, **kwargs: Any) -> Awaitable[Any]:
        raise NotImplementedError
