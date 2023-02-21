from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from TikTokLive.client.client import TikTokLiveClient

import enum
import re
from dataclasses import dataclass, field
from threading import Thread
from typing import List, Optional, Any, Dict

from ffmpy import FFmpeg
from mashumaro import DataClassDictMixin, pass_through

from TikTokLive.types import utilities
from TikTokLive.types.utilities import alias


class AbstractObject(DataClassDictMixin):
    """
    Abstract Object

    """

    pass


@dataclass()
class Avatar(AbstractObject):
    """
    The URLs to the avatar of a TikTok User

    """

    urls: List[str] = field(default_factory=lambda: [])

    @property
    def url(self):
        """
        The last avatar URL supplied, if any are supplied

        """

        if len(self.urls) > 0:
            return self.urls[-1]

    async def download(self) -> Optional[bytes]:
        """
        Download the GiftImage image
        :return: Image as a bytestring

        """

        return await utilities.download(self.url, getattr(self, "_client"))


@dataclass()
class UserDetail(AbstractObject):
    """
    Extra attributes on the User Object (e.g. following status)

    """

    follow_role: Optional[int] = None


@dataclass()
class TextBadge(AbstractObject):
    """
    User badges (e.g moderator)

    """

    type: Optional[str] = None
    """The type of badge"""

    name: Optional[str] = None
    """The name for the badge"""


@dataclass()
class ImageBadge(AbstractObject):
    """"
    Image Badge object containing an image badge for a TikTok User

    """

    @classmethod
    def __pre_deserialize__(cls, d: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Flatten it a bit to get just the image

        """

        d["url"] = d.get('image', dict()).get('url')
        return d

    async def download(self, client: TikTokLiveClient) -> Optional[bytes]:
        """
        Download the ImageBadge image
        :return: Image as a bytestring

        """

        return await utilities.download(self.url, client)

    url: Optional[str] = None
    """The TikTok CDN Image URL for the badge"""

    display_type: Optional[int] = None
    """The display type of the badge"""


@dataclass()
class BadgeContainer(AbstractObject):
    """
    Badge container housing a list of user badges

    """

    badge_scene_type: Optional[int] = None
    """Their badge "level". For a subscriber, for example, this can be 3/7"""

    image_badges: List[ImageBadge] = field(default_factory=lambda: [])
    """A list of image badges the user has (e.g. Subscriber badge)"""

    text_badges: List[TextBadge] = field(default_factory=lambda: [])
    """A list of text badges the user has (e.g. Moderator/Friend badge)"""


@dataclass()
class User(AbstractObject):
    """
    User object containing information on a TikTok User

    """

    nickname: Optional[str] = None
    """The user's nickname (e.g Charlie d'Amelio)"""

    avatar: Optional[Avatar] = field(default_factory=lambda: Avatar())
    """An object containing avatar url information"""

    unique_id: Optional[str] = None
    """The user's uniqueId (e.g @charlidamelio)"""

    user_id: Optional[int] = None
    """The user's Internal TikTok User ID"""

    details: UserDetail = field(default_factory=lambda: UserDetail())
    """Extra attributes for the user such as if they are following the streamer"""

    badges: List[BadgeContainer] = field(default_factory=lambda: list())
    """Badges for the user containing information such as if they are a stream moderator"""

    @property
    def is_following(self) -> bool:
        """
        Whether they are following the watched streamer

        """

        return self.details.follow_role >= 1

    @property
    def is_friend(self) -> bool:
        """
        Whether they are a friend of the watched streamer

        """

        return self.details.follow_role >= 2

    def __contains_badge(self, name: str) -> bool:
        """
        Check if a given badge type is in the badge list

        :param name: Name of the badge or URL
        :return: Whether it's there

        """

        for badge in self.badges:
            for text_badge in badge.text_badges:
                if name in text_badge.type or name in text_badge.name:
                    return True
            for image_badge in badge.image_badges:
                if name in image_badge.url or name in image_badge.display_type:
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

        # Sub badge name
        if self.__contains_badge("/sub_"):
            return True

        # Generic sub badge type
        for badge in self.badges:
            if badge.badge_scene_type in [4, 7]:
                return True

        return False

    @property
    def top_gifter_rank(self) -> Optional[int]:
        """
        Their top gifter rank if they are a top gifter

        """

        for badge in self.badges:
            for _badge in badge.image_badges:
                result = re.search(r'(?<=ranklist_top_gifter_)(\d+)(?=.png)', _badge.url)
                if result is not None:
                    return int(result.group())

        return None


