import json
from typing import Optional, Type

from dacite import from_dict
from pyee import AsyncIOEventEmitter

from .base import BaseClient
from ..types import events
from ..types.events import AbstractEvent, ViewerCountUpdateEvent, CommentEvent, LiveEndEvent, GiftEvent, QuestionEvent, UnknownEvent, ConnectEvent, DisconnectEvent


class TikTokLiveClient(AsyncIOEventEmitter, BaseClient):

    def __init__(self, unique_id: str, debug: bool = False, **options):
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
            self._disconnect()
            return LiveEndEvent()

        # Gift Received
        gift: Optional[str] = webcast_message.get("giftJson")
        if gift:
            del webcast_message["giftJson"]
            webcast_message["gift"] = json.loads(gift)
            event: GiftEvent = from_dict(GiftEvent, webcast_message)
            event.gift.extended_gift = self.available_gifts.get(event.gift.gift_id)
            event._as_dict = webcast_message
            return event

        # Question Received
        question: Optional[dict] = webcast_message.get("questionDetails")
        if question:
            event: QuestionEvent = from_dict(QuestionEvent, question)
            event._as_dict = question
            return event

        # We haven't implemented deserialization for it yet, or it doesn't have a model
        event: UnknownEvent = UnknownEvent()
        event._as_dict = webcast_message
        return event
