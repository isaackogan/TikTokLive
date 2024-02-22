import random
import re

from httpx import Response

from TikTokLive.client.errors import UserOfflineError
from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults


class FailedParseRoomIdError(RuntimeError):
    """
    Thrown when the Room ID cannot be parsed

    """


class RoomIdRoute(ClientRoute):
    """
    Route to retrieve the room ID for a user

    """

    async def __call__(self, unique_id: str) -> str:
        """
        Fetch the Room ID for a given unique_id from the page HTML

        :param unique_id: The user's username
        :return: The room ID string

        """

        # Get their livestream HTML
        response: Response = await self._web.get_response(
            url=WebDefaults.tiktok_app_url + f"/@{unique_id}/live"
        )

        # Parse & update the web client
        room_id: str = self.parse_room_id(response.text)
        self._web.params["room_id"] = room_id
        return room_id

    @classmethod
    def parse_room_id(cls, html: str) -> str:
        """
        Parse the room ID from livestream HTML

        :param html: The HTML to parse from https://tiktok.com/@<unique_id>/live
        :return: The user's room id
        :raises: UserOfflineError if the user is offline
        :raises: FailedParseRoomIdError if the user does not exist

        """

        match_metadata = re.search("room_id=([0-9]*)", html)
        if bool(match_metadata):
            return match_metadata.group(0).split("=")[1]

        match_json = re.search('"roomId":"([0-9]*)"', html)
        if bool(match_json):
            return match_json.group(0)

        if '"og:url"' in html:
            raise UserOfflineError("The user might be offline.")
        else:
            raise FailedParseRoomIdError("That user doesn't exist, or you might be blocked by TikTok.")
