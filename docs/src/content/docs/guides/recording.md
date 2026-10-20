---
title: Record a livestream
description: Save a stream to disk with the fetch_video_data route, pick a rendition the room publishes, stop on disconnect or from your own timer, and what FFmpeg is needed.
sidebar:
  order: 4
---

`client.web.fetch_video_data` records the live video with FFmpeg. It reads the stream URLs from the room's metadata, so the client must connect with `fetch_room_info=True`, and it runs FFmpeg as a subprocess, so the `ffmpeg` binary must be installed and on `PATH`. The `ffmpy` wrapper it uses ships with the package. This guide is a tightened version of the repository's `examples/recording.py`.

```sh
ffmpeg -version
```

If that fails, install FFmpeg first: `brew install ffmpeg` on macOS, `sudo apt install ffmpeg` on Debian and Ubuntu, or a build from the FFmpeg project for Windows.

## Start on connect, stop on disconnect

`fetch_video_data(output_fp, room_info, record_for=-1, quality=VideoFetchQuality.LD, record_format=VideoFetchFormat.FLV, output_format=None, **kwargs)` starts the recording on a background thread and returns at once; `start(...)` is an alias that takes the same keyword arguments. `room_info` is `client.room_info`, which is `None` unless the connection was made with `fetch_room_info=True`. `stop()` sends FFmpeg `SIGTERM`, which lets it close the file. `is_recording` becomes `True` once the thread has started FFmpeg, shortly after `start` returns, and `output_filename` is the path given to the last `start`.

`disconnect()` stops a running recording itself, so a recording started on `ConnectEvent` ends with the stream. The handler below still checks `is_recording` for a socket that closed on its own.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.client.logger import LogLevel
from TikTokLive.client.web.routes.fetch_video_data import VideoFetchQuality
from TikTokLive.events import ConnectEvent, DisconnectEvent

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent) -> None:
    if client.room_info is None:
        client.logger.error("No room info; connect with fetch_room_info=True to record")
        return

    client.web.fetch_video_data.start(
        output_fp=f"{event.unique_id}.mp4",
        room_info=client.room_info,
        quality=VideoFetchQuality.HD,
        output_format="mp4",
    )


@client.on(DisconnectEvent)
async def on_disconnect(event: DisconnectEvent) -> None:
    if client.web.fetch_video_data.is_recording:
        client.web.fetch_video_data.stop()
    client.logger.info(f"Recording saved to {client.web.fetch_video_data.output_filename}")


if __name__ == "__main__":
    client.logger.setLevel(LogLevel.INFO.value)
    client.run(fetch_room_info=True)
```

The route logs the start and the stop, with the duration, at `INFO`. Starting a second recording while one runs raises `DuplicateDownloadError`; one route records one stream at a time, so use one client per stream you record.

## Record for a fixed time

`record_for` is a length in seconds that the route passes to FFmpeg as `-t`, so FFmpeg exits by itself when the time is up; a value of `0` or less records until `stop()`. In this release the route does not notice that exit: `is_recording` stays `True` after a `record_for` recording completes, and the `stop()` that `disconnect()` then calls raises `ProcessLookupError`. Until that is fixed, time the recording yourself and call `stop()` before disconnecting. With `start()` the program can keep working while the recording runs:

```python
import asyncio

from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.routes.fetch_video_data import VideoFetchFormat, VideoFetchQuality

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


async def main() -> None:
    await client.start(fetch_room_info=True)
    if client.room_info is None:
        raise RuntimeError("room info was not fetched")

    client.web.fetch_video_data(
        output_fp="clip.mp4",
        room_info=client.room_info,
        quality=VideoFetchQuality.HD,
        record_format=VideoFetchFormat.HLS,
        output_format="mp4",
    )

    await asyncio.sleep(60)
    client.web.fetch_video_data.stop()
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
```

## Rendition, format, and container

`quality` is a `VideoFetchQuality` naming one of the renditions TikTok publishes for the room:

| Value | Rendition |
| --- | --- |
| `LD` | 480p, about 500 kbit/s (the default) |
| `SD` | 480p, about 800 kbit/s |
| `HD` | 540p, about 1 Mbit/s |
| `UHD` | 720p, about 1 Mbit/s |
| `ORIGIN` | The source as published |

Rooms do not publish every rendition; one seen while writing this guide offered only `hd` and an audio-only variant that the enum does not name. Requesting a rendition the room lacks raises `KeyError` from `start`, including the default `LD`. The renditions are listed in `room_info`, so print them first and pick a `VideoFetchQuality` whose value appears:

```python
import asyncio
import json
from typing import Any, Dict, List

from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.routes.fetch_video_data import VideoFetchQuality

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


async def main() -> None:
    await client.start(fetch_room_info=True)
    if client.room_info is None:
        raise RuntimeError("room info was not fetched")

    stream_data: Dict[str, Any] = json.loads(
        client.room_info["stream_url"]["live_core_sdk_data"]["pull_data"]["stream_data"]
    )
    renditions: Dict[str, Any] = stream_data["data"]
    print("Renditions:", sorted(renditions))

    usable: List[VideoFetchQuality] = [quality for quality in VideoFetchQuality if quality.value in renditions]
    print("Usable VideoFetchQuality values:", [quality.name for quality in usable])
    if usable:
        print(f"Formats for {usable[0].name}:", sorted(renditions[usable[0].value]["main"]))

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
```

`record_format` is a `VideoFetchFormat`, `FLV`, `HLS`, or `CMAF`, and names the stream variant to pull from the chosen rendition; when the rendition does not offer the requested variant the route falls back to FLV. `output_format` is the container FFmpeg writes, any muxer it supports such as `mp4`; when omitted, the record format's name is passed to FFmpeg as `-f` instead. Remaining keyword arguments reach FFmpeg: `loglevel` (default `error`), `global_options`, and extra `inputs` and `outputs` for ffmpy.

Room info cannot be fetched for an age-restricted room without a session; `fetch_room_info=True` raises `AgeRestrictedError` there. See [authentication](/configuration/authentication/) for setting one.
