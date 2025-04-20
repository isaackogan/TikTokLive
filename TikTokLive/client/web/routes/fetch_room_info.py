from typing import Any, Dict, Optional

from httpx import Response

from TikTokLive.client.errors import AgeRestrictedError, TikTokLiveError
from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults


class FailedFetchRoomInfoError(TikTokLiveError):
    """
    Thrown if Room info request fails

    """


class InvalidFetchRoomInfoPayload(TikTokLiveError):
    pass


class FetchRoomInfoRoute(ClientRoute):
    """
    Retrieve the room info payload of a livestream room

    """

    async def __call__(
            self,
            room_id: Optional[int] = None,
            unique_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch room info for a given livestreamer

        Known Constraint: This will not work if the stream is 18+ as age restricted streams cannot have room info retrieved

        :param room_id: The room id to get info for
        :return: The room info dict object

        """

        if room_id and unique_id:
            raise InvalidFetchRoomInfoPayload("Only one of room_id or unique_id may be specified")

        if unique_id:
            url: str = WebDefaults.tiktok_webcast_url + "/room/info_by_user/"
            extra_params: dict = {"unique_id": unique_id}
        else:
            url: str = WebDefaults.tiktok_webcast_url + "/room/info/"
            room_id: Optional[str] = str(room_id) if room_id else self._web.params["room_id"]
            if room_id is None:
                raise InvalidFetchRoomInfoPayload("No room_id specified & the client has no room ID stored")
            extra_params: dict = {"room_id": room_id}

        try:

            # Fetch from API
            response: Response = await self._web.get(
                url=url,
                extra_params=extra_params
            )
            # Get data
            data: dict = response.json().get("data", dict())

        except Exception as ex:
            raise FailedFetchRoomInfoError from ex

        # If age restricted
        if "prompts" in data or len(data) <= 1:
            raise AgeRestrictedError(
                "Age restricted stream. Cannot fetch room info. "
                "Pass sessionid to log in & bypass age restriction."
            )

        return data
