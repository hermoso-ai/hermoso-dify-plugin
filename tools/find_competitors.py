from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hermoso_client import HermosoClient, HermosoError, tool_output


class FindCompetitorsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        domain = str(tool_parameters.get("domain") or "").strip()
        if not domain:
            raise HermosoError("domain is required, for example allbirds.com.", status=400)
        mode = str(tool_parameters.get("mode") or "competitors")
        r = HermosoClient.from_credentials(self.runtime.credentials).call_tool(
            "find_competitors", {"domain": domain, "mode": mode}
        )
        out = tool_output(r)
        yield self.create_json_message(out)
        yield self.create_text_message(out["text"])
