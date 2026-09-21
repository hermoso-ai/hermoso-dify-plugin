"""LIVE, against https://app.hermoso.ai/v1, with a real key from HERMOSO_API_KEY.

Only endpoints that READ and spend nothing are called here: the credit balance is asserted to be
unchanged at the end. Nothing is generated, researched, scheduled, cancelled or published.

find_competitors is NOT here on purpose: it runs an AI model and spends credits (measured: the balance
assertion at the end of this file caught it), so it is covered by the mocked tests only.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def balance_before(live_key):
    from hermoso_client import HermosoClient

    return HermosoClient(live_key).credits()["balance"]


def test_live_provider_validation(registration, live_key, balance_before):
    registration.get_tool_provider_cls("hermoso")().validate_credentials({"hermoso_api_key": live_key})


def test_live_bad_key_is_rejected(registration):
    from dify_plugin.errors.tool import ToolProviderCredentialValidationError

    with pytest.raises(ToolProviderCredentialValidationError, match="rejected the API key"):
        registration.get_tool_provider_cls("hermoso")().validate_credentials({"hermoso_api_key": "hmk_invalid_key_000"})


def test_live_credits(run, live_key, balance_before):
    payload, text = run("hermoso_credits", key=live_key)
    assert isinstance(payload["balance"], (int, float)) and payload["plan"]
    assert "Credit balance" in text


def test_live_list_channels(run, live_key):
    payload, text = run("list_channels", key=live_key)
    ids = {c["id"] for c in payload["channels"]}
    assert {"instagram", "tiktok", "linkedin", "x"} <= ids
    assert all("account" not in c for c in payload["channels"])
    assert text.startswith("Connected and ready:")


def test_live_list_library(run, live_key):
    payload, text = run("list_library", {"kind": "image", "limit": 2}, key=live_key)
    assets = payload["data"].get("assets")
    assert isinstance(assets, list) and len(assets) <= 2
    for a in assets:
        assert a["url"].startswith("https://") and a["kind"] == "image"


def test_live_get_job_unknown_id_is_final(run, live_key):
    payload, text = run("get_job", {"job_id": "job_doesnotexist123"}, key=live_key)
    assert payload["status"] == "not_found" and payload["video_url"] == ""
    assert "Stop polling" in text


def test_live_list_scheduled_posts(run, live_key):
    payload, _ = run("list_scheduled_posts", {"limit": 3}, key=live_key)
    assert isinstance(payload["posts"], list) and len(payload["posts"]) <= 3
    for p in payload["posts"]:
        assert p["id"] and p["status"] and isinstance(p["channels"], list)


def test_live_balance_unchanged(live_key, balance_before):
    from hermoso_client import HermosoClient

    assert HermosoClient(live_key).credits()["balance"] == balance_before, "a read-only test spent credits"
