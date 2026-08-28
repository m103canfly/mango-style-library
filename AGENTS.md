# mango-style-library — Agent 入口

星露谷物语风格俯视 2D 像素游戏的主美术资产库 skill：批量产出风格统一的建筑/人物/植物/装饰/道具/食物/UI/神秘道具（诡秘之主 22 途径）/载具动物/VFX 素材，内置美术基准、《诡秘之主》九国地域标准、逐张验收、美术审查与 Godot 直出管线。

## 何时使用

- 做俯视 2D 像素游戏开发，要批量生成同一风格成套资产
- 要可直接导入 Godot 的素材（tile/角色/建筑/图标/载具等规格化 PNG）
- 要把场景效果图拆成资产库

## 使用方式（必读顺序）

1. 先读本目录 `SKILL.md`（完整工作流与 Pitfalls）
2. 两大全局基准文件：`references/art-direction.md`（调色板/尺寸比例/纸娃娃画布/时段罩色）、`references/world-nations.md`（九国注入块）
3. 按资产类别读对应 references 文件（characters / architecture-tiles / furniture-decor-plants / props-ui / beyonder-items / vehicles-animals / vfx-weather）

## 关键规则

- **图像生成只走 `scripts/gen_image.sh`**，不要直接调任何厂商 API；后端配置见 `references/harness-setup.md`（kimi 默认 / openai / deepseek）
- 生成后必须逐张验收（read 图，对照类别清单如实报告偏差），偏差按该类别"修方"重跑
- 批量产出后跑美术审查：`scripts/palette_audit.py` + `references/art-review.md` 闭环
- **定位红线**：含 HUD 的场景实机演示图是内部审查标准，不进引擎、不对外展示；对外交付只有 `godot_assets/` 里经 `scripts/godot_export.py` 处理的资产精灵
- 导出 Godot 资产：`python3 scripts/godot_export.py <输入.png> <类别> <输出目录> --name slug`（类别与尺寸见脚本 docstring）

## 各 harness 安装

- **kimi / Kimi Code**：skill 目录加入 skills 路径即用（原生格式）
- **codex**：本 `AGENTS.md` 即入口；`export GEN_IMAGE_BACKEND=openai OPENAI_API_KEY=...`
- **deepseek**：本 `AGENTS.md` 即入口；图像后端按 `references/harness-setup.md` 二选一配置
