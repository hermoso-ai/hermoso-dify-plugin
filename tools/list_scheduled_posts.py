from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hermoso_client import HermosoClient, as_int, post_summary


class ListScheduledPostsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        page = HermosoClient.from_credentials(self.runtime.credentials).list_posts(
            status=str(tool_parameters.get("status") or "").strip(),
            channel=str(tool_parameters.get("channel") or "").strip().lower(),
            limit=as_int(tool_parameters.get("limit"), 20, 1, 100),
        )
        posts = [post_summary(p) for p in (page.get("data") or []) if isinstance(p, dict)]
        yield self.create_json_message({"posts": posts, "has_more": bool(page.get("has_more"))})
        if not posts:
            yield self.create_text_message("No posts match.")
            return
        lines = [
            f"{p['id']} | {p['status']} | {p['scheduled_at']} | {', '.join(p['channels'])} | {p['caption'][:80]}"
            for p in posts
        ]
        yield self.create_text_message("\n".join(lines))
