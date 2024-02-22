from typing import Any, Dict, Optional

from httpx import Response

from TikTokLive.client.web.web_base import WebcastRoute
from TikTokLive.client.web.web_settings import WebDefaults


class FailedFetchGiftListError(RuntimeError):
    pass


class GiftListRoute(WebcastRoute):
    """Retrieve the room ID"""

    PATH: str = WebDefaults.tiktok_webcast_url + "/gift/list/"

    async def __call__(self, room_id: Optional[str] = None) -> Dict[str, Any]:

        try:
            response: Response = await self._web.get_response(url=self.PATH)
            return response.json()["data"]
        except Exception as ex:
            raise FailedFetchGiftListError from ex
