"""The package as Dify will load it: schema, registration, copy rules."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

EXPECTED_TOOLS = {
    "hermoso_credits", "list_channels", "find_competitors", "pull_competitor_ads", "research_ads",
    "generate_image", "generate_video", "get_job", "list_library", "schedule_post",
    "list_scheduled_posts", "cancel_scheduled_post",
}


def test_sdk_registers_every_tool_with_one_class(registration):
    provider_cfg, provider_cls, tools = registration.tools_mapping["hermoso"]
    assert provider_cls.__name__ == "HermosoProvider"
    assert set(tools) == EXPECTED_TOOLS
    assert "hermoso_api_key" in {c.name for c in provider_cfg.credentials_schema}


def test_every_tool_has_human_and_llm_copy_and_labels(registration):
    _, _, tools = registration.tools_mapping["hermoso"]
    for name, (cfg, _cls) in tools.items():
        assert cfg.identity.label.en_us, name
        assert cfg.description.human.en_us and len(cfg.description.llm) > 60, name
        for p in cfg.parameters:
            assert p.label.en_us, f"{name}.{p.name}"
            assert p.llm_description, f"{name}.{p.name}"
            assert p.human_description and p.human_description.en_us, f"{name}.{p.name}"


def test_long_running_tools_say_so(registration):
    _, _, tools = registration.tools_mapping["hermoso"]
    gv = tools["generate_video"][0].description
    assert "job_id" in gv.llm and "get_job" in gv.llm
    assert "job id" in gv.human.en_us.lower()


def test_tools_that_spend_credits_say_so(registration):
    _, _, tools = registration.tools_mapping["hermoso"]
    for name in ("find_competitors", "pull_competitor_ads", "research_ads", "generate_image", "generate_video"):
        assert "credits" in tools[name][0].description.human.en_us.lower(), name
        assert "credits" in tools[name][0].description.llm.lower(), name


def test_manifest_fields_the_marketplace_requires():
    m = yaml.safe_load((ROOT / "manifest.yaml").read_text(encoding="utf-8"))
    assert m["author"] == "hermoso-ai" and "dify" not in m["author"] and "langgenius" not in m["author"]
    assert m["repo"].startswith("https://github.com/")
    assert re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", m["contact"])
    assert m["privacy"] == "PRIVACY.md" and (ROOT / "PRIVACY.md").is_file()
    assert m["network"]["domains"] == ["app.hermoso.ai"]
    assert m["meta"]["runner"] == {"language": "python", "version": "3.12", "entrypoint": "main"}
    assert (ROOT / "_assets" / m["icon"]).is_file()


SHIPPED = [p for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".py", ".yaml", ".md", ".txt", ".svg"}
           and not any(part in {"tests", "scripts", ".git", "__pycache__", ".pytest_cache"} for part in p.parts)
           and p.name != "HANDOFF.md"]


def test_no_secret_no_em_dash_no_amounts_in_shipped_files():
    assert SHIPPED
    for path in SHIPPED:
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"hmk_[A-Za-z0-9]{16,}", text), f"possible API key in {path}"
        assert chr(0x2014) not in text and chr(0x2013) not in text, f"em or en dash in {path}"
        assert not re.search(r"\b\d+\s*(?:credits?|cr)\b", text, re.I), f"credit figure in {path}"
        assert not re.search(r"[$€£]\s?\d", text), f"price in {path}"
