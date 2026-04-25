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

需要设置 `OPENAI_API_KEY`；可选设置 `OPENAI_BASE_URL`、`OPENAI_IMAGE_MODEL`。
