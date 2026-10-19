---
title: Environment variables
description: Every environment variable TikTokLive reads, its default, what it changes, and when it is read.
sidebar:
  order: 3
---

Set these in the process environment before creating a client. TikTokLive does not load a `.env` file; use your shell, your process manager, or a library such as `python-dotenv` before the client is constructed.

| Variable | Default | Effect |
| --- | --- | --- |
| `SIGN_API_KEY` | Unset | API key for the signing provider. A `sign_api_key` in `web_kwargs["signer_kwargs"]` takes precedence over it, and it takes precedence over `WebDefaults.tiktok_sign_api_key`. Read when a client is constructed. See [signing](/configuration/signing/). |
| `SIGN_API_URL` | Unset; `WebDefaults.tiktok_sign_url` applies, `https://api.eulerstream.com` | Base URL of the signing provider, with the same precedence as the key: a `sign_api_base` in `signer_kwargs`, then this variable, then the `WebDefaults` field. Read when a client is constructed. |
| `SIGN_SERVER_MESSAGE_DISABLED` | Unset | Any non-empty value drops the provider's own message from `SignatureRateLimitError`; the retry delay stays. Read when a rate-limited response arrives. |
| `WHITELIST_AUTHENTICATED_SESSION_ID_HOST` | Unset | The signing host allowed to receive your TikTok session cookies. It must equal the part of `WebDefaults.tiktok_sign_url` after `://`, which is `api.eulerstream.com` by default; a request that would send a session otherwise raises `AuthenticatedWebSocketConnectionError`. Read on each such request. See [authentication](/configuration/authentication/). |
| `SEND_DEPRECATION_WARNINGS` | `true` | Set it to anything other than `true` (case-insensitive) to silence the warning logged when the deprecated `client.web.fetch_video` and `client.web.fetch_image` attributes are used in place of `fetch_video_data` and `fetch_image_data`. Read once when `TikTokLive` is imported. |

```sh
export SIGN_API_KEY="your-api-key"
export WHITELIST_AUTHENTICATED_SESSION_ID_HOST="api.eulerstream.com"
python chat.py
```

## Signing URL and the allowlist

`WHITELIST_AUTHENTICATED_SESSION_ID_HOST` is compared with `WebDefaults.tiktok_sign_url`, not with `SIGN_API_URL`. When you point the client at another provider with `SIGN_API_URL` and also use a session, set `WebDefaults.tiktok_sign_url` to the same URL, or the comparison expects `api.eulerstream.com`. The value after `://` is compared whole, so include a port if the URL has one.

## Application variables

Names such as `TIKTOK_SESSION_ID` and `TIKTOK_TARGET_IDC` in this site's examples are read by the example code with `os.environ`. The library does not read them.
