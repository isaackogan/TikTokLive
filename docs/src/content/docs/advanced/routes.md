---
title: Routes
description: Every route on client.web, the module it lives in, what it requests, what it returns, the client method that wraps it, and the errors it raises.
sidebar:
  order: 2
---

A route is a callable object on `client.web`, one per module under `TikTokLive.client.web.routes`. Each is created when the client is constructed and called like a function; all are `async` except `fetch_video_data`, which starts a thread. The high-level client calls them in a fixed order when it connects, and you can call any of them yourself, before, during, or instead of a connection. See the [web client page](/advanced/web-client/) for the request helpers they share and for writing a route of your own.

## Route registry

The attribute name is the module name for all but the two room-ID routes.

| Attribute on `client.web` | Module | Used by the client for |
| --- | --- | --- |
| `fetch_room_id_from_html` | `fetch_room_id_live_html` | Resolving the room ID when a connection starts. |
| `fetch_room_id_from_api` | `fetch_room_id_api` | The fallback when the live page gives no room ID. |
| `fetch_is_live` | `fetch_is_live` | `client.is_live()` and the live check before connecting. |
| `fetch_room_info` | `fetch_room_info` | `fetch_room_info=True`, stored on `client.room_info`. |
| `fetch_gift_list` | `fetch_gift_list` | `fetch_gift_info=True`, stored on `client.gift_info`. |
| `fetch_signed_websocket` | `fetch_signed_websocket` | The signing step of every connection. |
| `send_room_chat` | `send_room_chat` | `client.send_room_chat(content)`. |
| `fetch_user_unique_id` | `fetch_user_unique_id` | Resolving a numeric ID when `is_user_id=True`. |
| `fetch_image_data` | `fetch_image_data` | Not called by the client; see the [images guide](/guides/images/). |
| `fetch_video_data` | `fetch_video_data` | `disconnect()` stops a running recording; see the [recording guide](/guides/recording/). |

Requests to TikTok go to `WebDefaults.tiktok_app_url` or `WebDefaults.tiktok_webcast_url` with the client's headers, parameters, and cookies, and none of them is signed. `fetch_signed_websocket` and `send_room_chat` go to the signing provider, [Euler Stream](https://www.eulerstream.com/) by default, through `client.web.signer.sdk_client`. The generated [API reference](/api/) has the exact signatures.

```python
import asyncio
from typing import Any, Dict

from TikTokLive import TikTokLiveClient

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


async def main() -> None:
    room_id: int = await client.web.fetch_room_id_from_api(client.unique_id)
    live: bool = await client.web.fetch_is_live(room_id=room_id)
    print(f"Room {room_id} is {'live' if live else 'offline'}")

    if live:
        room_info: Dict[str, Any] = await client.web.fetch_room_info(room_id=room_id)
        print(room_info["owner"]["display_id"], sorted(room_info))

    gifts: Dict[str, Any] = await client.web.fetch_gift_list()
    print(f"{len(gifts.get('gifts', []))} gifts in the catalog")

    await client.web.close()


if __name__ == "__main__":
    asyncio.run(main())
```

## Room ID

`fetch_room_id_from_html(unique_id) -> str` requests `https://www.tiktok.com/@<unique_id>/live` without the client's base parameters and reads the `SIGI_STATE` JSON embedded in the page. It raises `UserOfflineError` when the page reports status `4`, `UserNotFoundError` when the page has no `LiveRoom` section (an account that cannot go live or does not exist), and `FailedParseRoomIdError` when the `SIGI_STATE` tag is missing or is not JSON, which the error text attributes to a block or a captcha, or when the room has no `roomId`.

`fetch_room_id_from_api(unique_id) -> int` requests `/api-live/user/room/` with `uniqueId` and `sourceType=54` and returns `data.user.roomId` as an `int`. It raises `FailedParseRoomIdError` when the response is not JSON, which the error text attributes to rate limiting or a temporary block, and `UserNotFoundError` when TikTok answers `user_not_found`. Its class method `fetch_user_room_data(web, unique_id)` returns the whole response, which `fetch_is_live` reuses.

When a connection starts, the client tries the HTML route and, on any error other than `UserOfflineError`, the API route; if that fails too, the API route's exception is raised with the HTML route's as its cause. Passing `room_id` to `run`, `connect`, or `start` skips both. `FailedParseRoomIdError` is defined in the `fetch_room_id_live_html` module; `UserOfflineError` and `UserNotFoundError` in `TikTokLive.client.errors`.

## Live status

`fetch_is_live(room_id=None, unique_id=None) -> bool` takes one of the two and raises `InvalidFetchIsLiveRequest` when given neither. By `room_id` it calls `fetch_is_live_room_ids` and returns the first entry, raising `MissingRoomIdInResponse` when the response has none; by `unique_id` it calls `fetch_is_live_unique_id`, which reads the API route's user data and returns whether `liveRoom.status` is not `4`.

`fetch_is_live_room_ids(*room_ids) -> List[bool]` requests `/room/check_alive/` once for every room given and returns their statuses in order. `client.is_live()` is a thin wrapper that checks by `unique_id`. See the [live-status guide](/guides/check-live/).