@dataclass()
class GiftIcon(AbstractObject):
    """
    Icon data for a given gift (such as its image URL)

    """

    avg_color: Optional[str] = None
    """Colour of the gift"""

    uri: Optional[str] = None
    """URI for the URL (the URL minus the https://cdn)"""

    is_animated: Optional[bool] = None
    """Whether or not it is an animated icon"""

    urls: Optional[List[str]] = alias("url_list")
    """A list of URLs containing various sizes of the gift's icon"""

    @property
    def url(self) -> Optional[str]:
        """
        Retrieve the highest quality URL offered

        """

        if len(self.urls) > 0:
            return self.urls[-1]

    async def download(self) -> Optional[bytes]:
        """
        Download the GiftIcon image
        :return: Image as a bytestring

        """

        return await utilities.download(self.url, getattr(self, "_client"))


@dataclass()
class GiftImage(AbstractObject):
    """
    Gift image
    
    """

    url: Optional[str] = None
    """Icon URL for the Gift"""

    async def download(self) -> Optional[bytes]:
        """
        Download the GiftImage image
        :return: Image as a bytestring

        """

        return await utilities.download(self.url, getattr(self, "_client"))


@dataclass()
class GiftInfo(AbstractObject):
    """
    Details about a given gift 
    
    """

    image: Optional[GiftImage] = field(default_factory=lambda: GiftImage())
    """Image container for the Gift"""

    description: Optional[str] = None
    """Describes the gift"""

    type: Optional[int] = None
    """The type of gift. Type 1 are repeatable, any other type are not."""

    diamond_count: Optional[int] = alias("diamondCount")
    """Diamond value of x1 of the gift"""

    name: Optional[str] = alias("giftName")
    """Name of the gift"""


@dataclass()
class GiftRecipient(AbstractObject):
    """
    Gift object containing information about the gift recipient

    """

    timestamp: Optional[int] = None
    """The time the gift was received"""

    user_id: Optional[int] = None
    """The user ID of the person that received the gift"""


@dataclass()
class GiftDetailed(AbstractObject):
    """
    A detailed version of the Gift object with extra information that may or may not be useful

    """

    id: Optional[bool] = None
    """Internal TikTok Gift Id"""

    combo: Optional[bool] = None
    """Whether the gift can be combo'd"""

    can_put_gift_in_box: Optional[bool] = None
    """Whether the gift can be put into a treasure box"""

    description: Optional[str] = alias("describe")
    """Extra description for the gift"""

    diamond_count: Optional[int] = None
    """How much the gift is worth"""

    duration: Optional[int] = None
    """How long the gift lasts"""

    for_link_mic: Optional[bool] = alias("for_linkmic")
    """Whether the gift is for link mic events"""

    icon: Optional[GiftIcon] = field(default_factory=lambda: GiftIcon())
    """Image icon for the gift"""

    is_box_gift: Optional[bool] = None
    """Whether the gift is a box gift"""

    is_broadcast_gift: Optional[bool] = None
    """Whether the gift is a broadcast gift (usually YES since... this is TikTokLive)"""

    name: Optional[str] = None
    """The display name of the gift"""

    notify: Optional[bool] = None
    """Whether this gift gives a notification (presumably for expensive gifts)"""

    type: Optional[int] = None
    """The type of gift"""

    primary_effect_id: Optional[int] = None
    """Unknown purpose"""

    event_name: Optional[str] = None
    """Unknown purpose"""

    is_displayed_on_panel: Optional[bool] = None
    """Unknown purpose"""

    is_random_gift: Optional[bool] = None
    """Unknown purpose"""

    is_gray: Optional[bool] = None
    """Unknown purpose"""

    gift_scene: Optional[int] = None
    """Unknown purpose"""


