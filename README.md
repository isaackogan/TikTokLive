TikTokLive
==================
A python library to connect to and read events from TikTok's LIVE service

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white&style=flat-square)](https://www.linkedin.com/in/isaac-kogan-5a45b9193/ )
[![HitCount](https://hits.dwyl.com/isaackogan/TikTokLive.svg?style=flat)](http://hits.dwyl.com/isaackogan/TikTokLive)
![Issues](https://img.shields.io/github/issues/isaackogan/TikTok-Live-Connector)
![Forks](https://img.shields.io/github/forks/isaackogan/TikTok-Live-Connector)
![Stars](https://img.shields.io/github/stars/isaackogan/TikTok-Live-Connector)
[![Support Server](https://img.shields.io/discord/831349828578574346.svg?color=7289da&logo=discord&style=flat-square)](https://discord.gg/JwW8UwfUmC)

<!-- [![Downloads](https://pepy.tech/badge/tiktoklive)](https://pepy.tech/project/tiktoklive) -->

A python library to receive and decode livestream events such as comments and gifts in real-time from TikTok's LIVE service by connecting to TikTok's internal WebCast push service. This library includes a wrapper that
connects to the WebCast service using only a user's `unique_id` and allows you to join your livestream as well as that of other streamers. No credentials are required to use TikTok-Live-Connector.

This library is a nearly 1:1 python implementation of the Javascript
[TikTok-Live-Connector](https://github.com/zerodytrash/TikTok-Livestream-Chat-Connector)
by [@zerodytrash](https://github.com/zerodytrash/) meant to serve as an alternative for users who feel more comfortable working in Python.

This is **not** an official API. It's a reverse engineering and research project.

Join the support discord and DM ``fallen#9745`` for inquiries, help and suggestions. Feel free to make pull requests with missing/new features, fixes, etc.

## Video Tutorial

The following is a video tutorial produced by [@Vyler](https://www.youtube.com/channel/UCh8JuEPtb0oBeVv2nt6Y96A) on YouTube that makes use of this library. Thank him for his hard work! Note this was not produced
by [@isaackogan](https://github.com/isaackogan). All video-related questions should be directed to Vyler!

[![YouTube Tutorial](https://img.youtube.com/vi/gubvklbZFTU/0.jpg)](https://www.youtube.com/watch?v=gubvklbZFTU)

## ![!Ukraine](https://raw.githubusercontent.com/yammadev/flag-icons/master/png/UA%402x.png) 💲💲 Buy Library Addons - Thermal Printer & More! 💲💲 ![!Ukraine](https://raw.githubusercontent.com/yammadev/flag-icons/master/png/UA%402x.png)

Custom addons for this library are for sale for charity. **100 percent** of proceeds go to [UNICEF's Ukraine Humanitarian Crisis](https://secure.unicef.ca/page/98630/donate/1) fund.

To purchase an addon, contact info@isaackogan.com with the item name. Setup troubleshooting will be provided, however hosting and setup of the applications is up to you and specific to your infrastructure.

Payments via [GoFundMe page](https://www.isaackogan.com/uadonate) OR PayPal/BTC/ETH (will be sent to GoFundMe through me). Delivery time varies. Items that have not purchased before yet have to be made for the first time
and will take time to produce. You will be updated through e-mail about their progress as it is being made. Items that have been produced will be delivered within 12h of your payment being acknowledged.

### VERY IMPORTANT: CAD Currency Notice

GoFundMe donations are in **CAD** (Canadian Dollars), because I am a Canadian. The number you type into GoFundMe **MUST** be the value listed in CAD. If the item costs $5 USD, you must put $7 into the GoFundMe, as that
is the Canadian conversion. If you under-pay, you **will be** asked to transfer the difference via PayPal.

### Thermal Printing

| Item       | Price (USD) | Price (CAD) | Description                                                                                                                                                                                                                                                                   |
|------------|-------------|-------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Standard   | ~ $30       | CA$ 40      | Print events to a Thermal Printer. For example, printing a comment with the user's name, message, and profile picture. This is a HIGHLY advanced wrapper allowing you to print to a USB printer (must have ESCPOS) like it's nothing.                                         |
| Setup Help | ~ $10       | CA$ 15      | Up to 45 minutes of 1-on-1 setup time. I will conference with you in a voice call on Discord and remotely control your PC via AnyDesk. I will install the software on the spot, with you. Must have a working phone with Discord, so I can see the printer in case I need to. |_

### Regular Items

| Item                                      | Price (USD)              | Price (CAD)              | Description                                                                                                                                                                                                                                                      |
|-------------------------------------------|--------------------------|--------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Donation Sounds                           | ~ $5                     | CA$ 7                    | Play custom sound files (mp3/wav/etc.) when a user donates to your stream with specific gifts (Rose, Sunglasses, etc.)                                                                                                                                           |
| Text Command System                       | ~ $5                     | CA$ 7                    | Using the same style handling as this library, parse text messages into Amazon Echo styled commands you can handle with an assortment of response options including playing a wav or text-to-speech, or custom response.                                         |
| Combined Text & Donation Sounds           | ~ $8                     | CA$ 10                   | Everything that "Donation Sounds" and "Text Command System" does, but combined into one singular program.                                                                                                                                                        |
| TikTok Chat to Twitch Chat Conversion Bot | ~ $8                     | CA$ 10                   | Send all TikTok chats to a Twitch channel's chat using a stream moderator/operator account on Twitch.                                                                                                                                                            |
| Custom Option                             | Contact for a quote      | Contact for a quote      | See something not on here? Contact for a custom quote. Please not that we reserve the right to add your commission to this shop for others to purchase after it is done. The goal of this shop is to support charity, so the more purchasable items, the better. |
| Donation                                  | Choose your contribution | Choose your contribution | Donate to the fund for the sake of it. Every dollar makes a difference.                                                                                                                                                                                          |

## Getting started

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

| Param Name | Required | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
|------------|----------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| unique_id  | Yes      | The unique username of the broadcaster. You can find this name in the URL.<br>Example: `https://www.tiktok.com/@officialgeilegisela/live` => `officialgeilegisela`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| debug      | No       | Whether to fire the "debug" event for receiving raw data                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| options    | No       | Here you can set the following optional connection properties. If you do not specify a value, the default value will be used.<br><br>`process_initial_data` (default: `true`) <br> Define if you want to process the initial data which includes old messages of the last seconds.<br><br>`fetch_room_info_on_connect` (default: `true`) <br> Define if you want to fetch all room information on start. If this option is enabled, the connection to offline rooms will be prevented. If enabled, the connect result contains the room info via the `room_info` attribute. You can also manually retrieve the room info (even in an unconnected state) using the `retrieve_room_info()` method.<br><br>`enable_extended_gift_info` (default: `false`) <br> Define if you want to receive extended information about gifts like gift name, cost and images which you can retrieve via the `available_gifts` attribute. <br><br>`polling_interval_ms` (default: `1000`) <br> Request polling interval.<br><br>`client_params` (default: `{}`) <br> Custom client params for Webcast API.<br><br>`headers` (default: `{}`) <br> Custom request headers passed to aiohttp.<br><br>`timeout_ms` (default: `1000`)<br>How long to wait before a request should fail<br><br>`loop` (default: `None`)<br>Optionally supply your own asyncio event loop for usage by the client. When set to None, the client pulls the current active loop or creates a new one. This option is mostly useful for people trying to nest asyncio. |

Example Options:

```python
from TikTokLive import TikTokLiveClient

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@oldskoldj", **(
        {
            # Whether to process initial data (cached chats, etc.)
            "process_initial_data": True,

            # Connect info (viewers, stream status, etc.)
            "fetch_room_info_on_connect": True,

            # Whether to get extended gift info (Image URLs, etc.)
            "enable_extended_gift_info": True,

            # How frequently to poll Webcast API
            "polling_interval_ms": 1000,

            # Custom Client params
            "client_params": {},

            # Custom request headers
            "headers": {},

            # Custom timeout for Webcast API requests
            "timeout_ms": 1000,

            # Custom Asyncio event loop
            "loop": None,

            # Whether to trust environment variables that provide proxies to be used in aiohttp requests
            "trust_env": False,

            # A ProxyContainer object for proxied requests
            "proxy_container": None

        }
    )
)

client.run()
```

## Methods

A `TikTokLiveClient` object contains the following methods.

| Method Name              | Description                                                                                                                                                              |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| run                      | Starts a connection to the live chat while blocking the main thread (sync)                                                                                               |
| start                    | Connects to the live chat without blocking the main thread (async)                                                                                                       |
| stop                     | Turns off the connection to the live chat.                                                                                                                               |
| retrieve_room_info       | Gets the current room info from TikTok API                                                                                                                               |
| retrieve_available_gifts | Retrieves a list of the available gifts for the room and adds it to the `extended_gift` attribute of the `Gift` object on the `gift` event, when enabled.                |
| add_listener             | Adds an *asynchronous* listener function (or, you can decorate a function with `@client.on()`) and takes two parameters, an event name and the payload, an AbstractEvent ||
| add_proxies              | Add proxies to the current list of proxies with a valid aiohttp proxy-url                                                                                                |
| get_proxies              | Get the current list of proxies by proxy-url                                                                                                                             |
| remove_proxies           | Remove proxies from the current list of proxies by proxy-url                                                                                                             |
| set_proxies_enabled      | Set whether or not proxies are enabled (disabled by default)                                                                                                             |

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

Triggered every time someone comments on the live

```python
@client.on("comment")
async def on_connect(event: CommentEvent):
    print(f"{event.user.nickname} -> {event.comment}")
```

### `live_end`

Triggered when the live stream gets terminated by the host.

```python
@client.on("live_end")
async def on_connect(event: LiveEndEvent):
    print(f"Livestream ended :(")
```

### `unknown`

Triggered when an unknown event is received that is not yet handled by this client

```python
@client.on("live_end")
async def on_connect(event: UnknownEvent):
    print(event.as_dict, "<- This is my data as a dict!")
```

## Contributors

* **Isaac Kogan** - *Initial work* - [isaackogan](https://github.com/isaackogan)
* **Zerody** - *Reverse-Engineering & README.md file* - [Zerody](https://github.com/zerodytrash/)

See the full list of [contributors](https://github.com/ChromegleApp/Chromegle/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
