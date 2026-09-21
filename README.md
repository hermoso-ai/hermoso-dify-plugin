# Hermoso for Dify

Give a Dify agent or workflow a marketing toolkit: research the ads that are winning in a market, generate on-brand image and video ads, and schedule posts to your own social channels.

[Hermoso](https://hermoso.ai) is a marketing platform with a REST API. This plugin is a thin client for that API. It talks to one host, `app.hermoso.ai`, over HTTPS.

- Source repository: https://github.com/hermoso-ai/hermoso-dify-plugin
- API reference: https://hermoso.ai/docs/api
- Support: hello@hermoso.ai

## Tools

| Tool | What it does | Spends Hermoso credits |
| --- | --- | --- |
| Check Credits | Credit balance and plan of the connected account | No |
| List Channels | The social channels the account can publish to, and which are connected | No |
| Find Competitors | Competitor and similar brands from a website domain | Yes |
| Pull Competitor Ads | The real ads one named brand is running on Facebook and Instagram | Yes |
| Research Ads | Open-ended ad research with a written summary (30 to 60 seconds) | Yes |
| Generate Image | One finished ad image from a prompt, on-brand by default | Yes |
| Generate Video | Starts a video render (long-running, see below) | Yes |
| Get Job | Status of a render job, and the media URL when it is done | No |
| List Library | Images and videos already generated in the account | No |
| Schedule Post | Schedules a post to one or more connected channels | No (posts to X are the one exception) |
| List Scheduled Posts | Scheduled and published posts with per-channel results | No |
| Cancel Scheduled Post | Cancels a post that has not gone out yet | No |

Credits are spent only when an AI model runs or ad research is pulled. Scheduling, publishing and reading do not spend credits, with one exception: a post to X spends a few credits when it goes out. Use Check Credits to see the balance at any time.

## Setup

1. Create a Hermoso account at https://app.hermoso.ai.
2. In the Hermoso app open **Settings, Agents & API** and create an API key. It starts with `hmk_`.
3. In Dify, install this plugin, open **Tools**, find **Hermoso**, choose **Authorize**, and paste the key.
4. Dify validates the key with one free read (`GET /v1/credits`). Nothing is generated or published during validation.

To schedule posts, connect your social accounts first. That is a browser sign-in with each platform, so it is done in the Hermoso app under **Settings, Connectors**, not from Dify. List Channels shows which channels are connected.

## Connection requirements

- Outbound HTTPS to `app.hermoso.ai` (port 443). No other host is contacted.
- Authentication is the API key, sent as `Authorization: Bearer hmk_...` on every request.
- The key is stored by Dify as a secret credential. The plugin never writes it to logs or error messages.
- Every request has a timeout. Reads wait up to 30 seconds. Calls that run a model wait up to 110 seconds.

## Usage

### In an agent

Add the Hermoso tools to an Agent app and ask in plain words:

- "Find the competitors of allbirds.com and pull the longest running ads for the top one."
- "Make a 4:5 image ad for our new trail shoe on a mountain ridge at sunrise."
- "Schedule that image to Instagram and LinkedIn for Friday at 9am New York time."

### In a workflow

Each tool returns a JSON object and a short text summary. Use the JSON fields as variables in later nodes.

### Video renders are long-running

A video render takes one to three minutes, longer than one tool call should wait.

1. **Generate Video** waits up to about 45 seconds. If the clip is ready it returns `status: done` and `video_url`. Otherwise it returns `status: rendering` and a `job_id`.
2. Call **Get Job** with that `job_id` until `status` is `done` or `error`. In a workflow, put Get Job in a loop with a short wait between calls.
3. Never call Generate Video again for the same request while a job is rendering. That would run a second render and spend credits twice.

`status: not_found` from Get Job is final. Stop polling that id.

### Scheduling

Schedule Post needs exactly one of `scheduled_at` (an ISO 8601 time in the future) or `use_queue` (the next free slot in the brand's posting schedule). This plugin never publishes immediately. The post goes to your real social accounts at that time, so in agent apps it is a good idea to have the agent confirm the caption, media, channels and time with you first.

Media can be a URL returned by Generate Image, Generate Video, Get Job or List Library, or any public `https` URL. Two or more images are published as a carousel on channels that support one.

Channel rules such as caption length and required media are checked when the post is scheduled. A post that a channel cannot accept is refused with the reason instead of failing later.

## What this plugin does not do

- It does not connect social accounts. That is a browser sign-in done in the Hermoso app.
- It does not manage paid ad campaigns, and it does not buy credits or change a plan.
- It does not publish immediately. Only scheduled posts.
- It does not run code, read local files or fetch arbitrary URLs itself. Media URLs you provide are passed to Hermoso, which fetches them.

## Errors

Errors come back as readable sentences from the Hermoso API, with a request id you can quote to support. Common ones:

- The API key was rejected: create a new key and update the authorization.
- A channel is not connected: connect it in the Hermoso app under Settings, Connectors.
- Not enough credits for a generation: nothing is rendered when the balance cannot cover it.

## Privacy

See [PRIVACY.md](PRIVACY.md) and https://hermoso.ai/privacy.

## Development

See [CONTRIBUTING.md](https://github.com/hermoso-ai/hermoso-dify-plugin/blob/main/CONTRIBUTING.md) in the source repository for how to run the tests.

## License

MIT
