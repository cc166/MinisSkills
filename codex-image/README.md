# codex-image

Minis 本地图片技能，使用 `gpt-image-2` 生成/编辑图片。

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

`image2 画` 默认先用 `gpt-5.4` 增强提示词，再交给 `gpt-image-2` 出图；端点默认 `auto`，优先 `/v1/images/generations`，失败时可回退 `/v1/chat/completions`。

需要设置 `OPENAI_API_KEY`；可选设置 `OPENAI_BASE_URL`、`OPENAI_IMAGE_MODEL`、`OPENAI_PROMPT_MODEL`、`OPENAI_IMAGE_ENDPOINT`。

说明：生成接口优先用 `curl` 读取大体积 chunked 响应，避免 iSH Python `http.client` 对部分网关出现空响应或 `IncompleteRead`。
