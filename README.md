TikTokLive
==================
The definitive Python library to connect to TikTok LIVE.

![Connections](https://tiktok.eulerstream.com/analytics/pips/1)
![Downloads](https://pepy.tech/badge/tiktoklive)
![Stars](https://img.shields.io/github/stars/isaackogan/TikTokLive?style=flat&color=0274b5)
![Forks](https://img.shields.io/github/forks/isaackogan/TikTokLive?style=flat&color=0274b5)
![Issues](https://img.shields.io/github/issues/isaackogan/TikTokLive)
[![Support Server](https://img.shields.io/discord/977648006063091742.svg?color=7289da&logo=discord&style=flat)](https://discord.gg/e2XwPNTBBr)

<!-- [![HitCount](https://hits.dwyl.com/isaackogan/TikTokLive.svg?style=flat)](http://hits.dwyl.com/isaackogan/TikTokLive) -->

TikTokLive is a Python library designed to connect to [TikTok LIVE](https://tiktok.com/live) and receive realtime events
such as comments, gifts, and likes through a websocket connection to TikTok's internal Webcast service. This library
allows you to
connect directly to TikTok with just a username (`@unique_id`). No credentials are required to use TikTokLive.

### Sponsors

I'm a 2nd-year Biology student in university who likes to program for fun. Please consider supporting development
through a small donation at [https://www.buymeacoffee.com/isaackogan](https://www.buymeacoffee.com/isaackogan). Anything
you can offer will go towards school & development costs for TikTokLive.

### Support

Join the [TikTokLive discord](https://discord.gg/e2XwPNTBBr) and visit
the [`#py-support`](https://discord.gg/uja6SajDxd)
channel for questions, contributions and ideas.

### Languages

TikTok LIVE is available in several alternate programming languages:

- **Node.JS:** https://github.com/zerodytrash/TikTok-Live-Connector
- **Java:** https://github.com/jwdeveloper/TikTok-Live-Java
- **C#/Unity:** https://github.com/frankvHoof93/TikTokLiveSharp
- **Go:** https://github.com/Davincible/gotiktoklive

## Table of Contents

- [Documentation](https://isaackogan.github.io/TikTokLive/)
- [Licensing](#license)
- [Examples](https://github.com/isaackogan/TikTokLive/tree/master/examples)
- [Contributors](#contributors)

## Getting Started

1. Install the module via pip from the [PyPi](https://pypi.org/project/TikTokLive/) repository

```shell script
$ pip install TikTokLive
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

## Parameters

| Param Name   | Required | Default | Description                                                                                                                                                                                                                                                                              |
|--------------|----------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| unique_id    | Yes      | `N/A`   | The unique username of the broadcaster. You can find this name in the URL of the user. For example, the `unique_id` for `https://www.tiktok.com/@isaackogz/live` would be `isaackogz`                                                                                                    |
| web_proxy    | No       | `None`  | TikTokLive supports proxying HTTP requests. This parameter accepts an `httpx.Proxy`. Note that if you do use a proxy you may be subject to reduced connection limits at times of high load.                                                                                              |
| ws_proxy     | No       | `None`  | TikTokLive supports proxying the websocket connection. This parameter accepts an `httpx.Proxy`. Using this proxy will never be subject to reduced connection limits.                                                                                                                     |
| sign_api_key | No       | `None`  | API keys to the [signature service](https://github.com/isaackogan/TikTokLive/wiki/All-About-Signatures) are not publicly available. They are offered to <u>companies</u> that require increased access to the sign server. Please do not reach out for one if you are not an enterprise. |
| web_kwargs   | No       | `{}`    | Under the scenes, the TikTokLive HTTP client uses the [`httpx`](https://github.com/encode/httpx) library. Arguments passed to `web_kwargs` will be forward the the underlying HTTP client.                                                                                               |
| ws_kwargs    | No        | `{}`     | Under the scenes, TikTokLive uses the [`websockets`](https://github.com/python-websockets/websockets) library to connect to TikTok. Arguments passed to `ws_kwargs` will be forwarded to the underlying WebSocket client.                                                                |

## WebDefaults

TikTokLive has a series of global defaults used to create the HTTP client. These values can be customized in the following way:

```python


```


## Methods

A `TikTokLiveClient` object contains the following methods:

| Method Name              | Description                                                                                                                                                                                                                   |
|--------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| run                      | Starts a connection to the live chat while blocking the main thread                                                                                                                                                           |
| start                    | (async) Connects to the live chat without blocking the main thread                                                                                                                                                            |
| stop                     | Turns off the connection to the live chat.                                                                                                                                                                                    |
| retrieve_room_info       | (async) Gets the current room info from TikTok API                                                                                                                                                                            |
| retrieve_available_gifts | (async) Retrieves a list of the available gifts for the room and adds it to the `extended_gift` attribute of the `Gift` object on the `gift` event, when enabled.                                                             |
| add_listener             | Adds an *asynchronous* listener function (or, you can decorate a function with `@client.on("<event>")`) and takes two parameters, an event name and the payload, an AbstractEvent                                             ||
| download                 | Start downloading the livestream video for a given duration or until stopped via the `stop_download` method. Supports the ability to add different flags, like `-c copy` which may reduce CPU usage by disabling transcoding. |
| stop_download            | Stop downloading the livestream video if currently downloading, otherwise throws an error                                                                                                                                     |

## Attributes

A `TikTokLiveClient` object contains the following attributes:

| Attribute Name  | Description                                                                                                                                  |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| room_id         | The Room ID of the livestream room the client is currently connected to                                                                      |
| room_info       | Information about the given livestream room                                                                                                  |
| unique_id       | The TikTok username of the person whose livestream the client is currently connected to (e.g. @charlidamelio)                                |
| connected       | Whether the client is currently connected to a livestream                                                                                    |
| connecting      | Whether the client is currently connecting to a livestream                                                                                   |
| available_gifts | A dictionary containing K:V pairs of `Dict[int, GiftDetailed]`, where the int is the internal TikTok gift id                                 |                              |
| proxies         | Get the current proxies being used for HTTP requests.<br/><br/>**Note:** To set the active proxies, set the value of this attribute          |
| loop            | The asyncio event loop the client is running off of                                                                                          |
| http            | The HTTP client TikTokLive uses to make all HTTP-based requests                                                                              |
| websocket       | The `WebcastWebsocketConnection` websocket client TikTokLive uses to manage its websocket connection                                         |
| ffmpeg          | The ffmpeg wrapper TikTokLive uses to manage ffmpeg-based stream downloads                                                                   |
| viewer_count    | The number of people currently watching the livestream broadcast. Updated automatically on a `viewer_update` event                           |
| top_viewers     | The top N (usually ~1-20) users, ranked by coins gifted to the streamer, for the broadcast. Updated automatically on a `viewer_update` event |

## Events

A `TikTokLiveClient` object has the following events. You can add events either by
doing `client.add_listener("event_name", callable)` or by decorating a function with `@client.on("event_name")` that
includes an event
payload parameter.

### `connect`

Triggered when the websocket connection is successfully established.

```python
@client.on("connect")
async def on_connect(event: ConnectEvent):
    print("Connected")
```

### `disconnect`

Triggered when the connection is terminated. You can call `start()`  to reconnect . Note that you should wait a little
bit before attempting a reconnect to to avoid being rate-limited.

```python
@client.on("disconnect")
async def on_disconnect(event: DisconnectEvent):
    print("Disconnected")
```

### `like`

Triggered every time someone likes the stream.

```python
@client.on("like")
async def on_like(event: LikeEvent):
    print(f"@{event.user.unique_id} liked the stream!")
```

### `join`

Triggered every time a new person joins the stream.

```python
@client.on("join")
async def on_join(event: JoinEvent):
    print(f"@{event.user.unique_id} joined the stream!")
```

### `gift`

Triggered every time a gift arrives. Extra information can be gleamed off the `available_gifts` client attribute.
> **NOTE:** Users have the capability to send gifts in a streak. This increases the `event.gift.count` value until the
> user terminates the streak. During this time new gift events are triggered again and again with an
> increased `event.gift.count` value. It should be noted that after the end of the streak, another gift event is
> triggered, which signals the end of the streak via `event.gift.is_repeating`:`1`. This applies only to gifts
> with `event.gift.info.type`:`1`. This means that even if the user sends an `event.gift.info.type`:`1` gift only once,
> you may receive the event twice. Once with `event.gift.is_repeating`:`0` and once with `event.gift.is_repeating`:`1`.
> Therefore, the event should be handled as follows in one of TWO ways. These are the same, except the second is a '
> higher
> level' implementation using TikTokLive API features:

```python
@client.on("gift")
async def on_gift(event: GiftEvent):
    # If it's type 1 and the streak is over
    if event.gift.info.type == 1:
        if event.gift.is_repeating == 1:
            print(f"{event.user.unique_id} sent {event.gift.count}x \"{event.gift.info.name}\"")

    # It's not type 1, which means it can't have a streak & is automatically over
    elif event.gift.info.type != 1:
        print(f"{event.user.unique_id} sent \"{event.gift.info.name}\"")
```

```python
@client.on("gift")
async def on_gift(event: GiftEvent):
    # Streakable gift & streak is over
    if event.gift.streakable and not event.gift.streaking:
        print(f"{event.user.unique_id} sent {event.gift.count}x \"{event.gift.info.name}\"")

    # Non-streakable gift
    elif not event.gift.streakable:
        print(f"{event.user.unique_id} sent \"{event.gift.info.name}\"")

```

### `follow`

Triggered every time someone follows the streamer.

```python
@client.on("follow")
async def on_follow(event: FollowEvent):
    print(f"@{event.user.unique_id} followed the streamer!")
```

### `share`

Triggered every time someone shares the stream.

```python
@client.on("share")
async def on_share(event: ShareEvent):
    print(f"@{event.user.unique_id} shared the stream!")

```

### `more_share`

Triggered when 5 or 10 users join from a viewer's share link.

```python
@client.on("more_share")
async def on_connect(event: MoreShareEvent):
    print(f"More than {event.amount} users have joined from {event.user.unique_id}'s share link!")
```

### `viewer_update`

Triggered every time the viewer count is updated. This event also updates the cached viewer count by default.

```python
@client.on("viewer_update")
async def on_connect(event: ViewerUpdateEvent):
    # Viewer Count
    print("Received a new viewer count:", event.viewer_count)
    print("The client automatically sets the count as an attribute too:", client.viewer_count)

    # Top VIewers
    print("You can even get the top viewers (by coins gifted)!:", event.top_viewers)
    print("The client automatically sets the top viewers as an attribute too:", client.top_viewers)

```

### `comment`

Triggered every time someone comments on the live.

**NOTE:** Some comments will be missing. Certain "low quality" comments will ONLY show up when a `session_id` is passed
to the client.

```python
@client.on("comment")
async def on_connect(event: CommentEvent):
    print(f"{event.user.nickname} -> {event.comment}")
```

### `emote`

Triggered when someone sends a subscription emote comment to the live chat.

```python
@client.on("emote")
async def on_connect(event: EmoteEvent):
    print(f"{event.user.nickname} -> {event.emote.image.url}")
```

### `envelope`

Triggered when someone sends an envelope (treasure box) to the TikTok streamer.

```python
@client.on("envelope")
async def on_connect(event: EnvelopeEvent):
    print(f"{event.treasure_box_user.unique_id} -> {event.treasure_box_data}")
```

### `ranking_update`

Triggered when a **stream** rank update is sent out. Can be `Weekly Ranking` or `Rising Star`!

```python
@client.on("ranking_update")
async def on_connect(event: RankingUpdateEvent):
    print(f"{event.user.unique_id} has the rank #{event.rank} for the {event.type} leaderboard.")
```

### `user_ranking_update`

Triggered when a **user** rank update is sent out. Can be `Top Viewer`
status.

```python
@client.on("user_ranking_update")
async def on_connect(event: UserRankingUpdateEvent):
    print(f"{event.user.unique_id} just became a #{event.rank} top viewer!")
```

### `mic_battle_start`

Triggered when a Mic Battle starts!

```python
@client.on("mic_battle_start")
async def on_connect(event: MicBattleStartEvent):
    print(f"A Mic battle has started!")
```

### `mic_battle_update`

Triggered when information is received about a mic battle's progress.

```python
@client.on("mic_battle_update")
async def on_connect(event: MicBattleUpdateEvent):
    print(f"An army in the mic battle has received points, or the status of the battle has changed!")
```

### `live_end`

Triggered when the live stream gets terminated by the host.

```python
@client.on("live_end")
async def on_connect(event: LiveEndEvent):
    print(f"Livestream ended :(")
```

### `intro_message`

Triggered when an intro message is sent to the live room.
An intro message is basically a pinned message at the top of chat when you join a room.

This event only fires if "process_initial_data" is enabled and the streamer has an intro message configured.

```python
@client.on("intro_message")
async def on_connect(event: IntroMessageEvent):
    print(f"Message: {event.message}")
```

### `unknown`

Triggered when ANY unknown event is received that is not yet handled by this client.

This includes both events where the protobuf has NOT been decoded, as well as events where it _has_ been decoded, but no
event object has been created (e.g. it's useless data).

Use this event to debug and find new events to add to TikTokLive. Mention
them [here](https://github.com/isaackogan/TikTokLive/issues/104) when you do.

This event is very advanced and handles both types of cases, an API to help you decode including offering the binary as
base64.
You can plug base64 into https://protobuf-decoder.netlify.app/ to reverse-engineer the protobuf schema.

```python
@client.on("unknown")
async def on_connect(event: UnknownEvent):
    print(f"Event Type: {event.type}")
    print(f"Event Base64: {event.base64}")
```

### `error`

Triggered when there is an error in the client or error handlers.

If this handler is not present in the code, an internal default handler will log errors in the console. If a handler is
added, all error handling (including logging) is up to the individual.

**Warning:** If you listen for the error event and do not log errors, you will not see when an error occurs. This
expected behaviour, listening to the error event overrides & disables the built-in one.

```python

@client.on("error")
async def on_connect(error: Exception):
    # Handle the error
    if isinstance(error, SomeRandomError):
        print("Handle some error!")
        return

    # Otherwise, log the error
    # You can use the internal method, but ideally your own
    client._log_error(error)

```

## Contributors

* **Isaac Kogan** - *Creator, Primary Maintainer, and Reverse-Engineering* - [isaackogan](https://github.com/isaackogan)
* **Zerody** - *Initial Reverse-Engineering Protobuf & Support* - [Zerody](https://github.com/zerodytrash/)
* **Davincible** - *Reverse-Engineering Stream Downloads*  - [davincible](https://github.com/davincible)
* **David Teather** - *TikTokLive Introduction Tutorial* - [davidteather](https://github.com/davidteather)

See also the full list of [contributors](https://github.com/isaackogan/TikTokLive/contributors) who have participated in
this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
