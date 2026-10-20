---
title: Web defaults
description: The WebDefaults object that supplies the base URLs, request parameters, headers, cookies, and API key shared by every client in a process.
sidebar:
  order: 2
---

`WebDefaults` is a module-level instance of the `_WebDefaults` dataclass in `TikTokLive.client.web.web_settings`. Every client reads it, so set fields before creating a client; the change applies to every client created afterwards in the process.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.events import ConnectEvent

WebDefaults.tiktok_sign_api_key = "your-api-key"
WebDefaults.web_client_headers["Accept-Language"] = "en-GB,en;q=0.9"

client: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent) -> None:
    print(f"Connected to @{event.unique_id}")


if __name__ == "__main__":
    client.run()
```

## Fields

| Field | Type | Default | Effect |
| --- | --- | --- | --- |
| `tiktok_app_url` | `str` | `https://www.tiktok.com` | Base URL for requests to `www.tiktok.com`: the live page and the API fallback that yield the room ID, the profile page used by `is_user_id`, and the prefix `parse_unique_id` strips from URLs. |
| `tiktok_sign_url` | `str` | `https://api.eulerstream.com` | Base URL of the signing provider, used when neither `sign_api_base` nor `SIGN_API_URL` is set. Its host is also what `WHITELIST_AUTHENTICATED_SESSION_ID_HOST` must match. See [signing](/configuration/signing/). |
| `tiktok_webcast_url` | `str` | `https://webcast.tiktok.com/webcast` | Base URL for Webcast API requests: live checks, room info, and the gift list. |
| `web_client_params` | `dict` | Generated | Query parameters added to every HTTP request to TikTok. |
| `web_client_headers` | `dict` | Generated | Headers sent with every HTTP request to TikTok, including `User-Agent`. |
| `web_client_cookies` | `dict` | `{"tt-target-idc": "useast1a"}` | Cookies the HTTP client starts with, stored for `.tiktok.com`. |
| `ws_client_params` | `dict` | Generated | Query parameters of the WebSocket URL. |
| `ws_client_params_append_str` | `str` | `&version_code=270000` | Raw string appended to the WebSocket URL after its query. |
| `tiktok_sign_api_key` | `str` or `None` | `None` | Signing provider API key, used when neither `sign_api_key` nor `SIGN_API_KEY` is set. |

The three generated dicts are filled when the module is imported from one randomly chosen location, device, and screen preset (`Locations`, `Devices`, and `Screens` in `TikTokLive.client.web.web_presets`): language, region, time zone, browser name, version, and platform, screen size, and the matching `User-Agent`. The choice is made once per process, so every client in it presents the same browser.

## When each field is read

`tiktok_sign_url` and `tiktok_sign_api_key` configure the client's signer and are read when the client is constructed. `web_client_params`, `web_client_headers`, and `web_client_cookies` are copied into `client.web.params`, `client.web.headers`, and the cookie jar at the same moment, after the `params`, `headers`, and `cookies` from `web_kwargs["httpx_kwargs"]` are merged over them; see [client options](/configuration/options/). `tiktok_app_url` and `tiktok_webcast_url` are read on each request, and `ws_client_params` and `ws_client_params_append_str` each time a connection opens, after `ws_kwargs["base_uri_params"]` and `ws_kwargs["base_uri_append_str"]` are applied.

## Per-client values

Use `WebDefaults` for values every client should share and `web_kwargs` or `ws_kwargs` for one client. The two compose: a header set on `WebDefaults.web_client_headers` reaches every client, and a header in one client's `httpx_kwargs["headers"]` replaces it for that client only.

```python
from TikTokLive import TikTokLiveClient
from TikTokLive.client.web.web_settings import WebDefaults

WebDefaults.web_client_headers["Accept-Language"] = "en-GB,en;q=0.9"

shared: TikTokLiveClient = TikTokLiveClient(unique_id="@isaackogz")
german: TikTokLiveClient = TikTokLiveClient(
    unique_id="@tv_asahi_news",
    web_kwargs={"httpx_kwargs": {"headers": {"Accept-Language": "de-DE,de;q=0.9"}}},
)
```

## Pointing at another signing server

Setting `tiktok_sign_url` changes the provider for every client, and the client talks to it through the Euler Stream SDK, so it must serve the same API. The environment variable `SIGN_API_URL` overrides the field for signing requests, but the session host allowlist compares against the field alone; see [signing](/configuration/signing/) and [authentication](/configuration/authentication/).
