import enum
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
class TikTokImage(AbstractObject):
    """
    An image resource on TikTok LIVE

    """

    urls: List[str] = field(default_factory=list)
    """The full URL including CDN"""

    uri: Optional[str] = None
    """URI without the CDN link"""

    @property
    def url(self) -> Optional[str]:
        """
        The last URL supplied, if any are supplied

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
class UserInfo(AbstractObject):
    """
    Extra attributes on the User Object (e.g. following status)

    """

    following: Optional[int] = None
    """Number of people they follow"""

    followers: Optional[int] = None
    """Number of people that follow them"""

    follow_role: Optional[int] = None
    """Whether they are a random, follower, or friend"""


@dataclass()
class Badge(AbstractObject):
    """
    TikTok Badge class

    """

    @classmethod
    def __pre_deserialize__(cls, badge: Dict[Any, Any]) -> Dict[Any, Any]:
        # Process image & text badges
        data: dict = {
            'badge_scene_type': badge.get('badge_scene_type'),
            'image': badge.get('image', dict()).get('image'),
            **badge.get('text', dict())
        }

        # Process complex badges
        if badge.get('complex'):
            data['image'] = badge["complex"].get('image', dict())
            data['name'] = badge["complex"].get('data')
            data = {**data, **badge["complex"].get('label', dict())}

        return data

    badge_scene_type: Optional[int] = None
    """Internal type for a badge"""

    image: Optional[TikTokImage] = None
    """Image associated with a badge"""

    label: Optional[str] = None
    """The internal TikTok badge label"""

    name: Optional[str] = None
    """The name of the badge"""


@dataclass()
class User(AbstractObject):
    """
    User object containing information on a TikTok User

    """

    user_id: Optional[int] = None
    """The user's Internal TikTok User ID"""

    nickname: Optional[str] = None
    """The user's nickname (e.g Charlie d'Amelio)"""

    avatar: Optional[TikTokImage] = field(default_factory=TikTokImage)
    """An object containing avatar url information"""

    unique_id: Optional[str] = None
    """The user's uniqueId (e.g @charlidamelio)"""

    sec_uid: Optional[str] = None
    """An internal alphanumeric TikTok User ID"""

    info: UserInfo = field(default_factory=UserInfo)
    """Extra attributes for the user such as if they are following the streamer"""

    badges: List[Badge] = field(default_factory=list)
    """Badges for the user containing important extra info"""

    def __badge_text_search(self, text: str) -> bool:
        """
        Search a badge for a given string of text

        :param text: Text to include in search
        :return: Search status

        """

        for badge in self.badges:
            for i in [badge.image.uri if badge.image else None, badge.name, badge.label]:
                if text.lower() in (i or "").lower():
                    return True

        return False

    def __badge_type_search(self, badge_type: int) -> bool:
        """
        Search for a given badge type

        :param badge_type: Type (int)
        :return: Search status

        """

        return any(badge_type == badge.badge_scene_type for badge in self.badges)

    @property
    def is_following(self) -> Optional[bool]:
        """
        Whether they are following the watched streamer

        """

        if self.info.follow_role is None:
            return None

        return (self.info.follow_role or 0) >= 1

    @property
    def is_friend(self) -> Optional[bool]:
        """
        Whether they are a friend of the watched streamer

        """

        if self.info.follow_role is None:
            return None

        return (self.info.follow_role or 0) >= 2

    @property
    def is_new_gifter(self) -> bool:
        """
        Whether they are a new gifter in the streamer's stream

        """

        return self.__badge_text_search("live_ng")

    @property
    def is_moderator(self) -> bool:
        """
        Whether they are a moderator for the watched streamer

        """

        return self.__badge_text_search("moderator")

    @property
    def is_subscriber(self) -> bool:
        """
        Whether they are a subscriber in the watched stream

        """

        return self.__badge_text_search("/sub_") or self.__badge_type_search(4)

    @property
    def is_top_gifter(self) -> bool:
        """
        Whether they are withi nthe top 3 gifters in the stream
        
        """

        return bool(self.top_gifter_rank)

    @property
    def top_gifter_rank(self) -> Optional[int]:
        """
        Their top gifter rank if they are a top gifter

        """

        for badge in self.badges:
            if "top_gifter" in (badge.image.uri if badge.image else ""):
                try:
                    return int(badge.name.split(' ')[1])  # Parse "No. 2" string
                except:
                    continue

    @property
    def gifter_level(self) -> Optional[int]:
        """
        The user's gifter level. If this is None, they do not have a gifter level.
        
        """

        for badge in self.badges:
            if "grade_badge" in (badge.image.uri if badge.image else ""):
                try:
                    return int(badge.name)
                except:
                    return None


