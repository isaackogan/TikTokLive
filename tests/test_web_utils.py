import pytest

from TikTokLive.client.errors import AuthenticatedWebSocketConnectionError
from TikTokLive.client.web.web_settings import WebDefaults
from TikTokLive.client.web.web_utils import check_authenticated_session


def test_anonymous_session_is_allowed_when_not_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WHITELIST_AUTHENTICATED_SESSION_ID_HOST", raising=False)

    assert check_authenticated_session(None, None, session_required=False) is False


def test_missing_session_is_rejected_when_required() -> None:
    with pytest.raises(ValueError, match="Session ID required"):
        check_authenticated_session(None, None, session_required=True)


def test_authenticated_session_requires_an_explicitly_authorized_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("WHITELIST_AUTHENTICATED_SESSION_ID_HOST", raising=False)

    with pytest.raises(AuthenticatedWebSocketConnectionError, match="BLOCKED"):
        check_authenticated_session("session-id", "useast1a", session_required=False)


def test_authenticated_session_accepts_the_configured_signing_host(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = WebDefaults.tiktok_sign_url.split("://", maxsplit=1)[1]
    monkeypatch.setenv("WHITELIST_AUTHENTICATED_SESSION_ID_HOST", host)

    assert check_authenticated_session("session-id", "useast1a", session_required=False) is True
