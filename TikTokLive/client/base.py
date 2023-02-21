import asyncio
import json
import logging
import os
import signal
from asyncio import AbstractEventLoop, Task
from datetime import datetime
from threading import Thread
from typing import Optional, List, Dict, Set, Union

import websockets
from ffmpy import FFmpeg, FFRuntimeError

from TikTokLive.client import config, wsclient
from TikTokLive.client.httpx import TikTokHTTPClient
from TikTokLive.client.wsclient import WebcastWebsocketConnection, WebcastConnect
from TikTokLive.types import AlreadyConnecting, AlreadyConnected, LiveNotFound, \
    FailedFetchRoomInfo, FailedFetchGifts, \
    FFmpegWrapper, AlreadyDownloadingStream, DownloadProcessNotFound, NotDownloadingStream, \
    InitialCursorMissing, VideoQuality, WebsocketConnectionFailed, GiftDetailed, FailedParseGift
from TikTokLive.utilities import validate_and_normalize_unique_id, get_room_id_from_main_page_html


class WebcastPushConnection:
    """
    Base client responsible for long polling to the TikTok Webcast API

    """

    def __init__(
            self,
            unique_id: str,
            loop: Optional[AbstractEventLoop] = None,
            http_params: Optional[dict] = None,
            http_headers: Optional[dict] = None,
            http_timeout: float = 10.0,
            ws_timeout: float = 10.0,
            ws_ping_interval: float = 10.0,
            ws_headers: Optional[dict] = None,
            process_initial_data: bool = True,
            enable_detailed_gifts: bool = False,
            trust_env: bool = False,
            proxies: Optional[Dict[str, str]] = None,
            lang: Optional[str] = "en-US",
            fetch_room_info_on_connect: bool = True,
            sign_api_key: Optional[str] = None
    ):
        """
        Initialize the base client

        :param unique_id: The unique id of the creator to connect to.
        :param loop: Optionally supply your own asyncio loop.
        :param http_params: Additional HTTP client parameters to include when making requests to the Webcast API AND connecting to the websocket server.
        :param http_timeout: How long to wait before considering an HTTP request in the http client timed out.
        :param http_headers: Additional HTTP client headers to include when making requests to the Webcast API AND connecting to the websocket server.
        :param ws_timeout: The timeout for the websocket connection.
        :param ws_ping_interval: The interval between keepalive pings on the websocket connection.
        :param process_initial_data: Whether to process the initial data (including cached chats).
        :param enable_detailed_gifts: Whether to retrieve extended (detailed) gift info including its icon & other important things.
        :param trust_env: Whether to trust environment variables that provide proxies to be used in HTTP requests.
        :param proxies: Enable proxied requests by turning on forwarding for the HTTP "proxies" argument. Websocket connections will NOT be proxied.
        :param lang: Change the language. Payloads *will* be in English, but this will change stuff like the extended_gift Gift attribute to the desired language!
        :param fetch_room_info_on_connect: Whether to fetch room info on connect. If disabled, you might attempt to connect to a closed livestream.
        :param sign_api_key: Parameter to increase the amount of connections allowed to be made per minute via a Sign Server API key. If you need this, contact the project maintainer.
        """

        # Event loop. On connect, this will be filled if None
        self.loop: Optional[AbstractEventLoop] = self.__get_event_loop(loop)

        # Managed Attributes
        self.__room_info: Optional[dict] = None
        self.__available_gifts: Dict[int, GiftDetailed] = dict()
        self.__unique_id: str = validate_and_normalize_unique_id(unique_id)
        self.__room_id: Optional[int] = None
        self.__connecting: bool = False
        self.__connected: bool = False
        self._ws_connection_task: Optional[Task] = None

        # Configured Attributes
        self._ws_headers: Optional[dict] = ws_headers or dict()
        self._ws_ping_interval: float = ws_ping_interval
        self._ws_timeout: float = ws_timeout
        self._process_initial_data: bool = process_initial_data
        self._enable_detailed_gifts: bool = enable_detailed_gifts
        self._fetch_room_info_on_connect: bool = fetch_room_info_on_connect

        # HTTP Client for Webcast API
        self.http: TikTokHTTPClient = TikTokHTTPClient(
            loop=self.loop,
            headers=http_headers or dict(),
            timeout=http_timeout,
            proxies=proxies,
            trust_env=trust_env,
            params=self.__get_client_params(http_params or dict(), lang),
            sign_api_key=sign_api_key
        )

        # Websocket Client for Webcast API
        self.websocket: Optional[WebcastWebsocketConnection] = None

        # FFMpeg client for video downloads
        self.ffmpeg: Optional[FFmpegWrapper] = None

    @classmethod
    def __get_client_params(cls, parameters: Dict[str, str], language: str) -> Dict[str, str]:
        """
        Generate client parameters for the HTTP Client

        """

        params: Dict[str, str] = config.DEFAULT_CLIENT_PARAMS.copy()
        params["app_language"] = language
        params["webcast_language"] = language

        return {**config.DEFAULT_CLIENT_PARAMS, **(parameters if isinstance(parameters, dict) else dict())}

    @classmethod
    def __get_event_loop(cls, loop: Optional[AbstractEventLoop]) -> AbstractEventLoop:
        """
        Get event loop for constructor

        :param loop: Loop object to validate
        :return: A valid event loop

        """

        if isinstance(loop, AbstractEventLoop) and loop.is_running():
            return loop
        else:
            try:
                return asyncio.get_running_loop()
            except RuntimeError:
                return asyncio.new_event_loop()

    async def __fetch_room_id(self) -> Optional[int]:
        """
        Fetch room ID of a given user

        :return: Their Room ID
        :raises: asyncio.TimeoutError

        """

        try:
            html: str = await self.http.get_livestream_page_html(self.__unique_id)
            self.__room_id = int(get_room_id_from_main_page_html(html))
            self.http.params["room_id"] = str(self.__room_id)
            return self.__room_id
        except Exception as ex:
            await self._on_error(ex, FailedFetchRoomInfo("Failed to fetch room id from Webcast, see stacktrace for more info."))
            return None

    async def __fetch_room_data(self) -> dict:
        """
        Fetch the websocket URL from the Signing API

        :return: Initial Webcast response

        """

        # Fetch from polling api
        webcast_response = await self.http.get_deserialized_object_from_signing_api("webcast/fetch/", self.http.params, "WebcastResponse")

        # Update cursor
        _last_cursor, _next_cursor = self.http.params["cursor"], webcast_response.get("cursor")
        self.http.params["cursor"] = _last_cursor if _next_cursor == "0" else _next_cursor

        # Add param if given
        if webcast_response.get("internalExt"):
            self.http.params["internal_ext"] = webcast_response["internalExt"]

        return webcast_response

    async def __websocket_connect(self, webcast_response: Dict[str, Union[dict, str]]) -> None:
        """
        Attempt to upgrade the connection to a websocket

        :param webcast_response: The initial webcast response including the wsParam and wsUrl items
        :return: The websocket, if one is produced

        """

        uri: str = self.http.update_url(
            webcast_response.get("wsUrl"),
            {**self.http.params, **{"imprp": webcast_response.get("wsParam").get("value")}}
        )

        headers: dict = {
            **{"Cookie": " ".join(f"{k}={v};" for k, v in self.http.cookies.items())},
            **self._ws_headers
        }

        aio_connection: WebcastConnect = wsclient.connect(
            uri=uri,
            extra_headers=headers,
            subprotocols=["echo-protocol"],
            ping_interval=self._ws_ping_interval,
            ping_timeout=self._ws_timeout,
            create_protocol=WebcastWebsocketConnection
        )

        # Continuously reconnect unless we're disconnecting
        async for websocket in aio_connection:
            try:
                self.websocket: WebcastWebsocketConnection = websocket
                self.__connected, self.__connecting = True, False
                await self._on_connect()

                # Continuously receive messages
                async for response in websocket:
                    # Stop listening if disconnected
                    if websocket.manually_closed:
                        break

                    # Webcast response must contain messages
                    if not response.get("messages"):
                        continue

                    await self._handle_webcast_messages(response)

                # If disconnected, disconnect & clean up
                if websocket.manually_closed:
                    self.websocket = None
                    aio_connection.disconnect()
                    await websocket.close()
            except websockets.ConnectionClosed:
                raise asyncio.CancelledError()

    async def _on_connect(self) -> None:
        """
        Perform actions when the websocket client is connected

        """

        raise NotImplementedError()

    async def _on_error(self, original: Exception, append: Optional[Exception]) -> None:
        """
        Send errors to the _on_error handler for handling, appends a custom exception

        :param original: The original Python exception
        :param append: The specific exception

        """

        raise NotImplementedError()

    async def _handle_webcast_messages(self, webcast_response) -> None:
        """
        Handle the parsing of webcast messages, meant to be overridden by superclass

        """

        raise NotImplementedError

    async def _connect(self) -> None:
        """
        Connect to the WebCast Websocket Server. Asynchronous

        :return: The room ID, if connection is successful

        """

        if self.__connecting:
            raise AlreadyConnecting()

        if self.__connected:
            raise AlreadyConnected()

        # Get the loop again
        self.loop: AbstractEventLoop = self.__get_event_loop(self.loop)
        self.http.loop = self.loop

        # Set to already connecting
        self.__connecting = True

        # Get the Room ID, always
        await self.__fetch_room_id()

        # Fetch room info when connecting
        if self._fetch_room_info_on_connect:
            await self.retrieve_room_info()

            # If offline
            if self.__room_info.get("status", 4) == 4:
                raise LiveNotFound("The requested user is most likely offline.")

        # Get extended gift info
        if self._enable_detailed_gifts:
            await self.retrieve_available_gifts()

        # Make initial request to Webcast, connect to WebSocket server
        webcast_response: Dict[str, Union[dict, str]] = await self.__fetch_room_data()

        if not webcast_response.get("cursor"):
            raise InitialCursorMissing("Missing cursor in initial fetch response.")

        # If a WebSocket is offered, upgrade
        if not (webcast_response.get("wsUrl") and webcast_response.get("wsParam")):
            raise WebsocketConnectionFailed("No websocket URL received from TikTok")

        # Process initial data if requested
        if self._process_initial_data:
            await self._handle_webcast_messages(webcast_response)

        # Blocks current async execution, CONNECTS TO WEBCAST
        self._ws_connection_task = self.loop.create_task(self.__websocket_connect(webcast_response))

    def _disconnect(self) -> None:
        """
        Set the disconnected status

        """

        self.websocket.disconnect()
        self.__is_polling_enabled = False
        self.__room_info: Optional[dict] = None
        self.__connecting: Optional[bool] = False
        self.__connected: Optional[bool] = False
        self.http.params["cursor"]: str = ""
        self.http.cookies.clear()

    def stop(self) -> None:
        """
        Stop the client safely

        """

        if self.__connected:
            return self._disconnect()

    async def start(self) -> None:
        """
        Start the client without blocking the main thread

        """

        await self._connect()

    async def _start(self) -> None:
        """
        Start the client & keep blocked

        """

        # Start the program
        await self.start()

        # Keep running during lifetime
        while self.__connected or self.__connecting:
            await asyncio.sleep(1)

        # Wait for the main task to close gracefully
        # If it doesn't close after 5 seconds, force it to close
        time_waited: float = 0.0
        while not self._ws_connection_task.done():
            await asyncio.sleep(0.25)
            time_waited += 0.25
            if time_waited > 5.0:
                self._ws_connection_task.cancel()
                break

    def run(self) -> None:
        """
        Run client while blocking main thread

        :return: None

        """

        self.loop.run_until_complete(self._start())

    async def retrieve_room_info(self) -> Optional[dict]:
        """
        Fetch room information from Webcast API

        :return: Room info dict

        """

        try:
            response = await self.http.get_json_object_from_webcast_api("room/info/", self.http.params)
            self.__room_info = response
            return self.__room_info
        except Exception as ex:
            await self._on_error(ex, FailedFetchRoomInfo("Failed to fetch room info from Webcast, see stacktrace for more info."))
            return None

    async def retrieve_available_gifts(self) -> Optional[Dict[int, GiftDetailed]]:
        """
        Fetch available gifts from Webcast API

        :return: Gift info dict

        """

        try:
            response = await self.http.get_json_object_from_webcast_api("gift/list/", self.http.params)
            gifts: Optional[List] = response.get("gifts")

            if isinstance(gifts, list):
                for gift_data in gifts:
                    try:
                        gift: GiftDetailed = GiftDetailed.from_dict(gift_data)
                        self.__available_gifts[gift.id] = gift
                    except Exception as ex:
                        await self._on_error(ex, FailedParseGift("Failed to parse gift's extra info"))
            return self.__available_gifts
        except Exception as ex:
            await self._on_error(ex, FailedFetchGifts("Failed to fetch gift data from Webcast, see stacktrace for more info."))
            return None

    def download(
            self,
            path: str,
            duration: Optional[int] = None,
            quality: Optional[VideoQuality] = None,
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
        :param quality: If quality is None, download quality will auto
        :param verbose: Whether to log info about the download in console

        :return: None
        :raises: AlreadyDownloadingStream if already downloading and attempting to start a second download

        """

        # If already downloading stream at the moment
        if self.ffmpeg is not None:
            raise AlreadyDownloadingStream()

        # Set a runtime
        runtime: Optional[str] = None
        if duration is not None and duration >= 1:
            runtime = f"-t {duration}"

        # Set a quality
        url: dict = json.loads(self.room_info['stream_url']['live_core_sdk_data']['pull_data']['stream_data'])
        quality = quality if isinstance(quality, VideoQuality) else VideoQuality.ORIGIN

        # Set the URL based on selected quality
        url_param: str = url['data'][quality.value]['main']['hls']
        if len(url_param.strip()) == 0:
            url_param: str = url['data'][quality.value]['main']['flv']

        # Function Running
        def spool():
            try:
                self.ffmpeg.ffmpeg.run()
            except FFRuntimeError as ex:
                if ex.exit_code and ex.exit_code != 255:
                    self.ffmpeg = None
                    raise
            self.ffmpeg = None

        # Create an FFmpeg wrapper
        self.ffmpeg = FFmpegWrapper(
            ffmpeg=FFmpeg(
                inputs={**{url_param: None}, **inputs},
                outputs={**{path: runtime}, **outputs},
                global_options={"-y", f"-loglevel {loglevel}"}.union(global_options)
            ),
            thread=Thread(target=spool),
            verbose=verbose,
            path=path,
            runtime=runtime
        )

        # Start the download
        self.ffmpeg.thread.start()
        self.ffmpeg.started_at = int(datetime.utcnow().timestamp())

        # Give info about the started download
        if self.ffmpeg.verbose:
            logging.warning(f"Started the download to path \"{path}\" for duration \"{'infinite' if runtime is None else duration} seconds\" on user @{self.unique_id} with \"{quality.name}\" video quality")

    def stop_download(self) -> None:
        """
        Stop downloading a livestream if currently downloading

        :return: None
        :raises NotDownloadingStream: Raised if trying to stop when not downloading and
        :raises DownloadProcessNotFound: Raised if stopping before the ffmpeg process has opened

        """

        # If attempting to stop a download when none is occurring
        if self.ffmpeg is None:
            raise NotDownloadingStream("Not currently downloading the stream!")

        # If attempting to stop a download before the process has opened
        if self.ffmpeg.ffmpeg.process is None:
            raise DownloadProcessNotFound("Download process not found. You are likely stopping the download before the ffmpeg process has opened. Add a delay!")

        # Kill the process
        os.kill(self.ffmpeg.ffmpeg.process.pid, signal.CTRL_BREAK_EVENT)

        # Give info about the final product
        if self.ffmpeg.verbose:
            logging.warning(
                f"Stopped the download to path \"{self.ffmpeg.path}\" on user @{self.unique_id} after "
                f"\"{int(datetime.utcnow().timestamp()) - self.ffmpeg.started_at} seconds\" of downloading"
            )

    @property
    def proxies(self) -> Optional[Dict[str, str]]:
        """
        Get the current proxies being used in HTTP requests

        """
        return self.http.proxies

    @proxies.setter
    def proxies(self, proxies: Optional[Dict[str, str]]) -> None:
        """
        Set the proxies to be used by the HTTP client (Not Websockets)

        :param proxies: The proxies to use in HTTP requests

        """
        self.http.proxies = proxies

    @property
    def room_id(self) -> Optional[int]:
        """
        Room ID if the connection was successful

        """
        return self.__room_id

    @property
    def room_info(self) -> Optional[dict]:
        """
        Room info dict if the connection was successful

        """
        return self.__room_info

    @property
    def unique_id(self) -> str:
        """
        Unique ID of the streamer

        """
        return self.__unique_id

    @property
    def connected(self) -> bool:
        """
        Whether the client is connected

        """

        return self.__connected

    @property
    def connecting(self) -> bool:
        """
        Whether the client is in the process of connecting
        
        """

        return self.__connecting

    @property
    def available_gifts(self) -> Dict[int, GiftDetailed]:
        """
        Available gift information for live room

        """

        return self.__available_gifts
