from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import CommentEvent

client = TikTokLiveClient("@satisfyy.me")


async def sign_url(raw_url: str, session_id: str):
    """
    
    You will need to create your OWN function to modify the HTTP request to your liking so that it passes TikTok Auth.
    TikTokLive cannot and will not provide signatures, but if you want this functionality, it's here.
    
    :param raw_url: The URL that requires signing
    :param session_id: The sessionid sending the message
    :return: None
    
    """

    # You will need to generate each of
    signed_url: str = raw_url + (
        f"&msToken={'MUST_GENERATE_ME'}"
        f"&X-Bogus={'MUST_GENERATE_ME'}"
        f"&User-Agent={'MUST_GENERATE_ME'}"
        f"&browserVersion={'MUST_GENERATE_ME'}"
        f"&browserName={'MUST_GENERATE_ME'}"
        f"&_signature={'MUST_GENERATE_ME'}"
    )

    # You will need to supply your own headers
    headers: dict = {
        "Cookie": "ttwid=MUST_GENERATE_TTWID;",
        **client._http.headers
    }

    return signed_url, headers


@client.on("message")
async def on_ping(event: CommentEvent):
    """
    When someone runs the /ping command, choose how to react

    :param event: Comment event
    :return: None

    """

    # If not ping, return
    if event.comment.lower() != "/ping":
        return

        # Reply with Pong
    reply: str = f"{event.user.uniqueId} Pong!"
    print(f"The bot will respond in chat with \"{reply}\"")

    await client.send_message(
        text=reply,
        sign_url_fn=sign_url,
        session_id="SESSION_ID_HERE"
    )


if __name__ == '__main__':
    """
    An example showing you how you can send comments to your live
    
    """

    client.run()
