from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hermoso_client import HermosoClient, HermosoError, job_output


class GetJobTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        job_id = str(tool_parameters.get("job_id") or "").strip()
        if not job_id:
            raise HermosoError("job_id is required: pass the id generate_video returned.", status=400)
        r = HermosoClient.from_credentials(self.runtime.credentials).call_tool("get_job", {"id": job_id})
        out = job_output(r, job_id=job_id)
        yield self.create_json_message(out)
        yield self.create_text_message(out["message"])
