# Art Review Scorecard

本文件把审查从 checklist 升级为可比较、可回归的评分制。工具只提供证据，最终 verdict 由审查人签名并写回资产台账。

## Review material boundaries

- `assets/anchors/style-anchor-manifest.yaml` 中 `status=approved` 的分类锚是资产级权威。
- `assets/scene-bible/visual/` 是无 HUD 的地域场景软参考；`review/` 是地区 10 景审查拼图。
- Scene Bible 不进 Godot、不作为对外资产、不决定尺寸、角色比例、动画或 tile 接缝。
- 场景图不能单独替代 character/architecture/environment/interior/ui Gold Anchor。

## Critical fail gates

出现任一项直接 `REJECT`，总分不覆盖该结论：

- 文件不可读、alpha/画布/类别尺寸错误，或导出后关键内容被裁掉。
- 角色/纸娃娃层未共享 transform，或动画帧仍逐帧 bbox/fit。
- 纸娃娃脚底不在 y=47，且偏差 ≥2px。
- AI 文字、伪水印、明显非目标 IP/品牌元素进入对外交付资产。
- 软边抗锯齿、半写实笔触、错误透视使其不再属于项目像素语言。
- Scene Bible/HUD review 图被误标为 engine-ready 资产。
- provenance 缺失到无法追溯 prompt/model/backend/source/anchor/palette/transform/version 中任一关键环节。

## 100-point score

| 维度 | 分值 | 评分依据 |
|---|---:|---|
| Technical integrity | 20 | 文件、alpha、目标画布、像素边缘、无裁切/残点/水印 |
| Silhouette & composition | 20 | 100% 尺寸可读、视觉重心、轮廓、留白、视角 |
| Style & palette | 20 | 固定 Master/Region/Special Palette、左上光、非纯黑描边、块状明暗 |
| Category & regional identity | 15 | 类别配方命中；地域资产与 Scene Bible 特征一致但不照抄 HUD/构图 |
| Scale & alignment | 15 | 与 32px tile、门洞、角色 baseline、paper-doll shared transform 一致 |
| Motion/continuity | 10 | 动画相位、foot lock、轮廓重叠、身份一致；静态资产按跨变体一致性评分 |

每维先给 0–5 档，再乘权重：

- 5：可作为该维度的回归基准。
- 4：生产可用，只有不影响组合的轻微偏差。
- 3：可修复但必须复核，不能直接晋升 Gold Anchor。
- 2：明显偏离，需要重做或大修。
- 1：核心意图只部分命中。
- 0：不可用或无法验证。

计算：`维度得分 = 档位 / 5 × 分值`。

## Verdict thresholds

| Verdict | 阈值 | 处置 |
|---|---:|---|
| APPROVE | 90–100 且无 critical fail | 可进入 production；Gold Anchor 晋升要求 ≥92 |
| REVIEW | 75–89 且无 critical fail | 保持 candidate；修正后重审 |
| REJECT | <75 或任一 critical fail | 不进生产/不进回归基准，重做或回退 |

不得为了“过线”把 N/A 维度直接送满分。静态资产的 Motion/continuity 改审同一资产的变体、层或同族一致性；若确实只有单件且无变体，将 10 分按 4:3:3 分配给 silhouette、style、scale，并记录 `score_profile=static-single`。

## Tool evidence

### Palette

`scripts/palette_audit.py` 负责发现超出固定色板的主色，不再从场景图动态扩展机器基准。合法地区色和特殊色必须通过 `--region` / `--special` 显式声明。

### Motion

`scripts/motion_audit.py` 输出 bbox width/height variance、centroid drift、foot baseline drift、silhouette overlap、score 和 verdict。它不能判断脚的身份、动作表演或服装设计，人工仍需对照 `references/character-motion-standard.md`。

### Anchor authority

`scripts/validate_anchor_pack.py --strict` 是发布门：只要五类 Gold Anchor 的 required slots 未满足，系统可以运行，但不能声称 Anchor Pack 已 release-ready。

## Review record

每次审查必须写入资产台账：

- `review_score`、`review_verdict`、`reviewer`、`reviewed_at`、`review_profile`；
- 工具报告路径与版本；
- critical fail（若有）；
- 修正去向：prompt / specification / script / palette / anchor / asset source；
- 修正后的新 `asset_version`，不得静默覆盖旧版本。

审查闭环只有在台账和相应规范/脚本/资产版本更新后才算完成。
