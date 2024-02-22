from typing import Any, Dict, Optional

from httpx import Response

from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults


class FailedFetchRoomInfoError(RuntimeError):
    """
    Thrown if Room info request fails

    """


class FetchRoomInfoRoute(ClientRoute):
    """
    Retrieve the room info payload of a livestream room

    """

    async def __call__(self, room_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch room info for a given livestream room id

        :param room_id: The room id to get info for
        :return: The room info dict object

        """

        try:

            response: Response = await self._web.get_response(
                url=WebDefaults.tiktok_webcast_url + "/room/info/",
                extra_params={"room_id": room_id or self._web.params["room_id"]}
            )

            return response.json()["data"]

        except Exception as ex:
            raise FailedFetchRoomInfoError from ex
