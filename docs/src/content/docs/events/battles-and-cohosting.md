---
title: Battles and cohosting
description: Battle, Power-Up, and link-mic events for cohost and multi-guest sessions, with the enum values that distinguish their subtypes.
sidebar:
  order: 4
---

A battle is a timed contest between linked hosts scored in diamonds; link-mic is the channel that connects them, and the same channel carries cohost and multi-guest sessions without a battle. These events keep their schema fields; the client does not merge them into one battle model. Host IDs appear as `int` keys and `anchor_id_str` strings in the same message.

Each section names the Webcast message and links its schema page, which lists every field. Replace `@isaackogz` with a creator who is live. Each example registers its listener before connecting.

## LinkMicBattleEvent

A battle was started. Message: [`WebcastLinkMicBattle`](/schema/webcast/model/message/webcastlinkmicbattle/).

The same message reports every stage of a battle, so check `action` before treating it as a start. Key fields: `battle_id`; `action`, a `LinkMicBattleBattleAction` such as `INVITE`, `ACCEPT`, `REJECT`, `CANCEL`, `OPEN`, `FINISH`, `QUIT_APPLY`, or `LEAVE_LINKMIC`; `battle_settings`, a `BattleSetting` with the duration and rules; `anchors_info`, the participating hosts as `BattleUserInfoWrapper` objects keyed by user ID; `armies`; `battle_result`, a dict from host user ID to `BattleResult` with `result`, `score`, and `diamond_score`, filled on `FINISH`; `team_member`, `team_armies`, and `team_battle_result` for team battles; `action_by_user_id`; and `bubble_text`.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import LinkMicBattleEvent
from TikTokLiveProto.v3.webcast.im import LinkMicBattleBattleAction

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(LinkMicBattleEvent)
async def on_battle(event: LinkMicBattleEvent) -> None:
    if event.action == LinkMicBattleBattleAction.OPEN:
        print(f"Battle {event.battle_id} started with {len(event.anchors_info)} hosts")
    elif event.action == LinkMicBattleBattleAction.FINISH:
        for user_id, result in event.battle_result.items():
            print(f"  host {user_id}: {result.score} points")


if __name__ == "__main__":
    client.run()
```

## LinkMicArmiesEvent

A battle user received points. Message: [`WebcastLinkMicArmies`](/schema/webcast/model/message/webcastlinkmicarmies/).

Key fields: `battle_id` and `channel_id`; `armies`, a dict from host user ID to `BattleUserArmies` with `hostscore`, the host's current score, and `user_armies`, the top contributors; `team_armies`; `trigger_reason`, a `LinkMicArmiesTriggerReason` of `SCORE_UPDATE`, `BATTLE_END`, `OPT_OUT_UPDATE`, `KEEP_ALIVE`, or `EFFECT_UPDATE`; `from_user_id`, `gift_id`, `gift_count`, `gift_icon_image`, `repeat_count`, and `total_diamond_count` for the gift that triggered the update; `trigger_critical_strike`; and `battle_settings`. A `KEEP_ALIVE` update carries scores without a gift.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import LinkMicArmiesEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(LinkMicArmiesEvent)
async def on_armies(event: LinkMicArmiesEvent) -> None:
    scores = {host_id: armies.hostscore for host_id, armies in event.armies.items()}
    print(f"Battle {event.battle_id} ({event.trigger_reason.name}): {scores}")


if __name__ == "__main__":
    client.run()
```

## LinkMicBattleItemCardEvent

A battle Power-Up card was obtained, used, or awarded. Message: [`WebcastLinkMicBattleItemCard`](/schema/webcast/model/message/webcastlinkmicbattleitemcard/).

Key fields: `battle_id`; `msg_type`, a `BattleCardMsgType` naming the card and action: `CARD_OBTAIN_GUIDE`, `AWARD_CARD_NOTICE`, `SPECIAL_EFFECT_NOTICE`, or one of `USE_CRITICAL_STRIKE_CARD`, `USE_SMOKE_CARD`, `USE_EXTRA_TIME_CARD`, `USE_SPECIAL_EFFECT_CARD`, `USE_POTION_CARD`, `USE_WAVE_CARD`, `USE_TOP_2_CARD`, `USE_TOP_3_CARD`, and `USE_VAULT_GLOVE_CARD`; one nested message per type (`card_obtain_guide`, `award_card_notice`, `use_critical_strike_card`, `use_smoke_card`, and so on), of which only the one matching `msg_type` is set; and `award_reason`.

## LinkMicBattlePunishFinishEvent

A battle's punishment phase ended. Message: [`WebcastLinkMicBattlePunishFinish`](/schema/webcast/model/message/webcastlinkmicbattlepunishfinish/).

Key fields: `battle_id` and `channel_id`; `reason`, `TIME_UP` or `CUT_SHORT`; `op_uid`, the user who cut it short; `battle_settings`; and `match_punish_extra_info`.

## LinkmicBattleTaskEvent

