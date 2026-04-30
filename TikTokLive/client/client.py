import asyncio
import inspect
import logging
import traceback
import re
from html import unescape
from asyncio import AbstractEventLoop, Task, CancelledError
from logging import Logger
from typing import Optional, Type, Dict, Any, Union, Callable, List, Coroutine, AsyncIterator, overload

import httpx
from pyee.asyncio import AsyncIOEventEmitter
from pyee.base import Handler

from TikTokLive.client.errors import AlreadyConnectedError, UserOfflineError
from TikTokLive.client.logger import TikTokLiveLogHandler, LogLevel
from TikTokLive.client.web.routes.fetch_signed_websocket import WebcastPlatform
from TikTokLive.client.web.routes.fetch_user_unique_id import FailedResolveUserId
from TikTokLive.client.web.web_client import TikTokWebClient
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.client.ws.ws_client import WebcastWSClient
from TikTokLive.client.ws.ws_connect import WebcastProxy
from TikTokLive.events import Event, EventHandler, ControlEvent
from TikTokLive.events.custom_events import WebsocketResponseEvent, FollowEvent, ShareEvent, LiveEndEvent, \
    DisconnectEvent, LivePauseEvent, LiveUnpauseEvent, UnknownEvent, CustomEvent, ConnectEvent, SuperFanEvent, \
    SuperFanJoinEvent, SuperFanBoxEvent
from TikTokLive.events.proto_events import EVENT_MAPPINGS, ProtoEvent, BarrageEvent, EnvelopeEvent
from TikTokLive.proto import ProtoMessageFetchResult, ProtoMessageFetchResultBaseProtoMessage
from TikTokLive.proto.custom_proto import ControlAction
from TikTokLive.proto.proto_utils import common_display_type

# Default fingerprints of parse failures rooted in upstream proto schema
# bugs. These are substring-matched against the exception's ``str(...)`` and
# any matching parse error is logged at DEBUG instead of ERROR. Clients can
# extend the list at runtime via ``client.parse_error_ignorelist``.
#
# v3 fixed the v2-era ``LinkLayerListUser.linkmic_id`` int64-vs-string bug,
# so the list starts empty. Add new fingerprints here as upstream schema
# regressions surface.
DEFAULT_PARSE_ERROR_IGNORELIST: List[str] = []

# Maximum number of bytes to include from the raw payload when logging a
# parse failure. Anything over this gets truncated with a "(N more)" suffix
# to keep the log readable while still being diagnostic.
_PARSE_ERROR_PAYLOAD_PREVIEW_BYTES: int = 32


def _truncate_payload(payload: Optional[bytes]) -> str:
    """Format raw payload for log output, truncated to a small preview."""
    if not payload:
        return repr(payload)
    if len(payload) <= _PARSE_ERROR_PAYLOAD_PREVIEW_BYTES:
        return repr(payload)
    head = payload[:_PARSE_ERROR_PAYLOAD_PREVIEW_BYTES]
    return f"{head!r}...(+{len(payload) - _PARSE_ERROR_PAYLOAD_PREVIEW_BYTES} more bytes)"


