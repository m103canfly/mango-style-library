# 廷根资产到 Godot 的交付路径

生成式图片是 HD 设计/动作参考，不能直接进引擎。Godot 只接收按 `tingen_pixel_v3_hd` 原生 1× 重绘、打包和复核的资产。

## 三段职责

1. **参考阶段**：Agent 绑定 approved Gold Anchor、地域 Scene Bible 和任务合同生成 HD 参考，登记 prompt/model/backend/source hash。
2. **像素制作阶段**：像素画师在任务规定的精确 1× 画布中重绘；不得缩小生成图、全图最近色量化或用分数缩放修尺寸。
3. **引擎阶段**：`package_asset.py` 生成标准目录，`validate_delivery.py` 复核 PNG/Alpha/色板/预览/Manifest；Godot 再验证入口、碰撞、导航和同屏比例。

## Godot 导入固定项

- Texture Filter：Nearest。
- Mipmaps：关闭。
- Compression：Lossless 或经项目批准的像素安全模式。
- Repeat：只对合同声明 `tileable=true` 的纹理开启。
- Sprite、Node2D、TileMapLayer 的位置和缩放使用整数值。
- 不得从 PNG Alpha 自动生成门、碰撞、遮挡或导航。

标准 `import_contract.json` 初始把 runtime validation 标为 pending；完成下列四项后才能改为 passed：

- 入口宽度与交互点正确；
- 碰撞形状来自显式项目数据；
- 导航区域/障碍来自显式项目数据；
- 与 64×64 tile、64×96 人物同屏比例通过。

## 类别速查

| 类别 | 项目规格 | 引擎注意 |
|---|---|---|
| 地形 tile | 原生 64×64；审核样板为同一 tile 精确 3×3 | Terrain 变体独立制作，不能靠平滑缩放 |
| 人物 | 每帧完整 64×96，锚点 `(32,96)` | 至少四向；步行 2 格/秒、跑步 5 格/秒由节点速度控制 |
| 立面组件 | 96–192px，16px 对齐，任务写死尺寸 | 门洞/窗/遮挡层按合同拆分 |
| 建筑组合 | 384–1024px，任务写死尺寸 | 底边中点锚点；入口与碰撞独立文件 |
| 地标组合 | 1024–2048px | 先验证同屏比例和显存/加载策略 |
| 廷根市政厅 | 1024–1536px 专项范围 | 公共门洞净宽至少 64px |
| UI/VFX/道具 | 专项合同规定 | 不允许从旧默认尺寸猜测 |

## 场景整合

- 道路、地块和建筑基线只用 0°/90°；规划连接只用精确 45°。
- 北向朝上，正交投影，无透视汇聚。
- 白天左上主光、右下暗面必须在所有素材中一致。
- 接触阴影若烘焙进 PNG，使用登记色和硬 Alpha 像素/抖动图案；禁止半透明高斯软影。需要软光时由 Godot 项目级 Shader/Light2D 统一实现。
- Tile 边界、Y-Sort、前景遮挡和建筑入口必须在可玩竖切中验证，Scene Bible 只能提供地域观感参考。

图片审计通过不等于 `runtime_ready`。只有 Profile 色板批准、标准目录完整、评分通过且 Godot runtime validation 全部 passed，资产才可进入项目正式库。
