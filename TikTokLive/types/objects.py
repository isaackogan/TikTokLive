from dataclasses import dataclass, field
from typing import List, Optional


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
class BadgeContainer(AbstractObject):
    """
    Badge container housing a list of user badges

    """

    badges: List[Badge] = field(default_factory=lambda: [])
    """Badges for the user (e.g. moderator)"""


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

    badge: BadgeContainer = BadgeContainer()
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

    @property
    def is_moderator(self) -> bool:
        """
        Whether they are a moderator for the watched streamer

        """

        return any(badge.type == "pm_mt_moderator_im" for badge in self.badge.badges)


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

    describe: Optional[str]
    diamond_count: Optional[int]
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
class Gift(AbstractObject):
    """
    Gift object containing information about a given gift
    
    """

    from_user_id: Optional[int]
    """TikTok ID of the user that sent the gift"""

    to_user_id: Optional[int]
    """TikTok ID of the user that received the gift (the streamer)"""

    gift_id: Optional[int]
    """ID of the gift"""

    gift_type: Optional[int]
    """The type of gift (type 1 are repeatable, other types are not)"""

    repeat_count: Optional[int]
    """The number of times the gift has repeated"""

    room_id: Optional[int]
    """The room ID that the gift was sent to"""

    repeat_end: Optional[int]
    """Values 1 or 0, dictates whether the gift repetition has ended, ONLY for Type 1"""

    log_id: Optional[str]
    msg_id: Optional[int]
    anchor_id: Optional[int]
    from_idc: Optional[str]

    # Extra Gift Info
    extended_gift: Optional[ExtendedGift]
    """Extended gift including important data like the gift's image"""
