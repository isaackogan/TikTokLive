from json import JSONDecodeError
from typing import Optional, Dict

from TikTokLive.client.errors import UserOfflineError, WebcastBlocked200Error
from TikTokLive.client.web.web_base import ClientRoute, TikTokHTTPClient
from TikTokLive.client.web.web_settings import WebDefaults


class SendRoomLikeRoute(ClientRoute):

    def __init__(self, web: TikTokHTTPClient):
        super().__init__(web)

    async def __call__(
            self,
            count: int,
            room_id: Optional[int] = None
    ) -> dict:
        """
        Send a specified # of likes to a TikTok LIVE room

        """

        extra_params: Dict[str, str] = {
            "room_id": room_id if room_id else self._web.params["room_id"],
            "count": count
        }

        response = await self._web.post(
            url=WebDefaults.tiktok_webcast_url + "/room/like/",
            extra_params=extra_params,

            # Requires the curl_cffi backend to spoof JA3 fingerprints
            http_backend="curl_cffi",

            # Requires a valid signature
            sign_url=True,

            # For some reason the signing must be done with the GET method
            # for TikTok to reply with the requisite _signature parameter
            sign_url_method="GET",
            sign_url_type="fetch",
        )

        try:
            response_data: dict = response.json()
        except JSONDecodeError:
            raise WebcastBlocked200Error("Blocked! This is likely due to a mismatch in the JA3 fingerprint.")

        if response_data['data']['result'] == 'room_err':
            raise UserOfflineError("You cannot send a like to a room that is offline!")

        return response_data
