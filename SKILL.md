---
name: mango-style-library
description: 为星露谷式俯视 2D 游戏生产风格统一、可审计、可回归的项目资产；覆盖分类 Gold Anchors、九地区 Scene Bible、固定调色板、纸娃娃/动画共享 transform、评分审查和 Godot 导出。用于批量资产、地域化资产、角色动作或 Godot-ready 原型；完整 HUD 场景只作为内部 review 资料。
---

# Mango AI Art Direction System

目标不是“生成一张好看的图”，而是让同一项目的资产能够复现、追溯、组合和回归。

## Release gate

开始 production 任务前运行：

```bash
python scripts/validate_anchor_pack.py --strict
```

只要五类 Category Gold Anchor 槽位未全部 approved，系统仍可用于生成 candidate 和验证管线，但不得把结果标为 production-ready 或声称 Anchor Pack 完整。不得用 Scene Bible 顶替缺失的分类锚。

## Read before work

所有任务先读：

- `references/art-direction.md`：全局尺寸、baseline、光照、描边、固定调色板层级。
- `references/style-anchor-system.md`：四级基准体系与参考图权威边界。
- `references/art-review.md`：100 分评分、APPROVE/REVIEW/REJECT 与 critical fail。
- `references/asset-provenance.md`：资产台账必填字段。

地区资产再读 `references/world-nations.md`；动画再读 `references/character-motion-standard.md`；其余按类别只读相应配方：

| 类别 | 配方 |
|---|---|
| 建筑、道路、室内 tileset | `references/architecture-tiles.md` |
| 人物、纸娃娃、头像、动作 | `references/characters.md` |
| 家具、装饰、植物 | `references/furniture-decor-plants.md` |
| 道具、食物、UI | `references/props-ui.md` |
| 神秘道具 | `references/beyonder-items.md` |
| 载具、动物 | `references/vehicles-animals.md` |
| VFX、天气、环境动画 | `references/vfx-weather.md` |

## Reference chain

每次生成按顺序选参考并登记 manifest id：

1. 一个相同类别、相同视角、`status=approved` 的 Category Gold Anchor。
2. 需要地域差异时，再加一个 `assets/scene-bible/manifest.yaml` 中的无 HUD visual anchor。
3. 角色连续性任务再加该角色上一版 approved 资产。

Scene Bible 只定义地域建筑语言、宏观构图、气候植被与材料关系；不定义角色尺寸、纸娃娃对齐、动画、tile 接缝、孤立资产轮廓或 HUD 布局。

## Generate

图像生成只经 `scripts/gen_image.sh` 的后端适配层，不直接调用厂商 API。后端配置见 `references/harness-setup.md`。prompt 使用英文；文字、编号和符文留空，进引擎后叠字体。

每个源文件立即登记 `assets/asset-registry-template.csv` 要求的 prompt/model/backend/seed/source/anchor/scene/palette/version 字段。无 seed 的后端写 `unsupported`，不能留成未知。

## Export

单件静态资产可用兼容命令：

```bash
python scripts/godot_export.py input.png building godot_assets --name loen_townhouse --region loen
```

纸娃娃层和动画帧必须整组导出：

```bash
python scripts/godot_export.py group layer godot_assets \
  base.png outfit.png hair.png acc.png \
  --group-id loen_man01_default \
  --name loen_man01_base --name loen_man01_outfit --name loen_man01_hair --name loen_man01_acc \
  --region loen
```

组导出先统一源画布，再用 union bbox 只计算一次 scale/origin/baseline。`.transform.json` 的 `transform_id` 必须回填台账。禁止对同组成员逐图 bbox/fit。

导出器默认映射到 `assets/palettes/palettes.json` 的 Master Palette；地区色用 `--region`，VFX/UI/神秘色用可重复的 `--special`。禁止逐图自由 64 色量化。

## Review and regression

逐件按 `references/art-review.md` 评分。动画先运行：

```bash
python scripts/motion_audit.py frame1.png frame2.png frame3.png --json motion.json
```

每批运行固定色板审查，并把报告路径与结论写回台账：

```bash
python scripts/palette_audit.py godot_assets --region loen --json palette.json
```

修改脚本、规范、palette、anchor 或 gold fixture 后运行：

```bash
bash scripts/run_art_regression.sh
```

APPROVE 要求总分 ≥90 且无 critical fail；Gold Anchor 晋升要求 ≥92。REVIEW 不能进入 Gold 或 production，REJECT 必须重做/回退。

## Scene Bible maintenance

九地区 90 景的源 ZIP 不进仓库。需要重建无 HUD visual anchors、review 拼图和 SHA-256 元数据时：

```bash
python scripts/import_scene_bible.py --source-dir <场景包目录>
```

不要横向扩场景或类别；新增内容应先证明现有 90 景或五类锚无法覆盖决策需求。

## Delivery boundary

- Scene Bible、HUD review 图和候选锚是内部资料，不进 Godot、不作宣传图。
- 对外交付只包括经固定 palette、目标画布、provenance 和评分审查的 `godot_assets/` 资产。
- AI 直出是原型品质；正式发行品质仍需美术逐像素精修和 in-engine vertical slice 验证。
