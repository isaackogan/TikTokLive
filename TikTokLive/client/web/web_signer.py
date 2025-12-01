from typing import Optional, Literal
from EulerApiSdk import AuthenticatedClient, Client

from TikTokLive.client.errors import (
    UnexpectedSignatureError,
    SignatureMissingTokensError,
    PremiumEndpointError
)


class TikTokSigner:
    """
    Utility to sign any TikTok request using EulerApiSdk
    """

    def __init__(
        self,
        sign_api_key: Optional[str] = None
    ):
        """
        Initialize signer using EulerApiSdk client
        Only one variable stores API key
        """
        self._sign_api_key = sign_api_key

        # Initialize proper client based on API key
        if self._sign_api_key:
            self.client = AuthenticatedClient(api_key=self._sign_api_key)
        else:
            self.client = Client()

    async def webcast_sign(
        self,
        url: str,
        method: str,
        sign_url_type: Literal["xhr", "fetch"],
        payload: str,
        user_agent: str,
        session_id: Optional[str] = None,
        tt_target_idc: Optional[str] = None
    ):
        """
        Generate signed URL using EulerApiSdk
        """

        # Remove unwanted query params before sending
        for param in ["X-Bogus", "X-Gnarly", "msToken"]:
            url = url.replace(f"{param}=", "").split('&')[0]

        try:
            # Call EulerApiSdk client method
            response = await self.client.web_signer.webcast_sign_url(
                url=url,
                method=method,
                type=sign_url_type,
                payload=payload,
                userAgent=user_agent,
                sessionId=session_id,
                ttTargetIdc=tt_target_idc
            )
        except Exception as ex:
            raise UnexpectedSignatureError(
                "Failed to sign request via EulerApiSdk."
            ) from ex

        # Validate response
        if response.code == 403:
            raise PremiumEndpointError(
                "You do not have permission to sign this URL.",
                api_message=response.message
            )

        if "msToken" not in response.response.signedUrl:
            raise SignatureMissingTokensError(
                "Missing tokens in sign response!"
            )

        return {
            "code": response.code,
            "message": response.message,
            "response": {
                "signedUrl": response.response.signedUrl,
                "userAgent": response.response.userAgent,
                "browserName": response.response.browserName,
                "browserVersion": response.response.browserVersion,
            }
        }

    @property
    def client_instance(self) -> Client:
        """Access to the underlying EulerApiSdk client"""
        return self.client
