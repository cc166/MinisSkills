---
name: codex-image
version: 1.0.7
local: true
source: https://github.com/cc166/MinisSkills/tree/main/codex-image
source_url: https://github.com/cc166/MinisSkills/tree/main/codex-image
repository: https://github.com/cc166/MinisSkills
homepage: https://github.com/cc166/MinisSkills/tree/main/codex-image
upstream_policy: overwrite-from-user-repo-only
description: 使用 gpt-image-2 / image_generation 工具生成图片的本地技能。用户说“image2画”“image2 画”“用 image2 画”“gpt-image-2 画图”“生成图片”“画图”时触发。默认执行 `image2 画 "提示词"`：使用 OpenAI-compatible `/v1/responses`，模型 `gpt-5.5`，工具 `image_generation`；失败时回退 Minis App 原生 `minis-model-use`。
---

# codex-image

使用 OpenAI-compatible `/v1/responses` + `image_generation` 工具生成图片。

本地快速触发词：`image2画`

## 用法

```bash
image2 画 "提示词" [输出.png]
```

默认流程：

```text
gpt-5.5 /v1/responses + tools=[{"type":"image_generation"}]
```

失败时回退：

```bash
minis-model-use run --model gpt-image-2 --endpoint auto
```

## 可选环境变量

- `IMAGE2_RESPONSES_MODEL=gpt-5.5`：responses 出图模型
- `IMAGE2_RESPONSES_BASE_URL=https://ai.input.im/v1`：responses base URL；未设置时优先 `OPENAI_BASE_URL`，否则用 `https://ai.input.im/v1`
- `IMAGE2_USE_RESPONSES=0`：禁用 responses，直接走 Minis fallback
- `IMAGE2_MINIS_MODEL=gpt-image-2`：fallback 模型
- `IMAGE2_MINIS_ENDPOINT=auto`：fallback 端点

## 工作流

1. 用户说 `image2画...`、`image2 画...` 或要求画图时，提取图片提示词。
2. 运行：
   ```bash
   image2 画 "提示词" /var/minis/attachments/out.png
   ```
3. 只确认文件存在，不默认视觉检查。
4. 直接用 Markdown 图片返回。
