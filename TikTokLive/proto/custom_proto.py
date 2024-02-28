from __future__ import annotations

from typing import Type, TypeVar

import betterproto

from TikTokLive.proto import User, GiftStruct

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
    def unique_id(self) -> str:
        """
        Retrieve the user's @unique_id

        :return: User's unique_id

        """

        return self.display_id


@proto_extension
class ExtendedGiftStruct(GiftStruct):
    """
    Extended gift object with clearer streak handling

    """

    @property
    def streakable(self) -> bool:
        """
        Whether a gift is capable of streaking

        :return: The gift

        """

        return self.type == 1

