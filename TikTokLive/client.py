import asyncio
import json
import logging
import traceback
from asyncio import AbstractEventLoop
from typing import Optional, List, Type

from dacite import from_dict
from pyee import AsyncIOEventEmitter

from TikTokLive.http import TikTokHTTPClient
from .types import AlreadyConnecting, AlreadyConnected, LiveNotFound, FailedConnection, events
from .types.events import ConnectEvent, DisconnectEvent, ViewerCountUpdateEvent, CommentEvent, UnknownEvent, LiveEndEvent, AbstractEvent, GiftEvent
from .utils import validate_and_normalize_unique_id, get_room_id_from_main_page_html


class TikTokLiveClient(AsyncIOEventEmitter):

    def __init__(self, unique_id: str, loop: AbstractEventLoop = None, **options):
        """
        Create a livestream client

        :param unique_id: Unique ID
        :param loop: Asyncio Event Loop
        :param options: Dict Options

        """

        # Call super
        super().__init__()

        # Event Loop
        self.loop: AbstractEventLoop = self.__get_event_loop() if loop is None else loop

        # Private Attributes
        self.__unique_id: str = validate_and_normalize_unique_id(unique_id)
        self.__discard_extra_events: Optional[bool] = None
        self.__room_info: Optional[dict] = None
        self.__connecting: Optional[bool] = None
        self.__connected: Optional[bool] = None
        self.__available_gifts: List[dict] = []
        self.__room_id: Optional[str] = None
        self.__viewer_count: Optional[int] = None

        # Protected Attributes
        self._client_params: dict = {**TikTokHTTPClient.DEFAULT_CLIENT_PARAMS, **options.get("_client_params", dict())}
        self._options: dict = self.__get_options(**options)
        self._http_client = TikTokHTTPClient(options.get("headers"), timeout_ms=options.get("timeout"))

        # Set unconnected status
        self.__set_unconnected()

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
    def available_gifts(self) -> List[dict]:
        """
        Available gift information
        :return: Gift info

        """

        return self.__available_gifts

    @classmethod
    def __get_event_loop(cls) -> AbstractEventLoop:
        """
        Get asyncio event loop
        :return: Event loop

        """

        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            return asyncio.get_running_loop()

    @classmethod
    def __get_options(cls, **provided_options: dict):
        """
        Build dict of options from defaults & supplied overrides

        :param provided_options: Provided overrides
        :return: Dict containing options

        """

        return (
            {
                **{
                    "process_initial_data": True,
                    "fetch_room_info_on_connect": True,
                    "enable_extended_gift_info": True,
                    "request_polling_interval_ms": 1000,
                    "client_params": {},
                    "request_headers": {}
                },
                **provided_options
            }
        )

    def __set_unconnected(self):
        """
        Set unconnected status
        :return: None

        """

        self.__is_polling_enabled = False
        self.__room_info: Optional[dict] = None
        self.__connecting: Optional[bool] = False
        self.__connected: Optional[bool] = False
        self._client_params["cursor"]: str = ""

    async def __fetch_room_id(self) -> Optional[str]:
        """
        Fetch room ID of a given user

        :return: Their Room ID
        :raises: asyncio.TimeoutError

        """

        try:
            html: str = await self._http_client.get_livestream_page_html(self.__unique_id)
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
            response = await self._http_client.get_json_object_from_webcast_api("room/info/", self._client_params)
            self.__room_info = response
            return self.__room_info
        except:
            logging.error(traceback.format_exc() + "\nFailed to retrieve room info from webcast api")
            return None

    async def __fetch_available_gifts(self) -> Optional[List[dict]]:
        """
        Fetch available gifts from Webcast API
        :return: Gift info dict

        """

        try:
            response = await self._http_client.get_json_object_from_webcast_api("gift/list/", self._client_params)
            self.__available_gifts: List[dict] = response.get("gifts")
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
        polling_interval: int = int(self._options.get("request_polling_interval_ms", 1000) / 1000)

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

        webcast_response = await self._http_client.get_deserialized_object_from_webcast_api("im/fetch/", self._client_params, "WebcastResponse")
        self._client_params["cursor"] = webcast_response.get("cursor")

        if is_initial and not self._options.get("process_initial_data"):
            return

        await self.__handle_webcast_messages(webcast_response)

    async def __handle_webcast_messages(self, webcast_response):
        """
        Handle webcast messages using event emitter
        :param webcast_response:
        :return:

        """

        for message in webcast_response.get("messages", list()):
            response: Optional[AbstractEvent] = self.__parse_message(webcast_message=message)

            if isinstance(response, AbstractEvent):
                self.emit(response.name, response)

    def __parse_message(self, webcast_message: dict) -> Optional[AbstractEvent]:
        event_dict: Optional[dict] = webcast_message.get("event")

        # It's a traditional event
        if event_dict:
            del webcast_message["event"]

            # Bring event details up to main
            for key, value in event_dict["eventDetails"].items():
                webcast_message[key] = value

            schema: Type[AbstractEvent] = events.__events__.get(webcast_message["displayType"])
            if schema is not None:
                # Create event
                event: AbstractEvent = from_dict(schema, webcast_message)
                event._as_dict = webcast_message
                return event

        # Viewer update
        if webcast_message.get("viewerCount"):
            event: ViewerCountUpdateEvent = from_dict(ViewerCountUpdateEvent, webcast_message)
            event._as_dict = webcast_message
            self.__viewer_count = event.viewerCount
            return event

        # Comment
        if webcast_message.get("comment"):
            event: CommentEvent = from_dict(CommentEvent, webcast_message)
            event._as_dict = webcast_message
            return event

        # Live ended
        action: Optional[int] = webcast_message.get("action")
        if action is not None and action == 3:
            self.__set_unconnected()
            return LiveEndEvent()

        # Gift Received
        gift: Optional[str] = webcast_message.get("giftJson")
        if gift:
            del webcast_message["giftJson"]
            webcast_message["gift"] = json.loads(gift)
            event: GiftEvent = from_dict(GiftEvent, webcast_message)
            event._as_dict = webcast_message
            return event

        # We haven't implemented deserialization for it yet, or it doesn't have a model
        event: UnknownEvent = UnknownEvent()
        event._as_dict = webcast_message
        return event

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
            if self._options.get("fetch_room_info_on_connect"):
                await self.__fetch_room_info()

                # If offline
                if self.__room_info.get("status", 4) == 4:
                    raise LiveNotFound()

            # Get extended gift info
            if self._options.get("enable_extended_gift_info"):
                await self.__fetch_available_gifts()

            # Make initial request to Webcast Messaging
            await self.__fetch_room_data(True)
            self.__connected = True

            # Use request polling (Websockets not implemented)
            self.loop.create_task(self.__fetch_room_polling())

            event: ConnectEvent = ConnectEvent()
            self.emit(event.name, event)

            return self.__room_id

        except:
            self.__connecting = False
            raise FailedConnection()

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
            self.__set_unconnected()

            event: DisconnectEvent = DisconnectEvent()
            self.emit(event.name, event)

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

    async def retrieve_available_gifts(self) -> Optional[dict]:
        """
        Retrieve available gifts from Webcast API
        :return: None

        """

        return await self.__fetch_available_gifts()
