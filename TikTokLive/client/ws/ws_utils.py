import base64
import logging
import os
from gzip import GzipFile
from http.cookies import SimpleCookie
from io import BytesIO

from TikTokLive.client.errors import InitialCursorMissingError, WebsocketURLMissingError
from TikTokLive.client.logger import TikTokLiveLogHandler
from TikTokLive.proto import ProtoMessageFetchResult
from TikTokLive.proto.custom_extras import WebcastPushFrame


def build_webcast_uri(
        initial_webcast_response: ProtoMessageFetchResult,
        base_uri_params: dict,
        base_uri_append_str: str
) -> str:
    """
    Build a webcast URI from a base URI and parameters. This method will format the base URI
    with the parameters and return the formatted URI.

    :param initial_webcast_response: The initial Webcast response
    :param base_uri_params: Parameters to format the URI with
    :param base_uri_append_str: String to append to the base URI
    :return: str The formatted URI

    """

    if not initial_webcast_response.cursor:
        raise InitialCursorMissingError("Missing cursor in initial fetch response.")

    if not initial_webcast_response.push_server:
        raise WebsocketURLMissingError("No websocket URL received from TikTok.")

    if not initial_webcast_response.route_params:
        raise WebsocketURLMissingError("Websocket parameters missing.")

    # Build the URI parameters dict
    uri_params: dict = {
        **initial_webcast_response.route_params,
        **base_uri_params,
        "internal_ext": initial_webcast_response.internal_ext,
        "cursor": initial_webcast_response.cursor,
    }

    # Build the URI
    connect_uri: str = (
            initial_webcast_response.push_server
            + "?"
            + '&'.join(f"{key}={value}" for key, value in uri_params.items())
            + base_uri_append_str
    )

    return connect_uri


def extract_webcast_push_frame(data: bytes, logger: logging.Logger = TikTokLiveLogHandler.get_logger()) -> WebcastPushFrame:
    """
    Extract a WebcastPushFrame from a raw byte payload. This method will parse the payload
    and return a WebcastPushFrame object. This method is useful for extracting push frames
    from a WebSocket connection.

    :param data: Raw byte payload to extract from
    :param logger: Logger to use for logging
    :return: WebcastPushFrame The extracted push frame

    """

    # Parse the push frame from the raw byte payload
    return WebcastPushFrame().parse(data)


def extract_webcast_response_message(push_frame: WebcastPushFrame, logger: logging.Logger = TikTokLiveLogHandler.get_logger()) -> ProtoMessageFetchResult:
    """
    Extract the ProtoMessageFetchResult from a push frame. If compression is enabled on the WebSocket,
    then messages will come gzipped. This method will decompress the payload if necessary.
    The gzip format allows for less bandwidth usage, at the cost of a slight CPU increase for message decompression.

    :param push_frame: Push frame to extract from
    :param logger: Logger to use for logging
    :return: ProtoMessageFetchResult The extracted response

    """

    # If there is no compression header, return the payload parsed as-is
    if not push_frame.headers or 'compress_type' not in push_frame.headers or push_frame.headers['compress_type'] == 'none':
        return ProtoMessageFetchResult().parse(push_frame.payload)

    # If there is a compression type, but it's NOT gzip (should never happen, if it does, represents a TikTok update)
    if push_frame.headers.get('compress_type', None) != 'gzip':
        logger.error(f"Unknown compression type: {push_frame.headers.get('compress_type', None)}")
        return ProtoMessageFetchResult().parse(push_frame.payload)  # Just pray it works

    # If the compress type is gzip, we need to decompress the payload
    gzip_file = GzipFile(fileobj=BytesIO(push_frame.payload))

    # Decompress it
    try:
        decompressed_bytes = gzip_file.read()
    finally:
        gzip_file.close()

    # Parse the response from the decompressed data
    return ProtoMessageFetchResult().parse(decompressed_bytes)


def extract_websocket_options(headers: dict) -> dict[str, str]:
    """
    Options are a cookie-style string, so we parse with SimpleCookie from the stdlib

    """

    options = SimpleCookie()
    options.load(headers.get('Handshake-Options', ''))

    return {key: value.value for key, value in options.items()}
