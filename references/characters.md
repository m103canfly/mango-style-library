# 配方：廷根人物、纸娃娃与动作参考

人物正式资产遵循 `tingen_pixel_v3_hd`：原生 1×、64×96、脚底锚点 `(32,96)`。本文件中的生图 prompt 只生产 HD 参考，不生产可直接导入 Godot 的最终 Sprite。

## 生产分层

```text
approved character Gold Anchor
        ↓
生成式 HD 角色/动作参考
        ↓
像素画师在固定 64×96 画布重绘
        ↓
纸娃娃叠层 / motion / palette / alpha 审计
        ↓
package_asset.py 标准交付
```

不得把生成图交给 `godot_export.py` 缩到 64×96 后冒充 1× 成品。`godot_export.py` 只生成带有 `reference_candidate_not_runtime_ready` 标记的候选画布。

## 角色 HD 参考

### 素体参考

```text
A high-definition visual reference for one <region> <man/woman>, <skin tone>,
<body type>, neutral underwear, standing straight, full body, front view,
arms separated from torso, clear readable silhouette, simple face, orthographic
2D game character design, upper-left key light, lower-right shadow planes,
transparent background, no ground, no cast shadow, no text, no UI
```

素体参考确认身份、头身比、正面轮廓和服装覆盖边界。它不是 1× 素体层。

### 层参考

每个层参考都绑定相同素体参考与 approved character Gold Anchor：

```text
High-definition paper-doll layer reference for the exact character in the
reference image: only the <outfit / hair / accessory>, same pose, proportions,
canvas placement and silhouette logic, everything else transparent,
orthographic 2D game design, upper-left key light, no ground, no text, no UI
```

像素画师在同一 64×96 文件中绘制 `base / outfit / hair / acc`，不做逐层 bbox/fit。层叠顺序：`base → outfit → hair → acc`。

## 完整 NPC HD 参考

```text
A high-definition full-body character reference of one <age/gender/occupation>
NPC from Tingen, <hair>, <clothing>, <held object>, neutral standing pose,
front view, orthographic 2D game design, clear silhouette, upper-left key light,
lower-right shadow planes, transparent background, no ground, no cast shadow,
no text, no UI
```

同一 NPC 换装必须绑定上一版 approved 角色资产，保持脸、发型、身材和主轮廓身份。生图结果只作为重绘参考。

## 对话头像

头像尺寸必须由专项任务合同规定；不能沿用旧版固定 64×64 假设。参考 prompt：

```text
A high-definition portrait reference of <character>, chest-up, <hair>,
<jewelry>, <expression>, front view, orthographic 2D game portrait design,
upper-left key light, transparent background, no text, no UI
```

## 四向动画参考

完整规范见 `references/character-motion-standard.md`。至少四向：`south / west / east / north`；west/east 都要正式重绘，不能默认镜像。

一次只生成一个方向的 HD 动作参考，建议让参考序列覆盖完整接触/下降/经过/上升相位：

```text
A high-definition animation reference sheet for the exact same character,
<idle / walking / running>, <south/west/east/north> view, 8 clearly separated
full-body poses in one horizontal row, complete limbs and garment in every pose,
consistent proportions, outfit, face, palette intent and silhouette identity,
orthographic 2D game design, transparent background, no ground, no shadow,
no text, no UI
```

正式 1× 重绘帧数：待机 4–6，步行 6–8，跑步 6–8。所有帧完整 64×96，共享 `(32,96)`；不得切肢体后机械平移。

## 审计与交付

每方向先运行：

```bash
python scripts/motion_audit.py frame_01.png frame_02.png frame_03.png \
  frame_04.png frame_05.png frame_06.png --animation-type walk --json walk.motion.json
```

每个正式帧再进入标准交付：

```bash
python scripts/package_asset.py npc_walk_south_01.png deliveries \
  --asset-id character.npc.walk.south.001.v001 \
  --asset-name npc_walk_south_01 \
  --asset-class character_frame \
  --district-id tingen.district.golden_indus \
  --facing south \
  --material-id skin.fair --material-id cloth.navy \
  --source-status pixel_redraw_from_generated_reference
```

## 验收清单

- [ ] PNG 为原生 64×96，而非预先放大或 HD 缩小成品。
- [ ] Alpha 只有 0/255，无抗锯齿、软边、平滑渐变。
- [ ] 脚底锚点为 `(32,96)` 画布边界，最后可见行 y=95。
- [ ] 所有层和帧共用坐标系，没有逐层/逐帧 bbox fit。
- [ ] 颜色来自声明的廷根材质子色板，人物默认不超过 24 个不透明色。
- [ ] 白天左上主光，暗面右下。
- [ ] 四向齐全；idle/walk/run 帧数满足合同。
- [ ] 步行 2 格/秒、跑步 5 格/秒由 Godot 世界移动控制，不写进动画 FPS。
- [ ] `_4x.png` 仅为 Nearest 预览；`_1x.png` 才是运行时图片候选。
- [ ] 入口、碰撞、导航和同屏比例另行验证后才能标 `runtime_ready`。
