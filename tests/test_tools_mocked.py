"""Every tool, with HTTP mocked. These cover the calls that spend credits or write to real accounts,
which are never exercised against the live API."""

from __future__ import annotations

import pytest
import requests
from conftest import FAKE_KEY, tool_result

from hermoso_client import HermosoClient, HermosoError


def test_bearer_header_and_json_body(api, run):
    api.on("POST", "/tools/find_competitors", tool_result("find_competitors", "3 brands", {"candidates": [{"name": "A"}]}))
    payload, text = run("find_competitors", {"domain": "allbirds.com"})
    assert api.last["headers"]["Authorization"] == f"Bearer {FAKE_KEY}"
    assert api.last["json"] == {"domain": "allbirds.com", "mode": "competitors"}
    assert payload["data"]["candidates"][0]["name"] == "A" and text == "3 brands"


def test_pull_competitor_ads_maps_params_and_clamps_limit(api, run):
    api.on("POST", "/tools/pull_competitor_ads", tool_result("pull_competitor_ads", "12 ads", {"ads": []}))
    run("pull_competitor_ads", {"company_name": "Allbirds", "domain": "allbirds.com", "country": "gb", "limit": 500})
    assert api.last["json"] == {"companyName": "Allbirds", "domain": "allbirds.com", "country": "GB", "limit": 30, "sort": "longest_running"}


def test_pull_competitor_ads_needs_a_brand(api, run):
    with pytest.raises(HermosoError, match="company_name, domain"):
        run("pull_competitor_ads", {})
    assert api.calls == []


def test_research_ads_omits_empty_brand(api, run):
    api.on("POST", "/tools/research_ads", tool_result("research_ads", "Summary...", {"results": []}))
    run("research_ads", {"query": "protein bar hooks", "brand": ""})
    assert api.last["json"] == {"query": "protein bar hooks"}
    assert api.last["timeout"] >= 100


def test_generate_image_returns_url_and_sends_refs(api, run):
    api.on("POST", "/tools/generate_image", tool_result("generate_image", "Image ready", {"image": "https://assets.hermoso.ai/a/i.jpg", "model": "X"}))
    payload, text = run("generate_image", {"prompt": "a shoe", "aspect_ratio": "4:5", "reference_images": "https://x.com/a.png, https://x.com/b.png", "use_brand": False})
    assert api.last["json"] == {"prompt": "a shoe", "aspectRatio": "4:5", "useBrand": False, "refImages": ["https://x.com/a.png", "https://x.com/b.png"]}
    assert payload["image_url"] == "https://assets.hermoso.ai/a/i.jpg" and "Image ready:" in text


def test_generate_image_refuses_non_https_reference(api, run):
    with pytest.raises(HermosoError, match="https"):
        run("generate_image", {"prompt": "x", "reference_images": "file:///etc/passwd"})
    assert api.calls == []


def test_generate_video_still_rendering_returns_job_id(api, run):
    api.on("POST", "/tools/generate_video", tool_result("generate_video", "Still rendering", {"jobId": "job_abc", "url": None, "stillRendering": True, "raw": None}))
    payload, text = run("generate_video", {"prompt": "a shoe on a ridge", "duration_seconds": 8})
    assert api.last["json"] == {"prompt": "a shoe on a ridge", "aspectRatio": "9:16", "durationSeconds": 8.0}
    assert payload["status"] == "rendering" and payload["job_id"] == "job_abc" and payload["video_url"] == ""
    assert "get_job" in text and "job_abc" in text


def test_generate_video_finished_inline(api, run):
    api.on("POST", "/tools/generate_video", tool_result("generate_video", "Video ready", {"jobId": "job_abc", "url": "https://assets.hermoso.ai/a/v.mp4", "model": "M", "creditsUsed": 1}))
    payload, _ = run("generate_video", {"prompt": "x", "audio": False})
    assert api.last["json"]["audio"] is False
    assert payload["status"] == "done" and payload["video_url"].endswith("v.mp4")


@pytest.mark.parametrize(
    ("data", "status"),
    [
        ({"id": "job_1", "status": "running", "progress": 0.4}, "rendering"),
        ({"id": "job_1", "status": "queued"}, "rendering"),
        ({"id": "job_1", "status": "done", "url": "https://assets.hermoso.ai/a/v.mp4"}, "done"),
        ({"id": "job_1", "status": "error", "error": "model refused"}, "error"),
        ({"id": "job_1", "status": "not_found"}, "not_found"),
    ],
)
def test_get_job_statuses(api, run, data, status):
    api.on("POST", "/tools/get_job", tool_result("get_job", "Job job_1", data))
    payload, text = run("get_job", {"job_id": "job_1"})
    assert api.last["json"] == {"id": "job_1"}
    assert payload["status"] == status and payload["job_id"] == "job_1"
    if status == "not_found":
        assert "Stop polling" in text
    if status == "error":
        assert "model refused" in text


