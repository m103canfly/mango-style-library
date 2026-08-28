# 配方：动作集 + 环境动画 + 神秘学特效（VFX）+ 天气时段变体

诡秘之主项目的"动起来"文件。动画条与特效的共识同人物：**AI 出草图 → Aseprite/Godot 粒子人工收尾**。所有 prompt 用英文。

## 目录

- 角色动作集
- 环境动画条（灯焰/炊烟/水波/旗帜）
- 神秘学特效（仪式阵/灰雾/灵视/星光门）
- 天气与时段变体
- 验收清单
- 修方

## 角色动作集

在 sprite sheet 配方（见 `references/characters.md`）基础上扩展动作词库，规则不变（带单帧参考图、单方向、3-4 帧）：

| 动作 | prompt 词 |
|---|---|
| 待机 | `idle breathing` |
| 行走 | `walking` |
| 奔跑 | `running` |
| 坐下 | `sitting down` |
| 交互 | `interacting with an object` |
| 施法 | `casting a spell, one hand raised` |
| 受击 | `flinching from a hit` |

## 环境动画条

```
A pixel art animation strip: <物件>, <N> frames in a single horizontal row, identical
object in every frame, only the <火焰/烟/水/旗> changes between frames, Stardew Valley
style pixel art, clean chunky 16-bit pixel art, bright saturated colors, transparent
background, no ground, game asset animation strip
```

- 灯焰闪烁：`a gas lamp lantern, only the flame flickers`（4 帧）
- 炊烟：`a brick chimney, only the smoke drifts upward`（4-6 帧）
- 喷泉水波：`a stone fountain basin, only the water ripples`（4 帧）
- 旗帜飘动：`a hanging banner, only the fabric waves`（4 帧）

## 神秘学特效（VFX）

发光特效统一写 `glowing, luminous edges, transparent background`；引擎里用 Additive 混合或 GPUParticles2D 叠。导出用 `vfx` 类别（64×64）。

- 仪式魔法阵：`one glowing ritual magic circle, top-down flat view, concentric rings with rune marks and small candles at the nodes, pale golden glow`（符文必须是抽象纹理）
- 灰雾：`one cluster of swirling gray fog wisps, soft ethereal curls, semi-transparent look`（灰雾之上氛围件）
- 灵视：`one spirit vision effect, glowing threads and faint spirit silhouettes, ethereal blue-white`
- 星光门（门途径）：`one door-shaped portal of starlight, cosmic blue swirls with star sparks, glowing edges`
- 魔药雾气：`one small puff of <途径主色> mystical vapor with sparkles`
- 雨滴/雪粒子：`one rain streak particle` / `one small snowflake particle`（小件，供粒子系统）

## 天气与时段变体

**优先后处理罩色，不重新生成**（省配额且零漂移）：

1. Godot 里 CanvasModulate 罩色：白昼 #FFFFFF / 黄昏 #F0C8A0 / 夜晚 #6B7FA8 / 雾天 #C8D4D4
2. 雾天加一层半透明雾 sprite（上面的灰雾配方，放大平铺，低透明度缓慢平移）
3. 夜晚灯光件单独提层：路灯/窗户改发光态（`lit windows` 变体图或引擎 PointLight2D）
4. 只有"换季节"才重新生成（雪地弗萨克 vs 夏日费内波特这类本来就分资产）

### 大雾天后处理配方（2026-08 贝克兰德证交所已验证）

PIL/引擎通用的四层叠法：① 世界层降饱和（×0.8）+ 冷灰调（B 通道 ×1.05）；② 雾密度场 = 距离渐变（远处浓）+ 2-3 条正弦飘带 + 低频噪声（大半径模糊过的随机网格），密度上限 0.9，雾色 #D5D9DF；③ 按密度场把雾色混入世界层；④ **HUD 必须羽化遮罩还原到雾层之上**——游戏 HUD 在 CanvasLayer 不受雾影响，这步漏了画面就"假"。

## 验收清单

- [ ] 动画条：帧数对、物件本体逐帧一致、只有声明的部位在动
- [ ] VFX：发光边缘干净、透明底、符文是抽象纹理不是乱码字
- [ ] 仪式阵：严格正俯视、圆环居中不变形
- [ ] 天气变体：罩色值与 art-direction 表一致，不重新生成同物件的"雾版"

## 修方

- **整帧都在动**（动画条要求只动局部）：把 `only the <部位> changes` 提前到句首；仍失败则手动复制静帧、只改动局部
- **特效不透明/带底**：补 `isolated on transparent background`，导出后检查四角 alpha
- **符文出乱码字**：prompt 删一切 `runes with text`，改 `abstract rune-like markings`
