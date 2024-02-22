class AlreadyConnecting(RuntimeError):
    """
    Error that is raised when attempting to connect to a livestream whilst already attempting to connect.

    """
    

class AlreadyConnected(RuntimeError):
    """
    Error that is raised when attempting to connect to a livestream whilst already connected.

    """


class LiveNotFound(RuntimeError):
    """
    Error that is raised when the livestream you are trying to connect to is offline/does-not-exist.

    """


class FailedConnection(RuntimeError):
    """
    Error that is raised when the connection to a livestream fails (generic).

    """


class InitialCursorMissing(FailedConnection):
    """
    Error that is raised when the initial cursor is missing

    """


class WebsocketConnectionFailed(FailedConnection):
    """
    Raised when a connection to the TikTok Webcast websocket fails

    """


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


class FailedFetchGifts(FailedHTTPRequest):
    """
    Error raised when fetching gifts encounters an exception

    """


class FailedParseMessage(RuntimeError):
    """
    Error raised when a protobuf message fails to be parsed

    """


class FailedParseGift(FailedParseMessage):
    """
    Error raised when a gift fails to be parsed properly

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


class SignatureRateLimitReached(FailedHTTPRequest):
    """
    When a user hits the signature rate limit

    """

    def __init__(self, retry_after: int, reset_time: int, *args, **kwargs):
        """
        Constructor for signature rate limit

        :param retry_after: How long to wait until the next attempt
        :param reset_time: The unix timestamp for when the client can request again
        :param args: Default RuntimeException *args
        :param kwargs: Default RuntimeException **kwargs

        """

        self._retry_after: int = retry_after
        self._reset_time: int = reset_time

        _args = list(args)
        _args[0] = str(args[0]) % str(self.retry_after)
        FailedHTTPRequest.__init__(self, *_args)

    @property
    def retry_after(self) -> int:
        """
        How long to wait until the next attempt

        """

        return self._retry_after

    @property
    def reset_time(self) -> int:
        """
        The unix timestamp for when the client can request again

        """

        return self._reset_time
