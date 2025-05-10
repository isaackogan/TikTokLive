from typing import Optional

import httpx

from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults


class SendRoomChatRoute(ClientRoute):

    async def __call__(
            self,
            content: str,
            room_id: Optional[int] = None,
            session_id: Optional[str] = None,
    ) -> dict:

        payload: dict = {
            "roomId": room_id or self._web.params['room_id'],
            "content": content,
            "sessionId": ""
        }

        response: httpx.Response = await self._web.signer.client.post(
            url=WebDefaults.tiktok_sign_url + "/webcast/chat/",
            json=payload,
        )

        return response.json()
