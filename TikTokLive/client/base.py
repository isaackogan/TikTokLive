import asyncio
import logging
import sys
import traceback
from asyncio import AbstractEventLoop
from typing import Optional, List, Dict

from dacite import from_dict

from TikTokLive.client.http import TikTokHTTPClient
from TikTokLive.client.proxy import ProxyContainer
from TikTokLive.types import AlreadyConnecting, AlreadyConnected, LiveNotFound, FailedConnection, ExtendedGift
from TikTokLive.utils import validate_and_normalize_unique_id, get_room_id_from_main_page_html


class BaseClient:
    """
    Base client responsible for long polling to the TikTok Webcast API

    """

    def __init__(
            self,
            unique_id: str,
            loop: Optional[AbstractEventLoop] = None,
            client_params: Optional[dict] = None,
            headers: Optional[dict] = None,
            timeout_ms: Optional[int] = None,
            polling_interval_ms: int = 1000,
            process_initial_data: bool = True,
            fetch_room_info_on_connect: bool = True,
            enable_extended_gift_info: bool = True,
            trust_env: bool = False,
            proxy_container: Optional[ProxyContainer] = None,
    ):
        """
        Initialize the base client

        :param unique_id: The unique id of the creator to connect to
        :param loop: Optionally supply your own asyncio loop
        :param client_params: Additional client parameters to include when making requests to the Webcast API
        :param headers: Additional headers to include when making requests to the Webcast API
        :param timeout_ms: The timeout (in ms) for requests made to the Webcast API
        :param polling_interval_ms: The interval between requests made to the Webcast API
        :param process_initial_data: Whether to process the initial data (including cached chats)
        :param fetch_room_info_on_connect: Whether to fetch room info (check if everything is kosher) on connect
        :param enable_extended_gift_info: Whether to retrieve extended gift info including its icon & other important things
        :param trust_env: Whether to trust environment variables that provide proxies to be used in aiohttp requests
        :param proxy_container: A proxy container that allows you to submit an unlimited # of proxies for rotation

        """

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
        self._viewer_count: Optional[int] = None
        self.__connecting: bool = False
        self.__connected: bool = False

        # Protected Attributes
        self._client_params: dict = {**TikTokHTTPClient.DEFAULT_CLIENT_PARAMS, **(client_params if isinstance(client_params, dict) else dict())}
        self._http: TikTokHTTPClient = TikTokHTTPClient(headers if headers is not None else dict(), timeout_ms=timeout_ms, proxy_container=proxy_container, trust_env=trust_env)
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
        self._client_params["cursor"] = _last_cursor if _next_cursor == "0" else _next_cursor

        if is_initial and not self._process_initial_data:
            return

        await self._handle_webcast_messages(webcast_response)

    async def _handle_webcast_messages(self, webcast_response) -> None:
        """
        Handle the parsing of webcast messages, meant to be overridden by superclass

        """

        raise NotImplementedError

    async def _connect(self) -> str:
        """
        Connect to the Websocket API

        :return: The room ID, if connection is successful

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

        except Exception as ex:
            message: str
            tb: str = traceback.format_exc()

            if "SSLCertVerificationError" in tb:
                message = (
                    "Your certificates might be out of date! Navigate to your base interpreter's "
                    "directory and click on (execute) \"Install Certificates.command\".\nThis package is reading the interpreter path as "
                    f"{sys.executable}, but if you are using a venv please navigate to your >> base << interpreter."
                )
            else:
                message = str(ex)

            self.__connecting = False
            raise FailedConnection(message)

    def _disconnect(self) -> None:
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

    async def set_proxies_enabled(self, enabled: bool) -> None:
        """
        Set whether to use proxies in requests

        :param enabled: Whether proxies are enabled or not
        :return: None

        """

        self._http.proxy_container.set_enabled(enabled)

    async def add_proxies(self, *proxies: str) -> None:
        """
        Add proxies to the proxy container for request usage
        
        :param proxies: Proxies for usage
        :return: None
        
        """

        for proxy in proxies:
            self._http.proxy_container.proxies.append(proxy)

    async def remove_proxies(self, *proxies: str) -> None:
        """
        Remove proxies from the proxy container for request usage

        :param proxies: Proxies to remove
        :raises ValueError: Raises ValueError if proxy is not present
        :return: None

        """

        for proxy in proxies:
            self._http.proxy_container.proxies.remove(proxy)

    async def get_proxies(self) -> List[str]:
        """
        Get a list of the current proxies in the proxy container being used for requests

        :return: The proxies in the request container
        """

        return self._http.proxy_container.proxies

    @property
    def viewer_count(self) -> Optional[int]:
        """
        Return viewer count of user

        :return: Viewer count

        """
        return self._viewer_count

    @property
    def room_id(self) -> Optional[int]:
        """
        Room ID if the connection was successful

        :return: Room's ID

        """
        return self.__room_id

    @property
    def room_info(self) -> Optional[dict]:
        """
        Room info dict if the connection was successful

        :return: Room Info Dict

        """

        return self.__room_info

    @property
    def unique_id(self) -> str:
        """
        Unique ID of the streamer

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
        Available gift information for live room

        :return: Gift info

        """

        return self.__available_gifts
