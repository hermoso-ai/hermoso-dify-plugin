"""Writes tools/*.yaml from one table so labels and descriptions stay consistent.

Development helper only. It is excluded from the package by .difyignore.
Run:  python scripts/build_tool_yaml.py
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
AUTHOR = "hermoso-ai"


def L(en: str, zh: str) -> dict:
    return {"en_US": en, "zh_Hans": zh}


def P(name, type_, label, human, llm, *, required=False, form="llm", default=None, options=None, min_=None, max_=None):
    p = {"name": name, "type": type_, "required": required, "label": label, "human_description": human,
         "llm_description": llm, "form": form}
    if default is not None:
        p["default"] = default
    if options:
        p["options"] = [{"value": v, "label": lab} for v, lab in options]
    if min_ is not None:
        p["min"] = min_
    if max_ is not None:
        p["max"] = max_
    return p


ASPECT_IMAGE = [(v, L(v, v)) for v in ["1:1", "4:5", "9:16", "16:9", "3:4", "4:3"]]
ASPECT_VIDEO = [(v, L(v, v)) for v in ["9:16", "16:9", "1:1", "4:3", "3:4"]]

TOOLS = [
    dict(
        name="hermoso_credits",
        label=L("Check Credits", "查询额度"),
        human=L("Show the credit balance and plan of the connected Hermoso account. Free.",
                "查看已连接 Hermoso 账户的额度余额和套餐。免费。"),
        llm="Returns the Hermoso account's credit balance and plan. Free and read-only. Call it before a "
            "generation or an ad research call when the user asks what they have left. Only AI model runs and "
            "ad research spend credits. Publishing and scheduling do not, except posts to X.",
        params=[],
    ),
    dict(
        name="find_competitors",
        label=L("Find Competitors", "查找竞争对手"),
        human=L("Discover competitor and similar brands from a company's website domain. Spends a small amount of credits.",
                "根据公司网站域名发现竞争品牌和相似品牌。消耗少量额度。"),
        llm="Discovers a brand's competitors, similar brands and adjacent brands from its website domain. "
            "Returns a list of {name, domain, kind, reason}. It runs an AI model, so it spends a small amount of "
            "Hermoso credits. Use the returned name or "
            "domain with pull_competitor_ads to see the ads a brand is running.",
        params=[
            P("domain", "string", L("Brand domain", "品牌域名"),
              L("The company website domain, for example allbirds.com.", "公司网站域名，例如 allbirds.com。"),
              "The brand's website domain without a path, for example allbirds.com.", required=True),
            P("mode", "select", L("Mode", "模式"),
              L("Competitors (excludes the searched brand) or the best relevant advertisers to learn from.",
                "竞争对手（不含所查品牌），或最值得借鉴的相关广告主。"),
              "competitors (default): head-to-head rivals and similar brands, excluding the searched brand. "
              "inspiration: the brands with the most copyable ads for this market, including the searched brand.",
              default="competitors",
              options=[("competitors", L("Competitors", "竞争对手")), ("inspiration", L("Best relevant ads", "最佳相关广告"))]),
        ],
    ),
    dict(
        name="pull_competitor_ads",
        label=L("Pull Competitor Ads", "拉取竞品广告"),
        human=L("Get the real ads one named brand is running on Facebook and Instagram, deduplicated and sorted. Spends credits.",
                "获取某个品牌在 Facebook 和 Instagram 上正在投放的真实广告，已去重并排序。消耗额度。"),
        llm="Returns the live ads ONE named brand is running in the Meta ad library (Facebook and Instagram), "
            "deduplicated and sorted, with ad copy, call to action, media URLs and run dates. One call, a few "
            "seconds. Give company_name, domain, or both; both gives the most reliable match. Spends Hermoso "
            "credits. If the brand name is ambiguous the result can be empty with a note rather than a wrong brand.",
        params=[
            P("company_name", "string", L("Company name", "公司名称"),
              L("The advertiser name, for example Allbirds.", "广告主名称，例如 Allbirds。"),
              "The advertiser's brand name. Give this, domain, or both."),
            P("domain", "string", L("Company domain", "公司域名"),
              L("The advertiser website domain, for example allbirds.com.", "广告主网站域名，例如 allbirds.com。"),
              "The advertiser's website domain. It is used to resolve the right advertiser page."),
            P("country", "string", L("Country", "国家"),
              L("Two-letter country code. Default US.", "两位国家代码，默认 US。"),
              "Two-letter ISO country code of the ad library to read, for example US, GB, DE. Default US.",
              default="US"),
            P("limit", "number", L("Max ads", "最多广告数"),
              L("How many ads to return (1 to 30).", "返回的广告数量（1 到 30）。"),
              "Maximum number of ads to return, 1 to 30. Default 10.", default=10, min_=1, max_=30),
            P("sort", "select", L("Sort", "排序"),
              L("Longest running surfaces proven ads first.", "按投放时长排序可优先看到已验证有效的广告。"),
              "longest_running (default, proven ads first), newest, or impressions.",
              default="longest_running",
              options=[("longest_running", L("Longest running", "投放最久")), ("newest", L("Newest", "最新")),
                       ("impressions", L("Most impressions", "展示最多"))]),
        ],
    ),
    dict(
        name="research_ads",
        label=L("Research Ads", "广告调研"),
        human=L("Open-ended ad research across ad libraries with a written summary. Takes 30 to 60 seconds. Spends credits.",
                "跨广告库的开放式广告调研，并给出文字总结。需要 30 到 60 秒。消耗额度。"),
        llm="Open-ended ad research that needs judgment across platforms: comparisons, which angle is working "
            "in a market, who else is doing something. It runs several library lookups and writes a synthesis, "
            "so it typically takes 30 to 60 seconds. Spends Hermoso credits. For one named brand's ads use "
            "pull_competitor_ads instead, which is faster.",
        params=[
            P("query", "string", L("Research question", "调研问题"),
              L("What to research, in plain words.", "用自然语言描述要调研的内容。"),
              "What to research, for example: the longest-running protein bar ads on Meta and the hooks they repeat.",
              required=True),
            P("brand", "string", L("Brand", "品牌"),
              L("Optional brand name to tailor the research to. Defaults to the account's saved brand.",
                "可选：用于定制调研的品牌名称，默认使用账户中保存的品牌。"),
              "Optional brand name to tailor the research to. Omit to use the workspace's saved brand."),
        ],
    ),
    dict(
        name="generate_image",
        label=L("Generate Image", "生成图片"),
        human=L("Generate an ad image from a prompt, on-brand by default, and return its URL. Spends credits.",
                "根据提示词生成广告图片（默认符合品牌风格），并返回图片链接。消耗额度。"),
        llm="Generates one finished image from a prompt and returns its hosted URL. The call waits for the "
            "image, usually under a minute. By default it uses the account's saved brand references so the "
            "result is on-brand; set use_brand to false for a plain prompt-only generation. reference_images "
            "composites real product or logo images into the scene. Spends Hermoso credits.",
        params=[
            P("prompt", "string", L("Prompt", "提示词"),
              L("Describe the image: subject, composition, lighting and any text on the image.",
                "描述图片：主体、构图、光线以及图片上的文字。"),
              "The full image prompt: subject, composition, lighting and any on-image ad text.", required=True),
            P("aspect_ratio", "select", L("Aspect ratio", "宽高比"),
              L("Shape of the image. Default 1:1.", "图片比例，默认 1:1。"),
              "Aspect ratio of the image. Default 1:1. Use 4:5 or 1:1 for feeds, 9:16 for stories and reels.",
              default="1:1", options=ASPECT_IMAGE),
            P("reference_images", "string", L("Reference image URLs", "参考图片链接"),
              L("Optional public image URLs (product, logo), separated by commas.",
                "可选：公开的图片链接（产品、标志），用逗号分隔。"),
              "Optional comma-separated public https image URLs of a product or logo to composite into the image."),
            P("use_brand", "boolean", L("Use saved brand", "使用已保存品牌"),
              L("Use the account's saved brand references. Turn off for a plain generation.",
                "使用账户中保存的品牌素材。关闭后为纯提示词生成。"),
              "true (default) uses the saved brand's product and logo references. false runs the prompt alone.",
              default=True, form="form"),
            P("model", "string", L("Model", "模型"),
              L("Optional image model id. Leave empty for the recommended default.", "可选：图片模型 ID，留空使用推荐默认值。"),
              "Optional image model id. Omit it unless the user named a model; the default is a sound choice.",
              form="form"),
        ],
    ),
    dict(
        name="generate_video",
        label=L("Generate Video", "生成视频"),
        human=L("Start a video render from a prompt. Long-running: returns the video URL if it finishes quickly, otherwise a job id to poll with Get Job. Spends credits.",
                "根据提示词开始渲染视频。耗时较长：若很快完成则返回视频链接，否则返回任务 ID，请用“查询任务”轮询。消耗额度。"),
        llm="Starts ONE video render from a prompt. LONG-RUNNING: renders take 1 to 3 minutes. This tool waits "
            "up to about 45 seconds; if the clip is ready it returns video_url, otherwise it returns "
            "status=rendering with a job_id. When you get a job_id, call get_job with it until status is done "
            "or error. NEVER call generate_video again for the same request while a job is rendering: that "
            "spends credits twice. Spends Hermoso credits.",
        params=[
            P("prompt", "string", L("Prompt", "提示词"),
              L("Describe the clip: subject, action, camera and mood.", "描述视频片段：主体、动作、镜头和氛围。"),
              "The video prompt or shot description: subject, action, camera movement, setting and mood.", required=True),
            P("duration_seconds", "number", L("Duration (seconds)", "时长（秒）"),
              L("Length of the clip. Leave empty for the model default.", "视频时长，留空使用模型默认值。"),
              "Clip length in seconds. Omit for the model's default. Not every length is available on every model; "
              "an unsupported length is refused with the lengths that are available.", min_=1, max_=60),
            P("aspect_ratio", "select", L("Aspect ratio", "宽高比"),
              L("Shape of the video. Default 9:16.", "视频比例，默认 9:16。"),
              "Aspect ratio. Default 9:16 (vertical). Use 16:9 for YouTube, 1:1 for feeds.",
              default="9:16", options=ASPECT_VIDEO),
            P("reference_image", "string", L("First frame image URL", "首帧图片链接"),
              L("Optional public image URL to start the clip from.", "可选：作为视频首帧的公开图片链接。"),
              "Optional public https image URL that anchors the first frame, for example a product photo."),
            P("audio", "boolean", L("Audio", "音频"),
              L("Render with sound. Turn off for a silent clip.", "渲染带声音的视频，关闭则为无声视频。"),
              "true (default) renders with sound. false renders a silent clip.", default=True, form="form"),
            P("model", "string", L("Model", "模型"),
              L("Optional video model id. Leave empty for the recommended default.", "可选：视频模型 ID，留空使用推荐默认值。"),
              "Optional video model id. Omit it unless the user named a model.", form="form"),
        ],
    ),
    dict(
        name="get_job",
        label=L("Get Job", "查询任务"),
        human=L("Check a render job started by Generate Video. Returns its status and the media URL when done. Free.",
                "查询由“生成视频”启动的渲染任务，返回状态，完成后返回媒体链接。免费。"),
        llm="Polls a render job by id. Returns status (queued, running, done, error or not_found), progress, and "
            "on done the media URL. Each call can wait up to about 45 seconds, and a render takes 1 to 3 "
            "minutes, so several calls are normal. Keep calling until done or error. not_found is final: stop "
            "polling and do not start the render again. Free.",
        params=[
            P("job_id", "string", L("Job id", "任务 ID"),
              L("The job id returned by Generate Video, for example job_abc123.", "“生成视频”返回的任务 ID，例如 job_abc123。"),
              "The job id returned by generate_video, for example job_abc123.", required=True),
        ],
    ),
    dict(
        name="list_library",
        label=L("List Library", "素材库列表"),
        human=L("List the images and videos already generated in this Hermoso account, newest first. Free.",
                "列出该 Hermoso 账户中已生成的图片和视频，按时间倒序。免费。"),
        llm="Lists the images and videos in the account's Hermoso Library, newest first, with each asset's URL, "
            "kind, model and age. The URLs can be passed to schedule_post as media. Free and read-only.",
        params=[
            P("kind", "select", L("Kind", "类型"), L("Filter by asset kind.", "按素材类型筛选。"),
              "image, video or all (default).", default="all",
              options=[("all", L("All", "全部")), ("image", L("Images", "图片")), ("video", L("Videos", "视频"))]),
            P("limit", "number", L("Max assets", "最多素材数"), L("How many to return (1 to 60).", "返回数量（1 到 60）。"),
              "Maximum number of assets, 1 to 60. Default 20.", default=20, min_=1, max_=60),
        ],
    ),
    dict(
        name="list_channels",
        label=L("List Channels", "渠道列表"),
        human=L("List the social channels this Hermoso account can publish to and which are connected. Free.",
                "列出该 Hermoso 账户可发布的社交渠道及其连接状态。免费。"),
        llm="Lists every publishing channel with its id, whether it is connected, its caption length limit, the "
            "visibilities it supports and its carousel limits. Call it before schedule_post to pick valid "
            "channel ids. A channel that is not connected must be linked by the user in the Hermoso app under "
            "Settings, Connectors; that is a browser sign-in and cannot be done from here. Free.",
        params=[],
    ),
    dict(
        name="schedule_post",
        label=L("Schedule Post", "定时发布"),
        human=L("Schedule a social post to one or more connected channels at a future time or the next queue slot. Free, except posts to X, which spend a few credits. This writes to your real social accounts.",
                "将社交帖子定时发布到一个或多个已连接渠道，可指定未来时间或使用下一个队列时段。免费（发布到 X 的帖子除外，会消耗少量额度）。此操作会写入你的真实社交账号。"),
        llm="Schedules ONE post to one or more connected channels. It will be published to the user's real "
            "social accounts at that time, so confirm the caption, media, channels and time with the user "
            "first. Give exactly one of scheduled_at or use_queue. This tool never publishes immediately. "
            "Channel rules (caption limits, media requirements) are checked now and refused by name rather "
            "than failing later. Returns the created post with its id. Spends no credits, with one exception: "
            "a post to X spends a few credits when it goes out.",
        params=[
            P("channels", "string", L("Channels", "渠道"),
              L("Channel ids separated by commas, for example instagram, tiktok. See List Channels.",
                "渠道 ID，用逗号分隔，例如 instagram, tiktok。参见“渠道列表”。"),
              "Comma-separated channel ids from list_channels, for example: instagram, tiktok, linkedin.", required=True),
            P("caption", "string", L("Caption", "文案"), L("The post text.", "帖子正文。"),
              "The post text used on every channel."),
            P("media_urls", "string", L("Media URLs", "媒体链接"),
              L("Image or video URLs separated by commas. Two or more images make a carousel.",
                "图片或视频链接，用逗号分隔。两张及以上图片将作为轮播。"),
              "Comma-separated media URLs in order: a Hermoso URL from generate_image, generate_video, get_job "
              "or list_library, or a public https URL. One item is a single post; two or more images are a carousel."),
            P("scheduled_at", "string", L("Scheduled time", "发布时间"),
              L("ISO 8601 time in the future, for example 2030-01-15T09:00:00Z.", "未来的 ISO 8601 时间，例如 2030-01-15T09:00:00Z。"),
              "When to publish, ISO 8601 with a timezone offset or Z, at least one minute in the future. "
              "Give this OR use_queue, not both."),
            P("use_queue", "boolean", L("Use posting queue", "使用发布队列"),
              L("Take the next free slot in the brand's posting schedule instead of naming a time.",
                "使用品牌发布日程中的下一个空闲时段，而不是指定时间。"),
              "true takes the next free slot of the brand's saved posting schedule. Give this OR scheduled_at.",
              default=False),
            P("timezone", "string", L("Timezone", "时区"),
              L("IANA timezone for the queue, for example America/New_York.", "队列使用的 IANA 时区，例如 America/New_York。"),
              "IANA timezone for use_queue, for example America/New_York. Defaults to the brand's saved zone."),
            P("title", "string", L("Title", "标题"),
              L("Headline for YouTube and Pinterest.", "YouTube 和 Pinterest 使用的标题。"),
              "Headline that YouTube and Pinterest require. Derived from the caption when omitted."),
            P("link", "string", L("Link", "链接"), L("Optional link to attach.", "可选：附加的链接。"),
              "Optional destination link to attach to the post."),
            P("visibility", "select", L("Visibility", "可见性"),
              L("Public by default. Not every channel supports every option.", "默认公开。并非所有渠道都支持所有选项。"),
              "public (default), unlisted, private or draft. A channel that cannot honour the choice refuses it.",
              default="public", form="form",
              options=[("public", L("Public", "公开")), ("unlisted", L("Unlisted", "不公开列出")),
                       ("private", L("Private", "私密")), ("draft", L("Draft", "草稿"))]),
        ],
    ),
    dict(
        name="list_scheduled_posts",
        label=L("List Scheduled Posts", "已排期帖子列表"),
        human=L("List scheduled and already published posts with their per-channel results. Free.",
                "列出已排期和已发布的帖子及各渠道结果。免费。"),
        llm="Lists posts for this workspace, newest first: id, status, scheduled time, channels, caption and "
            "per-channel results. Use it to confirm a schedule_post call or to find a post id to cancel. Free.",
        params=[
            P("status", "select", L("Status", "状态"), L("Filter by status.", "按状态筛选。"),
              "Optional status filter.",
              options=[("scheduled", L("Scheduled", "已排期")), ("published", L("Published", "已发布")),
                       ("partially_published", L("Partially published", "部分发布")), ("failed", L("Failed", "失败"))]),
            P("channel", "string", L("Channel", "渠道"), L("Only posts that include this channel id.", "仅显示包含该渠道的帖子。"),
              "Optional channel id filter, for example instagram."),
            P("limit", "number", L("Max posts", "最多帖子数"), L("How many to return (1 to 100).", "返回数量（1 到 100）。"),
              "Maximum number of posts, 1 to 100. Default 20.", default=20, min_=1, max_=100),
        ],
    ),
    dict(
        name="cancel_scheduled_post",
        label=L("Cancel Scheduled Post", "取消已排期帖子"),
        human=L("Cancel a post that is still scheduled. It cannot remove a post that was already published. Free.",
                "取消仍在排期中的帖子。无法删除已经发布的帖子。免费。"),
        llm="Cancels ONE scheduled post by id so it will not be published. Only works while the post is still "
            "scheduled; an already published post is refused. Confirm with the user first. Free.",
        params=[
            P("post_id", "string", L("Post id", "帖子 ID"),
              L("The id from Schedule Post or List Scheduled Posts.", "来自“定时发布”或“已排期帖子列表”的 ID。"),
              "The post id returned by schedule_post or list_scheduled_posts.", required=True),
        ],
    ),
]


def main() -> None:
    out = ROOT / "tools"
    for t in TOOLS:
        doc = {
            "identity": {"name": t["name"], "author": AUTHOR, "label": t["label"]},
            "description": {"human": t["human"], "llm": t["llm"]},
            "parameters": t["params"],
            "extra": {"python": {"source": f"tools/{t['name']}.py"}},
        }
        if not t["params"]:
            doc.pop("parameters")
        (out / f"{t['name']}.yaml").write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")
    print(f"wrote {len(TOOLS)} tool definitions")


if __name__ == "__main__":
    main()
