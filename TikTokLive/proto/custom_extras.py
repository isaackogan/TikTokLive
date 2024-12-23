from typing import TypedDict


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
