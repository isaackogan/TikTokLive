from dataclasses import dataclass
from typing import TypedDict, Dict

import betterproto


class WebcastWSAckPayload(TypedDict):
    """
    JSON payload for an Ack. Only sent sometimes, in Brave browser. God knows why.

    """

    # In milliseconds
    server_fetch_time: int

    # In milliseconds
    push_time: int

    # "r" <- I assume for response?
    msg_type: str

    # Seq ID on the OG message
    seq_id: int

    # Is this from the proxy (if this field is populated, then false)
    is_from_ws_proxy: bool


@dataclass(eq=False, repr=False)
class WebcastPushFrame(betterproto.Message):
    seq_id: int = betterproto.uint64_field(1)
    log_id: int = betterproto.uint64_field(2)
    service: int = betterproto.uint64_field(3)
    method: int = betterproto.uint64_field(4)
    headers: Dict[str, str] = betterproto.map_field(
        5, betterproto.TYPE_STRING, betterproto.TYPE_STRING
    )
    payload_encoding: str = betterproto.string_field(6)
    payload_type: str = betterproto.string_field(7)
    payload: bytes = betterproto.bytes_field(8)


@dataclass(eq=False, repr=False)
class HeartbeatFrameRoomInfo(betterproto.Message):
    room_id: int = betterproto.uint64_field(1)


@dataclass(eq=False, repr=False)
class HeartbeatFrameMetadataField6(betterproto.Message):
    unknown_1: int = betterproto.uint32_field(14)


@dataclass(eq=False, repr=False)
class HeartbeatFrameMetadataField7(betterproto.Message):
    unknown_1: int = betterproto.uint32_field(13)


@dataclass(eq=False, repr=False)
class HeartbeatFrame(betterproto.Message):
    """Heartbeat Keepalive Message"""

    metadata_field_6: HeartbeatFrameMetadataField6 = betterproto.message_field(6)
    metadata_field_7: HeartbeatFrameMetadataField7 = betterproto.message_field(7)
    room_info: HeartbeatFrameRoomInfo = betterproto.message_field(8)

    @classmethod
    def from_defaults(cls, room_id: int) -> "HeartbeatFrame":
        """
        Generate a HeartbeatFrame with default values
        """

        return cls(
            metadata_field_6=HeartbeatFrameMetadataField6(unknown_1=98),
            metadata_field_7=HeartbeatFrameMetadataField7(unknown_1=98),
            room_info=HeartbeatFrameRoomInfo(room_id=room_id)
        )
