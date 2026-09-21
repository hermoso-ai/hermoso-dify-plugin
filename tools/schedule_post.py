from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hermoso_client import HermosoClient, HermosoError, as_bool, post_summary, split_list


class SchedulePostTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        channels = [c.lower() for c in split_list(tool_parameters.get("channels"))]
        if not channels:
            raise HermosoError("channels is required, for example: instagram, tiktok. See list_channels.", status=400)
        scheduled_at = str(tool_parameters.get("scheduled_at") or "").strip()
        use_queue = as_bool(tool_parameters.get("use_queue"), False)
        # The REST API publishes immediately when neither is given. This tool is for scheduling,
        # so that case is refused here instead of going live by omission.
        if bool(scheduled_at) == use_queue:
            raise HermosoError(
                "Give exactly one of scheduled_at (an ISO 8601 time in the future) or use_queue=true. "
                "This tool never publishes immediately.",
                status=400,
            )
        media = split_list(tool_parameters.get("media_urls"))
        bad = [u for u in media if not u.lower().startswith("https://")]
        if bad:
            raise HermosoError(f"media_urls must be https URLs. Not accepted: {bad[0]}", status=400)
        body: dict[str, Any] = {"channels": channels, "caption": str(tool_parameters.get("caption") or "")}
        if media:
            body["media"] = media
        if use_queue:
            body["use_queue"] = True
            if str(tool_parameters.get("timezone") or "").strip():
                body["timezone"] = str(tool_parameters["timezone"]).strip()
        else:
            body["scheduled_at"] = scheduled_at
        for key in ("title", "link"):
            if str(tool_parameters.get(key) or "").strip():
                body[key] = str(tool_parameters[key]).strip()
        visibility = str(tool_parameters.get("visibility") or "").strip()
        if visibility and visibility != "public":
            body["visibility"] = visibility
        post = HermosoClient.from_credentials(self.runtime.credentials).create_post(body)
        out = post_summary(post)
        yield self.create_json_message(out)
        yield self.create_text_message(
            f"Scheduled post {out['id']} to {', '.join(out['channels'])} for {out['scheduled_at']} "
            f"(status: {out['status']})."
        )
