from typing import Any, Dict, Optional

from httpx import Response

from TikTokLive.client.web.web_base import WebcastRoute
from TikTokLive.client.web.web_settings import WebDefaults


class FailedFetchRoomInfoError(RuntimeError):
    pass


class RoomInfoRoute(WebcastRoute):
    """Retrieve the room ID"""

    PATH: str = WebDefaults.tiktok_webcast_url + "/room/info/"

    async def __call__(self, room_id: Optional[str] = None) -> Dict[str, Any]:

        try:

            response: Response = await self._web.get_response(
                url=self.PATH,
                extra_params={"room_id": room_id or self._web.params["room_id"]}
            )

            return response.json()["data"]

        except Exception as ex:
            raise FailedFetchRoomInfoError from ex
