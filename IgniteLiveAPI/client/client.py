import asyncio
import inspect
import logging
import re
from asyncio import AbstractEventLoop, Task, CancelledError
from html import unescape
from logging import Logger
from typing import Optional, Type, Dict, Any, Union, Callable, List, Coroutine, AsyncIterator, overload

import httpx
from python_socks import ProxyError
from websockets.exceptions import WebSocketException
from TikTokLiveProto.v3.webcast.model.data import EnvelopeBusinessType
from pyee.asyncio import AsyncIOEventEmitter
from pyee.base import Handler

from IgniteLiveAPI.client.errors import AlreadyConnectedError, UserOfflineError, IdleTimeoutError, ReconnectFailedError, \
    WebcastBlockedError, InitialCursorMissingError, WebsocketURLMissingError, SignAPIError, SignatureRateLimitError, \
    PremiumEndpointError, AuthenticatedWebSocketConnectionError
from IgniteLiveAPI.client.logger import IgniteLiveLogHandler, LogLevel
from IgniteLiveAPI.client.reconnect import ReconnectPolicy
from IgniteLiveAPI.client.web.routes.fetch_is_live import MissingRoomIdInResponse
from IgniteLiveAPI.client.web.routes.fetch_signed_websocket import WebcastPlatform
from IgniteLiveAPI.client.web.routes.fetch_user_unique_id import FailedResolveUserId
from IgniteLiveAPI.client.web.web_client import TikTokWebClient
from IgniteLiveAPI.client.web.web_settings import WebDefaults
from IgniteLiveAPI.client.ws.ws_client import WebcastWSClient
from IgniteLiveAPI.client.ws.ws_connect import WebcastProxy
from IgniteLiveAPI.events import Event, EventHandler, ControlEvent
from IgniteLiveAPI.events.custom_events import WebsocketResponseEvent, FollowEvent, ShareEvent, LiveEndEvent, \
    DisconnectEvent, ReconnectEvent, LivePauseEvent, LiveUnpauseEvent, UnknownEvent, CustomEvent, ConnectEvent, SuperFanEvent, \
    SuperFanJoinEvent, SuperFanBoxEvent
from IgniteLiveAPI.events.proto_events import EVENT_MAPPINGS, ProtoEvent, BarrageEvent, EnvelopeEvent
from IgniteLiveAPI.proto import ProtoMessageFetchResult, ProtoMessageFetchResultBaseProtoMessage
from IgniteLiveAPI.proto.custom_proto import ControlAction
from IgniteLiveAPI.proto.proto_utils import common_display_type

# Default fingerprints of parse failures rooted in upstream proto schema
# bugs. These are substring-matched against the exception's ``str(...)`` and
# any matching parse error is logged at DEBUG instead of ERROR. Clients can
# extend the list at runtime via ``client.parse_error_ignorelist``.
#
# v3 fixed the v2-era ``LinkLayerListUser.linkmic_id`` int64-vs-string bug,
# so the list starts empty. Add new fingerprints here as upstream schema
# regressions surface.
DEFAULT_PARSE_ERROR_IGNORELIST: List[str] = []

# Failures that mean "the network or TikTok hiccupped, try again", as opposed to "retrying cannot help".
# Order matters: FATAL is checked first because several of its members subclass retryable types
# (e.g. PremiumEndpointError is a SignAPIError).
_FATAL_RECONNECT_ERRORS = (
    WebcastBlockedError,  # TikTok detected the client; hammering it makes the block worse
    PremiumEndpointError,  # The sign provider refuses this key / route, so it will refuse again
    AuthenticatedWebSocketConnectionError,  # Session-ID safety check; a configuration problem
    UserOfflineError,
)
_RETRYABLE_RECONNECT_ERRORS = (
    IdleTimeoutError,
    WebSocketException,  # ConnectionClosed, InvalidHandshake, ...
    OSError,  # Includes ConnectionError & TimeoutError
    asyncio.TimeoutError,
    httpx.TransportError,
    ProxyError,
    SignAPIError,
    InitialCursorMissingError,
    WebsocketURLMissingError,
    MissingRoomIdInResponse,  # fetch_is_live reports any failure of the check as this
)

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