class TikTokLiveClient(AsyncIOEventEmitter):
    """
    A client to connect to & read from TikTok LIVE streams

    """

    def __init__(
            self,
            # User to connect to
            unique_id: str | int,
            platform: WebcastPlatform = WebcastPlatform.WEB,

            # Proxies
            web_proxy: Optional[httpx.Proxy] = None,
            ws_proxy: Optional[WebcastProxy] = None,

            # Client kwargs
            web_kwargs: Optional[dict] = None,
            ws_kwargs: Optional[dict] = None,

            is_user_id: Optional[bool] = False
    ):
        """
        Instantiate the TikTokLiveClient client

        :param unique_id: The username of the creator to connect to
        :param web_proxy: An optional proxy used for HTTP requests
        :param ws_proxy: An optional proxy used for the WebSocket connection
        :param web_kwargs: Optional arguments used by the HTTP client
        :param ws_kwargs: Optional arguments used by the WebSocket client
        :param is_user_id: Optional argument to resolve userid to unique_id

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

        # Substring fingerprints of parse errors we silently demote to DEBUG
        # because the underlying schema bug lives upstream in TikTokLiveProto
        # rather than in this codebase. Append to extend; clear to make every
        # parse failure ERROR-level again.
        self.parse_error_ignorelist: List[str] = list(DEFAULT_PARSE_ERROR_IGNORELIST)

        # Properties
        self._is_user_id: bool = bool(is_user_id)
        self._ws_platform: WebcastPlatform = platform
        self._unique_id: str = self.parse_unique_id(unique_id)
        self._room_id: Optional[int] = None
        self._room_info: Optional[Dict[str, Any]] = None
        self._gift_info: Optional[Dict[str, Any]] = None
        self._event_loop_task: Optional[Task] = None

    @classmethod
    def parse_unique_id(cls, unique_id: str | int) -> str:
        """
        Parse unique ID from a generic string. Numeric ids (int or numeric
        string) are stringified verbatim; URL-style strings are stripped to
        the bare ``unique_id``.

        :param unique_id: The unique_id to parse
        :return: The parsed unique_id

        """

        return str(unique_id) \
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
        :return: Task containing the heartbeat of the client

        """

        if self._ws.connected:
            raise AlreadyConnectedError("You can only make one connection per client!")

        self._unique_id = await self._resolve_user_id(self._unique_id)

        # <Required> Fetch room ID
        try:
            self._room_id = int(room_id or await self._web.fetch_room_id_from_html(self._unique_id))
        except Exception as base_ex:

            # Do not raise on UserNotFoundError as this can be a captcha issue
            if isinstance(base_ex, UserOfflineError):
                raise base_ex

            try:
                self._logger.debug("Failed to parse room ID from HTML. Using API fallback.")
                self._room_id = int(await self._web.fetch_room_id_from_api(self.unique_id))
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
        initial_webcast_response: ProtoMessageFetchResult = await self._web.fetch_signed_websocket(self._ws_platform)

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
            *,
            process_connect_events: bool = True,
            compress_ws_events: bool = True,
            fetch_room_info: bool = False,
            fetch_gift_info: bool = False,
            fetch_live_check: bool = True,
            room_id: Optional[int] = None,
    ) -> Task:
        """
        Start a future-blocking connection to TikTokLive.

        Kwargs are spelled out (not ``**kwargs``) so IDE autocomplete and
        mypy can verify call sites. Every option is forwarded to
        :meth:`start`.

        :param callback: A callback function to run when connected
        :param process_connect_events: Whether to process initial events sent on room join
        :param compress_ws_events: Whether to compress WebSocket events using gzip
        :param fetch_room_info: Whether to fetch room info on join
        :param fetch_gift_info: Whether to fetch gift info on join
        :param fetch_live_check: Whether to check if the user is live
        :param room_id: Optional override to skip room scraping
        :return: The task, once it's finished

        """

        task: Task = await self.start(
            process_connect_events=process_connect_events,
            compress_ws_events=compress_ws_events,
            fetch_room_info=fetch_room_info,
            fetch_gift_info=fetch_gift_info,
            fetch_live_check=fetch_live_check,
            room_id=room_id,
        )

        try:
            if inspect.iscoroutinefunction(callback):
                self._asyncio_loop.create_task(callback())
            elif inspect.isawaitable(callback):
                self._asyncio_loop.create_task(callback)
            elif inspect.isfunction(callback):
                callback()
            await task
        except (CancelledError, KeyboardInterrupt) as ex:

            if isinstance(ex, CancelledError):
                self._logger.debug("The client has been manually stopped with 'client.stop()'.")

            if isinstance(ex, KeyboardInterrupt):
                self._logger.info("KeyboardInterrupt: shutting down cleanly.")

            self._clean_tasks()

        return task

    def _clean_tasks(self) -> None:
        """
        Clean up on aisle task

        """

        self._asyncio_loop.run_until_complete(self.disconnect())

        pending = [t for t in asyncio.all_tasks(self._asyncio_loop) if not t.done()]
        for task in pending:
            task.cancel()

        if pending:
            self._asyncio_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

    def run(
            self,
            *,
            process_connect_events: bool = True,
            compress_ws_events: bool = True,
            fetch_room_info: bool = False,
            fetch_gift_info: bool = False,
            fetch_live_check: bool = True,
            room_id: Optional[int] = None,
    ) -> Task:
        """
        Start a thread-blocking connection to TikTokLive.

        Mirrors :meth:`connect` / :meth:`start`'s kwargs explicitly so IDEs
        autocomplete and type-check the same options.

        :param process_connect_events: Whether to process initial events sent on room join
        :param compress_ws_events: Whether to compress WebSocket events using gzip
        :param fetch_room_info: Whether to fetch room info on join
        :param fetch_gift_info: Whether to fetch gift info on join
        :param fetch_live_check: Whether to check if the user is live
        :param room_id: Optional override to skip room scraping
        :return: The task, once it's finished

        """

        connect_coro = self.connect(
            process_connect_events=process_connect_events,
            compress_ws_events=compress_ws_events,
            fetch_room_info=fetch_room_info,
            fetch_gift_info=fetch_gift_info,
            fetch_live_check=fetch_live_check,
            room_id=room_id,
        )

        # KeyboardInterrupt has to be caught here, not inside ``connect()`` —
        # when Ctrl+C fires while the loop is parked in ``selector.select``,
        # only this synchronous frame is on the call stack. The suspended
        # ``connect`` coroutine is owned by the loop and never sees the
        # exception. ``_clean_tasks`` runs ``disconnect`` + cancels and
        # drains pending tasks so websockets' close handshake and the ping
        # loop don't die mid-await.
        try:
            return self._asyncio_loop.run_until_complete(connect_coro)
        except KeyboardInterrupt:
            self._logger.info("KeyboardInterrupt: shutting down cleanly.")
            self._clean_tasks()
            raise

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
        self._clean_tasks()

    # Liskov overrides of pyee.EventEmitter.on/add_listener: pyee keys events
    # by string; we accept an Event class and convert internally via
    # event.get_type(). The deviation is deliberate — class-based subscription
    # is the documented public API. ``@overload``s keep the decorator branch
    # (``@client.on(ConnectEvent)``) typed as ``Callable[[handler], handler]``
    # so the inner async function checks against pyee's TypeVars cleanly.
    # ``# noinspection PyMethodOverriding`` silences PyCharm's separate
    # signature-mismatch inspector (mypy uses ``# type: ignore[override]``).
    # noinspection PyMethodOverriding
    @overload  # type: ignore[override]
    def on(self, event: Type[Event], f: EventHandler) -> Handler:  # type: ignore[type-var,misc]
        ...  # type: ignore[type-var,misc,unused-ignore]

    # noinspection PyMethodOverriding
    @overload
    def on(self, event: Type[Event]) -> Callable[[EventHandler], EventHandler]:
        ...

    # noinspection PyMethodOverriding
    def on(
            self,
            event: Type[Event],
            f: Optional[EventHandler] = None,
    ) -> Union[Handler, Callable[[EventHandler], EventHandler]]:
        """
        Decorator that can be used to register a Python function as an event listener

        :param event: The event to listen to
        :param f: The function to handle the event
        :return: The wrapped function as a generated `pyee.Handler` object

        """

        return super(TikTokLiveClient, self).on(event.get_type(), f)  # type: ignore[type-var,return-value]

    # noinspection PyMethodOverriding
    def add_listener(  # type: ignore[override]
            self,
            event: Type[Event],
            f: EventHandler,
    ) -> Handler:  # type: ignore[type-var,misc]
        """
        Method that can be used to register a Python function as an event listener

        :param event: The event to listen to
        :param f: The function to handle the event
        :return: The generated `pyee.Handler` object

        """

        return super().add_listener(event=event.get_type(), f=f)  # type: ignore[return-value]

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

        # By this point ``start`` has resolved the room ID; mypy can't follow.
        assert self._room_id is not None

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
                self._logger.debug(f"Received Event '{event.get_type()}' [{event.size} bytes]")
                self.emit(event.get_type(), event)

        # Send the Disconnect event when we disconnect
        ev: DisconnectEvent = DisconnectEvent()
        self.emit(ev.get_type(), ev)

    async def _parse_webcast_response(self, webcast_response: ProtoMessageFetchResult) -> AsyncIterator[Event]:
        """
        Parse incoming webcast responses into events that can be emitted

        :param webcast_response: The ProtoMessageFetchResult protobuf message
        :return: A list of events that can be gleamed from this event

        """

        # The first event means we connected
        if webcast_response.is_first:
            assert self._room_id is not None
            yield ConnectEvent(unique_id=self._unique_id, room_id=self._room_id)

        # Yield events
        for message in webcast_response.messages:
            for event in await self._parse_webcast_response_message(
                    webcast_response=webcast_response,
                    webcast_response_message=message,
            ):
                if event is not None:
                    yield event

    async def _parse_webcast_response_message(
            self,
            webcast_response: ProtoMessageFetchResult,
            webcast_response_message: Optional[ProtoMessageFetchResultBaseProtoMessage],
    ) -> List[Event]:
        """
        Parse incoming webcast responses into events that can be emitted

        :param webcast_response_message: The ProtoMessageFetchResultMessage protobuf message
        :return: A list of events that can be gleamed from this event

        """

        # Invalid response handler
        if webcast_response_message is None:
            self._logger.warning("Received a null ProtoMessageFetchResultMessage from the Webcast server.")
            return []

        # ``EVENT_MAPPINGS`` is annotated as ``Dict[str, Type[BaseEvent]]`` for
        # the codegen template's sake; every value is in fact a ProtoEvent
        # subclass, so the cast at use-time is honest.
        event_type: Optional[Type[ProtoEvent]] = (
            EVENT_MAPPINGS.get(webcast_response_message.method)  # type: ignore[assignment]
        )
        # ``WebsocketResponseEvent`` carries the outer fetch result by
        # composition (``raw``); subscribers can inspect cursor, ws_params,
        # the full message list, etc. through that field.
        response_event: Event = WebsocketResponseEvent(raw=webcast_response)

        # If the event is not tracked, return
        if event_type is None:
            return [response_event, UnknownEvent(raw=webcast_response)]

        # Get the underlying events
        try:
            proto_event: ProtoEvent = event_type().parse(webcast_response_message.payload)
        except Exception as ex:
            # Known upstream-schema bugs are demoted to DEBUG so they don't
            # drown the operator's log. Match by substring against the
            # error's str() representation.
            ex_repr = str(ex)
            is_known_schema_bug = any(token in ex_repr for token in self.parse_error_ignorelist)

            if is_known_schema_bug:
                self._logger.debug(
                    "Skipped %s payload (known upstream schema mismatch): %s",
                    webcast_response_message.method,
                    ex.__class__.__name__,
                )
            elif not self.ignore_broken_payload:
                # Truncate raw bytes preview so a single 8KB payload doesn't
                # blow up the log; full traceback is in exc_info.
                self._logger.error(
                    "Failed to parse %s payload (%d bytes); raw=%s",
                    webcast_response_message.method,
                    len(webcast_response_message.payload or b""),
                    _truncate_payload(webcast_response_message.payload),
                    exc_info=True,
                )
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

    async def get_avatar_url(
            self,
            unique_id: str | int | None = None,
    ) -> Optional[str]:
        """
        Fetch the profile avatar URL for a user by their unique_id.

        This uses the public profile HTML (same source as visiting
        https://www.tiktok.com/@username in a browser) and parses
        the CDN avatar URL from it.

        Args:
            unique_id: Optional override; defaults to this client's unique_id.

        Returns:
            CDN avatar URL string, or None if it could not be found.
        """

        # Resolve ID the same way other helpers do
        resolved = await self._resolve_user_id(unique_id or self.unique_id)
        profile_url = f"https://www.tiktok.com/@{resolved}"

        # Use the existing web client so headers / cookies / proxies are reused
        response = await self._web.get(
            url=profile_url,
            # We don't need signed params here just basically like just raw HTML
            base_params=False,
            base_headers=False,
            extra_headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        )

        html = response.text

        # Match the JSON-encoded avatar field used on profile pages:
        #   "avatarLarger":"https:\/\/...tiktokcdn...jpeg"
        match = re.search(r'"avatarLarger":"([^"]+)"', html)
        if not match:
            return None

        raw = match.group(1)
        # TikTok often encodes "/" as "\u002F" in this JSON blob
        avatar_url = raw.replace(r"\\u002F", "/")
        avatar_url = unescape(avatar_url)
        return avatar_url

    async def handle_custom_event(self, response: ProtoMessageFetchResultBaseProtoMessage, event: ProtoEvent) -> \
            Optional[CustomEvent]:
        """
        Extract CustomEvent events from existing ProtoEvent events

        :param response: The ProtoMessageFetchResultMessage to parse for the custom event
        :param event: The ProtoEvent to parse for the custom event
        :return: The event, if one exists

        """

        # SuperFanEvent / SuperFanJoinEvent — rooted in BarrageMessage. The
        # marker can land on either ``content.display_type`` or
        # ``common_barrage_content.display_type``, so we scan both. The more
        # specific ``ttlive_superfan_commentnotif_superfanjoined`` is checked
        # first; everything else carrying ``ttlive_superfan`` is the generic
        # "became a super fan" event. Mirrors the JS connector exactly.
        if isinstance(event, BarrageEvent):
            display_types = [
                dt.lower()
                for dt in (
                    getattr(event.content, "display_type", None),
                    getattr(event.common_barrage_content, "display_type", None),
                )
                if isinstance(dt, str) and dt
            ]
            if any("ttlive_superfan_commentnotif_superfanjoined" in dt for dt in display_types):
                return SuperFanJoinEvent().parse(response.payload)
            if any("ttlive_superfan" in dt for dt in display_types):
                return SuperFanEvent().parse(response.payload)

        # SuperFanBoxEvent — envelope variant. Match either the displayType
        # marker or the explicit business_type enum, mirroring the JS connector.
        # v3 dropped the named ``BusinessTypeSuperFanBox`` variant from the
        # enum, but the wire value (19) is unchanged; compare numerically.
        if isinstance(event, EnvelopeEvent):
            envelope_dt = common_display_type(event.common).lower()
            business_type = getattr(event.envelope_info, "business_type", None)
            if (
                    "ttlive_superfanbox" in envelope_dt
                    or (business_type is not None and int(business_type) == 19)
            ):
                return SuperFanBoxEvent().parse(response.payload)

        # LiveEndEvent, LivePauseEvent, LiveUnpauseEvent
        if isinstance(event, ControlEvent):
            if event.action in {
                ControlAction.STREAM_ENDED,
                ControlAction.STREAM_SUSPENDED,
            }:
                # If the stream is over, disconnect the client. Can't await due to circular dependency.
                self._asyncio_loop.create_task(self.disconnect())
                return LiveEndEvent().parse(response.payload)
            elif event.action == ControlAction.STREAM_PAUSED:
                return LivePauseEvent().parse(response.payload)
            elif event.action == ControlAction.STREAM_UNPAUSED:
                return LiveUnpauseEvent().parse(response.payload)
            return None

        # FollowEvent / ShareEvent — keyed off the common display-text marker.
        common_dt = common_display_type(event.common)
        if "follow" in common_dt:
            return FollowEvent().parse(response.payload)
        if "share" in common_dt:
            return ShareEvent().parse(response.payload)

        # Not a custom event
        return None

    async def _resolve_user_id(self, unique_id: str | int) -> str:
        """Resolve a unique_id and return the resolved value"""
        parsed_id = self.parse_unique_id(unique_id)
        if parsed_id.isdigit() and self._is_user_id:
            resolved_id = await self._web.fetch_user_unique_id(int(parsed_id))
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
