class AlreadyConnecting(RuntimeError):
    """
    Error that is raised when attempting to connect to a livestream whilst already attempting to connect.

    """
    pass


class AlreadyConnected(RuntimeError):
    """
    Error that is raised when attempting to connect to a livestream whilst already connected.

    """
    pass


class LiveNotFound(RuntimeError):
    """
    Error that is raised when the livestream you are trying to connect to is offline/does-not-exist.

    """
    pass


class FailedConnection(RuntimeError):
    """
    Error that is raised when the connection to a livestream fails (generic).

    """
    pass


class InvalidSessionId(RuntimeError):
    """
    Error raised when a session ID is expired or missing

    """

    pass


class ChatMessageSendFailure(RuntimeError):
    """
    Error raised when a TikTok chat message fails to send

    """

    pass


class ChatMessageRepeat(ChatMessageSendFailure):
    """
    Error raised when someone repeats a chat message

    """

    pass
