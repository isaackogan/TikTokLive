import random
import re

from httpx import Response

from TikTokLive.client.errors import UserOfflineError
from TikTokLive.client.web.web_base import WebcastRoute
from TikTokLive.client.web.web_settings import WebDefaults


class FailedParseRoomIdError(RuntimeError):
    pass


class RoomIdRoute(WebcastRoute):
    """Retrieve the room ID"""

    PATH: str = WebDefaults.tiktok_app_url + "/@%s/live"

    async def __call__(self, unique_id: str) -> str:

        response: Response = await self._web.get_response(
            url=self.PATH % (unique_id,)
        )

        # Parse & update the web client
        room_id: str = self.parse_room_id(response.text)
        self._web.params["room_id"] = room_id
        return room_id

    @classmethod
    def generate_device_id(cls) -> int:
        """Generate Device ID"""

        return random.randrange(10000000000000000000, 99999999999999999999)

    @classmethod
    def parse_room_id(cls, html: str) -> str:
        """Parse Room ID"""

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
