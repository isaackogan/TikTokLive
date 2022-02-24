from dataclasses import dataclass
from typing import Optional

from TikTokLive.types import User, Gift


class AbstractEvent:
    name: str = "event"
    _as_dict: dict = dict()

    def __init__(self):
        self.__name = None

    @property
    def as_dict(self) -> dict:
        return self._as_dict


@dataclass()
class ConnectEvent(AbstractEvent):
    name: str = "connect"
    pass


@dataclass()
class DisconnectEvent(AbstractEvent):
    name: str = "disconnect"
    pass


@dataclass()
class LikeEvent(AbstractEvent):
    user: Optional[User]
    likeCount: Optional[int]
    totalLikeCount: Optional[int]
    displayType: Optional[str]
    label: Optional[str]

    name: str = "like"


@dataclass()
class JoinEvent(AbstractEvent):
    user: Optional[User]
    displayType: Optional[str]
    label: Optional[str]

    name: str = "join"


@dataclass()
class FollowEvent(AbstractEvent):
    user: Optional[User]
    displayType: Optional[str]
    label: Optional[str]

    name: str = "follow"


@dataclass()
class ShareEvent(AbstractEvent):
    user: Optional[User]
    displayType: Optional[str]
    label: Optional[str]
    name: str = "share"


@dataclass()
class ViewerCountUpdateEvent(AbstractEvent):
    viewerCount: Optional[int]
    name: str = "viewer_count_update"


@dataclass()
class CommentEvent(AbstractEvent):
    user: Optional[User]
    comment: Optional[str]
    name: str = "comment"


@dataclass()
class UnknownEvent(AbstractEvent):
    name: str = "unknown"


@dataclass()
class LiveEndEvent(AbstractEvent):
    name: str = "live_end"


@dataclass()
class GiftEvent(AbstractEvent):
    user: Optional[User]
    gift: Optional[Gift]

    name: str = "gift"


__events__ = {
    "pm_mt_msg_viewer": LikeEvent,
    "live_room_enter_toast": JoinEvent,
    "pm_main_follow_message_viewer_2": FollowEvent,
    "pm_mt_guidance_share": ShareEvent
}
