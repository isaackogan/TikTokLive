from TikTokLive.client.web.routes import FetchIsLiveRoute
from TikTokLive.client.web.routes.fetch_video import VideoFetchRoute
from TikTokLive.client.web.routes.fetch_gift_list import GiftListRoute
from TikTokLive.client.web.routes.fetch_image import ImageFetchRoute
from TikTokLive.client.web.routes.fetch_room_id import RoomIdRoute
from TikTokLive.client.web.routes.fetch_room_info import FetchRoomInfoRoute
from TikTokLive.client.web.routes.fetch_sign import SignFetchRoute
from TikTokLive.client.web.web_base import TikTokHTTPClient


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

        self.fetch_room_id: RoomIdRoute = RoomIdRoute(self)
        self.fetch_room_info: FetchRoomInfoRoute = FetchRoomInfoRoute(self)
        self.fetch_gift_list: GiftListRoute = GiftListRoute(self)
        self.fetch_image: ImageFetchRoute = ImageFetchRoute(self)
        self.fetch_video: VideoFetchRoute = VideoFetchRoute(self)
        self.fetch_is_live: FetchIsLiveRoute = FetchIsLiveRoute(self)
        self.fetch_sign_fetch: SignFetchRoute = SignFetchRoute(self, self._sign_api_key)
