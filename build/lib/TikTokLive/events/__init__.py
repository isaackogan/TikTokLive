from typing import Type, Union

from .custom_events import *
from ..client.logger import TikTokLiveLogHandler

try:
    from .proto_events import *

    Event: Type = Union[CustomEvent, ProtoEvent]
except (ModuleNotFoundError, NameError):
    Event: Type = Union[CustomEvent]
    TikTokLiveLogHandler.get_logger().error(
        "Failed to load the proto events class! "
        "Ignore this if merging from an empty/nonexistent file."
    )
