---
title: Getting Started
description: Install TikTokLive and receive comments, gifts, and other events from a TikTok livestream with Python.
head:
  - tag: title
    content: "TikTok LIVE API for Python: TikTokLive Documentation"
---

TikTokLive receives comments, gifts, likes, follows, shares, viewer counts, battles, and other events from a TikTok livestream. Connect with a creator's `@unique_id` using `TikTokLiveClient`.

## Prerequisites

- Python 3.10 or newer. The client is built on `asyncio`: `client.run()` starts an event loop and blocks, which suits small scripts, and `await client.start()` joins an event loop you already run.
- No TikTok login for public livestreams. Signing uses a third-party provider, [Euler Stream](https://www.eulerstream.com/) by default. Age-restricted rooms and connections made with a TikTok session have additional requirements; see [authentication](/configuration/authentication/).

This is an unofficial reverse-engineering project, not a supported vendor API. TikTok can change the Webcast protocol without notice, and a defined event may not be sent in every room or region. See [protocol types](/advanced/protocol/) for how to distinguish schema definitions from verified event behavior.

## Install

```sh
pip install TikTokLive
```

## Listen to a livestream

Save this as `chat.py`, replace `@isaackogz` with a creator who is live, and run `python chat.py`.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent, CommentEvent

# Create the client
client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


# Listen to an event with a decorator
@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent) -> None:
    print(f"Connected to @{event.unique_id} (Room ID: {client.room_id})")


# Or add a listener with client.add_listener()
async def on_comment(event: CommentEvent) -> None:
    if event.user is None:
        return
    print(f"{event.user.nickname} -> {event.comment}")


client.add_listener(CommentEvent, on_comment)

if __name__ == "__main__":
    # Run the client and block the main thread.
    # Use await client.start() to run non-blocking.
    client.run()
```

Register listeners before calling `run()`: the first signed response can carry messages, and they are emitted right after `ConnectEvent`. `run()` returns when the connection ends, and `Ctrl+C` disconnects cleanly.

`unique_id` accepts `isaackogz`, `@isaackogz`, or `https://www.tiktok.com/@isaackogz/live`. Pass a numeric user ID with `is_user_id=True` to resolve it to a username first. The other constructor parameters are listed in [options](/configuration/options/).

## Read event payloads

Every proto event subclasses its TikTokLiveProto v3 message, so its fields are the schema's fields. For a comment, the text is `event.content` (`event.comment` is an alias), the username is `event.user.unique_id`, and the display name is `event.user.nickname`. Nested messages such as `event.user` and `event.gift` are `Optional` and can be absent; check for `None` before reading them, as the example above does. The [event catalog](/events/) lists each event with its message, and the [schema reference](/schema/) describes every field.

`event.get_type()` returns the event class name, which is the key `client.on()` subscribes to.

## Signing

The default signing provider is Euler Stream, a hosted [TikTok LIVE signing API](https://www.eulerstream.com/). A TikTok login is unnecessary for public rooms; provider rate limits still apply, and an API key raises them. Set the key in the `SIGN_API_KEY` environment variable or on `WebDefaults.tiktok_sign_api_key` before creating the client; the environment variable takes precedence. For production workloads that need an uptime guarantee, the managed [TikTok LIVE WebSocket API](https://www.eulerstream.com/websockets) handles signing, scaling, and protocol changes for you. See [signing](/configuration/signing/) and [troubleshooting](/troubleshooting/).

## Next steps

- [Connection lifecycle](/getting-started/connection/): `run`, `start`, and `connect`, room and gift information, disconnects, and reconnecting.
- [Event catalog](/events/): find an event by its name or what it does.
- [Gift streaks](/guides/gifts/): count a streaked gift once, when the streak ends.
- [Configuration](/configuration/options/): client parameters, `WebDefaults`, and environment variables.
- [API reference](/api/): generated from the Python source in this checkout.

These docs describe the library on `master`. Use the [migration guide](/getting-started/migration/) when updating code written for 6.x. The guides and the generated API belong to the same checkout, so compare `pip show TikTokLive` with the version on the [API reference](/api/) index when something differs from your installed release.

For the Node.js implementation, see [TikTok LIVE Connector](https://ttlc.docs.isaackogan.com/). For the managed Euler Stream service, see [Euler Stream's documentation](https://www.eulerstream.com/docs). Their names and payload shapes can differ from this Python package.
