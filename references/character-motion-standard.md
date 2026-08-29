# 廷根人物动作标准（tingen_pixel_v3_hd）

本文件定义项目原生 1×、64×96 人物动画的硬规则。生成式图像只能提供 HD 动作参考；最终动画必须由像素画师按本标准重绘，不能把生成图缩小后直接交付。

## 标准动画合同

- 每帧：完整 64×96 RGBA PNG；Alpha 只能是 0 或 255。
- 方向：至少 `south / west / east / north` 四向。不得以运行时镜像代替 west 或 east 的正式资产。
- 待机：每方向 4–6 帧。
- 步行：每方向 6–8 帧。
- 跑步：每方向 6–8 帧。
- 所有方向、所有帧共享脚底锚点 `(32,96)`，坐标种类为 `canvas_boundary`；最后一个可见像素行是 y=95。
- 所有帧都是完整姿势。禁止裁取脚、袖子、头发或衣摆后机械平移冒充动画。
- 动画 FPS 只控制动作播放。世界移动速度由 Godot 节点独立控制：步行 2 格/秒，跑步 5 格/秒。

## 机械审计阈值

| 项目 | APPROVE | REVIEW | REJECT |
|---|---:|---:|---:|
| foot anchor | 每帧 `(32,96)` | — | 任一帧不落 y=96 边界 |
| foot baseline drift | ≤1px | — | >2px；1–2px 需人工确认 |
| bbox height variance | ≤10% | 10–20% | >20% |
| bbox width variance | ≤18% | 18–36% | >36% |
| centroid drift | ≤6px | 6–12px | >12px |
| adjacent silhouette overlap | ≥0.52 | 0.32–0.52 | <0.32 |
| head vertical motion | 0–2px | 3–4px | >4px |
| hip vertical motion | 0–2px | 3–4px | >4px |

`motion_audit.py` 负责画布、帧数、bbox、质心、脚底边界和轮廓重叠。头部、髋部、支撑脚身份和表演仍需人工看图。

## South / north 行走

- contact：双脚接近中线，重心位于支撑脚上方。
- passing-A：左腿前出、右腿后收；脚尖纵向差 4–8px，手臂与腿反相。
- passing-B：与 A 相位相反；不能复用 A 后只移动整条腿。
- 最大步幅：双脚最远分离 8–14px；超过 16px 需要专项动作合同。
- 躯干水平摆动 0–2px；禁止整身左右漂移超过 4px。
- 头部和髋部允许 0–2px 垂直 bob，不得逐帧缩放。
- 裙摆或大衣下摆可随跨步展开 2–4px，但肩宽、头宽和主轮廓身份必须稳定。

## West / east 行走

- contact：支撑脚落在 y=96 边界，另一脚接近。
- passing：前脚向行进方向伸出 6–10px，后脚离地 1–2px；重心位于支撑脚上方 ±2px。
- 手臂与腿反相，前后差 4–8px。固定手持物优先稳定道具轮廓，可缩小同侧手臂摆幅。
- 鼻尖、帽檐、发型和头部朝向不能在帧间换形。
- 身体前倾最多 2px；禁止整身旋转、剪切或缩放产生走路感。
- east 与 west 都必须交付；不对称制服、手持物和伤痕不能靠镜像猜测。

## Foot lock

Foot lock 是支撑脚接触地面时，接地点不在画布内滑动。

1. 为每个 contact 帧标记支撑脚接地点 `(x,96)`。
2. 到下一 passing/contact 相位前，该支撑脚接地点水平漂移不超过 1px。
3. 动画循环首尾的同一支撑脚位置差不超过 1px。
4. 角色世界位移由 Godot 节点完成，Sprite 内不得让两脚同时向后滑。

脚身份和接地点必须在人工审查记录中标注；单靠 Alpha bbox 无法判断是哪只脚。

## Silhouette 与身份

- 800% Nearest 预览下，头、躯干、前后腿和至少一只手可区分。
- 100% 下，相邻相位无需依赖五官、纽扣或纹理细节即可辨认。
- 帽子、发型、肩宽、衣摆和手持物主形不能在帧间换设计。
- 小装饰允许 1px 抖动，但不能造成主体质心漂移。
- 禁止抗锯齿、透明软边、平滑渐变和子像素位移。

## 导出与审计

正式 1× 帧不能经过 bbox/fit 或缩放。以每方向 6–8 张完整 64×96 帧直接审计：

```bash
python scripts/motion_audit.py \
  south_01.png south_02.png south_03.png south_04.png south_05.png south_06.png \
  --animation-type walk --json south_walk.motion.json
```

完整四向 Sheet 必须按 `south / west / east / north` 四行排列：

```bash
python scripts/motion_audit.py --sheet npc_walk.png --hframes 6 --vframes 4 \
  --animation-type walk --json npc_walk.motion.json
```

若只是对生成式 HD 参考做候选归一化，可以使用 `godot_export.py group character` 检查共享 transform；该输出仍是 `reference_candidate_not_runtime_ready`，不能进入标准交付目录。
