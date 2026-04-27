---
name: floopfloop-create-project
description: Use when the user asks you to create a new FloopFloop project from a natural-language prompt — generates a website, app, bot, API, internal tool, or game and deploys it to a live URL. Covers picking a botType, choosing a subdomain, and waiting for the build.
---

# Creating a FloopFloop project

FloopFloop turns a natural-language prompt into a deployed project. The
canonical surface for AI agents is the [FloopFloop MCP server](https://www.npmjs.com/package/@floopfloop/mcp), which
exposes 22 tools wrapping the FloopFloop API. If the MCP isn't configured,
fall back to one of the language SDKs (`@floopfloop/sdk` for Node, `floopfloop`
on PyPI for Python, etc.).

## The flow

1. **Pick a `botType`** based on what the user described:
   - `site` (default) — marketing pages, blogs, content sites
   - `app` — apps with auth + database (todo, dashboard, social tool)
   - `bot` — Telegram/Discord-style automation
   - `api` — JSON API server, no UI
   - `internal` — admin tools, dashboards
   - `game` — playable browser games

2. **Optionally suggest a friendly subdomain.** `suggest_subdomain` takes
   the user's prompt and returns a slug; `check_subdomain` verifies it's
   free. Skip these if the user gave you a name.

3. **Call `create_project`.** Required: `prompt`. Optional: `name`,
   `subdomain`, `botType`, `isAuthProtected`, `teamId`. Returns a project
   id immediately; the build runs asynchronously.

4. **Wait for the build to reach a terminal state.** Use `wait_for_live`
   (blocks, default 10-min ceiling, capped at 30 min) or poll
   `project_status` if you need progress callbacks. Terminal states are
   `live`, `failed`, `cancelled`, `archived` — all of which stop the
   build; only `failed` / `cancelled` are errors.

## Example

```jsonl
{"tool":"suggest_subdomain","args":{"prompt":"a cat-cafe blog"}}
→ {"subdomain":"purr-press"}

{"tool":"check_subdomain","args":{"slug":"purr-press"}}
→ {"available":true}

{"tool":"create_project","args":{"prompt":"A cat-cafe blog with 3 sample posts","subdomain":"purr-press","botType":"site"}}
→ {"project":{"id":"p_abc","subdomain":"purr-press",...},"deployment":{...}}

{"tool":"wait_for_live","args":{"ref":"purr-press"}}
→ {"id":"p_abc","status":"live","url":"https://purr-press.floop.tech",...}
```

## Gotchas

- **Each `create_project` call costs credits** (typically 1 build credit).
  Run `usage_summary` first if the user is on a tight quota.
- **Builds normally finish in 60–120 seconds.** If `wait_for_live` is
  taking longer, the project is queued behind other builds —
  `project_status` returns `queuePosition` while queued.
- **Never construct a subdomain by hand for production users.** Use
  `suggest_subdomain` (free, AI-generated) so the slug isn't taken and
  matches the project's intent.
- **`isAuthProtected: true` adds a login wall** to the deployed site.
  Default is `false` (public).
- **Don't rebuild the same prompt twice** if the user just wanted a
  preview — call `cancel_project` instead.

## SDK fallback

If the MCP isn't available:

```ts
// Node
import { FloopClient } from "@floopfloop/sdk";
const floop = new FloopClient({ apiKey: process.env.FLOOP_API_KEY! });

const { project } = await floop.projects.create({
  prompt: "A cat-cafe blog with 3 sample posts",
  subdomain: "purr-press",
  botType: "site",
});
const live = await floop.projects.waitForLive(project.id);
console.log(live.url);
```

```python
# Python
from floopfloop import FloopClient

floop = FloopClient(api_key=os.environ["FLOOP_API_KEY"])
result = floop.projects.create(prompt="A cat-cafe blog with 3 sample posts", subdomain="purr-press", bot_type="site")
live = floop.projects.wait_for_live(result["project"]["id"])
print(live["url"])
```

Other SDKs (Go / Rust / Ruby / PHP / Swift / Kotlin) follow the same
shape — see [docs.sdks.md](https://github.com/FloopFloopAI/floop-skills/blob/main/docs/sdk-quick-reference.md)
for one-liners per language.
