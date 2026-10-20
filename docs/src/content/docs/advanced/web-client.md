---
title: Web client
description: The TikTokWebClient behind client.web, its request helpers, cookie jar, headers and parameters, the signer, and how to write a route of your own.
sidebar:
  order: 1
---

`client.web` is a `TikTokWebClient`, from `TikTokLive.client.web.web_client`. It extends `TikTokHTTPClient` in `TikTokLive.client.web.web_base` with the routes listed on the [routes page](/advanced/routes/). It owns one `httpx.AsyncClient`, built when the client is constructed from `web_proxy` and `web_kwargs` (see [client options](/configuration/options/)), the cookie jar, the headers and query parameters sent to TikTok, and the signer that talks to the signing provider. The high-level `TikTokLiveClient` uses it for every HTTP request it makes; you can use it directly for requests of your own, with or without connecting to a room.

## Request helpers

| Member | Purpose |
| --- | --- |
| `get(url, ...)` | Send a `GET` and return the `httpx.Response`. |
| `post(url, ...)` | Send a `POST` and return the `httpx.Response`. |
| `request(url, method, ...)` | Send any method; `get` and `post` call it. |
| `build_request(url, method, ...)` | Build the `httpx.Request` without sending it; `request` calls it, then `httpx.AsyncClient.send`. |
| `build_url(url, extra_params=None, base_params=True)` | Merge the client's parameters into a URL and return an `httpx.URL`. |
| `httpx_client` | The underlying `httpx.AsyncClient`, for anything the helpers do not cover. |
| `close()` | Close the `httpx.AsyncClient`. |

`get`, `post`, and `request` share one set of keyword arguments:

| Argument | Default | Effect |
| --- | --- | --- |
| `extra_params` | `None` | Query parameters added for this request, over the client's `params`. |
| `extra_headers` | `None` | Headers added for this request, over the client's `headers`. |
| `base_params` | `True` | Include `client.web.params` in the query. The live page and profile page routes pass `False`. |
| `base_headers` | `True` | Include `client.web.headers`. |
| `sign_url` | `False` | Ask the signer for a signed URL first; see below. |
| `sign_url_method`, `sign_url_type` | `None` | The method and type (`"xhr"` or `"fetch"`) to sign with; default to the request's method and `"xhr"`. |
| `http_client` | `None` | An `httpx.AsyncClient` to use in place of the client's own. |
| Other keyword arguments | | Passed to `httpx.AsyncClient.build_request`, such as `content`, `json`, or `timeout`. |

A request is built in this order. `build_request` first overwrites `params["device_id"]` with a fresh random number, on every request. `build_url` then reads any query already in `url`, puts the client's `params` under it when `base_params` is on, and `extra_params` over both; it joins the pairs with `=` and `&` as they are, without percent-encoding, so encode a value that contains reserved characters yourself. The headers are `client.web.headers`, when `base_headers` is on, with `extra_headers` over them, and the cookie jar is attached.

```python
import asyncio

from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.web_settings import WebDefaults

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


async def main() -> None:
    room_id: int = await client.web.fetch_room_id_from_api(client.unique_id)
    response = await client.web.get(
        url=WebDefaults.tiktok_webcast_url + "/room/check_alive/",
        extra_params={"room_ids": str(room_id)},
    )
    print(response.status_code, response.json())
    await client.web.close()


if __name__ == "__main__":
    asyncio.run(main())
```

The base URLs come from `WebDefaults`: `tiktok_app_url` for `www.tiktok.com` pages and `tiktok_webcast_url` for the Webcast API. See [web defaults](/configuration/web-defaults/).

## Cookies, headers, and parameters

`client.web.cookies` is an `httpx.Cookies` jar. It starts from `WebDefaults.web_client_cookies` with `httpx_kwargs["cookies"]` merged over it, every cookie stored for the `.tiktok.com` domain, and it is shared by the HTTP client and the WebSocket handshake. `set_session(session_id, tt_target_idc)` writes `sessionid`, `sessionid_ss`, and `sid_tt` with the session value and `tt-target-idc` with the data center, and sets `params["user_is_login"]` to `"true"`; `set_session(None, None)` writes empty strings and sets it back to `"false"`. The signing step of a connection stores the cookies the provider returns in its `X-Set-TT-Cookie` header here as well. See [authentication](/configuration/authentication/).

`client.web.headers` is a plain `dict`: `WebDefaults.web_client_headers` with `httpx_kwargs["headers"]` merged over it. Its `User-Agent` is sent to TikTok, to the signing provider with each signing request, and in the WebSocket handshake, so the three agree.

