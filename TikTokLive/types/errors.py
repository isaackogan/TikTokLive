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
