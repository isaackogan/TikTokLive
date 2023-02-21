import json
import re

from TikTokLive.types import FailedParseUserHTML


def get_room_id_from_main_page_html(main_page_html: str) -> str:
    """
    Get the room ID from the HTML of the creator's page.
    If this fails, you are probably blocked from TikTok. Use a VPN.

    :return: The client's Room ID

    """

    try:
        return re.search(r'room_id=([0-9]*)', main_page_html).group(0).split("=")[1]
    except:
        pass

    try:
        c = r'{' + re.search(r'"roomId":"([0-9]*)"', main_page_html).group(0) + r'}'
        return json.loads(c)['roomId']
    except:
        pass

    exception: str = "User might be offline" if '"og:url"' in main_page_html else "Your IP or country might be blocked by TikTok."
    raise FailedParseUserHTML(exception)


def validate_and_normalize_unique_id(unique_id: str) -> str:
    """
    Take a host of unique_id formats and convert them into a "normalized" version.
    For example, "@tiktoklive" -> "tiktoklive"

    :return: Normalized version of the unique_id
    """

    if not isinstance(unique_id, str):
        raise Exception("Missing or invalid value for 'uniqueId'. Please provide the username from TikTok URL.")

    return (
        unique_id
            .replace("https://www.tiktok.com/", "")
            .replace("/live", "")
            .replace("@", "")
            .strip()
    )