A battle task started, progressed, settled, or paid out its reward. Message: [`WebcastLinkmicBattleTaskMessage`](/schema/webcast/model/message/webcastlinkmicbattletaskmessage/).

Key fields: `battle_id`; `task_message_type`, a `BattleTaskMessageType` of `START`, `TASK_UPDATE`, `TASK_SETTLE`, or `REWARD_SETTLE`; and one nested message per type: `start` with its `config`, `task_update` with `progress`, `from_user_id`, and `prompt_key`, `task_settle` with `result` and `reward_start_time`, and `reward`.

## LinkMicFanTicketMethodEvent

Fan-ticket totals for a link-mic session were announced. Message: [`WebcastLinkMicFanTicketMethod`](/schema/webcast/model/message/webcastlinkmicfanticketmethod/).

Key fields: `fan_ticket_room_notice`, a `FanTicketRoomNoticeContent` with `user_fan_ticket`, the per-user totals, `total_linkmic_fan_ticket`, `match_id`, `event_time`, `fan_ticket_icon_url`, `play_id`, `play_scene`, and `score_type`.

## LinkMicMethodEvent

Link-mic signalling between cohosts (invite, reply, channel setup, and RTC details). Message: [`WebcastLinkMicMethod`](/schema/webcast/model/message/webcastlinkmicmethod/).

Key fields: `message_type`, a plain `int` whose values are not named in the schema; `channel_id`, `anchor_linkmic_id`, and `rival_anchor_id`; `user_id`, `from_user_id`, `to_user_id`, and `invite_uid`; `answer`, `reply_type`, and `reply_prompts` for a reply; `start_time`, `start_time_ms`, and `duration`; `layout`, `linkmic_layout`, and `scene`; `linked_users`; `fan_ticket` and `total_linkmic_fan_ticket`; `tips` and `prompts`; and the RTC fields `rtc_app_id`, `rtc_ext_info`, `rtc_join_channel`, and `access_key`. Verify the numeric subtypes against a live session before relying on them.

## LinkEvent

Generic link-mic event. Message: [`WebcastLinkMessage`](/schema/webcast/model/message/webcastlinkmessage/).

Key fields: `message_type`, a plain `int`; `linker_id` and `scene`; and one nested `*_content` message per type, such as `invite_content`, `reply_content`, `create_content`, `close_content`, `enter_content`, `leave_content`, `cancel_content`, `kick_out_content`, `linked_list_change_content`, `waiting_list_change_content`, `mute_content`, `cohost_list_change_content`, `media_change_content`, `mic_idx_update_content`, and `sys_kick_out_content`; plus `extra`, `expire_timestamp`, and `version`. Only the content matching the type is set; the others are `None`.

## LinkLayerEvent

Link-mic layer/visibility change. Message: [`WebcastLinkLayerMessage`](/schema/webcast/model/message/linkcore/webcastlinklayermessage/).

Key fields: `message_type`, a `LinkLayerMessageType` such as `LINKER_CREATE`, `LINKER_INVITE`, `LINKER_APPLY`, `LINKER_PERMIT`, `LINKER_REPLY`, `LINKER_KICK_OUT`, `LINKER_LEAVE`, `LINKER_FINISH`, `LINKER_LIST_CHANGE`, or the `LINKER_*_GROUP` values; `channel_id`, `scene`, `linker_mode`, `rtc_room_id`, and `version`; and one nested `*_content` message per type (`create_channel_content`, `invite_content`, `apply_content`, `permit_apply_content`, `reply_invite_content`, `kick_out_content`, `leave_content`, `finish_content`, `list_change_content`, the group contents, and `business_content`).

## LinkMicLayoutStateEvent

Link-mic layout state update. Message: [`WebcastLinkMicLayoutStateMessage`](/schema/webcast/im/webcastlinkmiclayoutstatemessage/).

Key fields: `channel_id`, `scene`, and `version`; `biz_layout_state`, with `multi_guest_biz_layout_extra` and `co_host_biz_layout_extra`; and `biz_spot_list`, the `BizSpotInfo` entries with `spot_id`, `pos_identity`, and `biz_spot_extra`. Apply updates in `version` order.

## LinkStateEvent

Link-mic channel state update. Message: [`WebcastLinkStateMessage`](/schema/webcast/im/webcastlinkstatemessage/).

Key fields: `channel_id`, `scene`, `version`, and `state_type`; `layout`, a `LayoutState` with `layout_id` and `layout_key`; `user_states`, the `LinkUserState` entries with `user`, `linkmic_id`, `pos`, `audio_muted`, `video_muted`, and `online_user_state`; `spot_list` and `ui_pos`; `background` and `wallpaper_url`; `audio_muted_remote_channels`; `linker_mode`; and `need_ack`.

## SpeakerEvent

Active speaker update (link-mic audio). Message: [`WebcastSpeakerMessage`](/schema/webcast/model/message/webcastspeakermessage/).

The installed v3 schema defines only `common` for this message, so the event cannot identify the speaker. Listen to it as a signal that speaker state changed.
