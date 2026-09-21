from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from hermoso_client import HermosoClient, HermosoError, as_bool, media_url, split_list, tool_output


class GenerateImageTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        prompt = str(tool_parameters.get("prompt") or "").strip()
        if not prompt:
            raise HermosoError("prompt is required: describe the image.", status=400)
        refs = split_list(tool_parameters.get("reference_images"))
        bad = [u for u in refs if not u.lower().startswith("https://")]
        if bad:
            raise HermosoError(f"reference_images must be public https URLs. Not accepted: {bad[0]}", status=400)
        args: dict[str, Any] = {
            "prompt": prompt,
            "aspectRatio": str(tool_parameters.get("aspect_ratio") or "1:1"),
            "useBrand": as_bool(tool_parameters.get("use_brand"), True),
            "model": str(tool_parameters.get("model") or "").strip(),
        }
        if refs:
            args["refImages"] = refs
        r = HermosoClient.from_credentials(self.runtime.credentials).call_tool("generate_image", args)
        out = tool_output(r)
        out["image_url"] = media_url(r, ("image", "url"))
        yield self.create_json_message(out)
        if out["image_url"]:
            yield self.create_text_message(f"Image ready: {out['image_url']}")
        else:
            yield self.create_text_message(out["text"])
