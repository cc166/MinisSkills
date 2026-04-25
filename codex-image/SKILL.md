---
name: codex-image
version: 1.0.1
local: true
source: https://github.com/cc166/MinisSkills/tree/main/codex-image
source_url: https://github.com/cc166/MinisSkills/tree/main/codex-image
repository: https://github.com/cc166/MinisSkills
homepage: https://github.com/cc166/MinisSkills/tree/main/codex-image
upstream_policy: overwrite-from-user-repo-only
description: 使用 gpt-image-2 进行图片生成与图片编辑的本地技能。用户说“画图、生成图片、改图、P图、image2、gpt-image-2、OpenAI 图片 API、Codex 图片”时触发；默认使用 `image2 画/改`，优先走用户自己的 OpenAI-compatible API。
---

# codex-image

使用 `gpt-image-2` 生成/编辑图片的 Minis 本地技能。

来源：<https://github.com/cc166/MinisSkills/tree/main/codex-image>

## 用法

```bash
image2 画 "提示词" [输出.png]
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
- `image2` 会自动读取 `/etc/profile` 里的环境变量。
- 生成图片时已内置多次重试，兼容部分网关的 `502` / `IncompleteRead`。

## 环境变量

- `OPENAI_API_KEY`：必需
- `OPENAI_BASE_URL`：可选，默认 `https://api.openai.com/v1`；中转/New API/one-api 通常需要带 `/v1`
- `OPENAI_IMAGE_MODEL`：可选，默认 `gpt-image-2`

不要打印密钥值，只检查 set/not_set。

## 高级命令

```bash
python3 /var/minis/skills/codex-image/scripts/openai_image_api.py gen "prompt" -o /var/minis/attachments/out.png --retries 6
python3 /var/minis/skills/codex-image/scripts/openai_image_api.py edit --image /var/minis/attachments/in.png "edit" -o /var/minis/attachments/out.png
```

## 备用 Codex 链路

只有在用户 API 不可用且用户明确要 ChatGPT Session/Codex 回退时使用：

```bash
python3 /var/minis/skills/codex-image/scripts/codex_image.py "prompt" -o /var/minis/attachments/out.png
python3 /var/minis/skills/codex-image/scripts/codex_image_edit.py "edit" --image /var/minis/attachments/in.png -o /var/minis/attachments/out.png
```
