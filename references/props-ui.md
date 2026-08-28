# 配方：道具/物品图标 + UI/HUD 组件

所有 prompt 用英文。图标与 UI 最吃"成套风格统一"，同系列必须共用风格锚定参考图。

## 目录

- 道具/物品图标
- UI/HUD 组件
- 成套生产流程
- 验收清单
- 修方

## 道具/物品图标

```
A single game asset sprite: one <物品> item icon, <材质/颜色/细节>, Stardew Valley
style pixel art, clean chunky 16-bit pixel art, bright saturated colors, front view,
isolated single object on transparent background, no ground, no shadow,
crisp clean edges, game asset, game item icon
```

参数：`--ratio 1:1 --resolution 1K --background transparent`。

推荐示例：
- 武器：`one silver revolver with a wooden grip`
- 卡牌：`one tarot card with a golden sun pattern on a deep blue back`
- 货币：`one gold coin with a rose emblem`
- 食物：`one loaf of crusty bread, golden brown`
- 材料：`one grey potion bottle with a cork, glowing faintly`
- 工具：`one black walking cane with a golden handle`

## UI/HUD 组件

配方同上结构，关键在**写死边框材质 + 中心状态**。推荐示例：

- 面板框（9-slice 底）：`one rectangular game UI window frame, ornate dark wooden border with golden corner ornaments, flat empty beige parchment center panel filling the middle`
- 按钮：`one rectangular game UI button, warm wooden plank with golden trim, slightly rounded corners, empty center`
- 物品栏格：`one empty inventory slot, dark brown inner square with a thin golden border`
- 血条：`one horizontal game status bar, glossy red fill with a dark red left segment and golden frame caps`（空条用 `empty dark inner bar`）
- 蓝条/魔条：同上改 `glossy purple-blue fill`
- 头像框：`one square portrait frame, ornate golden border with a small heart emblem on top, empty dark center`
- 时钟面板：`one rectangular game clock panel, wooden frame with a small sun icon on the left and empty beige text area`
- 图标按钮：`one round game icon button with a golden ring border and a <信封/齿轮/地图> symbol in the center`

## 成套生产流程

同系列 UI/图标要看起来是一套的：

1. 先生成"基准件"（通常是面板框或物品栏格），验收确认边框材质、金色色号、圆角风格
2. 基准件 `image-to-url` 转 URL；同系列后续每张都带该系列已验收基准件 + `style-anchor-manifest.yaml` 中 approved UI Gold Anchor。需要地域差异时再加一个 Scene Bible visual anchor，不能用场景图替代 UI 锚
3. prompt 开头写 `matching the UI style of the reference image, same border material, same golden trim color`
4. 文件名成体系：`UI_面板框.png`、`UI_按钮_确认.png`、`图标_左轮.png`

## 验收清单

- [ ] 边框闭合不断线、四角装饰对称
- [ ] 面板/按钮中心为平坦纯色区（方便引擎 9-slice 或叠字）
- [ ] 同系列金色/木色色号一致（对照基准件）
- [ ] 透明底、无多余背景装饰

## 修方

- **中心被画满图案**：补 `flat empty center panel, no text, no symbols`；仍不行就接受它——引擎里中心本来要盖文字/内容，让美术掏空
- **同系列色号漂移**：确认带了基准件参考图，把 `same golden trim color as the reference` 放句首
- **AI 写 UI 文字必错**：prompt 一律 `no text`，文字进引擎后用字体渲染
