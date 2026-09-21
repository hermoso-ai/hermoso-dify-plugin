from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hermoso_client import HermosoClient, HermosoError


class CancelScheduledPostTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        post_id = str(tool_parameters.get("post_id") or "").strip()
        if not post_id:
            raise HermosoError("post_id is required. Find it with list_scheduled_posts.", status=400)
        r = HermosoClient.from_credentials(self.runtime.credentials).cancel_post(post_id)
        out = {"id": r.get("id") or post_id, "cancelled": bool(r.get("deleted"))}
        yield self.create_json_message(out)
        yield self.create_text_message(f"Cancelled scheduled post {out['id']}." if out["cancelled"] else f"Post {out['id']} was not cancelled.")
