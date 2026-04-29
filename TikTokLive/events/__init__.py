from typing import Awaitable, Callable, TypeAlias, TypeVar, Union

from .custom_events import *
from .proto_events import *

Event: TypeAlias = Union[CustomEvent, ProtoEvent]

EventHandler = TypeVar("EventHandler", bound=Callable[[Event], Union[None, Awaitable[None]]])