`client.web.params` is a plain `dict`: `WebDefaults.web_client_params` with `httpx_kwargs["params"]` merged over it. The client adds `referer` and `root_referer` at construction and `room_id` when a connection starts; routes such as `fetch_room_info`, `fetch_signed_websocket`, and `send_room_chat` read `params["room_id"]` when no room is passed to them. Both dicts can be edited after construction and apply to the next request.

`generate_device_id()` returns the random 20-digit device ID that `build_request` assigns; you will not normally call it.

## Signing

`client.web.signer` is a `TikTokSigner`, from `TikTokLive.client.web.web_signer`. It is configured from `web_kwargs["signer_kwargs"]` (`sign_api_key`, `sign_api_base`), then the `SIGN_API_KEY` and `SIGN_API_URL` environment variables, then `WebDefaults.tiktok_sign_api_key` and `WebDefaults.tiktok_sign_url`; see [signing](/configuration/signing/). It wraps a client from the [Euler Stream](https://www.eulerstream.com/) SDK: an `AuthenticatedClient` that sends the key in an `X-Api-Key` header when one is set, otherwise a plain `Client`, both with a `User-Agent` of `TikTokLive.py/<version>`. In this release the SDK client is created with `verify_ssl=False`. Three properties expose it: `sign_api_key` (the key in use, or `None`), `sdk_client`, and `client`, the SDK's own `httpx.AsyncClient`, which is separate from `client.web.httpx_client` and is not affected by `web_proxy`.

`webcast_sign(url, method, sign_url_type, payload, user_agent, session_id=None, tt_target_idc=None)` asks the provider to sign any `/webcast/` URL. It removes `X-Bogus`, `X-Gnarly`, and `msToken` from the query, posts the URL, method, type, payload, and user agent, and returns the provider's response; `build_request` then replaces the request's URL with `signed_url` and its `User-Agent` with the agent the provider chose. When a session is set, the host allowlist is checked first and the session is included. Failures raise `UnexpectedSignatureError` for a transport error or a non-200 status, `PremiumEndpointError` when the provider answers 403, and `SignatureMissingTokensError` when the response has no `signed_url` or it carries no `msToken`.

`sign_url=True` is the only way a request reaches `webcast_sign`, and no built-in route sets it. The signing step of a connection is the `fetch_signed_websocket` route, which calls the provider's WebSocket endpoint through `signer.sdk_client` directly; see [routes](/advanced/routes/).

## Write a route

A route is a subclass of `ClientRoute`, from `TikTokLive.client.web.web_base`. Its constructor takes the web client and stores it as `self._web`, with a logger as `self._logger`; the subclass defines `__call__` with whatever parameters and return type it needs. The built-in routes are instance attributes of `TikTokWebClient`, created in its constructor, and the client calls them by attribute name, so replacing one on `client.web` with an instance of your own subclass changes what that client does at that step.

```python
import asyncio
from typing import Any, Dict

from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.web_base import ClientRoute
from TikTokLive.client.web.web_settings import WebDefaults


class FetchCheckAliveRoute(ClientRoute):
    """Return TikTok's raw check_alive response for one room."""

    async def __call__(self, room_id: int) -> Dict[str, Any]:
        response = await self._web.get(
            url=WebDefaults.tiktok_webcast_url + "/room/check_alive/",
            extra_params={"room_ids": str(room_id)},
        )
        return response.json()


client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
check_alive: FetchCheckAliveRoute = FetchCheckAliveRoute(client.web)


async def main() -> None:
    room_id: int = await client.web.fetch_room_id_from_api(client.unique_id)
    print(await check_alive(room_id))
    await client.web.close()


if __name__ == "__main__":
    asyncio.run(main())
```

Requests to TikTok are rate-limited and blocked at TikTok's discretion; a route that fails with a non-JSON response or missing page data is usually seeing that. See [troubleshooting](/troubleshooting/).

## Closing

`client.web.close()` closes the HTTP session and is the right call for a client used without connecting. `client.disconnect()` leaves the session open so the client can connect again. `client.close()` also closes the session, and in this release its cleanup runs the event loop synchronously, so awaiting it inside a running coroutine raises `RuntimeError`; see [troubleshooting](/troubleshooting/).

`client.web.fetch_video` and `client.web.fetch_image` are deprecated names for `fetch_video_data` and `fetch_image_data`; each use logs a warning unless `SEND_DEPRECATION_WARNINGS` is turned off. See [environment variables](/configuration/environment/).
