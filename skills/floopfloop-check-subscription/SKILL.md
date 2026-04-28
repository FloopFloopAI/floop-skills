---
name: floopfloop-check-subscription
description: Use when the user asks about their FloopFloop plan, billing period, credit balance, or whether they've hit limits — "what plan am I on?", "how many credits do I have left?", "when does my subscription renew?", "am I about to hit my limit?". Distinguishes the current_subscription tool (plan tier, billing) from usage_summary (current-period consumption).
---

# Checking a FloopFloop subscription / plan / credits

The MCP exposes **two** read-only tools that overlap on plan-and-credit data — pick the right one based on what the user is actually asking.

## The two tools

| Tool | Returns | Use when the user asks… |
|---|---|---|
| `current_subscription` | Plan tier itself: `planName`, `planDisplayName`, `priceMonthly`, `priceAnnual`, `billingPeriod`, `currentPeriodStart`, `currentPeriodEnd`, `canceledAt`, `monthlyCredits`, `maxProjects`, `maxStorageMb`, `maxBandwidthMb`, `creditRolloverMonths`, `features`. Plus a `credits` block: `current`, `rolledOver`, `total`, `rolloverExpiresAt`, `lifetimeUsed`. | "What plan am I on?", "When does my subscription renew?", "How many credits do I have?", "Am I cancelled?" |
| `usage_summary` | Current-period consumption: `plan` (subset of fields), `credits`, `currentPeriod` (`projectsCreated`, `buildsUsed`, `refinementsUsed`, `storageUsedMb`, `bandwidthUsedMb`). | "Am I about to hit my limit?", "How much storage am I using?", "How many builds have I used this month?" |

Some overlap on `monthlyCredits` and `maxProjects`, but the audiences are different. Don't call both unless the user genuinely needs both views.

## When BOTH `subscription` and `credits` are null

`current_subscription` returns `{ subscription: null, credits: null }` for users who don't have a subscription record yet — most often:

- **Mid-signup:** account exists but the subscription row hasn't been created.
- **Cancelled with no grace credits remaining:** subscription was deleted, no rollover credits left.

Tell the user "no active subscription found" rather than crashing on the null. Suggest visiting `https://www.floopfloop.com/account/billing` to start or restore a subscription.

## Example

```jsonl
{"tool":"current_subscription","args":{}}
→ {
    "subscription": {
      "status": "active",
      "billingPeriod": "monthly",
      "currentPeriodStart": "2026-04-01T00:00:00Z",
      "currentPeriodEnd": "2026-05-01T00:00:00Z",
      "canceledAt": null,
      "planName": "pro",
      "planDisplayName": "Pro",
      "priceMonthly": 29,
      "priceAnnual": 290,
      "monthlyCredits": 500,
      "maxProjects": 50,
      ...
    },
    "credits": {
      "current": 423,
      "rolledOver": 50,
      "total": 473,
      "rolloverExpiresAt": "2026-05-01T00:00:00Z",
      "lifetimeUsed": 1234
    }
  }
```

A useful summary to give the user: "You're on the Pro plan ($29/mo, renewing 2026-05-01). 473 credits available (423 current + 50 rolled-over expiring 2026-05-01). Lifetime usage: 1,234 credits."

## Gotchas

- **Don't paraphrase prices in a different currency.** `priceMonthly: 29` is dollars (US). If the user is in a region where they pay in another currency, FloopFloop bills in USD regardless — don't invent a conversion.
- **`features: {}` is allowed.** The `features` field is an opaque dict the SDK passes through. If empty, the user is on a plan with no special features flagged. Don't assume "no features" means "broken plan."
- **Don't call `remove_api_key` to "rotate" a subscription.** Subscriptions and API keys are independent — cancelling one doesn't touch the other. If the user wants to cancel their subscription, direct them to the web console.
- **`current_subscription` does NOT include the user's email or account info.** Pair it with `whoami` if the user wants both ("am I logged in as the right user, and what's my plan?").

## SDK fallback

```ts
// Node
const result = await floop.subscriptions.current();
if (!result.subscription) {
  console.log("No active subscription");
} else {
  console.log(`${result.subscription.planDisplayName}: $${result.subscription.priceMonthly}/mo, renews ${result.subscription.currentPeriodEnd}`);
  console.log(`Credits: ${result.credits?.total ?? 0} (${result.credits?.current ?? 0} current + ${result.credits?.rolledOver ?? 0} rolled over)`);
}
```

```python
# Python
result = floop.subscriptions.current()
if not result.get("subscription"):
    print("No active subscription")
else:
    s, c = result["subscription"], result.get("credits", {})
    print(f"{s['planDisplayName']}: ${s['priceMonthly']}/mo, renews {s['currentPeriodEnd']}")
    print(f"Credits: {c.get('total', 0)} ({c.get('current', 0)} current + {c.get('rolledOver', 0)} rolled over)")
```

The other 6 SDKs (Go, Rust, Ruby, PHP, Swift, Kotlin) follow the same shape — `client.subscriptions().current()` (Go/PHP) or `client.subscriptions.current` (Ruby/Kotlin/Swift) or `client.subscriptions().current().await` (Rust).
