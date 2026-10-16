# -*- coding: utf-8 -*-
"""
把三张塔渲染截图（不透明、深蓝底 #223B54 + 网格 + 贯穿全图的十字准星 + 投影）做成透明底 UI 图标。

思路（不靠一张图卡死颜色阈值，靠"背景模型 + 连通性"）：
  1) 背景模型 = ①调色板颜色（深蓝底、网格线的实际色值，从图片边框统计得出）
               ②"深蓝的等比例压暗"（navy × k）—— 投影就是底色叠半透明黑，
                  它在 RGB 空间里落在"黑→navy"这条射线上，用射线投影残差判定。
  2) 从所有边框像素做**洪水填充**：只吃"落在背景模型内"的像素。
     背景连通且连到边框，塔身是封闭实体 —— 即使塔身上有和投影/底色同族的深色块，
     也因为没有连通路径而绝不会被误删。
  3) 边缘 1~2px 用"到背景模型的距离"做 alpha 渐变，避免锯齿硬边。
  4) 抠准星：那条十字线是**半透明叠加**，压在不同底色上颜色会变；
     定位靠"命中最多的那一列/行"，判废靠**"与垂直方向邻居明显不同"**，
     修补值取邻居中位数（塔身保持不透明，不能挖成透明洞）。
  5) 按 alpha 裁到塔身外接框 → 加边距 → 补正方形 → LANCZOS 重采样到统一尺寸。

用法：
  python tower_icon_bg_remove.py            # 只输出到 tmp，不写工程
  python tower_icon_bg_remove.py --apply    # 覆盖写入 Assets/_UIAssets/UI/
"""
import argparse
import os
from collections import Counter, deque

import numpy as np
from PIL import Image

CLIP_DIR = r"C:\Users\78296\.workbuddy\clipboard-images"

# 语义映射：附件 → 项目里的三张塔图标（已按 _UIAssets/Tower 的塔身美术逐一核对）
JOBS = [
    ("Normal", "clipboard-2026-10-15T11-36-46-923Z-ef3f3f3c.png", "UI_TowerIcon_Normal.png"),
    ("Power",  "clipboard-2026-10-15T11-36-46-928Z-9986857c.png", "UI_TowerIcon_Power.png"),
    ("Retard", "clipboard-2026-10-15T11-36-46-931Z-07716692.png", "UI_TowerIcon_Retard.png"),
]

ASSET_DIR = r"D:\FreedomTower_1\Assets\_UIAssets\UI"

OUT_SIZE = 96         # 统一输出边长（与 HUD 建造栏 84×84 的显示尺寸基本 1:1，最清晰且体积最小）
MARGIN_RATIO = 0.05   # 裁切后四周留白比例
BG_TOL = 12.0         # 洪水填充：到背景模型距离 <= 该值即视为背景
SOFT_LO, SOFT_HI = 7.0, 30.0   # 边缘 alpha 渐变区间
CROSS_TOL = 34.0      # 准星色命中阈值（只用于定位那条线在哪一列/行）
BAND_EXPAND = 3       # 准星带宽：核心列/行 左右各扩这么多列（覆盖线宽 + 抗锯齿边）
BG_TOL_BAND = 42.0    # 带内判"是不是落在背景上"的宽松阈值（带外的准星抗锯齿边色差可达 30+）
CROSS_ANOMALY = 8.0   # 带内判"压在塔身上"的修补阈值：与带外邻居中位数差 > 该值才补


def border_palette(rgb: np.ndarray, ring: int = 3):
    """从四边 ring 像素统计背景调色板（深蓝底 + 网格线），并返回出现最多的底色。"""
    h, w, _ = rgb.shape
    px = np.concatenate([
        rgb[:ring, :, :].reshape(-1, 3),
        rgb[-ring:, :, :].reshape(-1, 3),
        rgb[:, :ring, :].reshape(-1, 3),
        rgb[:, -ring:, :].reshape(-1, 3),
    ], axis=0)
    counts = Counter(map(tuple, px.tolist()))
    base = np.array(max(counts.items(), key=lambda kv: kv[1])[0], dtype=np.float32)
    thresh = max(5, int(len(px) * 0.002))
    palette = [np.array(c, dtype=np.float32) for c, n in counts.items() if n >= thresh]
    return base, palette, counts


def bg_distance(rgb: np.ndarray, base: np.ndarray, palette: list) -> np.ndarray:
    """
    每个像素到"背景模型"的距离 = min(到各调色板颜色的距离, 到"黑→底色"射线的残差)。
    投影 = 底色叠半透明黑，落在射线上；残差小就说明它只是被压暗的底色。
    """
    h, w, _ = rgb.shape
    flat = rgb.reshape(-1, 3).astype(np.float32)
    d = np.full(flat.shape[0], 1e9, dtype=np.float32)
    for c in palette:
        np.minimum(d, np.sqrt(((flat - c) ** 2).sum(axis=1)), out=d)

    denom = float((base * base).sum())
    k = np.clip(flat @ base / denom, 0.0, 1.05)
    resid = np.sqrt(((flat - k[:, None] * base[None, :]) ** 2).sum(axis=1))
    np.minimum(d, resid, out=d)
    return d.reshape(h, w)


