#!/usr/bin/env python3
"""调色板一致性审查：用基准色板度量素材库每件资产的主色偏差。

基准色板 = art-direction.md 主调色板锚点 + 风格锚场景主色（可选多张）。
对每件资产取主色（alpha>100 像素，5bit 分箱前 5），计算到基准色的最近欧氏距离：
全部主色 Δ≤TOL → PASS；1 个超差 → REVIEW；≥2 个超差 → FLAG。

判定只是"提请复核"，不是结论——超差常见原因：基准缺口（如新色系资产）、
合法例外（vfx/神秘道具的途径色、他国调色板）、或真实漂移。审查结论必须
回到 references/art-review.md 的闭环里人工裁定并回填修方/基准。

用法：
    python3 palette_audit.py <assets_dir> [--anchor <场景图>]... [--tol 48] [--sheet <输出.png>]
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# art-direction.md 主调色板锚点（与文档同步维护）
MASTER = np.array([
    (0x8B, 0x5A, 0x2B), (0x6B, 0x3E, 0x1D), (0xD9, 0xA4, 0x41), (0xB4, 0x50, 0x3C),
    (0xE8, 0xDC, 0xC0), (0x5A, 0x6B, 0x7C), (0x4E, 0x9B, 0x3A), (0x2E, 0x6B, 0x28),
    (0xA8, 0xD9, 0x4E), (0x2E, 0x3A, 0x54), (0xB8, 0xC4, 0xC4),
    (0xF2, 0xC4, 0x9B),  # 肤色 fair skin（2026-08 审查回填）
    (0xC8, 0x25, 0x1A),  # 邮筒红 pillar red（2026-08 审查回填）
])


def palette_of(pixels, k):
    px = pixels.astype(np.uint32)
    bins = (px[:, 0] >> 3) << 10 | (px[:, 1] >> 3) << 5 | (px[:, 2] >> 3)
    vals, counts = np.unique(bins, return_counts=True)
    top = vals[counts.argsort()[::-1][:k]]
    return np.array([(((v >> 10) & 31) * 8 + 4, ((v >> 5) & 31) * 8 + 4, (v & 31) * 8 + 4)
                     for v in top])


def dedupe(pal, tol=40):
    keep = []
    for c in pal:
        if all(np.abs(np.array(c) - np.array(k)).sum() > tol for k in keep):
            keep.append(c)
    return np.array(keep) if keep else pal


def anchor_palette(path, k=30):
    a = np.array(Image.open(path).convert("RGB"))
    return palette_of(a.reshape(-1, 3), k)


def asset_dominant(path):
    a = np.array(Image.open(path).convert("RGBA"))
    px = a[a[..., 3] > 100][:, :3]
    return palette_of(px, 5) if len(px) else None


def audit(assets_dir, bench, tol):
    rows_out = []
    for root, _, files in os.walk(assets_dir):
        for f in sorted(files):
            if not f.endswith(".png"):
                continue
            p = os.path.join(root, f)
            dom = asset_dominant(p)
            if dom is None:
                continue
            rows = []
            for c in dom:
                d = float(np.sqrt(((bench.astype(int) - np.array(c)) ** 2).sum(axis=1)).min())
                rows.append((tuple(int(x) for x in c), round(d)))
            outliers = sum(1 for _, d in rows if d > tol)
            verdict = "PASS" if outliers == 0 else ("REVIEW" if outliers == 1 else "FLAG")
            rows_out.append((p, rows, max(d for _, d in rows), verdict))
    rows_out.sort(key=lambda r: ({"FLAG": 0, "REVIEW": 1, "PASS": 2}[r[3]], r[0]))
    return rows_out


def render_sheet(rows_out, bench, tol, dest):
    f24 = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 26)
    f18 = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 18)
    f14 = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 13)
    ROW_H, THUMB, W = 64, 56, 900
    sheet = Image.new("RGB", (W, 100 + len(rows_out) * ROW_H + 20), (245, 243, 238))
    dd = ImageDraw.Draw(sheet)
    dd.text((W // 2, 12), "素材库调色板一致性审查", font=f24, fill=(40, 35, 30), anchor="ma")
    for j, c in enumerate(bench[:18]):
        dd.rectangle([30 + j * 46, 48, 30 + j * 46 + 40, 78], fill=tuple(int(x) for x in c), outline=(90, 90, 90))
    dd.text((30, 84), "基准色板（前 18 色）", font=f14, fill=(110, 105, 95))
    VC = {"PASS": (46, 130, 60), "REVIEW": (200, 140, 20), "FLAG": (200, 50, 40)}
    for i, (p, rows, worst, v) in enumerate(rows_out):
        y = 100 + i * ROW_H
        img = Image.open(p).convert("RGBA")
        bb = img.split()[3].getbbox()
        crop = img.crop(bb) if bb else img
        sc = min((THUMB - 6) / crop.width, (THUMB - 6) / crop.height)
        disp = crop.resize((max(1, int(crop.width * sc)), max(1, int(crop.height * sc))), Image.NEAREST)
        ck = Image.new("RGB", (THUMB, THUMB), (190, 190, 190))
        ck.paste(disp, ((THUMB - disp.width) // 2, (THUMB - disp.height) // 2), disp)
        sheet.paste(ck, (10, y + 4))
        dd.text((74, y + 8), "/".join(p.split("/")[-2:]), font=f14, fill=(40, 35, 30))
        dd.text((74, y + 30), f"最差距离 {worst}", font=f14, fill=(110, 105, 95))
        for j, (c, d) in enumerate(rows):
            x = 300 + j * 110
            dd.rectangle([x, y + 10, x + 40, y + 40], fill=c, outline=(90, 90, 90))
            dd.text((x + 48, y + 18), f"Δ{d}", font=f14,
                    fill=(200, 50, 40) if d > tol else (110, 105, 95))
        dd.rectangle([W - 90, y + 14, W - 14, y + 42], outline=VC[v], width=2)
        dd.text((W - 52, y + 20), v, font=f18, fill=VC[v], anchor="ma")
    sheet.save(dest)
    return dest


def main():
    ap = argparse.ArgumentParser(description="素材库调色板一致性审查")
    ap.add_argument("assets_dir")
    ap.add_argument("--anchor", action="append", default=[], help="风格锚场景图（可多张）")
    ap.add_argument("--tol", type=int, default=48)
    ap.add_argument("--sheet", default=None, help="输出审查图 PNG 路径")
    args = ap.parse_args()
    bench = [MASTER]
    for a in args.anchor:
        bench.append(anchor_palette(a))
    bench = dedupe(np.vstack(bench))
    rows_out = audit(args.assets_dir, bench, args.tol)
    n = {"PASS": 0, "REVIEW": 0, "FLAG": 0}
    for p, rows, worst, v in rows_out:
        n[v] += 1
        print(f"{v:6s} Δ{worst:3d}  {'/'.join(p.split('/')[-2:])}")
    print(f"\n合计 PASS {n['PASS']} / REVIEW {n['REVIEW']} / FLAG {n['FLAG']}（基准 {len(bench)} 色，容差 {args.tol}）")
    if args.sheet:
        render_sheet(rows_out, bench, args.tol, args.sheet)
        print("审查图:", args.sheet)


if __name__ == "__main__":
    main()
