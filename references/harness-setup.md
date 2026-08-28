# 各 Harness 接入配置（图像后端）

skill 的全部生成调用收敛在 `scripts/gen_image.sh` 一个入口，接新 harness = 给它配一个图像后端。后端选择优先级：`GEN_IMAGE_BACKEND` 环境变量 > 自动探测（kimi 插件目录 → OPENAI_API_KEY → DEEPSEEK_API_KEY）。

## kimi / Kimi Code（默认，已全量验证）

- 后端：`kimi`（自动探测到 `/app/.agents/plugins/image_generation` 即用）
- 首次使用：`scripts/gen_image.sh ensure-deps`
- 参考图规则：必须是公网 URL，本地图先 `scripts/gen_image.sh image-to-url --image-path <图>` 转换
- 安装：skill 目录加入 skills 搜索路径即可（本环境原生）

## codex（OpenAI）

- 配置：`export GEN_IMAGE_BACKEND=openai` + `export OPENAI_API_KEY=sk-...`
- 走 OpenAI Images API（gpt-image-1）：透明底、1:1/3:2/2:3/16:9/9:16 比例映射已内置；带 `--reference-image` 时自动切 edits 端点（本地路径或 URL 均可，无需 image-to-url）
- 注意：该后端按官方文档端点实现，未在本环境实测——接入后先用一张 1:1 小图验证再批量
- 安装：让 AGENTS 读取 skill 根目录的 `AGENTS.md`（Codex 自动识别 AGENTS.md），或直接引用 SKILL.md

## deepseek harness

- DeepSeek 官方公开 API 目前**没有图像生成端点**，两条路：
  1. 自建 OpenAI 兼容图像端点（如 Janus 服务）：`export GEN_IMAGE_BACKEND=deepseek` + `DEEPSEEK_IMAGE_ENDPOINT=https://.../images/generations`（+ `DEEPSEEK_API_KEY`）
  2. 或复用 OpenAI 后端：`GEN_IMAGE_BACKEND=openai` + `OPENAI_API_KEY`
- 无图像后端时，skill 的纯本地工具（`scripts/godot_export.py`、`scripts/palette_audit.py`）仍可独立使用，不依赖生图
- 安装：同 codex，经 `AGENTS.md` 接入

## 后端契约（要接第 4 个 harness 时）

任何实现同一 CLI 签名的程序都可作为后端：`generate --description --ratio --resolution --background --reference-image×N --output`，成功即在 `--output` 写出图片。写一个新 case 分支进 `gen_image.sh` 即可，skill 其余部分零改动。
