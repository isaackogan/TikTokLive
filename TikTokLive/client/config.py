from typing import Dict, Union

"""Default HTTP client parameters to include in requests to the Webcast API & Websocket Server"""
DEFAULT_CLIENT_PARAMS: Dict[str, Union[int, bool, str]] = {
    "aid": 1988,
    "app_language": 'en-US',
    "app_name": 'tiktok_web',
    "browser_language": 'en',
    "browser_name": 'Mozilla',
    "browser_online": True,
    "browser_platform": 'Win32',
    "browser_version": '5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
    "cookie_enabled": True,
    "cursor": '',
    "internal_ext": '',
    "device_platform": 'web',
    "focus_state": True,
    "from_page": 'user',
    "history_len": 4,
    "is_fullscreen": False,
    "is_page_visible": True,
    "did_rule": 3,
    "fetch_rule": 1,
    "last_rtt": 0,
    "live_id": 12,
    "resp_content_type": 'protobuf',
    "screen_height": 1152,
    "screen_width": 2048,
    "tz_name": 'Europe/Berlin',
    "referer": 'https://www.tiktok.com/',
    "root_referer": 'https://www.tiktok.com/',
    "msToken": '',
    "version_code": 180800,
    "webcast_sdk_version": '1.3.0',
    "update_version_code": '1.3.0',
}

"""Default HTTP client headers to include in requests to the Webcast API & Websocket Server"""
DEFAULT_REQUEST_HEADERS: Dict[str, str] = {
    "Connection": 'keep-alive',
    'Cache-Control': 'max-age=0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.63 Safari/537.36',
    "Accept": 'text/html,application/json,application/protobuf',
    "Referer": 'https://www.tiktok.com/',
    "Origin": 'https://www.tiktok.com',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
}

"""The URL of the TikTok Webapp"""
TIKTOK_URL_WEB: str = 'https://www.tiktok.com/'

"""The URL of the Webcast API"""
TIKTOK_URL_WEBCAST: str = 'https://webcast.tiktok.com/webcast/'

"""The URL of the Webcast External Signing API"""
TIKTOK_SIGN_API: str = "https://tiktok.eulerstream.com/"
