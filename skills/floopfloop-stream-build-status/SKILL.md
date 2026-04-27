---
name: floopfloop-stream-build-status
description: Use when you need to know whether a FloopFloop project's build has finished — "is it deployed yet?", "wait for this to be live", "show me the build progress". Covers wait_for_live vs project_status polling, terminal state semantics, and timeout handling.
---

# Streaming a FloopFloop build to a terminal state

A FloopFloop build is asynchronous. After `create_project` or
`refine_project`, the project's status moves through:

`draft → queued → generating → generated → deploying → live`

…or eventually `failed` / `cancelled` / `archived`. The four **terminal**
states are `live`, `failed`, `cancelled`, `archived` — once one of
those is reached, polling stops.

## Two ways to wait

### `wait_for_live` (blocks)

Best for "I just want the URL." Blocks until terminal, returns the
hydrated project on success, surfaces a typed error on `failed` /
`cancelled`.

```jsonl
{"tool":"wait_for_live","args":{"ref":"purr-press"}}
→ {"id":"p_abc","status":"live","url":"https://purr-press.floop.tech",...}

{"tool":"wait_for_live","args":{"ref":"purr-press","timeoutMs":120000}}
// timeoutMs caps the wait; default is 10 minutes, max 30 minutes.
```

### `project_status` (poll)

Best for "I want to show progress to the user." Returns the current
snapshot; call repeatedly to see transitions.

```jsonl
{"tool":"project_status","args":{"ref":"purr-press"}}
→ {"step":3,"totalSteps":6,"status":"generating","message":"Writing components","progress":0.45,"queuePosition":null}
```

## What to do on each terminal state

- **`live`** — success. Read `project.url` and surface to the user.
- **`archived`** — terminal but not active. The project exists but isn't
  running; treat as a no-op success (it isn't an error).
- **`failed`** — build error. The MCP wraps this as an `isError: true`
  result with code `BUILD_FAILED` and the error message. Surface the
  message to the user; suggest a `refine_project` with a fix or a
  `cancel_project` + new attempt.
- **`cancelled`** — someone (often the user) called `cancel_project`.
  Code `BUILD_CANCELLED`. Don't retry automatically.

## Gotchas

- **Don't poll faster than every 2 seconds.** Backend rate-limits at
  this granularity, and faster polling burns rate-limit budget without
  surfacing new info.
- **The default `wait_for_live` ceiling is 10 minutes.** If the user is
  building something genuinely slow (rare), pass `timeoutMs` up to 30
  minutes. Beyond that, call `project_status` yourself and let the user
  decide when to give up.
- **`queuePosition` only appears while status is `queued`.** Don't
  treat its absence as "the queue cleared" — check `status` itself.
- **A project can transition `live` → `archived`** if the user archives
  it from the web UI mid-stream. Treat archived as a clean exit, not an
  unexpected state.
- **`step` and `totalSteps` change when `codeEditOnly` is in effect** —
  the patch path is 3 steps total, so `step: 2` in a code-edit means
  "67% done", not "33%". Use `progress` (0.0–1.0) for a stable
  percentage if you're rendering a progress bar.

## SDK fallback

```ts
// Node — async iterator yields each de-duplicated snapshot
for await (const ev of floop.projects.stream("purr-press")) {
  console.log(`[${ev.status}] ${ev.message} (${ev.step}/${ev.totalSteps})`);
}
// Or block + return the project:
const live = await floop.projects.waitForLive("purr-press");
```

```python
# Python
for ev in floop.projects.stream("purr-press"):
    print(f"[{ev['status']}] {ev['message']} ({ev['step']}/{ev['totalSteps']})")
live = floop.projects.wait_for_live("purr-press")
```
