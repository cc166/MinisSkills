# codex-image

本地图片生成技能。

## 用法

```bash
image2 画 "提示词" [输出.png]
```

快速触发词：`image2画`

默认流程：

```text
gpt-5.5 /v1/responses + image_generation tool
```

失败时回退：

```text
minis-model-use run --model gpt-image-2 --endpoint auto
```
