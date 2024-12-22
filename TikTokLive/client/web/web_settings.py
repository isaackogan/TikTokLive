import random
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, Union, Optional

from TikTokLive.client.web.web_presets import LocationPreset, DevicePreset, ScreenPreset, Locations, Devices, Screens

# Pick a random location and device preset on start
Location: LocationPreset = random.choice(Locations)
Device: DevicePreset = random.choice(Devices)
Screen: ScreenPreset = random.choice(Screens)

"""Default HTTP client parameters to include in requests to the Webcast API, Sign Server, and Websocket Server"""
DEFAULT_CLIENT_PARAMS: Dict[str, Union[int, str]] = {

    # Original Data Collected
    "aid": 1988,
    "app_language": Location["lang"],
    "app_name": 'tiktok_web',
    "browser_language": Location["lang_country"],
    "browser_name": Device["browser_name"],
    "browser_online": "true",
    "browser_platform": Device["browser_platform"],
    "browser_version": Device["browser_version"],
    "cookie_enabled": "true",
    "device_platform": "web_pc",
    "focus_state": "true",
    "from_page": 'user',
    "history_len": random.randint(4, 14),
    "is_fullscreen": "false",
    "is_page_visible": "true",
    "screen_height": Screen["screen_height"],
    "screen_width": Screen["screen_width"],
    "tz_name": Location["tz_name"],
    "referer": 'https://www.tiktok.com/',
    "root_referer": 'https://www.tiktok.com/',
    "channel": "tiktok_web",

    # New Data
    "data_collection_enabled": "true",
    "os": Device["os"],
    "priority_region": Location["country"],
    "region": Location["country"],
    "user_is_login": "false",
    "webcast_language": Location["lang"],

    # Note: Never include X-Bogus
    "msToken": "",

}

# There's a special set of params for just the WebSocket
DEFAULT_WS_CLIENT_PARAMS: Dict[str, Union[int, str]] = {
    "aid": 1988,
    "app_language": Location["lang"],
    "app_name": "tiktok_web",
    "browser_language": Location["lang_country"],
    "browser_name": Device["browser_name"],
    "browser_version": Device["browser_version"],
    "browser_online": "true",
    "cookie_enabled": "true",
    "imprp": "",
    "tz_name": Location["tz_name"],
    "device_platform": "web",
    "compress": "",
    "debug": "true",
    "heartbeatDuration": "0",
    "host": urllib.parse.quote_plus("https://webcast.tiktok.com"),
    "identity": "audience",
    "live_id": "12",
    "sup_ws_ds_opt": "1",
    "update_version_code": "1.3.0",
    "version_code": "270000",
    "webcast_sdk_version": "1.3.0",
    "screen_height": Screen["screen_height"],
    "screen_width": Screen["screen_width"],
}

"""Default HTTP client headers to include in requests to the Webcast API, Sign Server, and Websocket Server"""
DEFAULT_REQUEST_HEADERS: Dict[str, str] = {
    "Connection": 'keep-alive',
    'Cache-Control': 'max-age=0',
    'User-Agent': Device["user_agent"],
    "Accept": 'text/html,application/json,application/protobuf',
    "Referer": 'https://www.tiktok.com/',
    "Origin": 'https://www.tiktok.com',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    "Sec-Fetch-Site": 'same-site',
    "Sec-Fetch-Mode": 'cors',
    "Sec-Fetch-Dest": 'empty',
    "Sec-Fetch-Ua-Mobile": '?0',
}

"""The unique identifier for ttlive-python"""
CLIENT_NAME: str = "ttlive-python"


"""Whether the curl cffi library is installed"""
try:
    import curl_cffi

    SUPPORTS_CURL_CFFI: bool = True
except ImportError:
    SUPPORTS_CURL_CFFI: bool = False


@dataclass()
class _WebDefaults:
    """
    Default values used when instantiating the TikTokWebClient for a TikTokLiveClient object

    """

    tiktok_app_url: str = "https://www.tiktok.com"
    tiktok_sign_url: str = "https://tiktok.eulerstream.com"
    tiktok_webcast_url: str = 'https://webcast.tiktok.com/webcast'
    client_params: dict = field(default_factory=lambda: DEFAULT_CLIENT_PARAMS)
    client_ws_params: dict = field(default_factory=lambda: DEFAULT_WS_CLIENT_PARAMS)
    client_headers: dict = field(default_factory=lambda: DEFAULT_REQUEST_HEADERS)
    tiktok_sign_api_key: Optional[str] = None
    ja3_impersonate: str = "chrome131"


"""The modifiable settings global for web defaults"""
WebDefaults: _WebDefaults = _WebDefaults()

__all__ = [
    "WebDefaults",
    "CLIENT_NAME",
    "SUPPORTS_CURL_CFFI"
]
