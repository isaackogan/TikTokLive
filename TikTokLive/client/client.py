import logging
import traceback
from typing import Optional, Type, Callable

from dacite import from_dict

from .base import BaseClient
from ..proto.utilities import from_dict_plus
from ..types import events
from ..types.events import AbstractEvent, ViewerCountUpdateEvent, CommentEvent, LiveEndEvent, GiftEvent, QuestionEvent, UnknownEvent, ConnectEvent, DisconnectEvent, EmoteEvent, EnvelopeEvent, \
    SubscribeEvent, WeeklyRankingEvent, MicBattleEvent, MicArmiesEvent


class TikTokLiveClient(BaseClient):
    """
    TikTokLive Client responsible for emitting events asynchronously

    """

    def __init__(self, unique_id: str, debug: bool = False, **options):
        """
        Initialize the BaseClient for TikTokLive Webcast tracking

        :param unique_id: The unique id of the creator to connect to
        :param debug: Debug mode -> Add all events' raw payload to a "debug" event
        :param options: Extra options from the BaseClient

        """

        self.debug_enabled: bool = debug
        self._session_id: Optional[str] = None
        BaseClient.__init__(self, unique_id, **options)

    async def _on_error(self, original: Exception, append: Optional[Exception]) -> None:
        """
        Send errors to the _on_error handler for handling, appends a custom exception

        :param original: The original Python exception
        :param append: The specific exception
        :return: None

        """

        _exc = original

        # If adding on to it
        if append is not None:
            try:
                raise append from original
            except Exception as ex:
                _exc = ex

        # If not connected, just raise it
        if not self.connected:
            raise _exc

        # If connected, no handler
        if len(self.listeners("error")) < 1:
            self._log_error(_exc)
            return

        # If connected, has handler
        self.emit("error", _exc)

    @classmethod
    def _log_error(cls, exception: Exception) -> None:
        """
        Log an error

        :param exception: The exception
        :return: None

        """

        try:
            raise exception
        except:
            logging.error(traceback.format_exc())
        return

    async def _connect(self, session_id: str = None) -> int:
        """
        Wrap connection in a connect event

        """

        self._session_id = session_id
        room_id: int = await super(TikTokLiveClient, self)._connect(session_id=self._session_id)

        if self.connected:
            event: ConnectEvent = ConnectEvent()
            self.emit(event.name, event)

        return room_id

    async def reconnect(self) -> int:
        """
        Add the ability to reconnect the client

        """

        return await self._connect(self._session_id)

    def _disconnect(self, webcast_closed: bool = False) -> None:
        """
        Wrap disconnection in a disconnect event

        """

        super(TikTokLiveClient, self)._disconnect(webcast_closed=webcast_closed)

        if not self.connected:
            event: DisconnectEvent = DisconnectEvent(webcast_closed=webcast_closed)
            self.emit(event.name, event)

    async def _handle_webcast_messages(self, webcast_response: dict) -> None:
        """
        Handle webcast messages using an event emitter
        :param webcast_response: The response

        """

        for message in webcast_response.get("messages", list()):
            response: Optional[AbstractEvent] = self.__parse_message(webcast_message=message)

            if isinstance(response, AbstractEvent):
                self.emit(response.name, response)

            if self.debug_enabled:
                self.emit("debug", AbstractEvent(data=message))

    def __parse_message(self, webcast_message: dict) -> Optional[AbstractEvent]:
        """
        Parse a webcast message into an event and return to the caller

        :param webcast_message: The message to parse
        :return: The parsed object of base-type AbstractEvent

        """

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
        if webcast_message["type"] == "WebcastRoomUserSeqMessage":
            count: Optional[int] = webcast_message.get("viewerCount")
            self._viewer_count = count if count is not None else self._viewer_count

            return from_dict_plus(
                ViewerCountUpdateEvent,
                webcast_message
            )

        # Live ended
        action: Optional[int] = webcast_message.get("action")
        if action is not None and action == 3:
            self._disconnect()
            return LiveEndEvent()

        # Gift Handling
        if webcast_message["type"] == "WebcastGiftMessage":
            webcast_message["gift"] = webcast_message
            event: GiftEvent = from_dict(GiftEvent, webcast_message)
            event.gift.extended_gift = self.available_gifts.get(event.gift.giftId)
            event._as_dict = webcast_message
            return event

        # Envelope Event
        if webcast_message["type"] == "WebcastEnvelopeMessage":
            try:
                webcast_message["treasureBoxUser"] = webcast_message["treasureBoxUser"]["user2"]["user3"][0]["user4"]["user"]
            except:
                webcast_message["treasureBoxUser"] = None

            return from_dict_plus(
                EnvelopeEvent,
                webcast_message
            )

        standard: Optional[Callable] = {
            "WebcastChatMessage": lambda: from_dict_plus(CommentEvent, webcast_message),  # Comment
            "WebcastEmoteChatMessage": lambda: from_dict_plus(EmoteEvent, webcast_message),  # Emote
            "WebcastQuestionNewMessage": lambda: from_dict_plus(QuestionEvent, webcast_message.get("questionDetails")),  # Q&A Question
            "WebcastHourlyRankMessage": lambda: from_dict_plus(WeeklyRankingEvent, webcast_message),  # Hourly Ranking
            "WebcastLinkMicBattle": lambda: from_dict_plus(MicBattleEvent, webcast_message),  # Mic Battle (Battle Start)
            "WebcastLinkMicArmies": lambda: from_dict_plus(MicArmiesEvent, webcast_message),  # Mic Armies (Battle Update)
            "WebcastSubNotifyMessage": lambda: from_dict_plus(SubscribeEvent, webcast_message)  # Subscribe Event
        }.get(webcast_message["type"], lambda ev=UnknownEvent(): ev.set_as_dict(webcast_message))  # Unknown Event

        return standard()
