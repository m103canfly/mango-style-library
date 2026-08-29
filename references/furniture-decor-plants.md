# 配方：室内家具 + 灯饰（室内/室外）+ 桌面摆件 + 街道装饰 + 植物

生成前从本文件复制配方改造。所有 prompt 用英文。国家的植物地域清单见 `references/world-nations.md`。

## 目录

- 室内家具
- 室内灯饰
- 室外灯饰
- 桌面摆件
- 街道/广场装饰件
- 植物
- 验收清单
- 修方

## 室内家具

俯视 2D 游戏里家具为**微俯视正面**（能看到桌面/床面顶面）：

```
A single game asset sprite: one <家具描述>, Stardew Valley style pixel art, clean
chunky 16-bit pixel art, bright saturated colors, flat 2D slight top-down view like
Stardew Valley farmhouse interiors, isolated single object on transparent background,
no ground, no shadow, crisp clean edges, game asset
```

已验证/推荐：餐桌椅 `one wooden dining table with four chairs, warm brown oak, a white tablecloth and a vase with red flowers on top`、书架 `one tall wooden bookshelf filled with colorful book spines, dark walnut wood`、床 `one single bed with a green patchwork quilt and white pillow, dark wooden frame`、壁炉 `one stone fireplace with a warm glowing fire, grey bricks, wooden mantel with candles`、衣柜 `one wooden wardrobe cabinet with brass handles, chestnut brown`、书桌 `one writing desk with drawers, dark mahogany, an open book on top`、沙发 `one Victorian chaise longue sofa, deep red velvet, curved wooden legs`、钢琴 `one upright wooden piano, dark polished wood, candle holder on top`。

## 室内灯饰

煤气时代光源，**发光件要写出光晕**（`warm glowing`）：

- 壁灯：`one wall-mounted gas sconce with brass arm and a warm glowing yellow flame in a glass shade`
- 吊灯：`one brass chandelier with six candle lights, warm glowing flames, hanging chain`
- 台灯：`one oil table lamp with green glass shade, brass base, warm glowing flame`
- 落地灯：`one tall standing oil lamp with brass pole and frosted glass globe, warm glow`
- 烛光：`one brass candlestick with a lit white candle, small warm flame`

## 室外灯饰

- 煤气路灯（已验证）：`one Victorian gas street lamp with black cast-iron pole, decorative curved top, and a warm glowing yellow glass lantern`
- 多头广场灯：`one Victorian plaza lamp post with three glass lanterns on curved arms, black cast-iron`
- 门廊灯：`one carriage lantern beside a door, black iron frame, warm glowing glass panels`
- 信号灯：`one small railway signal lantern, red and green glass, brass frame`
- 码头风灯：`one ship lantern, brass with thick glass, warm glow`

## 桌面摆件

配合桌面/壁炉架摆放，按 icon/prop 类别生成：

- 座钟：`one ornate mantel clock, dark wood case, brass face and pendulum`
- 墨水瓶羽毛笔：`one glass inkwell with a white quill pen in it`
- 茶具：`one porcelain tea set, teapot and two cups, white with blue floral pattern`
- 相框：`one small brass photo frame with a portrait silhouette`
- 地球仪：`one desktop globe on a wooden stand, vintage map colors`
- 花瓶：`one porcelain vase with red roses`
- 书信堆：`one stack of letters tied with a red ribbon, wax seal on top`
- 报纸：`one folded newspaper, blank grey pages`

## 街道/广场装饰件

已验证/推荐：喷泉 `one circular stone fountain with a small bronze statue on top, light grey stone basin with blue water`、栅栏 `one short black cast-iron fence segment with pointed rails, straight horizontal row`、长椅 `one wooden park bench with black cast-iron armrests and legs, warm brown planks`、花坛 `one rectangular stone flower bed filled with red and yellow tulips`、路牌 `one wooden signpost with two directional arrows, blank arrows`、邮筒 `one red cast-iron post box with a domed top and a mail slot`、公告栏 `one wooden notice board with pinned paper notes, dark brown frame`、雕像 `one bronze statue of a gentleman on a stone pedestal, dark green patina`、消防栓（时代用 `one cast-iron water pump, dark green`）。

## 植物

```
A single game asset sprite: one <植物描述，从 world-nations 植被清单取>, Stardew
Valley style pixel art, clean chunky 16-bit pixel art, bright saturated colors, <视角>,
isolated single plant on transparent background, no ground, no shadow,
crisp clean edges, game asset
```

- 树木通用：必须带三层色描述——`a round layered green canopy, darker green edge, mid green body, light green upper-left highlight`（弗萨克针叶树改 `layered dark green needles with snow on branches`）
- 盆栽（已验证）：`one potted topiary plant, a round trimmed green bush in a brown terracotta pot`
- 作物：`one turnip crop with white round roots and green leaves, planted in dark soil mound`（带土堆方便直接摆）
- 各国乔木/灌木/花卉/作物清单直接查 `references/world-nations.md` 的"植被资产清单"

## 验收清单

- [ ] 块状硬边像素、明亮饱和色，无软笔触
- [ ] 透明底、无地面、无投影
- [ ] 家具为微俯视正面，未漂纯侧视或 3/4 大透视
- [ ] 发光件有暖色光晕描述命中（glowing）
- [ ] 树木树冠三层色
- [ ] 植物命中该地域清单，无串味

## 修方

- **宽扁重复件（栅栏/栏杆/长椅）不能自动 fit**：先用专项任务合同写死 16px 对齐的原生 1× 尺寸，再由像素画师按该画布重绘。连续铺贴段单独声明 `tileable=true`；标准地形 tile 是 64×64，不能把任意 prop 拉伸成 tile。
- **视角不对**：补 `flat 2D, slight top-down Stardew Valley view, object centered in frame`
- **树冠糊成一团**：补三层色描述 + `chunky readable pixels`
- **多件套被拆散**（桌椅分家）：写死 `as one combined sprite`，或拆两次生成
- **灯光不亮**：把 `warm glowing yellow` 放句首；仍不亮则在引擎里加 PointLight2D 兜底
