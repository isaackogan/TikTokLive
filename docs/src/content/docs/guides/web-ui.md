---
title: Web UI and overlays
description: Run the client in a Python process and stream selected events to a browser over Server-Sent Events, following the repository's web-ui example.
sidebar:
  order: 7
---

Run the client in a Python process you control and forward only the data your interface needs. The browser never holds the signing API key or a TikTok session; it receives small JSON messages over a transport you own. This guide uses Server-Sent Events (SSE) with Flask, the pattern of the repository's `examples/web-ui/service.py`, which pairs the service below with a single `index.html`. The same shape works with any web framework or with WebSockets.

The flow has three parts: a background thread owns the client's event loop and runs `connect()`; event handlers turn each event into a small `dict` and put it on a queue per connected browser; an endpoint reads its queue and writes each `dict` as an SSE `data:` line.

```sh
pip install flask
python service.py
```

## The service

```python
import asyncio
import json
import queue
import threading
import time
from typing import Any, Dict, Iterator, Set

from flask import Flask, Response

from TikTokLive import TikTokLiveClient
from TikTokLive.client.errors import UserOfflineError
from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent, GiftEvent, LikeEvent

UNIQUE_ID: str = "@isaackogz"
QUEUE_SIZE: int = 500

app = Flask(__name__)
client: TikTokLiveClient = TikTokLiveClient(unique_id=UNIQUE_ID)
loop: asyncio.AbstractEventLoop = asyncio.new_event_loop()

subscribers: Set["queue.Queue[Dict[str, Any]]"] = set()
subscribers_lock = threading.Lock()


def emit(event_type: str, **payload: Any) -> None:
    """Fan a small, JSON-safe dict out to every connected browser."""
    message: Dict[str, Any] = {"type": event_type, "ts": time.time(), **payload}
    with subscribers_lock:
        for subscriber in subscribers:
            try:
                subscriber.put_nowait(message)
            except queue.Full:
                pass  # a slow tab loses events rather than stalling the client


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent) -> None:
    emit("connect", username=event.unique_id)


@client.on(DisconnectEvent)
async def on_disconnect(event: DisconnectEvent) -> None:
    emit("disconnect")


@client.on(CommentEvent)
async def on_comment(event: CommentEvent) -> None:
    if event.user is None:
        return
    emit("comment", user=event.user.nickname, comment=event.content)


@client.on(GiftEvent)
async def on_gift(event: GiftEvent) -> None:
    # Wait for a streak to finish so each gift is shown once
    if event.user is None or event.gift is None or event.streaking:
        return
    emit("gift", user=event.user.nickname, gift=event.gift.name, count=event.repeat_count)


@client.on(LikeEvent)
async def on_like(event: LikeEvent) -> None:
    if event.user is None:
        return
    emit("like", user=event.user.nickname, count=event.count, total=event.total)


def run_client() -> None:
    """Own the client's event loop on a background thread."""
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(client.connect())
    except UserOfflineError:
        emit("error", message=f"{UNIQUE_ID} is not live")
    except Exception as ex:
        emit("error", message=str(ex))
    finally:
        loop.run_until_complete(client.web.close())
        loop.close()


@app.get("/api/stream")
def stream() -> Response:
    subscriber: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=QUEUE_SIZE)
    with subscribers_lock:
        subscribers.add(subscriber)

    def generate() -> Iterator[str]:
        try:
            while True:
                try:
                    message = subscriber.get(timeout=15)
                except queue.Empty:
                    yield ": keep-alive\n\n"  # a failed write here reveals a closed tab
                    continue
                yield f"data: {json.dumps(message)}\n\n"
        finally:
            with subscribers_lock:
                subscribers.discard(subscriber)

    return Response(generate(), mimetype="text/event-stream")


@app.post("/api/disconnect")
def disconnect() -> Dict[str, str]:
    # connect() runs on the background loop, so schedule the disconnect there
    if not loop.is_closed():
        asyncio.run_coroutine_threadsafe(client.disconnect(), loop)
    return {"status": "disconnecting"}


if __name__ == "__main__":
    threading.Thread(target=run_client, daemon=True).start()
    app.run(port=5000, threaded=True)
```

The client's loop is created up front and handed to the thread, so the request handlers can reach it: `asyncio.run_coroutine_threadsafe(client.disconnect(), loop)` is the way to stop a connection from another thread. When `connect()` returns, the thread closes the HTTP session with `client.web.close()` and the loop; `client.close()` is not used here because its cleanup runs the loop synchronously and raises `RuntimeError` inside a running one. The service connects once; to reconnect when the stream ends, run the thread's body in a loop as [connection lifecycle](/getting-started/connection/) describes.

Flask is not a dependency of TikTokLive; install it separately. `threaded=True` lets the SSE response stream while other requests are served.

## The browser

The page opens an `EventSource` and renders each message. Keep user text as text: `textContent` rather than `innerHTML`, so a comment cannot inject markup into your overlay.

```html
<div id="feed"></div>
<script>
  const feed = document.getElementById("feed");
  const source = new EventSource("/api/stream");
  source.onmessage = (message) => {
    const event = JSON.parse(message.data);
    const row = document.createElement("div");
    row.textContent = event.type === "comment"
      ? `${event.user}: ${event.comment}`
      : `${event.type} ${JSON.stringify(event)}`;
    feed.prepend(row);
  };
</script>
```

The repository's `examples/web-ui/index.html` adds a username field, connect and disconnect buttons, and styling for each message type on top of this.

## Shape the data

Event payloads are large protobuf messages with nested users, images, and badges. Pick the fields the interface shows and send those, as `emit` does above; a `str`, `int`, `float`, `bool`, or a `dict` and `list` of them serializes with `json.dumps` without help. Guard `event.user` and `event.gift`, which are `Optional`, and apply the event's own rules before forwarding, such as skipping `GiftEvent` while `streaking` is `True` so a streak is shown once. See the [event catalog](/events/) for the fields each event carries.

Give each browser its own bounded queue, as above, so a tab that stops reading does not grow memory without limit or hold up the client. A full queue drops the message for that tab; if an overlay must not miss anything, give it a larger queue or a persistent store rather than an unbounded one.

## Several rooms and shutdown

Use one `TikTokLiveClient` per room, each on its own loop and thread. Clients have separate cookie jars and state, but `WebDefaults` is process-wide: the signing URL, API key, default headers, and cookies set there apply to every client in the process. See [web defaults](/configuration/web-defaults/).

On shutdown, schedule `client.disconnect()` on each client's loop and join the threads, then stop the web server. Keep the signing API key and any TikTok session in this process; the [authentication](/configuration/authentication/) page describes where a session is sent and why it must not reach a browser.
