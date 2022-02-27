from dataclasses import dataclass
from typing import List, Optional


class AbstractObject:
    pass


@dataclass()
class Avatar(AbstractObject):
    urls: List[str]

    @property
    def avatar_url(self):
        return self.urls[-1]


@dataclass()
class ExtraAttributes(AbstractObject):
    followRole: Optional[int]


@dataclass()
class User(AbstractObject):
    userId: Optional[int]
    uniqueId: Optional[str]
    nickname: Optional[str]
    profilePicture: Optional[Avatar]
    extraAttributes: Optional[ExtraAttributes]

    @property
    def is_following(self) -> bool:
        return (
            self.extraAttributes is not None
            and self.extraAttributes.followRole is not None
            and self.extraAttributes.followRole >= 1
        )

    @property
    def is_friend(self) -> bool:
        return (
                self.extraAttributes is not None
                and self.extraAttributes.followRole is not None
                and self.extraAttributes.followRole >= 2
        )


@dataclass()
class Gift(AbstractObject):
    anchor_id: Optional[int]
    from_idc: Optional[str]
    from_user_id: Optional[int]
    gift_id: Optional[int]
    gift_type: Optional[int]
    log_id: Optional[str]
    msg_id: Optional[int]
    profitapi_message_dur: Optional[int]
    repeat_count: Optional[int]
    repeat_end: Optional[int]
    room_id: Optional[int]
    send_gift_profit_api_start_ms: Optional[int]
    send_gift_profit_core_start_ms: Optional[int]
    send_gift_req_start_ms: Optional[int]
    send_gift_send_message_success_ms: Optional[int]
    send_profitapi_dur: Optional[int]
    to_user_id: Optional[int]
