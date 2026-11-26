import os

from IgniteLiveAPI.client.logger import IgniteLiveLogHandler
from IgniteLiveAPI.client.web.routes import FetchIsLiveRoute
from IgniteLiveAPI.client.web.routes.fetch_gift_list import FetchGifListRoute
from IgniteLiveAPI.client.web.routes.fetch_image_data import FetchImageDataRoute
from IgniteLiveAPI.client.web.routes.fetch_room_id_api import FetchRoomIdAPIRoute
from IgniteLiveAPI.client.web.routes.fetch_room_id_live_html import FetchRoomIdLiveHTMLRoute
from IgniteLiveAPI.client.web.routes.fetch_room_info import FetchRoomInfoRoute
from IgniteLiveAPI.client.web.routes.fetch_signed_websocket import FetchSignedWebSocketRoute
from IgniteLiveAPI.client.web.routes.fetch_user_unique_id import FetchUserUniqueIdRoute
from IgniteLiveAPI.client.web.routes.fetch_video_data import FetchVideoDataRoute
from IgniteLiveAPI.client.web.routes.send_room_chat import SendRoomChatRoute
from IgniteLiveAPI.client.web.web_base import TikTokHTTPClient

SEND_DEPRECATION_WARNINGS = os.environ.get('SEND_DEPRECATION_WARNINGS', 'true').lower() == 'true'


class TikTokWebClient(TikTokHTTPClient):
    """
    Wrapper for the HTTP client to add web routes

    """

    def __init__(self, **kwargs):
        """
        Create a web client with registered TikTok routes

        :param kwargs: Arguments to pass to the super-class

        """

        super().__init__(**kwargs)

        self.fetch_room_id_from_html: FetchRoomIdLiveHTMLRoute = FetchRoomIdLiveHTMLRoute(self)
        self.fetch_room_id_from_api: FetchRoomIdAPIRoute = FetchRoomIdAPIRoute(self)
        self.fetch_room_info: FetchRoomInfoRoute = FetchRoomInfoRoute(self)
        self.fetch_gift_list: FetchGifListRoute = FetchGifListRoute(self)
        self.fetch_image_data: FetchImageDataRoute = FetchImageDataRoute(self)
        self.fetch_video_data: FetchVideoDataRoute = FetchVideoDataRoute(self)
        self.fetch_is_live: FetchIsLiveRoute = FetchIsLiveRoute(self)
        self.fetch_signed_websocket: FetchSignedWebSocketRoute = FetchSignedWebSocketRoute(self)
        self.send_room_chat: SendRoomChatRoute = SendRoomChatRoute(self)
        self.fetch_user_unique_id: FetchUserUniqueIdRoute = FetchUserUniqueIdRoute(self)

        self._logger = IgniteLiveLogHandler.get_logger()

    @property
    def fetch_video(self) -> FetchVideoDataRoute:
        """
        Return the video data route

        :return: The video data route

        """

        if SEND_DEPRECATION_WARNINGS:
            self._logger.warning(
                "The 'fetch_video' attribute is deprecated and will be removed in a future release. "
                "Please use 'fetch_video_data' instead."
            )

        return self.fetch_video_data

    @property
    def fetch_image(self) -> FetchImageDataRoute:
        """
        Return the image data route

        :return: The image data route

        """

        if SEND_DEPRECATION_WARNINGS:
            self._logger.warning(
                "The 'fetch_image' attribute is deprecated and will be removed in a future release. "
                "Please use 'fetch_image_data' instead."
            )

        return self.fetch_image_data