def test_schedule_post_builds_v1_body(api, run):
    api.on("POST", "/posts", {"object": "post", "id": "sch_1", "status": "scheduled", "scheduled_at": "2030-01-15T09:00:00.000Z", "channels": ["instagram", "linkedin"], "caption": "Hi", "media": [{"type": "image", "url": "https://assets.hermoso.ai/a/i.jpg"}], "results": []})
    payload, text = run("schedule_post", {"channels": "Instagram, linkedin", "caption": "Hi", "media_urls": "https://assets.hermoso.ai/a/i.jpg", "scheduled_at": "2030-01-15T09:00:00Z", "visibility": "public"})
    assert api.last["method"] == "POST" and api.last["path"] == "/posts"
    assert api.last["json"] == {"channels": ["instagram", "linkedin"], "caption": "Hi", "media": ["https://assets.hermoso.ai/a/i.jpg"], "scheduled_at": "2030-01-15T09:00:00Z"}
    assert payload["id"] == "sch_1" and payload["media"] == ["https://assets.hermoso.ai/a/i.jpg"] and "sch_1" in text


def test_schedule_post_queue_mode(api, run):
    api.on("POST", "/posts", {"object": "post", "id": "sch_2", "status": "scheduled", "channels": ["x"]})
    run("schedule_post", {"channels": "x", "caption": "Hi", "use_queue": True, "timezone": "America/New_York"})
    assert api.last["json"] == {"channels": ["x"], "caption": "Hi", "use_queue": True, "timezone": "America/New_York"}


@pytest.mark.parametrize("params", [
    {"channels": "x", "caption": "Hi"},  # neither: the API would publish NOW
    {"channels": "x", "caption": "Hi", "scheduled_at": "2030-01-15T09:00:00Z", "use_queue": True},
])
def test_schedule_post_never_publishes_immediately(api, run, params):
    with pytest.raises(HermosoError, match="never publishes immediately"):
        run("schedule_post", params)
    assert api.calls == [], "a refused schedule must not reach the API"


def test_schedule_post_surfaces_api_refusal(api, run):
    api.on("POST", "/posts", {"error": {"type": "invalid_request_error", "code": "post_refused", "message": "Instagram needs an image or a video."}, "request_id": "req_9"}, status=400)
    with pytest.raises(HermosoError) as err:
        run("schedule_post", {"channels": "instagram", "caption": "Hi", "scheduled_at": "2030-01-15T09:00:00Z"})
    assert "Instagram needs an image" in str(err.value) and "req_9" in str(err.value)


def test_list_and_cancel_posts(api, run):
    api.on("GET", "/posts", {"object": "list", "data": [{"id": "sch_1", "status": "scheduled", "scheduled_at": "2030-01-15T09:00:00.000Z", "channels": ["x"], "caption": "Hi"}], "has_more": False})
    payload, text = run("list_scheduled_posts", {"status": "scheduled", "limit": 5})
    assert api.last["params"] == {"status": "scheduled", "limit": 5}
    assert payload["posts"][0]["id"] == "sch_1" and "sch_1" in text
    api.on("DELETE", "/posts/sch_1", {"object": "post", "id": "sch_1", "deleted": True})
    payload, _ = run("cancel_scheduled_post", {"post_id": "sch_1"})
    assert api.last["method"] == "DELETE" and payload == {"id": "sch_1", "cancelled": True}


def test_list_channels_drops_account_names(api, run):
    api.on("GET", "/channels", {"object": "list", "data": [
        {"id": "instagram", "name": "Instagram", "available": True, "connected": True, "account": "Jane Person", "caption_max": 2200},
        {"id": "x", "name": "X", "available": True, "connected": False, "account": None},
    ]})
    payload, text = run("list_channels")
    assert "Jane Person" not in str(payload) and "account" not in payload["channels"][0]
    assert "Connected and ready: instagram." in text and "Not connected: x." in text


def test_provider_validation_uses_the_free_read(api, registration):
    api.on("GET", "/credits", {"object": "credits", "balance": 10, "plan": "free"})
    provider = registration.get_tool_provider_cls("hermoso")()
    provider.validate_credentials({"hermoso_api_key": FAKE_KEY})
    assert [(c["method"], c["path"]) for c in api.calls] == [("GET", "/credits")]


def test_provider_validation_rejects_a_bad_key_without_echoing_it(api, registration):
    from dify_plugin.errors.tool import ToolProviderCredentialValidationError

    api.on("GET", "/credits", {"error": {"code": "invalid_api_key", "message": "bad"}, "request_id": "req_1"}, status=401)
    provider = registration.get_tool_provider_cls("hermoso")()
    with pytest.raises(ToolProviderCredentialValidationError) as err:
        provider.validate_credentials({"hermoso_api_key": "hmk_super_secret_value_123456"})
    assert "hmk_super_secret_value_123456" not in str(err.value)
    assert "Settings, Agents & API" in str(err.value)
    with pytest.raises(ToolProviderCredentialValidationError):
        provider.validate_credentials({"hermoso_api_key": ""})


def test_transport_errors_never_leak_the_key(api):
    api.on("GET", "/credits", requests.ConnectionError("boom Authorization: Bearer hmk_super_secret_value_123456"))
    with pytest.raises(HermosoError) as err:
        HermosoClient("hmk_super_secret_value_123456").credits()
    assert "hmk_" not in str(err.value) and err.value.code == "network_error"
    api.on("GET", "/credits", requests.Timeout("slow"))
    with pytest.raises(HermosoError) as err:
        HermosoClient("hmk_x").credits()
    assert err.value.code == "timeout"


def test_non_json_error_body(api):
    api.on("GET", "/credits", ValueError("not json"), status=502)
    with pytest.raises(HermosoError, match="HTTP 502"):
        HermosoClient("hmk_x").credits()
