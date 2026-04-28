# codex-image

本地 `gpt-image-2` 图片生成技能。

## 用法

```bash
image2 画 "提示词" [输出.png]
```

快速触发词：`image2画`

默认流程：

```text
gpt-5.4 优化提示词 → minis-model-use run --model gpt-image-2 --endpoint auto
```

可用 `IMAGE2_OPTIMIZE_PROMPT=0` 跳过提示词优化。
