---
name: floopfloop-handle-errors
description: Use when a FloopFloop tool call returns an isError result or throws — distinguishes retryable transport errors from permanent ones, explains Retry-After header semantics, and shows the canonical exponential-backoff pattern.
---

# Handling FloopFloop errors

The FloopFloop MCP wraps every API error in an `isError: true` content
result with the format:

```
[<CODE> <STATUS>] <message> (request <requestId>)
```

…where `<CODE>` is the typed error code, `<STATUS>` is the HTTP status,
and `<requestId>` (when present) lets the FloopFloop team trace the
specific request in their logs. Same shape across all SDKs — Node /
Python / Go / Rust / Ruby / PHP / Swift / Kotlin all parse the wire
envelope into a typed error class.

## Error-code reference

### Retryable (back off and try again)

| Code | When | What to do |
|---|---|---|
| `RATE_LIMITED` | 429, you exceeded per-key rate limit | Wait `retryAfterMs` (parsed from server header), then retry |
| `NETWORK_ERROR` | Transport-level failure (DNS, connection refused) | Exponential backoff |
| `TIMEOUT` | Request exceeded client timeout (default 30 s) | Exponential backoff; consider increasing the timeout |
| `SERVICE_UNAVAILABLE` | 503 from upstream | Exponential backoff |
| `SERVER_ERROR` | 500 / 502 / 504 generic server error | Exponential backoff |

### Permanent (do NOT retry — surface to the user)

| Code | When | What to do |
|---|---|---|
| `UNAUTHORIZED` | 401 — bad/expired API key | Tell the user to check `FLOOP_API_KEY` |
| `FORBIDDEN` | 403 — key doesn't have access to that resource | Tell the user; check team scope |
| `NOT_FOUND` | 404 — project / key / subdomain doesn't exist | Confirm the ref the user gave you |
| `CONFLICT` | 409 — subdomain taken, name collision | Suggest an alternative |
| `VALIDATION_ERROR` | 400 / 422 — bad input | Surface the message; fix the input |
| `LIMIT_EXCEEDED` | 403 — out of credits / over plan limits | Direct the user to `usage_summary` and the upgrade page |
| `BUILD_FAILED` | Project entered `failed` terminal state | Surface the build message; suggest refine or cancel+retry |
| `BUILD_CANCELLED` | Project was cancelled | Don't retry automatically |
| `SECRET_DETECTED` | A refinement message contained an apparent API key / token | Strip the secret from the message and resend |

### Special cases

- `UNKNOWN` / `<server-defined-code>` — codes the SDK doesn't recognise
  pass through verbatim. Don't retry by default.

## Backoff pattern

```
attempt 1: wait 250 ms + jitter
attempt 2: wait 500 ms + jitter
attempt 3: wait 1 s + jitter
attempt 4: wait 2 s + jitter
attempt 5: wait 4 s + jitter (max 30 s, then give up)
```

…unless the server provided `retryAfterMs` (parsed from `Retry-After`
header — handles both delta-seconds AND HTTP-date), in which case use
that value directly. The header trumps your own backoff schedule.

```ts
// Node SDK pattern (works the same in every other SDK)
import { FloopError } from "@floopfloop/sdk";

const RETRYABLE = new Set([
  "RATE_LIMITED", "NETWORK_ERROR", "TIMEOUT",
  "SERVICE_UNAVAILABLE", "SERVER_ERROR",
]);

async function withRetry<T>(fn: () => Promise<T>, maxAttempts = 5): Promise<T> {
  for (let attempt = 1; ; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (!(err instanceof FloopError) || !RETRYABLE.has(err.code) || attempt >= maxAttempts) {
        throw err;
      }
      const serverHint = err.retryAfterMs;
      const expoBackoff = Math.min(30_000, 250 * 2 ** (attempt - 1));
      await new Promise(r => setTimeout(r, (serverHint ?? expoBackoff) + Math.random() * 250));
    }
  }
}
```

## Gotchas

- **Don't retry `VALIDATION_ERROR`, `UNAUTHORIZED`, `FORBIDDEN`, or
  `NOT_FOUND`.** They won't fix themselves — you'll just burn rate-limit
  budget and hide the real error from the user.
- **`Retry-After` is in seconds in some SDKs, milliseconds in others.**
  Node and Python normalise to ms (`retryAfterMs`); Ruby and PHP keep
  the wire format (seconds, `retryAfter`). The MCP error string format
  is consistent regardless.
- **`NETWORK_ERROR` could be a real outage** — surface to the user
  after `maxAttempts` rather than swallowing forever.
- **Cancellation matters.** If the user is in a chat that gets
  cancelled mid-retry, abort the retry loop. The Node SDK's
  `AbortSignal` propagates through; Python uses `httpx.Timeout` /
  signal handlers.
- **If you see `SECRET_DETECTED`, the BACKEND rejected your message
  for containing a secret-shaped string** (API key prefix, JWT, etc.).
  Don't retry verbatim; ask the user to redact the secret first.
