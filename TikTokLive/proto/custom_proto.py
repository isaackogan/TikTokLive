from __future__ import annotations

# noinspection PyUnresolvedReferences
import re
# noinspection PyUnresolvedReferences
from typing import Optional, List, Type, TypeVar, Tuple

# noinspection PyUnresolvedReferences
import betterproto2

from TikTokLiveProto.v3.webcast.model import Gift
from TikTokLiveProto.v3.webcast.model.base.user import User

# "MessageType" is a proto enum field.
# This underscore is the difference between life & death, because if you shadow the proto field,
# everything crashes & burns in a fiery hell.
_MessageType = TypeVar('_MessageType', bound=betterproto2.Message)


def proto_extension(cls: Type[_MessageType]) -> Type[_MessageType]:
    """
    Betterproto doesn't properly handle inheriting existing messages.
    This method takes the superclass proto metadata and assigns that to this one.

    :param cls: Class to wrap
    :return: The class, wrapped.

    """

    for obj in cls.__mro__[1:]:
        if issubclass(obj, betterproto2.Message):
            # Intentional metaclass-level mutation: copy the parent's
            # ``_betterproto`` metadata onto the subclass so betterproto2's
            # serialiser uses the inherited proto schema.
            # noinspection PyProtectedMember
            cls._betterproto = obj()._betterproto  # type: ignore[method-assign,assignment,arg-type]
            return cls

    return cls


@proto_extension
class ExtendedUser(User):
    """
    Extended user object with backwards compatibility

    """

    @classmethod
    def from_user(cls, user: User) -> ExtendedUser:
        """
        Convert a user to an ExtendedUser object

        :param user: Original user object
        :return: ExtendedUser instance
        """

        if isinstance(user, ExtendedUser):
            return user
        # betterproto2's from_dict is the canonical round-trip for
        # restructuring nested message values (the constructor expects
        # already-typed children, while from_dict reconstructs them from
        # the dict shape).
        return ExtendedUser.from_dict(user.to_dict(), ignore_unknown_fields=True)

    @property
    def unique_id(self) -> Optional[str]:
        """Legacy alias for the @-handle. v3 exposes it as ``display_id``."""

        return self.display_id or None

    @property
    def is_friend(self) -> bool:
        """
        Is the user friends with the streamer

        :return: Whether the user is friends with the streamer

        """

        # ``follow_info`` itself is Optional in v2 (proto3 implicit-optional);
        # only ``follow_status`` inside it is non-Optional. Treat absence as
        # "not friends".
        if self.follow_info is None:
            return False
        return self.follow_info.follow_status >= 2

    def _get_all_badge_info(self) -> List[Tuple[str, str]]:
        """
        Retrieve unique badge types with their levels.

        :return: List of (badge_type, level) tuples, with unique badge types
        """

        badge_dict = {}
        for badge in getattr(self, "badges", []) or []:
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
    def member_rank(self) -> Optional[int]:
        """
        What is the user's "member rank" in the stream?

        Historically these were roman-numeral strings; in v2 the badge
        carries the integer level directly, so this returns the parsed
        level (an alias of ``member_level``).

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

    def __init__(self, proto_gift: Optional[Gift] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.m_gift: Optional[Gift] = proto_gift
        if proto_gift is not None:
            for attr, value in proto_gift.__dict__.items():
                setattr(self, attr, value)

    @property
    def streakable(self) -> bool:
        """Whether a gift is capable of streaking."""

        return self.type == 1


# ``ControlAction`` is part of the upstream v3 schema (renamed from the
# legacy ``CONTROL_ACTION_*`` form to ``STREAM_*``) — re-export it from here
# so existing ``from TikTokLive.proto.custom_proto import ControlAction``
# imports keep resolving to the canonical enum.
from TikTokLiveProto.v3.webcast.im import ControlAction as ControlAction  # noqa: E402, F401
