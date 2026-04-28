# codex-image

Minis 本地图片技能，默认直接走 Minis 原生 `minis-model-use`。

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

`image2 画` 等价于：

```bash
minis-model-use run --model gpt-image-2 --endpoint auto
```

可选环境变量：`IMAGE2_MINIS_MODEL`、`IMAGE2_MINIS_ENDPOINT`。
