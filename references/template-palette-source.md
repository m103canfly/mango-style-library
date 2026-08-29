# 廷根模板色板来源与材质塑形规则

## 权威来源

用户指定的 `场景包_鲁恩王国.zip` 十张原始模板图是 `tingen_pixel_v3_hd` 的颜色来源权威。仓库内 `assets/scene-bible/visual/loen/` 已经做过逐图 192 色量化，只能作为地域 visual anchor，不能反向充当正式 RGB 提取源。

原始模板含连续色、生成噪声和大量近似 RGB，因此“收录模板里所有颜色”不可执行，也会破坏 10–24 色的单资产预算。仓库改为提交一份可重建、可审计的冻结注册表：

```bash
python scripts/extract_template_palette.py <场景包_鲁恩王国.zip>
```

提取器先按固定比例排除 HUD，再对十景做 Nearest 采样和 HSV 语义分层。聚类中心只用于定位；最终登记的每个 RGB 都必须是原图无 HUD 区域实际出现过的像素，不登记计算生成的平均色。输出包括：

- `assets/palettes/tingen-template-palette.json`：64 色 Master、来源文件 SHA-256、裁切和算法版本；
- `assets/palettes/tingen-materials.json`：材质子色板与语义 tone ramp；
- `assets/palettes/tingen-template-palette.png`：Nearest 预览。

运行中的 Codex/IDE/CI 只读这些已提交文件，禁止按本机图片动态采样。这样同一 Git commit 在不同代码代理、图像后端和机器上得到同一颜色合同。

## 为什么不会退化成平涂

Master Palette 只是允许使用的颜色词表，不是把整张图一次性量化的目标。正式 1× 资产必须按材质 ID 选择局部子色板。每个可塑形材质还登记 `tone_ramp`：

- `deep_shadow` / `shadow`：结构转折、接触阴影和遮挡；
- `midtone`：材质固有色；
- `light` / `highlight`：左上主光、边角磨损或反光；
- 小尺寸人物皮肤可以使用三阶 `shadow / midtone / highlight`。

`minimum_tone_roles` 是自动复核下限。资产所有 RGB 都合法、但某个声明材质没有使用足够明暗角色时，`audit.json` 会记录 `flat-shading review required`，结果保持 `REVIEW`，不能仅凭色板闭包晋升 Gold Anchor。

自动检查不能识别所有材质遮罩，也不能判断像素 cluster 是否画得好。因此人工 Style & palette 评分仍需检查：左上光、块状明暗、材质纹理、冷暖/色相偏移、轮廓内外对比，以及是否出现机械渐变或噪点抖动。

## 禁止事项

- 禁止将十张模板的全部 RGB 直接并入运行时登记表。
- 禁止使用仓库内逐图量化后的 Scene Bible visual PNG 重新推导 Master。
- 禁止对建筑、人物或其他复合资产执行整图最近色重映射后宣称可交付。
- 禁止运行时依据当前目录中的图片扩展色板。
- 禁止把 HD 生成图缩小、量化或 remap 后直接作为原生 1× 资产。
