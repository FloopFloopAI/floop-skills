# Changelog

All notable changes to `floop-skills` are documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.2.0] — 2026-04-28

### Added
- **`floopfloop-check-subscription` skill** — covers the
  `current_subscription` MCP tool (newly shipped in `@floopfloop/mcp@0.1.0-alpha.6`).
  Walks the agent through distinguishing `current_subscription`
  ("what plan am I on, when does it renew?") from `usage_summary`
  ("am I about to hit my limits?") — the two tools overlap on
  `monthlyCredits` and `maxProjects` but answer different user
  questions. Documents the both-null edge case for users mid-signup
  or cancelled-with-no-grace.

### Changed
- Total skill count now **7** (was 6). Skills badge in README + the
  "What's in the box" table updated in lockstep.

## [0.1.0] — 2026-04-27

### Added

First public release. Six skills covering the canonical FloopFloop
agent workflows:

- `floopfloop-create-project` — natural-language → deployed URL.
  Picks a `botType`, optionally suggests a subdomain, calls
  `create_project`, waits for the build via `wait_for_live`. SDK
  fallback included.
- `floopfloop-refine-project` — sends a refinement to an existing
  project. Documents the three response shapes (queued / processing
  / saved-only), explains when to use `codeEditOnly` for the 3-step
  shortcut, and what NOT to do with the flag.
- `floopfloop-upload-attachment` — two-step upload + refine flow.
  Lists allowed file types, the 5 MB cap, and the `attachments`-pass-
  exactly-as-returned rule.
- `floopfloop-stream-build-status` — `wait_for_live` vs
  `project_status` polling, terminal-state semantics (live / failed /
  cancelled / archived), poll cadence, `progress` vs `step`/`totalSteps`.
- `floopfloop-handle-errors` — full error-code reference (retryable
  vs permanent), `Retry-After` semantics across SDKs, canonical
  exponential-backoff snippet.
- `floopfloop-manage-secrets` — write-only store semantics, rotation
  pattern, deploy-time-pickup gotcha, the `SECRET_DETECTED` rejection.

### Infra

- `scripts/validate-skills.py` enforces frontmatter + naming
  conventions on every PR.
- `scripts/install.sh` for one-line install into `~/.claude/skills`
  or per-project `.claude/skills`.
- README with install instructions, repo layout, contributing guide,
  and links to related FloopFloop repos.
- MIT license.
