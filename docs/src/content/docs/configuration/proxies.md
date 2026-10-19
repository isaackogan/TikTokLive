---
title: Proxies
description: Route the client's HTTP requests and its WebSocket connection through HTTP or SOCKS proxies with web_proxy and ws_proxy.
sidebar:
  order: 6
---

The client has two network paths that can be proxied independently: the HTTP requests it makes to TikTok, and the WebSocket connection to TikTok's Webcast server. Requests to the signing provider go through a third, separate HTTP client that neither parameter affects.

| Parameter | Type | Applies to |
| --- | --- | --- |
| `web_proxy` | `httpx.Proxy` | HTTP requests to TikTok: the live page and API that yield the room ID, live checks, room info, the gift list, and the profile page. |
| `ws_proxy` | `WebcastProxy` | The WebSocket connection. |

```python
from httpx import Proxy

from TikTokLive import TikTokLiveClient
from TikTokLive.events import ConnectEvent

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@isaackogz",
    web_proxy=Proxy("http://proxy.example.com:8080", auth=("username", "password")),
    ws_proxy=Proxy("socks5://proxy.example.com:1080", auth=("username", "password")),
)


@client.on(ConnectEvent)
async def on_connect(event: ConnectEvent) -> None:
    print(f"Connected to @{event.unique_id}")


if __name__ == "__main__":
    client.run()
```

## HTTP proxy

`web_proxy` is passed as the `proxy` argument of the `httpx.AsyncClient` behind `client.web`, so it accepts whatever `httpx.Proxy` accepts; see the [httpx proxy documentation](https://www.python-httpx.org/advanced/proxies/). It may also be given as `web_kwargs={"web_proxy": ...}`; the parameter wins when both are set.

Like any `httpx.AsyncClient`, the HTTP client honours the `HTTP_PROXY`, `HTTPS_PROXY`, and `ALL_PROXY` environment variables when no `web_proxy` is given, unless you pass `web_kwargs={"httpx_kwargs": {"trust_env": False}}`. The signing provider's client is also an `httpx.AsyncClient` and follows the same variables.

## WebSocket proxy

`ws_proxy` accepts an `httpx.Proxy` or a `websockets_proxy.Proxy`; `WebcastProxy`, in `TikTokLive.client.ws.ws_connect`, is the union of the two. An `httpx.Proxy` is converted when the connection opens: its URL must use the `http://`, `socks4://`, or `socks5://` scheme, and credentials come from `auth=` or from the URL's user information. Any other scheme, including `https://`, raises `ValueError` at connect time. A `websockets_proxy.Proxy` is used as is; `websockets_proxy.Proxy.from_url(...)` builds one from the same URL forms.

With a proxy set, the client waits `proxy_conn_timeout` seconds, `10.0` by default, for the proxy to connect; change it through `ws_kwargs`. `ws_kwargs={"proxy": ...}` is an alternative to the parameter.

```python
from websockets_proxy import Proxy

from TikTokLive import TikTokLiveClient

client: TikTokLiveClient = TikTokLiveClient(
    unique_id="@isaackogz",
    ws_proxy=Proxy.from_url("socks5://username:password@proxy.example.com:1080"),
    ws_kwargs={"proxy_conn_timeout": 20.0},
)
```

## What each side sees

TikTok sees the proxy's address on each proxied path, and the WebSocket URL the provider returns is used unchanged through the proxy. The signing provider is reached directly, or through the environment's proxy variables, never through `web_proxy` or `ws_proxy`. For connection failures through a proxy, see [troubleshooting](/troubleshooting/).
