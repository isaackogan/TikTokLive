import griffe

import gen_api


def test_reexported_modules_lists_star_imports():
    mods = gen_api.reexported_modules()
    assert "TikTokLiveProto.v3.webcast.model.message" in mods
    assert "TikTokLiveProto.v3.webcast.model.gift.model" not in mods


def test_slugs():
    assert gen_api.api_slug("IgniteLiveAPI.client.client.IgniteLiveClient") == "igniteliveapi/client/client/igniteliveclient"
    assert gen_api.schema_slug("TikTokLiveProto.v3.webcast.model.message.WebcastChatMessage") == "webcast/model/message/webcastchatmessage"


def test_client_page_has_signature_and_params(igniteliveapi_module):
    client = igniteliveapi_module["client"]["client"]["IgniteLiveClient"]
    md = gen_api.page_for(client, import_path="IgniteLiveAPI", source_url=None)
    assert md.startswith("---\ntitle: IgniteLiveClient\n")
    assert "unique_id" in md and "## Parameters" in md and "## Methods" in md and "is_live" in md


def test_page_for_object_without_docstring(igniteliveapi_module):
    obj = igniteliveapi_module["client"]["web"]["routes"]  # package with no docstring
    md = gen_api.page_for(obj, import_path="IgniteLiveAPI.client.web.routes", source_url=None)
    assert "title: routes" in md


def test_schema_covers_non_reexported_message(tmp_path, proto_module):
    paths = gen_api.render_schema(proto_module, gen_api.reexported_modules(), tmp_path)
    page = tmp_path / "webcast/model/gift/model/webcastgoalupdatemessage.md"
    assert page.exists()
    assert "from TikTokLiveProto.v3.webcast.model.gift.model import WebcastGoalUpdateMessage" in page.read_text()
    chat = (tmp_path / "webcast/model/message/webcastchatmessage.md").read_text()
    assert "from IgniteLiveAPI.proto import WebcastChatMessage" in chat
    assert len(paths) > 300


def test_render_api_excludes_private_and_proto(tmp_path, igniteliveapi_module):
    paths = gen_api.render_api(igniteliveapi_module, tmp_path)
    names = {p.relative_to(tmp_path).as_posix() for p in paths}
    assert "igniteliveapi/client/client/igniteliveclient.md" in names
    assert "igniteliveapi/proto/custom_proto/extendedgift.md" in names
    assert not any(n.startswith("igniteliveapi/proto/") and not n.startswith("igniteliveapi/proto/custom_proto/") for n in names)
    assert not any("/_" in n for n in names)


def submodules_listed(page):
    """Names in the ``## Submodules`` list of a generated module page."""
    section = page.read_text().split("## Submodules\n\n", 1)[1].split("\n\n", 1)[0]
    return [line.split("`")[1] for line in section.splitlines()]


def test_iter_modules_sorts_submodules_regardless_of_insertion_order():
    pkg = griffe.Module("pkg")
    for name in ("zeta", "alpha", "_private", "mid"):
        pkg.set_member(name, griffe.Module(name))
    pkg["mid"].set_member("b", griffe.Module("b"))
    pkg["mid"].set_member("a", griffe.Module("a"))
    assert [m.name for m in gen_api.iter_modules(pkg)] == ["pkg", "alpha", "mid", "a", "b", "zeta"]


def test_render_api_output_is_ordered_alphabetically(tmp_path, igniteliveapi_module):
    paths = gen_api.render_api(igniteliveapi_module, tmp_path)
    for page in ("igniteliveapi/index.md", "igniteliveapi/client/index.md"):
        listed = submodules_listed(tmp_path / page)
        assert len(listed) > 1 and listed == sorted(listed)
    module_dirs = [p.relative_to(tmp_path).parent.as_posix() for p in paths if p.name == "index.md"]
    assert module_dirs == sorted(module_dirs)
