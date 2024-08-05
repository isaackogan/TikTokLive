from TikTokLive.client.web.routes import FetchIsLiveRoute
from TikTokLive.client.web.routes.room_id_api import RoomIdAPIRoute
from TikTokLive.client.web.routes.download_video import VideoFetchRoute
from TikTokLive.client.web.routes.gift_list import GiftListRoute
from TikTokLive.client.web.routes.image_download import ImageFetchRoute
from TikTokLive.client.web.routes.room_id_live_html import RoomIdLiveHTMLRoute
from TikTokLive.client.web.routes.room_info import FetchRoomInfoRoomIdRoute
from TikTokLive.client.web.routes.sign_fetch import SignFetchRoute
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

        self.fetch_room_id_from_html: RoomIdLiveHTMLRoute = RoomIdLiveHTMLRoute(self)
        self.fetch_room_id_from_api: RoomIdAPIRoute = RoomIdAPIRoute(self)
        self.fetch_room_info: FetchRoomInfoRoomIdRoute = FetchRoomInfoRoomIdRoute(self)
        self.fetch_gift_list: GiftListRoute = GiftListRoute(self)
        self.fetch_image: ImageFetchRoute = ImageFetchRoute(self)
        self.fetch_video: VideoFetchRoute = VideoFetchRoute(self)
        self.fetch_is_live: FetchIsLiveRoute = FetchIsLiveRoute(self)
        self.fetch_sign_fetch: SignFetchRoute = SignFetchRoute(self, self._sign_api_key)
