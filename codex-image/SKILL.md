---
name: codex-image
version: 1.6.1
local: true
source: https://github.com/cc166/MinisSkills/tree/main/codex-image
source_url: https://github.com/cc166/MinisSkills/tree/main/codex-image
repository: https://github.com/cc166/MinisSkills
homepage: https://github.com/cc166/MinisSkills/tree/main/codex-image
upstream_policy: overwrite-from-user-repo-only
description: 干净的 `/responses` + SSE 流式 `image_generation` 本地画图技能。用户说“image2画 / 画图 / 生成图片 / 改图 / P图”时触发。默认只出图，不附验证摘要；不模拟网页登录，不使用浏览器 UA/Origin/Referer；不走 `/v1/images/generations`。
---

# codex-image

干净调用 OpenAI-compatible `/responses` + SSE 流式 `image_generation` tool 生成和编辑图片。

## 硬规则

- **默认且唯一主路径**：`POST {IMAGE2_BASE_URL}/responses` 或 `IMAGE2_RESPONSES_URL`。
- **必须 `stream: true`**，接收 `text/event-stream`。
- **必须通过 tools 调用图片生成**：`tools=[{"type":"image_generation"}]`。
- **禁止使用** `/v1/images/generations`、`/images/generations`、`images-gen`、`minis-model-use --endpoint auto/images-gen` 作为默认绘图路径。
- **不要模拟网页登录**：不发送浏览器伪装 UA，不发送 `Origin` / `Referer`；默认 UA 为 `Minis image2-responses/1.0`。
- **输出规则**：用户让画图时，成功后只返回 Markdown 图片，不附 JSON、验证字段、文件格式、尺寸等验证摘要；失败才简短报错。

## 当前脚本

- 入口：`/var/minis/skills/codex-image/bin/image2`，已同步到 `/usr/local/bin/image2`
- 核心：`/var/minis/skills/codex-image/scripts/image2_responses.py`
- 旧脚本 `generate_image.py` 不再作为入口使用。

## 模型选择

- 默认不硬编码模型；核心脚本读取 `minis-model-use list` 中 App 可见模型列表，选择第一个支持 `image_output` 的模型 ID。
- 只有显式设置 `IMAGE2_MODEL` 时才覆盖当前 App 模型。

## 用法

```bash
image2 画 "提示词" [输出.png]
image2 改 输入图片 "修改要求" [输出.png]
```

## 环境变量

- `IMAGE2_MODEL`：可选；显式指定 responses 模型。不设则跟随 Minis App 模型列表当前优先模型。
- `IMAGE2_BASE_URL=https://ai.input.im`：base URL，会自动拼 `/responses`。
- `IMAGE2_RESPONSES_URL`：完整 responses URL；优先级高于 `IMAGE2_BASE_URL`。
- `IMAGE2_USER_AGENT`：可选自定义 UA；默认 `Minis image2-responses/1.0`。

默认 key 读取顺序：`IMAGE2_API_KEY` → `OPENAI_API_KEY` → `INPUT_API_KEY` → `CODEX_API_KEY`。

如果 key 存在其他环境变量里：

```bash
IMAGE2_API_KEY_ENV=你的变量名 image2 画 "提示词"
```

## Token 控制

默认 payload 保持极简，只发送：

```json
["input", "model", "store", "stream", "tool_choice", "tools"]
```

默认不发送 `instructions`、`reasoning`、`include`、`parallel_tool_calls`，也不再每次生成随机 `prompt_cache_key`。

- `IMAGE2_PROMPT_PRESET=character`：轻量补充提示词；可选 `character/portrait/scene/空值`。
- `IMAGE2_PROMPT_CACHE_KEY`：可选固定缓存 key；默认不设置。
- `IMAGE2_REASONING_EFFORT`：默认不发送；只有显式设置时才加入 payload。
- `IMAGE2_DRY_RUN=1`：只验证 payload 和端点，不发请求；普通画图不要展示 dry-run 信息。
- `IMAGE2_DEBUG=1`：保存完整 SSE 日志。

## 工作流

1. 触发词：`image2画...`、`image2 画...`、`画图`、`生成图片`、`改图`、`P图`。
2. 提取提示词或编辑要求，少量补充画面词即可，不要大段扩写。
3. 执行 `image2 画 "提示词" /var/minis/attachments/out.png`。
4. 成功时从 JSON 结果中取 `path`，最终回复只放图片。
5. 不主动执行 `file` 等额外验证命令；不展示 backend/model/endpoint/token 等摘要。
