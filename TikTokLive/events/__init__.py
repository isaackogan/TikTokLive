from typing import Awaitable, Callable, TypeAlias, TypeVar, Union

from .custom_events import *
from .proto_events import *

Event: TypeAlias = Union[CustomEvent, ProtoEvent]

# ``Callable[..., ...]`` (rather than ``Callable[[Event], ...]``) so a handler
# annotated with a specific subclass — e.g. ``async def on_connect(event:
# ConnectEvent)`` — still satisfies the bound. ``Callable`` parameter types are
# contravariant; ``Callable[[ConnectEvent], …]`` is *not* a subtype of
# ``Callable[[Event], …]``, which would force every callsite to widen its
# annotation back to the union.
EventHandler = TypeVar("EventHandler", bound=Callable[..., Union[None, Awaitable[None]]])