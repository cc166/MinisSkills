# codex-image

本地图片生成技能：**干净调用 `/responses` + SSE 流式 `image_generation` tool**。

## 用法

```bash
image2 画 "提示词" [输出.png]
image2 改 输入图 "修改要求" [输出.png]
```

## 核心脚本

- 入口：`bin/image2`
- 核心：`scripts/image2_responses.py`

## 默认流程

```text
POST {IMAGE2_BASE_URL}/responses
Accept: text/event-stream
User-Agent: Minis image2-responses/1.0
stream: true
tools: [{"type":"image_generation"}]
→ 从 SSE 事件里提取 partial_image_b64/result/b64_json
→ 保存 PNG
→ 最终回复只返回图片
```

## 不做什么

- 不使用 `/v1/images/generations`
- 不使用 `/images/generations`
- 不用 `minis-model-use --endpoint auto/images-gen` 作为默认画图路径
- 不模拟网页登录：不发浏览器 UA，不发 Origin/Referer

## Token 控制

默认 payload 极简：`input/model/store/stream/tool_choice/tools`。不发送 `instructions/reasoning/include/parallel_tool_calls`，也不再每次生成随机 `prompt_cache_key`。

## 环境变量

```bash
IMAGE2_BASE_URL=https://ai.input.im
IMAGE2_API_KEY=...
# 可选覆盖模型：
IMAGE2_MODEL=gpt-5.5
# 或指定 key 所在变量：
IMAGE2_API_KEY_ENV=INPUT_API_KEY
```

默认 key 读取顺序：`IMAGE2_API_KEY` → `OPENAI_API_KEY` → `INPUT_API_KEY` → `CODEX_API_KEY`。
