# Character Motion Standard

本文件定义 32×48 角色的正面/背面/侧面行走硬规则。生成提示词只能帮助草图接近这些规则；最终验收以共享 transform 导出后的逐帧像素为准。

## Canonical frame set

- 画布：每帧 32×48，透明背景。
- 方向：`down`、`right`、`up` 三行；`left` 运行时镜像 `right`。
- 每行 3 个唯一帧：`contact/idle`、`passing-A`、`passing-B`。
- 播放：F1 → F2 → F1 → F3；推荐 160–220ms/帧，移动速度与脚步相位在引擎中联调。
- 同一方向的所有帧必须使用一次 asset-group 导出，共享 union bbox、scale、origin、baseline。

## Global invariants

| 项目 | 硬规则 | REVIEW 区间 | REJECT |
|---|---|---|---|
| foot baseline | 接触地面的脚底 y=47 | 漂移 1px | 漂移 ≥2px |
| bbox height variance | ≤10% | 10–20% | >20% |
| bbox width variance | ≤18% | 18–36% | >36% |
| centroid drift | ≤3px | 3–6px | >6px |
| adjacent silhouette overlap | ≥0.52 | 0.32–0.52 | <0.32 |
| head vertical motion | 0–1px | 2px | >2px |
| hip vertical motion | 0–1px | 2px | >2px |

`motion_audit.py` 负责前五项的机械筛查；头部、髋部与动作可读性仍需人工看图。

## Front and back walk

正面/背面因为腿部被躯干遮挡，不能靠整体放大缩小制造运动。

- 接触帧：双脚接近中线，一只脚可前出 1px；身体重心居中。
- passing-A：左腿前出、右腿后收；脚尖水平差 2–4px；左臂与右腿反相。
- passing-B：与 A 镜像；不得复用 A 后只改 1 个像素。
- 步幅：左右脚最远横向分离 4–7px；超过 8px 会破坏二头身半比例。
- 躯干：水平摆动 0–1px；禁止整身左右漂移超过 2px。
- 头部：保持大小和五官中心；允许垂直 0–1px 的 bob，禁止逐帧缩放。
- 髋部：允许 0–1px 垂直位移；不得用髋部上下跳 3px 代替腿部相位。
- 轮廓：裙摆/大衣下摆可随跨步打开 1–2px，但肩宽和头宽保持稳定。

## Side walk

侧面帧必须让腿部相位在轮廓上可读。

- contact/idle：支撑脚落地，另一脚靠近；脚底 y=47。
- passing-A：前脚向行进方向伸出 3–5px，后脚离地 1px；身体重心位于支撑脚上方 ±1px。
- passing-B：相位反转；后腿变前腿，双脚颜色/轮廓不能互相吞没。
- 手臂摆动：与腿反相，手部前后差 2–4px；手持固定道具时优先保持道具稳定，可减少同侧手臂摆幅。
- 头部朝向、鼻尖、帽檐和发型轮廓不得在 A/B 帧换形。
- 身体前倾最多 1px；禁止用整身旋转或剪切产生走路感。

## Foot lock

Foot lock 是“支撑脚接触地面时不在屏幕上滑动”。

1. 在 A 帧标记支撑脚接地点 `(x,47)`。
2. 到下一接触/站立帧前，该点在画布中的水平位移不超过 1px。
3. 角色世界移动由 Godot 节点完成，sprite 内不要让两只脚同时向后滑。
4. 动画循环首尾的支撑脚位置差不超过 1px。

`motion_audit.py` 可检查 baseline，但 foot lock 的脚身份与接地点仍需人工标记。

## Silhouette and identity

- 放大到 800% 时，头、躯干、前后腿和至少一只手必须能分辨。
- 缩回 100% 时，A/B 两个跨步相位不依赖五官或纽扣细节也能区分。
- 帽子、头发外轮廓、肩宽、衣摆主形不得在帧间换设计。
- 面积较小的装饰可以抖动 1px，但不能成为重心漂移来源。
- 不对称装备需要单独的 left 变体；若运行时镜像会产生剧情/操作错误，不得沿用标准镜像规则。

## Export and audit

帧条切分后不要逐帧调用旧式 fit。一次传入同方向全部帧：

```bash
python scripts/godot_export.py group character godot_assets \
  down_f1.png down_f2.png down_f3.png \
  --group-id player_walk_down --name player_down_1 --name player_down_2 --name player_down_3

python scripts/motion_audit.py \
  godot_assets/character/player_down_1.png \
  godot_assets/character/player_down_2.png \
  godot_assets/character/player_down_3.png \
  --json godot_assets/character/player_walk_down.motion.json
```

导出 sidecar 中的 `transform_id` 和 motion score/verdict 必须写入资产台账。