def flood_bg_mask(cand: np.ndarray) -> np.ndarray:
    """从四边洪水填充：只在 cand=True 的像素上扩散，返回 True=背景。"""
    h, w = cand.shape
    mask = np.zeros((h, w), dtype=bool)
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            if cand[y, x] and not mask[y, x]:
                mask[y, x] = True
                dq.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if cand[y, x] and not mask[y, x]:
                mask[y, x] = True
                dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and cand[ny, nx] and not mask[ny, nx]:
                mask[ny, nx] = True
                dq.append((ny, nx))
    return mask


def find_crosshair(rgb: np.ndarray):
    """定位那条贯穿全图的十字线所在的行/列（背景段颜色准，取命中最多的一列/一行）。"""
    h, w, _ = rgb.shape
    edge = np.concatenate([rgb[0:3].reshape(-1, 3), rgb[:, 0:3].reshape(-1, 3)], axis=0).astype(np.int32)
    bright = edge[edge.sum(axis=1) > 230]
    if len(bright) == 0:
        return None, None
    color = np.array(max(Counter(map(tuple, bright.tolist())).items(), key=lambda kv: kv[1])[0], dtype=np.float32)
    dist = np.sqrt(((rgb.astype(np.float32) - color) ** 2).sum(axis=2))
    hit = dist <= CROSS_TOL
    colcnt, rowcnt = hit.sum(axis=0).astype(float), hit.sum(axis=1).astype(float)

    def band(cnt, length, idx):
        peak = cnt[idx]
        if peak < length * 0.20 or peak < 5 * (np.median(cnt) + 1):
            return None
        out = {idx}
        for step in (-1, 1):
            i = idx + step
            while 0 <= i < len(cnt) and cnt[i] >= peak * 0.35:
                out.add(i)
                i += step
        return out

    return band(colcnt, h, int(np.argmax(colcnt))), band(rowcnt, w, int(np.argmax(rowcnt))), color


def resolve_crosshair(rgb: np.ndarray, mask: np.ndarray, dist: np.ndarray, cols, rows):
    """
    处理准星带（核心列/行 + 左右各扩 BAND_EXPAND，覆盖线宽与抗锯齿边）。

    带内逐像素二选一：
      · 判背景 —— 带外左右（或上下）最近的两个像素**都是背景**，且本像素到背景模型的距离
        也在宽松阈值内 → 它在背景上 → 直接判背景（alpha=0）。
        【为什么要"两个条件都满足"】只看邻居会把细塔身（比如 Normal 的炮管）误当背景挖空；
        只看颜色又漏掉抗锯齿边。两个条件一起才既安全又干净。
      · 否则判塔身 —— 它在塔身之上 → 用带外邻居的中位数补色（保持不透明），
        只在"与邻居中位数差 > CROSS_ANOMALY"时才补，避免把塔身真实细节磨平。

    返回 (force_bg 掩码, 修补像素数)。force_bg 只落在"两侧都是背景"的位置，
    不会给洪水填充开出通往塔身内部的新通路。
    """
    h, w, _ = rgb.shape
    if not cols and not rows:
        return np.zeros((h, w), dtype=bool), 0
    band_c, band_r = set(), set()
    for c in (cols or ()):
        band_c.update(range(c - BAND_EXPAND, c + BAND_EXPAND + 1))
    for r in (rows or ()):
        band_r.update(range(r - BAND_EXPAND, r + BAND_EXPAND + 1))
    band_c = {c for c in band_c if 0 <= c < w}
    band_r = {r for r in band_r if 0 <= r < h}

    force_bg = np.zeros((h, w), dtype=bool)
    fixed = 0

    def scan(lines, in_band, limit, step):
        i = lines + step
        while 0 <= i < limit and i in in_band:
            i += step
        return i if 0 <= i < limit else None

    # 竖带（在横带上的像素交给横带处理，避免重复）
    for x in sorted(band_c):
        for y in range(h):
            if y in band_r:
                continue
            xl = scan(x, band_c, w, -1)
            xr = scan(x, band_c, w, +1)
            if xl is None or xr is None:
                continue
            if mask[y, xl] and mask[y, xr] and dist[y, x] <= BG_TOL_BAND:
                force_bg[y, x] = True
                continue
            samples = [rgb[y, i] for i in (xl, xr, xl - 1, xr + 1)
                       if 0 <= i < w and i not in band_c and not mask[y, i]]
            if not samples:
                continue
            ref = np.median(np.array(samples, dtype=np.float32), axis=0)
            if float(np.linalg.norm(rgb[y, x].astype(np.float32) - ref)) > CROSS_ANOMALY:
                rgb[y, x] = ref.astype(np.uint8)
                fixed += 1

    # 横带
    for y in sorted(band_r):
        for x in range(w):
            yl = scan(y, band_r, h, -1)
            yr = scan(y, band_r, h, +1)
            if yl is None or yr is None:
                continue
            if mask[yl, x] and mask[yr, x] and dist[y, x] <= BG_TOL_BAND:
                force_bg[y, x] = True
                continue
            samples = [rgb[i, x] for i in (yl, yr, yl - 1, yr + 1)
                       if 0 <= i < h and i not in band_r and not mask[i, x]]
            if not samples:
                continue
            ref = np.median(np.array(samples, dtype=np.float32), axis=0)
            if float(np.linalg.norm(rgb[y, x].astype(np.float32) - ref)) > CROSS_ANOMALY:
                rgb[y, x] = ref.astype(np.uint8)
                fixed += 1

    return force_bg, fixed


