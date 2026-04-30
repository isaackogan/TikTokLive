from typing import Any, Dict, Optional

from EulerApiSdk.api.tik_tok_live_premium import send_room_chat
from EulerApiSdk.models.webcast_room_chat_payload import WebcastRoomChatPayload
from EulerApiSdk.types import UNSET, Unset

from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_utils import check_authenticated_session


class SendRoomChatRoute(ClientRoute):

    async def __call__(
            self,
            content: str,
            room_id: Optional[int] = None,
            session_id: Optional[str] = None,
            tt_target_idc: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Check sid
        session_id = session_id or self._web.cookies.get('sessionid')
        tt_target_idc = tt_target_idc or self._web.cookies.get('tt-target-idc')
        check_authenticated_session(session_id, tt_target_idc, session_required=True)

        # Check room_id
        room_id = room_id or self._web.params.get('room_id')

        if not room_id:
            raise ValueError(
                "Room ID is required to send a chat message. Use client.web.send_room_chat if you want to use this function without connecting.")

        body = WebcastRoomChatPayload(
            content=content,
            target_room_id=str(room_id),
        )

        # Session credentials ride in ``X-Cookie-Header`` so the sign server
        # can replay them as the authenticated user. v2 sent them as JSON
        # body fields (``sessionId`` / ``ttTargetIdc``); the SDK moved them
        # to the cookie header for consistency with TikTok's own auth model.
        cookie_parts = [f"sessionid={session_id}"]
        if tt_target_idc:
            cookie_parts.append(f"tt-target-idc={tt_target_idc}")
        cookie_header = "; ".join(cookie_parts)

        # ``send_room_chat`` is annotated as taking ``AuthenticatedClient`` only
        # but at runtime ``Client`` works identically.
        sdk_response = await send_room_chat.asyncio_detailed(
            client=self._web.signer.sdk_client,  # type: ignore[arg-type]
            body=body,
            x_cookie_header=cookie_header,
        )

        if sdk_response.parsed is None:
            return {"code": sdk_response.status_code.value, "message": "", "data": None}

        parsed = sdk_response.parsed
        message: str = "" if isinstance(parsed.message, Unset) else parsed.message
        data = None if isinstance(parsed.data, Unset) else parsed.data
        return {"code": int(parsed.code), "message": message, "data": data}
