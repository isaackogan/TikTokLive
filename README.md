# TikTok LIVE API for Python: Real-Time Livestream Events (Unofficial)

TikTok LIVE API (TikTokLive) is the #1 TikTok LIVE client for **Python**. Connect to any [TikTok LIVE](https://www.tiktok.com/live) stream and receive **real-time chat messages, gifts, likes, follows, shares, viewer counts, battles, and more** using just a creator's `@unique_id`. No login, no credentials or app are required.

TikTokLive is the definitive third-party Python library for reading the TikTok LIVE websocket, building TikTok chat bots, gift trackers, live stream overlays, alerts, and analytics tools.

Full documentation, guides, and the complete event reference are at [ttl.docs.isaackogan.com](https://ttl.docs.isaackogan.com/).

[![Discord](https://img.shields.io/discord/977648006063091742?logo=discord&label=TikTokLive%20Discord&labelColor=%23171717&color=%231877af)](https://discord.gg/N3KSxzvDX8)
![Live TikTok LIVE API connections](https://api.eulerstream.com/analytics/pips)
![TikTokLive PyPI downloads](https://pepy.tech/badge/tiktoklive)
![TikTokLive GitHub stars](https://img.shields.io/github/stars/isaackogan/TikTokLive?style=flat&color=0274b5)
![TikTokLive GitHub forks](https://img.shields.io/github/forks/isaackogan/TikTokLive?style=flat&color=0274b5)
![TikTokLive open issues](https://img.shields.io/github/issues/isaackogan/TikTokLive)

> **Note:** This is <strong>not</strong> a production-ready API. It is a reverse engineering project. Use the [WebSocket API](https://www.eulerstream.com/websockets) for production by [Euler Stream](https://www.eulerstream.com/).

## What Can You Build With the TikTok LIVE API?

- **TikTok live chat readers** and chat bots that respond to comments in real time
- **Gift trackers and donation alerts** for TikTok LIVE streamers (with streak handling)
- **OBS overlays and stream widgets** driven by live TikTok events
- **TikTok LIVE analytics**: viewer counts, likes, follows, battle (PK) scores
- **Moderation tools** that react to deleted messages and room events
- **Text-to-speech (TTS) readers** and interactive livestream games

## TikTok LIVE API for Production

<table>
<tr>
    <td><br/><img width="180px" style="border-radius: 10px" alt="Euler Stream TikTok LIVE API logo" src="https://raw.githubusercontent.com/isaackogan/TikTokLive/master/.github/SquareLogo.png"><br/><br/></td>
    <td>
        <a href="https://www.eulerstream.com/">
            <strong>Euler Stream</strong> offers a comprehensive TikTok LIVE API, WebSocket Server, CAPTCHA Solutions and much more!
        </a>
    </td>
</tr>
</table>

## Table of Contents

- [Getting Started](#getting-started)
    - [Parameters](#parameters)
    - [Methods](#methods)
    - [Properties](#properties)
    - [WebDefaults](#webdefaults)
- [Events](#events)
- [Documentation](https://ttl.docs.isaackogan.com/)
- [Other Languages](#tiktok-live-api-in-other-languages-nodejs-java-c-go-rust)
- [Community](#community)
- [Examples](https://github.com/isaackogan/TikTokLive/tree/master/examples)
- [FAQ](#frequently-asked-questions)
- [Licensing](#license)
- [Star History](#star-history)
- [Contributors](#contributors)

## Community

Join the [TikTokLive discord](https://discord.gg/e2XwPNTBBr) and visit
the [`#py-support`](https://discord.gg/uja6SajDxd)
channel for questions, contributions and ideas.

## Getting Started

Install the TikTok LIVE API client for Python via pip from the [PyPi](https://pypi.org/project/TikTokLive/) repository:

```shell script
pip install TikTokLive
```

Then create your first real-time TikTok LIVE chat connection:

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

For more quickstart examples, including a TikTok live chat reader, gift tracker, and live status checker, see the [examples folder](https://github.com/isaackogan/TikTokLive/tree/master/examples) provided in the source tree.

## TikTok LIVE API in Other Languages: Node.js, Java, C#, Go, Rust

The TikTokLive TikTok LIVE API is available in several alternate programming languages:

- **Node.JS / JavaScript / TypeScript:** [TikTok-Live-Connector](https://github.com/zerodytrash/TikTok-Live-Connector)
- **Java:** [TikTok-Live-Java](https://github.com/jwdeveloper/TikTok-Live-Java)
- **C# / Unity:** [TikTokLiveSharp](https://github.com/frankvHoof93/TikTokLiveSharp)
- **Go:** [gotiktoklive](https://github.com/steampoweredtaco/gotiktoklive)
- **Rust:** [TikTokLiveRust](https://github.com/jwdeveloper/TikTokLiveRust)

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
| ws_client_params_append_str | `str`  | Extra string data to append to the TikTokLive WebSocket connection URI.                                                                                                       |

## Events

The TikTok LIVE API emits real-time events for everything happening in a livestream: comments, gifts, likes, joins, follows, shares, battles (PK), polls, captions, subscriptions, and moderation actions. Events can be listened to using a decorator or non-decorator method call. The following examples illustrate how you can listen to an event:

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

- [`ConnectEvent`](https://ttl.docs.isaackogan.com/events/control/#connectevent) - Triggered when the Webcast connection is initiated
- [`DisconnectEvent`](https://ttl.docs.isaackogan.com/events/control/#disconnectevent) - Triggered when the Webcast connection closes (including the livestream ending)
- [`LiveEndEvent`](https://ttl.docs.isaackogan.com/events/stream-control/#liveendevent) - Triggered when the livestream ends
- [`LivePauseEvent`](https://ttl.docs.isaackogan.com/events/stream-control/#livepauseevent) - Triggered when the livestream is paused
- [`LiveUnpauseEvent`](https://ttl.docs.isaackogan.com/events/stream-control/#liveunpauseevent) - Triggered when the livestream is unpaused
- [`FollowEvent`](https://ttl.docs.isaackogan.com/events/chat-and-audience/#followevent) - Triggered when a user in the livestream follows the streamer
- [`ShareEvent`](https://ttl.docs.isaackogan.com/events/chat-and-audience/#shareevent) - Triggered when a user shares the livestream
- [`SuperFanEvent`](https://ttl.docs.isaackogan.com/events/subscriptions-and-fans/#superfanevent) - Triggered when a viewer becomes a super fan of the streamer
- [`SuperFanJoinEvent`](https://ttl.docs.isaackogan.com/events/subscriptions-and-fans/#superfanjoinevent) - Triggered when an existing super fan joins the live (distinct from `SuperFanEvent`)
- [`SuperFanBoxEvent`](https://ttl.docs.isaackogan.com/events/subscriptions-and-fans/#superfanboxevent) - Triggered when a super-fan envelope (gift box) is delivered
- [`WebsocketResponseEvent`](https://ttl.docs.isaackogan.com/events/control/#websocketresponseevent) - Triggered when any event is received (contains the event)
- [`UnknownEvent`](https://ttl.docs.isaackogan.com/events/control/#unknownevent) - An instance of `WebsocketResponseEvent` thrown whenever an event does not have an existing definition, useful for debugging

### Proto Events

These events are auto-generated from the
[TikTokLiveProto](https://pypi.org/project/TikTokLiveProto/) v3 schema. Only
events whose proto messages are present in v3 are emitted; if you don't see
one you used to rely on, it's because TikTok removed it from the schema.

If you know what an event does that's missing a description below,
[make a pull request](https://github.com/isaackogan/TikTokLive/pulls) and add it.

<ul>
<li><a href="https://ttl.docs.isaackogan.com/events/subscriptions-and-fans/#barrageevent"><code>BarrageEvent</code></a> - A "VIP" viewer (based on gifting level) joins the chat room</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#captionevent"><code>CaptionEvent</code></a> - Auto-caption update from the host's audio</li>
<li><a href="https://ttl.docs.isaackogan.com/events/chat-and-audience/#commentevent"><code>CommentEvent</code></a> - A viewer sent a chat comment</li>
<li><a href="https://ttl.docs.isaackogan.com/events/stream-control/#controlevent"><code>ControlEvent</code></a> - Stream action (e.g. start, end, pause, unpause)</li>
<li><a href="https://ttl.docs.isaackogan.com/events/chat-and-audience/#emotechatevent"><code>EmoteChatEvent</code></a> - A custom emote was sent in chat</li>
<li><a href="https://ttl.docs.isaackogan.com/events/subscriptions-and-fans/#envelopeevent"><code>EnvelopeEvent</code></a> - A treasure chest / envelope was sent</li>
<li><a href="https://ttl.docs.isaackogan.com/events/gifts-and-goals/#giftevent"><code>GiftEvent</code></a> - A gift was sent (see <a href="#giftevent">Gift handling</a> below)</li>
<li><a href="https://ttl.docs.isaackogan.com/events/gifts-and-goals/#goalupdateevent"><code>GoalUpdateEvent</code></a> - Subscriber/follow goal updated</li>
<li><a href="https://ttl.docs.isaackogan.com/events/rankings/#hourlyrankrewardevent"><code>HourlyRankRewardEvent</code></a> - Hourly rank reward delivered</li>
<li><a href="https://ttl.docs.isaackogan.com/events/moderation-and-access/#imdeleteevent"><code>ImDeleteEvent</code></a> - A viewer's messages were deleted by a moderator</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#inroombannerevent"><code>InRoomBannerEvent</code></a> - In-room banner notice</li>
<li><a href="https://ttl.docs.isaackogan.com/events/chat-and-audience/#joinevent"><code>JoinEvent</code></a> - A viewer joined the livestream</li>
<li><a href="https://ttl.docs.isaackogan.com/events/chat-and-audience/#likeevent"><code>LikeEvent</code></a> - The stream received likes</li>
<li><a href="https://ttl.docs.isaackogan.com/events/battles-and-cohosting/#linkevent"><code>LinkEvent</code></a> - Generic link-mic event</li>
<li><a href="https://ttl.docs.isaackogan.com/events/battles-and-cohosting/#linklayerevent"><code>LinkLayerEvent</code></a> - Link-mic layer/visibility change</li>
<li><a href="https://ttl.docs.isaackogan.com/events/battles-and-cohosting/#linkmicarmiesevent"><code>LinkMicArmiesEvent</code></a> - A battle user received points</li>
<li><a href="https://ttl.docs.isaackogan.com/events/battles-and-cohosting/#linkmicbattleevent"><code>LinkMicBattleEvent</code></a> - A battle was started</li>
<li><a href="https://ttl.docs.isaackogan.com/events/battles-and-cohosting/#linkmicbattleitemcardevent"><code>LinkMicBattleItemCardEvent</code></a> - A battle Power-Up card was obtained, used, or awarded</li>
<li><a href="https://ttl.docs.isaackogan.com/events/battles-and-cohosting/#linkmicbattlepunishfinishevent"><code>LinkMicBattlePunishFinishEvent</code></a> - A battle's punishment phase ended</li>
<li><a href="https://ttl.docs.isaackogan.com/events/battles-and-cohosting/#linkmicfanticketmethodevent"><code>LinkMicFanTicketMethodEvent</code></a> - Fan-ticket totals for a link-mic session were announced</li>
<li><a href="https://ttl.docs.isaackogan.com/events/battles-and-cohosting/#linkmicmethodevent"><code>LinkMicMethodEvent</code></a> - Link-mic signalling between cohosts (invite, reply, channel setup, and RTC details)</li>
<li><a href="https://ttl.docs.isaackogan.com/events/battles-and-cohosting/#linkmicbattletaskevent"><code>LinkmicBattleTaskEvent</code></a> - A battle task started, progressed, settled, or paid out its reward</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#liveintroevent"><code>LiveIntroEvent</code></a> - Live-intro message appears</li>
<li><a href="https://ttl.docs.isaackogan.com/events/moderation-and-access/#messagedetectevent"><code>MessageDetectEvent</code></a> - Message-delivery probe carrying detection flags and timing information</li>
<li><a href="https://ttl.docs.isaackogan.com/events/games-and-commerce/#oecliveshoppingevent"><code>OecLiveShoppingEvent</code></a> - Live-shopping signal</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#pollevent"><code>PollEvent</code></a> - The creator launched / updated a poll</li>
<li><a href="https://ttl.docs.isaackogan.com/events/chat-and-audience/#questionnewevent"><code>QuestionNewEvent</code></a> - Someone asked a new question via the question feature</li>
<li><a href="https://ttl.docs.isaackogan.com/events/rankings/#ranktextevent"><code>RankTextEvent</code></a> - Gift count made a viewer enter the top three</li>
<li><a href="https://ttl.docs.isaackogan.com/events/rankings/#rankupdateevent"><code>RankUpdateEvent</code></a> - Room ranking entrance updated (rank types, current rank, and tabs)</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#roomevent"><code>RoomEvent</code></a> - Broadcast message to all room users (e.g. "Welcome to TikTok LIVE!")</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#roompinevent"><code>RoomPinEvent</code></a> - A message was pinned</li>
<li><a href="https://ttl.docs.isaackogan.com/events/chat-and-audience/#roomuserseqevent"><code>RoomUserSeqEvent</code></a> - Current viewer count information</li>
<li><a href="https://ttl.docs.isaackogan.com/events/chat-and-audience/#socialevent"><code>SocialEvent</code></a> - A viewer shared or followed the host (also surfaced as <code>FollowEvent</code> / <code>ShareEvent</code> custom events)</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#systemevent"><code>SystemEvent</code></a> - A plain-text system message from TikTok</li>
<li><a href="https://ttl.docs.isaackogan.com/events/moderation-and-access/#unauthorizedmemberevent"><code>UnauthorizedMemberEvent</code></a> - An unauthorized viewer entered the room (nickname and entry text only, no user object)</li>
</ul>

#### More proto events

<ul>
<li><a href="https://ttl.docs.isaackogan.com/events/moderation-and-access/#accesscontrolevent"><code>AccessControlEvent</code></a> - Access-control update for the room (e.g. CAPTCHA challenge issued to a viewer)</li>
<li><a href="https://ttl.docs.isaackogan.com/events/moderation-and-access/#accessrecallevent"><code>AccessRecallEvent</code></a> - Access restriction lifted / recalled for a viewer</li>
<li><a href="https://ttl.docs.isaackogan.com/events/gifts-and-goals/#boostcardevent"><code>BoostCardEvent</code></a> - Boost cards delivered to the room</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#bottomevent"><code>BottomEvent</code></a> - Bottom-of-screen notice (often a punishment or violation banner)</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#capsuleevent"><code>CapsuleEvent</code></a> - In-room capsule / promotional pill notice</li>
<li><a href="https://ttl.docs.isaackogan.com/events/rankings/#gameranknotifyevent"><code>GameRankNotifyEvent</code></a> - Game-rank notification</li>
<li><a href="https://ttl.docs.isaackogan.com/events/gifts-and-goals/#giftbroadcastevent"><code>GiftBroadcastEvent</code></a> - Big gift broadcast notice across rooms</li>
<li><a href="https://ttl.docs.isaackogan.com/events/gifts-and-goals/#giftdynamicrestrictionevent"><code>GiftDynamicRestrictionEvent</code></a> - Dynamic gift restriction update</li>
<li><a href="https://ttl.docs.isaackogan.com/events/gifts-and-goals/#giftpanelupdateevent"><code>GiftPanelUpdateEvent</code></a> - Gift panel content update</li>
<li><a href="https://ttl.docs.isaackogan.com/events/gifts-and-goals/#giftpromptevent"><code>GiftPromptEvent</code></a> - Anti-addiction / spending-limit prompt before gifting</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#guideevent"><code>GuideEvent</code></a> - In-room guide / tooltip prompt</li>
<li><a href="https://ttl.docs.isaackogan.com/events/battles-and-cohosting/#linkmiclayoutstateevent"><code>LinkMicLayoutStateEvent</code></a> - Link-mic layout state update</li>
<li><a href="https://ttl.docs.isaackogan.com/events/battles-and-cohosting/#linkstateevent"><code>LinkStateEvent</code></a> - Link-mic channel state update</li>
<li><a href="https://ttl.docs.isaackogan.com/events/games-and-commerce/#livegameintroevent"><code>LiveGameIntroEvent</code></a> - Live-game intro message</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#marqueeannouncementevent"><code>MarqueeAnnouncementEvent</code></a> - Marquee announcement scrolling across the room</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#noticeevent"><code>NoticeEvent</code></a> - Generic notice / system tip in the room</li>
<li><a href="https://ttl.docs.isaackogan.com/events/games-and-commerce/#partnershipdropsupdateevent"><code>PartnershipDropsUpdateEvent</code></a> - Partnership drops campaign update</li>
<li><a href="https://ttl.docs.isaackogan.com/events/games-and-commerce/#partnershipgameofflineevent"><code>PartnershipGameOfflineEvent</code></a> - Partnership game taken offline</li>
<li><a href="https://ttl.docs.isaackogan.com/events/games-and-commerce/#partnershippunishevent"><code>PartnershipPunishEvent</code></a> - Partnership punishment notice</li>
<li><a href="https://ttl.docs.isaackogan.com/events/moderation-and-access/#perceptionevent"><code>PerceptionEvent</code></a> - Perception dialog (warning / violation surfaced to a viewer)</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#roomnotifyevent"><code>RoomNotifyEvent</code></a> - Room-wide notification banner</li>
<li><a href="https://ttl.docs.isaackogan.com/events/moderation-and-access/#roomverifyevent"><code>RoomVerifyEvent</code></a> - Room verification action (e.g. forced verify / close)</li>
<li><a href="https://ttl.docs.isaackogan.com/events/battles-and-cohosting/#speakerevent"><code>SpeakerEvent</code></a> - Active speaker update (link-mic audio)</li>
<li><a href="https://ttl.docs.isaackogan.com/events/subscriptions-and-fans/#subnotifyevent"><code>SubNotifyEvent</code></a> - Subscription notification (subscribe / renew / gift sub)</li>
<li><a href="https://ttl.docs.isaackogan.com/events/subscriptions-and-fans/#subpineventevent"><code>SubPinEventEvent</code></a> - Subscription pin card action</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#toastevent"><code>ToastEvent</code></a> - Transient toast notification</li>
<li><a href="https://ttl.docs.isaackogan.com/events/room-and-display/#viewerpicksupdateevent"><code>ViewerPicksUpdateEvent</code></a> - Viewer-picks (audience-driven prompt) update</li>
</ul>

### `GiftEvent`

Fires every time a gift is sent. Extra static metadata for every gift type
in the room can be fetched once on connect by passing
`fetch_gift_info=True` to `client.run()` / `client.start()`; the result is
cached on `client.gift_info`.

> **Streaks**: streakable gifts trigger multiple `GiftEvent`s as the viewer
> ramps up the streak, with `event.repeat_count` incrementing each time.
> The final gift in a streak carries `event.repeat_end == 1`. Use the
> `event.streaking` helper to filter intermediate events out and only act
> on the final one.

```python
@client.on(GiftEvent)
async def on_gift(event: GiftEvent):
    gift = event.gift
    if gift is None:
        return

    # Streakable gift & streak is over
    if not event.streaking and gift.type == 1:  # ``type == 1`` is streakable
        print(f"{event.user.unique_id} sent {event.repeat_count}x \"{gift.name}\"")

    # Non-streakable gift
    elif gift.type != 1:
        print(f"{event.user.unique_id} sent \"{gift.name}\"")
```

In v3 the canonical `Gift` field names are `name`, `type`, and `image`. The
v2-era prefixed names (`gift_name`, `gift_type`, `gift_image`) remain
available as read-only aliases on `ExtendedGift` for backwards compatibility.
Wrap a `Gift` in `ExtendedGift(...)` if you want the `.streakable` helper.

## Checking If A User Is Live

It is considered inefficient to use the connect method to check if a user is live. It is better to use the dedicated `await client.is_live()` method.

There is a [complete example](https://github.com/isaackogan/TikTokLive/blob/master/examples/check_live.py) of how to do this in the [examples](https://github.com/isaackogan/TikTokLive/tree/master/examples) folder.

## Frequently Asked Questions

### Is there an official TikTok LIVE API?

TikTok does not offer a public official API for reading livestream events. TikTokLive is an unofficial, open-source TikTok LIVE API client that reads the same Webcast websocket data available to any viewer of a stream.

### How do I get TikTok LIVE chat messages in Python?

Install with `pip install TikTokLive`, create a `TikTokLiveClient` with the streamer's `@unique_id`, and listen for `CommentEvent`. See the [Getting Started](#getting-started) example above; it takes about ten lines of code.

### Is the TikTok LIVE API free?

Yes. TikTokLive is free and open source under a modified AGPL license. Signing is handled by a third-party signature server ([Euler Stream](https://www.eulerstream.com/)) with free community rate limits; an API key raises those limits.

### Can I track TikTok gifts, likes, and viewer counts in real time?

Yes. `GiftEvent` (with streak handling), `LikeEvent`, and `RoomUserSeqEvent` deliver gifts, likes, and live viewer counts as they happen, alongside 50+ other event types including battles, polls, captions, and subscriptions.

### Does this work with Node.js, Java, C#, Go, or Rust?

Yes, sister libraries exist for each. See [Other Languages](#tiktok-live-api-in-other-languages-nodejs-java-c-go-rust).

## Star History

<p align="center">
    <img alt="TikTokLive GitHub star history chart: growth of the TikTok LIVE API for Python" src="https://star-history.dera.page/svg?repos=isaackogan/TikTokLive&type=Date&theme=dark" onerror="this.src='https://star-history.dera.page/svg?repos=isaackogan/TikTokLive&type=Date'" />
</p>

## License

This project is licensed under a modified AGPL license - see the [LICENSE](https://github.com/isaackogan/TikTokLive/blob/master/LICENSE) file for details.

## Contributors

* **Isaac Kogan** - *Creator, Primary Maintainer, and Reverse-Engineering* - [isaackogan](https://github.com/isaackogan)
* **Zerody** - *Creator of the NodeJS library, introduced me to scraping TikTok LIVE* - [Zerody](https://github.com/zerodytrash/)

See also the full list of secondary [contributors](https://github.com/isaackogan/TikTokLive/contributors) who have participated in
this project.
