import asyncio
import inspect
import logging
import traceback
import urllib.parse
from asyncio import AbstractEventLoop, Task, CancelledError
from logging import Logger
from typing import Optional, Type, AsyncIterator, Dict, Any, Tuple, Union, Callable, List, Coroutine

from httpx import Proxy
from pyee import AsyncIOEventEmitter
from pyee.base import Handler

from TikTokLive.client.errors import AlreadyConnectedError, UserOfflineError, InitialCursorMissingError, \
    WebsocketURLMissingError, AgeRestrictedError
from TikTokLive.client.logger import TikTokLiveLogHandler, LogLevel
from TikTokLive.client.web.web_client import TikTokWebClient
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.client.ws.ws_client import WebcastWSClient
from TikTokLive.events import Event, EventHandler
from TikTokLive.events.custom_events import WebsocketResponseEvent, ConnectEvent, FollowEvent, ShareEvent, LiveEndEvent, \
    DisconnectEvent, LivePauseEvent, LiveUnpauseEvent, UnknownEvent, CustomEvent
from TikTokLive.events.proto_events import EVENT_MAPPINGS, ProtoEvent, ControlEvent
from TikTokLive.proto import WebcastResponse, WebcastResponseMessage, ControlAction


class TikTokLiveClient(AsyncIOEventEmitter):
    """
    A client to connect to & read from TikTok LIVE streams

    """

    def __init__(
            self,
            unique_id: str,
            web_proxy: Optional[Proxy] = None,
            ws_proxy: Optional[Proxy] = None,
            web_kwargs: dict = {},
            ws_kwargs: dict = {}
    ):
        """
        Instantiate the TikTokLiveClient client

        :param unique_id: The username of the creator to connect to
        :param web_proxy: An optional proxy used for HTTP requests
        :param ws_proxy: An optional proxy used for the WebSocket connection
        :param web_kwargs: Optional arguments used by the HTTP client
        :param ws_kwargs: Optional arguments used by the WebSocket client

        """

        super().__init__()

        self._ws: WebcastWSClient = WebcastWSClient(
            ws_kwargs=ws_kwargs,
            proxy=ws_proxy
        )

        self._web: TikTokWebClient = TikTokWebClient(
            httpx_kwargs=web_kwargs,
            proxy=web_proxy
        )

        self._logger: Logger = TikTokLiveLogHandler.get_logger(
            level=LogLevel.ERROR
        )

        # Properties
        self._unique_id: str = self.parse_unique_id(unique_id)
        self._room_id: Optional[str] = None
        self._room_info: Optional[Dict[str, Any]] = None
        self._gift_info: Optional[Dict[str, Any]] = None
        self._event_loop_task: Optional[Task] = None

    @classmethod
    def parse_unique_id(cls, unique_id: str) -> str:
        """
        Parse unique ID from a generic string

        :param unique_id: The unique_id to parse
        :return: The parsed unique_id

        """

        return unique_id \
            .replace(WebDefaults.tiktok_app_url + "/", "") \
            .replace("/live", "") \
            .replace("@", "", 1) \
            .strip()

    async def start(
            self,
            *,
            process_connect_events: bool = True,
            fetch_room_info: bool = True,
            fetch_gift_info: bool = False,
            room_id: Optional[int] = None
    ) -> Task:
        """
        Create a non-blocking connection to TikTok LIVE and return the task

        :param process_connect_events: Whether to process initial events sent on room join
        :param fetch_room_info: Whether to fetch room info on join
        :param fetch_gift_info: Whether to fetch gift info on join
        :param room_id: An override to the room ID to connect directly to the livestream and skip scraping the live.
                        Useful when trying to scale, as scraping the HTML can result in TikTok blocks.
        :return: Task containing the heartbeat of the client

        """

        if self._ws.connected:
            raise AlreadyConnectedError("You can only make one connection per client!")

        # <Required> Fetch room ID
        self._room_id: str = room_id or await self._web.fetch_room_id(self._unique_id)

        # <Optional> Fetch room info
        if fetch_room_info:
            self._room_info = await self._web.fetch_room_info()
            if "prompts" in self._room_info and len(self._room_info) == 1:
                raise AgeRestrictedError("Age restricted. Pass sessionid to log in & bypass age restriction.")
            if self._room_info.get("status", 4) == 4:
                raise UserOfflineError()

        # <Optional> Fetch gift info
        if fetch_gift_info:
            self._gift_info = await self._web.fetch_gift_list()

        # <Required> Fetch the first response
        webcast_response: WebcastResponse = await self._web.fetch_sign_fetch()

        # <Optional> Disregard initial events
        webcast_response.messages = webcast_response.messages if process_connect_events else []

        # Handle detection & invalid payloads
        if not webcast_response.cursor:
            raise InitialCursorMissingError("Missing cursor in initial fetch response.")
        if not webcast_response.push_server:
            raise WebsocketURLMissingError("No websocket URL received from TikTok.")
        if not webcast_response.route_params_map:
            raise WebsocketURLMissingError("Websocket parameters missing.")

        # Start the websocket connection & return it
        self._event_loop_task = self._asyncio_loop.create_task(self._client_loop(webcast_response))
        return self._event_loop_task

    async def connect(
            self,
            callback: Optional[
                Union[
                    Callable[[None], None],
                    Callable[[None], Coroutine[None, None, None]],
                    Coroutine[None, None, None],
                ]
            ] = None,
            **kwargs
    ) -> Task:
        """
        Start a future-blocking connection to TikTokLive

        :param callback: A callback function to run when connected
        :param kwargs: Kwargs to pass to start
        :return: The task, once it's finished

        """

        task: Task = await self.start(**kwargs)

        try:
            if inspect.iscoroutinefunction(callback):
                self._asyncio_loop.create_task(callback())
            elif inspect.isawaitable(callback):
                self._asyncio_loop.create_task(callback)
            elif inspect.isfunction(callback):
                callback()
            await task
        except CancelledError:
            self._logger.debug("The client has been manually stopped with 'client.stop()'.")

        return task

    def run(self, **kwargs) -> Task:
        """
        Start a thread-blocking connection to TikTokLive

        :param kwargs: Kwargs to pass to start
        :return: The task, once it's finished

        """

        return self._asyncio_loop.run_until_complete(self.connect(**kwargs))

    async def disconnect(self) -> None:
        """
        Disconnect the client from the websocket

        :return: None

        """

        # Wait gracefully for things to finish
        await self._ws.disconnect()
        await self._event_loop_task

        # If recording, stop
        if self._web.fetch_video.is_recording:
            self._web.fetch_video.stop()

        # Reset state vars
        self._room_id = None
        self._room_info = None
        self._gift_info = None
        self._event_loop_task = None

    async def _client_loop(self, initial_response: WebcastResponse) -> None:
        """
        Run the main client loop to handle events

        :param initial_response: The WebcastResponse retrieved from the sign server with connection info
        :return: None

        """

        async for event in self._ws_loop(initial_response):

            if event is None:
                continue

            self._logger.debug(f"Received Event '{event.type}'.")
            self.emit(event.type, event)

        # Disconnecting
        ev: DisconnectEvent = DisconnectEvent()
        self.emit(ev.type, ev)

    async def _ws_loop(self, initial_response: WebcastResponse) -> AsyncIterator[Optional[Event]]:
        """
        Run the websocket loop to handle incoming WS messages

        :param initial_response: The WebcastResponse retrieved from the sign server with connection info
        :return: None

        """

        first_event: bool = True

        # Handle websocket connection
        async for response_message in self._ws.connect(*self._build_connect_info(initial_response)):

            if first_event:
                first_event = False

                # Send a connection event
                yield ConnectEvent(unique_id=self._unique_id, room_id=self._room_id)

                # Handle initial messages
                for webcast_message in initial_response.messages:
                    for event in self._parse_webcast_response(webcast_message):
                        yield event

            for event in self._parse_webcast_response(response_message):
                yield event

    def _build_connect_info(self, initial_response: WebcastResponse) -> Tuple[str, dict]:
        """
        Create connection info for starting the connection

        :param initial_response: The WebcastResponse retrieved from the sign server with connection info
        :return: None

        """

        connect_uri: str = (
                initial_response.push_server
                + "?"
                + urllib.parse.urlencode({**self._web.params, **initial_response.route_params_map})
        )

        connect_headers: dict = {
            "Cookie": " ".join(f"{k}={v};" for k, v in self._web.cookies.items())
        }

        return connect_uri, connect_headers

    def on(self, event: Type[Event], f: Optional[EventHandler] = None) -> Union[Handler, Callable[[Handler], Handler]]:
        """
        Decorator that can be used to register a Python function as an event listener

        :param event: The event to listen to
        :param f: The function to handle the event
        :return: The wrapped function as a generated `pyee.Handler` object

        """

        return super(TikTokLiveClient, self).on(event.get_type(), f)

    def add_listener(self, event: Type[Event], f: EventHandler) -> Handler:
        """
        Method that can be used to register a Python function as an event listener

        :param event: The event to listen to
        :param f: The function to handle the event
        :return: The generated `pyee.Handler` object

        """
        if isinstance(event, str):
            return super().add_listener(event=event, f=f)

        return super().add_listener(event=event.get_type(), f=f)

    def has_listener(self, event: Type[Event]) -> bool:
        """
        Check whether the client is listening to a given event

        :param event: The event to check listening for
        :return: Whether it is being listened to

        """

        return event.__name__ in self._events

    def _parse_webcast_response(self, response: Optional[WebcastResponseMessage]) -> List[Event]:
        """
        Parse incoming webcast responses into events that can be emitted

        :param response: The WebcastResponseMessage protobuf message
        :return: A list of events that can be gleamed from this event

        """

        # Invalid response handler
        if response is None:
            self._logger.warning("Received a null WebcastResponseMessage from the Webcast server.")
            return []

        # Get the proto mapping for proto-events
        event_type: Optional[Type[ProtoEvent]] = EVENT_MAPPINGS.get(response.method)
        response_event: Event = WebsocketResponseEvent().from_pydict(response.to_dict())

        # If the event is not tracked, return
        if event_type is None:
            return [response_event, UnknownEvent().from_pydict(response.to_dict())]

        # Get the underlying events
        try:
            proto_event: ProtoEvent = event_type().parse(response.payload)
        except Exception:
            self._logger.error(traceback.format_exc())
            return [response_event]

        parsed_events: List[Event] = [response_event, proto_event]
        custom_event: Optional[Event] = self._parse_custom_event(response, proto_event)

        # Add the custom event IF not null
        return [custom_event, *parsed_events] if custom_event else parsed_events

    async def is_live(self, unique_id: Optional[str] = None) -> bool:
        """
        Check if the client is currently live on TikTok

        :param unique_id: Optionally override the user to check
        :return: Whether they are live on TikTok

        """

        return await self._web.fetch_is_live(unique_id=unique_id or self.unique_id)

    @classmethod
    def _parse_custom_event(cls, response: WebcastResponseMessage, event: ProtoEvent) -> Optional[CustomEvent]:
        """
        Extract CustomEvent events from existing ProtoEvent events

        :param response: The WebcastResponseMessage to parse for the custom event
        :param event: The ProtoEvent to parse for the custom event
        :return: The event, if one exists

        """

        # LiveEndEvent, LivePauseEvent, LiveUnpauseEvent
        if isinstance(event, ControlEvent):
            if event.action == ControlAction.STREAM_ENDED:
                return LiveEndEvent().parse(response.payload)
            elif event.action == ControlAction.STREAM_PAUSED:
                return LivePauseEvent().parse(response.payload)
            elif event.action == ControlAction.STREAM_PAUSED:
                return LiveUnpauseEvent().parse(response.payload)
            return None

        # FollowEvent
        if "follow" in event.common.display_text.key:
            return FollowEvent().parse(response.payload)

        # ShareEvent
        if "share" in event.common.display_text.key:
            return ShareEvent().parse(response.payload)

        # Not a custom event
        return None

    @property
    def unique_id(self) -> str:
        """
        The cleaned unique-id parameter passed to the client

        """

        return self._unique_id

    @property
    def room_id(self) -> Optional[str]:
        """
        The room ID the user is currently connected to

        :return: Room ID or None

        """

        return self._room_id

    @property
    def web(self) -> TikTokWebClient:
        """
        The HTTP client that this client uses for requests

        :return: A copy of the TikTokWebClient

        """

        return self._web

    @property
    def _asyncio_loop(self) -> AbstractEventLoop:
        """
        Property to return the existing or generate a new asyncio event loop

        :return: An asyncio event loop

        """

        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.new_event_loop()

    @property
    def connected(self) -> bool:
        """
        Whether the WebSocket client is currently connected to TikTok

        :return: Connection status

        """

        return self._ws.connected

    @property
    def logger(self) -> logging.Logger:
        """
        The internal logger used by TikTokLive

        :return: An instance of a `logging.Logger`

        """

        return self._logger

    @property
    def gift_info(self) -> Optional[dict]:
        """
        Information about the stream's gifts *if* fetch_gift_info=True when starting the client e.g. with `client.run`)

        :return: The stream gift info

        """

        return self._gift_info

    @property
    def room_info(self) -> Optional[dict]:
        """
        Information about the room *if* fetch_room_info=True when starting the client (e.g. with `client.run`)

        :return: Dictionary of room info

        """

        return self._room_info