def drop_specks(alpha: np.ndarray, min_area: int = 8) -> int:
    """删掉面积过小的孤立连通块（准星末端/投影残留的 1~3px 碎点）。"""
    h, w = alpha.shape
    solid = alpha > 0
    seen = np.zeros((h, w), dtype=bool)
    killed = 0
    for sy in range(h):
        for sx in range(w):
            if not solid[sy, sx] or seen[sy, sx]:
                continue
            comp, dq = [], deque([(sy, sx)])
            seen[sy, sx] = True
            while dq:
                y, x = dq.popleft()
                comp.append((y, x))
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1),
                               (y - 1, x - 1), (y - 1, x + 1), (y + 1, x - 1), (y + 1, x + 1)):
                    if 0 <= ny < h and 0 <= nx < w and solid[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True
                        dq.append((ny, nx))
            if len(comp) < min_area:
                for y, x in comp:
                    alpha[y, x] = 0
                killed += len(comp)
    return killed


def build_icon(src_path: str) -> Image.Image:
    im = Image.open(src_path).convert("RGB")
    rgb = np.asarray(im).astype(np.uint8).copy()
    h, w, _ = rgb.shape
    base, palette, counts = border_palette(rgb)

    dist = bg_distance(rgb, base, palette)
    mask = flood_bg_mask(dist <= BG_TOL)

    # ---- 抠准星：先按邻居判定/修补，再带着 force_bg 重算背景掩码 ----
    cols, rows, line_color = find_crosshair(rgb)
    force_bg, fixed = resolve_crosshair(rgb, mask, dist, cols, rows)

    dist = bg_distance(rgb, base, palette)
    mask = flood_bg_mask((dist <= BG_TOL) | force_bg)

    alpha = np.full((h, w), 255.0, dtype=np.float32)
    alpha[mask] = 0.0
    ring = np.zeros((h, w), dtype=bool)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        ring |= (~mask) & np.roll(mask, (dy, dx), axis=(0, 1))
    soft = np.clip((dist - SOFT_LO) / (SOFT_HI - SOFT_LO), 0.0, 1.0) * 255.0
    alpha[ring] = np.minimum(alpha[ring], soft[ring])

    alpha = np.clip(alpha, 0, 255).astype(np.uint8)
    killed = drop_specks(alpha)
    out = Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), "RGBA")

    ys, xs = np.nonzero(alpha > 8)
    if len(ys) == 0:
        raise RuntimeError("全图被判成背景了：%s" % src_path)
    cw, ch = int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)
    out = out.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))

    side = int(round(max(cw, ch) * (1 + 2 * MARGIN_RATIO)))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(out, ((side - cw) // 2, (side - ch) // 2), out)
    if side != OUT_SIZE:
        canvas = canvas.resize((OUT_SIZE, OUT_SIZE), Image.LANCZOS)

    print("  [%s] %dx%d 调色板%d色 填充掉%.1f%% 准星列%s行%s修补%dpx 去碎点%dpx 内容框%dx%d -> %s"
          % (os.path.basename(src_path), w, h, len(palette),
             float(mask.sum()) / (h * w) * 100.0,
             sorted(cols) if cols else "-", sorted(rows) if rows else "-", fixed, killed,
             cw, ch, canvas.size))
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--out-dir", default=r"D:\FreedomTower_1\.workbuddy\tmp_icons")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    for tag, clip, target in JOBS:
        icon = build_icon(os.path.join(CLIP_DIR, clip))
        if args.apply:
            dst = os.path.join(ASSET_DIR, target)
            icon.save(dst, "PNG", optimize=True)
            print("  -> 已写入 %s (%d 字节)" % (dst, os.path.getsize(dst)))
        else:
            icon.save(os.path.join(args.out_dir, target), "PNG")
            preview = Image.new("RGBA", (OUT_SIZE, OUT_SIZE), (42, 49, 56, 255))
            preview.alpha_composite(icon)
            preview.save(os.path.join(args.out_dir, "preview_%s.png" % tag), "PNG")


if __name__ == "__main__":
    main()
