import asyncio
import logging
import traceback
from asyncio import AbstractEventLoop
from typing import Optional, List, Dict

from dacite import from_dict

from TikTokLive.client.http import TikTokHTTPClient
from TikTokLive.types import AlreadyConnecting, AlreadyConnected, LiveNotFound, FailedConnection, ExtendedGift
from TikTokLive.utils import validate_and_normalize_unique_id, get_room_id_from_main_page_html


class BaseClient:

    def __init__(
            self,
            unique_id: str,
            loop: Optional[AbstractEventLoop] = None,
            client_params: Optional[dict] = None,
            headers: Optional[dict] = None,
            timeout_ms: int = 0,
            polling_interval_ms: int = 1000,
            process_initial_data: bool = True,
            fetch_room_info_on_connect: bool = True,
            enable_extended_gift_info: bool = True
    ):
        # Get Event Loop
        if isinstance(loop, AbstractEventLoop):
            self.loop: AbstractEventLoop = loop
        else:
            try:
                self.loop: AbstractEventLoop = asyncio.get_event_loop()
            except RuntimeError:
                self.loop: AbstractEventLoop = asyncio.get_running_loop()

        # Private Attributes
        self.__unique_id: str = validate_and_normalize_unique_id(unique_id)
        self.__discard_extra_events: Optional[bool] = None
        self.__room_info: Optional[dict] = None
        self.__available_gifts: Dict[int, ExtendedGift] = dict()
        self.__room_id: Optional[str] = None
        self.__viewer_count: Optional[int] = None
        self.__connecting: bool = False
        self.__connected: bool = False

        # Protected Attributes
        self._client_params: dict = {**TikTokHTTPClient.DEFAULT_CLIENT_PARAMS, **(client_params if isinstance(client_params, dict) else dict())}
        self._http: TikTokHTTPClient = TikTokHTTPClient(headers if headers is not None else dict(), timeout_ms=timeout_ms)
        self._polling_interval_ms: int = polling_interval_ms
        self._process_initial_data: bool = process_initial_data
        self._fetch_room_info_on_connect: bool = fetch_room_info_on_connect
        self._enable_extended_gift_info: bool = enable_extended_gift_info

    async def __fetch_room_id(self) -> Optional[str]:
        """
        Fetch room ID of a given user

        :return: Their Room ID
        :raises: asyncio.TimeoutError

        """

        try:
            html: str = await self._http.get_livestream_page_html(self.__unique_id)
            self.__room_id = get_room_id_from_main_page_html(html)
            self._client_params["room_id"] = self.__room_id
            return self.__room_id
        except:
            logging.error(traceback.format_exc() + "\nFailed to retrieve room id from page source")
            return None

    async def __fetch_room_info(self) -> Optional[dict]:
        """
        Fetch room information from Webcast API
        :return: Room info dict

        """

        try:
            response = await self._http.get_json_object_from_webcast_api("room/info/", self._client_params)
            self.__room_info = response
            return self.__room_info
        except:
            logging.error(traceback.format_exc() + "\nFailed to retrieve room info from webcast api")
            return None

    async def __fetch_available_gifts(self) -> Optional[Dict[int, ExtendedGift]]:
        """
        Fetch available gifts from Webcast API
        :return: Gift info dict

        """

        try:
            response = await self._http.get_json_object_from_webcast_api("gift/list/", self._client_params)
            gifts: Optional[List] = response.get("gifts")

            if isinstance(gifts, list):
                for gift in gifts:
                    try:
                        _gift: ExtendedGift = from_dict(ExtendedGift, gift)
                        self.__available_gifts[_gift.id] = _gift
                    except:
                        logging.error(traceback.format_exc() + "\nFailed to parse gift's extra info")

            return self.__available_gifts
        except:
            logging.error(traceback.format_exc() + "\nFailed to retrieve gifts from webcast api")
            return None

    async def __fetch_room_polling(self) -> None:
        """
        Main loop containing polling for the client
        :return: None

        """

        self.__is_polling_enabled = True
        polling_interval: int = int(self._polling_interval_ms / 1000)

        while self.__is_polling_enabled:
            try:
                await self.__fetch_room_data()
            except:
                logging.error(traceback.format_exc() + "\nError while fetching room data")

            await asyncio.sleep(polling_interval)

    async def __fetch_room_data(self, is_initial: bool = False) -> None:
        """
        Fetch room data from the Webcast API and deserialize it
        :param is_initial: Is it the initial request to the API
        :return: None

        """

        webcast_response = await self._http.get_deserialized_object_from_webcast_api("im/fetch/", self._client_params, "WebcastResponse")
        _last_cursor, _next_cursor = self._client_params["cursor"], webcast_response.get("cursor")

        # Handle invalid cursor value
        self._client_params["cursor"] = _last_cursor if _next_cursor == "0" else _next_cursor
        await self._handle_webcast_messages(webcast_response)

    async def _handle_webcast_messages(self, webcast_response):
        """
        Handle the parsing of webcast messages

        """

        return

    async def _connect(self) -> str:
        """
        Connect to the Websocket API
        :return:
        """

        if self.__connecting:
            raise AlreadyConnecting()

        if self.__connected:
            raise AlreadyConnected()

        self.__connecting = True

        try:
            await self.__fetch_room_id()

            # Fetch room info when connecting
            if self._fetch_room_info_on_connect:
                await self.__fetch_room_info()

                # If offline
                if self.__room_info.get("status", 4) == 4:
                    raise LiveNotFound()

            # Get extended gift info
            if self._enable_extended_gift_info:
                await self.__fetch_available_gifts()

            # Make initial request to Webcast Messaging
            await self.__fetch_room_data(True)
            self.__connected = True

            # Use request polling (Websockets not implemented)
            self.loop.create_task(self.__fetch_room_polling())

            return self.__room_id

        except:
            self.__connecting = False
            raise FailedConnection()

    def _disconnect(self):
        """
        Set unconnected status
        :return: None

        """

        self.__is_polling_enabled = False
        self.__room_info: Optional[dict] = None
        self.__connecting: Optional[bool] = False
        self.__connected: Optional[bool] = False
        self._client_params["cursor"]: str = ""

    async def start(self) -> Optional[str]:
        """
        Start the client without blocking the main thread
        :return: Room ID that was connected to

        """

        return await self._connect()

    async def stop(self) -> None:
        """
        Stop the client
        :return: None

        """

        if self.__connected:
            self._disconnect()
            return

    def run(self) -> None:
        """
        Run client while blocking main thread
        :return: None

        """

        self.loop.run_until_complete(self._connect())
        self.loop.run_forever()

    async def retrieve_room_info(self) -> Optional[dict]:
        """
        Method to retrieve room information
        :return: Dictionary containing all room info

        """

        # If not connected yet, get their room id
        if not self.__connected:
            await self.__fetch_room_id()

        # Fetch their info & return it
        return await self.__fetch_room_info()

    async def retrieve_available_gifts(self) -> Optional[Dict[int, ExtendedGift]]:
        """
        Retrieve available gifts from Webcast API
        :return: None

        """

        return await self.__fetch_available_gifts()

    @property
    def viewer_count(self) -> Optional[int]:
        """
        Return viewer count of user
        :return: Viewer count

        """
        return self.__viewer_count

    @property
    def room_id(self) -> Optional[int]:
        """
        Room ID if connection successful
        :return: Room's ID

        """
        return self.__room_id

    @property
    def room_info(self) -> Optional[dict]:
        """
        Room info dict if connection successful
        :return: Room Info Dict

        """

        return self.__room_info

    @property
    def unique_id(self) -> str:
        """
        Unique ID of creator
        :return: Their unique ID

        """

        return self.__unique_id

    @property
    def connected(self) -> bool:
        """
        Whether the client is connected
        :return: Result

        """

        return self.__connected

    @property
    def available_gifts(self) -> Dict[int, ExtendedGift]:
        """
        Available gift information
        :return: Gift info

        """

        return self.__available_gifts
