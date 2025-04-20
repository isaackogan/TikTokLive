import json
import re
from json import JSONDecodeError
from typing import Optional

from httpx import Response

from TikTokLive.client.errors import TikTokLiveError
from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults


class FailedParseAppInfo(TikTokLiveError):
    """
    Thrown when the App Info cannot be parsed

    """


class FailedResolveUserId(TikTokLiveError):
    """
    Thrown when the User ID cant be resolved

    """


class FetchUserUniqueIdRoute(ClientRoute):
    """
    Route to retrieve the room ID for a user

    """

    APP_INFO_PATTERN: re.Pattern = re.compile(
        r"""<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>""")

    async def __call__(self, user_id: int) -> str:
        """
        Fetch the unique_id for a given User ID from the page HTML

        :param user_id: The user's username
        :return: The unique_id of a User ID

        """

        # Get their User HTML
        response: Response = await self._web.get(
            url=WebDefaults.tiktok_app_url + f"/@{user_id}",
            base_params=False
        )

        return self.parse_app_info(response.text)

    @classmethod
    def parse_app_info(cls, html: str) -> str:
        """
        Parse the room ID from livestream HTML

        :param html: The HTML to parse from https://tiktok.com/@<user_id>
        :return: The unique_id of a User ID

        """

        match: Optional[re.Match[str]] = cls.APP_INFO_PATTERN.search(html)

        if match is None:
            raise FailedParseAppInfo(
                "Failed to extract data __UNIVERSAL_DATA_FOR_REHYDRATION__, you might be blocked by TikTok.")

        try:
            app_info: dict = json.loads(match.group(1))
        except JSONDecodeError:
            raise FailedParseAppInfo("Failed to extract data, you might be blocked by TikTok.")

        try:
            unique_id: str = (
                app_info
                .get('__DEFAULT_SCOPE__', {})
                .get('webapp.user-detail', {})
                .get('userInfo', {})
                .get('user', {})
                .get('uniqueId')
            )

        except Exception:  # Catch errors during key traversal (e.g., AttributeError)
            raise FailedResolveUserId("Failed to parse user data from JSON")

        if unique_id is None:
            raise FailedResolveUserId("Failed to resolve User ID to unique_id")

        return unique_id
