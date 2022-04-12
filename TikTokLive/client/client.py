from typing import Optional, Type

from dacite import from_dict
from pyee import AsyncIOEventEmitter

from .base import BaseClient
from ..proto.utilities import from_dict_plus
from ..types import events
from ..types.events import AbstractEvent, ViewerCountUpdateEvent, CommentEvent, LiveEndEvent, GiftEvent, QuestionEvent, UnknownEvent, ConnectEvent, DisconnectEvent


class TikTokLiveClient(AsyncIOEventEmitter, BaseClient):
    """
    TikTokLive Client responsible for emitting events asynchronously

    """

    def __init__(self, unique_id: str, debug: bool = False, **options):
        """

        :param unique_id: The unique id of the creator to connect to
        :param debug: Debug mode -> Add all events' raw payload to a "debug" event
        :param options: Extra options from the BaseClient

        """

        self.debug_enabled: bool = debug

        BaseClient.__init__(self, unique_id, **options)
        AsyncIOEventEmitter.__init__(self, self.loop)
            
    async def _connect(self) -> str:
        """
        Wrap connection in a connect event

        """

        result: str = await super(TikTokLiveClient, self)._connect()

        if self.connected:
            event: ConnectEvent = ConnectEvent()
            self.emit(event.name, event)

        return result

    def _disconnect(self) -> None:
        """
        Wrap disconnection in a disconnect event

        """

        super(TikTokLiveClient, self)._disconnect()

        if not self.connected:
            event: DisconnectEvent = DisconnectEvent()
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

        # Comment
        if webcast_message["type"] == "WebcastChatMessage":
            return from_dict_plus(
                CommentEvent,
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

        # Question
        if webcast_message["type"] == "WebcastQuestionNewMessage":
            return from_dict_plus(
                QuestionEvent,
                webcast_message.get("questionDetails")
            )

        # We haven't implemented deserialization for it yet, or it doesn't have a model
        event: UnknownEvent = UnknownEvent()
        event._as_dict = webcast_message
        return event
