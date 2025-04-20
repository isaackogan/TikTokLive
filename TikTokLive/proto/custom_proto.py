from __future__ import annotations

# noinspection PyUnresolvedReferences
import re
# noinspection PyUnresolvedReferences
from typing import Optional, List, Type, TypeVar, Tuple

# noinspection PyUnresolvedReferences
import betterproto

from TikTokLive.proto import *
from TikTokLive.proto import User

# "MessageType" is a proto enum field.
# This underscore is the difference between life & death, because if you shadow the proto field,
# everything crashes & burns in a fiery hell.
_MessageType: Type = TypeVar('_MessageType', bound=betterproto.Message)


def proto_extension(cls: _MessageType):
    """
    Betterproto doesn't properly handle inheriting existing messages.
    This method takes the superclass proto metadata and assigns that to this one.

    :param cls: Class to wrap
    :return: The class, wrapped.

    """

    for obj in cls.__mro__[1:]:
        if issubclass(obj, betterproto.Message):
            # noinspection PyProtectedMember
            cls._betterproto = obj()._betterproto
            return cls

    return cls


@proto_extension
class ExtendedUser(User):
    """
    Extended user object with backwards compatibility

    """

    @classmethod
    def from_user(cls, user: User, **kwargs) -> ExtendedUser:
        """
        Convert a user to an ExtendedUser object

        :param user: Original user object
        :param kwargs: Any kwargs to pass
        :return: ExtendedUser instance
        """

        if isinstance(user, ExtendedUser):
            return user
        try:
            return ExtendedUser(**user.to_pydict(**kwargs))
        except AttributeError:
            user_dict = {}
            for field in user.__class__.__dataclass_fields__:
                try:
                    user_dict[field] = getattr(user, field)
                except AttributeError as e:
                    if "is set to None" in str(e):
                        underlying_attr = f"_{field}"
                        if hasattr(user, underlying_attr):
                            user_dict[field] = getattr(user, underlying_attr)
                        else:
                            user_dict[field] = None
                    else:
                        raise
            return ExtendedUser(**user_dict)

    @property
    def display_id(self):
        """Backwards compatibility for username"""

        return getattr(self, "username", getattr(self, "nick_name", None))

    @property
    def unique_id(self) -> str:
        """
        Retrieve the user's @unique_id

        :return: User's unique_id
        """

        return self.username

    @property
    def nickname(self) -> str:
        """
        Retrieve the user's @nickname

        :return: User's nickname
        """

        return getattr(self, "nick_name", getattr(self, "username", None))

    @property
    def is_friend(self) -> bool:
        """
        Is the user friends with the streamer

        :return: Whether the user is friends with the streamer

        """

        if self.follow_info.follow_status is None:
            return False

        return (self.follow_info.follow_status or 0) >= 2

    def _get_all_badge_info(self) -> List[Tuple[str, str]]:
        """
        Retrieve unique badge types with their levels.

        :return: List of (badge_type, level) tuples, with unique badge types
        """

        badge_dict = {}
        for badge in getattr(self, "badge_list", []):
            scene = getattr(badge, "badge_scene", None)
            log_extra = getattr(badge, "log_extra", None)
            badge_level = getattr(log_extra, "level", None) if log_extra else None
            if scene and badge_level:
                scene_name = str(scene).replace("BADGE_SCENE_TYPE_", "").upper()
                if scene_name not in badge_dict:
                    badge_dict[scene_name] = str(badge_level)
        return list(badge_dict.items())

    def _get_badge_level(self, badge_type: str, level: Optional[str | int] = None) -> Optional[int]:
        """
        Retrieve the level of a specific badge type with optional validation.

        :param badge_type: Badge type to check (e.g., "FANS", "SUBSCRIBER").
        :param level: Optional level to validate.
        :return: Level as int if found and validated, None otherwise.
        """

        target_badge = badge_type.replace("BADGE_SCENE_TYPE_", "").upper()
        for badge_name, badge_level in self._get_all_badge_info():
            if badge_name == target_badge:
                if level is None or str(level) == badge_level:
                    return int(badge_level)
        return None

    def has_badge(self, badge_type: str, level: Optional[str | int] = None) -> bool:
        """
        Check if the user has a specific badge type with optional level validation.

        :param badge_type: Badge type to check (e.g., "SUBSCRIBER").
        :param level: Optional level to validate.
        :return: True if the badge exists with matching criteria, False otherwise.
        """

        return self._get_badge_level(badge_type, level) is not None

    @property
    def get_all_badges(self) -> List[Tuple[str, str]]:
        """
        Retrieve all badges with their types and levels.

        :return: List of (badge_type, level) tuples
        """

        return self._get_all_badge_info()

    @property
    def is_subscriber(self) -> bool:
        """
        Is the user subscribed to the streamer

        :return: Whether the user has the subscriber badge

        """

        return bool(self.has_badge("SUBSCRIBER"))

    @property
    def is_moderator(self) -> bool:
        """
        Is the user a moderator in the stream

        :return: Whether the user has the moderator badge

        """

        return bool(self._get_badge_level("ADMIN") == 0)

    @property
    def is_top_gifter(self) -> bool:
        """
        Is the user a top gifter in the stream

        :return: Whether the user has the top gifter badge

        """

        return bool(self._get_badge_level("RANK_LIST") == 0)

    @property
    def member_level(self) -> Optional[int]:
        """
        What is the user's "member level" in the stream? This is a number.

        :return: The parsed member level badge
        """

        return self._get_badge_level("FANS")

    @property
    def member_rank(self) -> Optional[str]:
        """
        What is the user's "member rank" in the stream? These are roman numerals.

        :return: The parsed member rank from the member level badge

        """

        return self.member_level

    @property
    def gifter_level(self) -> Optional[int]:
        """
        What is the user's "gifter level" overall? An actual number specific to their level.

        :return: The parsed gifter level from the gifter level badge

        """

        return self._get_badge_level("USER_GRADE")


@proto_extension
class ExtendedGift(Gift):
    """
    Extended gift object with clearer streak handling

    """

    def __init__(self, proto_gift: Gift = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if proto_gift is not None:
            self.m_gift = proto_gift
            for attr, value in proto_gift.__dict__.items():
                setattr(self, attr, value)
        else:
            self.m_gift = None

    @property
    def streakable(self) -> bool:
        """
        Whether a gift is capable of streaking

        :return: The gift

        """

        return self.type == 1


class ControlAction(betterproto.Enum):
    CONTROL_ACTION_FALLBACK_UNKNOWN = 0
    CONTROL_ACTION_STREAM_PAUSED = 1
    CONTROL_ACTION_STREAM_UNPAUSED = 2
    CONTROL_ACTION_STREAM_ENDED = 3
    CONTROL_ACTION_STREAM_SUSPENDED = 4
