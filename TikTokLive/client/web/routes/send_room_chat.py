from typing import Optional

import httpx

from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.client.web.web_utils import check_authenticated_session


class SendRoomChatRoute(ClientRoute):

    async def __call__(
            self,
            content: str,
            room_id: Optional[int] = None,
            session_id: Optional[str] = None,
            tt_target_idc: Optional[str] = None,
    ) -> dict:
        # Check sid
        session_id: str = session_id or self._web.cookies.get('sessionid')
        tt_target_idc: str = tt_target_idc or self._web.cookies.get('tt-target-idc')
        check_authenticated_session(session_id, tt_target_idc, session_required=True)

        # Check room_id
        room_id: int = room_id or self._web.params.get('room_id')

        if not room_id:
            raise ValueError("Room ID is required to send a chat message. Use client.web.send_room_chat if you want to use this function without connecting.")

        payload: dict = {
            "roomId": str(room_id),
            "content": content,
            "sessionId": session_id,
            "ttTargetIdc": tt_target_idc,
        }

        response: httpx.Response = await self._web.signer.client.post(
            url=WebDefaults.tiktok_sign_url + "/webcast/chat/",
            json=payload,
        )

        return response.json()
