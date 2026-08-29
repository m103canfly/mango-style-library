---
name: mango-style-library
description: 为廷根项目生产风格统一、可审计、可回归的 2D 像素资产；覆盖 tingen_pixel_v3_hd 原生 1× 合同、分类 Gold Anchors、Scene Bible、材质子色板、四向人物动画、评分审查和 Godot 交付。生成式图片只作 HD 参考；完整 HUD 场景只作内部 review 资料。
---

# Mango AI Art Direction System

目标不是“生成一张好看的图”，而是让同一项目的资产能够复现、追溯、组合和回归。当前项目默认 Profile 是 `profiles/tingen_pixel_v3_hd/profile.json`。

## Release gate

开始 production 任务前运行：

```bash
python scripts/validate_project_profile.py --strict
```

严格门同时检查分类 Gold Anchors 和廷根 RGB 色板批准状态。模板派生色板现已批准；当前剩余发布阻断项是五类 Gold Anchor Pack。发布门未满足时，系统仍可生成 HD reference、制作原生 1× candidate 和验证管线，但不得标 production/runtime-ready。

## Read before work

所有任务先读：

- `references/art-direction.md`：全局尺寸、baseline、光照、描边、固定调色板层级。
- `references/template-palette-source.md`：模板色板来源、材质 tone ramp 与防平涂边界。
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

## Generate HD reference

图像生成只经 `scripts/gen_image.sh` 的后端适配层，不直接调用厂商 API。后端配置见 `references/harness-setup.md`。prompt 使用英文；文字、编号和符文留空，进引擎后叠字体。

所有生成结果必须登记为 `generated_hd_reference`。它们只能决定设计、轮廓、材质分区和动作意图；禁止缩小、最近色量化或自动 fit 后直接交付。正式资产由像素画师在任务合同规定的原生 1× 画布重绘。

每个源文件立即登记 `assets/asset-registry-template.csv` 要求的 prompt/model/backend/seed/source/anchor/scene/palette/version 字段。无 seed 的后端写 `unsupported`，不能留成未知。

## Candidate normalization and native delivery

对 HD 参考做构图/共享 transform 诊断时可用兼容命令：

```bash
python scripts/godot_export.py input.png building reference_candidates --name loen_townhouse --region loen
```

HD 纸娃娃参考层和动画参考帧必须整组归一化：

```bash
python scripts/godot_export.py group layer reference_candidates \
  base.png outfit.png hair.png acc.png \
  --group-id loen_man01_default \
  --name loen_man01_base --name loen_man01_outfit --name loen_man01_hair --name loen_man01_acc \
  --region loen
```

组导出先统一源画布，再用 union bbox 只计算一次 scale/origin/baseline。`.transform.json` 的 `transform_id` 必须回填台账。禁止对同组成员逐图 bbox/fit。该工具输出固定标记为 `reference_candidate_not_runtime_ready`。

候选导出器默认映射到 `assets/palettes/tingen-template-palette.json` 以便比较；这不能替代正式 1× 材质落色。复合资产必须按 `assets/palettes/tingen-materials.json` 的材质遮罩和 tone ramp 分别处理，禁止全图最近色量化。只通过 RGB 闭包但 tone roles 不足时必须进入平涂复核。

像素画师完成原生 1× PNG 后，使用项目打包器；它不会缩放运行时 PNG：

```bash
python scripts/package_asset.py input_1x.png deliveries \
  --asset-id facade.municipal_hall.entrance_bay.v001 \
  --asset-name municipal_hall_entrance_bay \
  --asset-class facade_component \
  --district-id tingen.district.golden_indus \
  --material-id stone.warm_dressed --material-id door.dark_green_civic \
  --material-id glass.slate_blue --material-id iron.black_cast \
  --source-status pixel_redraw_from_generated_reference \
  --task-contract contracts/municipal_hall_entrance_bay.json

python scripts/validate_delivery.py \
  deliveries/facade.municipal_hall.entrance_bay.v001
```

## Review and regression

逐件按 `references/art-review.md` 评分。动画先运行：

```bash
python scripts/motion_audit.py frame1.png frame2.png frame3.png --json motion.json
```

每批运行固定色板审查，并把报告路径与结论写回台账：

```bash
python scripts/palette_audit.py reference_candidates --region loen --json palette.json
```

六维审查输入必须逐项附证据，再由评分器计算统一 verdict：

```bash
python scripts/art_score.py review-input.json --json review.json
```

把资产标为 `approved_1x` 或 `runtime_validation_pending` 时，`package_asset.py` 必须带 `--review-json review.json`；candidate 不得伪造批准状态。

修改脚本、规范、palette、anchor 或 gold fixture 后运行：

```bash
bash scripts/run_art_regression.sh
```

APPROVE 要求总分 ≥90 且无 critical fail；Gold Anchor 晋升要求 ≥92。REVIEW 不能进入 Gold 或 production，REJECT 必须重做/回退。技术图片通过仍不等于 `runtime_ready`，还必须验证入口、碰撞、导航和同屏比例。

## Scene Bible maintenance

九地区 90 景的源 ZIP 不进仓库。需要重建无 HUD visual anchors、review 拼图和 SHA-256 元数据时：

```bash
python scripts/import_scene_bible.py --source-dir <场景包目录>
```

不要横向扩场景或类别；新增内容应先证明现有 90 景或五类锚无法覆盖决策需求。

## Delivery boundary

- Scene Bible、HUD review 图和候选锚是内部资料，不进 Godot、不作宣传图。
- 对外交付只包括符合 `tingen_pixel_v3_hd` 标准目录、provenance 和评分审查的原生 1× 资产。
- AI 直出始终是 HD 参考；正式发行品质必须逐像素重绘并通过 in-engine vertical slice。
