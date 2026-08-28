# 美术方向基准（所有资产的统一约束）

主美术职责的一页：调色板、光照、描边、尺寸比例。任何类别生成前都要确认 prompt 不违反本页；各国专属色彩板另见 `references/world-nations.md`。

## 目录

- 主调色板
- 光照与描边规则
- 尺寸比例基准表
- 纸娃娃画布与叠层规范
- 时段罩色基准

## 调色板层级（机器权威 + 文案锚点）

机器权威文件是 `assets/palettes/palettes.json`，版本化为：

1. **Master Palette**：全项目共享的轮廓、材质、肤色、中性色、植被和常用 UI 色。
2. **Region Accent Palette**：九国/地区的少量强调色；只在资产明确属于该地区时叠加。
3. **Special Palette**：UI、VFX、神秘道具、发光等有明确语义的例外色；必须显式选择。

导出时用 `scripts/palette_remap.py` 或 `godot_export.py --region/--special` 映射到上述固定色集合。禁止再对每张图片独立做 64 色量化；否则同一木材、肤色和阴影会产生不可审计的多套近似色。

下表是 prompt 文案锚点，不是完整机器色板：

prompt 里写颜色时优先用下列对应描述，保证几百件资产同色系：

| 用途 | 色值锚点 | prompt 用词 |
|---|---|---|
| 木材主体 | #8B5A2B / #6B3E1D | warm brown wood |
| 金色装饰 | #D9A441 | warm golden trim |
| 红砖 | #B4503C | warm red brick |
| 石材奶白 | #E8DCC0 | cream stone |
| 板岩灰蓝 | #5A6B7C | blue-grey slate |
| 草地/树冠中色 | #4E9B3A | fresh mid green |
| 树冠深边 | #2E6B28 | darker green edge |
| 树冠高光 | #A8D94E | light yellow-green highlight |
| 制服深蓝 | #2E3A54 | dark navy blue |
| 雾/阴影灰 | #B8C4C4 | cool grey |
| 肤色（鲁恩/因蒂斯） | #F2C49B | fair skin |
| 邮筒红 | #C8251A | pillar-box red |

## 光照与描边规则

- 主光源永远**左上**：高光在物件左上缘，右下为暗面；投影极淡或省略（prompt 已含 `no shadow`）
- 阴影色不用黑：主色相加深约 30%（如红砖暗面 #8C3D2E）
- 外轮廓 1px 深色描边（主色加深 50%），**不用纯黑**；内部色块之间不描边
- 顶光正午感：星露谷式明亮通透，拒绝黄昏长影、雾气、体积光（除非做天气变体，见 `references/vfx-weather.md`）

## 尺寸比例基准表

所有资产按同一比例尺，拼在一起才不崩：

| 资产 | 画布（godot_export 类别） | 比例要点 |
|---|---|---|
| 地面 tile | 32×32 | 基准单位 |
| 角色/纸娃娃层 | 32×48 | 二头身半，脚底贴画布底 |
| 门洞 | 建筑内 ≥32×40 | 角色能"走进"门 |
| 单层窗 | 建筑内 16-20px 高 | 层高 32-48px |
| 建筑立面 | 128×128 | 2-5 层按层高堆 |
| 大型公共建筑/地标 | 256×256（building_l） | 柱廊/大屋顶等内容多时升级此档，保证门洞 ≥40px（2026-08 证交所实测：128 档门洞仅 28px 不达标） |
| 树 | 64×64 | 冠径≈48，树干高≈24 |
| 道具/食物图标 | 32×32 | 视觉重心居中偏上 |
| 对话头像 | 64×64 | 胸像，肩以下裁掉 |
| 载具 | 160×128 | 侧视，长边≤160 |
| UI 组件 | 256×128 内适应 | 边框 9-slice 可切 |

## 纸娃娃画布与叠层规范

换装系统对齐机制：**所有人物层共用 32×48 画布，脚底贴 y=47，水平居中，并以一个 asset group 共享 transform**。同画布但逐层 bbox/fit 仍会产生比例漂移，因此 base/outfit/hair/acc 必须一次传给 `godot_export.py group layer ...`，由 union bbox 只计算一次 scale/origin/baseline。

- z-order（从下到上）：`base`（素体）→ `outfit`（服装）→ `hair`（发型）→ `acc`（首饰/手持物）
- 文件命名：`角色名_层名.png`，如 `loen_man01_base.png`、`loen_man01_outfit_frock.png`、`loen_man01_hair_sidepart.png`
- 首饰在 32×48 全身像仅 1-2px 示意；戒指/怀表链/胸针等细节靠 64×64 对话头像承载
- 组导出的 `.transform.json` sidecar 是资产 provenance 的一部分；任何单层重做都必须复用整组重新导出，不能只替换一个逐图 fit 结果。

## 时段罩色基准

天气/时段用 Godot CanvasModulate 罩色实现（不必重新生成，详见 `references/vfx-weather.md`）：

| 时段 | 罩色 |
|---|---|
| 白昼 | #FFFFFF |
| 黄昏 | #F0C8A0 |
| 夜晚 | #6B7FA8 |
| 雾天 | #C8D4D4（另叠半透明雾 sprite 层） |
