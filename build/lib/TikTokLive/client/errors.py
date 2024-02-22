class AlreadyConnectedError(RuntimeError):
    pass


class UserOfflineError(RuntimeError):
    pass


class InitialCursorMissingError(RuntimeError):
    pass


class WebsocketURLMissingError(RuntimeError):
    pass
