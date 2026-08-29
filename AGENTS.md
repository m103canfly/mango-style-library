# mango-style-library — Agent 入口

廷根项目级 AI Art Direction System：`tingen_pixel_v3_hd` 原生 1× 合同、分类 Gold Anchors、九地区 Scene Bible、材质子色板、评分审查、provenance 与回归测试。

## 何时使用

- 做俯视 2D 像素游戏开发，要批量生成同一风格成套资产
- 要按廷根 64×64 tile、64×96 人物和标准目录向 Godot 交付原生 1× PNG
- 要把场景效果图拆成资产库

## 使用方式（必读顺序）

1. 先读本目录 `SKILL.md`（完整工作流与 Pitfalls）
2. 全局基准：`profiles/tingen_pixel_v3_hd/profile.json`、`references/art-direction.md`、`references/style-anchor-system.md`、`references/art-review.md`、`references/asset-provenance.md`
3. 先跑 `python scripts/validate_project_profile.py --strict`；Anchor 或正式色板未过时只能产出 candidate
4. 地区资产读 `references/world-nations.md`，动画读 `references/character-motion-standard.md`，再按类别读对应配方

## 关键规则

- **图像生成只走 `scripts/gen_image.sh`**，不要直接调任何厂商 API；所有生成结果只能登记为 HD reference，不能缩小直交付
- 生成后必须逐张验收（read 图，对照类别清单如实报告偏差），偏差按该类别"修方"重跑
- Scene Bible 是地域场景软参考，不能替代 character/architecture/environment/interior/ui Gold Anchor
- HD 纸娃娃/动画参考必须走 `godot_export.py group` 做共享 transform 诊断；正式 64×96 帧不得经过 bbox/fit
- 批量产出后跑固定色板审查；动画另跑 `scripts/motion_audit.py`
- **定位红线**：含 HUD 的场景图和生成式图片都是内部参考；对外交付只能由 `package_asset.py` 打包并经 `validate_delivery.py` 复核
- 每个资产必须记录 prompt/model/backend/anchor/scene/palette/transform/review/version provenance
- 变更管线后运行 `bash scripts/run_art_regression.sh`

## 各 harness 安装

- **kimi / Kimi Code**：skill 目录加入 skills 路径即用（原生格式）
- **codex**：本 `AGENTS.md` 即入口；`export GEN_IMAGE_BACKEND=openai OPENAI_API_KEY=...`
- **deepseek**：本 `AGENTS.md` 即入口；图像后端按 `references/harness-setup.md` 二选一配置
