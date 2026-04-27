---
name: floopfloop-refine-project
description: Use when the user wants to change something about an existing FloopFloop project — copy edits, layout tweaks, new features, bug fixes. Explains the three response shapes (queued / processing / saved-only), when to use codeEditOnly for a 3-step shortcut, and how to wait for the follow-up build.
---

# Refining a FloopFloop project

`refine_project` sends a change request to an existing project. Unlike
`create_project`, the response is one of **three** shapes that depend on
the project's current state — pick the right next step based on which
shape came back.

## The three response shapes

| Response | Meaning | Next step |
|---|---|---|
| `{"processing": true, "deploymentId": "...", "queuePriority": N}` | Backend started a fresh build immediately | `wait_for_live` to know when it's done |
| `{"queued": true, "messageId": "..."}` | Project is currently building; your message is queued behind it | `wait_for_live` — when the current build finishes, the queued message is processed automatically |
| `{"queued": false}` | Saved as a chat message, no build was triggered | Nothing to wait for; the message is in the project's conversation history |

The third shape happens when the user's change is purely conversational
(asking a question rather than requesting code). The backend decides.

## codeEditOnly — the 3-step shortcut

For surface-level edits (copy edits, colour swaps, typo fixes, simple
text changes), pass `codeEditOnly: true`:

- **Build runs 3 steps instead of 6** (no replan, no redesign, no full
  redeploy — just an in-place patch).
- **Charges roughly half a refinement credit** (`CODE_EDIT` vs `REFINEMENT`
  cost on the backend).
- **Only meaningful once the project is `live`.** On a project that
  hasn't deployed yet, the flag is ignored and you get a normal initial
  build.

When NOT to use `codeEditOnly`: anything needing a redesign, a new
dependency, restructured routing, or new capabilities. The backend
won't promote a code-edit to a full refinement automatically — it just
runs the 3-step patch with limited tools, and you may end up paying for
a second refinement to redo the change properly.

## Example

```jsonl
{"tool":"refine_project","args":{"ref":"purr-press","message":"Change the hero headline from 'Welcome' to 'Hello there.'","codeEditOnly":true}}
→ {"processing":true,"deploymentId":"d_xyz","queuePriority":1}

{"tool":"wait_for_live","args":{"ref":"purr-press"}}
→ {"id":"p_abc","status":"live","url":"https://purr-press.floop.tech",...}
```

For threading attachments (screenshots, PDFs, CSVs) into a refinement,
read [floopfloop-upload-attachment](../floopfloop-upload-attachment/SKILL.md)
— `upload_from_path` produces an `UploadedAttachment` you pass as
`attachments: [...]` on `refine_project`.

## Gotchas

- **Always check the response shape before calling `wait_for_live`.**
  If you got `{"queued": false}`, `wait_for_live` will still complete
  (the project is already `live`) but you'll have wasted a poll loop.
- **`codeEditOnly` is one-way.** If you set it and the change actually
  needed a full refinement, you'll see degraded results, not an
  automatic retry.
- **Concurrent refines on the same project queue up.** If you fire
  three `refine_project` calls in quick succession, only the first
  triggers an immediate build; the others come back as `queued: true`
  and process in order.
- **`refine_project` is destructive in the sense that it changes the
  live site** once the build completes. Confirm with the user before
  refining a production project they care about.

## SDK fallback

```ts
// Node
const result = await floop.projects.refine("purr-press", {
  message: "Change the hero headline from 'Welcome' to 'Hello there.'",
  codeEditOnly: true,
  wait: true,  // SDK convenience: blocks until terminal
});
```

```python
# Python
result = floop.projects.refine(
    "purr-press",
    message="Change the hero headline from 'Welcome' to 'Hello there.'",
    code_edit_only=True,
    wait=True,
)
```
