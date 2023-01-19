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

A python library to receive and decode livestream events such as comments and gifts in real-time from TikTok's LIVE service by connecting to TikTok's internal Webcast push service. This library includes a wrapper that
connects to the Webcast service using only a user's `unique_id` and allows you to join your livestream as well as that of other streamers. No credentials are required to use TikTokLive.

This library is a Python implementation of the JavaScript
[TikTok-Live-Connector](https://github.com/zerodytrash/TikTok-Live-Connector)
by [@zerodytrash](https://github.com/zerodytrash/) meant to serve as an alternative for users who feel more comfortable working in Python or require it for their specific project parameters.

Join the [support discord](https://discord.gg/e2XwPNTBBr) and visit the `#support` channel for questions, contributions and ideas. Feel free to make pull requests with missing/new features, fixes, etc.

**NOTE:** This is **not** an official API. It's a reverse engineering and research project.

> **UPDATE:**<br>Due to a change on the part of TikTok, versions prior to **v4.3.8** are no longer functional. If you are using an unsupported version, upgrade to the latest version using the `pip install TikTokLive --upgrade` command.

## Increased Access (API Keys)

Need increased access to TikTok's servers? API keys can be acquired by contacting me on Discord.
50% of my share of the proceeds goes to https://www.thetrevorproject.org/. The other 50% of my share goes towards my caffeine addiction.

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


# Define handling an event via "callback"
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

| Param Name | Required | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
|------------|----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| unique_id  | Yes      | The unique username of the broadcaster. You can find this name in the URL.<br>Example: `https://www.tiktok.com/@isaackogz` => `isaackogz`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| debug      | No       | Whether to fire the "debug" event for receiving raw data                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **options  | No       | Here you can set the following optional connection properties. If you do not specify a value, the default value will be used.<br><br>`process_initial_data` (default: `true`) <br> Define if you want to process the initial data which includes old messages of the last seconds.<br><br>`fetch_room_info_on_connect` (default: `true`) <br> Define if you want to fetch all room information on start. If this option is enabled, the connection to offline rooms will be prevented. If enabled, the connect result contains the room info via the `room_info` attribute. You can also manually retrieve the room info (even in an unconnected state) using the `retrieve_room_info()` method.<br><br>`enable_extended_gift_info` (default: `false`) <br> Define if you want to receive extended information about gifts like gift name, cost and images which you can retrieve via the `available_gifts` attribute. <br><br>`ping_interval_ms` (default: `1000`) <br> How frequently to make requests to the webcast API when long polling.<br><br>`client_params` (default: `{}`) <br> Custom client params for Webcast API.<br><br>`headers` (default: `{}`) <br> Custom request headers passed to aiohttp.<br><br>`timeout_ms` (default: `1000`)<br>How long to wait before a request should fail<br><br>`loop` (default: `None`)<br>Optionally supply your own asyncio event loop for usage by the client. When set to None, the client pulls the current active loop or creates a new one. This option is mostly useful for people trying to nest asyncio.<br/><br/>`trust_env` (default: `false`)<br/>Whether to trust environment variables that provide proxies in httpx requests<br/><br/>`proxies` (default: `None`)<br/>Enable proxied requests by turning on forwarding for the HTTPX "proxies" argument. Websocket connections will NOT be proxied<br/><br/>`lang` (default: `en`)<br/>Change the language. Payloads *will* be in English, but front-end content will be in the desired language!<br/><br/>`websocket_enabled` (default: `True`)<br/>Whether to use websockets or rely on purely long polling. You want to use websockets.<br/><br/>`sign_api_key` (default: `None`)<br/>Parameter to increase the amount of connections allowed to be made per minute via a Sign Server API key. If you need this, contact the project maintainer. |

Example Options:

```python
from TikTokLive import TikTokLiveClient

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@oldskoldj", **(
        {

            # Custom Asyncio event loop
            "loop": None,

            # Custom Client params
            "client_params": {},

            # Custom request headers to include in HTTP Requests
            "request_headers": {},
            
            # Custom websocket headers to include when connecting to the TikTok WebSocket
            "websocket_headers": {},
            
            # Custom timeout for Webcast API requests
            "timeout_ms": 1000,

            # How frequently to make requests the webcast API when long polling
            "ping_interval_ms": 1000,

            # Whether to process initial data (cached chats, etc.)
            "process_initial_data": True,

            # Whether to get extended gift info (Image URLs, etc.)
            "enable_extended_gift_info": True,

            # Whether to trust environment variables that provide proxies to be used in http requests
            "trust_env": False,

            # A dict object for proxies requests
            "proxies": {
                "http://": "http://username:password@localhost:8030",
                "https://": "http://420.69.420:8031",
            },

            # Set the language for Webcast responses (Changes extended_gift's language)
            "lang": "en-US",

            # Connect info (viewers, stream status, etc.)
            "fetch_room_info_on_connect": True,

            # Whether to allow Websocket connections
            "websocket_enabled": False,
            
            # Parameter to increase the amount of connections made per minute via a Sign Server API key. 
            # If you need this, contact the project maintainer.
            "sign_api_key": None

        }
    )
)

if __name__ == "__main__":
    client.run()
```

## Methods

A `TikTokLiveClient` object contains the following methods.

| Method Name              | Description                                                                                                                                                                                    |
|--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| run                      | Starts a connection to the live chat while blocking the main thread (sync)                                                                                                                     |
| start                    | Connects to the live chat without blocking the main thread (async)                                                                                                                             |
| stop                     | Turns off the connection to the live chat.                                                                                                                                                     |
| retrieve_room_info       | Gets the current room info from TikTok API                                                                                                                                                     |
| retrieve_available_gifts | Retrieves a list of the available gifts for the room and adds it to the `extended_gift` attribute of the `Gift` object on the `gift` event, when enabled.                                      |
| add_listener             | Adds an *asynchronous* listener function (or, you can decorate a function with `@client.on()`) and takes two parameters, an event name and the payload, an AbstractEvent                       ||
| download                 | Start downloading the livestream video for a given duration or until stopped via the `stop_download` method                                                                                    |
| stop_download            | Stop downloading the livestream video if currently downloading, otherwise throws an error                                                                                                      |
| send_message             | Send a message to the chat. This is only partially implemented. See the [examples/message.py](https://github.com/isaackogan/TikTokLive/tree/master/examples/message.py) example for more info. |

## Attributes

| Attribute Name  | Description                                                                                                                          |
|-----------------|--------------------------------------------------------------------------------------------------------------------------------------|
| viewer_count    | The number of people currently watching the livestream broadcast                                                                     |
| room_id         | The ID of the livestream room the client is currently connected to                                                                   |
| room_info       | Information about the given livestream room                                                                                          |
| unique_id       | The TikTok username of the person whose livestream the client is currently connected to                                              |
| connected       | Whether the client is currently connected to a livestream                                                                            |
| available_gifts | A dictionary containing K:V pairs of `Dict[int, ExtendedGift]`                                                                       |                              |
| proxies         | Get the current proxies being used for HTTP requests.<br/><br/>**Note:** To set the active proxies, set the value of this attribute. |

## Events

A `TikTokLiveClient` object has the following events. You can add events either by doing `client.add_listener("event_name", callable)` or by decorating a function with `@client.on("event_name")` that includes an event
payload parameter.

### `connect`

Triggered when the connection gets successfully established.

```python
@client.on("connect")
async def on_connect(event: ConnectEvent):
    print("Connected")
```

### `disconnect`

Triggered when the connection gets disconnected. You can call `start()`  to have reconnect . Note that you should wait a little bit before attempting a reconnect to to avoid being rate-limited.

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
    print("Someone liked the stream!")
```

### `join`

Triggered every time a new person joins the stream.

```python
@client.on("join")
async def on_join(event: JoinEvent):
    print("Someone joined the stream!")
```

### `gift`

Triggered every time a gift arrives. Extra information can be gleamed off the `available_gifts` client attribute.
> **NOTE:** Users have the capability to send gifts in a streak. This increases the `data.gift.repeat_count` value until the user terminates the streak. During this time new gift events are triggered again and again with an increased `data.gift.repeat_count` value. It should be noted that after the end of the streak, another gift event is triggered, which signals the end of the streak via `data.gift.repeat_end`:`1`. This applies only to gifts with `data.gift.gift_type`:`1`. This means that even if the user sends a `gift_type`:`1` gift only once, you will receive the event twice. Once with `repeat_end`:`0` and once with `repeat_end`:`1`. Therefore, the event should be handled as follows in one of TWO ways:

```python
@client.on("gift")
async def on_gift(event: GiftEvent):
    # If it's type 1 and the streak is over
    if event.gift.gift_type == 1:
        if event.gift.repeat_end == 1:
            print(f"{event.user.uniqueId} sent {event.gift.repeat_count}x \"{event.gift.extended_gift.name}\"")

    # It's not type 1, which means it can't have a streak & is automatically over
    elif event.gift.gift_type != 1:
        print(f"{event.user.uniqueId} sent \"{event.gift.extended_gift.name}\"")
```

```python
@client.on("gift")
async def on_gift(event: GiftEvent):
    # If it's type 1 and the streak is over
    if event.gift.streakable:
        if not event.gift.streaking:
            print(f"{event.user.uniqueId} sent {event.gift.repeat_count}x \"{event.gift.extended_gift.name}\"")

    # It's not type 1, which means it can't have a streak & is automatically over
    else:
        print(f"{event.user.uniqueId} sent \"{event.gift.extended_gift.name}\"")
```

### `follow`

Triggered every time someone follows the streamer.

```python
@client.on("follow")
async def on_follow(event: FollowEvent):
    print("Someone followed the streamer!")
```

### `share`

Triggered every time someone shares the stream.

```python
@client.on("share")
async def on_share(event: ShareEvent):
    print("Someone shared the streamer!")
```

### `viewer_count_update`

Triggered every time the viewer count is updated. This event also updates the cached viewer count by default.

```python
@client.on("viewer_count_update")
async def on_connect(event: ViewerCountUpdateEvent):
    print("Received a new viewer count:", event.viewCount)
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
    print(f"{event.user.nickname} -> {event.emote.image.imageUrl}")
```

### `envelope`

Triggered when someone sends an envelope (treasure box) to the TikTok streamer.

```python
@client.on("envelope")
async def on_connect(event: EnvelopeEvent):
    print(f"{event.treasureBoxUser.uniqueId} -> {event.treasureBoxData}")
```

### `subscribe`

Triggered when someone subscribes to the TikTok streamer.

```python
@client.on("subscribe")
async def on_connect(event: SubscribeEvent):
    print(f"{event.user.uniqueId} just subscribed to {client.unique_id}!")
```

### `weekly_ranking`

Triggered when a weekly ranking update is sent out.

```python
@client.on("weekly_ranking")
async def on_connect(event: WeeklyRankingEvent):
    print(f"{client.unique_id} is in the top {event.data.rankings.rank.id} streamers!")
```

### `mic_battle`

Triggered when a Mic Battle starts!

```python
@client.on("mic_battle")
async def on_connect(event: MicBattleEvent):
    print(f"A Mic battle has started between {', '.join([user.battleGroup.user.uniqueId for user in event.battleUsers])}")
```

### `mic_armies`

Triggered when information is received about a mic battle's progress.

```python
@client.on("mic_armies")
async def on_connect(event: MicArmiesEvent):
    print(f"Mic battle data: {event.battleUsers}")
```

### `more_share`

Triggered when more than 5 or 10 users join from a viewer's share link.

```python
@client.on("more_share")
async def on_connect(event: MoreShareEvent):
    print(f"More than {event.amount} users have joined from {user.uniqueId}'s share link!")
```

### `live_end`

Triggered when the live stream gets terminated by the host.

```python
@client.on("live_end")
async def on_connect(event: LiveEndEvent):
    print(f"Livestream ended :(")
```

### `unknown`

Triggered when an unknown event is received that is not yet handled by this client.

```python
@client.on("unknown")
async def on_connect(event: UnknownEvent):
    print(event.as_dict, "<- This is my data as a dict!")
```

### `error`

Triggered when there is an error in the client or error handlers.

If this handler is not present in the code, an internal default handler will log errors in the console. If a handler is added, all error handling (including logging) is up to the individual.

**Warning:** If you listen for the error event and do not log errors, you will not see when an error occurs. This is because listening to the error event causes the default one to be overriden/turned off.

```python

@client.on("error")
async def on_connect(error: Exception):
    # Handle the error
    if isinstance(error, SomeRandomError):
        print("Handle Some Error")
        return

    # Otherwise, log the error
    client._log_error(error)

```

## Contributors

* **Isaac Kogan** - *Initial work & primary maintainer* - [isaackogan](https://github.com/isaackogan)
* **Zerody** - *Reverse-Engineering & Support* - [Zerody](https://github.com/zerodytrash/)
* **Davincible** - *Reverse-Engineering Stream Downloads*  - [davincible](https://github.com/davincible)
* **David Teather** - *TikTokLive Introduction Tutorial* - [davidteather](https://github.com/davidteather)

See also the full list of [contributors](https://github.com/isaackogan/TikTokLive/contributors) who have participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
