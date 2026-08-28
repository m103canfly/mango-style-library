---
name: mango-style-library
description: 星露谷物语风格游戏主美术资产库批量生产——建筑（地标/公共/住宅矩阵/零部件/道路/室内tileset）、人物（纸娃娃分层换装/完整NPC/对话头像/多帧动作）、植物、家具装饰（室内灯饰/室外灯饰/桌面摆件）、道具、食物、UI/HUD、神秘道具（诡秘之主22途径）、载具动物、特效与天气时段变体，用 image_generation 插件产出风格统一的游戏素材。内置美术方向基准（调色板/光照/尺寸比例）、《诡秘之主》九国地域标准（鲁恩/因蒂斯/弗萨克/费内波特/塞加尔诸邦/拜朗/高地/帕斯/哈加提，维多利亚时代基底）、逐张验收流程、Godot 直出后处理（去水印/对像素网格/调色量化）与引擎落地指引。当用户做俯视 2D 像素游戏开发、要批量生成同一风格成套资产、要可直接导入 Godot 的素材、或要把场景效果图拆成资产库时使用。场景实机演示图（含完整 HUD 整幅画面）走 pixel-art-game-assets skill。
---

# Mango Style Library（星露谷风游戏主美术资产库）

批量产出风格统一的星露谷式俯视 2D 游戏资产：美术基准 + 地域标准 + 分类配方 + 验收 + Godot 直出。

## Scope

- 两大全局文件，任何生成任务**先读**：
  - `references/art-direction.md`：主调色板、光照/描边规则、尺寸比例基准、纸娃娃画布规范、时段罩色
  - `references/world-nations.md`：九国/地区建筑·服设·植被·美食·地标注入块（资产属于具体国家时）
- 分类配方（按需读对应文件）：
  | 类别 | 参考文件 | 典型产物 |
  |---|---|---|
  | 建筑（地标/公共/住宅矩阵/零部件/道路/室内 tileset） | `references/architecture-tiles.md` | 教堂、电报局、联排别墅、路面井盖、墙纸地板 |
  | 人物（纸娃娃/完整NPC/头像/sprite sheet） | `references/characters.md` | 素体、服装层、对话头像、行走图 |
  | 家具/灯饰/桌面摆件/街道装饰/植物 | `references/furniture-decor-plants.md` | 书桌、煤气壁灯、路灯、茶具、各国树木 |
  | 道具/食物/UI | `references/props-ui.md` + 各国美食清单（world-nations） | 物品图标、地方美食、面板按钮 |
  | 神秘道具（22途径+泛神秘） | `references/beyonder-items.md` | 灵摆、封印物、魔药、符咒 |
  | 载具/动物 | `references/vehicles-animals.md` | 出租马车、蒸汽列车、飞空艇、马、鸽 |
  | 动作集/环境动画/VFX/天气 | `references/vfx-weather.md` | 施法帧、灯焰动画、仪式阵、雾夜变体 |
- 不管：含完整 HUD 的整幅场景实机演示图（→ pixel-art-game-assets skill）；引擎代码工程本身（落地拆分见 `references/engine-handoff.md`）。
- **产物定位红线**：实机演示图 = 内部审查标准（风格锚+审查基准），不进引擎、不对外展示；对外交付的只有 godot_assets 资产精灵。详见 `references/art-review.md` 定位红线节。

## Workflow

1. **工具**：一律经 `scripts/gen_image.sh` 适配层调用图像后端（跨 harness 可移植，后端规则与配置见脚本头注释与 `references/harness-setup.md`）：
   ```bash
   <skill目录>/scripts/gen_image.sh ensure-deps          # kimi 后端首次必跑
   <skill目录>/scripts/gen_image.sh image-to-url --image-path <本地参考图>   # kimi 后端：参考图必须先转公网 URL
   <skill目录>/scripts/gen_image.sh generate --description "..." --ratio ... --resolution ... --background ... --reference-image <URL> --output /mnt/agents/output/<name>.png
   ```
   参数硬约束沿用 image_generation 插件：透明底仅 1K + 1:1/3:2/2:3 + PNG；kimi 后端参考图必须是公网 URL。
