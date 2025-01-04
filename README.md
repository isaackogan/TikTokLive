TikTokLive API
==================
This is an unofficial API wrapper for TikTok LIVE written in Python. With this API you can connect to any TikTok livestream and fetch all data available to users in a stream using just a creator's `@unique_id`.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white&style=flat-square)](https://www.linkedin.com/in/isaackogan/)
[![LinkedIn](https://www.eulerstream.com/api/pips/patrons?v=002)](https://www.eulerstream.com/)
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

<table>
<tr>
    <td><br/><img width="180px" style="border-radius: 10px" src="https://raw.githubusercontent.com/isaackogan/TikTokLive/master/.github/SquareLogo.png"><br/><br/></td>
    <td>
        <a href="https://www.eulerstream.com">
            <strong>Euler Stream</strong> is a paid TikTok LIVE service providing managed TikTok LIVE WebSocket connections, increased access, TikTok LIVE alerts, JWT authentication and more.
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

- `GiftEvent` - Triggered when a gift is sent to the streamer
- `GoalUpdateEvent` - Triggered when the subscriber goal is updated
- `ControlEvent` - Triggered when a stream action occurs (e.g. Livestream start, end)
- `LikeEvent` - Triggered when the stream receives a like
- `SubscribeEvent` - Triggered when someone subscribes to the TikTok creator
- `PollEvent` - Triggered when the creator launches a new poll
- `CommentEvent` - Triggered when a comment is sent in the stream
- `RoomEvent` - Messages broadcasted to all users in the room (e.g. "Welcome to TikTok LIVE!")
- `EmoteChatEvent` - Triggered when a custom emote is sent in the chat
- `EnvelopeEvent` - Triggered every time someone sends a treasure chest
- `SocialEvent` - Triggered when a user shares the stream or follows the host
- `QuestionNewEvent` - Triggered every time someone asks a new question via the question feature.
- `LiveIntroEvent` - Triggered when a live intro message appears
- `LinkMicArmiesEvent` - Triggered when a TikTok battle user receives points
- `LinkMicBattleEvent` - Triggered when a TikTok battle is started
- `JoinEvent` - Triggered when a user joins the livestream
- `LinkMicFanTicketMethodEvent`
- `LinkMicMethodEvent`
- `BarrageEvent` - Triggered when a "VIP" viewer (based on their gifting level) joins the live chat room
- `CaptionEvent`
- `ImDeleteEvent` - Triggered when a viewer's messages are deleted
- `RoomUserSeqEvent` - Current viewer count information
- `RankUpdateEvent`
- `RankTextEvent` - Triggered when gift count makes a viewer one of the top three
- `HourlyRankEvent`
- `UnauthorizedMemberEvent`
- `MessageDetectEvent`
- `OecLiveShoppingEvent`
- `RoomPinEvent` - Triggered when a message is pinned
- `SystemEvent`
- `LinkEvent`
- `LinkLayerEvent`

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

