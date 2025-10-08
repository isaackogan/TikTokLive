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
class HeartbeatMessage(betterproto.Message):
    """Heartbeat Keepalive Message"""

    room_id: int = betterproto.uint64_field(1)
    send_packet_seq_id: int = betterproto.uint64_field(2)


@dataclass(eq=False, repr=False)
class WebcastImEnterRoomMessage(betterproto.Message):
    """Message sent when entering a webcast room."""

    room_id: int = betterproto.int64_field(1)  # sent
    room_tag: str = betterproto.string_field(2)  # not sent
    live_region: str = betterproto.string_field(3)  # not sent
    live_id: int = betterproto.int64_field(4)  # "12" <- static value
    identity: str = betterproto.string_field(5)  # "audience"
    cursor: str = betterproto.string_field(6)  # ""
    account_type: int = betterproto.int64_field(7)  # 0
    enter_unique_id: int = betterproto.int64_field(8)  # not sent
    filter_welcome_msg: str = betterproto.string_field(9)  # "0"
    is_anchor_continue_keep_msg: bool = betterproto.bool_field(10)  # 0
