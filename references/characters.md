# 配方：人物系统（纸娃娃分层 / 完整 NPC / 对话头像 / 多帧动作）

人物产物分三层，按需求选管线。尺寸与叠层规范见 `references/art-direction.md`；各国服设注入块见 `references/world-nations.md`。所有 prompt 用英文。

## 目录

- 纸娃娃分层管线（可换装，本项目默认）
- 完整 NPC 直出 + 锁角色换装
- 对话头像立绘（首饰/面部细节承载层）
- 多帧动作 sprite sheet
- 验收清单
- 修方

## 纸娃娃分层管线（可换装）

**分工共识：AI 出层草图 → 同画布对齐（godot_export 保证）→ Aseprite 人工擦层间残边。** AI 很难只画单层而把其余留空，常把素体也画上——这是已知短板，靠后处理与人工兜底，验收时如实报告。

### 第 1 步：素体 base（每国×男女各一，用户确认"就是他/她"后存档）

```
A single game asset sprite: paper-doll base body of one <国家> <man/woman>, <skin tone>
skin, <体型>, simple grey underwear, standing straight, front view, arms slightly apart,
full body, simple face with dot eyes, Stardew Valley style pixel art, clean chunky 16-bit
pixel art, bright saturated colors, isolated on transparent background, no ground,
no shadow, crisp clean edges, game asset
```

参数：`--ratio 2:3 --resolution 1K --background transparent`。肤色锚点：鲁恩/因蒂斯 `fair skin`、弗萨克 `pale skin`、费内波特 `olive skin`、拜朗本地 `tan brown skin`、高地 `warm brown skin`。

### 第 2 步：生成层（必须带素体参考图）

素体 `image-to-url` 后，每层一次生成：

```
paper-doll clothing layer for the exact character in the reference image: only the
<服装/发型/首饰描述，从 world-nations 服设矩阵取>, same body proportions, same position,
same pose, everything except the <layer 名> fully transparent, Stardew Valley style
pixel art, clean chunky 16-bit pixel art, bright saturated colors, front view,
transparent background, no shadow, game asset
```

层类型与命名（z-order 从下到上）：
1. `outfit` 服装层：礼服/风衣/工作服等场合装（服设矩阵见 world-nations）
2. `hair` 发型层：`only the hairstyle, <颜色/样式>`
3. `acc` 首饰/手持层：`only the <pocket watch chain / brooch / cane / necklace>`（全身像仅示意，细节看头像）

### 第 3 步：同画布导出与合成预览

每层跑 `godot_export.py <层图> character <目录> --name <角色名_层名>`——统一裁到 32×48、脚底贴底、水平居中，**叠层即对齐**。合成预览：PIL 按 z-order 依次 paste（base→outfit→hair→acc）。

## 完整 NPC 直出 + 锁角色换装

路人 NPC 不值得分层时用整条直出（省一道人工）：

```
A single game asset sprite: one character sprite of <性别年龄> <职业>, <发型发色>,
<服装细节>, <姿势/手持物>, full body, standing, front view, simple face with dot eyes,
Stardew Valley style pixel art, clean chunky 16-bit pixel art, bright saturated colors,
isolated single character on transparent background, no ground, no shadow,
crisp clean edges, game asset
```

参数：`--ratio 2:3 --resolution 1K --background transparent`。同一 NPC 换装：以验收过的图作 `--reference-image`，`the same character from the reference image, same face, same hairstyle, same body proportions, now wearing <新服装>`。

## 对话头像立绘（首饰/面部细节承载层）

对话 UI、角色档案用；首饰、发型、面部特征在这里画清：

```
A single game asset sprite: character portrait bust of <人物描述>, chest-up, <发型>,
<首饰细节：怀表链/胸针/耳环/眼镜>, <表情>, front view, simple clean face with dot eyes,
Stardew Valley style pixel art, clean chunky 16-bit pixel art, bright saturated colors,
isolated on transparent background, no shadow, crisp clean edges, game asset
```

参数：`--ratio 1:1 --resolution 1K --background transparent`；导出用 `portrait` 类别（64×64）。

## 多帧动作 sprite sheet

**AI 出草图序列 → Aseprite 人工修帧对齐**，不要期待直接可用。

```
A pixel art sprite sheet: one character <角色描述，与单帧版一字不差>, <动作> animation,
<N> frames arranged in a single horizontal row, equal spacing between frames, identical
character design, outfit and colors in every frame, <方向> view, Stardew Valley style
pixel art, clean chunky 16-bit pixel art, bright saturated colors, transparent background,
no ground, no shadow, game asset sprite sheet
```

参数：`--ratio 3:2 --resolution 1K --background transparent`。硬规则：必须用验收过的单帧图作 `--reference-image`；一次只出一个方向（4 方向行走分 4 次）；3-4 帧封顶。动作词库：`walking`、`idle breathing`、`sitting`、`swinging a tool`、`casting a spell`、`interacting`。环境动画与特效帧另见 `references/vfx-weather.md`。

## 四向行走动画（星露谷官方结构，2026-08 对照官方 wiki 修正）

**规格**：4 方向（上/下/左/右），但 sheet 只画 **3 行 × 3 帧 = 96×144**（每帧 32×48，Godot 导入 Hframes=3 / Vframes=3）。这是星露谷官方 farmer sprite 的行走结构（Modding: Farmer sprite 词条）：

