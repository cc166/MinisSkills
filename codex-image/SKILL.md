---
name: codex-image
version: 1.0.4
local: true
source: https://github.com/cc166/MinisSkills/tree/main/codex-image
source_url: https://github.com/cc166/MinisSkills/tree/main/codex-image
repository: https://github.com/cc166/MinisSkills
homepage: https://github.com/cc166/MinisSkills/tree/main/codex-image
upstream_policy: overwrite-from-user-repo-only
description: 使用 gpt-image-2 生成图片的本地技能。用户说“image2画”“image2 画”“用 image2 画”“gpt-image-2 画图”“生成图片”“画图”时触发。默认直接执行 `image2 画 "提示词"`，该命令使用 Minis App 原生 `minis-model-use run --model gpt-image-2 --endpoint images-gen`。
---

# codex-image

使用 `gpt-image-2` 生成图片。这个本地版保持原 `codex-image` 的极简思路：**理解用户提示词 → 调用 image generation → 返回图片**。

本地快速触发词：`image2画`

## 用法

```bash
image2 画 "提示词" [输出.png]
```

等价于调用 Minis 原生模型：

```bash
minis-model-use run --model gpt-image-2 --endpoint images-gen
```

## 工作流

1. 用户说 `image2画...`、`image2 画...` 或要求画图时，提取图片提示词。
2. 运行：
   ```bash
   image2 画 "提示词" /var/minis/attachments/out.png
   ```
3. 确认图片文件存在。
4. 用 Markdown 图片返回：
   ```markdown
   ![图片](minis://attachments/out.png)
   ```

## 备注

- 默认端点：`images-gen`，更接近原技能的直接 image generation 链路。
- 如需 App 自动选择端点，可临时使用：
  ```bash
  IMAGE2_MINIS_ENDPOINT=auto image2 画 "提示词"
  ```
- 相对输出文件名默认保存到 `/var/minis/attachments/`。
