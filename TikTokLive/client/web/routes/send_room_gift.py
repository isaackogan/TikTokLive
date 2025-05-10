from json import JSONDecodeError
from typing import Optional, TypedDict

from TikTokLive.client.errors import WebcastBlocked200Error
from TikTokLive.client.web.web_base import ClientRoute, TikTokHTTPClient
from TikTokLive.client.web.web_settings import WebDefaults


class GiftPayload(TypedDict):
    """
    Gift payload for sending a gift to a TikTok LIVE room.

    Example Payload:

    count: 1
    enter_from: live_detail_
    gift_id: 5655
    is_opted_in_host: true
    is_subscription: false
    room_id: 7451132632405510917
    send_gift_req_start_ms: 1734862440968
    send_scene: 1
    send_type: 1
    to_user_id: 7230478347297063942

    """

    room_id: Optional[int]
    count: int
    enter_from: str
    gift_id: int
    is_opted_in_host: bool
    is_subscription: bool
    send_gift_req_start_ms: int
    send_scene: int
    to_user_id: int
    send_type: int


class SendRoomGiftRoute(ClientRoute):

    def __init__(self, web: TikTokHTTPClient):
        super().__init__(web)

    async def __call__(
            self,
            payload: GiftPayload,
    ) -> dict:
        """
        Send a gift to a TikTok LIVE room

        """

        payload["room_id"] = payload["room_id"] if payload["room_id"] else self._web.params["room_id"]

        response = await self._web.post(
            url=WebDefaults.tiktok_webcast_url + "/gift/send/",
            extra_headers={
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
            },

            # Requires the payload to be sent as form data
            data=payload,

            # Requires the curl_cffi backend to spoof JA3 fingerprints
            http_backend="curl_cffi",

            # Requires a valid signature
            sign_url=True,

            # For some reason the signing must be done with the GET method
            # for TikTok to reply with the requisite _signature parameter
            sign_url_method="GET",
            sign_url_type="fetch"
        )

        try:
            response_data: dict = response.json()
        except JSONDecodeError:
            raise WebcastBlocked200Error("Blocked! This is likely due to a mismatch in the JA3 fingerprint.")

        return response_data
