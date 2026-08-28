# Asset Provenance

`assets/asset-registry-template.csv` 是生产资产的最小可追溯记录。每个导出 PNG 占一行；同一纸娃娃组或动画组共享 `asset_group_id` 和 `transform_id`。

## Required before REVIEW

- identity：`id`、`asset_group_id`、`category`、`nation`、`slug`；
- source：`source_png`、`source_sha256`；
- generation：`prompt`、`prompt_sha256`、`model`、`backend`、`seed`（后端无 seed 时写 `unsupported`）；
- references：`anchor_ids`、`scene_bible_ids`；没有使用时写空，不得用模糊文件名代替 manifest id；
- color：`palette_ids`、`palette_version`；
- geometry：`transform_id`、`transform_path`；静态 tile 也保留单图 transform；
- version：`asset_version`、`parent_asset_id`、`status`。

## Required before APPROVE

在上述字段之外，必须填写 `review_profile`、`review_score`、`review_verdict`、`reviewer`、`reviewed_at`。动画还必须填写 `motion_report`。

多值字段用 `|` 分隔并保持 manifest id；时间使用带时区的 ISO 8601。修改资产时新增版本行并通过 `parent_asset_id` 指向上一版，不覆盖历史审查记录。

## Authority constraints

- `anchor_ids` 只能引用 `assets/anchors/style-anchor-manifest.yaml` 中存在的 id；production 资产至少一个同类别 anchor 必须是 `approved`。
- `scene_bible_ids` 只能作为地域软参考；它不能填进 `anchor_ids`。
- `review_verdict=APPROVE` 但 score <90、critical fail 未清除或 provenance 缺字段，视为无效记录。
