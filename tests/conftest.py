"""Shared fixtures.

`registration` boots the SDK's own PluginRegistration against this directory, which is exactly what
the Dify runtime does at start-up: it parses manifest.yaml, the provider YAML and every tool YAML
through the SDK's schema, then imports every tool module and demands ONE Tool subclass in each.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# dify_plugin FIRST: it applies gevent's monkey patches on import, exactly as main.py does at runtime.
# Importing requests (and with it ssl) before that patch makes every real HTTPS call recurse forever.
import dify_plugin  # noqa: F401  isort: skip
import pytest
import requests

ROOT = Path(__file__).resolve().parent.parent
FAKE_KEY = "hmk_test_not_a_real_key"


@pytest.fixture(scope="session")
def registration():
    from dify_plugin import DifyPluginEnv
    from dify_plugin.core.plugin_registration import PluginRegistration

    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        return PluginRegistration(DifyPluginEnv())
    finally:
        os.chdir(cwd)


class FakeResponse:
    def __init__(self, status: int, body: Any):
        self.status_code = status
        self._body = body

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class FakeHermoso:
    """Stands in for requests.Session.request. Records every call; answers from a route table."""

    def __init__(self):
        self.calls: list[dict[str, Any]] = []
        self.routes: dict[tuple[str, str], tuple[int, Any]] = {}

    def on(self, method: str, path: str, body: Any, status: int = 200):
        self.routes[(method.upper(), path)] = (status, body)
        return self

    def __call__(self, _session, method, url, **kwargs):
        path = url.replace("https://app.hermoso.ai/v1", "")
        self.calls.append({"method": method.upper(), "path": path, **kwargs})
        assert url.startswith("https://app.hermoso.ai/v1/"), f"unexpected host: {url}"
        assert kwargs.get("timeout"), "every request must carry a timeout"
        status, body = self.routes.get((method.upper(), path), (404, {"error": {"code": "not_mocked", "message": f"no mock for {method} {path}"}}))
        if isinstance(body, Exception) and not isinstance(body, ValueError):
            raise body
        return FakeResponse(status, body)

    @property
    def last(self) -> dict[str, Any]:
        return self.calls[-1]


@pytest.fixture
def api(monkeypatch):
    fake = FakeHermoso()
    def _request(session, method, url, **kwargs):
        return fake(session, method, url, **kwargs)

    monkeypatch.setattr(requests.Session, "request", _request)
    return fake


@pytest.fixture
def run(registration):
    """run('tool_name', {...}, key=...) -> (json_payload, text)"""

    def _run(tool: str, params: dict[str, Any] | None = None, key: str = FAKE_KEY):
        cls = registration.get_tool_cls("hermoso", tool)
        assert cls is not None, f"tool {tool} is not registered"
        messages = list(cls.from_credentials({"hermoso_api_key": key}).invoke(params or {}))
        payload, text = None, ""
        for m in messages:
            kind = getattr(m.type, "value", m.type)
            if kind == "json":
                payload = m.message.json_object
            elif kind == "text":
                text += m.message.text
        return payload, text

    return _run


def tool_result(tool: str, text: str, data: dict | None = None) -> dict:
    return {"object": "tool_result", "tool": tool, "text": text, "data": data}


@pytest.fixture(scope="session")
def live_key() -> str:
    key = os.environ.get("HERMOSO_API_KEY", "").strip()
    if not key:
        pytest.skip("HERMOSO_API_KEY is not set")
    return key


def dumps(o: Any) -> str:
    return json.dumps(o, ensure_ascii=False)
