class AlreadyConnecting(RuntimeError):
    pass


class AlreadyConnected(RuntimeError):
    pass


class LiveNotFound(RuntimeError):
    pass


class FailedConnection(RuntimeError):
    pass
