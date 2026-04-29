from typing import Awaitable, Callable, TypeAlias, TypeVar, Union

from .custom_events import *
from ..client.logger import TikTokLiveLogHandler

try:
    from .proto_events import *

    Event: TypeAlias = Union[CustomEvent, ProtoEvent]
except (ModuleNotFoundError, NameError):
    Event: TypeAlias = Union[CustomEvent]
    TikTokLiveLogHandler.get_logger().error(
        "Failed to load the proto events class! "
        "Ignore this if merging from an empty/nonexistent file."
    )

EventHandler = TypeVar("EventHandler", bound=Callable[[Event], Union[None, Awaitable[None]]])