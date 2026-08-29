# mango-style-library

廷根 2D 像素项目的 AI Art Direction System：`tingen_pixel_v3_hd` 原生 1× 合同、模板派生固定 RGB、带 tone ramp 的材质子色板、分类 Gold Anchors、九地区 90 景 Scene Bible、四向 64×96 人物动画、评分审查、provenance 和 Godot 回归管线。

入口见 `SKILL.md`。生成式图片只作 HD 参考；正式资产用 `scripts/package_asset.py` 打包并由 `scripts/validate_delivery.py` 复核。修改管线后运行 `bash scripts/run_art_regression.sh`；发布前运行 `python scripts/validate_project_profile.py --strict`。
