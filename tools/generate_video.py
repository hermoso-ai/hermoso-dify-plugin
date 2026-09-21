from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hermoso_client import HermosoClient, HermosoError, as_bool, job_output


class GenerateVideoTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        prompt = str(tool_parameters.get("prompt") or "").strip()
        if not prompt:
            raise HermosoError("prompt is required: describe the clip.", status=400)
        ref = str(tool_parameters.get("reference_image") or "").strip()
        if ref and not ref.lower().startswith("https://"):
            raise HermosoError("reference_image must be a public https URL.", status=400)
        args: dict[str, Any] = {
            "prompt": prompt,
            "aspectRatio": str(tool_parameters.get("aspect_ratio") or "9:16"),
            "refImage": ref,
            "model": str(tool_parameters.get("model") or "").strip(),
        }
        duration = tool_parameters.get("duration_seconds")
        if duration not in (None, ""):
            args["durationSeconds"] = float(duration)
        if not as_bool(tool_parameters.get("audio"), True):
            args["audio"] = False
        r = HermosoClient.from_credentials(self.runtime.credentials).call_tool("generate_video", args)
        out = job_output(r)
        yield self.create_json_message(out)
        yield self.create_text_message(out["message"])
