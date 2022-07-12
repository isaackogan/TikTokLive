import re
from dataclasses import dataclass, field
from threading import Thread
from typing import List, Optional

from ffmpy import FFmpeg


class AbstractObject:
    """
    Abstract Object

    """

    pass


@dataclass()
class Avatar(AbstractObject):
    """
    The URLs to the avatar of a TikTok User

    """

    urls: List[str]

    @property
    def avatar_url(self):
        """
        The last (highest quality) avatar URL supplied

        """
        return self.urls[-1]


@dataclass()
class ExtraAttributes(AbstractObject):
    """
    Extra attributes on the User Object (e.g. following status)

    """

    followRole: Optional[int] = field(default_factory=lambda: 0)


@dataclass()
class Badge(AbstractObject):
    """
    User badges (e.g moderator)

    """

    type: Optional[str]
    """The type of badge"""

    name: Optional[str]
    """The name for the badge"""


@dataclass()
class ImageBadgeImage:
    """
    Image container with the URL of the user badge

    """

    url: Optional[str]
    """The TikTok CDN Image URL for the badge"""


@dataclass()
class ImageBadge:
    """"
    Image Badge object containing an image badge for a TikTok User

    """

    displayType: Optional[int]
    """The displayType of the badge"""

    image: Optional[ImageBadgeImage]
    """Container for the image badge"""


@dataclass()
class BadgeContainer(AbstractObject):
    """
    Badge container housing a list of user badges

    """

    imageBadges: List[ImageBadge] = field(default_factory=lambda: [])
    """A list of image badges the user has (e.g. Subscriber badge)"""

    badges: List[Badge] = field(default_factory=lambda: [])
    """A list of text badges the user has (e.g. Moderator/Friend badge)"""


@dataclass()
class User(AbstractObject):
    """
    User object containing information on a TikTok User

    """

    userId: Optional[int]
    """The user's user id"""

    uniqueId: Optional[str]
    """The user's uniqueId (e.g @charlidamelio)"""

    nickname: Optional[str]
    """The user's nickname (e.g Charlie d'Amelio)"""

    profilePicture: Optional[Avatar]
    """An object containing avatar url information"""

    extraAttributes: ExtraAttributes = field(default_factory=lambda: ExtraAttributes())
    """Extra attributes for the user such as if they are following the streamer"""

    badges: List[BadgeContainer] = field(default_factory=lambda: [])
    """Badges for the user containing information such as if they are a stream moderator"""

    @property
    def is_following(self) -> bool:
        """
        Whether they are following the watched streamer

        """

        return self.extraAttributes.followRole >= 1

    @property
    def is_friend(self) -> bool:
        """
        Whether they are a friend of the watched streamer

        """

        return self.extraAttributes.followRole >= 2

    def __contains_badge(self, name: str) -> bool:
        """
        Check if a given badge type is in the badge list

        :param name: Name of the badge
        :return: Whether it's there

        """

        for badge in self.badges:
            for _badge in badge.badges:
                if name in _badge.type:
                    return True

        return False

    @property
    def is_new_gifter(self) -> bool:
        """
        Whether they are a new gifter in the streamer's stream

        """

        return self.__contains_badge("live_ng")

    @property
    def is_moderator(self) -> bool:
        """
        Whether they are a moderator for the watched streamer

        """

        return self.__contains_badge("moderator")

    @property
    def is_subscriber(self) -> bool:
        """
        Whether they are a subscriber in the watched stream

        """

        return self.__contains_badge("/sub_")

    @property
    def top_gifter_rank(self) -> Optional[int]:
        """
        Their top gifter rank if they are a top gifter

        """

        for badge in self.badges:
            for _badge in badge.imageBadges:
                result = re.search(r'(?<=ranklist_top_gifter_)(\d+)(?=.png)', _badge.image.url)
                if result is not None:
                    return int(result.group())

        return None


@dataclass()
class GiftIcon(AbstractObject):
    """
    Icon data for a given gift (such as its image URL)

    """
    avg_color: Optional[str]
    uri: Optional[str]

    is_animated: Optional[bool]
    """Whether or not it is an animated icon"""

    url_list: Optional[List[str]]
    """A list of URLs containing various sizes of the gift's icon"""


@dataclass()
class ExtendedGift(AbstractObject):
    """
    Extended gift data for a gift including a whole lotta extra properties.

    """

    id: Optional[int]
    """ The ID of the gift """

    name: Optional[str]
    """ The name of the gift """

    type: Optional[int]
    """The type of gift"""

    diamond_count: Optional[int]
    """The currency (Diamond) value of the item"""

    describe: Optional[str]
    duration: Optional[int]
    event_name: Optional[str]
    icon: Optional[GiftIcon]
    image: Optional[GiftIcon]
    notify: Optional[bool]
    is_broadcast_gift: Optional[bool]
    is_displayed_on_panel: Optional[bool]
    is_effect_befview: Optional[bool]
    is_random_gift: Optional[bool]
    is_gray: Optional[bool]


@dataclass()
class GiftDetailImage(AbstractObject):
    """
    Gift image
    
    """

    giftPictureUrl: Optional[str]
    """Icon URL for the Gift"""


@dataclass()
class GiftDetails(AbstractObject):
    """
    Details about a given gift 
    
    """

    giftImage: Optional[GiftDetailImage]
    """Image container for the Gift"""

    describe: Optional[str]
    """Describes the gift"""

    giftType: Optional[int]
    """The type of gift. Type 1 are repeatable, any other type are not."""

    diamondCount: Optional[int]
    """Diamond value of 1 of the gift"""

    giftName: Optional[str]
    """Name of the gift"""


