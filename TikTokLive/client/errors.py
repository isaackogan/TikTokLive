class AlreadyConnectedError(RuntimeError):
    """
    Thrown when attempting to connect to a user that is already connected to

    """


class UserOfflineError(RuntimeError):
    """
    Thrown when the requested streamer to watch is offline

    """


class UserNotFoundError(RuntimeError):
    """
    Thrown when the request to check if a user is live fails because a user has no
    livestream account (e.g. <1000 followers)

    """

    def __init__(self, unique_id: str, *args):
        self.unique_id: str = unique_id
        super().__init__(*args)


class AgeRestrictedError(RuntimeError):
    """
    Thrown when a LIVE is age restricted. Pass sessionid to bypass.
    """


class InitialCursorMissingError(RuntimeError):
    """
    Thrown when the cursor for connecting to TikTok is missing (blocked)

    """


class WebsocketURLMissingError(RuntimeError):
    """
    Thrown when the websocket URL to connect to TikTok is missing (blocked)

    """
