"""API Url for euler sign services"""
import os
import re
from typing import Optional, TypedDict

import httpx
from httpx import URL

from TikTokLive.__version__ import PACKAGE_VERSION
from TikTokLive.client.errors import UnexpectedSignatureError, SignatureMissingTokensError, PremiumEndpointError
from TikTokLive.client.web.web_settings import WebDefaults


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

        """

        self._sign_api_key: Optional[str] = sign_api_key or os.environ.get("SIGN_API_KEY") or WebDefaults.tiktok_sign_api_key
        self._sign_api_base: str = sign_api_base or os.environ.get("SIGN_API_URL") or WebDefaults.tiktok_sign_url

        self._httpx: httpx.AsyncClient = httpx.AsyncClient(
            headers={
                "User-Agent": f"TikTokLive.py/{PACKAGE_VERSION}",
                "X-Api-Key": self._sign_api_key or ""
            },
            verify=False
        )

    @property
    def sign_api_key(self) -> Optional[str]:
        """API key for signing requests"""
        return self._sign_api_key

    async def webcast_sign(
            self,
            url: str | URL,
            method: str
    ) -> SignResponse:
        """
        Fetch a signed URL for any /webcast/* route using the Sign Server

        :param url: The URL to sign
        :param method: The HTTP method to sign with
        :return: The signature response

        """

        must_remove_params = [
            "X-Bogus",
            "_signature",
            "msToken",
        ]

        url = str(url)

        for param in must_remove_params:
            url = re.sub(rf"({param}=[^&]*&?)", "", url).rstrip('&').rstrip('?')

        try:
            response: httpx.Response = await self._httpx.post(
                url=f"{self._sign_api_base}/webcast/sign_url/",
                data={
                    "url": url,
                    "method": method
                },
            )
        except Exception as ex:
            raise UnexpectedSignatureError(
                "Failed to sign a request due to an error."
            ) from ex

        try:
            sign_response = response.json()
        except Exception as ex:
            raise UnexpectedSignatureError(
                "Failed to retrieve JSON from a signed request: " + str(response)
            ) from ex

        if sign_response['code'] == 403:
            raise PremiumEndpointError(
                "You do not have permission from the signature provider to sign this URL.",
                api_message=sign_response['message']
            )

        if "msToken" not in sign_response['response']['signedUrl']:
            raise SignatureMissingTokensError(
                "Failed to sign a request due to missing tokens in response!"
            )

        return sign_response
