class AlreadyConnectedError(RuntimeError):
    """
    Thrown when attempting to connect to a user that is already connected to

    """


class UserOfflineError(RuntimeError):
    """
    Thrown when the requested streamer to watch is offline

    """


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
