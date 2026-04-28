# floop-skills

[![License: MIT](https://img.shields.io/github/license/FloopFloopAI/floop-skills)](./LICENSE)
[![Validate skills](https://img.shields.io/github/actions/workflow/status/FloopFloopAI/floop-skills/validate.yml?branch=main&logo=github&label=validate)](https://github.com/FloopFloopAI/floop-skills/actions/workflows/validate.yml)
[![Skills](https://img.shields.io/badge/skills-7-blue)](#whats-in-the-box)

**Drop-in [Claude Code](https://www.anthropic.com/claude-code) / [Claude Desktop](https://claude.ai/download) / [Copilot CLI](https://docs.github.com/en/copilot/github-copilot-in-the-cli) / Codex / Gemini CLI skills for [FloopFloop](https://www.floopfloop.com).**

Skills are markdown playbooks an AI agent loads on demand to learn _how_ to do something. The [FloopFloop MCP server](https://www.npmjs.com/package/@floopfloop/mcp) exposes the *capabilities* (22 tools); these skills explain the *workflows* — which tools to call in which order, FloopFloop-specific gotchas (credit costs, attachment size limits, codeEditOnly trade-offs, terminal-state semantics), and concrete copy-paste examples.

Pair them with the MCP and an agent goes from "configured to call FloopFloop tools" to "configured to use FloopFloop correctly" with a single clone.

## What's in the box

| Skill | Use when… |
|---|---|
| [`floopfloop-create-project`](./skills/floopfloop-create-project/SKILL.md) | The user asks for a new website, app, bot, API, internal tool, or game from a natural-language prompt |
| [`floopfloop-refine-project`](./skills/floopfloop-refine-project/SKILL.md) | The user wants to change something about an existing project — covers the three response shapes (queued / processing / saved-only) and `codeEditOnly` |
| [`floopfloop-upload-attachment`](./skills/floopfloop-upload-attachment/SKILL.md) | The user references a local file (mockup, PDF, CSV) in a refinement |
| [`floopfloop-stream-build-status`](./skills/floopfloop-stream-build-status/SKILL.md) | You need to wait for a build to finish — `wait_for_live` vs `project_status` polling |
| [`floopfloop-handle-errors`](./skills/floopfloop-handle-errors/SKILL.md) | A FloopFloop tool returns an error — the retryable / permanent split + canonical exponential-backoff pattern |
| [`floopfloop-manage-secrets`](./skills/floopfloop-manage-secrets/SKILL.md) | The user wants to add, list, or remove project env-var secrets safely |
| [`floopfloop-check-subscription`](./skills/floopfloop-check-subscription/SKILL.md) | The user asks about plan, billing period, or credit balance — distinguishes `current_subscription` from `usage_summary` |

Each skill is a self-contained markdown file with frontmatter — the agent's host process discovers them at startup and loads the body on demand when the description matches the user's intent.

## Install

### Claude Code / Claude Desktop

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/FloopFloopAI/floop-skills.git /tmp/floop-skills
cp -r /tmp/floop-skills/skills/* ~/.claude/skills/
```

Restart Claude Code. The next time you ask Claude to "build me a FloopFloop site for …" it'll load `floopfloop-create-project` and follow the playbook.

### Per-project (recommended for teams)

```bash
mkdir -p .claude/skills
git clone https://github.com/FloopFloopAI/floop-skills.git /tmp/floop-skills
cp -r /tmp/floop-skills/skills/* .claude/skills/
git add .claude/skills && git commit -m "Add FloopFloop agent skills"
```

Now every contributor on the project gets the same playbooks.

### Update later

```bash
cd /tmp/floop-skills && git pull
cp -r /tmp/floop-skills/skills/* ~/.claude/skills/   # or .claude/skills/
```

### Other agent hosts

The skills format follows Anthropic's [skills convention](https://www.anthropic.com/news/skills) — the `name` / `description` frontmatter is the universal hook. Most other agent runtimes (Copilot CLI, Codex, Gemini CLI) support skills in similar layouts; see the platform-specific install path in their docs and copy the `skills/` directory there.

## Setup checklist

These skills assume:

1. **You have the [`@floopfloop/mcp`](https://www.npmjs.com/package/@floopfloop/mcp) server configured** in your agent host. Quick config for Claude Desktop:

   ```json
   {
     "mcpServers": {
       "floopfloop": {
         "command": "npx",
         "args": ["-y", "@floopfloop/mcp"],
         "env": { "FLOOP_API_KEY": "flp_..." }
       }
     }
   }
   ```

2. **You have a FloopFloop API key.** Get one at [floopfloop.com/account/api-keys](https://www.floopfloop.com/account/api-keys) (Business plan required for issuing keys).

3. **You're on the latest MCP** (`@floopfloop/mcp@0.1.0-alpha.5` or newer). Earlier versions don't expose `attachments` or `codeEditOnly` on `refine_project` and the skills assume those work.

If your agent host can't run the MCP, the skills include SDK fallbacks for Node, Python, Go, Rust, Ruby, PHP, Swift, and Kotlin — pick the one that fits your stack from [docs/sdks.md](https://github.com/FloopFloopAI/floop-mcp/blob/main/docs/sdks.md).

## Repo layout

```
floop-skills/
├─ skills/
│  ├─ floopfloop-create-project/SKILL.md
│  ├─ floopfloop-refine-project/SKILL.md
│  ├─ floopfloop-upload-attachment/SKILL.md
│  ├─ floopfloop-stream-build-status/SKILL.md
│  ├─ floopfloop-handle-errors/SKILL.md
│  └─ floopfloop-manage-secrets/SKILL.md
├─ scripts/
│  └─ install.sh           # one-line install convenience
├─ .github/workflows/
│  └─ validate.yml         # frontmatter + filename sanity check on every PR
├─ CHANGELOG.md
├─ LICENSE                 # MIT
└─ README.md               # you are here
```

## Contributing

Adding a skill? It needs:

1. A directory under `skills/` named `floopfloop-<verb>-<noun>` (kebab-case, prefix for namespace safety in `~/.claude/skills/`).
2. A `SKILL.md` inside, with frontmatter `name:` (matching the directory) and `description:` (a "Use when…" sentence the agent matches against user intent).
3. A row added to the table in this README.
4. A row added to `CHANGELOG.md`'s `[Unreleased]` section.

The validator workflow runs on every PR — it checks the frontmatter parses and that `name` matches the directory.

## Related

- [`@floopfloop/mcp`](https://github.com/FloopFloopAI/floop-mcp) — MCP server (capabilities)
- [`@floopfloop/sdk`](https://github.com/FloopFloopAI/floop-node-sdk) — Node SDK
- [`floopfloop` (PyPI)](https://github.com/FloopFloopAI/floop-python-sdk) — Python SDK
- [`floop-cli`](https://github.com/FloopFloopAI/floop-cli) — single-binary CLI
- [Other 6 SDKs](https://github.com/FloopFloopAI) — Go, Rust, Ruby, PHP, Swift, Kotlin

## License

MIT — see [LICENSE](./LICENSE).
