import os
from http.cookies import SimpleCookie
from typing import Optional

import httpx
from httpx import Response

from TikTokLive.client.errors import SignAPIError, SignatureRateLimitError, AuthenticatedWebSocketConnectionError
from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults, CLIENT_NAME
from TikTokLive.client.ws.ws_utils import extract_webcast_response_message
from TikTokLive.proto import WebcastResponse, WebcastPushFrame


class FetchSignedWebSocketRoute(ClientRoute):
    """
    Call the signature server to receive the TikTok websocket URL

    """

    async def __call__(
            self,
            room_id: Optional[int] = None,
            preferred_agent_id: Optional[int] = None,
            session_id: Optional[str] = None
    ) -> WebcastResponse:
        """
        Call the method to get the first WebcastResponse (as bytes) to use to upgrade to WebSocket & perform the first ack

        :param room_id: Override the room ID to fetch the webcast for
        :param preferred_agent_id: The preferred agent ID to use for the request
        :return: The WebcastResponse forwarded from the sign server proxy, as raw bytes

        """

        extra_headers: dict = {
        }

        extra_params: dict = {
            'client': CLIENT_NAME,
        }

        if room_id is not None:
            extra_params['room_id'] = room_id

        if preferred_agent_id is not None:
            extra_params['preferred_agent_id'] = preferred_agent_id

        # The session ID we want to add to the request
        session_id: str = session_id or self._web.cookies.get('sessionid')

        if self._web.authenticate_websocket and session_id:
            if not os.getenv('WHITELIST_AUTHENTICATED_SESSION_ID_HOST'):
                raise AuthenticatedWebSocketConnectionError(
                    "For your safety, this request has been BLOCKED. To understand why, see the reason below:\n\t"
                    "You set 'authenticate_websocket' to True, which allows your Session ID to be sent to the Sign Server when connecting to TikTok LIVE.\n\t"
                    "This is risky, because a session ID grants a user complete access to your account.\n\t"
                    "You should ONLY enable this setting if you trust the Sign Server. The Euler Stream sign server does NOT store your session ID. Third party servers MAY."
                    "\n\n\t>> THIRD PARTY SIGN SERVERS MAY STEAL YOUR SESSION ID. <<\n\n\t"
                    "It should also be noted that since there are a limited number of sign servers, your session ID will\n\t"
                    "connect to TikTok with the same IP address as other users. This could potentially lead to a ban of the account.\n\t"
                    "With that said, there has never been a case of a ban due to this feature.\n\t"
                    "You are only recommended to use this setting if you are aware of the risks and are willing to take them.\n\t"
                    "If you are sure you want to enable this setting, set the environment variable 'WHITELIST_AUTHENTICATED_SESSION_ID_HOST' to the HOST you want to authorize (e.g. 'tiktok.eulerstream.com').\n\t"
                    "By doing so, you acknowledge the risks and agree to take responsibility for any consequences."
                )

            if os.getenv('WHITELIST_AUTHENTICATED_SESSION_ID_HOST', '') != WebDefaults.tiktok_sign_url.split("://")[1]:
                raise AuthenticatedWebSocketConnectionError(
                    f"The host '{os.getenv('WHITELIST_AUTHENTICATED_SESSION_ID_HOST')}' you set in 'WHITELIST_AUTHENTICATED_SESSION_ID_HOST' does not match the host '{WebDefaults.tiktok_sign_url.split('://')[1]}' of the Sign Server. "
                    f"Please set the correct host in 'WHITELIST_AUTHENTICATED_SESSION_ID_HOST' to authorize the Sign Server."
                )

            extra_params['session_id'] = session_id
            self._logger.warning("Sending session ID to sign server for WebSocket connection. This is a risky operation.")

        # Add the API key if it exists
        if self._web.signer.sign_api_key is not None:
            extra_headers['X-Api-Key'] = self._web.signer.sign_api_key

        try:
            response: httpx.Response = await self._web.get(
                url=WebDefaults.tiktok_sign_url + "/webcast/fetch/",
                extra_headers=extra_headers,
                extra_params=extra_params
            )
        except httpx.ConnectError as ex:
            raise SignAPIError(
                SignAPIError.ErrorReason.CONNECT_ERROR,
                "Failed to connect to the sign server due to an httpx.ConnectError!"
            ) from ex

        self._logger.debug(f"Sign API Fetched from agent {response.headers.get('X-Agent-Id')}: {response.status_code}")
        data: bytes = await response.aread()

        if response.status_code == 429:
            data_json = response.json()
            server_message: Optional[str] = None if os.environ.get('SIGN_SERVER_MESSAGE_DISABLED') else data_json.get("message")
            limit_label: str = f"({data_json['limit_label']}) " if data_json.get("limit_label") else ""

            raise SignatureRateLimitError(
                response.headers.get("RateLimit-Reset"),
                response.headers.get("X-RateLimit-Reset"),
                server_message,
                (
                    f"{limit_label}Too many connections started, try again in %s seconds."
                )

            )

        elif not data:
            raise SignAPIError(
                SignAPIError.ErrorReason.EMPTY_PAYLOAD,
                f"Sign API returned an empty request. Are you being detected by TikTok?"
            )

        elif not response.status_code == 200:
            raise SignAPIError(
                SignAPIError.ErrorReason.SIGN_NOT_200,
                f"Failed request to Sign API with status code {response.status_code} and payload \"{response.read()}\"."
            )

        # Update web params & cookies
        self._update_client_cookies(response)
        response_data: bytes = response.read()

        # Package it in a push frame & parse it to maintain parity with the WebcastWebSocket
        return extract_webcast_response_message(
            logger=self._logger,
            push_frame=WebcastPushFrame(
                log_id=-1,
                payload=response_data,
                payload_type="msg"
            ),
        )

    def _update_client_cookies(self, response: Response) -> None:
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
                "Sign server did not return cookies!"
            )

        jar.load(cookies_header)

        for cookie, morsel in jar.items():
            self._web.cookies.set(cookie, morsel.value, ".tiktok.com")
