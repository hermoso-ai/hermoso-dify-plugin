from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hermoso_client import HermosoClient

KEEP = (
    "id", "name", "available", "unavailable_reason", "connected", "needs_reconnect",
    "visibilities", "carousel", "caption_max",
)


class ListChannelsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        rows = HermosoClient.from_credentials(self.runtime.credentials).channels().get("data") or []
        # The connected account's display name is left out on purpose: the agent needs to know
        # WHETHER a channel is connected, not whose name is on it.
        channels = [{k: row.get(k) for k in KEEP} for row in rows if isinstance(row, dict)]
        yield self.create_json_message({"channels": channels})
        ready = [c["id"] for c in channels if c.get("connected") and c.get("available")]
        missing = [c["id"] for c in channels if c.get("available") and not c.get("connected")]
        lines = [f"Connected and ready: {', '.join(ready) or 'none'}."]
        if missing:
            lines.append(
                f"Not connected: {', '.join(missing)}. Connect them in the Hermoso app under Settings, Connectors."
            )
        yield self.create_text_message("\n".join(lines))
