from typing import Optional, List

from httpx import Response

from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults


class InvalidFetchIsLiveRequest(RuntimeError):
    """
    Thrown when the request to check if a user is live fails

    """

    pass


class InvalidLiveUser(RuntimeError):
    """
    Thrown when the request to check if a user is live fails because a user has no
    livestream account (e.g. <1000 followers)

    """

    def __init__(self, unique_id: str, *args):
        self.unique_id: str = unique_id
        super().__init__(*args)


class FetchIsLiveRoute(ClientRoute):
    """
    Check if a given user is alive through their unique_id or room_id

    """

    async def __call__(
            self,
            room_id: Optional[str] = None,
            unique_id: Optional[str] = None
    ) -> bool:
        """
        Check whether a given user is live on TikTok.

        :param unique_id: The user's unique_id
        :param room_id: Or, their room_id
        :return: Whether they are live
        :raises: InvalidLiveUser
        :raises: InvalidFetchIsLiveRequest

        """

        if not unique_id and not room_id:
            raise InvalidFetchIsLiveRequest(
                "One of 'unique_id' or 'room_id' must be specified. Both cannot be empty."
            )

        if room_id is not None:
            return (await self.fetch_is_live_room_ids(room_id))[0]

        return await self.fetch_is_live_unique_id(unique_id)

    async def fetch_is_live_room_ids(self, *room_ids: str) -> List[bool]:
        """
        Check whether a list of room_id's are currently live

        :param room_ids: The room_id's to check
        :return: Whether they are alive, in the order they were sent

        """

        response: Response = await self._web.get_response(
            url=WebDefaults.tiktok_webcast_url + f"/room/check_alive/",
            extra_params={"room_ids": ",".join(room_ids)}
        )

        response_json: dict = response.json()
        return [i["alive"] for i in response_json["data"]]

    async def fetch_is_live_unique_id(self, unique_id: str) -> bool:
        """
        Check whether a given user is live

        :param unique_id: The unique_id of the user
        :return: Whether they are live

        :raises: InvalidLiveUser

        """

        response: Response = await self._web.get_response(
            url=WebDefaults.tiktok_app_url + f"/api-live/user/room/",
            extra_params=(
                {
                    "uniqueId": unique_id,
                    "sourceType": 54
                }
            )
        )

        response_json: dict = response.json()

        # Invalid user
        if response_json["message"] == "user_not_found":
            raise InvalidLiveUser(
                unique_id,
                (
                    f"The requested user '{unique_id}' is not capable of going LIVE on TikTok, "
                    "or has never gone live on TikTok, or does not exist."
                )
            )

        return response_json["data"]["liveRoom"]["status"] != 4
