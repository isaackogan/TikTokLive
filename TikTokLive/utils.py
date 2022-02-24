def get_room_id_from_main_page_html(main_page_html: str):
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


def validate_and_normalize_unique_id(unique_id: str):

    if not isinstance(unique_id, str):
        raise Exception("Missing or invalid value for 'uniqueId'. Please provide the username from TikTok URL.")\

    return (
        unique_id
            .replace("https://www.tiktok.com/", "")
            .replace("/live", "")
            .replace("@", "")
            .strip()
    )