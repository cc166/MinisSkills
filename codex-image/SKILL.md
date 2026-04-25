---
name: codex-image
version: 1.0.1
local: true
source: https://github.com/cc166/MinisSkills/tree/main/codex-image
source_url: https://github.com/cc166/MinisSkills/tree/main/codex-image
repository: https://github.com/cc166/MinisSkills
homepage: https://github.com/cc166/MinisSkills/tree/main/codex-image
upstream_policy: overwrite-from-user-repo-only
description: 使用 gpt-image-2 / Minis 内置 image-output 模型进行图片生成与图片编辑的本地技能。用户说“画图、生成图片、改图、P图、image2、gpt-image-2、OpenAI 图片 API、Codex 图片”时触发；默认使用 `image2 画/改`，优先走 Minis App 自带 `minis-model-use` 图像输出，失败再回退用户自己的 OpenAI-compatible API。
---

# codex-image

使用 `gpt-image-2` / Minis 内置 image-output 模型生成/编辑图片的 Minis 本地技能。

来源：<https://github.com/cc166/MinisSkills/tree/main/codex-image>

## 用法

```bash
image2 画 "提示词" [输出.png]      # 默认优先 minis-model-use 内置 image-output，失败再回退 OpenAI Images API
image2 改 输入图.png "修改要求" [输出.png]
```

示例：

```bash
image2 画 "赛博朋克猫，霓虹灯，电影感" cat.png
image2 改 input.png "去掉右下角 logo，其他不变" edited.png
```

说明：

- 相对文件名默认在 `/var/minis/attachments/` 下读写。
- `image2 "提示词"` 等同于 `image2 画 "提示词"`。
- `image2 画` 默认优先调用 Minis App 自带 `minis-model-use` 的 image-output 模型（默认 `gpt-image-1.5`，可用 `IMAGE2_MINIS_MODEL=gpt-5.5` 调整）；失败后回退到 `OPENAI_API_KEY` + `/images/generations`，并在回退链路中用 `gpt-5.4` 增强提示词。
- `image2` 会自动读取 `/etc/profile` 里的环境变量。
- 生成接口支持 `images-gen / chat / auto`；默认 `auto`，优先 `/v1/images/generations`，失败时可回退 `/v1/chat/completions`。

## 环境变量

- `OPENAI_API_KEY`：必需
- `OPENAI_BASE_URL`：可选，默认 `https://api.openai.com/v1`；中转/New API/one-api 通常需要带 `/v1`
- `OPENAI_IMAGE_MODEL`：可选，默认 `gpt-image-2`
- `OPENAI_PROMPT_MODEL`：可选，默认 `gpt-5.4`，用于出图前增强提示词
- `IMAGE2_USE_MINIS`：可选，默认 `1`；设为 `0` 可禁用 Minis 内置图像模型，直接走 OpenAI fallback
- `IMAGE2_MINIS_MODEL`：可选，默认 `gpt-image-1.5`；也可设为 `gpt-5.5`
- `OPENAI_IMAGE_ENDPOINT`：可选，`auto` / `images-gen` / `chat`，fallback 链路默认 `auto`

不要打印密钥值，只检查 set/not_set。

## 高级命令

```bash
python3 /var/minis/skills/codex-image/scripts/openai_image_api.py gen "prompt" -o /var/minis/attachments/out.png --enhance --endpoint auto --retries 6
python3 /var/minis/skills/codex-image/scripts/openai_image_api.py edit --image /var/minis/attachments/in.png "edit" -o /var/minis/attachments/out.png
```

## 备用 Codex 链路

只有在用户 API 不可用且用户明确要 ChatGPT Session/Codex 回退时使用：

```bash
python3 /var/minis/skills/codex-image/scripts/codex_image.py "prompt" -o /var/minis/attachments/out.png
python3 /var/minis/skills/codex-image/scripts/codex_image_edit.py "edit" --image /var/minis/attachments/in.png -o /var/minis/attachments/out.png
```
