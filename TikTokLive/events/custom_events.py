from __future__ import annotations

from dataclasses import dataclass
from typing import Type, Union, Optional

from TikTokLive.events.base_event import BaseEvent
from TikTokLive.events.proto_events import SocialEvent, ControlEvent
from TikTokLive.proto import WebcastResponseMessage


@dataclass()
class UnknownEvent(WebcastResponseMessage, BaseEvent):
    pass


@dataclass()
class ConnectEvent(BaseEvent):
    """
    Manually thrown whenever a connection is started

    """

    unique_id: str
    room_id: str


@dataclass()
class DisconnectEvent(BaseEvent):
    pass


@dataclass()
class LiveEndEvent(ControlEvent):
    """
    Thrown when the stream ends

    """


class FollowEvent(SocialEvent):
    """
    A SocialEvent, but we give it its own class for clarity's sake.

    """


class ShareEvent(SocialEvent):
    """
    A SocialEvent, but we give it its own class for clarity's sake.

    """

    @property
    def users_joined(self) -> Optional[int]:
        """
        The number of people that have joined the stream from the share

        :return: The number of people that have joined

        """

        try:
            display_text: str = self.common.display_text.key
            return int(display_text.split("pm_mt_guidance_viewer_")[1].split("_share")[0])
        except IndexError:
            return None


CustomEvent: Type = Union[UnknownEvent, ConnectEvent, FollowEvent, ShareEvent, LiveEndEvent, DisconnectEvent]

__all__ = [
    "UnknownEvent",
    "ConnectEvent",
    "FollowEvent",
    "ShareEvent",
    "LiveEndEvent",
    "CustomEvent",
    "DisconnectEvent"
]
