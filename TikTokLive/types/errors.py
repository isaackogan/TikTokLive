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


class InitialCursorMissing(FailedConnection):
    """
    Error that is raised when the initial cursor is missing

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


class WebsocketConnectionFailed(RuntimeError):
    """
    Raised when a connection to the TikTok Webcast websocket fails

    """

    pass


class FailedHTTPRequest(RuntimeError):
    """
    Error raised whenever a request fails to HTTP [Generic]

    """


class FailedFetchRoomInfo(FailedHTTPRequest):
    """
    Error raised when failing to fetch room info

    """


class FailedParseUserHTML(FailedFetchRoomInfo):
    """
    Error raised when failing to parse room html to retrieve the Room ID of the stream

    """


class FailedRoomPolling(FailedHTTPRequest):
    """
    Error raised when room polling encounters an exception

    """

    pass


class FailedFetchGifts(FailedHTTPRequest):
    """
    Error raised when fetching gifts encounters an exception

    """


class DownloadStreamError(RuntimeError):
    """
    Error raised broadly for anything relating to downloading streams

    """

    pass


class AlreadyDownloadingStream(DownloadStreamError):
    """
    Error raised when already downloading a livestream and one attempts to start a second download

    """


class NotDownloadingStream(DownloadStreamError):
    """
    Error raised when trying to stop downloading a livestream you are not currently downloading

    """


class DownloadProcessNotFound(DownloadStreamError):
    """
    Error raised when stopping a download and the process is not found. Usually, you're stopping it before the process spawns

    """
