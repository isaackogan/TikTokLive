from asyncio import Event
from typing import TypeVar, Callable, Union, Awaitable


class BaseEvent:

    @property
    def type(self) -> str:
        return self.get_type()

    @classmethod
    def get_type(cls) -> str:
        return cls.__name__


