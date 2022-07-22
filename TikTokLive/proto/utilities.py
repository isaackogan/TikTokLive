from dacite import from_dict, Config
from dacite.core import T
from dacite.data import Data
from protobuf_to_dict import protobuf_to_dict
from typing import Type, Optional, Any

from TikTokLive.proto import tiktok_schema_pb2 as tiktok_schema


def deserialize_message(proto_name: str, obj: bytes) -> dict:
    """
    Deserialize a protobuf message into a dictionary

    :param proto_name: The name of the message
    :param obj: The protobuf object to deserialize
    :return: The dictionary containing the deserialized message

    """

    schema = getattr(tiktok_schema, proto_name)
    webcast_data = schema()
    webcast_data.ParseFromString(obj)

    dict_data: dict = protobuf_to_dict(webcast_data)

    if proto_name == "WebcastResponse":
        for idx, message in enumerate(dict_data.get("messages", list())):
            if str(message.get("type")) not in [
                "WebcastControlMessage",
                "WebcastRoomUserSeqMessage",
                "WebcastChatMessage",
                "WebcastMemberMessage",
                "WebcastGiftMessage",
                "WebcastSocialMessage",
                "WebcastLikeMessage",
                "WebcastQuestionNewMessage",
                "WebcastLinkMicBattle",
                "WebcastLinkMicArmies",
                "WebcastHourlyRankMessage",
                "WebcastInRoomBannerMessage",
                "SystemMessage",
                "WebcastEmoteChatMessage",
                "WebcastEnvelopeMessage"
            ]:
                continue

            _type = message.get("type")
            _schema = getattr(tiktok_schema, _type)()
            _schema.ParseFromString(message.get("binary"))
            _dict_data = protobuf_to_dict(_schema)
            _dict_data["type"] = _type
            dict_data["messages"][idx] = _dict_data

    return dict_data


def deserialize_websocket_message(binary_message: bytes) -> dict:
    """
    Deserialize Websocket data. Websocket messages are in a container which contains additional data.
    A message type 'msg' represents a normal WebcastResponse

    :param binary_message: The binary to decode
    :return: The resultant decoded python dictionary

    """

    decoded: dict = deserialize_message("WebcastWebsocketMessage", binary_message)
    return {**decoded, **deserialize_message("WebcastResponse", decoded.get("binary"))} if decoded.get("type") == "msg" else dict()


def from_dict_plus(data_class: Type[T], data: Data, config: Optional[Config] = None) -> Any:
    """
    Load a schema from a dict and set the _as_dict attribute automatically

    :param data_class: Data class schema
    :param data: Data to fit into data class
    :param config: Config for dacite
    :return: A dataclass containing type T

    """

    result = from_dict(data_class, data, config)
    if isinstance(result, data_class):
        result._as_dict = data
    return result
