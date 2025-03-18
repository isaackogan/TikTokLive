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
