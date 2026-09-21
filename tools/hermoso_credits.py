from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hermoso_client import HermosoClient


class HermosoCreditsTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        c = HermosoClient.from_credentials(self.runtime.credentials).credits()
        out = {"balance": c.get("balance"), "plan": c.get("plan"), "shared_workspace": bool(c.get("shared_workspace"))}
        yield self.create_json_message(out)
        yield self.create_text_message(f"Credit balance: {out['balance']} (plan: {out['plan']}).")
