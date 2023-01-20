from dataclasses import dataclass, field
from typing import Optional, List

from TikTokLive.types import User, Gift, Emote, TreasureBoxData, RankContainer, MicBattleUser, MicArmiesUser


class AbstractEvent:
    """
    Abstract Event
    
    """

    name: str = "event"
    _as_dict: dict = dict()

    def __init__(self, data: dict = dict()):
        self._as_dict: dict = data
        self.__name = None

    def set_as_dict(self, data: dict):
        """
        Set that _as_dict attribute

        :param data: The data to set it to
        :return: None

        """

        self._as_dict = data
        return self

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

    webcast_closed: bool
    """Whether the Webcast server closed the connection. If false, the client disconnected themselves."""

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
    """The type of event"""

    label: Optional[str]
    """Label for event in live chat"""

    @property
    def through_share(self) -> bool:
        """
        Whether they joined through a link vs. the TikTok App

        :return: Returns True if they joined through a share link

        """
        return self.displayType == "pm_mt_join_message_other_viewer"

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
    """Type of event"""

    label: Optional[str]
    """Internal Webcast Label"""

    name: str = "share"


@dataclass()
class MoreShareEvent(ShareEvent):
    """
    Event that fires when a user shared the livestream more than 5 users or more than 10 users

    "user123 has shared to more than 10 people!"

    """

    name: str = "more_share"

    @property
    def amount(self) -> Optional[int]:
        """
        The number of people that have joined the stream off the user

        :return: The number of people that have joined

        """

        try:
            return int(self.displayType.split("pm_mt_guidance_viewer_")[1].split("_share")[0])
        except IndexError:
            pass


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


@dataclass()
class EmoteEvent(AbstractEvent):
    """
    Event that fires when someone sends a subscriber emote
    
    """

    user: Optional[User]
    """Person who sent the emote message"""

    emote: Optional[Emote]
    """The emote the person sent"""

    name: str = "emote"


@dataclass()
class EnvelopeEvent(AbstractEvent):
    """
    Event that fire when someone sends an envelope
    
    """

    treasureBoxData: Optional[TreasureBoxData]
    """Data about the enclosed Treasure Box in the envelope"""

    treasureBoxUser: Optional[User]
    """Data about the user that sent the treasure box"""

    name: str = "envelope"


@dataclass()
class SubscribeEvent(AbstractEvent):
    """
    Event that fires when someone subscribes to the streamer

    """

    user: Optional[User]
    """The user that subscribed to the streamer"""

    exhibitionType: Optional[int]
    """Unknown"""

    subscribeType: Optional[int]
    """Unknown"""

    oldSubScribeStatus: Optional[int]
    """Whether they were subscribed before"""

    subscribingStatus: Optional[int]
    """Whether they are subscribing now"""

    name: str = "subscribe"


@dataclass()
class WeeklyRankingEvent(AbstractEvent):
    """
    Event that fires when the weekly rankings are updated

    """

    data: Optional[RankContainer]
    """Weekly ranking data"""

    name: str = "weekly_ranking"


@dataclass()
class MicBattleEvent(AbstractEvent):
    """
    Event that fires when a Mic Battle starts

    """

    battleUsers: List[MicBattleUser] = field(default_factory=lambda: [])
    """Information about the users engaged in the Mic Battle"""

    name: str = "mic_battle"


@dataclass()
class MicArmiesEvent(AbstractEvent):
    """
    Event that fires during a Mic Battle to update its progress

    """

    battleStatus: Optional[int]
    """The status of the current Battle"""

    battleUsers: List[MicArmiesUser] = field(default_factory=lambda: [])
    """Information about the users engaged in the Mic Battle"""

    name: str = "mic_armies"


__events__ = {
    "pm_mt_msg_viewer": LikeEvent,
    "live_room_enter_toast": JoinEvent,
    "pm_main_follow_message_viewer_2": FollowEvent,
    "pm_mt_guidance_share": ShareEvent,
    "pm_mt_join_message_other_viewer": JoinEvent,
    "pm_mt_guidance_viewer_5_share": MoreShareEvent,
    "pm_mt_guidance_viewer_10_share": MoreShareEvent
}
