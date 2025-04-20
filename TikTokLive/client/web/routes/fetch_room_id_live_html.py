import json
import re
from json import JSONDecodeError
from typing import Optional

from httpx import Response

from TikTokLive.client.errors import UserOfflineError, UserNotFoundError, TikTokLiveError
from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults


class FailedParseRoomIdError(TikTokLiveError):
    """
    Thrown when the Room ID cannot be parsed

    """


class FetchRoomIdLiveHTMLRoute(ClientRoute):
    """
    Route to retrieve the room ID for a user

    """

    SIGI_PATTERN: re.Pattern = re.compile(r"""<script id="SIGI_STATE" type="application/json">(.*?)</script>""")

    async def __call__(self, unique_id: str) -> str:
        """
        Fetch the Room ID for a given unique_id from the page HTML

        :param unique_id: The user's username
        :return: The room ID string

        """

        # Get their livestream HTML
        response: Response = await self._web.get(
            url=WebDefaults.tiktok_app_url + f"/@{unique_id}/live",
            base_params=False
        )

        # Parse room ID
        return self.parse_room_id(response.text)

    @classmethod
    def parse_room_id(cls, html: str) -> str:
        """
        Parse the room ID from livestream HTML

        :param html: The HTML to parse from https://tiktok.com/@<unique_id>/live
        :return: The user's room id
        :raises: UserOfflineError if the user is offline
        :raises: FailedParseRoomIdError if the user does not exist

        """

        match: Optional[re.Match[str]] = cls.SIGI_PATTERN.search(html)

        if match is None:
            raise FailedParseRoomIdError("Failed to extract the SIGI_STATE HTML tag, you might be blocked by TikTok.")

        # Load SIGI_STATE JSON
        try:
            sigi_state: dict = json.loads(match.group(1))
        except JSONDecodeError:
            raise FailedParseRoomIdError("Failed to parse SIGI_STATE into JSON. Are you captcha-blocked by TikTok?")

        # LiveRoom is missing for users that have never been live
        if sigi_state.get('LiveRoom') is None:
            raise UserNotFoundError(
                "The requested user is not capable of going LIVE on TikTok, "
                "has never gone live on TikTok, or does not exist.."
            )

        # Method 1) Parse the room ID from liveRoomUserInfo/user#roomId
        room_data: dict = sigi_state["LiveRoom"]["liveRoomUserInfo"]["user"]
        room_id: str = room_data.get('roomId')
        username_str: str = f" '@{room_data['uniqueId']}' " if room_data.get('uniqueId') else " "

        # User is offline
        if room_data.get('status') == 4:
            raise UserOfflineError(f"The requested TikTok LIVE user{username_str}is offline.")

        return room_id
