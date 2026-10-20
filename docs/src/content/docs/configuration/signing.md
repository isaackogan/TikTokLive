---
title: Signing
description: How TikTokLive obtains a signed WebSocket connection from Euler Stream, where to put an API key, how to use another signing server, and how rate limits and other provider errors surface.
sidebar:
  order: 4
---

TikTokLive does not build the Webcast WebSocket URL itself: when a connection starts, it asks a signing provider for the first fetch result and the signed WebSocket URL. The default provider is [Euler Stream](https://www.eulerstream.com/) at `https://api.eulerstream.com`, reached through the `EulerApiSdk` package. Signing works without an account; an API key raises the limits that apply to you. Plans, limits, and endpoint permissions are set by the provider and described in [Euler Stream's documentation](https://www.eulerstream.com/docs), not here.

## What is sent to the provider

When `run`, `connect`, or `start` reaches the signing step, `client.web.fetch_signed_websocket` makes one request to the provider carrying the room ID, the client's `User-Agent` header, the `platform`, the client identifier `ttlive-python`, and, only when a session is set, your `sessionid` and `tt-target-idc` cookies; see [authentication](/configuration/authentication/). The response body is the first `ProtoMessageFetchResult`, which holds the WebSocket URL and may already hold messages, and an `X-Set-TT-Cookie` header whose cookies the client stores for the connection. Every request to the provider identifies the library with a `User-Agent` of `TikTokLive.py/<version>` and, when a key is configured, sends it in an `X-Api-Key` header.

`client.web.send_room_chat` also goes through the provider, using its premium chat endpoint. Requests to TikTok's own HTTP API, such as the room ID, live checks, room info, and the gift list, are not signed and do not touch the provider.

## API key

Three places are consulted, in this order; the first non-empty value wins.

1. `web_kwargs={"signer_kwargs": {"sign_api_key": "..."}}`, for one client.
2. The `SIGN_API_KEY` environment variable.
3. `WebDefaults.tiktok_sign_api_key`, set before creating the client.

The key is read when the client is constructed, so set the variable or the field first. `client.web.signer.sign_api_key` returns the key in use, or `None`.

```sh
export SIGN_API_KEY="your-api-key"
```

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.web_settings import WebDefaults

WebDefaults.tiktok_sign_api_key = "your-api-key"

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
print(client.web.signer.sign_api_key)
```

## Signing server URL

The base URL follows the same precedence: `sign_api_base` in `signer_kwargs`, then the `SIGN_API_URL` environment variable, then `WebDefaults.tiktok_sign_url`. The client talks to the URL through the Euler Stream SDK, so another server must serve the same API. If you also use a session, the allowlist described in [authentication](/configuration/authentication/) compares against `WebDefaults.tiktok_sign_url` only, so set the field rather than only the variable.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.web_settings import WebDefaults

WebDefaults.tiktok_sign_url = "https://sign.example.com"

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
```

## Rate limits

When the provider answers with HTTP 429, the connection attempt raises `SignatureRateLimitError` from `TikTokLive.client.errors`. `retry_after` is the number of seconds to wait, read from the response's `RateLimit-Remaining` header, and `reset_time` is the Unix timestamp at which the limit resets, from `RateLimit-Reset`. The message names the limit that was hit and quotes the provider's own message in a framed block; set `SIGN_SERVER_MESSAGE_DISABLED` to drop the quote. The client does not retry on its own.

```python
import asyncio

from TikTokLive import TikTokLiveClient
from TikTokLive.client.errors import SignatureRateLimitError

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


async def main() -> None:
    while True:
        try:
            await client.connect()
            return
        except SignatureRateLimitError as error:
            print(f"Rate limited; retrying in {error.retry_after} seconds")
            await asyncio.sleep(error.retry_after)


if __name__ == "__main__":
    asyncio.run(main())
```

Each connection attempt spends one signing request, so poll with `is_live` rather than by connecting; see [connection lifecycle](/getting-started/connection/).

## Other provider errors

Every provider failure is a `SignAPIError`. Its `reason` is a `SignAPIError.ErrorReason`, `response` is the `httpx.Response` when there was one, and `log_id` and `agent_id` are the provider's `X-Request-Id` and `X-Agent-Id` headers, which identify the request when you contact the [TikTok LIVE signing API](https://www.eulerstream.com/) team about it.

| Reason | Raised when |
| --- | --- |
| `CONNECT_ERROR` | The provider could not be reached. |
| `RATE_LIMIT` | HTTP 429; the error is a `SignatureRateLimitError`. |
| `EMPTY_PAYLOAD` | The provider returned an empty body, or, as `SignatureMissingTokensError`, a URL-signing response without `signed_url` or `msToken`. |
| `SIGN_NOT_200` | Any other non-200 status; the message includes the body. Also used by `UnexpectedSignatureError` when URL signing fails. |
| `EMPTY_COOKIES` | The response carried no `X-Set-TT-Cookie` header. |
| `PREMIUM_ENDPOINT` | URL signing was refused with code 403, as `PremiumEndpointError`: the key in use does not permit that endpoint. |
| `AUTHENTICATED_WS` | A session would be sent to a host not allowed by `WHITELIST_AUTHENTICATED_SESSION_ID_HOST`, as `AuthenticatedWebSocketConnectionError`. |

`client.web.signer.webcast_sign` signs an arbitrary `/webcast/` URL and is reached through `client.web.get(url, sign_url=True)`. No built-in route uses it in this release, so `UnexpectedSignatureError`, `SignatureMissingTokensError`, and `PremiumEndpointError` concern custom routes only. For symptoms and fixes, see [troubleshooting](/troubleshooting/).
