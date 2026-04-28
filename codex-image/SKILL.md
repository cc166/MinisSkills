---
name: codex-image
version: 1.0.3
local: true
source: https://github.com/cc166/MinisSkills/tree/main/codex-image
source_url: https://github.com/cc166/MinisSkills/tree/main/codex-image
repository: https://github.com/cc166/MinisSkills
homepage: https://github.com/cc166/MinisSkills/tree/main/codex-image
upstream_policy: overwrite-from-user-repo-only
description: 使用 gpt-image-2 进行图片生成与图片编辑的本地技能。用户说“画图、生成图片、改图、P图、image2、gpt-image-2、OpenAI 图片 API、Codex 图片”时触发；默认使用 `image2 画/改`。`image2 画` 贴近原 codex-image：直接调用 Minis App 自带 `minis-model-use run --model gpt-image-2 --endpoint images-gen`。
---

# codex-image

使用 `gpt-image-2` 生成/编辑图片的 Minis 本地技能。

来源：<https://github.com/cc166/MinisSkills/tree/main/codex-image>

## 用法

```bash
image2 画 "提示词" [输出.png]      # minis-model-use run --model gpt-image-2 --endpoint images-gen
image2 改 输入图.png "修改要求" [输出.png]
```

说明：

- `image2 画` 直接调用 Minis App 自带 `minis-model-use run --model gpt-image-2 --endpoint images-gen`。
- 这更接近原 `codex-image` 的直接 image_generation 工具链路，少一层自动端点判断，通常更直接。
- 如需让 App 自动切换端点，可临时使用：`IMAGE2_MINIS_ENDPOINT=auto image2 画 "提示词"`。
- 相对文件名默认在 `/var/minis/attachments/` 下读写。
- `image2 "提示词"` 等同于 `image2 画 "提示词"`。
- `image2` 会自动读取 `/etc/profile` 里的环境变量。

## 环境变量

- `IMAGE2_MINIS_MODEL`：可选，默认 `gpt-image-2`
- `IMAGE2_MINIS_ENDPOINT`：可选，默认 `images-gen`；可设为 `auto` 或 `chat`
- `OPENAI_API_KEY` / `OPENAI_BASE_URL`：仅在 `image2 改` 的 fallback 编辑链路需要

## 编辑

```bash
image2 改 input.png "去掉右下角 logo，其他不变" edited.png
```

当前 `image2 改` 仍走本地 OpenAI-compatible `/images/edits` 脚本；`image2 画` 已贴近原技能的直接 image generation 链路。
