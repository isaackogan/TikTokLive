from dataclasses import dataclass, field
from typing import List, Optional


class AbstractObject:
    pass


@dataclass()
class Avatar(AbstractObject):
    urls: List[str]

    @property
    def avatar_url(self):
        return self.urls[-1]


@dataclass()
class ExtraAttributes(AbstractObject):
    followRole: Optional[int] = field(default_factory=lambda: 0)


@dataclass()
class Badge(AbstractObject):
    type: Optional[str]
    name: Optional[str]


@dataclass()
class BadgeContainer(AbstractObject):
    badges: List[Badge] = field(default_factory=lambda: [])


@dataclass()
class User(AbstractObject):
    userId: Optional[int]
    uniqueId: Optional[str]
    nickname: Optional[str]
    profilePicture: Optional[Avatar]
    extraAttributes: ExtraAttributes = field(default_factory=lambda: ExtraAttributes())
    badge: BadgeContainer = BadgeContainer()

    @property
    def is_following(self) -> bool:
        return self.extraAttributes.followRole >= 1

    @property
    def is_friend(self) -> bool:
        return self.extraAttributes.followRole >= 2

    @property
    def is_moderator(self) -> bool:
        return any(badge.type == "pm_mt_moderator_im" for badge in self.badge.badges)


@dataclass()
class GiftIcon(AbstractObject):
    avg_color: Optional[str]
    urls: Optional[List[str]]


@dataclass()
class ExtendedGift(AbstractObject):
    id: Optional[int]
    name: Optional[str]
    type: Optional[int]
    describe: Optional[str]
    diamond_count: Optional[int]
    duration: Optional[int]
    event_name: Optional[str]
    icon: Optional[GiftIcon]
    notify: Optional[bool]
    is_broadcast_gift: Optional[bool]
    is_displayed_on_panel: Optional[bool]
    is_effect_befview: Optional[bool]
    is_random_gift: Optional[bool]
    is_gray: Optional[bool]


@dataclass()
class Gift(AbstractObject):
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
