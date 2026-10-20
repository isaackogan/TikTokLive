---
title: Troubleshooting
description: Diagnose connection failures, signing errors, blocked WebSockets, missing events, recording problems, and the known limitations of this release.
---

Start with the smallest [Getting Started](/) example, the exact installed versions from `pip show TikTokLive TikTokLiveProto`, the operation that failed, and the original exception with its cause chain. A connection has four stages that fail differently: the HTTP requests to TikTok that resolve the room and check that it is live, the signing request to the provider, the WebSocket handshake with TikTok, and the decoding of messages once connected. Succeeding at one does not establish that the next works, and a proxy or a session can affect each stage separately.

Every error the library raises subclasses `TikTokLiveError`, in `TikTokLive.client.errors`, except where a standard exception is named below. Each message starts with the package version.

## Connection errors

| Error | Meaning and next check |
| --- | --- |
| `AlreadyConnectedError` | `run`, `connect`, or `start` was called while the client's socket is open. Use one connection per client, or `disconnect()` first. |
| `UserOfflineError` | The live page reported status `4`, or the live check before connecting said the creator is not live. Poll with `is_live()` instead of connecting repeatedly; see [connection lifecycle](/getting-started/connection/). |
| `UserNotFoundError` | The account cannot go live, has never gone live, or does not exist, according to the live page or the API. Check the `unique_id`; the error carries it. |
| `FailedParseRoomIdError` | The live page had no `SIGI_STATE` JSON or the API answered with something other than JSON. The error text attributes both to a block, a captcha, or rate limiting by TikTok. The client tries the live page first and then the API, so the API's error is raised with the page's as its cause. Try `room_id=` on the connection call to skip both, slow down, or change the address the requests come from. |
| `AgeRestrictedError` | `fetch_room_info=True` on an age-restricted room: TikTok withholds the room information without a logged-in session. See [authentication](/configuration/authentication/). |
| `ValueError` from `fetch_signed_websocket` | `platform=WebcastPlatform.MOBILE` without a `sessionid` cookie, or a session set without `tt-target-idc`. |
| `TypeError` from the constructor | `web_kwargs` holds a key other than `httpx_kwargs`, `signer_kwargs`, and `web_proxy`; cookies go in `web_kwargs["httpx_kwargs"]["cookies"]`. See [client options](/configuration/options/). |
| `InitialCursorMissingError`, `WebsocketURLMissingError` | The signed response had no cursor, no WebSocket URL, or no route parameters, so no connection URL could be built. The provider answered without the data TikTok normally returns; retry, and report it with the provider's `log_id` if it persists. |
| `WebcastBlockedError` | TikTok rejected the WebSocket handshake with status 400 or 200; see below. |
| `websockets.exceptions.ConnectionClosedError` | The socket closed with a code other than 1000 or 1001 after connecting; see below. |

## Signing errors

