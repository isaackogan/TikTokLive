import urllib.parse
from typing import TypedDict, List


class LocationPreset(TypedDict):
    """en style ISO code"""
    lang: str

    """en-US style ISO code"""
    lang_country: str

    """US style ISO code"""
    country: str

    """America/Toronto style TZ name"""
    tz_name: str


class DevicePreset(TypedDict):
    browser_version: str
    browser_name: str
    browser_platform: str
    user_agent: str
    os: str


class ScreenPreset(TypedDict):
    screen_width: int
    screen_height: int


Locations: List[LocationPreset] = [
    {
        "lang_country": "en-GB",
        "lang": "en",
        "country": "GB",
        "tz_name": "Europe/London"
    },
    {
        "lang_country": "en-CA",
        "lang": "en",
        "country": "CA",
        "tz_name": "America/Toronto"
    },
    {
        "lang_country": "en-AU",
        "lang": "en",
        "country": "AU",
        "tz_name": "Australia/Sydney"
    },
    {
        "lang_country": "en-NZ",
        "lang": "en",
        "country": "NZ",
        "tz_name": "Pacific/Auckland"
    },
    {
        "lang_country": "en-ZA",
        "lang": "en",
        "country": "ZA",
        "tz_name": "Africa/Johannesburg"
    },
    {
        "lang_country": "en-IE",
        "lang": "en",
        "country": "IE",
        "tz_name": "Europe/Dublin"
    },
    {
        "lang_country": "en-JM",
        "lang": "en",
        "country": "JM",
        "tz_name": "America/Jamaica"
    },
    {
        "lang_country": "en-BZ",
        "lang": "en",
        "country": "BZ",
        "tz_name": "America/Belize"
    },
    {
        "lang_country": "en-TT",
        "lang": "en",
        "country": "TT",
        "tz_name": "America/Port_of_Spain"
    }
]


def user_agent_to_device_preset(user_agent: str) -> DevicePreset:
    """
    Convert a user agent string to a DevicePreset

    :param user_agent: The user agent string
    """

    first_slash = user_agent.find("/")
    browser_name = user_agent[:first_slash]
    browser_version = user_agent[first_slash + 1:]

    # Safe='' is used to make it so that the slashes in the user agent string are escaped
    return {
        "user_agent": user_agent,
        "browser_name": urllib.parse.quote(browser_name, safe=''),
        "browser_version": urllib.parse.quote(browser_version, safe=''),
        "browser_platform": "MacIntel" if "Macintosh" in user_agent else "Win32",
        "os": "mac" if "Macintosh" in user_agent else "windows"
    }


Devices: List[DevicePreset] = [

    # Latest Chrome UA's -> https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome
    user_agent_to_device_preset("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"),
    user_agent_to_device_preset("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"),

    # Latest Safari UA's -> https://www.whatismybrowser.com/guides/the-latest-user-agent/safari
    user_agent_to_device_preset("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15"),

    # Latest Firefox UA's -> https://www.whatismybrowser.com/guides/the-latest-user-agent/firefox
    user_agent_to_device_preset("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0"),
    user_agent_to_device_preset("Mozilla/5.0 (Macintosh; Intel Mac OS X 14.7; rv:130.0) Gecko/20100101 Firefox/130.0"),

    # Latest Edge UA's -> https://www.whatismybrowser.com/guides/the-latest-user-agent/edge
    user_agent_to_device_preset("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/128.0.2739.79"),
    user_agent_to_device_preset("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/128.0.2739.79"),

    # Latest Opera UA's -> https://www.whatismybrowser.com/guides/the-latest-user-agent/opera
    user_agent_to_device_preset("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 OPR/113.0.0.0"),
    user_agent_to_device_preset("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 OPR/113.0.0.0")
]

Screens: List[ScreenPreset] = [
    {
        "screen_width": 1920,
        "screen_height": 1080
    },
    {
        "screen_width": 2560,
        "screen_height": 1440
    },
    {
        "screen_width": 3840,
        "screen_height": 2160
    },
    {
        "screen_width": 4096,
        "screen_height": 2160
    },
    {
        "screen_width": 5120,
        "screen_height": 2880
    },
    {
        "screen_width": 7680,
        "screen_height": 4320
    },
    {
        "screen_width": 1152,
        "screen_height": 2048
    },
    {
        "screen_width": 1440,
        "screen_height": 2560
    },
    {
        "screen_width": 2160,
        "screen_height": 3840
    },
    {
        "screen_width": 4320,
        "screen_height": 7680
    }
]
