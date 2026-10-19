import gen_api


def test_reexported_modules_lists_star_imports():
    mods = gen_api.reexported_modules()
    assert "TikTokLiveProto.v3.webcast.model.message" in mods
    assert "TikTokLiveProto.v3.webcast.model.gift.model" not in mods


def test_slugs():
    assert gen_api.api_slug("TikTokLive.client.client.TikTokLiveClient") == "tiktoklive/client/client/tiktokliveclient"
    assert gen_api.schema_slug("TikTokLiveProto.v3.webcast.model.message.WebcastChatMessage") == "webcast/model/message/webcastchatmessage"


def test_client_page_has_signature_and_params(tiktoklive_module):
    client = tiktoklive_module["client"]["client"]["TikTokLiveClient"]
    md = gen_api.page_for(client, import_path="TikTokLive", source_url=None)
    assert md.startswith("---\ntitle: TikTokLiveClient\n")
    assert "unique_id" in md and "## Parameters" in md and "## Methods" in md and "is_live" in md


def test_page_for_object_without_docstring(tiktoklive_module):
    obj = tiktoklive_module["client"]["web"]["routes"]  # package with no docstring
    md = gen_api.page_for(obj, import_path="TikTokLive.client.web.routes", source_url=None)
    assert "title: routes" in md


def test_schema_covers_non_reexported_message(tmp_path, proto_module):
    paths = gen_api.render_schema(proto_module, gen_api.reexported_modules(), tmp_path)
    page = tmp_path / "webcast/model/gift/model/webcastgoalupdatemessage.md"
    assert page.exists()
    assert "from TikTokLiveProto.v3.webcast.model.gift.model import WebcastGoalUpdateMessage" in page.read_text()
    chat = (tmp_path / "webcast/model/message/webcastchatmessage.md").read_text()
    assert "from TikTokLive.proto import WebcastChatMessage" in chat
    assert len(paths) > 300


def test_render_api_excludes_private_and_proto(tmp_path, tiktoklive_module):
    paths = gen_api.render_api(tiktoklive_module, tmp_path)
    names = {p.relative_to(tmp_path).as_posix() for p in paths}
    assert "tiktoklive/client/client/tiktokliveclient.md" in names
    assert "tiktoklive/proto/custom_proto/extendedgift.md" in names
    assert not any(n.startswith("tiktoklive/proto/") and not n.startswith("tiktoklive/proto/custom_proto/") for n in names)
    assert not any("/_" in n for n in names)
