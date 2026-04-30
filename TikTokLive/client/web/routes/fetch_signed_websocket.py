import enum
import json
import os
from http.cookies import SimpleCookie
from json import JSONDecodeError
from typing import Optional

import httpx
from EulerApiSdk.api.tik_tok_live import fetch_webcast_url
from EulerApiSdk.models.webcast_fetch_platform import WebcastFetchPlatform
from EulerApiSdk.types import UNSET

from TikTokLive.client.errors import SignAPIError, SignatureRateLimitError
from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import CLIENT_NAME
from TikTokLive.client.web.web_utils import check_authenticated_session
from TikTokLive.client.ws.ws_utils import extract_webcast_response_message
from TikTokLive.proto import ProtoMessageFetchResult, WebcastPushFrame


class WebcastPlatform(enum.Enum):
    """
    Enum for the platform to request the WebSocket URL for

    """

    WEB = "web"
    MOBILE = "mobile"


# Map our public-API enum onto the SDK's. Kept distinct so consumers don't
# have to import from EulerApiSdk just to pick a platform.
_PLATFORM_TO_SDK: dict[WebcastPlatform, WebcastFetchPlatform] = {
    WebcastPlatform.WEB: WebcastFetchPlatform.WEB,
    WebcastPlatform.MOBILE: WebcastFetchPlatform.MOBILE,
}


class FetchSignedWebSocketRoute(ClientRoute):
    """
    Call the signature server to receive the TikTok websocket URL

    """

    async def __call__(
            self,
            platform: WebcastPlatform,
            room_id: Optional[int] = None,
            session_id: Optional[str] = None,
            tt_target_idc: Optional[str] = None
    ) -> ProtoMessageFetchResult:
        """
        Call the method to get the first ProtoMessageFetchResult (as bytes) to use to upgrade to WebSocket & perform the first ack

        :param room_id: Override the room ID to fetch the webcast for
        :return: The ProtoMessageFetchResult forwarded from the sign server proxy, as raw bytes

        """

        # The session ID we want to add to the request
        session_id = session_id or self._web.cookies.get('sessionid')
        tt_target_idc = tt_target_idc or self._web.cookies.get('tt-target-idc')

        if check_authenticated_session(session_id, tt_target_idc, session_required=False):
            self._logger.warning("Sending session ID to sign server for WebSocket connection. This is a risky operation.")

        if platform == WebcastPlatform.MOBILE and not session_id:
            raise ValueError("Mobile platform requires a 'sessionid' cookie to be set, via client.web.set_session().")

        effective_room_id = room_id or self._web.params.get('room_id', None)

        # Build the request via the SDK's ``_get_kwargs`` so query-param /
        # header construction stays in lockstep with upstream — but bypass
        # ``asyncio_detailed`` because its 200 handler unconditionally calls
        # ``response.json()`` on what is in fact raw protobuf bytes.
        kwargs = fetch_webcast_url._get_kwargs(
            client_query=CLIENT_NAME,
            room_id=str(effective_room_id) if effective_room_id is not None else UNSET,
            user_agent=self._web.headers['User-Agent'],
            platform=_PLATFORM_TO_SDK[platform],
            client_enter=True,
            session_id=session_id if session_id else UNSET,
            tt_target_idc=tt_target_idc if tt_target_idc else UNSET,
        )

        try:
            response: httpx.Response = await self._web.signer.sdk_client.get_async_httpx_client().request(**kwargs)
        except httpx.ConnectError as ex:
            raise SignAPIError(
                SignAPIError.ErrorReason.CONNECT_ERROR,
                "Failed to connect to the sign server due to an httpx.ConnectError!",
                response=None
            ) from ex

        status_code = response.status_code

        self._logger.debug(
            f"Attempted to fetch WebSocket information fetch from the Sign Server API! <-> "
            f"Status: {status_code} - "
            f"Agent ID: \"{response.headers.get('X-Agent-Id', 'N/A')}\" - "
            f"Log ID: {response.headers.get('X-Request-Id')} - "
            f"Log Code: {response.headers.get('X-Log-Code')} "
            f"<->"
        )

        data: bytes = response.content

        if status_code == 429:
            try:
                data_json = json.loads(data) if data else {}
            except JSONDecodeError:
                data_json = {}
            server_message: Optional[str] = None if os.environ.get('SIGN_SERVER_MESSAGE_DISABLED') else data_json.get("message")
            limit_label: str = f"({data_json['limit_label']}) " if data_json.get("limit_label") else ""

            raise SignatureRateLimitError(
                server_message,
                (
                    f"{limit_label}Too many connections started, try again in %s seconds."
                ),
                response=response
            )

        elif not data:
            raise SignAPIError(
                SignAPIError.ErrorReason.EMPTY_PAYLOAD,
                f"Sign API returned an empty request. Are you being detected by TikTok?",
                response=response
            )

        elif status_code != 200:

            try:
                payload: str = json.dumps(json.loads(data), indent=2)
            except JSONDecodeError:
                payload = f'"{data.decode("utf-8", errors="replace")}"'

            raise SignAPIError(
                SignAPIError.ErrorReason.SIGN_NOT_200,
                f"Failed request to Sign API with status code {status_code} and the following payload:\n{payload}",
                response=response
            )

        # Update web params & cookies
        self._update_client_cookies(response)

        # Package it in a push frame & parse it to maintain parity with the WebcastWebSocket
        return extract_webcast_response_message(
            logger=self._logger,
            push_frame=WebcastPushFrame(
                log_id=-1,
                payload=data,
                payload_type="msg"
            ),
        )

    def _update_client_cookies(self, response: httpx.Response) -> None:
        """
        Update the cookies in the cookie jar from the sign server response

        :param response: The `httpx.Response` to parse for cookies
        :return: None

        """

        jar: SimpleCookie = SimpleCookie()
        cookies_header: Optional[str] = response.headers.get("X-Set-TT-Cookie")

        if not cookies_header:
            raise SignAPIError(
                SignAPIError.ErrorReason.EMPTY_COOKIES,
                "Sign server did not return cookies!",
                response=response
            )

        jar.load(cookies_header)
        for cookie, morsel in jar.items():

            # If it has the cookie, delete the cookie first
            if self._web.cookies.get(cookie):
                self._web.cookies.delete(cookie)

            self._web.cookies.set(cookie, morsel.value, ".tiktok.com")
