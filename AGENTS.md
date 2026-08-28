# mango-style-library — Agent 入口

星露谷物语风格俯视 2D 像素游戏的项目级 AI Art Direction System：分类 Gold Anchors、九地区 Scene Bible、固定调色板、共享 transform、评分审查、provenance 与回归测试。

## 何时使用

- 做俯视 2D 像素游戏开发，要批量生成同一风格成套资产
- 要可直接导入 Godot 的素材（tile/角色/建筑/图标/载具等规格化 PNG）
- 要把场景效果图拆成资产库

## 使用方式（必读顺序）

1. 先读本目录 `SKILL.md`（完整工作流与 Pitfalls）
2. 全局基准：`references/art-direction.md`、`references/style-anchor-system.md`、`references/art-review.md`、`references/asset-provenance.md`
3. 先跑 `python scripts/validate_anchor_pack.py --strict`；未过时只能产出 candidate，不得标 production-ready
4. 地区资产读 `references/world-nations.md`，动画读 `references/character-motion-standard.md`，再按类别读对应配方

## 关键规则

- **图像生成只走 `scripts/gen_image.sh`**，不要直接调任何厂商 API；后端配置见 `references/harness-setup.md`（kimi 默认 / openai / deepseek）
- 生成后必须逐张验收（read 图，对照类别清单如实报告偏差），偏差按该类别"修方"重跑
- Scene Bible 是地域场景软参考，不能替代 character/architecture/environment/interior/ui Gold Anchor
- 纸娃娃层与动画帧必须走 `godot_export.py group`，共享 union bbox/scale/origin/baseline；禁止逐图 fit
- 批量产出后跑固定色板审查；动画另跑 `scripts/motion_audit.py`
- **定位红线**：含 HUD 的场景实机演示图是内部审查标准，不进引擎、不对外展示；对外交付只有 `godot_assets/` 里经 `scripts/godot_export.py` 处理的资产精灵
- 每个资产必须记录 prompt/model/backend/anchor/scene/palette/transform/review/version provenance
- 变更管线后运行 `bash scripts/run_art_regression.sh`

## 各 harness 安装

- **kimi / Kimi Code**：skill 目录加入 skills 路径即用（原生格式）
- **codex**：本 `AGENTS.md` 即入口；`export GEN_IMAGE_BACKEND=openai OPENAI_API_KEY=...`
- **deepseek**：本 `AGENTS.md` 即入口；图像后端按 `references/harness-setup.md` 二选一配置
