"""
Minimal web UI example.

A Flask backend that connects a TikTokLiveClient to a livestream and
streams Comment/Gift/Like events to the browser over Server-Sent Events
(SSE), paired with a static index.html that renders them as a live feed.

Run:
    pip install flask
    python examples/web-ui/service.py

Then open http://localhost:5000 and enter a "@username" to connect.
"""
import asyncio
import json
import queue
import threading
import time
from pathlib import Path
from typing import Optional

from flask import Flask, Response, jsonify, request, send_from_directory

from TikTokLive.client.client import TikTokLiveClient
from TikTokLive.client.errors import UserOfflineError
from TikTokLive.events import CommentEvent, ConnectEvent, DisconnectEvent, GiftEvent, LikeEvent

app = Flask(__name__, static_folder=None)

_events: "queue.Queue[dict]" = queue.Queue()
_client: Optional[TikTokLiveClient] = None
_thread: Optional[threading.Thread] = None
_lock = threading.Lock()


def _emit(event_type: str, **payload) -> None:
    _events.put({"type": event_type, "ts": time.time(), **payload})


def _build_client(username: str) -> TikTokLiveClient:
    client = TikTokLiveClient(unique_id=username)

    @client.on(ConnectEvent)
    async def on_connect(event: ConnectEvent):
        _emit("connect", username=event.unique_id)

    @client.on(DisconnectEvent)
    async def on_disconnect(_: DisconnectEvent):
        _emit("disconnect")

    @client.on(CommentEvent)
    async def on_comment(event: CommentEvent):
        _emit("comment", user=event.user.nickname, comment=event.comment)

    @client.on(GiftEvent)
    async def on_gift(event: GiftEvent):
        # Wait for a streakable gift's streak to finish before showing it,
        # otherwise every repeat in the streak prints its own line.
        if event.gift.streakable and event.streaking:
            return

        _emit("gift", user=event.user.nickname, gift=event.gift.name, count=event.repeat_count)

    @client.on(LikeEvent)
    async def on_like(event: LikeEvent):
        _emit("like", user=event.user.nickname, count=event.count, total=event.total)

    return client


def _run_client(client: TikTokLiveClient) -> None:
    try:
        client.run()
    except UserOfflineError:
        _emit("error", message="That user is not currently live.")
    except Exception as ex:
        _emit("error", message=str(ex))


def _stop_current_client() -> None:
    global _client, _thread

    if _client is None:
        return

    # client.run() blocks inside an event loop owned by the background
    # thread, so disconnecting from the Flask request thread has to be
    # scheduled onto that same loop rather than awaited directly here.
    asyncio.run_coroutine_threadsafe(_client.disconnect(), _client._asyncio_loop)
    _thread.join(timeout=5)
    _client = None
    _thread = None


@app.post("/api/connect")
def connect():
    global _client, _thread

    username = (request.get_json(silent=True) or {}).get("username", "").strip()
    if not username:
        return jsonify({"error": "username is required"}), 400

    with _lock:
        _stop_current_client()
        _client = _build_client(username)
        _thread = threading.Thread(target=_run_client, args=(_client,), daemon=True)
        _thread.start()

    return jsonify({"status": "connecting", "username": username})


@app.post("/api/disconnect")
def disconnect():
    with _lock:
        _stop_current_client()

    return jsonify({"status": "disconnected"})


@app.get("/api/stream")
def stream():
    def generate():
        while True:
            event = _events.get()
            yield f"data: {json.dumps(event)}\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.get("/")
def index():
    return send_from_directory(Path(__file__).parent, "index.html")


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
