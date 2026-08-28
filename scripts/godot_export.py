#!/usr/bin/env python3
"""Godot 直出后处理：把 image_generation 产出的 PNG 处理成可直接导入 Godot 的像素网格素材。

处理链：去左下「AI生成」水印区（tile 类改用对侧镜像填补，不留透明洞）→ 透明内容裁剪 → 缩放到类别目标像素网格 → 调色板量化 → 按类别归档。

注意：全幅纹理（tile）必须用 opaque 背景生成——transparent 生成全幅纹理可能出现 alpha 通道整体失效。

用法：
    python3 godot_export.py <input.png> <category> <out_dir> [--name slug]

category 与目标画布（宽x高）：
    tile      32x32    地面/纹理（内容拉伸铺满整个画布）
    icon      32x32    道具/食物/神秘道具图标（适应画布，居中）
    ui        256x128  UI 组件（适应画布，居中）
    character 32x48    角色单帧（适应画布，贴底居中）
    layer     32x48    纸娃娃服装/发型/首饰层（同 character 画布，叠层即对齐）
    portrait  64x64    对话头像胸像（适应画布，居中）
    building  128x128  建筑立面（适应画布，贴底居中）
    building_l 256x256 大型公共建筑/地标（适应画布，贴底居中；128 装不下门洞 ≥40px 时用）
    plant     64x64    植物（适应画布，贴底居中）
    prop      64x64    大件道具/装饰/动物（适应画布，居中）
    vehicle   160x128  载具（适应画布，贴底居中）
    vfx       64x64    特效（适应画布，居中）

产物直接拖进 Godot 工程即可作原型素材；正式品质仍建议美术按图重绘（AI 图非逐格原生像素）。
"""
import argparse
import os

import numpy as np
from PIL import Image

# category: (canvas_w, canvas_h, resize_mode, anchor)
CANVAS = {
    "tile": (32, 32, "stretch", "center"),
    "icon": (32, 32, "fit", "center"),
    "ui": (256, 128, "fit", "center"),
    "character": (32, 48, "fit", "bottom"),
    "layer": (32, 48, "fit", "bottom"),
    "portrait": (64, 64, "fit", "center"),
    "building": (128, 128, "fit", "bottom"),
    "building_l": (256, 256, "fit", "bottom"),
    "plant": (64, 64, "fit", "bottom"),
    "prop": (64, 64, "fit", "center"),
    "vehicle": (160, 128, "fit", "bottom"),
    "vfx": (64, 64, "fit", "center"),
}

# 左下水印区：x < WM_X 且 y > 1-WM_H 的区域整体置透明（「AI生成」水印固定位）
WM_X, WM_H = 0.30, 0.10


def erase_watermark(img):
    """把左下水印区 alpha 置 0。返回新图。"""
    w, h = img.size
    px = img.load()
    for y in range(int(h * (1 - WM_H)), h):
        for x in range(int(w * WM_X)):
            r, g, b, a = px[x, y]
            px[x, y] = (r, g, b, 0)
    return img


def repair_tile_watermark(img):
    """tile 全幅纹理不能留透明洞：用对侧（右上）同尺寸区域 180° 翻转填补水印区。"""
    w, h = img.size
    a = np.array(img)
    y0, x0 = int(h * (1 - WM_H)), int(w * WM_X)
    zh, zw = h - y0, x0
    a[y0:h, 0:x0] = a[0:zh, w - zw:w][::-1, ::-1]
    return Image.fromarray(a)


def process(inp, category, out_dir, name=None):
    if category not in CANVAS:
        raise SystemExit(f"未知 category: {category}，可选 {list(CANVAS)}")
    img = Image.open(inp).convert("RGBA")
    img = erase_watermark(img)
    if category == "tile":
        img = repair_tile_watermark(img)

    # 清低 alpha 噪点地板：AI 透明底图常带满幅微弱噪点（alpha<64），
    # 会把 alpha 包围盒撑到满幅，fit 缩放按包围盒计算 → 逐帧/逐件缩放抖动
    a = np.array(img)
    a[a[..., 3] < 64, 3] = 0
    img = Image.fromarray(a)

    bbox = img.getbbox()  # 透明内容裁剪
    if bbox:
        img = img.crop(bbox)

    tw, th, mode, anchor = CANVAS[category]
    if mode == "stretch":
        canvas = img.resize((tw, th), Image.LANCZOS)
    else:
        scale = min(tw / img.width, th / img.height)
        nw, nh = max(1, round(img.width * scale)), max(1, round(img.height * scale))
        resized = img.resize((nw, nh), Image.LANCZOS)
        canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        x = (tw - nw) // 2
        y = (th - nh) // 2 if anchor == "center" else th - nh
        canvas.paste(resized, (x, y))

    # 调色板量化，强化像素感（FASTOCTREE 支持 RGBA）
    canvas = canvas.quantize(colors=64, method=Image.FASTOCTREE).convert("RGBA")

    slug = name or os.path.splitext(os.path.basename(inp))[0]
    dest_dir = os.path.join(out_dir, category)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, f"{slug}.png")
    canvas.save(dest)
    print(f"[{category}] {dest}  ({tw}x{th})")
    return dest


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="AI 生成图 → Godot 直出像素素材")
    ap.add_argument("input")
    ap.add_argument("category", choices=list(CANVAS))
    ap.add_argument("out_dir")
    ap.add_argument("--name", default=None, help="输出文件名（不含扩展名），建议英文 slug")
    args = ap.parse_args()
    process(args.input, args.category, args.out_dir, args.name)
