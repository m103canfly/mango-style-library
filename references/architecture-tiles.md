# 配方：建筑（地标/公共/住宅/零部件）+ 道路 + 地板 tile + 室内套件

生成前从本文件复制配方改造。所有 prompt 用英文，招牌文字可指定中文。国家的地域变体注入块见 `references/world-nations.md`；尺寸比例见 `references/art-direction.md`。

## 目录

- 独特地标建筑（教堂/火车站/皇宫/首相府/大学/大使馆）
- 公共建筑（警察局/剧院/证券交易所/电报局等）
- 住宅矩阵（户型×材质变体）
- 建筑零部件（门/窗/屋檐/招牌）
- 道路资产（路面/路沿/井盖/下水口）
- 地板与地面 tile（可平铺纹理）
- 室内 tileset（墙/地板/楼梯/地毯）
- 验收清单
- 修方

## 独特地标建筑

一件一配方，构图取**正面立面+标志物特写感**。结构：`A single game asset sprite: one <地标描述>，` + 通用资产后缀（见 SKILL.md），地标前冠国家注入块风格词。已验证级示例：

- 教堂（鲁恩）：`one grand Gothic Revival cathedral facade, twin stone spires, large rose window, pointed arches, flying buttresses, grey stone`
- 蒸汽火车站：`one Victorian train station facade, red brick clock tower entrance, large glass-and-iron arched train shed visible behind`
- 皇宫：`one grand classical palace facade, cream stone, columned portico, central pediment with royal crest, rows of tall windows`
- 首相府：`one modest terraced government townhouse, dark brick, black door with brass number plate, white columns at door, guard lantern`
- 大使馆：`one grand embassy townhouse, stone facade, two flag poles with flags on the balcony`
- 大学：`one sandstone university hall, clock tower, arched cloister walkway, mullioned windows`
- 剧院：`one ornate theater facade, arched entrance with marquee, gilded decorations, poster frames on both sides`

## 公共建筑

模板化：户型相近，换招牌与标志物。配方：

```
A single game asset sprite: one <公共建筑类型> facade, <国家注入块风格>, <标志物>,
a signboard with Chinese text '<中文名>', + 通用资产后缀
```

类型速查：警察局 `police station, blue lamp over the door`、证券交易所 `stock exchange, Corinthian columned portico`、电报局 `telegraph office, small antenna on roof`、银行 `bank, brass doors and barred windows`、邮局 `post office, red mail box by the door`、医院 `hospital, white facade with red cross...（时代吻合用 green cross 药剂师铺替代更稳）`、报社 `newspaper office, printing press visible in window`。

**两个已验证补充（2026-08 贝克兰德证交所）**：
- **俯视场景用的建筑必须带屋顶坡面**——纯正面立面缺屋顶，拼进俯视场景像纸板房。配方在类型词后加：`in slight top-down view with a large visible roof — the upper part is a big <屋顶材质> roof slope tilted toward the viewer with shingle texture`（住宅为 `<材质> gable roof`）。视角词放句首附近、不带正面建筑参考图，否则锚回立面。
- **大型公共建筑导出用 `building_l`（256×256）**：柱廊+大屋顶+台阶+招牌全塞进 128 会把门洞压到 40px 以下，角色进不了门。

## 住宅矩阵（户型×材质变体）

四种户型，每种先生成基准件，再用锁风格流程换材质（`same building, same shape and windows, walls changed to <新材质>` + 基准件参考图）：

| 户型 | 基准 prompt |
|---|---|
| 独栋别墅 | `one detached two-story villa with small front garden fence, gable roof` |
| 联排别墅 | `one terraced townhouse, narrow front, three stories, shared roof line` |
| 高公寓 | `one tall tenement apartment building, five stories, many identical windows, fire-escape-free` |
| 矮公寓 | `one low apartment block, two stories over a shop, flat parapet roof` |

材质槽：`red brick` / `cream stone` / `half-timbered` / `stucco in <国家色>`。

## 建筑零部件（门/窗/屋檐/招牌）

配方：`A single game asset sprite: one <物件描述>` + 通用资产后缀。已验证：

- 窗：`one Victorian arched window with cream stone frame, dark wooden window panes, and a small flower box with pink flowers under the sill`
- 门：`one Victorian double wooden door entrance with dark green double doors, brass handles, cream stone doorframe, small arched transom window above, and two short stone steps`
- 雨棚屋檐：`one Victorian shop awning eave with purple and white striped fabric canopy and decorative scalloped edge with gold trim, no building behind it`
- 招牌：`one hanging wooden shop signboard with black wrought iron bracket, blank dark wooden panel`（要文字加 `with Chinese text '<字>'`；留白更灵活）

