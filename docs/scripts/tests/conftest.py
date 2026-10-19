"""Make ``gen_api`` importable and load the packages once per session."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gen_api  # noqa: E402


@pytest.fixture(scope="session")
def tiktoklive_module():
    return gen_api.load_module("TikTokLive")


@pytest.fixture(scope="session")
def proto_module():
    return gen_api.load_module("TikTokLiveProto")
