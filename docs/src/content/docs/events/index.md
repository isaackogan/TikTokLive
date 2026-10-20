---
title: Event catalog
description: Every TikTokLive event, the Webcast message it carries, what it means, and the page that documents it.
sidebar:
  order: 0
---

Register a handler with the `@client.on(Event)` decorator or with `client.add_listener(Event, handler)`. Both take the event class, and the handler receives one instance of it. A handler can be a coroutine or a plain function.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, LikeEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(CommentEvent)
async def on_comment(event: CommentEvent) -> None:
    if event.user is None:
        return
    print(f"{event.user.unique_id}: {event.content}")


def on_like(event: LikeEvent) -> None:
    print(f"+{event.count} likes, {event.total} in total")


client.add_listener(LikeEvent, on_like)

if __name__ == "__main__":
    client.run()
```

This checkout defines 74 events: 62 proto events and 12 custom events. A proto event subclasses its TikTokLiveProto v3 message, so its fields are the message's fields; the tables below name the message, and each name on the grouped pages links to the [schema reference](/schema/) for the full field list. A custom event is created by the client: `ConnectEvent` and `DisconnectEvent` from the connection, `WebsocketResponseEvent` and `UnknownEvent` from the raw traffic, and the other eight from a proto event whose payload matches a marker. Every class is importable from `TikTokLive.events`.

A derived event is emitted in addition to its source, so a follow arrives as `FollowEvent` and then as `SocialEvent`, and a stream end as `LiveEndEvent` and then as `ControlEvent`; listen to one or the other to avoid counting it twice. Every message is also emitted as `WebsocketResponseEvent` before its own event. Register listeners before connecting: the first signed response can carry messages, and they are emitted right after `ConnectEvent` unless `process_connect_events=False`. See [connection lifecycle](/getting-started/connection/).

Nested messages such as `event.user` and `event.gift` are `Optional` and can be absent, so check for `None` before reading them. IDs are `int`, timestamps are `int` milliseconds or seconds as the schema says, and a message defined in the schema is not necessarily sent in every room or region.

## Find an event

### Control

The client's own lifecycle and the raw WebSocket traffic. Details: [Control events](/events/control/).

| Event | Message | Description |
| --- | --- | --- |
| `ConnectEvent` | `custom` | The client connected to the room and parsed the first signed response |
| `DisconnectEvent` | `custom` | The WebSocket loop exited and the client disconnected from the room |
| `WebsocketResponseEvent` | `custom` | Any Webcast message was received (carries the raw fetch result it came from) |
| `UnknownEvent` | `custom` | A Webcast message arrived that TikTokLive has no event class for yet, useful for debugging |

### Chat and audience

Comments, joins, viewer counts, likes, follows, shares, questions, and emotes. Details: [Chat and audience](/events/chat-and-audience/).

| Event | Message | Description |
| --- | --- | --- |
| `CommentEvent` | `WebcastChatMessage` | A viewer sent a chat comment |
| `JoinEvent` | `WebcastMemberMessage` | A viewer joined the livestream |
| `RoomUserSeqEvent` | `WebcastRoomUserSeqMessage` | Current viewer count information |
| `LikeEvent` | `WebcastLikeMessage` | The stream received likes |
| `SocialEvent` | `WebcastSocialMessage` | A viewer shared or followed the host (also surfaced as `FollowEvent` / `ShareEvent` custom events) |
| `FollowEvent` | `custom` | A viewer followed the streamer |
| `ShareEvent` | `custom` | A viewer shared the livestream |
| `QuestionNewEvent` | `WebcastQuestionNewMessage` | Someone asked a new question via the question feature |
| `EmoteChatEvent` | `WebcastEmoteChatMessage` | A custom emote was sent in chat |

### Gifts and goals

Gifts, streaks, goals, and the gift panel. Details: [Gifts and goals](/events/gifts-and-goals/).

| Event | Message | Description |
| --- | --- | --- |
| `GiftEvent` | `WebcastGiftMessage` | A gift was sent (see [Gift handling](/events/gifts-and-goals/#giftevent) below) |
| `GoalUpdateEvent` | `WebcastGoalUpdateMessage` | Subscriber/follow goal updated |
| `BoostCardEvent` | `WebcastBoostCardMessage` | Boost cards delivered to the room |
| `GiftBroadcastEvent` | `WebcastGiftBroadcastMessage` | Big gift broadcast notice across rooms |
| `GiftDynamicRestrictionEvent` | `WebcastGiftDynamicRestrictionMessage` | Dynamic gift restriction update |
| `GiftPanelUpdateEvent` | `WebcastGiftPanelUpdateMessage` | Gift panel content update |
| `GiftPromptEvent` | `WebcastGiftPromptMessage` | Anti-addiction / spending-limit prompt before gifting |

### Battles and cohosting

Battles, Power-Ups, and link-mic (cohost and multi-guest) signalling. Details: [Battles and cohosting](/events/battles-and-cohosting/).

| Event | Message | Description |
| --- | --- | --- |
| `LinkMicBattleEvent` | `WebcastLinkMicBattle` | A battle was started |
| `LinkMicArmiesEvent` | `WebcastLinkMicArmies` | A battle user received points |
| `LinkMicBattleItemCardEvent` | `WebcastLinkMicBattleItemCard` | A battle Power-Up card was obtained, used, or awarded |
| `LinkMicBattlePunishFinishEvent` | `WebcastLinkMicBattlePunishFinish` | A battle's punishment phase ended |
| `LinkmicBattleTaskEvent` | `WebcastLinkmicBattleTaskMessage` | A battle task started, progressed, settled, or paid out its reward |
| `LinkMicFanTicketMethodEvent` | `WebcastLinkMicFanTicketMethod` | Fan-ticket totals for a link-mic session were announced |
| `LinkMicMethodEvent` | `WebcastLinkMicMethod` | Link-mic signalling between cohosts (invite, reply, channel setup, and RTC details) |
| `LinkEvent` | `WebcastLinkMessage` | Generic link-mic event |
| `LinkLayerEvent` | `WebcastLinkLayerMessage` | Link-mic layer/visibility change |
| `LinkMicLayoutStateEvent` | `WebcastLinkMicLayoutStateMessage` | Link-mic layout state update |
| `LinkStateEvent` | `WebcastLinkStateMessage` | Link-mic channel state update |
| `SpeakerEvent` | `WebcastSpeakerMessage` | Active speaker update (link-mic audio) |

### Subscriptions and super fans

Barrages, super fans, envelopes, and subscriptions. Details: [Subscriptions and super fans](/events/subscriptions-and-fans/).

| Event | Message | Description |
| --- | --- | --- |
| `BarrageEvent` | `WebcastBarrageMessage` | A "VIP" viewer (based on gifting level) joins the chat room |
| `SuperFanEvent` | `custom` | A viewer became a super fan of the streamer |
| `SuperFanJoinEvent` | `custom` | An existing super fan joined the livestream |
| `EnvelopeEvent` | `WebcastEnvelopeMessage` | A treasure chest / envelope was sent |
| `SuperFanBoxEvent` | `custom` | A super-fan envelope (gift box) was delivered |
| `SubNotifyEvent` | `WebcastSubNotifyMessage` | Subscription notification (subscribe / renew / gift sub) |
| `SubPinEventEvent` | `WebcastSubPinEventMessage` | Subscription pin card action |

### Room messages and display

Announcements, captions, polls, pins, banners, and other presentation messages. Details: [Room messages and display](/events/room-and-display/).

| Event | Message | Description |
| --- | --- | --- |
| `LiveIntroEvent` | `WebcastLiveIntroMessage` | Live-intro message appears |
| `SystemEvent` | `WebcastSystemMessage` | A plain-text system message from TikTok |
| `RoomEvent` | `WebcastRoomMessage` | Broadcast message to all room users (e.g. "Welcome to TikTok LIVE!") |
| `CaptionEvent` | `WebcastCaptionMessage` | Auto-caption update from the host's audio |
| `InRoomBannerEvent` | `WebcastInRoomBannerMessage` | In-room banner notice |
| `PollEvent` | `WebcastPollMessage` | The creator launched / updated a poll |
| `RoomPinEvent` | `WebcastRoomPinMessage` | A message was pinned |
| `BottomEvent` | `WebcastBottomMessage` | Bottom-of-screen notice (often a punishment or violation banner) |
| `CapsuleEvent` | `WebcastCapsuleMessage` | In-room capsule / promotional pill notice |
| `GuideEvent` | `WebcastGuideMessage` | In-room guide / tooltip prompt |
| `MarqueeAnnouncementEvent` | `WebcastMarqueeAnnouncementMessage` | Marquee announcement scrolling across the room |
| `NoticeEvent` | `WebcastNoticeMessage` | Generic notice / system tip in the room |
| `RoomNotifyEvent` | `WebcastRoomNotifyMessage` | Room-wide notification banner |
| `ToastEvent` | `WebcastToastMessage` | Transient toast notification |
| `ViewerPicksUpdateEvent` | `WebcastViewerPicksUpdateMessage` | Viewer-picks (audience-driven prompt) update |

### Rankings

Hourly ranks, leaderboard entrances, and rank text. Details: [Rankings](/events/rankings/).

| Event | Message | Description |
| --- | --- | --- |
| `HourlyRankRewardEvent` | `WebcastHourlyRankRewardMessage` | Hourly rank reward delivered |
| `RankUpdateEvent` | `WebcastRankUpdateMessage` | Room ranking entrance updated (rank types, current rank, and tabs) |
| `RankTextEvent` | `WebcastRankTextMessage` | Gift count made a viewer enter the top three |
| `GameRankNotifyEvent` | `WebcastGameRankNotifyMessage` | Game-rank notification |

### Moderation and access

Deletions, access control, verification, and warnings. Details: [Moderation and access](/events/moderation-and-access/).

| Event | Message | Description |
| --- | --- | --- |
| `ImDeleteEvent` | `WebcastImDeleteMessage` | A viewer's messages were deleted by a moderator |
| `UnauthorizedMemberEvent` | `WebcastUnauthorizedMemberMessage` | An unauthorized viewer entered the room (nickname and entry text only, no user object) |
| `MessageDetectEvent` | `WebcastMsgDetectMessage` | Message-delivery probe carrying detection flags and timing information |
| `RoomVerifyEvent` | `WebcastRoomVerifyMessage` | Room verification action (e.g. forced verify / close) |
| `AccessControlEvent` | `WebcastAccessControlMessage` | Access-control update for the room (e.g. CAPTCHA challenge issued to a viewer) |
| `AccessRecallEvent` | `WebcastAccessRecallMessage` | Access restriction lifted / recalled for a viewer |
| `PerceptionEvent` | `WebcastPerceptionMessage` | Perception dialog (warning / violation surfaced to a viewer) |

### Games, commerce, and partnerships

Live shopping, live games, and partnership campaigns. Details: [Games, commerce, and partnerships](/events/games-and-commerce/).

| Event | Message | Description |
| --- | --- | --- |
| `OecLiveShoppingEvent` | `WebcastOecLiveShoppingMessage` | Live-shopping signal |
| `LiveGameIntroEvent` | `WebcastLiveGameIntroMessage` | Live-game intro message |
| `PartnershipDropsUpdateEvent` | `WebcastPartnershipDropsUpdateMessage` | Partnership drops campaign update |
| `PartnershipGameOfflineEvent` | `WebcastPartnershipGameOfflineMessage` | Partnership game taken offline |
| `PartnershipPunishEvent` | `WebcastPartnershipPunishMessage` | Partnership punishment notice |

### Stream control

Stream start, pause, resume, end, and suspension. Details: [Stream control](/events/stream-control/).

| Event | Message | Description |
| --- | --- | --- |
| `ControlEvent` | `WebcastControlMessage` | Stream action (e.g. start, end, pause, unpause) |
| `LiveEndEvent` | `custom` | The livestream ended or was suspended |
| `LivePauseEvent` | `custom` | The livestream was paused |
| `LiveUnpauseEvent` | `custom` | A paused livestream resumed |