- **行序**：R1 `down`（面向屏幕）/ R2 `right`（朝右）/ R3 `up`（背向屏幕）
- **每方向 3 帧**：F1 站立、F2 跨步 A、F3 跨步 B；**播放序列 F1→F2→F1→F3 循环（各 200ms）**，站立帧复用。静止 = F1
- **朝左不单独画**：运行时把 right 行水平翻转（Godot `flip_h`）。官方明确左右互为镜像；镜像导致的道具换手（扫帚/文明杖换侧）官方同样接受。强不对称角色如坚持双向都画，作变体另行存档，不进标准 sheet

**帧条配方**（每方向一次生成，双参考图：角色锚图 + 风格锚）——只需 down/right/up 三条，left 不生成：

```
A pixel art sprite sheet: the exact same character as the reference image, <一句最简角色
身份，细节交给锚图>, walking animation, 4 frames in a single horizontal row with equal
spacing: frame 1 standing still, frame 2 left leg forward mid-stride, frame 3 standing
still, frame 4 right leg forward mid-stride, identical character design, outfit and colors
in every frame, <方向词>, Stardew Valley style pixel art, clean chunky 16-bit pixel art,
bright saturated colors, transparent background, no ground, no shadow, game asset sprite sheet
```

方向词：down `front view facing the viewer`；up `back view facing away from the viewer`；right `side view facing right`。角色描述压到最简（`one Victorian police constable in a dark navy uniform and custodian helmet` 级别），细节全靠锚图锁定，描述越多越容易和锚图打架。

**后处理切帧**（AI 帧间距不均，必须程序切）：擦左下水印区 → alpha 列投影找连续段（合并 <30px 空隙）→ 段数 ≠4 时容错（多取前 4 段/少拆最宽段）→ 逐帧 alpha 裁剪 → **取 f1/f2/f4 三帧**（站立/跨步A/跨步B，丢弃 f3 重复站立帧）→ 每帧跑 `godot_export.py <帧> character <目录>`（统一 32×48 贴底）→ 按 down/right/up 行序拼 96×144 sheet。

**实测经验**（巡警样图）：侧视两方向腿部相位最清晰（跨步/并腿分明）；面向/背向相位较含蓄，靠手臂摆动和肩部晃动补足，验收时放宽这两向的腿部差异要求；帧间一致性整体良好，微小漂移（帽徽/纽扣位置）属草图级，Aseprite 收尾。

## 验收清单

- [ ] 素体：全身完整、正面、双臂微张、肤色正确
- [ ] 层：只含本层物件（多余像素如实报告并擦除）、比例与素体一致
- [ ] 合成：32×48 叠层后无错位、无残边
- [ ] 头像：胸像构图、首饰可辨、与全身像同一人
- [ ] sprite sheet：帧数对、单行等距、逐帧同一人、动作相位连贯
- [ ] 四向行走：sheet 3 行（down/right/up）× 3 帧（站立/跨步A/跨步B）、96×144、播放序列 F1-F2-F1-F3、left 由 right 镜像、脚贴各帧底边

## 修方

- **层里长出了素体/别的层**：退化处理——按完整角色验收，人工在 Aseprite 擦除非本层区域（程序化备选：按肤色+区域擦除后导出，2026-08 样图验证可行）；下批 prompt 把 `everything except the <layer> fully transparent` 提前到句首
- **叠层后素体露出**（样图实测：微张手臂露出修身风衣袖外）：服装轮廓必须完全覆盖素体该部位——生成层时补 `loose fit, sleeves and hem fully covering the body`；或合成时把服装层 alpha 向外膨胀 1-2px 后擦除其下素体像素；遮不住则直接用 AI 着装原图当完整角色
- **跨帧/跨图长相漂移**：确认带了参考图，把 `identical character design, outfit and colors in every frame` 提前；帧数降到 3
- **GIF 人物忽大忽小**（2026-08 实测）：AI 透明底图带满幅低 alpha 噪点地板（alpha<64 的数千个微弱点），alpha 包围盒被撑到满幅，godot_export 的 fit 按包围盒缩放 → 逐帧缩放抖动。已修：导出管线在裁切前把 alpha<64 整体清零（对全部类别生效）；帧内孤立残点（切帧遗留）用连通域过滤（保最大域 + ≥25px 域），但注意甄别——贴近身体的小连通域可能是角色的手，勿误删
- **升 64×96 的教训**（2026-08 实测，已回退）：角色单独升 64×96 会破坏场景比例（96px 人物 vs 64px 树木、128 建筑门洞进不去人）——**角色尺寸必须和 tile/建筑同档联动，不能单独升**。且升档会暴露跨生成比例漂移：素体与着装层若来自不同次生成（头身比都可能不同），32×48 时亚像素误差被量化掩盖，64×96 下头发露出帽顶、纱影罩脸全部显形。若未来整体升档：素体与各服装层必须在同一次生成或同一参考图链上锁定头身比；帽类层纱影用"保帽子 keep-mask + 头区清 alpha"处理；仍错位则兜底——直接用 AI 着装原图当完整角色，纸娃娃交 Aseprite 人工收尾
- **首饰被画成全身大件**：首饰层改走头像立绘，全身像省略
