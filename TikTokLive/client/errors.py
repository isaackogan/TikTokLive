import enum
from functools import cached_property
from typing import Optional

import httpx

from TikTokLive.__version__ import PACKAGE_VERSION


class TikTokLiveError(RuntimeError):
    """
    Base error class for TikTokLive errors

    """

    def __init__(self, *args):
        args = list(args)
        args.insert(0, f"TikTokLive v{PACKAGE_VERSION} ->")

        # If it was empty
        if len(args) == 1:
            args.append("No Message Provided")

        super().__init__(" ".join(args))


class AlreadyConnectedError(TikTokLiveError):
    """
    Thrown when attempting to connect to a user that is already connected to

    """


class UserOfflineError(TikTokLiveError):
    """
    Thrown when the requested streamer to watch is offline

    """


class UserNotFoundError(TikTokLiveError):
    """
    Thrown when the request to check if a user is live fails because a user has no
    livestream account (e.g. <1000 followers)

    """

    def __init__(self, unique_id: str, *args):
        self.unique_id: str = unique_id
        super().__init__(*args)


class AgeRestrictedError(TikTokLiveError):
    """
    Thrown when a LIVE is age restricted. Pass sessionid to bypass.
    """


class InitialCursorMissingError(TikTokLiveError):
    """
    Thrown when the cursor for connecting to TikTok is missing (blocked)

    """


class WebsocketURLMissingError(TikTokLiveError):
    """
    Thrown when the websocket URL to connect to TikTok is missing (blocked)

    """


class WebcastBlocked200Error(TikTokLiveError):
    """
    Thrown when the webcast is blocked by TikTok with a 200 status code (detected)

    """


class SignAPIError(TikTokLiveError):
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
            *args: str,
            response: Optional[httpx.Response] = None,
    ):
        """
        Initialize a sign API Error class

        :param reason: The reason for the error
        :param args: Additional error arguments passed to the super-class

        """

        self._response = response
        self.reason = reason
        args = list(args)
        args.insert(0, f"[{reason.name}]")
        super().__init__(" ".join(args))

    @property
    def response(self) -> httpx.Response | None:
        """
        The response object from the Sign API

        """

        return self._response

    @cached_property
    def log_id(self) -> int | None:
        """
        The log ID from the response

        """

        if not self.response:
            return None

        log_id: Optional[str] = self.response.headers.get("X-Log-ID", None)
        return int(log_id) if log_id else log_id

    @cached_property
    def agent_id(self) -> str | None:
        """
        The agent ID from the response

        """

        if not self.response:
            return None

        return self.response.headers.get("X-Agent-ID", None)

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

    def __init__(self, api_message: Optional[str], *args, response: httpx.Response):
        """
        Constructor for signature rate limit
        :param api_message: The message provided by the API
        :param args: Default RuntimeException *args
        :param kwargs: Default RuntimeException **kwargs

        """

        # Message provided by the API
        euler_msg: Optional[str] = self.format_sign_server_message(api_message) if api_message else None
        _args = list(args)

        if euler_msg:
            _args.append(euler_msg)

        _args[0] = str(args[0]) % self.calculate_retry_after(response=response)
        super().__init__(SignAPIError.ErrorReason.RATE_LIMIT, *_args, response=response)

    @classmethod
    def calculate_retry_after(cls, response: httpx.Response) -> int:
        """
        Calculate the retry after time from the response headers

        :param response: The response object
        :return: The retry after time in seconds

        """

        return int(response.headers.get("RateLimit-Remaining"))

    @cached_property
    def retry_after(self) -> int:
        """
        How long to wait until the next attempt

        """

        return self.calculate_retry_after(response=self.response)

    @cached_property
    def reset_time(self) -> int:
        """
        The unix timestamp for when the client can request again

        """

        return self.response.headers.get("RateLimit-Reset")


class UnexpectedSignatureError(SignAPIError):

    def __init__(self, *args, **kwargs):
        super().__init__(SignAPIError.ErrorReason.SIGN_NOT_200, *args, **kwargs)


class SignatureMissingTokensError(SignAPIError):

    def __init__(self, *args, **kwargs):
        super().__init__(SignAPIError.ErrorReason.EMPTY_PAYLOAD, *args, **kwargs)


class PremiumEndpointError(SignAPIError):

    def __init__(self, *args, api_message: str, **kwargs):
        _args = list(args)
        _args.append(self.format_sign_server_message(api_message))

        super().__init__(SignAPIError.ErrorReason.PREMIUM_ENDPOINT, *_args, **kwargs)


class AuthenticatedWebSocketConnectionError(SignAPIError):
    """
    Thrown when sending the session ID to the sign server as this is deemed a risky operation that could lead to an account being banned.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(SignAPIError.ErrorReason.AUTHENTICATED_WS, *args, **kwargs)


if __name__ == '__main__':
    """Error testing"""
    raise AlreadyConnectedError("User is already connected")
