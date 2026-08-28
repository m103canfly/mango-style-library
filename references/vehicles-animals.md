# 配方：载具 + 动物

俯视 2D 游戏里载具与动物用**侧视（side view）**——与建筑的正面立面不同，本文件配方统一写死 `side view`。所有 prompt 用英文。

## 目录

- 载具（陆运/蒸汽/飞行）
- 动物（役用/城市/野生）
- 验收清单
- 修方

## 载具

```
A single game asset sprite: one <载具描述>, side view, Stardew Valley style pixel art,
clean chunky 16-bit pixel art, bright saturated colors, isolated single object on
transparent background, no ground, no shadow, crisp clean edges, game asset
```

参数：`--ratio 3:2 --resolution 1K --background transparent`（横长物件）；导出用 `vehicle` 类别（160×128）。

已验证/推荐：

- 出租马车：`one black horse-drawn hansom cab, enclosed two-wheel carriage with a driver seat at the back, side view`（马与车厢可拆开两件，方便 Y-Sort）
- 公共马车：`one double-decker horse-drawn omnibus, open upper deck with passengers seats, advertisement boards on the side, side view`
- 马匹：`one chestnut carriage horse with leather harness, standing, side view`
- 蒸汽列车头：`one Victorian steam locomotive, black boiler with brass details, tall smokestack with white steam puff, red wheels, side view`
- 列车车厢：`one Victorian passenger train carriage, dark green with cream window frames, side view`
- 飞空艇：`one steampunk airship, cream balloon envelope with brass ribs, wooden gondola hanging below, small propellers, side view`
- 自行车：`one penny-farthing bicycle, large front wheel, black iron frame, side view`
- 货运马车：`one wooden cargo wagon with canvas cover, side view`

## 动物

配方同上单件资产结构，icon/prop 级小件：

- 鸽子：`one grey pigeon, standing, side view`（广场氛围件，可再做 2-3 帧啄食）
- 乌鸦：`one black crow, standing, side view`（偷盗者/错误途径氛围件）
- 猫：`one black cat sitting, curled tail, side view`
- 狗：`one brown terrier dog, standing, side view`
- 海鸥：`one seagull, white and grey, side view`（港口/费内波特）
- 松鼠：`one red squirrel holding a nut, side view`（公园/林地）
- 羊/牛（草原）：`one sheep, woolly white` / `one brown cow, standing, side view`（帕斯/哈加提）

## 验收清单

- [ ] 纯侧视，未漂成 3/4 或正面
- [ ] 透明底、无地面、无投影
- [ ] 马车类车轮/车轴结构可读（AI 常画错轮子数，逐轮核对）
- [ ] 列车/飞艇的年代感正确（无现代部件：无橡胶轮胎、无电灯）
- [ ] 尺寸对照 art-direction 表（载具长边 ≤160）

## 修方

- **轮子数错/结构糊**：prompt 里写死 `two large spoked wheels`，仍错则接受后人工修（2026-08 实测：写死 two-wheel 的 hansom 仍产出四轮 growler——轮数核对必须逐轮数，氛围正确可留用但在台账标注偏差）
- **视角漂**：句首 `side view, perfectly flat side profile`
- **蒸汽/烟雾画成灰团**：`small white steam puffs, clean shapes`，烟雾太大就裁掉，引擎里用粒子补
