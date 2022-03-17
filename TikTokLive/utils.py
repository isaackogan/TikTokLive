def get_room_id_from_main_page_html(main_page_html: str) -> str:
    """
    Get the room ID from the HTML of the creator's page.
    If this fails, you are probably blocked from TikTok. Use a VPN.

    :return: Their room ID

    """
    try:
        return main_page_html.split("__room_id=")[1].split("\"/>")[0]
    except:
        pass

    try:
        return main_page_html.split('"roomId":"')[1].split('"}')[0]
    except:
        pass

    valid_response: bool = '"og:url"' in main_page_html
    raise Exception("User might be offline" if valid_response else "Your IP or country might be blocked by TikTok.")


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