@dataclass()
class Gift(AbstractObject):
    """
    Gift object containing information about a given gift
    
    """

    id: Optional[int] = None
    """The Internal TikTok ID of the gift"""

    count: Optional[int] = alias("repeatCount", default=None)
    """Number of times the gift has repeated"""

    is_repeating: Optional[int] = alias("repeatEnd", default=None)
    """Whether or not the repetition is over"""

    info: Optional[GiftInfo] = field(default_factory=lambda: GiftInfo())
    """Details about the specific Gift sent"""

    recipient: Optional[GiftRecipient] = field(default_factory=lambda: GiftRecipient())
    """Who received the gift (for streams with multiple users)"""

    detailed: Optional[GiftDetailed] = field(metadata={"serialization_strategy": pass_through}, default=None)
    """If offered, allow a default gift"""

    @property
    def streakable(self) -> Optional[bool]:
        """
        Whether a given gift can have a streak

        :return: True if it is type 1, otherwise False
        """

        return self.info.type == 1 if self.info.type is not None else None

    @property
    def streaking(self) -> bool:
        """
        Whether the streak is over
        
        :return: True if currently streaking, False if not

        """

        return bool(self.is_repeating)


@dataclass()
class EmoteImage(AbstractObject):
    """
    Container encapsulating the image URL for the Emote

    """

    url: Optional[str] = None
    """TikTok CDN link to the given Emote for the streamer"""

    async def download(self) -> Optional[bytes]:
        """
        Download the EmoteImage image
        :return: Image as a bytestring

        """

        return await utilities.download(self.url, getattr(self, "_client"))


@dataclass()
class Emote(AbstractObject):
    """
    The Emote a user sent in the chat

    """

    emoteId: Optional[str] = None
    """ID of the TikTok Emote"""

    image: Optional[EmoteImage] = field(default_factory=lambda: EmoteImage())
    """Container encapsulating the image URL for the sent Emote"""


@dataclass()
class TreasureBoxData(AbstractObject):
    """
    Information about the gifted treasure box

    """

    coins: Optional[int] = None
    """Number of coins enclosed in the treasure box"""

    openable: Optional[int] = None
    """Whether the treasure box can be opened"""

    timestamp: Optional[int] = None
    """Timestamp for when the treasure box was sent"""


@dataclass()
class ExtraRankData(AbstractObject):
    """
    Extra UI data related to the rank update

    """

    colour: Optional[str] = None
    """Colour that the rank corresponds to (for the UI)"""

    id: Optional[int] = None
    """Some sort of internal ID, potentially related to rank"""


@dataclass()
class LinkUser(AbstractObject):
    """
    A user in a TikTok LinkMicBattle (TikTok Battle Events)

    """

    user_id: Optional[int] = None
    """Internal TikTok user id of the user"""

    nickname: Optional[str] = None
    """User's Nickname"""

    avatar: Optional[Avatar] = field(default_factory=lambda: Avatar())
    """User's Profile Picture"""

    unique_id: Optional[str] = None
    """The uniqueId of the user"""


@dataclass()
class MicBattleGroup(AbstractObject):
    """
    A container encapsulating LinkUser data for TikTok Battles

    """

    user: Optional[LinkUser] = None
    """The TikTok battle LinkUser"""


@dataclass()
class BattleArmy(AbstractObject):
    """
    A group containing

    """

    host_user_id: Optional[int] = None
    """The user ID of the host for this battle army"""

    points: Optional[int] = None
    """The number of points the battle army has"""

    participants: List[User] = field(default_factory=lambda: [])
    """The users involved in the specific battle army"""


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


class VideoQuality(enum.Enum):
    """
    Video quality selection for stream downloads

    """

    LD = "ld"
    """Low definition (480p, vbrate-500,000)"""

    SD = "sd"
    """Standard definition (480p, vbrate-800,000)"""

    HD = "hd"
    """High definition (540p, vbrate-1,000,000)"""

    UHD = "uhd"
    """Ultra-high definition (720p, vbrate-1,000,000)"""

    ORIGIN = "origin"
    """Original definition (N/A, vbrate-N/A)"""
