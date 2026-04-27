---
name: floopfloop-upload-attachment
description: Use when the user references a local file (screenshot, PDF, CSV, image) in a FloopFloop refinement — "make the homepage look like this mockup", "use this CSV as seed data", etc. Walks through the two-step upload + refine flow with attachment validation rules.
---

# Uploading an attachment to a FloopFloop refinement

The attachment flow is two-stop: upload bytes via `upload_from_path`,
then thread the returned `UploadedAttachment` into a `refine_project`
call.

## The flow

1. **Get the file path from the user.** The MCP host (Claude Desktop,
   Cursor, Zed, …) runs with the user's filesystem permissions, so an
   absolute or relative path works.

2. **Call `upload_from_path`.** It validates the file extension, presigns
   an S3 slot via the FloopFloop API, PUTs the bytes directly to S3, and
   returns an `UploadedAttachment` (`{key, fileName, fileType, fileSize}`).

3. **Pass the attachment to `refine_project`** as `attachments: [<that obj>]`.
   Up to 5 attachments per refinement; the build sees them alongside the
   text message.

## Allowed file types

`png`, `jpg/jpeg`, `gif`, `svg`, `webp`, `ico`, `pdf`, `txt`, `csv`,
`doc`, `docx`. Max 5 MB per file. The MCP validates client-side before
hitting the network, so bad inputs throw `VALIDATION_ERROR` immediately.

## Example

```jsonl
{"tool":"upload_from_path","args":{"filePath":"./mockup.png"}}
→ {"key":"uploads/u_abc/f_xyz/mockup.png","fileName":"mockup.png","fileType":"image/png","fileSize":1234567}

{"tool":"refine_project","args":{
  "ref":"purr-press",
  "message":"Make the homepage hero look like this mockup. Match the colour palette and the rounded card layout.",
  "attachments":[{"key":"uploads/u_abc/f_xyz/mockup.png","fileName":"mockup.png","fileType":"image/png","fileSize":1234567}],
  "wait":true
}}
→ {"id":"p_abc","status":"live","url":"https://purr-press.floop.tech",...}
```

## Gotchas

- **Pass the `UploadedAttachment` exactly as returned.** The backend
  validates `att.key.startsWith("uploads/<userId>/")` — if you build the
  object yourself with a guessed key, it gets silently dropped.
- **Attachments only flow through `refine`, not `create_project`.** If
  the user wants to anchor a brand-new project against an image, create
  with a text prompt first, then refine with the attachment as a
  follow-up.
- **5 MB is a hard ceiling.** Don't try to compress on the fly — ask
  the user to provide a smaller file or describe the relevant content
  in text.
- **Don't upload the same file twice.** Re-use the `UploadedAttachment`
  across multiple refinements if needed; the backend doesn't dedupe.
- **The MCP doesn't currently expose `upload_from_bytes`.** If the
  attachment isn't on disk (e.g. you generated it in memory), write it
  to a tempfile first, then call `upload_from_path`.

## SDK fallback

```ts
// Node
import { readFile } from "node:fs/promises";

const bytes = await readFile("./mockup.png");
const attachment = await floop.uploads.create({
  fileName: "mockup.png",
  file: bytes,
});
await floop.projects.refine("purr-press", {
  message: "Make the homepage hero look like this mockup.",
  attachments: [attachment],
  wait: true,
});
```

```python
# Python
with open("./mockup.png", "rb") as f:
    attachment = floop.uploads.create(file_name="mockup.png", file=f.read())
floop.projects.refine(
    "purr-press",
    message="Make the homepage hero look like this mockup.",
    attachments=[attachment],
    wait=True,
)
```
