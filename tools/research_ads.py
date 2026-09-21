from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hermoso_client import HermosoClient, HermosoError, tool_output


class ResearchAdsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        query = str(tool_parameters.get("query") or "").strip()
        if not query:
            raise HermosoError("query is required: say what to research.", status=400)
        r = HermosoClient.from_credentials(self.runtime.credentials).call_tool(
            "research_ads", {"query": query, "brand": str(tool_parameters.get("brand") or "").strip()}
        )
        out = tool_output(r)
        yield self.create_json_message(out)
        yield self.create_text_message(out["text"])
