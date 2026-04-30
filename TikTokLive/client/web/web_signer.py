"""API Url for euler sign services"""
import os
import re
from typing import Optional, TypedDict, Literal

import httpx
from httpx import URL

from EulerApiSdk import AuthenticatedClient, Client
from EulerApiSdk.api.tik_tok_live import sign_webcast_url
from EulerApiSdk.models.sign_tik_tok_url_body import SignTikTokUrlBody
from EulerApiSdk.models.sign_tik_tok_url_body_method import SignTikTokUrlBodyMethod
from EulerApiSdk.models.sign_tik_tok_url_body_type import SignTikTokUrlBodyType
from EulerApiSdk.models.sign_tik_tok_url_response import SignTikTokUrlResponse
from EulerApiSdk.types import UNSET

from TikTokLive.__version__ import PACKAGE_VERSION
from TikTokLive.client.errors import UnexpectedSignatureError, SignatureMissingTokensError, PremiumEndpointError
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.client.web.web_utils import check_authenticated_session


class SignData(TypedDict):
    """
    Data for signed URLs

    """

    signedUrl: str
    userAgent: str
    browserName: str
    browserVersion: str


class SignResponse(TypedDict):
    """
    Response wrapper from signature server

    """

    code: int
    message: str
    response: Optional[SignData]


class TikTokSigner:
    """
    Utility to sign any TikTok request using Euler Stream

    """

    def __init__(
            self,
            sign_api_key: Optional[str] = None,
            sign_api_base: Optional[str] = None
    ):
        """
        Initialize the signing class

        :param sign_api_key: API key for signing requests
        :param sign_api_base: Base URL for the signing API

        """

        api_key = sign_api_key or os.environ.get("SIGN_API_KEY") or WebDefaults.tiktok_sign_api_key
        self._base_url = sign_api_base or os.environ.get("SIGN_API_URL") or WebDefaults.tiktok_sign_url

        headers = {"User-Agent": f"TikTokLive.py/{PACKAGE_VERSION}"}

        if api_key:
            self._sdk_client: AuthenticatedClient | Client = AuthenticatedClient(
                base_url=self._base_url,
                token=api_key,
                prefix="",
                auth_header_name="X-Api-Key",
                headers=headers,
                verify_ssl=False,
            )
        else:
            self._sdk_client = Client(
                base_url=self._base_url,
                headers=headers,
                verify_ssl=False,
            )

    @property
    def sign_api_key(self) -> Optional[str]:
        """API key for signing requests"""
        if isinstance(self._sdk_client, AuthenticatedClient):
            return self._sdk_client.token
        return None

    async def webcast_sign(
            self,
            url: str | URL,
            method: str,
            sign_url_type: Literal["xhr", "fetch"],
            payload: str,
            user_agent: str,
            session_id: Optional[str] = None,
            tt_target_idc: Optional[str] = None,
    ) -> SignResponse:
        """
        Fetch a signed URL for any /webcast/* route using the Sign Server

        :param url: The URL to sign
        :param sign_url_type: The type of signing to use
        :param session_id: The session ID to use for signing
        :param payload: The payload to send with the request
        :param tt_target_idc: The target IDC to use for signing
        :param method: The HTTP method to sign with
        :param user_agent: The user agent to use for signing
        :return: The signature response

        """

        must_remove_params = [
            "X-Bogus",
            "X-Gnarly",
            "msToken",
        ]

        url = str(url)

        for param in must_remove_params:
            url = re.sub(rf"({param}=[^&]*&?)", "", url).rstrip('&').rstrip('?')

        try:
            body = SignTikTokUrlBody(
                url=url,
                user_agent=user_agent,
                method=SignTikTokUrlBodyMethod(method.upper()),
                type_=SignTikTokUrlBodyType(sign_url_type),
                payload=payload if payload else UNSET,
            )

            # Authenticated signature
            if session_id:
                check_authenticated_session(session_id, tt_target_idc, session_required=False)
                body.session_id = session_id
                body.tt_target_idc = tt_target_idc if tt_target_idc else UNSET

            resp = await sign_webcast_url.asyncio_detailed(
                client=self._sdk_client,
                body=body,
            )

        except Exception as ex:
            raise UnexpectedSignatureError(
                "Failed to sign a request due to an error."
            ) from ex

        # Reconstruct httpx.Response for error handlers expecting response.request
        err_response = httpx.Response(
            status_code=resp.status_code.value,
            content=resp.content,
            headers=dict(resp.headers),
            request=httpx.Request("POST", f"{self._base_url}/webcast/sign_url"),
        )

        if resp.parsed is None:
            raise UnexpectedSignatureError(
                "Failed to parse response from signing request.",
                response=err_response
            )

        parsed = resp.parsed
        code = int(parsed.code) if isinstance(parsed, SignTikTokUrlResponse) else parsed.code
        message = "" if parsed.message is UNSET else parsed.message

        # Check body code first (API returns 200 with code=403 for premium errors)
        if code == 403:
            raise PremiumEndpointError(
                "You do not have permission from the signature provider to sign this URL.",
                api_message=message or "",
                response=err_response
            )

        # Then check HTTP status
        if resp.status_code.value == 403:
            raise PremiumEndpointError(
                "You do not have permission from the signature provider to sign this URL.",
                api_message=message or "",
                response=err_response
            )

        if resp.status_code.value != 200:
            raise UnexpectedSignatureError(
                f"Sign API returned status code {resp.status_code.value}: {resp.content.decode('utf-8', errors='replace')}",
                response=err_response
            )

        result: SignResponse = {
            "code": code,
            "message": message or "",
            "response": None
        }

        if isinstance(parsed, SignTikTokUrlResponse) and parsed.response is not UNSET:
            r = parsed.response
            result["response"] = {
                "signedUrl": "" if r.signed_url is UNSET else r.signed_url,
                "userAgent": "" if r.user_agent is UNSET else r.user_agent,
                "browserName": "" if r.browser_name is UNSET else r.browser_name,
                "browserVersion": "" if r.browser_version is UNSET else r.browser_version,
            }

        if result["response"] is None or "msToken" not in result["response"]["signedUrl"]:
            raise SignatureMissingTokensError(
                "Failed to sign a request due to missing tokens in response!",
                response=err_response
            )

        return result

    @property
    def sdk_client(self) -> AuthenticatedClient | Client:
        """The SDK client used to sign requests"""
        return self._sdk_client

    @property
    def client(self):
        """The httpx client used to sign requests"""
        return self._sdk_client.get_async_httpx_client()
