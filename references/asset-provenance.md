# Asset Provenance

`assets/asset-registry-template.csv` 是生产资产的索引台账；标准交付目录里的 `manifest.json`、`audit.json`、`source_reference.json` 和 `import_contract.json` 是逐资产机器记录。每个原生 1× PNG 占一行；同一纸娃娃组或动画组共享 `asset_group_id`、画布和 `(32,96)` 锚点。

## Required before REVIEW

- identity：`id`、`asset_group_id`、`category`、`nation`、`slug`；
- source：`source_png`、`source_sha256`；
- generation：`prompt`、`prompt_sha256`、`model`、`backend`、`seed`（后端无 seed 时写 `unsupported`）；
- references：`anchor_ids`、`scene_bible_ids`；没有使用时写空，不得用模糊文件名代替 manifest id；
- color：`palette_ids`、`palette_version`；
- geometry：`profile_id`、精确 dimensions、anchor、`anchor_coordinate_kind`；HD reference 候选另记 `transform_id`，正式 1× 不做 fit；
- version：`asset_version`、`parent_asset_id`、`status`。

## Required before APPROVE

在上述字段之外，必须填写 `review_profile`、`review_score`、`review_verdict`、`reviewer`、`reviewed_at`，并保留 `art_score.py` 的 review JSON。动画还必须填写 `motion_report`。

多值字段用 `|` 分隔并保持 manifest id；时间使用带时区的 ISO 8601。修改资产时新增版本行并通过 `parent_asset_id` 指向上一版，不覆盖历史审查记录。生成式来源必须写 `generated_hd_reference`；像素重绘后的正式来源写 `pixel_redraw_from_generated_reference`，两者不能混为一条。

## Authority constraints

- `anchor_ids` 只能引用 `assets/anchors/style-anchor-manifest.yaml` 中存在的 id；production 资产至少一个同类别 anchor 必须是 `approved`。
- `scene_bible_ids` 只能作为地域软参考；它不能填进 `anchor_ids`。
- `review_verdict=APPROVE` 但 score <90、critical fail 未清除或 provenance 缺字段，视为无效记录。
- `runtime_ready` 还要求廷根 RGB 登记色板已批准，且 `import_contract.json` 中入口、碰撞、导航、同屏比例均通过；PNG 图片通过不能替代这些工程验证。