## 道路资产

俯视游戏的街道层，tile + 小 prop 组合：

- 路面 tile（纹理配方，见下节）：`grey stone slab road, large rectangular slabs`（石板大街）、`cobblestone road`（小巷）、`packed dirt road`（城郊/殖民地）
- 路沿：`one straight curb stone edge, light grey, viewed from above, long horizontal strip`（按 prop 生成后切条）
- 井盖：`one round cast-iron manhole cover, dark iron with ring pattern, viewed from above`（icon 类别）
- 路沿下水口：`one cast-iron curb drain grate, rectangular, dark iron bars, viewed from above`（icon 类别）
- 不要斑马线/红绿灯——时代错位

## 地板与地面 tile（可平铺纹理）

```
A single game asset: a flat square tile of <材质> texture, uniform pattern filling
the entire square edge to edge, flat front view, no perspective, Stardew Valley style
pixel art, clean chunky 16-bit pixel art, bright saturated colors, <主色>,
tileable texture, game asset tile
```

已验证/推荐材质：室外 `grey cobblestone, warm grey tones`、`grass lawn, fresh green with tiny darker green noise dots`、`dirt path, warm brown`、`red brick pavement`；室内 `wooden plank floor, warm honey brown planks`、`stone slab floor, cool grey`、`checkered kitchen tiles, cream and brown`。
关键约束：`uniform pattern filling the entire square edge to edge` 必须有，否则模型在中央画单个物件。

## 室内 tileset（墙/地板/楼梯/地毯）

配合家具搭室内，全部是 tile 配方（上节结构）：

- 墙面：`interior wall with wainscoting, dark wood lower half, patterned wallpaper upper half in muted green`
- 地板：木地板/石砖（见上节室内材质）
- 地毯：`one rectangular Persian-style rug, deep red with golden border pattern, flat top-down view, filling the whole square`
- 楼梯：`one straight wooden staircase segment, top-down view, warm brown steps with dark edges`
- 墙角/门框过渡件：从主墙 tile 裁切，不单独生成

## 验收清单

- [ ] 块状硬边像素、明亮饱和色，无软笔触
- [ ] 透明底、无地面、无投影
- [ ] 纯正面立面，未漂 3/4
- [ ] 国家注入块识别物命中（对照 world-nations 速查表）
- [ ] 招牌中文逐字核对无错字
- [ ] 纹理充满方形、四边近似可对拼
- [ ] 门洞高度 ≥ 角色高度（对照 art-direction 比例表）

## 修方

- **tile 导出后是空图/全透明**：透明底生成全幅纹理的 alpha 失效事故（2026-08 实测）。tile 一律 `--background opaque` 重生成，生成后先验文件大小（>100KB）与 RGB 均值再进管线；godot_export.py 会对 tile 水印区做镜像填补而非擦除
- **视角漂成 3/4**：删否定词，换 `flat 2D, slight top-down Stardew Valley view, symmetrical composition, object centered in frame, chunky readable pixels, limited color palette`
- **纹理不对拼**：取图中心 1/2 区域裁切后人工做镜像/错缝变体，或仅作重绘参考
- **招牌错字**：文字加引号强调；仍错则出空白招牌，引擎里用字体叠字
- **地标不够"独特"**：把标志物写具体（`twin spires`、`rose window` 逐个列出），不要让模型自由发挥地标特征
- **拼进俯视场景像纸板房**（2026-08 已验证解法）：本文件配方产的是纯正面立面，适合横版/正交立面拼贴；要拼俯视 mockup 用 3/4 变体配方，两个要点缺一不可——① **视角描述放句首**（`A single game asset sprite seen from a slight top-down three-quarter view: ...` + 屋顶写成 `large sloped plane tilted toward the viewer`、老虎窗 `embedded in the roof slope`），埋在句中会被无视仍出正面图；② **不能拿正面建筑图作 --reference-image**（会把视角锚回正面），必须选同为 3/4 视角的 approved architecture Gold Anchor；地区 Scene Bible 只能补地域语言。没有合格 3/4 Gold Anchor 时产物保持 candidate。实测产出：屋顶坡面+侧墙可见的真 3/4，拼合后"纸板房"感消除
