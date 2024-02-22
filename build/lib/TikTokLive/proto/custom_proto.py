from __future__ import annotations

from typing import Type, TypeVar

import betterproto

from TikTokLive.proto import User, GiftStruct

MessageType: Type = TypeVar('MessageType', bound=betterproto.Message)


def proto_extension(cls: MessageType):
    """
    Betterproto doesn't properly handle inheriting existing messages.
    This method takes the superclass proto metadata and assigns that to this one.

    :param cls: The class
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

    @classmethod
    def from_user(cls, user: User, **kwargs) -> ExtendedUser:
        return ExtendedUser(**user.to_pydict(**kwargs))

    @property
    def unique_id(self) -> str:
        return self.display_id


@proto_extension
class ExtendedGiftStruct(GiftStruct):

    @property
    def streakable(self) -> bool:
        return self.type == 1