2. **风格锚定**：`assets/style-anchor-tingen-square.png` 是已验收的星露谷风实机图。批量生产时先 `image-to-url` 转公网 URL，每张 generate 都带 `--reference-image` 锁风格；用户另供参考图时同理叠加。
3. **定基准**：读 `references/art-direction.md` 确认颜色用词、光源、目标尺寸不违规；资产属于具体国家时读 `references/world-nations.md` 取注入块。
4. **选配方**：按类别读对应 references 文件，复制配方改造。所有 prompt 用英文；招牌文字可指定中文（UI/符文一律 `no text`）。通用参数：
   - 单件资产（1:1）/ 角色与纸娃娃层（2:3）/ 横长载具与 sprite sheet（3:2），统一 `--resolution 1K --background transparent`
   - 通用后缀（单件资产）：`Stardew Valley style pixel art, clean chunky 16-bit pixel art, bright saturated colors, front view, isolated single object on transparent background, no ground, no shadow, crisp clean edges, game asset`
5. **批量生成**：用 todo_write 建清单，每批 2-3 个并行跑；用 `assets/asset-registry-template.csv` 建台账（id/类别/国家/prompt/验收状态/路径），批量生产不丢不乱。原图文件名语义化中文。
6. **逐张验收**：每张生成后用 read_file 看图，对照类别配方 + art-direction + 地域清单逐条核对，**如实报告偏差**；偏差大按该类别"修方"小节调整重跑。**批量产出后跑美术审查**（`references/art-review.md`）：`scripts/palette_audit.py` 调色板一致性 + 人工裁定 + 修方/基准回填，审查结论必须落闭环。
7. **Godot 直出**（用户要"可直接导入 Godot"时必跑）：
   ```bash
   python3 scripts/godot_export.py <输入.png> <tile|icon|ui|character|layer|portrait|building|plant|prop|vehicle|vfx> <输出目录> --name english_slug
   ```
   产物英文命名、按类别归档（tile 32×32 / 角色与层 32×48 / 头像 64×64 / 建筑 128×128 / 载具 160×128 / 特效 64×64 / UI 256×128），直接拖进 Godot 工程当原型素材。纸娃娃多层同名同画布导出，叠层即对齐。

## Pitfalls（跨类别核心坑，各类别专属坑见 references）

- **风格漂移**：不写死通用后缀时模型输出半写实软笔触稿。每张带完整后缀 + 风格锚定参考图。
- **否定式描述响应差**：`no perspective` 常被无视。改正面描述：`flat 2D, slight top-down Stardew Valley view, symmetrical composition, object centered in frame`。
- **透明底硬约束**：transparent 仅 1K + 1:1/3:2/2:3 + PNG；要 2K 只能 opaque。
- **全幅纹理（tile）必须 opaque 生成**（2026-08 街区切片实测）：transparent 生成全幅纹理可能出现整张 alpha 通道失效（RGB 有纹理/全黑两种形态都出现过），且导出器按 alpha 裁切会得到空图块。tile 不需要透明，一律 `--background opaque`；生成后检查文件大小（1K 纹理应 >100KB）再进管线。godot_export.py 对 tile 已自动把左下水印区改为对侧镜像填补，不留透明洞。
- **一致性三难**：多帧动作跨帧漂、纸娃娃层间错位、换装换脸——全部靠"验收过的图作 `--reference-image` + 同画布导出 + Aseprite 人工收尾"兜底，生成时接受草图定位，验收如实报告。
- **AI 文字必错**：招牌/编号/符文一律出空白或抽象纹理，文字进引擎用字体叠。
- **直出素材是原型品质**：已去水印、对网格、可直用，但非逐格原生像素——原型/占位直接拖进 Godot，正式品质仍需美术精修；交付时主动说明。
