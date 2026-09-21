# Privacy Policy

This plugin connects Dify to the Hermoso API (`https://app.hermoso.ai/v1`). Hermoso's full privacy policy is at https://hermoso.ai/privacy. This page describes what the plugin itself handles.

## What the plugin does with data

The plugin is a stateless client. It does not collect analytics, does not store anything, does not write user data or credentials to logs, and contacts no host other than `app.hermoso.ai`.

## Data sent to Hermoso

Only what a tool call needs, over HTTPS:

- **Your Hermoso API key**, as an `Authorization` header, to authenticate each request. Dify stores the key as an encrypted secret credential. The plugin never returns it in output or error messages.
- **Tool inputs you or your agent provide**: a company domain or name for ad research, a research question, image and video prompts, reference image URLs, post captions, titles, links, media URLs, channel ids and schedule times.

The plugin does not ask for, or need, names, email addresses, phone numbers or other personal data. If you put personal data in a prompt or a caption, it is sent to Hermoso as part of that input.

## What Hermoso does with it

Hermoso processes these inputs to perform the request: it runs ad research, generates media, and stores scheduled posts and generated media in your Hermoso account. When a scheduled post goes out, Hermoso sends its caption and media to the social platforms you connected and chose for that post (for example Facebook, Instagram, Threads, TikTok, YouTube, LinkedIn, X, Pinterest, Bluesky or Telegram), under those platforms' own privacy policies. Connecting those accounts happens in the Hermoso app, not in this plugin.

Hermoso uses AI model providers and data providers as subprocessors to fulfil generation and research requests. Retention, subprocessors, and how to request access to or deletion of your data are described at https://hermoso.ai/privacy.

## Data returned to Dify

Tool results: ad research results (public advertising data), URLs of generated media, render job status, scheduled post records, channel connection status and the credit balance. The display name of a connected social account is left out of the List Channels result on purpose.

## Contact

hello@hermoso.ai
