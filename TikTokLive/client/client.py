import asyncio
import inspect
import logging
import traceback
from asyncio import AbstractEventLoop, Task, CancelledError
from logging import Logger
from typing import Optional, Type, Dict, Any, Union, Callable, List, Coroutine, AsyncIterator

import httpx
from pyee.asyncio import AsyncIOEventEmitter
from pyee.base import Handler

from TikTokLive.client.errors import AlreadyConnectedError, UserOfflineError, UserNotFoundError
from TikTokLive.client.logger import TikTokLiveLogHandler, LogLevel
from TikTokLive.client.web.routes.fetch_user_unique_id import FailedResolveUserId
from TikTokLive.client.web.web_client import TikTokWebClient
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.client.ws.ws_client import WebcastWSClient
from TikTokLive.client.ws.ws_connect import WebcastProxy
from TikTokLive.events import Event, EventHandler, ControlEvent
from TikTokLive.events.custom_events import WebsocketResponseEvent, FollowEvent, ShareEvent, LiveEndEvent, \
    DisconnectEvent, LivePauseEvent, LiveUnpauseEvent, UnknownEvent, CustomEvent, ConnectEvent
from TikTokLive.events.proto_events import EVENT_MAPPINGS, ProtoEvent
from TikTokLive.proto import ProtoMessageFetchResult, ProtoMessageFetchResultBaseProtoMessage
from TikTokLive.proto.custom_proto import ControlAction


