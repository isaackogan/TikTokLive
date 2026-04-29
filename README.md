TikTokLive Python API (Unofficial)
==================
TikTokLive is an unofficial Python API wrapper for TikTok LIVE written in Python. With this library you can connect to any TikTok livestream and fetch all data available to users in a stream using just a creator's `@unique_id`.

[![Discord](https://img.shields.io/discord/977648006063091742?logo=discord&label=TikTokLive%20Discord&labelColor=%23171717&color=%231877af)](https://discord.gg/N3KSxzvDX8)
![Connections](https://tiktok.eulerstream.com/analytics/pips)
![Downloads](https://pepy.tech/badge/tiktoklive)
![Stars](https://img.shields.io/github/stars/isaackogan/TikTokLive?style=flat&color=0274b5)
![Forks](https://img.shields.io/github/forks/isaackogan/TikTokLive?style=flat&color=0274b5)
![Issues](https://img.shields.io/github/issues/isaackogan/TikTokLive)

> [!NOTE]
> This is <strong>not</strong> a production-ready API. It is a reverse engineering project. Use the [WebSocket API](https://www.eulerstream.com/websockets) for production.

<a href="https://www.eulerstream.com/websockets" target="_blank">
    <img src="https://www.eulerstream.com/api/advert?l2=WebSocket+API&r=15&b=1.5&bc=404854&o=0.95"/>
</a>

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
- `SuperFanEvent` - Triggered when a viewer becomes a super fan of the streamer
- `SuperFanJoinEvent` - Triggered when an existing super fan joins the live (distinct from `SuperFanEvent`)
- `SuperFanBoxEvent` - Triggered when a super-fan envelope (gift box) is delivered
- `WebsocketResponseEvent` - Triggered when any event is received (contains the event)
- `UnknownEvent` - An instance of `WebsocketResponseEvent` thrown whenever an event does not have an existing definition, useful for debugging

### Proto Events

These events are auto-generated from the
[TikTokLiveProto](https://pypi.org/project/TikTokLiveProto/) v2 schema. Only
events whose proto messages are present in v2 are emitted; if you don't see
one you used to rely on, it's because TikTok removed it from the schema.

If you know what an event does that's missing a description below,
[make a pull request](https://github.com/isaackogan/TikTokLive/pulls) and add it.

<ul>
<li><code>BarrageEvent</code> - A "VIP" viewer (based on gifting level) joins the chat room</li>
<li><code>CaptionEvent</code> - Auto-caption update from the host's audio</li>
<li><code>CommentEvent</code> - A viewer sent a chat comment</li>
<li><code>ControlEvent</code> - Stream action (e.g. start, end, pause, unpause)</li>
<li><code>EmoteChatEvent</code> - A custom emote was sent in chat</li>
<li><code>EnvelopeEvent</code> - A treasure chest / envelope was sent</li>
<li><code>GiftEvent</code> - A gift was sent (see <a href="#giftevent">Gift handling</a> below)</li>
<li><code>GoalUpdateEvent</code> - Subscriber/follow goal updated</li>
<li><code>HourlyRankEvent</code> - Hourly rank update</li>
<li><code>ImDeleteEvent</code> - A viewer's messages were deleted by a moderator</li>
<li><code>InRoomBannerEvent</code> - In-room banner notice</li>
<li><code>JoinEvent</code> - A viewer joined the livestream</li>
<li><code>LikeEvent</code> - The stream received likes</li>
<li><code>LinkEvent</code> - Generic link-mic event</li>
<li><code>LinkLayerEvent</code> - Link-mic layer/visibility change</li>
<li><code>LinkMicArmiesEvent</code> - A battle user received points</li>
<li><code>LinkMicBattleEvent</code> - A battle was started</li>
<li><code>LinkMicBattlePunishFinishEvent</code> - A battle's punishment phase ended</li>
<li><code>LinkMicFanTicketMethodEvent</code></li>
<li><code>LinkMicMethodEvent</code></li>
<li><code>LinkmicBattleTaskEvent</code></li>
<li><code>LiveIntroEvent</code> - Live-intro message appears</li>
<li><code>MessageDetectEvent</code></li>
<li><code>OecLiveShoppingEvent</code> - Live-shopping signal</li>
<li><code>PollEvent</code> - The creator launched / updated a poll</li>
<li><code>QuestionNewEvent</code> - Someone asked a new question via the question feature</li>
<li><code>RankTextEvent</code> - Gift count made a viewer enter the top three</li>
<li><code>RankUpdateEvent</code></li>
<li><code>RoomEvent</code> - Broadcast message to all room users (e.g. "Welcome to TikTok LIVE!")</li>
<li><code>RoomPinEvent</code> - A message was pinned</li>
<li><code>RoomUserSeqEvent</code> - Current viewer count information</li>
<li><code>SocialEvent</code> - A viewer shared or followed the host (also surfaced as <code>FollowEvent</code> / <code>ShareEvent</code> custom events)</li>
<li><code>SystemEvent</code></li>
<li><code>UnauthorizedMemberEvent</code></li>
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
    # Streakable gift & streak is over
    if event.gift.streakable and not event.streaking:
        print(f"{event.user.unique_id} sent {event.repeat_count}x \"{event.gift.gift_name}\"")

    # Non-streakable gift
    elif not event.gift.streakable:
        print(f"{event.user.unique_id} sent \"{event.gift.gift_name}\"")
```

The `event.gift` accessor returns an `ExtendedGift` (the v2 `Gift` proto with
`.streakable` added). The legacy attribute names (`gift.name`, `gift.type`,
`gift.image`) remain available as read-only aliases for backwards
compatibility with code written against earlier versions, and resolve to
the v2 fields (`gift_name`, `gift_type`, `gift_image`) underneath.

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