@dataclass()
class TopViewer(AbstractObject):
    """
    Top viewer in a livestream

    """

    coins_given: int = None
    """Number of coins they have given to the streamer"""

    user: Optional[User] = None
    """User information. Tends to be mostly populated for top 3 only"""

    rank: Optional[int] = None
    """Their "top viewer" rank, typically ~1-20"""


@dataclass()
class GiftIcon(TikTokImage):
    """
    Icon data for a given gift (such as its image URL)

    """

    avg_color: Optional[str] = None
    """Colour of the gift"""

    is_animated: Optional[bool] = None
    """Whether or not it is an animated icon"""

    urls: Optional[List[str]] = alias("url_list")
    """A list of URLs containing various sizes of the gift's icon"""


@dataclass()
class GiftInfo(AbstractObject):
    """
    Details about a given gift 
    
    """

    image: Optional[TikTokImage] = field(default_factory=TikTokImage)
    """Image container for the Gift"""

    description: Optional[str] = None
    """Describes the gift"""

    type: Optional[int] = None
    """The type of gift. Type 1 are repeatable, any other type are not."""

    diamond_count: Optional[int] = None
    """Diamond value of x1 of the gift"""

    name: Optional[str] = None
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

    can_put_in_gift_box: Optional[bool] = None
    """Whether the gift can be put into a treasure box"""

    description: Optional[str] = alias("describe")
    """Extra description for the gift"""

    diamond_count: Optional[int] = None
    """How much the gift is worth"""

    duration: Optional[int] = None
    """How long the gift lasts"""

    for_link_mic: Optional[bool] = alias("for_linkmic")
    """Whether the gift is for link mic events"""

    icon: Optional[GiftIcon] = field(default_factory=GiftIcon)
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

    is_repeating: Optional[int] = alias("repeatEnd", default=0)
    """Whether or not the repetition is over"""

    info: Optional[GiftInfo] = field(default_factory=GiftInfo)
    """Details about the specific Gift sent"""

    recipient: Optional[GiftRecipient] = field(default_factory=GiftRecipient)
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

    emote_id: Optional[str] = None
    """ID of the TikTok Emote"""

    image: Optional[EmoteImage] = field(default_factory=EmoteImage)
    """Container encapsulating the image URL for the sent Emote"""


@dataclass()
class ChatImage(AbstractObject):
    """
    An image sent in the TikTok LIVE chat as part of a comment

    """

    @classmethod
    def __pre_deserialize__(cls, d: Dict[Any, Any]) -> Dict[Any, Any]:
        """
        Flatten the message a bit

        """

        d["image"] = d.get("image", dict()).get("image")
        return d

    position: int = 0
    """Position of the message in the chat"""

    image: Optional[TikTokImage] = field(default_factory=TikTokImage)
    """Instance of the image"""


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

    avatar: Optional[TikTokImage] = field(default_factory=TikTokImage)
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

    participants: List[User] = field(default_factory=list)
    """The users involved in the specific battle army"""


@dataclass()
class ValueLabel(AbstractObject):
    """
    Label containing a value

    """

    data: Optional[int] = None
    label: Optional[str] = None
    label2: Optional[str] = None
    label3: Optional[str] = None


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
