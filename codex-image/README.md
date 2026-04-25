# codex-image

Minis 本地图片技能，使用 Minis 内置 image-output 模型 / `gpt-image-2` 生成与编辑图片。

来源：<https://github.com/cc166/MinisSkills/tree/main/codex-image>

## 安装

```bash
git clone https://github.com/cc166/MinisSkills.git /tmp/MinisSkills
sh /tmp/MinisSkills/codex-image/scripts/install.sh
```

## 用法

```bash
image2 画 "提示词" [输出.png]
image2 改 输入图.png "修改要求" [输出.png]
```

`image2 画` 默认使用 Minis App 自带 `minis-model-use` 调用你配置的 `gpt-image-2 --endpoint auto`；失败后回退到 `OPENAI_API_KEY` + OpenAI-compatible Images API，并在 fallback 链路用 `gpt-5.4` 增强提示词。

可选环境变量：`IMAGE2_MINIS_MODEL`、`IMAGE2_USE_MINIS`、`OPENAI_BASE_URL`、`OPENAI_IMAGE_MODEL`、`OPENAI_PROMPT_MODEL`、`OPENAI_IMAGE_ENDPOINT`。
