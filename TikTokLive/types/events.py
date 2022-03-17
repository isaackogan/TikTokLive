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
        """
        Return a copy of the object as a dictionary

        :return: A copy of the raw payload

        """

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
    """The user that liked the stream"""

    likeCount: Optional[int]
    """The number of likes they sent (I think?)"""

    totalLikeCount: Optional[int]
    """The total number of likes on the stream"""

    displayType: Optional[str]
    label: Optional[str]

    name: str = "like"


@dataclass()
class JoinEvent(AbstractEvent):
    """
    Event that fires when a user joins the livestream
    
    """

    user: Optional[User]
    """The user that joined the stream"""

    displayType: Optional[str]
    label: Optional[str]

    name: str = "join"


@dataclass()
class FollowEvent(AbstractEvent):
    """
    Event that fires when a user follows the livestream
    
    """

    user: Optional[User]
    """The user that followed the streamer"""

    displayType: Optional[str]
    label: Optional[str]

    name: str = "follow"


@dataclass()
class ShareEvent(AbstractEvent):
    """
    Event that fires when a user shares the livestream
    
    """

    user: Optional[User]
    """The user that shared the stream"""

    displayType: Optional[str]
    label: Optional[str]
    name: str = "share"


@dataclass()
class ViewerCountUpdateEvent(AbstractEvent):
    """
    Event that fires when the viewer count for the livestream updates
    
    """

    viewerCount: Optional[int]
    """The number of people viewing the stream currently"""

    name: str = "viewer_count_update"


@dataclass()
class CommentEvent(AbstractEvent):
    """
    Event that fires when someone comments on the livestream
    
    """

    user: Optional[User]
    """The user that sent the comment"""

    comment: Optional[str]
    """The UTF-8 text comment that was sent"""

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
    """The user that sent the gift"""

    gift: Optional[Gift]
    """Object containing gift data"""

    name: str = "gift"


@dataclass()
class QuestionEvent(AbstractEvent):
    """
    Event that fires when someone asks a Q&A question
    
    """

    questionText: Optional[str]
    """The question that was asked"""

    user: Optional[User]
    """User who asked the question"""

    name: str = "question"


__events__ = {
    "pm_mt_msg_viewer": LikeEvent,
    "live_room_enter_toast": JoinEvent,
    "pm_main_follow_message_viewer_2": FollowEvent,
    "pm_mt_guidance_share": ShareEvent
}
