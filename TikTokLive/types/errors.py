class AlreadyConnecting(RuntimeError):
    """
    Already connecting to live

    """
    pass


class AlreadyConnected(RuntimeError):
    """
    Already connected to live

    """
    pass


class LiveNotFound(RuntimeError):
    """
    Live not found

    """
    pass


class FailedConnection(RuntimeError):
    """
    Failed to make connection

    """
    pass
