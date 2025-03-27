from __future__ import annotations

# noinspection PyUnresolvedReferences
import re
import warnings
# noinspection PyUnresolvedReferences
from typing import Optional, List, Type, TypeVar, Tuple

# noinspection PyUnresolvedReferences
import betterproto

from TikTokLive.proto import *
from TikTokLive.proto import User, BadgeStruct
from TikTokLive.proto.proto_utils import badge_match_user, SUBSCRIBER_BADGE_PATTERN, MODERATOR_BADGE_PATTERN, \
    TOP_GIFTER_BADGE_PATTERN, MEMBER_LEVEL_BADGE_PATTERN, GIFTER_LEVEL_BADGE_PATTERN

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

        return ExtendedUser(**user.to_pydict(**kwargs))

    @property
    def display_id(self):
        """Backwards compatibility for user"""
        warnings.warn(
            "ExtendedUser.display_id is deprecated - use ExtendedUser.username instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return getattr(self, "username", getattr(self, "nick_name", None))

    @property
    def unique_id(self) -> str:
        """
        Retrieve the user's @unique_id

        :return: User's unique_id

        """

        return self.username

    @property
    def is_friend(self) -> bool:
        """
        Is the user friends with the streamer

        :return: Whether the user is friends with the streamer

        """

        if self.follow_info.follow_status is None:
            return False

        return (self.follow_info.follow_status or 0) >= 2

    @property
    def subscriber_badge(self) -> Optional[BadgeStruct]:
        """
        Retrieve the subscriber badge of a user

        :return: The user's subscriber badge

        """

        matches: List[Tuple[re.Match, BadgeStruct]] = badge_match_user(
            user=self,
            p=SUBSCRIBER_BADGE_PATTERN
        )

        return matches[0] if matches else None

    @property
    def is_subscriber(self) -> bool:
        """
        Is the user subscribed to the streamer

        :return: Whether the user has the subscriber badge

        """

        return bool(self.subscriber_badge)

    @property
    def is_moderator(self) -> bool:
        """
        Is the user a moderator in the stream

        :return: Whether the user has the moderator badge

        """

        return bool(
            badge_match_user(
                user=self,
                p=MODERATOR_BADGE_PATTERN
            )
        )

    @property
    def is_top_gifter(self) -> bool:
        """
        Is the user a top gifter in the stream

        :return: Whether the user has the top gifter badge

        """

        return bool(
            badge_match_user(
                user=self,
                p=TOP_GIFTER_BADGE_PATTERN
            )
        )

    @property
    def member_level(self) -> Optional[int]:
        """
        What is the user's "member level" in the stream? This is a number.

        :return: The parsed member level badge
        """

        matches: list[tuple[re.Match, BadgeStruct]] = badge_match_user(
            user=self,
            p=MEMBER_LEVEL_BADGE_PATTERN
        )

        if len(matches) > 0:
            return int(matches[0][0].group(1))

        return None

    @property
    def member_rank(self) -> Optional[str]:
        """
        What is the user's "member rank" in the stream? These are roman numerals.

        :return: The parsed member rank from the member level badge

        """

        matches: list[tuple[re.Match, BadgeStruct]] = badge_match_user(
            user=self,
            p=MEMBER_LEVEL_BADGE_PATTERN
        )

        if len(matches) > 0:
            return matches[0][1].combine.str

        return None

    @property
    def gifter_level(self) -> Optional[int]:
        """
        What is the user's "gifter level" in the stream? An actual number specific to their level.

        :return: The parsed gifter level from the gifter level badge

        """

        matches: list[tuple[re.Match, BadgeStruct]] = badge_match_user(
            user=self,
            p=GIFTER_LEVEL_BADGE_PATTERN
        )

        if len(matches) > 0:
            return int(matches[0][1].combine_badge_struct.str)

        return None


@proto_extension
class ExtendedGift(Gift):
    """
    Extended gift object with clearer streak handling

    """

    def __init__(self, proto_gift: Gift):
        self.m_gift = proto_gift

        for attr, value in proto_gift.__dict__.items():
            setattr(self, attr, value)

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
