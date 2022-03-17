
from protobuf_to_dict import protobuf_to_dict

from TikTokLive.proto import tiktok_schema_pb2 as tiktok_schema


def serialize_message(proto_name, obj):
    schema = getattr(tiktok_schema, proto_name)()
    return schema.SerializeToString(obj)


def deserialize_message(proto_name, obj) -> dict:
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
                "WebcastLinkMicArmies"
            ]:
                continue

            _schema = getattr(tiktok_schema, message.get("type"))()
            _schema.ParseFromString(message.get("binary"))
            dict_data["messages"][idx] = protobuf_to_dict(_schema)

    return dict_data
