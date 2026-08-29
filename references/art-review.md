# Art Review Scorecard

本文件把审查从 checklist 升级为可比较、可回归的评分制。工具只提供证据，最终 verdict 由审查人签名并写回资产台账。

## Review material boundaries

- `assets/anchors/style-anchor-manifest.yaml` 中 `status=approved` 的分类锚是资产级权威。
- `assets/scene-bible/visual/` 是无 HUD 的地域场景软参考；`review/` 是地区 10 景审查拼图。
- Scene Bible 不进 Godot、不作为对外资产、不决定尺寸、角色比例、动画或 tile 接缝。
- 场景图不能单独替代 character/architecture/environment/interior/ui Gold Anchor。

## Critical fail gates

出现任一项直接 `REJECT`，总分不覆盖该结论：

- 文件不可读、不是 PNG、Alpha 出现 0/255 之外的值、画布/类别尺寸错误，或关键内容被裁掉。
- 生成式 HD 参考被缩小、量化、bbox/fit 后直接冒充原生 1× 交付。
- 正式纸娃娃层或动画帧经过逐层/逐帧 bbox/fit，没有保持原生 64×96 共同坐标系。
- 人物脚底锚点不是 `(32,96)` `canvas_boundary`，或最后可见像素未落在 y=95。
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
| Scale & alignment | 15 | 与 64px tile、≥64px 公共门洞、`(32,96)` 人物锚点和纸娃娃共同坐标系一致 |
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

### Score computation

审查者先为六个维度分别给出 0–5 档，并为每个维度填写至少一个证据引用（技术 audit、motion report、Anchor 对照、Godot 截图或人工批注）。再运行：

```bash
python scripts/art_score.py review-input.json --json review.json
```

`art_score.py` 只负责可重复地计算权重、阈值和 critical fail 覆盖关系；它不会替审查者虚构证据，也不会自动把资产晋升为 Gold Anchor。

### Palette

`scripts/palette_audit.py` 负责候选参考的固定色板诊断，不再从场景图动态扩展机器基准。正式 1× 资产由 `package_asset.py` / `validate_delivery.py` 对声明的材质子色板逐色验证，不能靠全图最近色量化过关。廷根 RGB 注册表处于 provisional 时不得给出 `runtime_ready`。

### Motion

`scripts/motion_audit.py` 输出画布/帧数、bbox width/height variance、centroid drift、foot anchor/baseline drift、silhouette overlap、score 和 verdict；完整 Sheet 还验证四个方向行。它不能判断脚的身份、动作表演或服装设计，人工仍需对照 `references/character-motion-standard.md`。

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
