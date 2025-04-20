from typing import Any, Dict, Optional

from httpx import Response

from TikTokLive.client.errors import TikTokLiveError
from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults


class FailedFetchGiftListError(TikTokLiveError):
    """
    Thrown when a request to the gift list endpoint fails

    """


class FetchGifListRoute(ClientRoute):
    """
    Retrieve the gift list from TikTok

    """

    async def __call__(self, room_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch the gift list from TikTok

        :param room_id: The room ID to fetch gifts for
        :return: Detailed gift information

        """

        try:
            response: Response = await self._web.get(
                url=WebDefaults.tiktok_webcast_url + "/gift/list/"
            )
            return response.json()["data"]
        except Exception as ex:
            raise FailedFetchGiftListError from ex