class TikTokLiveClient(AsyncIOEventEmitter):
    """
    A client to connect to & read from TikTok LIVE streams

    """

    def __init__(
            self,
            # User to connect to
            unique_id: str | int,

            # Proxies
            web_proxy: Optional[httpx.Proxy] = None,
            ws_proxy: Optional[WebcastProxy] = None,

            # Client kwargs
            web_kwargs: Optional[dict] = None,
            ws_kwargs: Optional[dict] = None,

            is_userid: Optional[bool] = False
    ):
        """
        Instantiate the TikTokLiveClient client

        :param unique_id: The username of the creator to connect to
        :param web_proxy: An optional proxy used for HTTP requests
        :param ws_proxy: An optional proxy used for the WebSocket connection
        :param web_kwargs: Optional arguments used by the HTTP client
        :param ws_kwargs: Optional arguments used by the WebSocket client
        :param is_userid: Optional argument to resolve userid to unique_id

        """

        super().__init__()

        self._ws: WebcastWSClient = WebcastWSClient(
            ws_kwargs=ws_kwargs or {},
            ws_proxy=ws_proxy
        )

        self._web: TikTokWebClient = TikTokWebClient(
            web_proxy=web_proxy or (web_kwargs or {}).pop("web_proxy", None),
            **(web_kwargs or {})
        )

        self._web.params['referer'] = f"https://www.tiktok.com/@{unique_id}/live"
        self._web.params['root_referer'] = f"https://www.tiktok.com/@{unique_id}/live"

        self._logger: Logger = TikTokLiveLogHandler.get_logger(
            level=LogLevel.ERROR
        )

        # Overridable properties
        self.ignore_broken_payload: bool = False

        # Properties
        self._is_userid: bool = is_userid
        self._unique_id: str = self.parse_unique_id(unique_id)
        self._room_id: Optional[int] = None
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
            compress_ws_events: bool = True,
            fetch_room_info: bool = False,
            fetch_gift_info: bool = False,
            fetch_live_check: bool = True,
            room_id: Optional[int] = None,
            preferred_agent_ids: Optional[list[str]] = None
    ) -> Task:
        """
        Create a non-blocking connection to TikTok LIVE and return the task

        :param process_connect_events: Whether to process initial events sent on room join
        :param fetch_room_info: Whether to fetch room info on join
        :param fetch_gift_info: Whether to fetch gift info on join
        :param fetch_live_check: Whether to check if the user is live (you almost ALWAYS want this enabled)
        :param room_id: An override to the room ID to connect directly to the livestream and skip scraping the live.
                        Useful when trying to scale, as scraping the HTML can result in TikTok blocks.
        :param compress_ws_events: Whether to compress the WebSocket events using gzip compression (you should probably have this on)
        :param preferred_agent_ids: The preferred agent IDs to use when connecting to the WebSocket
        :return: Task containing the heartbeat of the client

        """

        if self._ws.connected:
            raise AlreadyConnectedError("You can only make one connection per client!")

        self._unique_id = await self._resolve_user_id(self._unique_id)

        # <Required> Fetch room ID
        try:
            self._room_id: int = int(room_id or await self._web.fetch_room_id_from_html(self._unique_id))
        except Exception as base_ex:

            if isinstance(base_ex, UserOfflineError) or isinstance(base_ex, UserNotFoundError):
                raise base_ex

            try:
                self._logger.error("Failed to parse room ID from HTML. Using API fallback.")
                self._room_id: int = int(await self._web.fetch_room_id_from_api(self.unique_id))
            except Exception as super_ex:
                raise super_ex from base_ex

        # Gram Room ID
        self._web.params["room_id"] = str(self._room_id) or None

        # <Optional> Fetch live status
        if fetch_live_check and not await self._web.fetch_is_live(room_id=self._room_id):
            raise UserOfflineError()

        # <Optional> Fetch room info
        if fetch_room_info:
            self._room_info = await self._web.fetch_room_info()

        # <Optional> Fetch gift info
        if fetch_gift_info:
            self._gift_info = await self._web.fetch_gift_list()

        # <Required> Fetch the first response
        initial_webcast_response: ProtoMessageFetchResult = await self._web.fetch_signed_websocket(
            preferred_agent_ids=preferred_agent_ids
        )

        # Start the websocket connection & return it
        self._event_loop_task = self._asyncio_loop.create_task(
            self._ws_client_loop(
                initial_webcast_response=initial_webcast_response,
                process_connect_events=process_connect_events,
                compress_ws_events=compress_ws_events
            )
        )

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

    async def disconnect(self, close_client: bool = False) -> None:
        """
        Disconnect the client from the websocket.

        :param close_client: Whether to also close the HTTP client if you don't intend to reuse it
        :return: None

        """

        # Disconnect the WebSocket
        await self._ws.disconnect()

        # Wait for the event loop task to finish
        if self._event_loop_task is not None:
            try:
                await self._event_loop_task
            except Exception:
                self._logger.debug("an exception in event loop is ignored", exc_info=True)
            self._event_loop_task = None

        # If recording, stop it
        if self._web.fetch_video_data.is_recording:
            self._web.fetch_video_data.stop()

        # Close the client (if discarding)
        if close_client:
            await self.close()

        # Reset state vars
        self._room_id = None
        self._room_info = None
        self._gift_info = None

    async def close(self) -> None:
        """
        Discards the async sessions if you don't intend to use the client again

        :return: None

        """

        await self._web.close()

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

    async def _ws_client_loop(
            self,
            initial_webcast_response: ProtoMessageFetchResult,
            process_connect_events: bool,
            compress_ws_events: bool
    ) -> None:
        """
        Run the websocket loop to handle incoming WS events

        :param initial_webcast_response: The ProtoMessageFetchResult (as bytes) retrieved from the sign server with connection info
        :param process_connect_events: Whether to process initial events sent on room join
        :param compress_ws_events: Whether to compress the WebSocket events using gzip compression
        :return: None

        """

        # Handle websocket connection
        async for webcast_response in self._ws.connect(
                initial_webcast_response=initial_webcast_response,
                process_connect_events=process_connect_events,
                compress_ws_events=compress_ws_events,
                cookies=self._web.cookies,
                room_id=self._room_id,
                user_agent=self._web.headers['User-Agent']
        ):

            # Iterate over the events extracted
            async for event in self._parse_webcast_response(webcast_response):
                self._logger.debug(f"Received Event '{event.type}' [{event.size} bytes]")
                self.emit(event.type, event)

        # Send the Disconnect event when we disconnect
        ev: DisconnectEvent = DisconnectEvent()
        self.emit(ev.type, ev)

    async def _parse_webcast_response(self, webcast_response: ProtoMessageFetchResult) -> AsyncIterator[Event]:
        """
        Parse incoming webcast responses into events that can be emitted

        :param webcast_response: The ProtoMessageFetchResult protobuf message
        :return: A list of events that can be gleamed from this event

        """

        # The first event means we connected
        if webcast_response.is_first:
            yield ConnectEvent(unique_id=self._unique_id, room_id=self._room_id)

        # Yield events
        for message in webcast_response.messages:
            for event in await self._parse_webcast_response_message(webcast_response_message=message):
                if event is not None:
                    yield event

    async def _parse_webcast_response_message(self, webcast_response_message: Optional[
        ProtoMessageFetchResultBaseProtoMessage]) -> List[Event]:
        """
        Parse incoming webcast responses into events that can be emitted

        :param webcast_response_message: The ProtoMessageFetchResultMessage protobuf message
        :return: A list of events that can be gleamed from this event

        """

        # Invalid response handler
        if webcast_response_message is None:
            self._logger.warning("Received a null ProtoMessageFetchResultMessage from the Webcast server.")
            return []

        # Get the proto mapping for proto-events
        event_type: Optional[Type[ProtoEvent]] = EVENT_MAPPINGS.get(webcast_response_message.method)
        response_event: Event = WebsocketResponseEvent().from_dict(webcast_response_message.to_dict())

        # If the event is not tracked, return
        if event_type is None:
            return [response_event, UnknownEvent().from_dict(webcast_response_message.to_dict())]

        # Get the underlying events
        try:
            proto_event: ProtoEvent = event_type().parse(webcast_response_message.payload)
        except Exception:
            if not self.ignore_broken_payload:
                self._logger.error(
                    traceback.format_exc() + "\nBroken Payload:\n" + str(webcast_response_message.payload))
            return [response_event]

        parsed_events: List[Event] = [response_event, proto_event]
        custom_event: Optional[Event] = await self.handle_custom_event(webcast_response_message, proto_event)

        # Add the custom event IF not null
        return [custom_event, *parsed_events] if custom_event else parsed_events

    async def is_live(self, unique_id: Optional[str | int] = None) -> bool:
        """
        Check if the client is currently live on TikTok

        :param unique_id: Optionally override the user to check
        :return: Whether they are live on TikTok

        """

        self._unique_id = unique_id = await self._resolve_user_id(unique_id or self.unique_id)

        return await self._web.fetch_is_live(unique_id=unique_id or self.unique_id)

    async def handle_custom_event(self, response: ProtoMessageFetchResultBaseProtoMessage, event: ProtoEvent) -> \
            Optional[CustomEvent]:
        """
        Extract CustomEvent events from existing ProtoEvent events

        :param response: The ProtoMessageFetchResultMessage to parse for the custom event
        :param event: The ProtoEvent to parse for the custom event
        :return: The event, if one exists

        """

        # LiveEndEvent, LivePauseEvent, LiveUnpauseEvent
        if isinstance(event, ControlEvent):
            if event.action in {
                ControlAction.CONTROL_ACTION_STREAM_ENDED,
                ControlAction.CONTROL_ACTION_STREAM_SUSPENDED
            }:
                # If the stream is over, disconnect the client. Can't await due to circular dependency.
                self._asyncio_loop.create_task(self.disconnect())
                return LiveEndEvent().parse(response.payload)
            elif event.action == ControlAction.CONTROL_ACTION_STREAM_PAUSED:
                return LivePauseEvent().parse(response.payload)
            elif event.action == ControlAction.CONTROL_ACTION_STREAM_PAUSED:
                return LiveUnpauseEvent().parse(response.payload)
            return None

        # FollowEvent
        if "follow" in event.base_message.display_text.key:
            return FollowEvent().parse(response.payload)

        # ShareEvent
        if "share" in event.base_message.display_text.key:
            return ShareEvent().parse(response.payload)

        # Not a custom event
        return None

    async def _resolve_user_id(self, unique_id: str | int) -> str:
        """Resolve a unique_id and return the resolved value"""
        parsed_id = self.parse_unique_id(unique_id)
        if parsed_id.isdigit() and self._is_userid:
            resolved_id = await self._web.fetch_user_unique_id(parsed_id)
            if not resolved_id:
                raise FailedResolveUserId(f"Resolved ID is invalid: {resolved_id}")
            return resolved_id
        return parsed_id

    async def send_room_chat(
            self,
            content: str
    ) -> Any:
        """
        Send a chat message to the room

        :param content: The content of the message
        :return: The response from TikTok

        """

        return await self._web.send_room_chat(content=content, room_id=self._room_id)

    @property
    def unique_id(self) -> str:
        """
        The cleaned unique-id parameter passed to the client

        """

        return self._unique_id

    @property
    def room_id(self) -> Optional[int]:
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
