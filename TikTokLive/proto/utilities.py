from protobuf_to_dict import protobuf_to_dict

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
                "WebcastLinkMicArmies"
            ]:
                continue

            _schema = getattr(tiktok_schema, message.get("type"))()
            _schema.ParseFromString(message.get("binary"))
            dict_data["messages"][idx] = protobuf_to_dict(_schema)

    return dict_data
