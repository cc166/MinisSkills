# minis-codex-image-skill

A standalone Minis skill for image generation/editing with `gpt-image-2`.

Source: <https://github.com/cc166/MinisSkills/tree/main/codex-image>

## Install

```bash
git clone https://github.com/cc166/MinisSkills.git /tmp/MinisSkills
sh /tmp/MinisSkills/codex-image/scripts/install.sh
```

## Use

```bash
image2 画 "提示词" [out.png]
image2 改 input.png "修改要求" [out.png]
```

Set `OPENAI_API_KEY`; optionally set `OPENAI_BASE_URL` and `OPENAI_IMAGE_MODEL`.
