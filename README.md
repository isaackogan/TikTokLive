TikTokLive
==================
A python library to connect to and read events from TikTok's LIVE service.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white&style=flat-square)](https://www.linkedin.com/in/isaac-kogan-5a45b9193/ )
[![HitCount](https://hits.dwyl.com/isaackogan/TikTokLive.svg?style=flat)](http://hits.dwyl.com/isaackogan/TikTokLive)
![Downloads](https://pepy.tech/badge/TikTokLive)
![Issues](https://img.shields.io/github/issues/isaackogan/TikTokLive)
![Forks](https://img.shields.io/github/forks/isaackogan/TikTokLive)
![Stars](https://img.shields.io/github/stars/isaackogan/TikTokLive)
[![Support Server](https://img.shields.io/discord/977648006063091742.svg?color=7289da&logo=discord&style=flat-square)](https://discord.gg/e2XwPNTBBr)

<!-- [![Downloads](https://pepy.tech/badge/tiktoklive)](https://pepy.tech/project/tiktoklive) -->

A python library to receive and decode livestream events such as comments and gifts in real-time from TikTok's LIVE service by connecting to TikTok's internal Webcast service. This library includes a wrapper that
connects to the Webcast service using only a user's `unique_id` and allows you to join your livestream as well as that of other streamers. No credentials are required to use TikTokLive.

This library was originally based off of the
[TikTok-Live-Connector](https://github.com/zerodytrash/TikTok-Live-Connector)
by [@zerodytrash](https://github.com/zerodytrash/), but has since taken on its own identity as it has added more features & changed much of its core functionality.


Join the [support discord](https://discord.gg/e2XwPNTBBr) and visit the `#support` channel for questions, contributions and ideas. Feel free to make pull requests with missing/new features, fixes, etc.

> **UPDATE:**<br>Due to a change on the part of TikTok, versions prior to **v4.3.8** are no longer functional. If you are using an unsupported version, upgrade to the latest version using the `pip install TikTokLive --upgrade` command.

## Other Languages

TikTok LIVE is availible in several alternative languages with only slight differences between the versions:

- **Node.JS:** https://github.com/zerodytrash/TikTok-Live-Connector
- **Go:** https://github.com/Davincible/gotiktoklive
- **C#/Unity:** https://github.com/frankvHoof93/TikTokLiveSharp

## Table of Contents

**Primary Information**

- [Documentation](https://isaackogan.github.io/TikTokLive/)
- [Contributors](#contributors)
- [License](#license)
- [Quickstart Examples](https://github.com/isaackogan/TikTokLive/tree/master/examples)

**Resources & Guides**

1. [David's Intro Tutorial](#tiktoklive-intro-tutorial)
2. [Getting Started](#getting-started)
3. [Params & Options](#Params-&-Options)
4. [Client Methods](#Methods)
5. [Client Attributes](#Attributes)
6. [TikTok Events](#Events)

## TikTokLive Intro Tutorial

I cannot recommend this tutorial enough for people trying to get started. It is succinct, informative and easy to understand, created by [David Teather](https://github.com/davidteather), the creator of the
Python [TikTok-Api](https://github.com/davidteather/TikTok-Api) package. Click the thumbnail to warp.

[![David's Tutorial](https://i.imgur.com/IOTkpvn.png)](https://www.youtube.com/watch?v=307ijmA3_lc)

## Getting Started

1. Install the module via pip

```
pip install TikTokLive
```

2. Create your first chat connection

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import CommentEvent, ConnectEvent

# Instantiate the client with the user's username
client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


# Define how you want to handle specific events via decorator
@client.on("connect")
async def on_connect(_: ConnectEvent):
    print("Connected to Room ID:", client.room_id)


# Notice no decorator?
async def on_comment(event: CommentEvent):
    print(f"{event.user.nickname} -> {event.comment}")


# Define handling an event via a "callback"
client.add_listener("comment", on_comment)

if __name__ == '__main__':
    # Run the client and block the main thread
    # await client.start() to run non-blocking
    client.run()
```

For more examples, [see the examples folder](https://github.com/isaackogan/TikTok-Live-Connector/tree/master/examples) provided in the tree.

## Params & Options

To create a new `TikTokLiveClient` object the following parameter is required. You can optionally add configuration options to this via kwargs.

`TikTokLiveClient(unique_id, **options)`

| Param Name | Required | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|------------|----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| unique_id  | Yes      | The unique username of the broadcaster. You can find this name in the URL.<br>Example: `https://www.tiktok.com/@isaackogz` => `isaackogz`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **options  | No       | Here you can set the following optional connection properties. If you do not specify a value, the default value will be used.<br><br>`process_initial_data` (default: `True`) <br> Define if you want to process initial data upon connecting (e.g. first 1-10 messages from BEFORE you connected).<br><br>`fetch_room_info_on_connect` (default: `True`) <br> Define if you want to fetch all room information on start. If this option is enabled, connection to offline rooms will be prevented. If enabled, the connect result contains the room info via the `room_info` attribute. You can also manually retrieve the room info (even in an unconnected state) using the `retrieve_room_info()` method.<br><br>`enable_detailed_gifts` (default: `False`) <br> Define if you want to receive extended information about gifts like gift name, cost and images which you can retrieve via the `available_gifts` attribute. When enabled, the `details` attribute in a `Gift` object will be populated.<br><br>`ws_ping_interval` (default: `10.0`) <br> The interval between keepalive pings on the websocket connection (in seconds).<br><br>`ws_timeout` (default: `10.0`)<br>How long to wait before the websocket connection is considered timed out (in seconds).<br><br>`http_timeout` (default: `10.0`) <br> How long to wait before considering an HTTP request in the http client timed out (in seconds).<br><br>`http_headers` (default: `{}`) <br> Additional HTTP client headers to include when making requests to the Webcast API AND connecting to the websocket server.<br><br>`http_params` (default: `{}`) <br>Additional HTTP client parameters to include when making requests to the Webcast API AND connecting to the websocket.<br><br>`loop` (default: `None`)<br>Optionally supply your own asyncio event loop for usage by the client. When set to None, the client pulls the current active loop or creates a new one. This option is mostly useful for people trying to nest asyncio.<br/><br/>`trust_env` (default: `False`)<br/>Whether to trust environment variables that provide proxies in httpx requests<br/><br/>`proxies` (default: `None`)<br/>Enable proxied requests by turning on forwarding for the HTTP "proxies" argument. Websocket connections will NOT be proxied<br/><br/>`lang` (default: `en-US`)<br/>Change the language. Payloads *will* be in English, but front-end content will be in the desired language!<br/><br/>`sign_api_key` (default: `None`)<br/>Parameter to increase the amount of connections allowed to be made per minute via a Sign Server API key. If you need this, contact the project maintainer. |


## Methods

A `TikTokLiveClient` object contains the following methods.

| Method Name              | Description                                                                                                                                                                       |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| run                      | Starts a connection to the live chat while blocking the main thread                                                                                                               |
| start                    | (async) Connects to the live chat without blocking the main thread                                                                                                                |
| stop                     | Turns off the connection to the live chat.                                                                                                                                        |
| retrieve_room_info       | (async) Gets the current room info from TikTok API                                                                                                                                |
| retrieve_available_gifts | (async) Retrieves a list of the available gifts for the room and adds it to the `extended_gift` attribute of the `Gift` object on the `gift` event, when enabled.                 |
| add_listener             | Adds an *asynchronous* listener function (or, you can decorate a function with `@client.on("<event>")`) and takes two parameters, an event name and the payload, an AbstractEvent ||
| download                 | Start downloading the livestream video for a given duration or until stopped via the `stop_download` method                                                                       |
| stop_download            | Stop downloading the livestream video if currently downloading, otherwise throws an error                                                                                         |

## Attributes

A `TikTokLiveClient` object contains the following attributes.

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

A `TikTokLiveClient` object has the following events. You can add events either by doing `client.add_listener("event_name", callable)` or by decorating a function with `@client.on("event_name")` that includes an event
payload parameter.

### `connect`

Triggered when the websocket connection is successfully established.

```python
@client.on("connect")
async def on_connect(event: ConnectEvent):
    print("Connected")
```

### `disconnect`

Triggered when the connection is terminated. You can call `start()`  to reconnect . Note that you should wait a little bit before attempting a reconnect to to avoid being rate-limited.

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
> **NOTE:** Users have the capability to send gifts in a streak. This increases the `event.gift.count` value until the user terminates the streak. During this time new gift events are triggered again and again with an increased `event.gift.count` value. It should be noted that after the end of the streak, another gift event is triggered, which signals the end of the streak via `event.gift.is_repeating`:`1`. This applies only to gifts with `event.gift.info.type`:`1`. This means that even if the user sends an `event.gift.info.type`:`1` gift only once, you may receive the event twice. Once with `event.gift.is_repeating`:`0` and once with `event.gift.is_repeating`:`1`. Therefore, the event should be handled as follows in one of TWO ways. These are the same, except the second is a 'higher level' implementation using TikTokLive API features:

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
    print(f"More than {event.amount} users have joined from {user.unique_id}'s share link!")
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

### `weekly_ranking`

Triggered when a weekly ranking update is sent out.

```python
@client.on("weekly_ranking")
async def on_connect(event: WeeklyRankingEvent):
    print(f"{client.unique_id} has the rank #{event.data.rank} of all streamers!")
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

This includes both events where the protobuf has NOT been decoded, as well as events where it _has_ been decoded, but no event object has been created (e.g. it's useless data).

Use this event to debug and find new events to add to TikTokLive. Mention them [here](https://github.com/isaackogan/TikTokLive/issues/104) when you do.

This event is very advanced and handles both types of cases, an API to help you decode including offering the binary as base64. 
You can plug base64 into https://protobuf-decoder.netlify.app/ to reverse-engineer the protobuf schema.

```python
@client.on("unknown")
async def on_connect(event: UnknownEvent):
    print(f"Event Type: {event.type}")
    print(f"Event Base64: {event.base64}")
```

### `error`

Triggered when there is an error in the client or error handlers.

If this handler is not present in the code, an internal default handler will log errors in the console. If a handler is added, all error handling (including logging) is up to the individual.

**Warning:** If you listen for the error event and do not log errors, you will not see when an error occurs. This expected behaviour, listening to the error event overrides & disables the built-in one.

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

See also the full list of [contributors](https://github.com/isaackogan/TikTokLive/contributors) who have participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
