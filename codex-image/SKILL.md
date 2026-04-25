---
name: codex-image
local: true
source: https://github.com/cc166/minis-codex-image-skill
upstream_policy: overwrite-from-user-repo-only
description: Generate or edit images with gpt-image-2 through the user's OpenAI-compatible Images API. Use this skill whenever the user asks to draw/create/generate/edit images, says image2, gpt-image-2, OpenAI image API, codex image, or ChatGPT image generation. Prefer `image2 画/改`.
---

# codex-image

Local Minis skill for image generation/editing with `gpt-image-2`.

Source of truth: <https://github.com/cc166/minis-codex-image-skill>

## Use

```bash
image2 画 "提示词" [out.png]
image2 改 input.png "修改要求" [out.png]
```

- Relative filenames resolve under `/var/minis/attachments/`.
- `image2 "prompt"` equals `image2 画 "prompt"`.
- `image2` auto-loads `/etc/profile` env variables.
- Text-to-image uses retries for flaky gateways.

## Environment

- `OPENAI_API_KEY` — required
- `OPENAI_BASE_URL` — optional; default `https://api.openai.com/v1`; gateway URLs usually include `/v1`
- `OPENAI_IMAGE_MODEL` — optional; default `gpt-image-2`

Never print secret values. Only check set/not-set.

## Advanced

```bash
python3 /var/minis/skills/codex-image/scripts/openai_image_api.py gen "prompt" -o /var/minis/attachments/out.png --retries 6
python3 /var/minis/skills/codex-image/scripts/openai_image_api.py edit --image /var/minis/attachments/in.png "edit" -o /var/minis/attachments/out.png
```

The script supports OpenAI-compatible `/images/generations` and `/images/edits`, saves `b64_json` or URL responses, and tolerates transient `502` / `IncompleteRead` gateway issues.

## Fallback

If the user API is unavailable and the user wants ChatGPT-session fallback, use:

```bash
python3 /var/minis/skills/codex-image/scripts/codex_image.py "prompt" -o /var/minis/attachments/out.png
python3 /var/minis/skills/codex-image/scripts/codex_image_edit.py "edit" --image /var/minis/attachments/in.png -o /var/minis/attachments/out.png
```
