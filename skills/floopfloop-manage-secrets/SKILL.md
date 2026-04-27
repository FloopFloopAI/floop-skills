---
name: floopfloop-manage-secrets
description: Use when the user wants to add, list, or remove environment secrets on a FloopFloop project — Stripe keys, database URLs, OAuth client secrets. Covers the write-only nature of the API, rotation patterns, and the destructive-hint warning hosts should surface.
---

# Managing FloopFloop project secrets

A FloopFloop project secret is a key/value env var that the deployed
runtime can read but no one (including the user) can read back over the
API. The store is write-only: list returns names + last-four characters,
never the full value.

## The three operations

| Tool | What it does | Hint |
|---|---|---|
| `list_secrets` | Returns `[{key, lastFour, createdAt, updatedAt}, ...]` | Read-only, idempotent |
| `set_secret` | Create OR overwrite a secret. No "update" — set is upsert. | `destructiveHint: true` |
| `remove_secret` | Delete by key | `destructiveHint: true` |

The MCP marks `set_secret` and `remove_secret` as `destructiveHint: true`
because both irrecoverably change project state — hosts should ask the
user to confirm before running them, especially if the project is in
production.

## The flow for adding a secret

1. **Confirm the project ref** (id or subdomain). Use `list_projects` if
   the user gave you a partial name.
2. **Run `list_secrets`** to see what's already set. If the key exists,
   warn the user that `set_secret` will overwrite — you can't recover
   the old value.
3. **Call `set_secret`** with `{ref, name, value}`. Returns the
   metadata; the value is never echoed back.
4. **Trigger a refine or wait for the next deploy** — secrets are read
   at deploy time, not in real time. The current `live` version
   doesn't see the new secret until the next build.

```jsonl
{"tool":"list_secrets","args":{"ref":"purr-press"}}
→ [{"key":"STRIPE_SECRET_KEY","lastFour":"_abc","createdAt":"...","updatedAt":"..."}]

{"tool":"set_secret","args":{"ref":"purr-press","name":"STRIPE_SECRET_KEY","value":"sk_live_..."}}
→ {"key":"STRIPE_SECRET_KEY","lastFour":"_xyz","createdAt":"...","updatedAt":"..."}

{"tool":"remove_secret","args":{"ref":"purr-press","name":"OLD_API_KEY"}}
→ {"success":true,"existed":true}
```

## Rotation pattern

To swap an old secret for a new one without downtime:

1. `set_secret` with the new value (this overwrites in place).
2. Trigger a `refine_project` with a no-op message ("Update environment")
   to redeploy with the new value picked up.
3. Verify the deployed app works against the new credential.
4. Revoke the old credential at the upstream provider (Stripe, AWS, etc.).

The order matters: rotate UPSTREAM last, after FloopFloop is using the
new value. Otherwise the live site has a window of broken auth.

## Gotchas

- **You CANNOT read back a secret value.** If the user asks "what's the
  value of `STRIPE_SECRET_KEY`?" tell them they need to look it up at
  the upstream provider — FloopFloop only shows the last 4 characters.
- **`set_secret` is upsert with no version history.** Overwriting loses
  the old value. If the user might want to revert, ask them to record
  it locally first.
- **A deployed project doesn't pick up new secrets until the next
  build.** Setting a secret without redeploying = no effect. Pair
  `set_secret` with a `refine_project` (even a trivial one) to force a
  redeploy.
- **Don't put secret values in the refinement `message`.** The backend
  has secret-detection (`SECRET_DETECTED` error) that rejects messages
  containing API-key-shaped strings — protects users from accidentally
  pasting secrets into chat history.
- **Project secrets are project-scoped, not user-scoped.** If the user
  has 5 projects all using the same Stripe key, you set it 5 times.
  There's no shared-secret feature today.
- **Secret keys (the `name` field) are case-sensitive** and follow env-var
  conventions: `UPPER_SNAKE_CASE`. The backend doesn't enforce this but
  the deployed runtime expects it.

## SDK fallback

```ts
// Node
const secrets = await floop.secrets.list("purr-press");
await floop.secrets.set("purr-press", "STRIPE_SECRET_KEY", "sk_live_...");
await floop.secrets.remove("purr-press", "OLD_API_KEY");
```

```python
# Python
secrets = floop.secrets.list("purr-press")
floop.secrets.set("purr-press", "STRIPE_SECRET_KEY", "sk_live_...")
floop.secrets.remove("purr-press", "OLD_API_KEY")
```
