from dataclasses import dataclass
from typing import Optional

from TikTokLive.types import User, Gift


class AbstractEvent:
    """
    Abstract Event
    
    """

    name: str = "event"
    _as_dict: dict = dict()

    def __init__(self, data: dict = dict()):
        self._as_dict: dict = data
        self.__name = None

    @property
    def as_dict(self) -> dict:
        return self._as_dict


@dataclass()
class ConnectEvent(AbstractEvent):
    """
    Event that fires when the client connect to a livestream
    
    """

    name: str = "connect"


@dataclass()
class DisconnectEvent(AbstractEvent):
    """
    Event that fires when the client disconnects from a livestream
    
    """

    name: str = "disconnect"


@dataclass()
class LikeEvent(AbstractEvent):
    """
    Event that fires when a user likes the livestream
    
    """

    user: Optional[User]
    likeCount: Optional[int]
    totalLikeCount: Optional[int]
    displayType: Optional[str]
    label: Optional[str]

    name: str = "like"


@dataclass()
class JoinEvent(AbstractEvent):
    """
    Event that fires when a user joins the livestream
    
    """

    user: Optional[User]
    displayType: Optional[str]
    label: Optional[str]

    name: str = "join"


@dataclass()
class FollowEvent(AbstractEvent):
    """
    Event that fires when a user follows the livestream
    
    """

    user: Optional[User]
    displayType: Optional[str]
    label: Optional[str]

    name: str = "follow"


@dataclass()
class ShareEvent(AbstractEvent):
    """
    Event that fires when a user shares the livestream
    
    """

    user: Optional[User]
    displayType: Optional[str]
    label: Optional[str]
    name: str = "share"


@dataclass()
class ViewerCountUpdateEvent(AbstractEvent):
    """
    Event that fires when the viewer count for the livestream updates
    
    """

    viewerCount: Optional[int]
    name: str = "viewer_count_update"


@dataclass()
class CommentEvent(AbstractEvent):
    """
    Event that fires when someone comments on the livestream
    
    """

    user: Optional[User]
    comment: Optional[str]
    name: str = "comment"


@dataclass()
class UnknownEvent(AbstractEvent):
    """
    Event that fires when an event is received that is not handled by other events in the library.
    
    """

    name: str = "unknown"


@dataclass()
class LiveEndEvent(AbstractEvent):
    """
    Event that fires when the livestream ends
    
    """

    name: str = "live_end"


@dataclass()
class GiftEvent(AbstractEvent):
    """
    Event that fires when a gift is received
    
    """

    user: Optional[User]
    gift: Optional[Gift]

    name: str = "gift"


@dataclass()
class QuestionEvent(AbstractEvent):
    """
    Event that fires when someone asks a Q&A question
    
    """
    
    questionText: Optional[str]
    user: Optional[User]

    name: str = "question"


__events__ = {
    "pm_mt_msg_viewer": LikeEvent,
    "live_room_enter_toast": JoinEvent,
    "pm_main_follow_message_viewer_2": FollowEvent,
    "pm_mt_guidance_share": ShareEvent
}
