---
name: azf-x-opencli-reading
description: An Zhaofeng's personal X/Twitter reading workflow for Edge + OpenCLI. Use when the user shares x.com/twitter.com links, asks to understand a tweet, X Article, thread, or says X/Twitter content was not read correctly. Prefer OpenCLI article/tweets commands before generic web/Jina fallback, and do not treat Chrome-extension warnings as proof that Edge OpenCLI is unavailable.
---

# AZF X OpenCLI Reading

Use this as An Zhaofeng's personal override on top of `agent-reach` for X/Twitter URLs.

## Environment

- An Zhaofeng primarily uses Microsoft Edge for OpenCLI.
- Edge has OpenCLI installed.
- `agent-reach doctor --json` or `opencli doctor` may mention Chrome/Chromium extension status. Do not stop only because Chrome is missing; directly test OpenCLI commands, because Edge may still work.

## Read Order

For any `x.com/.../status/...` or `twitter.com/.../status/...` URL:

1. Try X Article first when the page might be an article card, longform post, or only shows a title/preview:

```bash
opencli twitter article "URL" -f yaml
```

2. Try tweets/thread reading for ordinary posts:

```bash
opencli twitter tweets "URL" -f yaml
```

3. If OpenCLI fails, restart the daemon once and retry the relevant command:

```bash
opencli daemon restart
opencli doctor
```

4. Use Jina Reader or direct web fetch only as fallback/verification. If web output is a login page, a card preview, or only an `x.com/i/article/...` link, do not treat that as full content.

## Failure Handling

- Do not use `opencli twitter tweet`; current OpenCLI uses `tweets`.
- When `status` output contains `Article`, a cover image, a title, or a truncated preview, continue with `opencli twitter article`.
- If only metadata is available, clearly tell the user which path failed and whether login/browser bridge is needed.
- Prefer structured output (`-f yaml` or JSON) so the final explanation can distinguish author, title, content, URL, and metrics.
