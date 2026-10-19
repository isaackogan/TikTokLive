from pathlib import Path

import check_content

REPO = Path(__file__).resolve().parents[3]


def test_event_classes_includes_custom_and_proto():
    events = check_content.event_classes(REPO)
    assert events["CommentEvent"] == "WebcastChatMessage"
    assert events["ConnectEvent"] is None
    assert events["GoalUpdateEvent"] == "WebcastGoalUpdateMessage"
    assert len(events) >= 74


def test_client_surface():
    params, members = check_content.client_surface(REPO)
    assert params == ["unique_id", "platform", "web_proxy", "ws_proxy", "web_kwargs", "ws_kwargs", "is_user_id"]
    assert {"run", "start", "connect", "disconnect", "is_live", "room_id", "web"} <= set(members)
    assert not any(m.startswith("_") for m in members)


def test_web_defaults_fields_and_routes_and_env():
    assert "tiktok_sign_api_key" in check_content.web_defaults_fields(REPO)
    assert "fetch_signed_websocket" in check_content.route_modules(REPO)
    assert {"SIGN_API_KEY", "SIGN_API_URL", "SIGN_SERVER_MESSAGE_DISABLED", "SEND_DEPRECATION_WARNINGS", "WHITELIST_AUTHENTICATED_SESSION_ID_HOST"} <= check_content.env_vars(REPO)


def test_check_events_reports_missing_event():
    pages = [check_content.Page(Path("x.md"), "`CommentEvent` is documented.")]
    failures = check_content.check_events(pages, {"CommentEvent": "WebcastChatMessage", "NewShinyEvent": "WebcastNewShinyMessage"})
    assert failures == ["Missing event documentation: NewShinyEvent"]


def test_check_catalog_requires_row_with_proto_name():
    catalog = "| `CommentEvent` | `WebcastChatMessage` | A viewer sent a chat comment |\n"
    assert check_content.check_catalog(catalog, {"CommentEvent": "WebcastChatMessage"}) == []
    assert check_content.check_catalog(catalog, {"CommentEvent": "WebcastOtherMessage"}) == ["Event catalog row is stale: CommentEvent"]


def test_check_discord():
    pages = [check_content.Page(Path("t.md"), "Join https://discord.gg/abc")]
    assert check_content.check_discord(pages) == ["t.md: published pages must not reference Discord"]


def test_check_readme_catalog_detects_drift():
    readme = "<li><code>CommentEvent</code> - A viewer sent a chat comment</li>"
    assert check_content.check_readme_catalog(readme, "| `CommentEvent` | `WebcastChatMessage` | A viewer sent a chat comment |") == []
    assert check_content.check_readme_catalog(readme, "| `CommentEvent` | `WebcastChatMessage` | Something else |") == ["README description differs from catalog: CommentEvent"]


def test_check_readme_catalog_accepts_linked_event_name():
    readme = '<li><a href="https://ttl.docs.isaackogan.com/events/#commentevent"><code>CommentEvent</code></a> - A viewer sent a chat comment</li>'
    assert check_content.check_readme_catalog(readme, "| `CommentEvent` | `WebcastChatMessage` | A viewer sent a chat comment |") == []
    assert check_content.check_readme_catalog(readme, "| `CommentEvent` | `WebcastChatMessage` | Something else |") == ["README description differs from catalog: CommentEvent"]


def test_compile_examples_reports_type_error(tmp_path):
    bad = ("page.md, example 1", "from TikTokLive.events import GiftEvent\n\ndef f(e: GiftEvent) -> str:\n    return e.comment\n")
    good = ("page.md, example 2", "from TikTokLive.events import CommentEvent\n\ndef f(e: CommentEvent) -> str:\n    return e.comment\n")
    failures = check_content.compile_examples([bad, good], REPO)
    assert len(failures) == 1 and failures[0].startswith("page.md, example 1")
