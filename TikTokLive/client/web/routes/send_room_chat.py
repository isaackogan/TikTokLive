from typing import Optional

import httpx
from urllib.parse import quote

from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults


class SendRoomChatRoute(ClientRoute):

    async def __call__(
            self,
            content: str,
            room_id: Optional[int] = None
    ) -> dict:
        """
        Send a chat message to a TikTok room

        """

        extra_params: dict = {"content": quote(content, safe='?%')}

        if room_id is not None:
            extra_params["room_id"] = room_id

        response: httpx.Response = await self._web.post(
            sign_url=True,
            url=WebDefaults.tiktok_webcast_url + "/room/chat/",
            extra_params=extra_params,
        )

        return response.json()
