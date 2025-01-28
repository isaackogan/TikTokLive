import enum
from typing import Optional


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


class WebcastBlocked200Error(RuntimeError):
    """
    Thrown when the webcast is blocked by TikTok with a 200 status code (detected)

    """


class SignAPIError(RuntimeError):
    """
    Thrown when a fetch to the Sign API fails for one reason or another

    """

    class ErrorReason(enum.Enum):
        """
        Possible failure reasons

        """

        RATE_LIMIT = 1
        CONNECT_ERROR = 2
        EMPTY_PAYLOAD = 3
        SIGN_NOT_200 = 4
        EMPTY_COOKIES = 5
        PREMIUM_ENDPOINT = 6
        AUTHENTICATED_WS = 7

    def __init__(
            self,
            reason: ErrorReason,
            *args: str
    ):
        """
        Initialize a sign API Error class

        :param reason: The reason for the error
        :param args: Additional error arguments passed to the super-class

        """

        self.reason = reason
        args = list(args)
        args.insert(0, f"[{reason.name}]")
        super().__init__(" ".join(args))

    @classmethod
    def format_sign_server_message(cls, message: str) -> str:
        """
        Format the sign server message
        """

        message = message.strip()
        msg_len: int = len(message)
        header_text: str = "SIGN SERVER MESSAGE"
        header_len: int = (msg_len - len(header_text)) // 2
        padding_len: int = int(bool((msg_len - len(header_text)) % 2))

        # Center header text in header
        footer: str = "+" + "-" * (msg_len + 2) + "+"
        header: str = "+" + "-" * header_len + " " + header_text + " " + "-" * (header_len + padding_len) + "+"
        message: str = "| " + message + " |"

        return f"\n\t|\n\t{header}\n\t{message}\n\t{footer}"


class SignatureRateLimitError(SignAPIError):
    """
    Thrown when a user hits the Sign API limit

    """

    def __init__(self, retry_after: int, reset_time: int, api_message: Optional[str], *args):
        """
        Constructor for signature rate limit

        :param retry_after: How long to wait until the next attempt
        :param reset_time: The unix timestamp for when the client can request again
        :param api_message: The message provided by the API
        :param args: Default RuntimeException *args
        :param kwargs: Default RuntimeException **kwargs

        """

        # Message provided by the API
        euler_msg: Optional[str] = self.format_sign_server_message(api_message) if api_message else None

        self._retry_after: int = retry_after
        self._reset_time: int = reset_time

        _args = list(args)

        if euler_msg:
            _args.append(euler_msg)

        _args[0] = str(args[0]) % self.retry_after

        super().__init__(SignAPIError.ErrorReason.RATE_LIMIT, *_args)

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


class UnexpectedSignatureError(SignAPIError):

    def __init__(self, *args):
        super().__init__(SignAPIError.ErrorReason.SIGN_NOT_200, *args)


class SignatureMissingTokensError(SignAPIError):

    def __init__(self, *args):
        super().__init__(SignAPIError.ErrorReason.EMPTY_PAYLOAD, *args)


class PremiumEndpointError(SignAPIError):

    def __init__(self, *args, api_message: str):
        _args = list(args)
        _args.append(self.format_sign_server_message(api_message))

        super().__init__(SignAPIError.ErrorReason.PREMIUM_ENDPOINT, *_args)


class AuthenticatedWebSocketConnectionError(SignAPIError):
    """
    Thrown when sending the session ID to the sign server as this is deemed a risky operation that could lead to an account being banned.

    """

    def __init__(self, *args):
        super().__init__(SignAPIError.ErrorReason.AUTHENTICATED_WS, *args)
