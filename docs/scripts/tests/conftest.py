"""Make ``gen_api`` and ``verify_seo`` importable and load the packages once per session."""

import sys
from pathlib import Path

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_TESTS_DIR.parents[0]))  # docs/scripts
sys.path.insert(0, str(_TESTS_DIR.parents[2] / "scripts" / "seo"))  # scripts/seo

import gen_api  # noqa: E402


@pytest.fixture(scope="session")
def tiktoklive_module():
    return gen_api.load_module("TikTokLive")


@pytest.fixture(scope="session")
def proto_module():
    return gen_api.load_module("TikTokLiveProto")