Every provider failure is a `SignAPIError` with a `reason`, the `httpx.Response` when there was one, and `log_id` and `agent_id` read from the response headers. Quote those two IDs when you contact the [TikTok LIVE signing API](https://www.eulerstream.com/) team about a request. See [signing](/configuration/signing/) for the full reason table.

| Error | Meaning and next check |
| --- | --- |
| `SignatureRateLimitError` | The provider answered 429. `retry_after` is the number of seconds to wait and `reset_time` the Unix timestamp of the reset; the message names the limit that was hit and quotes the provider's own message unless `SIGN_SERVER_MESSAGE_DISABLED` is set. Wait for `retry_after`, coordinate retries across every room you connect to, and poll with `is_live()` rather than by connecting. An API key raises the limits that apply to you. |
| `SignAPIError` with `CONNECT_ERROR` | The provider could not be reached. Check the network, `SIGN_API_URL`, and whether the environment's proxy variables apply to the provider's client. |
| `SignAPIError` with `EMPTY_PAYLOAD` | The provider returned an empty body; the error asks whether TikTok is detecting you. Retry later; report with `log_id` if it continues. |
| `SignAPIError` with `SIGN_NOT_200` | Any other status; the message includes the body. |
| `SignAPIError` with `EMPTY_COOKIES` | The response carried no `X-Set-TT-Cookie` header. |
| `AuthenticatedWebSocketConnectionError` | A session would have been sent to a host not allowed by `WHITELIST_AUTHENTICATED_SESSION_ID_HOST`. Nothing was sent. The variable must equal the host part of `WebDefaults.tiktok_sign_url`, `api.eulerstream.com` by default; see [authentication](/configuration/authentication/). |
| `PremiumEndpointError`, `UnexpectedSignatureError`, `SignatureMissingTokensError` | Raised by URL signing, which only a custom route with `sign_url=True` uses: the key lacks permission for the endpoint, the request failed, or the response had no usable tokens. See [web client](/advanced/web-client/). |

Signing requests do not go through `web_proxy` or `ws_proxy`; the provider's client follows the environment's proxy variables instead. See [proxies](/configuration/proxies/).

## "WebSocket rejected by TikTok"

`WebcastBlockedError` means the handshake to TikTok's push server returned an HTTP status instead of the upgrade: 400 with a reason in the `Handshake-Msg` header, or 200, which the error treats as detection. The source notes one specific cause for the second case: the URL was signed with a session, but the matching `sessionid` cookie was not sent, which TikTok reports as an illegal secret key. Check that the session set on the client is the one the signing request used, that the signed URL was used right away (it expires), and whether the error happens without a proxy. Upstream endpoint changes also surface here, so compare with the latest release before assuming a provider outage.

Do not post signed URLs, cookies, API keys, or unredacted response bodies in a public report.

## The connection ends without DisconnectEvent

`DisconnectEvent` is emitted once when the WebSocket loop exits normally: the stream ended, you called `disconnect()`, or TikTok closed the socket with close code 1000 or 1001 or none. A close with any other code, such as a dropped network connection or an idle timeout, raises `websockets.exceptions.ConnectionClosedError` from `connect()` or from the task that `start()` returned, and no `DisconnectEvent` is emitted. Catch it where you await the connection and reconnect from there; the client does not reconnect on its own.

```python
import asyncio

from websockets.exceptions import ConnectionClosedError

from TikTokLive import TikTokLiveClient
from TikTokLive.client.errors import SignatureRateLimitError, UserOfflineError, WebcastBlockedError

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


async def main() -> None:
    try:
        await client.connect()
    except UserOfflineError:
        print("The creator is not live")
    except SignatureRateLimitError as error:
        print(f"Signing rate limit; retry in {error.retry_after} seconds")
    except WebcastBlockedError as error:
        print(f"TikTok rejected the WebSocket: {error}")
    except ConnectionClosedError as error:
        print(f"The socket closed abnormally: {error}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Connected, but no expected events

1. Register listeners before connecting. The first signed response can carry messages, and they are emitted right after `ConnectEvent`; `process_connect_events=False` drops them.
2. Check that the event is derived the way you expect. A follow arrives as `FollowEvent` and then as `SocialEvent`; a stream end as `LiveEndEvent` and then as `ControlEvent`; every message as `WebsocketResponseEvent` as well. See the [event catalog](/events/).
3. `SuperFanEvent` and `SuperFanJoinEvent` never fire in this release: the dispatcher reads a `display_type` attribute that the v3 `Text` message does not have, so the match cannot succeed. `SuperFanBoxEvent`, `FollowEvent`, and `ShareEvent` use a different check and are unaffected. See [subscriptions and fans](/events/subscriptions-and-fans/).
4. Listen for `UnknownEvent` to see messages the installed version has no class for, and for `WebsocketResponseEvent` to see every message, including ones whose payload fails to parse. A parse failure is logged at `ERROR` unless `ignore_broken_payload` or `parse_error_ignorelist` says otherwise. See the [debugging guide](/guides/debugging-events/).
5. Set `client.logger.setLevel(logging.DEBUG)` to log every emitted event by type.
6. Confirm that the room produces the feature. A message defined in the schema is not sent in every room or region; see [protocol types](/advanced/protocol/).

## Recording problems

- `KeyError: 'ld'` (or another rendition) from `fetch_video_data`: the room does not publish the requested rendition, and the default `VideoFetchQuality.LD` is one that rooms often lack. List the room's renditions from `client.room_info` and pick one it offers; the [recording guide](/guides/recording/) shows how.
- `ProcessLookupError` from `disconnect()` or `stop()`: a recording started with `record_for` ended on its own, but `is_recording` stays `True` in this release, so the `stop()` that `disconnect()` calls signals a process that has exited. Time the recording yourself and call `stop()` before disconnecting.
- `DuplicateDownloadError`: a recording is already running on this client; one client records one stream at a time.
- `FFExecutableNotFoundError` from `ffmpy`: FFmpeg is not installed or not on `PATH`. Run `ffmpeg -version` to check.
- `AgeRestrictedError` on `fetch_room_info=True`: recording needs the room information, and an age-restricted room withholds it without a session.

## Known limitations in this release

These describe the checked-in code; recheck them against a newer release.

- `await client.close()` and `await client.disconnect(close_client=True)` raise `RuntimeError: This event loop is already running` when awaited inside a running coroutine, because `close()` runs its cleanup synchronously on the loop. Use `await client.web.close()` to close the HTTP session from async code; `run()` cleans up by itself.
- `SuperFanEvent` and `SuperFanJoinEvent` are never emitted; see above.
- The default `VideoFetchQuality.LD` raises `KeyError` for rooms that publish only other renditions; a room seen while writing these pages offered only `hd` and an audio-only variant.
- After a `record_for` recording ends on its own, `is_recording` stays `True` and `disconnect()` raises `ProcessLookupError`.
- `WHITELIST_AUTHENTICATED_SESSION_ID_HOST` is compared with the host in `WebDefaults.tiktok_sign_url`, not with `SIGN_API_URL`. When you point a session-using client at another provider, set the field as well as the variable. See [environment variables](/configuration/environment/).
- `fetch_gift_list(room_id=None)` accepts a `room_id` that the request does not use; the catalog returned is not room-specific. See [routes](/advanced/routes/).

## Report a reproducible issue

File reports on the [TikTokLive GitHub issues](https://github.com/isaackogan/TikTokLive/issues) page. Include the output of `pip show TikTokLive TikTokLiveProto`, the Python version and operating system, the client options with secrets removed, a minimal example, the exact exception with its cause chain, and which stage failed: room ID, live check, signing, WebSocket handshake, or message decoding. For an event that does not arrive or does not parse, add the message `method` and a base64 payload from the [debugging guide](/guides/debugging-events/), reviewed for personal data. Never include session cookies, API keys, or signed URLs.
