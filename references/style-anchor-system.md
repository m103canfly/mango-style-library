# Style Anchor System
- 替换旧锚时保留旧版本为 `retired`，不得静默覆盖。
+- 替换旧锚时保留旧版本为 `retired`，不得静默覆盖。
本项目把“风格参考”分成四层。层级不能互相冒充；尤其不能把带 HUD 的整场景审查图当成角色、动画或尺寸锚。

## Level 0：Global Art Constitution

权威文件：`references/art-direction.md`。

它定义全项目共同的物理规则：像素画布、角色基线、门洞比例、左上主光、非纯黑描边、固定调色板层级。国家和具体服装不属于这一层。

## Level 1：Category Gold Anchors

权威清单：`assets/anchors/style-anchor-manifest.yaml`。

五类锚必须分别建立：

| 类别 | 定义什么 | 最少 approved 槽位 |
|---|---|---:|
| character | 头身比、正/侧面语言、轮廓、baseline、动作姿态 | 4 |
| architecture | 视角、门窗尺度、屋顶公式、材质明暗 | 3 |
| environment | tile 尺度、植被簇、地表边缘与对比 | 3 |
| interior | 室内视角、墙地面与家具尺度 | 3 |
| ui | 边框、圆角、图标尺度、状态对比、9-slice | 3 |

只有 `status: approved` 且具备版本、评分、审查人和审查时间的条目才是权威 Gold Anchor。`candidate` 只能用于比较，不得写入生产 prompt 的强制参考链；`needs-production` 表示资产缺口，不得用场景图顶替。

新增或晋升锚点后运行：

```bash
python scripts/validate_anchor_pack.py --strict
```

## Level 2：Regional Scene Bible

权威清单：`assets/scene-bible/manifest.yaml`。

90 张场景用于场景级地域审查，仓库内分成：

- `assets/scene-bible/visual/<region>/<scene>.png`：从原 2048×1152 审查图中裁出的无 HUD 中央视觉锚。
- `assets/scene-bible/review/<region>.png`：每个地区 10 景的验收拼图。
- `assets/scene-bible/source_registry.csv`：用户提供的 90 行验收台账。

Scene Bible 对“地域建筑语言、宏观构图、气候植被、材料关系、场景类型差异”有参考权；对“像素尺寸、角色比例、纸娃娃对齐、动画、tile 接缝、孤立资产轮廓、HUD 文案布局”没有权威性。

生成时，Scene Bible 只能作为地域补充参考，必须同时绑定对应类别的 approved Gold Anchor。若该类别无 approved 锚点，停止把产物标为 production-ready，转入 candidate/review。

## Level 3：In-engine Vertical Slice

最终权威是 Godot 内的可玩竖切：同屏比例、交互碰撞、动画节奏、UI 可读性和多时段表现均通过后，才能证明 Level 0–2 的规则在实际组合中成立。

## Reference selection

一次生成的参考链按以下顺序记录进资产台账：

1. 一个相同类别、相同视角的 approved Gold Anchor。
2. 需要地域差异时，再加一个 Scene Bible visual anchor。
3. 角色连续性任务再加该角色上一版 approved 资产。

不要同时堆叠多个互相竞争的场景图。不要从 Scene Bible 反推门洞像素、人物头身比或动画相位。

## Anchor review gate

候选锚晋升为 approved 必须满足：

- `references/art-review.md` 得分 ≥ 92；
- 无 critical fail；
- 已经通过固定调色板 remap 和目标画布导出；
- 相应类别的尺寸/视角/轮廓规则清晰可复用；
- provenance 齐全：prompt、model、backend、anchor chain、palette、transform、review、version；
- 替换旧锚时保留旧版本为 `retired`，不得静默覆盖。
