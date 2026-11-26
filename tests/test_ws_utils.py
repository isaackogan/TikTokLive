from urllib.parse import parse_qs, urlsplit

from IgniteLiveAPI.client.ws.ws_utils import build_webcast_uri
from IgniteLiveAPI.proto import ProtoMessageFetchResult

# The Euler Stream fallback push server echoes the user agent back as a route
# param. It contains spaces and parentheses, which are illegal in an HTTP
# request-target unless percent-encoded.
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_7_5) AppleWebKit/605.1.15 (KHTML, like Gecko)"


def _fetch_result(**route_params: str) -> ProtoMessageFetchResult:
    return ProtoMessageFetchResult(
        cursor="0",
        push_server="wss://ws-fallback.eulerstream.com/",
        route_params=route_params,
    )


def test_route_param_values_are_percent_encoded() -> None:
    uri = build_webcast_uri(
        initial_webcast_response=_fetch_result(token="abc.def", user_agent=USER_AGENT),
        base_uri_params={"room_id": 1},
        base_uri_append_str="",
    )

    query = urlsplit(uri).query
    assert " " not in query and "(" not in query
    assert parse_qs(query)["user_agent"] == [USER_AGENT]
    assert parse_qs(query)["token"] == ["abc.def"]


def test_pre_encoded_base_params_are_not_double_encoded() -> None:
    # Device presets ship ``browser_version`` already percent-encoded, so the
    # builder must leave base params alone and only encode route params.
    uri = build_webcast_uri(
        initial_webcast_response=_fetch_result(token="abc"),
        base_uri_params={"browser_version": "5.0%20%28Macintosh%29"},
        base_uri_append_str="&version_code=270000",
    )

    assert "browser_version=5.0%20%28Macintosh%29" in uri
    assert uri.endswith("&version_code=270000")
