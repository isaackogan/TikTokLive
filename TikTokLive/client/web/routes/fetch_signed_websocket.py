import os
from http.cookies import SimpleCookie
from typing import Optional

import httpx
from httpx import Response

from TikTokLive.client.errors import SignAPIError, SignatureRateLimitError
from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults, CLIENT_NAME
from TikTokLive.proto import WebcastResponse


class FetchSignedWebSocketRoute(ClientRoute):
    """
    Call the signature server to receive the TikTok websocket URL

    """

    async def __call__(
            self,
            room_id: Optional[int] = None
    ) -> WebcastResponse:
        """
        Call the method to get the first WebcastResponse to use to upgrade to websocket

        :return: The WebcastResponse forwarded from the sign server proxy

        """

        extra_headers: dict = {}
        extra_params: dict = {'client': CLIENT_NAME}

        if room_id is not None:
            extra_params['room_id'] = room_id

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

        webcast_response: WebcastResponse = WebcastResponse().parse(response.read())

        # Update web params & cookies
        self._update_client_cookies(response)
        return webcast_response

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
