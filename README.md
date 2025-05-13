TikTokLive API
==================
This is an unofficial API wrapper for TikTok LIVE written in Python. With this API you can connect to any TikTok livestream and fetch all data available to users in a stream using just a creator's `@unique_id`.

[![Discord](https://img.shields.io/discord/977648006063091742?logo=discord&label=TikTokLive%20Discord&labelColor=%23171717&color=%231877af)](https://discord.gg/N3KSxzvDX8)
![Connections](https://tiktok.eulerstream.com/analytics/pips/1)
![Downloads](https://pepy.tech/badge/tiktoklive)
![Stars](https://img.shields.io/github/stars/isaackogan/TikTokLive?style=flat&color=0274b5)
![Forks](https://img.shields.io/github/forks/isaackogan/TikTokLive?style=flat&color=0274b5)
![Issues](https://img.shields.io/github/issues/isaackogan/TikTokLive)

<!-- [![HitCount](https://hits.dwyl.com/isaackogan/TikTokLive.svg?style=flat)](http://hits.dwyl.com/isaackogan/TikTokLive) -->

<!--

COMING SOON:

## TikTok LIVE Interactive Bots

<table>
<tr>
    <td><br/><img width="180px" style="border-radius: 10px" src="https://raw.githubusercontent.com/isaackogan/TikTokLive/master/.github/BotsLogo.png"><br/><br/></td>
    <td>
        <a href="https://www.github.com/isaackogan/TikTokLive.py">
          Build interactive chatbots to increase retention & elevate user experience with the open source TikTokLive bot famework and a  <strong>Euler Stream</strong> API key.
        </a>
    </td>
</tr>
</table>

-->

## Enterprise Solutions

For enterprise-level service & greater rate limits, sign up with Euler Stream today:

<table>
<tr>
    <td><br/><img width="180px" style="border-radius: 10px" src="https://raw.githubusercontent.com/isaackogan/TikTokLive/master/.github/SquareLogo.png"><br/><br/></td>
    <td>
        <a href="https://www.eulerstream.com">
            <strong>Euler Stream</strong> provides increased rate limits, TikTok LIVE alerts, JWT authentication and more for enterprise customers. It offers generous tiers 
            starting at $0.
        </a>
    </td>
</tr>
</table>

<!--
Temporarily Removed May 3rd 2025

## Author's Choice

The following are my two favourite enterprise use-cases for the TikTokLive family of libraries. This is <strong>not</strong> paid promotion, and I receive nothing for these recommendations:

<table>
<tr>
    <td><br/><img width="180px" style="border-radius: 10px" src="https://tiktory.com/images/meta/favicon.svg"><br/><br/></td>
    <td>
        <a href="https://www.tiktory.com">
            <strong>Tiktory</strong> provides highly advanced custom overlays, follower alerts, and real-time goal tracking. Seamlessly integrate with OBS and stand out from the crowd!
        </a>
    </td>
</tr>
</table>

<table>
<tr>
    <td><br/><img width="180px" style="border-radius: 10px" src="https://cdn.casterlabs.co/branding/casterlabs/icon.svg"><br/><br/></td>
    <td>
        <a href="https://casterlabs.co/">
            <strong>Casterlabs</strong> is a powerful tool that unifies chats from various streaming platforms, providing a combined chat view, customizable alerts, and handy on-screen widgets for streamers!
        </a>
    </td>
</tr>
</table>

-->

## Table of Contents

- [Getting Started](#getting-started)
    - [Parameters](#parameters)
    - [Methods](#methods)
    - [Properties](#properties)
    - [WebDefaults](#webdefaults)
- [Documentation](https://isaackogan.github.io/TikTokLive/)
- [Other Languages](#other-languages)
- [Community](#community)
- [Examples](https://github.com/isaackogan/TikTokLive/tree/master/examples)
- [Licensing](#license)
- [Star History](#star-history)
- [Contributors](#contributors)

## Community

Join the [TikTokLive discord](https://discord.gg/e2XwPNTBBr) and visit
the [`#py-support`](https://discord.gg/uja6SajDxd)
channel for questions, contributions and ideas.

## Getting Started

1. Install the module via pip from the [PyPi](https://pypi.org/project/TikTokLive/) repository

```shell script
pip install TikTokLive
```

2. Create your first chat connection

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent

# Create the client
client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


# Listen to an event with a decorator!
@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent):
    print(f"Connected to @{event.unique_id} (Room ID: {client.room_id}")


# Or, add it manually via "client.add_listener()"
async def on_comment(event: CommentEvent) -> None:
    print(f"{event.user.nickname} -> {event.comment}")


client.add_listener(CommentEvent, on_comment)

if __name__ == '__main__':
    # Run the client and block the main thread
    # await client.start() to run non-blocking
    client.run()
```

For more quickstart examples, see the [examples folder](https://github.com/isaackogan/TikTokLive/tree/master/examples)
provided in the source tree.

## Other Languages

TikTokLive is available in several alternate programming languages:

- **Node.JS:** [https://github.com/zerodytrash/TikTok-Live-Connector](https://github.com/zerodytrash/TikTok-Live-Connector)
- **Java:** [https://github.com/jwdeveloper/TikTok-Live-Java](https://github.com/jwdeveloper/TikTok-Live-Java)
- **C#/Unity:** [https://github.com/frankvHoof93/TikTokLiveSharp](https://github.com/frankvHoof93/TikTokLiveSharp)
- **Go:** [https://github.com/steampoweredtaco/gotiktoklive](https://github.com/steampoweredtaco/gotiktoklive)
- **Rust:** [https://github.com/jwdeveloper/TikTokLiveRust](https://github.com/jwdeveloper/TikTokLiveRust)

## Parameters

| Param Name | Required | Default | Description                                                                                                                                                                                                               |
|------------|----------|---------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| unique_id  | Yes      | N/A     | The unique username of the broadcaster. You can find this name in the URL of the user. For example, the `unique_id` for [`https://www.tiktok.com/@isaackogz`](https://www.tiktok.com/@isaackogz) would be `isaackogz`.    |
| web_proxy  | No       | `None`  | TikTokLive supports proxying HTTP requests. This parameter accepts an `httpx.Proxy`. Note that if you do use a proxy you may be subject to reduced connection limits at times of high load.                               |
| ws_proxy   | No       | `None`  | TikTokLive supports proxying the websocket connection. This parameter accepts an `httpx.Proxy`. Using this proxy will never be subject to reduced connection limits.                                                      |
| web_kwargs | No       | `{}`    | Under the scenes, the TikTokLive HTTP client uses the [`httpx`](https://github.com/encode/httpx) library. Arguments passed to `web_kwargs` will be forward the the underlying HTTP client.                                |
| ws_kwargs  | No       | `{}`    | Under the scenes, TikTokLive uses the [`websockets`](https://github.com/python-websockets/websockets) library to connect to TikTok. Arguments passed to `ws_kwargs` will be forwarded to the underlying WebSocket client. |

## Methods

A `TikTokLiveClient` object contains the following methods worth mentioning:

| Method Name  | Notes   | Description                                                                                                                                                                         |
|--------------|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| run          | N/A     | Connect to the livestream and block the main thread. This is best for small scripts.                                                                                                |
| add_listener | N/A     | Adds an *asynchronous* listener function (or, you can decorate a function with `@client.on(Type[Event])`) and takes two parameters, an event name and the payload, an AbstractEvent ||
| connect      | `async` | Connects to the tiktok live chat while blocking the current future. When the connection ends (e.g. livestream is over), the future is released.                                     |
| start        | `async` | Connects to the live chat without blocking the main thread. This returns an `asyncio.Task` object with the client loop.                                                             |
| disconnect   | `async` | Disconnects the client from the websocket gracefully, processing remaining events before ending the client loop.                                                                    |

## Properties

A `TikTokLiveClient` object contains the following important properties:

| Attribute Name | Description                                                                                                                                                 |
|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| room_id        | The Room ID of the livestream room the client is currently connected to.                                                                                    |
| web            | The TikTok HTTP client. This client has a lot of useful routes you should explore!                                                                          |
| connected      | Whether you are currently connected to the livestream.                                                                                                      |
| logger         | The internal logger used by TikTokLive. You can use `client.logger.setLevel(...)` method to enable client debug.                                            |
| room_info      | Room information that is retrieved from TikTok when you use a connection method (e.g. `client.connect`) with the keyword argument `fetch_room_info=True` .  |
| gift_info      | Extra gift information that is retrieved from TikTok when you use a connection method (e.g. `client.run`) with the keyword argument `fetch_gift_info=True`. |

## WebDefaults

TikTokLive has a series of global defaults used to create the HTTP client which you can customize. For info on how to set these parameters, see
the [web_defaults.py](https://github.com/isaackogan/TikTokLive/blob/master/examples/web_defaults.py) example.

| Parameter                   | Type   | Description                                                                                                                                                                   |
|-----------------------------|--------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| tiktok_sign_api_key         | `str`  | A [Euler Stream](https://www.eulerstream.com/) API key used to increase rate limits.                                                                                          |
| tiktok_app_url              | `str`  | The TikTok app URL (`https://www.tiktok.com`) used to scrape the room.                                                                                                        |
| tiktok_sign_url             | `str`  | The [signature server](https://www.eulerstream.com/) used to generate tokens to connect to TikTokLive. By default, this is Euler Stream, but you can swap your own with ease. |
| tiktok_webcast_url          | `str`  | The TikTok livestream URL (`https://webcast.tiktok.com`) where livestreams can be accessed from.                                                                              |
| web_client_params           | `dict` | The URL parameters added on to TikTok requests from the HTTP client.                                                                                                          |
| web_client_headers          | `dict` | The headers added on to TikTok requests from the HTTP client.                                                                                                                 |
| web_client_cookies          | `dict` | Custom cookies to initialize the http client with.                                                                                                                            |
| ws_client_params            | `dict` | The URL parameters added to the URI when connecting to TikTok's Webcast WebSocket server.                                                                                     |
| ws_client_params_append_str | `dict` | Extra string data to append to the TikTokLive WebSocket connection URI.                                                                                                       |
| ws_client_headers           | `dict` | Extra headers to append to the TikTokLive WebSocket client.                                                                                                                   |
| ja3_impersonate             | `str`  | The ja3 fingerprint to impersonate. This should match whatever the current version is on the Sign Server, or "privileged" methods will fail.                                  |

## Events

Events can be listened to using a decorator or non-decorator method call. The following examples illustrate how you can listen to an event:

```python
@client.on(LikeEvent)
async def on_like(event: LikeEvent) -> None:
    ...


async def on_comment(event: CommentEvent) -> None:
    ...


client.add_listener(CommentEvent, on_comment)
```

There are two types of events, [`CustomEvent`](https://github.com/isaackogan/TikTokLive/blob/master/TikTokLive/events/custom_events.py)
events and [`ProtoEvent`](https://github.com/isaackogan/TikTokLive/blob/master/TikTokLive/events/proto_events.py) events.
Both belong to the TikTokLive `Event` type and can be listened to. The following events are available:

### Custom Events

- `ConnectEvent` - Triggered when the Webcast connection is initiated
- `DisconnectEvent` - Triggered when the Webcast connection closes (including the livestream ending)
- `LiveEndEvent` - Triggered when the livestream ends
- `LivePauseEvent` - Triggered when the livestream is paused
- `LiveUnpauseEvent` - Triggered when the livestream is unpaused
- `FollowEvent` - Triggered when a user in the livestream follows the streamer
- `ShareEvent` - Triggered when a user shares the livestream
- `WebsocketResponseEvent` - Triggered when any event is received (contains the event)
- `UnknownEvent` - An instance of `WebsocketResponseEvent` thrown whenever an event does not have an existing definition, useful for debugging

### Proto Events

If you know what an event does, [make a pull request](https://github.com/isaackogan/TikTokLive/pulls) and add the description.




<details>
<summary><h4>Proto Events</h4></summary>
<ul>
<li><code>GiftEvent</code> - Triggered when a gift is sent to the streamer</li>
<li><code>GoalUpdateEvent</code> - Triggered when the subscriber goal is updated</li>
<li><code>ControlEvent</code> - Triggered when a stream action occurs (e.g. Livestream start, end)</li>
<li><code>LikeEvent</code> - Triggered when the stream receives a like</li>
<li><code>SubscribeEvent</code> - Triggered when someone subscribes to the TikTok creator</li>
<li><code>PollEvent</code> - Triggered when the creator launches a new poll</li>
<li><code>CommentEvent</code> - Triggered when a comment is sent in the stream</li>
<li><code>RoomEvent</code> - Messages broadcasted to all users in the room (e.g. "Welcome to TikTok LIVE!")</li>
<li><code>EmoteChatEvent</code> - Triggered when a custom emote is sent in the chat</li>
<li><code>EnvelopeEvent</code> - Triggered every time someone sends a treasure chest</li>
<li><code>SocialEvent</code> - Triggered when a user shares the stream or follows the host</li>
<li><code>QuestionNewEvent</code> - Triggered every time someone asks a new question via the question feature</li>
<li><code>LiveIntroEvent</code> - Triggered when a live intro message appears</li>
<li><code>LinkMicArmiesEvent</code> - Triggered when a TikTok battle user receives points</li>
<li><code>LinkMicBattleEvent</code> - Triggered when a TikTok battle is started</li>
<li><code>JoinEvent</code> - Triggered when a user joins the livestream</li>
<li><code>LinkMicFanTicketMethodEvent</code></li>
<li><code>LinkMicMethodEvent</code></li>
<li><code>BarrageEvent</code> - Triggered when a "VIP" viewer (based on their gifting level) joins the live chat room</li>
<li><code>CaptionEvent</code></li>
<li><code>ImDeleteEvent</code> - Triggered when a viewer's messages are deleted</li>
<li><code>RoomUserSeqEvent</code> - Current viewer count information</li>
<li><code>RankUpdateEvent</code></li>
<li><code>RankTextEvent</code> - Triggered when gift count makes a viewer one of the top three</li>
<li><code>HourlyRankEvent</code></li>
<li><code>UnauthorizedMemberEvent</code></li>
<li><code>MessageDetectEvent</code></li>
<li><code>OecLiveShoppingEvent</code></li>
<li><code>RoomPinEvent</code> - Triggered when a message is pinned</li>
<li><code>SystemEvent</code></li>
<li><code>LinkEvent</code></li>
<li><code>LinkLayerEvent</code></li>
<li><code>KaraokeQueueListEvent</code></li>
<li><code>GroupLiveMemberNotifyEvent</code></li>
<li><code>SubscriptionGuideEvent</code></li>
<li><code>NoticeboardReviewEvent</code></li>
<li><code>BottomEvent</code></li>
<li><code>CapsuleEvent</code></li>
<li><code>LinkMicBattleEvent</code></li>
<li><code>QuestionSelectedEvent</code></li>
<li><code>TrayEvent</code></li>
<li><code>AssetEvent</code></li>
<li><code>WalletLiveRewardsRatioEvent</code></li>
<li><code>LinkScreenChangeEvent</code></li>
<li><code>PartnershipPunishEvent</code></li>
<li><code>GiftPanelUpdateEvent</code></li>
<li><code>AnchorTaskReminderEvent</code></li>
<li><code>LinkBusinessEvent</code></li>
<li><code>MarqueeAnnouncementEvent</code></li>
<li><code>GiftDynamicRestrictionEvent</code></li>
<li><code>CommonPopupEvent</code></li>
<li><code>EcBarrageEvent</code></li>
<li><code>PromoteAdStatusEvent</code></li>
<li><code>InteractionHubGoalEvent</code></li>
<li><code>EpiEvent</code></li>
<li><code>LinkmicAnimationEvent</code></li>
<li><code>KaraokeYouSingReqEvent</code></li>
<li><code>RealTimePerformancePageEvent</code></li>
<li><code>StreamStatusEvent</code></li>
<li><code>GiftCollectionUpdateEvent</code></li>
<li><code>CommercialCustomEvent</code></li>
<li><code>GuideEvent</code></li>
<li><code>DonationEvent</code></li>
<li><code>LiveGameIntroEvent</code></li>
<li><code>PartnershipDropsCardChangeEvent</code></li>
<li><code>GameGuessWidgetsEvent</code></li>
<li><code>MiddleTouchEvent</code></li>
<li><code>UserStatsEvent</code></li>
<li><code>WallpaperReviewEvent</code></li>
<li><code>LinkMicAdEvent</code></li>
<li><code>SubTimerStickerEvent</code></li>
<li><code>GiftGalleryEvent</code></li>
<li><code>GiftUpdateEvent</code></li>
<li><code>NoticeboardEvent</code></li>
<li><code>UpgradeEvent</code></li>
<li><code>BackpackEvent</code></li>
<li><code>AvatarStyleResultEvent</code></li>
<li><code>GameSettingChangeEvent</code></li>
<li><code>PartnershipDropsUpdateEvent</code></li>
<li><code>QuestionSwitchEvent</code></li>
<li><code>LiveInfoAuditNoticeEvent</code></li>
<li><code>CommonToastEvent</code></li>
<li><code>ToastEvent</code></li>
<li><code>DonationStickerModifyMethodEvent</code></li>
<li><code>PollEvent</code></li>
<li><code>HighlightFragementReadyEvent</code></li>
<li><code>GiftPromptEvent</code></li>
<li><code>ForceFetchRecommendationsEvent</code></li>
<li><code>GameGuessPinCardEvent</code></li>
<li><code>LinkLayoutEvent</code></li>
<li><code>GameOcrPingEvent</code></li>
<li><code>AnchorGrowLevelEvent</code></li>
<li><code>EnvelopePortalEvent</code></li>
<li><code>CohostReserveEvent</code></li>
<li><code>BaLeadGenEvent</code></li>
<li><code>PictionaryEndEvent</code></li>
<li><code>RoomNotifyEvent</code></li>
<li><code>FansEventEvent</code></li>
<li><code>KaraokeQueueEvent</code></li>
<li><code>FollowCardEvent</code></li>
<li><code>ActivityQuizUserIdentityEvent</code></li>
<li><code>LiveJourneyEvent</code></li>
<li><code>CommentsEvent</code></li>
<li><code>WeeklyRankRewardEvent</code></li>
<li><code>LinkStateEvent</code></li>
<li><code>AccessRecallEvent</code></li>
<li><code>AiSummaryEvent</code></li>
<li><code>PerceptionEvent</code></li>
<li><code>RoomVerifyEvent</code></li>
<li><code>GuideTaskEvent</code></li>
<li><code>VideoLiveCouponRcmdEvent</code></li>
<li><code>VideoLiveGoodsRcmdEvent</code></li>
<li><code>KaraokeSwitchEvent</code></li>
<li><code>PrivilegeAdvanceEvent</code></li>
<li><code>LinkMicBattlePunishFinishEvent</code></li>
<li><code>BoostedUsersEvent</code></li>
<li><code>RankToastEvent</code></li>
<li><code>CommentTrayEvent</code></li>
<li><code>AnchorReminderWordEvent</code></li>
<li><code>PaidContentLiveShoppingEvent</code></li>
<li><code>RoomEventEvent</code></li>
<li><code>RoomBottomEvent</code></li>
<li><code>DonationInfoEvent</code></li>
<li><code>GameMomentEvent</code></li>
<li><code>HashtagEvent</code></li>
<li><code>LinkMicBattleItemCardEvent</code></li>
<li><code>PrivilegeDynamicEffectEvent</code></li>
<li><code>AnchorGetSubQuotaEvent</code></li>
<li><code>OecLiveHotRoomEvent</code></li>
<li><code>AudienceReserveUserStateEvent</code></li>
<li><code>RealtimeLiveCenterMethodEvent</code></li>
<li><code>WallpaperEvent</code></li>
<li><code>SubPinEventEvent</code></li>
<li><code>LinkmicBattleTaskEvent</code></li>
<li><code>StarCommentPushEvent</code></li>
<li><code>EcTaskRefreshCouponListEvent</code></li>
<li><code>ShortTouchEvent</code></li>
<li><code>EffectControlEvent</code></li>
<li><code>KaraokeRedDotEvent</code></li>
<li><code>QuestionDeleteEvent</code></li>
<li><code>InRoomBannerEvent</code></li>
<li><code>ShareGuideEvent</code></li>
<li><code>EventEvent</code></li>
<li><code>InRoomBannerEventEvent</code></li>
<li><code>PlayTogetherEvent</code></li>
<li><code>SubContractStatusEvent</code></li>
<li><code>HourlyRankRewardEvent</code></li>
<li><code>PictionaryStartEvent</code></li>
<li><code>GuestInviteEvent</code></li>
<li><code>NoticeEvent</code></li>
<li><code>PartnershipDownloadCountEvent</code></li>
<li><code>GreetingEvent</code></li>
<li><code>LiveShowEvent</code></li>
<li><code>SubWaveEvent</code></li>
<li><code>GameReqSetGuessEvent</code></li>
<li><code>SpeakerEvent</code></li>
<li><code>LinkMicAnchorGuideEvent</code></li>
<li><code>CompetitionEvent</code></li>
<li><code>AvatarReportDeleteEvent</code></li>
<li><code>EffectPreloadingEvent</code></li>
<li><code>ColdStartEvent</code></li>
<li><code>CountdownForAllEvent</code></li>
<li><code>GiftBroadcastEvent</code></li>
<li><code>PreviewGameMomentEvent</code></li>
<li><code>GameRecommendCreateGuessEvent</code></li>
<li><code>VideoLiveGoodsOrderEvent</code></li>
<li><code>StarCommentNotificationEvent</code></li>
<li><code>InRoomBannerRefreshEvent</code></li>
<li><code>RoomStickerEvent</code></li>
<li><code>GiftProgressEvent</code></li>
<li><code>OecLiveManagerEvent</code></li>
<li><code>DiggEvent</code></li>
<li><code>AiLiveSummaryEvent</code></li>
<li><code>AnchorToolModificationEvent</code></li>
<li><code>MgPunishCenterActionEvent</code></li>
<li><code>PictionaryExitEvent</code></li>
<li><code>CountdownEvent</code></li>
<li><code>GameServerFeatureEvent</code></li>
<li><code>PlaybookEvent</code></li>
<li><code>GiftRecordCapsuleEvent</code></li>
<li><code>QuickChatListEvent</code></li>
<li><code>PartnershipCardChangeEvent</code></li>
<li><code>ScreenChatEvent</code></li>
<li><code>GameEmoteUpdateEvent</code></li>
<li><code>BoostCardEvent</code></li>
<li><code>RoomStreamAdaptationEvent</code></li>
<li><code>LinkmicBattleNoticeEvent</code></li>
<li><code>GoodyBagEvent</code></li>
</ul>
</details>

### Special Events

### `GiftEvent`

Triggered every time a gift arrives. Extra information can be gleamed from the `available_gifts` client attribute.
> **NOTE:** Users have the capability to send gifts in a streak. This increases the `event.gift.repeat_count` value until the
> user terminates the streak. During this time new gift events are triggered again and again with an
> increased `event.gift.repeat_count` value. It should be noted that after the end of a streak, a final gift event is
> triggered, which signals the end of the streak with `event.repeat_end`:`1`. The following handlers show how you can deal with this in your code.

Using the low-level direct proto:

```python
@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    # If it's type 1 and the streak is over
    if event.gift.info.type == 1:
        if event.gift.is_repeating == 1:
            print(f"{event.user.unique_id} sent {event.repeat_count}x \"{event.gift.name}\"")

    # It's not type 1, which means it can't have a streak & is automatically over
    elif event.gift.info.type != 1:
        print(f"{event.user.unique_id} sent \"{event.gift.name}\"")
```

Using the TikTokLive extended proto:

```python
@client.on("gift")
async def on_gift(event: GiftEvent):
    # Streakable gift & streak is over
    if event.gift.streakable and not event.streaking:
        print(f"{event.user.unique_id} sent {event.repeat_count}x \"{event.gift.name}\"")

    # Non-streakable gift
    elif not event.gift.streakable:
        print(f"{event.user.unique_id} sent \"{event.gift.name}\"")
```

### `SubscribeEvent`

This event will only fire when a session ID (account login) is passed to the HTTP client *before* connecting to TikTok LIVE.
You can set the session ID with [`client.web.set_session_id(...)`](https://github.com/isaackogan/TikTokLive/blob/master/examples/logged_in.py).

## Checking If A User Is Live

It is considered inefficient to use the connect method to check if a user is live. It is better to use the dedicated `await client.is_live()` method.

There is a [complete example](https://github.com/isaackogan/TikTokLive/blob/master/examples/check_live.py) of how to do this in the [examples](https://github.com/isaackogan/TikTokLive/tree/master/examples) folder.

## Star History

<p align="center">
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=isaackogan/TikTokLive&type=Date&theme=dark" onerror="this.src='https://api.star-history.com/svg?repos=isaackogan/TikTokLive&type=Date'" />
</p>

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributors

* **Isaac Kogan** - *Creator, Primary Maintainer, and Reverse-Engineering* - [isaackogan](https://github.com/isaackogan)
* **Zerody** - *Creator of the NodeJS library, introduced me to scraping TikTok LIVE* - [Zerody](https://github.com/zerodytrash/)

See also the full list of secondary [contributors](https://github.com/isaackogan/TikTokLive/contributors) who have participated in
this project.

