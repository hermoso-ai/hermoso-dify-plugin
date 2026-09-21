from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hermoso_client import HermosoClient, HermosoError, as_int, tool_output


class PullCompetitorAdsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        name = str(tool_parameters.get("company_name") or "").strip()
        domain = str(tool_parameters.get("domain") or "").strip()
        if not name and not domain:
            raise HermosoError("Give company_name, domain, or both.", status=400)
        r = HermosoClient.from_credentials(self.runtime.credentials).call_tool(
            "pull_competitor_ads",
            {
                "companyName": name,
                "domain": domain,
                "country": str(tool_parameters.get("country") or "US").strip().upper(),
                "limit": as_int(tool_parameters.get("limit"), 10, 1, 30),
                "sort": str(tool_parameters.get("sort") or "longest_running"),
            },
        )
        out = tool_output(r)
        yield self.create_json_message(out)
        yield self.create_text_message(out["text"])
