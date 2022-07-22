import asyncio
import logging
import os
import signal
import sys
import traceback
from asyncio import AbstractEventLoop
from datetime import datetime
from threading import Thread
from typing import Optional, List, Dict, Set

from dacite import from_dict
from ffmpy import FFmpeg, FFRuntimeError
from pyee import AsyncIOEventEmitter

from TikTokLive.client import config
from TikTokLive.client.http import TikTokHTTPClient
from TikTokLive.client.websocket import WebcastWebsocket
from TikTokLive.types import AlreadyConnecting, AlreadyConnected, LiveNotFound, FailedConnection, ExtendedGift, InvalidSessionId, ChatMessageSendFailure, ChatMessageRepeat, FailedFetchRoomInfo, FailedFetchGifts, \
    FailedRoomPolling, FFmpegWrapper, AlreadyDownloadingStream, DownloadProcessNotFound, NotDownloadingStream, InitialCursorMissing
from TikTokLive.utils import validate_and_normalize_unique_id, get_room_id_from_main_page_html


class BaseClient(AsyncIOEventEmitter):
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
            ping_interval_ms: int = 1000,
            process_initial_data: bool = True,
            enable_extended_gift_info: bool = True,
            trust_env: bool = False,
            proxies: Optional[Dict[str, str]] = None,
            lang: Optional[str] = "en-US",
            fetch_room_info_on_connect: bool = True,
            websocket_enabled: bool = True,
    ):
        """
        Initialize the base client

        :param unique_id: The unique id of the creator to connect to
        :param loop: Optionally supply your own asyncio loop
        :param client_params: Additional client parameters to include when making requests to the Webcast API
        :param headers: Additional headers to include when making requests to the Webcast API
        :param timeout_ms: The timeout (in ms) for requests made to the Webcast API
        :param ping_interval_ms: The interval between requests made to the Webcast API for both Websockets and Long Polling
        :param process_initial_data: Whether to process the initial data (including cached chats)
        :param enable_extended_gift_info: Whether to retrieve extended gift info including its icon & other important things
        :param trust_env: Whether to trust environment variables that provide proxies to be used in aiohttp requests
        :param proxies: Enable proxied requests by turning on forwarding for the HTTPX "proxies" argument. Websocket connections will NOT be proxied
        :param lang: Change the language. Payloads *will* be in English, but this will change stuff like the extended_gift Gift attribute to the desired language!
        :param fetch_room_info_on_connect: Whether to fetch room info on connect. If disabled, you might attempt to connect to a closed livestream
        :param websocket_enabled: Whether to use websockets or rely on purely long polling

        """
        AsyncIOEventEmitter.__init__(self)

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
        self.__session_id: Optional[str] = None
        self.__is_ws_upgrade_done: bool = False
        self.__websocket_enabled: bool = websocket_enabled

        # Change Language
        config.DEFAULT_CLIENT_PARAMS["app_language"] = lang
        config.DEFAULT_CLIENT_PARAMS["webcast_language"] = lang

        # Protected Attributes

        self._http: TikTokHTTPClient = TikTokHTTPClient(
            headers=headers if headers is not None else dict(),
            timeout_ms=timeout_ms,
            proxies=proxies,
            trust_env=trust_env,
            params={**config.DEFAULT_CLIENT_PARAMS, **(client_params if isinstance(client_params, dict) else dict())}
        )
        self._polling_interval_ms: int = ping_interval_ms
        self._process_initial_data: bool = process_initial_data
        self._enable_extended_gift_info: bool = enable_extended_gift_info
        self._fetch_room_info_on_connect: bool = fetch_room_info_on_connect
        self._download: Optional[FFmpegWrapper] = None
        self._socket: Optional[WebcastWebsocket] = None

        # Listeners
        self.add_listener("websocket", self._handle_webcast_messages)

    async def _on_error(self, original: Exception, append: Optional[Exception]) -> None:
        """
        Send errors to the _on_error handler for handling, appends a custom exception

        :param original: The original Python exception
        :param append: The specific exception
        :return: None

        """

        raise NotImplementedError()

    async def __fetch_room_id(self) -> Optional[str]:
        """
        Fetch room ID of a given user

        :return: Their Room ID
        :raises: asyncio.TimeoutError

        """

        try:
            html: str = await self._http.get_livestream_page_html(self.__unique_id)
            self.__room_id = get_room_id_from_main_page_html(html)
            self._http.params["room_id"] = self.__room_id
            return self.__room_id
        except Exception as ex:
            await self._on_error(ex, FailedFetchRoomInfo("Failed to fetch room id from Webcast, see stacktrace for more info."))
            return None

    async def __fetch_room_info(self) -> Optional[dict]:
        """
        Fetch room information from Webcast API

        :return: Room info dict

        """

        try:
            response = await self._http.get_json_object_from_webcast_api("room/info/", self._http.params)
            self.__room_info = response
            return self.__room_info
        except Exception as ex:
            await self._on_error(ex, FailedFetchRoomInfo("Failed to fetch room info from Webcast, see stacktrace for more info."))
            return None

    async def __fetch_available_gifts(self) -> Optional[Dict[int, ExtendedGift]]:
        """
        Fetch available gifts from Webcast API

        :return: Gift info dict

        """

        try:
            response = await self._http.get_json_object_from_webcast_api("gift/list/", self._http.params)
            gifts: Optional[List] = response.get("gifts")

            if isinstance(gifts, list):
                for gift in gifts:
                    try:
                        _gift: ExtendedGift = from_dict(ExtendedGift, gift)
                        self.__available_gifts[_gift.id] = _gift
                    except:
                        logging.error(traceback.format_exc() + "\nFailed to parse gift's extra info")

            return self.__available_gifts
        except Exception as ex:
            await self._on_error(ex, FailedFetchGifts("Failed to fetch gift data from Webcast, see stacktrace for more info."))
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
            except Exception as ex:
                await self._on_error(ex, FailedRoomPolling("Failed to retrieve events from Webcast, see stacktrace for more info."))

            await asyncio.sleep(polling_interval)

    async def __fetch_room_data(self, is_initial: bool = False) -> None:
        """
        Fetch room data from the Webcast API and deserialize it

        :param is_initial: Is it the initial request to the API
        :return: None

        """

        # Fetch from polling api
        webcast_response = await self._http.get_deserialized_object_from_webcast_api("im/fetch/", self._http.params, "WebcastResponse", is_initial)
        _last_cursor, _next_cursor = self._http.params["cursor"], webcast_response.get("cursor")
        self._http.params["cursor"] = _last_cursor if _next_cursor == "0" else _next_cursor

        # Add param if given
        if webcast_response.get("internalExt"):
            self._http.params["internal_ext"] = webcast_response["internalExt"]

        if is_initial:
            if not webcast_response.get("cursor"):
                raise InitialCursorMissing("Missing cursor in initial fetch response.")

            # If a WebSocket is offered, upgrade
            if bool(webcast_response.get("wsUrl")) and bool(webcast_response.get("wsParam")) and self.__websocket_enabled:
                await self.__try_websocket_upgrade(webcast_response)

            # Process initial data if requested
            if not self._process_initial_data:
                return

        await self._handle_webcast_messages(webcast_response)

    async def __try_websocket_upgrade(self, webcast_response) -> WebcastWebsocket:
        """
        Attempt to upgrade the connection to a websocket instead

        :param webcast_response: The initial webcast response including the wsParam and wsUrl items
        :return: The websocket, if one is produced

        """

        socket: WebcastWebsocket = WebcastWebsocket(
            client=self,
            ws_url=webcast_response.get("wsUrl"),
            cookies=self._http.client.cookies,
            client_params=self._http.params,
            ws_params={"imprp": webcast_response.get("wsParam").get("value")},
            headers=self._http.headers,
            loop=self.loop,
            ping_interval_ms=self._polling_interval_ms
        )

        self.__is_ws_upgrade_done = await socket.connect()
        self._socket = socket if self.__is_ws_upgrade_done else None
        return self._socket

    async def _handle_webcast_messages(self, webcast_response) -> None:
        """
        Handle the parsing of webcast messages, meant to be overridden by superclass

        """

        raise NotImplementedError

    async def _connect(self, session_id: str = None) -> str:
        """
        Connect to the WebcastWebsocket API

        :return: The room ID, if connection is successful

        """
        self.__set_session_id(session_id)

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
                    raise LiveNotFound("The requested user is most likely offline.")

            # Get extended gift info
            if self._enable_extended_gift_info:
                await self.__fetch_available_gifts()

            # Make initial request to Webcast Messaging
            await self.__fetch_room_data(True)
            self.__connected = True

            # If the websocket was not connected for whatever reason
            if not self.__is_ws_upgrade_done:
                # Switch to long polling if a session id was provided
                if self._http.client.cookies.get("sessionid"):
                    self.loop.create_task(self.__fetch_room_polling())

                else:
                    # No more options, fail to connect
                    raise FailedRoomPolling(
                        ("You have disabled websockets, but not included a sessionid for long polling. " if not self.__websocket_enabled else "")
                        + "Long polling is not available: Try adding a sessionid as an argument in start() or run()"
                    )

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
            await self._on_error(ex, FailedConnection(message))

    def _disconnect(self) -> None:
        """
        Set unconnected status

        :return: None

        """

        self.__is_polling_enabled = False
        self.__room_info: Optional[dict] = None
        self.__connecting: Optional[bool] = False
        self.__connected: Optional[bool] = False
        self._http.params["cursor"]: str = ""

    async def stop(self) -> None:
        """
        Stop the client safely

        :return: None

        """

        if self.__connected:
            self._disconnect()
            return

    async def start(self, session_id: Optional[str] = None) -> Optional[str]:
        """
        Start the client without blocking the main thread

        :return: Room ID that was connected to

        """

        return await self._connect(session_id=session_id)

    def run(self, session_id: Optional[str] = None) -> None:
        """
        Run client while blocking main thread

        :return: None

        """

        self.loop.run_until_complete(self._connect(session_id=session_id))
        self.loop.run_forever()

    def __set_session_id(self, session_id: Optional[str]) -> None:
        """
        Set the Session ID for authenticated requests

        :param session_id: New session ID
        :return: None

        """

        if session_id:
            self.__session_id = session_id
            self._http.client.cookies.set("sessionid", session_id)

    async def send_message(self, text: str, session_id: Optional[str] = None) -> Optional[str]:
        """
        Send a message to the TikTok Live Chat

        :param text: The message you want to send to the chat
        :param session_id: The Session ID (If you've already supplied one, you don't need to)
        :return: The response from the webcast API

        """

        self.__set_session_id(session_id)

        if not self.__session_id:
            raise InvalidSessionId("Missing Session ID. Please provide your current Session ID to use this feature.")

        params: dict = {**self._http.params, "content": text}
        response: dict = await self._http.post_json_to_webcast_api("room/chat/", params, None, sign_url=False)
        status_code: Optional[int] = response.get("status_code")
        data: Optional[dict] = response.get("data")

        if status_code == 0:
            return data

        try:
            raise {
                20003: InvalidSessionId("Your Session ID has expired. Please provide a new one"),
                50007: ChatMessageRepeat("You cannot send repeated chat messages!")
            }.get(
                status_code, ChatMessageSendFailure(f"TikTok responded with status code {status_code}: {data.get('message')}")
            )
        except Exception as ex:
            await self._on_error(ex, None)

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

    async def set_proxies(self, proxies: Optional[Dict[str, str]]) -> None:
        """
        Set the proxies to be used by the HTTP client (Not Websockets)

        :param proxies: The proxies to use in HTTP requests
        :return: None

        """

        self._http.proxies = proxies

    async def get_proxies(self) -> Optional[Dict[str, str]]:
        """
        Get the current proxies being used in HTTP requests

        :return: The current proxies in use

        """

        return self._http.proxies

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

    def download(
            self,
            path: str,
            duration: Optional[int] = None,
            verbose: bool = True,
            loglevel: str = "error",
            global_options: Set[str] = set(),
            inputs: Dict[str, str] = dict(),
            outputs: Dict[str, str] = dict()
    ) -> None:
        """
        Start downloading the user's livestream video for a given duration, NON-BLOCKING via Python Threading

        :param loglevel: Set the FFmpeg log level
        :param outputs: Pass custom params to FFmpeg outputs
        :param inputs: Pass custom params to FFmpeg inputs
        :param global_options: Pass custom params to FFmpeg global options
        :param path: The path to download the livestream video to
        :param duration: If duration is None or less than 1, download will go forever
        :param verbose: Whether to log info about the download in console

        :return: None
        :raises: AlreadyDownloadingStream if already downloading and attempting to start a second download

        """

        # If already downloading stream at the moment
        if self._download is not None:
            raise AlreadyDownloadingStream()

        # Set a runtime
        runtime: Optional[str] = None
        if duration is not None and duration >= 1:
            runtime = f"-t {duration}"

        # Function Running
        def spool():
            try:
                self._download.ffmpeg.run()
            except FFRuntimeError as ex:
                if ex.exit_code and ex.exit_code != 255:
                    self._download = None
                    raise
            self._download = None

        # Create an FFmpeg wrapper
        self._download = FFmpegWrapper(
            ffmpeg=FFmpeg(
                inputs={**{self.room_info["stream_url"]["hls_pull_url"]: None}, **inputs},
                outputs={**{path: runtime}, **outputs},
                global_options={"-y", f"-loglevel {loglevel}"}.union(global_options)
            ),
            thread=Thread(target=spool),
            verbose=verbose,
            path=path,
            runtime=runtime
        )

        # Start the download
        self._download.thread.start()
        self._download.started_at = int(datetime.utcnow().timestamp())

        # Give info about the started download
        if self._download.verbose:
            logging.warning(f"Started the download to path \"{path}\" for duration \"{'infinite' if runtime is None else duration} seconds\" on user @{self.unique_id}")

    def stop_download(self) -> None:
        """
        Stop downloading a livestream if currently downloading

        :return: None
        :raises NotDownloadingStream: Raised if trying to stop when not downloading and
        :raises DownloadProcessNotFound: Raised if stopping before the ffmpeg process has opened

        """

        # If attempting to stop a download when none is occurring
        if self._download is None:
            raise NotDownloadingStream("Not currently downloading the stream!")

        # If attempting to stop a download before the process has opened
        if self._download.ffmpeg.process is None:
            raise DownloadProcessNotFound("Download process not found. You are likely stopping the download before the ffmpeg process has opened. Add a delay!")

        # Kill the process
        os.kill(self._download.ffmpeg.process.pid, signal.CTRL_BREAK_EVENT)

        # Give info about the final product
        if self._download.verbose:
            logging.warning(
                f"Stopped the download to path \"{self._download.path}\" on user @{self.unique_id} after "
                f"\"{int(datetime.utcnow().timestamp()) - self._download.started_at} seconds\" of downloading"
            )
