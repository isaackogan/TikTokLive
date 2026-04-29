from __future__ import annotations

from dataclasses import dataclass
from typing import Type, Union, Optional

from TikTokLive.events.base_event import BaseEvent
from TikTokLive.events.proto_events import SocialEvent, ControlEvent, BarrageEvent, EnvelopeEvent
from TikTokLive.proto import ProtoMessageFetchResult


class WebsocketResponseEvent(ProtoMessageFetchResult, BaseEvent):
    """
    Triggered when any event is received from the WebSocket

    """


class UnknownEvent(WebsocketResponseEvent):
    """
    Triggered when a Webcast message is received that is NOT tracked by TikTokLive yet.

    """


class SuperFanEvent(BarrageEvent):
    """
    Emitted when a viewer becomes a super fan of the streamer.

    Subset of ``BarrageEvent`` matched when ``content.display_type`` or
    ``common_barrage_content.display_type`` carries the ``ttlive_superfan``
    marker (and is not the more specific "joined" variant).

    """


class SuperFanJoinEvent(BarrageEvent):
    """
    Emitted when an existing super fan joins the live (distinct from
    ``SuperFanEvent`` which fires when a viewer first becomes a super fan).

    Subset of ``BarrageEvent`` matched when ``content.display_type`` or
    ``common_barrage_content.display_type`` contains
    ``ttlive_superfan_commentnotif_superfanjoined``.

    """


class SuperFanBoxEvent(EnvelopeEvent):
    """
    Emitted when a super-fan envelope (gift box) is delivered.

    Subset of ``EnvelopeEvent`` matched either by
    ``common.display_text.display_type`` carrying ``ttlive_superfanbox``,
    or by ``envelope_info.business_type == BusinessTypeSuperFanBox`` (= 19).

    """


@dataclass()
class ConnectEvent(BaseEvent):
    """
    Manually thrown when the first payload is received from the Sign Server

    """

    unique_id: str
    room_id: int


class DisconnectEvent(BaseEvent):
    """
    Thrown when disconnecting from a stream

    """


class LiveEndEvent(ControlEvent):
    """
    Thrown when the stream ends

    """


class LivePauseEvent(ControlEvent):
    """
    Thrown when the stream is paused

    """


class LiveUnpauseEvent(ControlEvent):
    """
    Thrown when a paused stream is unpaused

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
            display_text: str = (self.common.display_text.display_type or "")
            return int(display_text.split("pm_mt_guidance_viewer_")[1].split("_share")[0])
        except IndexError:
            return None


CustomEvent: Type = Union[
    WebsocketResponseEvent,
    UnknownEvent,
    ConnectEvent,
    FollowEvent,
    ShareEvent,
    LiveEndEvent,
    LivePauseEvent,
    LiveUnpauseEvent,
    DisconnectEvent,
    SuperFanEvent,
    SuperFanJoinEvent,
    SuperFanBoxEvent,
]

__all__ = [
    "WebsocketResponseEvent",
    "UnknownEvent",
    "ConnectEvent",
    "FollowEvent",
    "ShareEvent",
    "LiveEndEvent",
    "LivePauseEvent",
    "LiveUnpauseEvent",
    "CustomEvent",
    "DisconnectEvent",
    "SuperFanEvent",
    "SuperFanJoinEvent",
    "SuperFanBoxEvent",
]
