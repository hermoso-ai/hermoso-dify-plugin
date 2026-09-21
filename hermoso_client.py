"""Thin HTTP client for the Hermoso REST API (https://app.hermoso.ai/v1).

Every request goes to one fixed HTTPS host, carries an explicit timeout, and
never puts the API key in an error message or a log line.
"""

from __future__ import annotations

from typing import Any

import requests

BASE_URL = "https://app.hermoso.ai/v1"
USER_AGENT = "hermoso-dify-plugin/0.0.1"

# Reads answer in a second or two. Tool calls that run a model can take far
# longer, so they get most of the plugin's 120 second request budget.
READ_TIMEOUT = 30
RUN_TIMEOUT = 110


class HermosoError(Exception):
    """A refusal or failure from the Hermoso API, safe to show to a user."""

    def __init__(self, message: str, status: int = 0, code: str = "", request_id: str = ""):
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code
        self.request_id = request_id

    def __str__(self) -> str:
        tail = f" (request {self.request_id})" if self.request_id else ""
        return f"{self.message}{tail}"


class HermosoClient:
    def __init__(self, api_key: str, base_url: str = BASE_URL, session: requests.Session | None = None):
        key = (api_key or "").strip()
        if not key:
            raise HermosoError(
                "No Hermoso API key is configured. Create one in the Hermoso app under "
                "MCP & CLI, then add it to this plugin's authorization.",
                status=401,
                code="missing_api_key",
            )
        self._key = key
        self._base = base_url.rstrip("/")
        self._http = session or requests.Session()

    @classmethod
    def from_credentials(cls, credentials: dict[str, Any]) -> "HermosoClient":
        return cls(str((credentials or {}).get("hermoso_api_key") or ""))

    # -- transport -----------------------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        timeout: int = READ_TIMEOUT,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._key}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        try:
            resp = self._http.request(
                method,
                f"{self._base}{path}",
                params={k: v for k, v in (params or {}).items() if v not in (None, "")},
                json=json_body,
                headers=headers,
                timeout=timeout,
            )
        except requests.Timeout as err:
            raise HermosoError(
                "Hermoso did not answer in time. If this call started a render or a post, it may "
                "still have gone through: check with get_job or list_scheduled_posts before retrying.",
                status=504,
                code="timeout",
            ) from err
        except requests.RequestException as err:
            # Never str(err): a transport error can echo request headers.
            raise HermosoError(
                f"Could not reach Hermoso ({type(err).__name__}). Check the network connection and retry.",
                status=503,
                code="network_error",
            ) from None

        try:
            body = resp.json()
        except ValueError:
            body = None

        if resp.status_code >= 400 or not isinstance(body, dict):
            err = (body or {}).get("error") if isinstance(body, dict) else None
            if isinstance(err, dict):
                message = str(err.get("message") or "Request failed")
                code = str(err.get("code") or "")
            else:
                message = f"Hermoso answered HTTP {resp.status_code}."
                code = ""
            if resp.status_code == 401:
                message = (
                    "Hermoso rejected the API key. Create a key in the Hermoso app under "
                    "MCP & CLI and update this plugin's authorization."
                )
            request_id = str((body or {}).get("request_id") or "") if isinstance(body, dict) else ""
            raise HermosoError(message, status=resp.status_code, code=code, request_id=request_id)
        return body

    # -- stable /v1 resources --------------------------------------------------------------------

    def credits(self) -> dict[str, Any]:
        return self.request("GET", "/credits")

    def channels(self) -> dict[str, Any]:
        return self.request("GET", "/channels")

    def list_posts(self, **params: Any) -> dict[str, Any]:
        return self.request("GET", "/posts", params=params)

    def create_post(self, body: dict[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/posts", json_body=body, timeout=RUN_TIMEOUT)

    def cancel_post(self, post_id: str) -> dict[str, Any]:
        return self.request("DELETE", f"/posts/{requests.utils.quote(post_id, safe='')}")

    # -- the tool passthrough --------------------------------------------------------------------

    def call_tool(self, name: str, args: dict[str, Any] | None = None, timeout: int = RUN_TIMEOUT) -> dict[str, Any]:
        """POST /v1/tools/{name}. Answers {object:'tool_result', tool, text, data}."""
        clean = {k: v for k, v in (args or {}).items() if v is not None and v != ""}
        return self.request("POST", f"/tools/{name}", json_body=clean, timeout=timeout)


def split_list(value: Any) -> list[str]:
    """'a, b\\nc' -> ['a', 'b', 'c']. Accepts a real list too."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        items = [str(v) for v in value]
    else:
        items = str(value).replace("\n", ",").split(",")
    return [i.strip() for i in items if i and i.strip()]


def as_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        n = int(float(value))
    except (TypeError, ValueError):
        n = default
    return max(low, min(high, n))


def as_bool(value: Any, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "on")


# -- shaping results -------------------------------------------------------------------------------


def tool_output(result: dict[str, Any]) -> dict[str, Any]:
    """{text, data} from a /v1/tools result. `data` is the tool's structured result, or {}."""
    data = result.get("data")
    return {"text": str(result.get("text") or ""), "data": data if isinstance(data, dict) else {}}


def media_url(result: dict[str, Any], keys: tuple[str, ...] = ("url", "video", "image")) -> str:
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value.startswith("http"):
            return value
    return ""


_STILL_RENDERING = (
    "Still rendering. Call get_job with job_id {job_id} until status is done or error. Renders take "
    "1 to 3 minutes. Do not call generate_video again for this request: that would spend credits twice."
)


def job_output(result: dict[str, Any], job_id: str = "") -> dict[str, Any]:
    """One shape for generate_video and get_job: {status, job_id, video_url, ...}.

    generate_video answers {jobId, url, stillRendering}; get_job answers {id, status, progress, url,
    error}. Both are folded into the same fields so a workflow can branch on `status` alone.
    """
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    jid = str(data.get("jobId") or data.get("id") or job_id or "")
    url = media_url(result)
    status = str(data.get("status") or "").lower()
    if not status:
        status = "done" if url else ("rendering" if data.get("stillRendering") or jid else "unknown")
    if status in ("queued", "running"):
        status = "rendering" if not url else "done"
    out: dict[str, Any] = {
        "status": status,  # rendering | done | error | not_found | unknown
        "job_id": jid,
        "video_url": url,
        "poster_url": data.get("poster") if isinstance(data.get("poster"), str) else "",
        "model": data.get("model") if isinstance(data.get("model"), str) else "",
        "credits_used": data.get("creditsUsed"),
        "progress": data.get("progress"),
        "error": data.get("error") if isinstance(data.get("error"), str) else "",
    }
    if status == "done":
        out["message"] = f"Render ready: {url}" if url else (str(result.get("text") or "") or "Render finished.")
    elif status == "rendering":
        out["message"] = _STILL_RENDERING.format(job_id=jid)
    elif status == "not_found":
        out["message"] = (
            f"No job with id {jid} on this workspace. Stop polling it, and do not start the render again "
            "on the strength of this."
        )
    elif status == "error":
        out["message"] = f"Render failed: {out['error'] or str(result.get('text') or '')}"
    else:
        out["message"] = str(result.get("text") or "")
    return out


def post_summary(post: dict[str, Any]) -> dict[str, Any]:
    media = [m.get("url") for m in (post.get("media") or []) if isinstance(m, dict) and m.get("url")]
    results = [
        {"channel": r.get("channel"), "ok": r.get("ok"), "url": r.get("url"), "error": r.get("error")}
        for r in (post.get("results") or [])
        if isinstance(r, dict)
    ]
    return {
        "id": str(post.get("id") or ""),
        "status": str(post.get("status") or ""),
        "scheduled_at": str(post.get("scheduled_at") or ""),
        "channels": [str(c) for c in (post.get("channels") or [])],
        "caption": str(post.get("caption") or ""),
        "title": str(post.get("title") or ""),
        "link": str(post.get("link") or ""),
        "media": media,
        "visibility": str(post.get("visibility") or ""),
        "results": results,
        "status_detail": post.get("status_detail"),
    }
