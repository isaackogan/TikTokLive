import os
from typing import Optional

from TikTokLive.client.errors import AuthenticatedWebSocketConnectionError
from TikTokLive.client.web.web_settings import WebDefaults


def check_authenticated_session_id(session_id: Optional[str]):
    if session_id is None:
        return

    if not os.getenv('WHITELIST_AUTHENTICATED_SESSION_ID_HOST'):
        raise AuthenticatedWebSocketConnectionError(
            "For your safety, this request has been BLOCKED. To understand why, see the reason below:\n\t"
            "You set a Session ID, which allows your Session ID to be sent to the Sign Server when connecting to TikTok LIVE.\n\t"
            "This is risky, because a session ID grants a user complete access to your account.\n\t"
            "You should ONLY enable this setting if you trust the Sign Server. The Euler Stream sign server does NOT store your session ID. Third party servers MAY."
            "\n\n\t>> THIRD PARTY SIGN SERVERS MAY STEAL YOUR SESSION ID. <<\n\n\t"
            "It should also be noted that since there are a limited number of sign servers, your session ID will\n\t"
            "connect to TikTok with the same IP address as other users. This could potentially lead to a ban of the account.\n\t"
            "With that said, there has never been a case of a ban due to this feature.\n\t"
            "You are only recommended to use this setting if you are aware of the risks and are willing to take them.\n\t"
            "If you are sure you want to enable this setting, set the environment variable 'WHITELIST_AUTHENTICATED_SESSION_ID_HOST' to the HOST you want to authorize (e.g. 'tiktok.eulerstream.com').\n\t"
            "By doing so, you acknowledge the risks and agree to take responsibility for any consequences."
        )

    if os.getenv('WHITELIST_AUTHENTICATED_SESSION_ID_HOST', '') != WebDefaults.tiktok_sign_url.split("://")[1]:
        raise AuthenticatedWebSocketConnectionError(
            f"The host '{os.getenv('WHITELIST_AUTHENTICATED_SESSION_ID_HOST')}' you set in 'WHITELIST_AUTHENTICATED_SESSION_ID_HOST' does not match the host '{WebDefaults.tiktok_sign_url.split('://')[1]}' of the Sign Server. "
            f"Please set the correct host in 'WHITELIST_AUTHENTICATED_SESSION_ID_HOST' to authorize the Sign Server."
        )