class IgniteLiveClient(AsyncIOEventEmitter):
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
        Instantiate the IgniteLiveClient client

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

        self._logger: Logger = IgniteLiveLogHandler.get_logger(
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

        # Reconnect supervisor state
        self._stop_requested: bool = False
        self._wake: Optional[asyncio.Event] = None
        self._live_check_on_reconnect: bool = True

    @staticmethod
    async def _none() -> None:
        """Awaitable placeholder for an optional fetch that was not requested"""
        return None

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
            reconnect: Union[bool, ReconnectPolicy] = False,
            idle_timeout: Optional[float] = None,
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
        :param reconnect: ``True`` (default policy) or a :class:`ReconnectPolicy` to automatically reconnect, with
                          exponential backoff, when the connection drops. Off by default.
        :param idle_timeout: Drop (and, with ``reconnect``, replace) a connection that receives no frames for this many
                             seconds. Off by default.
        :return: Task containing the heartbeat of the client

        Note: ``fetch_room_info`` / ``fetch_gift_info`` run concurrently with the signed WebSocket request. If one of
        them fails, the sign request has already been made (and counts against your sign-server rate limit).

        """

        if self._ws.connected:
            raise AlreadyConnectedError("You can only make one connection per client!")

        policy: Optional[ReconnectPolicy] = self._resolve_reconnect_policy(reconnect)
        if idle_timeout is not None and idle_timeout <= 0:
            raise ValueError("idle_timeout must be a positive number of seconds, or None to disable the watchdog")

        self._stop_requested = False
        self._wake = asyncio.Event()
        self._live_check_on_reconnect = fetch_live_check

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

        # The room info, gift list & signed WebSocket fetches are independent of each other, so run them
        # concurrently over the pooled connections instead of paying their round trips back-to-back.
        # (Signed WebSocket URLs also expire quickly, so spending less time before connecting helps.)
        # ``return_exceptions`` lets every request settle first; errors are then raised in the same
        # order the sequential version surfaced them: room info, gift list, then the signature.
        room_info_result, gift_info_result, initial_webcast_response = await asyncio.gather(
            self._web.fetch_room_info() if fetch_room_info else self._none(),
            self._web.fetch_gift_list() if fetch_gift_info else self._none(),
            self._web.fetch_signed_websocket(self._ws_platform),
            return_exceptions=True
        )

        for result in (room_info_result, gift_info_result, initial_webcast_response):
            if isinstance(result, BaseException):
                raise result

        if fetch_room_info:
            self._room_info = room_info_result

        if fetch_gift_info:
            self._gift_info = gift_info_result

        # Start the websocket connection & return it
        self._event_loop_task = self._asyncio_loop.create_task(
            self._ws_client_loop(
                initial_webcast_response=initial_webcast_response,
                process_connect_events=process_connect_events,
                compress_ws_events=compress_ws_events,
                reconnect=policy,
                idle_timeout=idle_timeout
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
            reconnect: Union[bool, ReconnectPolicy] = False,
            idle_timeout: Optional[float] = None,
    ) -> Task:
        """
        Start a future-blocking connection to IgniteLiveAPI.

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
        :param reconnect: ``True`` or a :class:`ReconnectPolicy` to reconnect automatically when the connection drops
        :param idle_timeout: Seconds without any frame before the connection is considered dead
        :return: The task, once it's finished

        """

        task: Task = await self.start(
            process_connect_events=process_connect_events,
            compress_ws_events=compress_ws_events,
            fetch_room_info=fetch_room_info,
            fetch_gift_info=fetch_gift_info,
            fetch_live_check=fetch_live_check,
            room_id=room_id,
            reconnect=reconnect,
            idle_timeout=idle_timeout,
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
            reconnect: Union[bool, ReconnectPolicy] = False,
            idle_timeout: Optional[float] = None,
    ) -> Task:
        """
        Start a thread-blocking connection to IgniteLiveAPI.

        Mirrors :meth:`connect` / :meth:`start`'s kwargs explicitly so IDEs
        autocomplete and type-check the same options.

        :param process_connect_events: Whether to process initial events sent on room join
        :param compress_ws_events: Whether to compress WebSocket events using gzip
        :param fetch_room_info: Whether to fetch room info on join
        :param fetch_gift_info: Whether to fetch gift info on join
        :param fetch_live_check: Whether to check if the user is live
        :param room_id: Optional override to skip room scraping
        :param reconnect: ``True`` or a :class:`ReconnectPolicy` to reconnect automatically when the connection drops
        :param idle_timeout: Seconds without any frame before the connection is considered dead
        :return: The task, once it's finished

        """

        connect_coro = self.connect(
            process_connect_events=process_connect_events,
            compress_ws_events=compress_ws_events,
            fetch_room_info=fetch_room_info,
            fetch_gift_info=fetch_gift_info,
            fetch_live_check=fetch_live_check,
            room_id=room_id,
            reconnect=reconnect,
            idle_timeout=idle_timeout,
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

        # Tell the reconnect supervisor this is intentional & wake it if it is sleeping between attempts
        self._stop_requested = True
        if self._wake is not None:
            self._wake.set()

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

        return super(IgniteLiveClient, self).on(event.get_type(), f)  # type: ignore[type-var,return-value]

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

    @staticmethod
    def _resolve_reconnect_policy(reconnect: Union[bool, ReconnectPolicy, None]) -> Optional[ReconnectPolicy]:
        """Normalise the ``reconnect`` argument: ``False``/``None`` -> off, ``True`` -> defaults, or a policy as given"""

        if isinstance(reconnect, ReconnectPolicy):
            return reconnect
        return ReconnectPolicy() if reconnect else None

    @property
    def _stopping(self) -> bool:
        """Whether ``disconnect()`` has been called. A property so checks after an ``await`` are not narrowed away."""

        return self._stop_requested

    @staticmethod
    def _is_retryable(ex: BaseException) -> bool:
        """Whether a reconnect might recover from this failure"""

        if isinstance(ex, _FATAL_RECONNECT_ERRORS):
            return False
        return isinstance(ex, _RETRYABLE_RECONNECT_ERRORS)

    @staticmethod
    def _describe_failure(ex: Optional[BaseException]) -> str:
        """Short, log-friendly summary of why a connection or attempt ended"""

        if ex is None:
            return "connection closed"
        return f"{type(ex).__name__}: {ex}"[:200]

    async def _sleep_unless_stopped(self, delay: float) -> bool:
        """
        Sleep between reconnect attempts, waking early if ``disconnect()`` is called.

        :return: Whether a stop was requested

        """

        if self._wake is not None and not self._stop_requested:
            try:
                await asyncio.wait_for(self._wake.wait(), timeout=delay)
            except asyncio.TimeoutError:
                pass

        return self._stop_requested

    async def _prepare_reconnect(self, room_id: int) -> Optional[ProtoMessageFetchResult]:
        """
        Everything a new connection needs: confirm the stream is still live and get a freshly signed response.
        The room ID is reused; it does not change while the same stream is running.

        :return: The initial response, or ``None`` if the stream is over (or the client was stopped meanwhile)

        """

        if self._live_check_on_reconnect and not await self._web.fetch_is_live(room_id=room_id):
            return None

        response: ProtoMessageFetchResult = await self._web.fetch_signed_websocket(self._ws_platform)
        return None if self._stop_requested else response

    async def _ws_client_loop(
            self,
            initial_webcast_response: ProtoMessageFetchResult,
            process_connect_events: bool,
            compress_ws_events: bool,
            reconnect: Optional[ReconnectPolicy] = None,
            idle_timeout: Optional[float] = None
    ) -> None:
        """
        Supervise the connection: run it, and, if a ``reconnect`` policy is set, replace it when it drops.

        Without a policy this is exactly one connection: failures propagate and a normal close emits ``DisconnectEvent``.
        With a policy, retryable failures (and unrequested clean closes) trigger a backoff, a live check, a fresh signature
        and a new connection, emitting ``ReconnectEvent`` before each attempt. The loop ends, emitting ``DisconnectEvent``,
        when ``disconnect()`` is called or the stream is over; it raises ``ReconnectFailedError`` when the attempt budget runs
        out, and re-raises failures that retrying cannot fix (e.g. ``WebcastBlockedError``).

        :param initial_webcast_response: The ProtoMessageFetchResult retrieved from the sign server with connection info
        :param process_connect_events: Whether to process initial events sent on room join (first connection only)
        :param compress_ws_events: Whether to compress the WebSocket events using gzip compression
        :param reconnect: The reconnect policy, or ``None`` for a single connection
        :param idle_timeout: Seconds without any frame before a connection is considered dead
        :return: None

        """

        # By this point ``start`` has resolved the room ID; mypy can't follow.
        assert self._room_id is not None
        room_id: int = self._room_id
        loop: AbstractEventLoop = asyncio.get_running_loop()

        response: ProtoMessageFetchResult = initial_webcast_response
        attempt: int = 0

        while True:
            started_at: float = loop.time()
            failure: Optional[Exception] = None

            try:
                await self._run_connection(
                    initial_webcast_response=response,
                    process_connect_events=process_connect_events,
                    compress_ws_events=compress_ws_events,
                    idle_timeout=idle_timeout
                )
            except Exception as ex:
                if reconnect is None or not self._is_retryable(ex):
                    raise
                failure = ex

            if reconnect is None or self._stop_requested:
                break

            # A connection that stayed healthy for a while earns a fresh attempt budget
            if loop.time() - started_at >= reconnect.stable_after:
                attempt = 0

            next_response: Optional[ProtoMessageFetchResult] = None
            while next_response is None:
                attempt += 1

                if reconnect.exhausted(attempt):
                    raise ReconnectFailedError(
                        f"Gave up reconnecting to {self._unique_id} after {reconnect.max_attempts} attempts. "
                        f"Last failure: {self._describe_failure(failure)}"
                    ) from failure

                delay: float = reconnect.delay(attempt)
                if isinstance(failure, SignatureRateLimitError):
                    try:
                        delay = max(delay, float(failure.retry_after))
                    except Exception:
                        pass  # Missing / malformed rate-limit headers: fall back to the backoff delay

                reason: str = self._describe_failure(failure)
                self._logger.warning(f"Connection lost ({reason}). Reconnecting in {delay:.1f}s (attempt {attempt}).")
                ev: ReconnectEvent = ReconnectEvent(attempt=attempt, delay=delay, reason=reason)
                self.emit(ev.get_type(), ev)

                if await self._sleep_unless_stopped(delay):
                    break

                try:
                    next_response = await self._prepare_reconnect(room_id)
                except Exception as ex:
                    if self._stopping:
                        break
                    if not self._is_retryable(ex):
                        raise
                    failure = ex
                    continue

                # ``None``: the stream ended while we were away (or we were stopped); nothing to reconnect to
                if next_response is None:
                    break

            if next_response is None:
                break

            response = next_response

            # The history replayed on join would duplicate events the caller already handled
            process_connect_events = False

        # Send the Disconnect event when we disconnect
        ev_disconnect: DisconnectEvent = DisconnectEvent()
        self.emit(ev_disconnect.get_type(), ev_disconnect)

    async def _run_connection(
            self,
            initial_webcast_response: ProtoMessageFetchResult,
            process_connect_events: bool,
            compress_ws_events: bool,
            idle_timeout: Optional[float]
    ) -> None:
        """
        Run ONE websocket connection to completion, emitting its events

        :param initial_webcast_response: The ProtoMessageFetchResult retrieved from the sign server with connection info
        :param process_connect_events: Whether to process initial events sent on room join
        :param compress_ws_events: Whether to compress the WebSocket events using gzip compression
        :param idle_timeout: Seconds without any frame before the connection is considered dead
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
                user_agent=self._web.headers['User-Agent'],
                idle_timeout=idle_timeout
        ):

            # Iterate over the events extracted
            async for event in self._parse_webcast_response(webcast_response):
                self._logger.debug(f"Received Event '{event.get_type()}' [{event.size} bytes]")
                self.emit(event.get_type(), event)

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

            business_type_match = business_type and business_type == EnvelopeBusinessType.SUPER_FAN_BOX

            # noinspection SpellCheckingInspection
            if "ttlive_superfanbox" in envelope_dt or business_type_match:
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
        Return the loop owned by this client.

        Caches a single loop on the instance so the synchronous
        ``run`` / ``_clean_tasks`` shutdown path reuses the loop that
        owns the websocket / ping tasks. Without this, each access in
        a non-running context would mint a fresh loop, and tasks
        created on the original would error with
        ``RuntimeError: ... attached to a different loop`` during
        Ctrl+C teardown.

        :return: An asyncio event loop

        """

        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            pass

        cached = getattr(self, "_owned_asyncio_loop", None)
        if cached is None or cached.is_closed():
            cached = asyncio.new_event_loop()
            self._owned_asyncio_loop = cached
        return cached

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
        The internal logger used by IgniteLiveAPI

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
