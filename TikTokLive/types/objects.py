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
    name: Optional[str]


@dataclass()
class BadgeContainer(AbstractObject):
    """
    Badge container housing a list of user badges

    """

    badges: List[Badge] = field(default_factory=lambda: [])


@dataclass()
class User(AbstractObject):
    """
    User object containing information on a TikTok User

    """

    userId: Optional[int]
    uniqueId: Optional[str]
    nickname: Optional[str]
    profilePicture: Optional[Avatar]
    extraAttributes: ExtraAttributes = field(default_factory=lambda: ExtraAttributes())
    badge: BadgeContainer = BadgeContainer()

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
    url_list: Optional[List[str]]


@dataclass()
class ExtendedGift(AbstractObject):
    """
    Extended gift data for a gift including a whole lotta extra properties.
    
    """

    "Test"
    id: Optional[int]
    
    name: Optional[str]
    type: Optional[int]
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

    anchor_id: Optional[int]
    from_idc: Optional[str]
    from_user_id: Optional[int]
    gift_id: Optional[int]
    gift_type: Optional[int]
    log_id: Optional[str]
    msg_id: Optional[int]
    repeat_count: Optional[int]
    repeat_end: Optional[int]
    room_id: Optional[int]
    to_user_id: Optional[int]

    # Extra Gift Info
    extended_gift: Optional[ExtendedGift]
