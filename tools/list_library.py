from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hermoso_client import HermosoClient, as_int, tool_output


class ListLibraryTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        r = HermosoClient.from_credentials(self.runtime.credentials).call_tool(
            "list_library",
            {
                "kind": str(tool_parameters.get("kind") or "all"),
                "limit": as_int(tool_parameters.get("limit"), 20, 1, 60),
            },
        )
        out = tool_output(r)
        yield self.create_json_message(out)
        yield self.create_text_message(out["text"])