## Room information and gifts

`fetch_room_info(room_id=None, unique_id=None) -> Dict[str, Any]` requests `/room/info/` for a room ID, which defaults to the connected room's `params["room_id"]`, or `/room/info_by_user/` for a `unique_id`; passing both raises `InvalidFetchRoomInfoPayload`. It returns the response's `data` dict, raises `AgeRestrictedError` when TikTok withholds it (the data carries `prompts` or has at most one key), and wraps any request failure in `FailedFetchRoomInfoError`. Pass `room_id` or `unique_id` explicitly when the client has not connected.

`fetch_gift_list(room_id=None) -> Dict[str, Any]` requests `/gift/list/` and returns the response's `data` dict, whose `gifts` entry lists the catalog; see the [gifts guide](/guides/gifts/). In this release the request does not use the `room_id` argument, so the catalog is the one TikTok returns for the client's defaults rather than for a particular room. A request failure raises `FailedFetchGiftListError`.

## Signed WebSocket

`fetch_signed_websocket(platform, room_id=None, session_id=None, tt_target_idc=None) -> ProtoMessageFetchResult` is the signing step of every connection, run by the client after the live check. It calls the provider's WebSocket endpoint with the room ID (defaulting to `params["room_id"]`), the client's `User-Agent`, the `platform` (`WebcastPlatform.WEB` or `WebcastPlatform.MOBILE`, defined in the same module), the client identifier `ttlive-python`, and, when a session is set, the session cookies from the arguments or the cookie jar after the host allowlist check. `WebcastPlatform.MOBILE` without a session raises `ValueError`.

The response body is the first fetch result, parsed into a `ProtoMessageFetchResult` with the WebSocket URL, the cursor, and possibly messages; the cookies in the response's `X-Set-TT-Cookie` header are stored in the jar, and a response without that header raises `SignAPIError` with reason `EMPTY_COOKIES`. HTTP 429 raises `SignatureRateLimitError`, an empty body `SignAPIError` with `EMPTY_PAYLOAD`, any other non-200 status `SIGN_NOT_200`, and a connection failure `CONNECT_ERROR`. See [signing](/configuration/signing/) for the error classes and [WebSocket client](/advanced/websocket/) for what happens with the result.

## Chat

`send_room_chat(content, room_id=None, session_id=None, tt_target_idc=None) -> Dict[str, Any]` posts a chat message through the provider's premium chat endpoint. A session is required: without `sessionid` the route raises `ValueError`, without `tt-target-idc` alongside it `ValueError` too, and without the host allowlist `AuthenticatedWebSocketConnectionError`. `room_id` defaults to `params["room_id"]` and raises `ValueError` when neither is set. The return value is a dict with `code`, `message`, and `data`. `client.send_room_chat(content)` passes the connected room. See the [chat guide](/guides/send-chat/).

## Users, images, and video

`fetch_user_unique_id(user_id) -> str` requests `https://www.tiktok.com/@<user_id>` without base parameters and reads the username from the page's `__UNIVERSAL_DATA_FOR_REHYDRATION__` JSON. It raises `FailedParseAppInfo` when that JSON is missing or invalid and `FailedResolveUserId` when it holds no `uniqueId`. The client calls it for a numeric `unique_id` when `is_user_id=True`.

`fetch_image_data(image) -> bytes` downloads an `ImageModel`, using `url_list[0]`, or a URL string with the client's session and returns the bytes. See the [images guide](/guides/images/).

`fetch_video_data(output_fp, room_info, record_for=-1, quality=VideoFetchQuality.LD, record_format=VideoFetchFormat.FLV, output_format=None, **kwargs) -> None` starts an FFmpeg recording on a thread from the stream URLs in `room_info`. The route also has `start(**kwargs)`, `stop()`, `is_recording`, `output_filename`, and `ffmpeg`, and raises `DuplicateDownloadError` when a recording is already running. `VideoFetchQuality` and `VideoFetchFormat` are defined in the same module. See the [recording guide](/guides/recording/) for the renditions and the caveats of this release.

## Error classes

Errors shared across routes are in `TikTokLive.client.errors`: `TikTokLiveError` is the base class, and `UserOfflineError`, `UserNotFoundError`, `AgeRestrictedError`, `WebcastBlockedError`, and the `SignAPIError` family are the ones routes raise. Route-specific errors are defined next to the route: `FailedParseRoomIdError` in `fetch_room_id_live_html`; `InvalidFetchIsLiveRequest` and `MissingRoomIdInResponse` in `fetch_is_live`; `FailedFetchRoomInfoError` and `InvalidFetchRoomInfoPayload` in `fetch_room_info`; `FailedFetchGiftListError` in `fetch_gift_list`; `DuplicateDownloadError` in `fetch_video_data`; `FailedParseAppInfo` and `FailedResolveUserId` in `fetch_user_unique_id`. All subclass `TikTokLiveError`, which subclasses `RuntimeError`, and every message starts with the package version. See [troubleshooting](/troubleshooting/).