@dataclass()
class GiftExtra:
    """
    Gift object containing information about the gift recipient

    """

    timestamp: Optional[int]
    """The time the gift was sent"""

    receiverUserId: Optional[int]
    """The user that received the gift"""


@dataclass()
class Gift(AbstractObject):
    """
    Gift object containing information about a given gift
    
    """

    giftId: Optional[int]
    """The Internal TikTok ID of the gift"""

    repeatCount: Optional[int]
    """Number of times the gift has repeated"""

    repeatEnd: Optional[int]
    """Whether or not the repetition is over"""

    giftDetails: Optional[GiftDetails]
    """Details about the specific Gift sent"""

    giftExtra: Optional[GiftExtra]
    """Details like who the gift was sent to (multi-user streams)"""

    extended_gift: Optional[ExtendedGift]
    """Extended gift including extra data (not very important as of april 2022)"""

    @property
    def streakable(self) -> bool:
        """
        Whether a given gift can have a streak

        :return: True if it is type 1, otherwise False
        """

        return self.giftDetails.giftType == 1

    @property
    def streaking(self) -> bool:
        """
        Whether the streak is over
        
        :return: True if currently streaking, False if not

        """

        return bool(self.repeatEnd)

    @property
    def repeat_count(self) -> int:
        """
        Alias for repeatCount for backwards compatibility

        :return: repeatCount Value
        """

        return self.repeatCount

    @property
    def repeat_end(self) -> int:
        """
        Alias for repeatEnd for backwards compatibility

        :return: repeatEnd Value

        """

        return self.repeatEnd

    @property
    def gift_type(self) -> int:
        """
        Alias for the giftDetails.giftType for backwards compatibility

        :return: giftType Value

        """

        return self.giftDetails.giftType


@dataclass()
class EmoteImage:
    """
    Container encapsulating the image URL for the Emote

    """

    imageUrl: Optional[str]
    """TikTok CDN link to the given Emote for the streamer"""


@dataclass()
class Emote:
    """
    The Emote a user sent in the chat

    """

    emoteId: Optional[str]
    """ID of the TikTok Emote"""

    image: Optional[EmoteImage]
    """Container encapsulating the image URL for the sent Emote"""


@dataclass()
class TreasureBoxData:
    """
    Information about the gifted treasure box

    """

    coins: Optional[int]
    """Coins of the treasure box"""

    canOpen: Optional[int]
    """Whether the treasure box can be opened"""

    timestamp: Optional[int]
    """Timestamp for when the treasure box was sent"""


@dataclass()
class MemberMessageDetails:
    """
    Details about a given member message proto event

    """

    displayType: Optional[str]
    """The displayType of the message corresponding to the type of member message"""

    label: Optional[str]
    """Display Label for the member message"""


@dataclass()
class RankItem:
    """
    Rank Item for the user ranking

    """

    colour: Optional[str]
    """Colour that the rank corresponds to (for the UI)"""

    id: Optional[int]
    """The rank. If id=400, they are in the Top 400"""


@dataclass()
class WeeklyRanking:
    """
    Container with the weekly ranking data

    """

    type: Optional[str]
    """Unknown"""

    label: Optional[str]
    """Label for the UI"""

    rank: Optional[RankItem]
    """The weekly ranking data"""


@dataclass()
class RankContainer:
    """
    Container encapsulating weekly ranking data

    """

    rankings: Optional[WeeklyRanking]


@dataclass()
class MemberMessage:
    """
    Container encapsulating the member message details

    """

    eventDetails: Optional[MemberMessageDetails]


@dataclass()
class LinkUser:
    """
    A user in a TikTok LinkMicBattle (TikTok Battle Events)

    """

    userId: Optional[int]
    """userId of the user"""

    nickname: Optional[str]
    """User's Nickname"""

    profilePicture: Optional[Avatar]
    """User's Profile Picture"""

    uniqueId: Optional[str]
    """The uniqueId of the user"""


@dataclass()
class MicBattleGroup:
    """
    A container encapsulating LinkUser data for TikTok Battles

    """

    user: LinkUser
    """The TikTok battle LinkUser"""


@dataclass()
class MicBattleUser:
    """
    A container encapsulating the LinkUser data for TikTok Battles

    """
    battleGroup: MicBattleGroup


@dataclass()
class MicArmiesGroup:
    """
    A group containing

    """

    points: Optional[int]
    """The number of points the person has"""

    users: List[User] = field(default_factory=lambda: [])
    """(Presumably) the users involved in the battle"""


@dataclass()
class MicArmiesUser:
    """
    Information about the Mic Armies User

    """

    hostUserId: Optional[int]
    """The user ID of the TikTok host"""

    battleGroups: Optional[MicArmiesGroup]
    """Information about the users involved in the battle"""


@dataclass()
class FFmpegWrapper:
    """
    A wrapper for the FFmpeg Stream Download utility in the TikTokLive Package

    """

    runtime: Optional[str]
    """FFMpeg argument for how long to download for"""

    thread: Thread
    """The thread object in which a download is occuring"""

    ffmpeg: FFmpeg
    """The ffmpy FFmpeg object in which a subprocess is spawned to download"""

    verbose: bool
    """Whether to include logging messages about the status of the download"""

    path: str
    """The path to download the video to"""

    started_at: int = -1
    """The time at which the download began"""
