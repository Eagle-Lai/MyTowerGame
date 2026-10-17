# -*- coding: utf-8 -*-
"""
Batch reskin: all monster PNGs -> golden palette + light spots.
Generic per-pixel approach (works for any monster color scheme):
  - colorful pixels: hue -> golden hue, saturation slightly compressed,
    lightness kept EXACTLY (all shading/texture/outline structure intact)
  - neutral pixels (dark outline, whites, grays): untouched
  - spots: light density, deterministic per file (crc32 of path)
  - alpha channel: bit-identical to original

Usage:
    python reskin_batch.py <monsters_dir> [--density light] [--apply]
Without --apply it runs in report-only mode (no files written).
"""
import os, sys, zlib, io, base64, argparse
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reskin_monster_v2 import erode, pick_spots, SPOT_DENSITY

def dilate(mask, iters):
    m = mask.copy()
    for _ in range(iters):
        p = np.pad(m, 1, constant_values=False)
        m = (p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] |
             p[1:-1, :-2] | p[1:-1, 2:])
    return m

def big_white_regions(white_mask, erode_it=9, max_grow=80):
    """Large pure-white areas (bodies) vs small ones (eyes/details).
    Erode to find cores of big regions, then constrained-dilate back."""
    core = erode(white_mask, erode_it)
    if not core.any():
        return core
    grown = core
    for _ in range(max_grow):
        p = np.pad(grown, 1, constant_values=False)
        g2 = (p[1:-1, 1:-1] | p[:-2, 1:-1] | p[2:, 1:-1] |
              p[1:-1, :-2] | p[1:-1, 2:]) & white_mask
        if (g2 == grown).all():
            break
        grown = g2
    return grown

GOLDEN_HUE = 39.0 / 360.0
DARK_L = 0.24        # below -> outline/dark, keep
WHITE_S = 0.10       # below sat & above L -> whites, keep
WHITE_L = 0.85
SPOT_L = (0.20, 0.95)
SPOT_S = 0.10           # measured on post-transform saturation
SPOT_COLOR = (143, 100, 20)   # 8F6414 golden dark
EDGE_SOFT = 2.0

# ---------- vectorized RGB <-> HSL ----------
def rgb_to_hsl(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = rgb.max(-1); mn = rgb.min(-1)
    l = (mx + mn) / 2.0
    d = mx - mn
    s = np.where(d == 0, 0.0, d / (1 - np.abs(2 * l - 1) + 1e-12))
    s = np.clip(s, 0, 1)
    h = np.zeros_like(l)
    m = (d > 1e-12)
    idx = m & (mx == r); h[idx] = ((g - b)[idx] / d[idx]) % 6
    idx = m & (mx == g); h[idx] = (b - r)[idx] / d[idx] + 2
    idx = m & (mx == b); h[idx] = (r - g)[idx] / d[idx] + 4
    return h / 6.0, s, l

def hsl_to_rgb(h, s, l):
    def f(n):
        k = (n + h * 12) % 12
        a = s * np.minimum(l, 1 - l)
        return l - a * np.maximum(-1.0, np.minimum(np.minimum(k - 3, 9 - k), 1.0))
    return np.stack([f(0), f(8), f(4)], axis=-1)

def golden_transform(rgba):
    rgb = rgba[..., :3].astype(np.float64) / 255.0
    alpha = rgba[..., 3]
    h, s, l = rgb_to_hsl(rgb)
    # keep only: dark outline/silhouette (L<=0.24) and SMALL pure-white
    # regions (eye whites, small details); LARGE white areas = body -> golden cream
    op = alpha > 128
    white_mask = (s < 0.015) & (l >= 0.70) & op
    white_body = big_white_regions(white_mask) if white_mask.any() else white_mask
    # large BLACK bodies (black-furred monsters) -> dark golden brown;
    # thin outlines & small dark parts (pupils, nostrils) stay black
    dark_mask = (l <= 0.24) & op
    dark_body = big_white_regions(dark_mask, erode_it=5) if dark_mask.any() else dark_mask
    # protect pupils etc.: dark regions enclosed by eye whites
    if dark_body.any() and white_mask.any():
        dark_body &= ~dilate(white_mask, 6)
    # mid-gray neutral bodies (cool gray fur) -> golden tan
    gray_mask = (s < 0.015) & (l > 0.24) & (l < 0.70) & op
    gray_body = big_white_regions(gray_mask, erode_it=5) if gray_mask.any() else gray_mask
    colorful = ((s >= 0.015) & (l > DARK_L)) | white_body | dark_body | gray_body
    s2 = np.clip(s * 0.95 + 0.05, 0, 1)
    # saturation floor: low-sat grays/whites/creams become clearly golden
    s2 = np.where(colorful & (s < 0.15), np.maximum(s2, 0.12), s2)
    s2 = np.where(white_body, np.maximum(s2, 0.10), s2)
    s2 = np.where(dark_body, np.maximum(s2, 0.30), s2)
    # deepen shadows slightly; lift near-silhouette dark bodies a bit
    l2 = np.where(colorful & (l < 0.45), l * 0.93, l)
    l2 = np.where(colorful & (l > 0.24) & (l < 0.38), l * 1.12, l2)
    # dark bodies: lift from near-black into readable dark golden brown
    l2 = np.where(dark_body, 0.14 + l * 0.9, l2)
    l2 = np.clip(l2, 0, 1)
    new_rgb = hsl_to_rgb(np.full_like(h, GOLDEN_HUE), s2, l2)
    out_rgb = np.where(colorful[..., None], new_rgb, rgb)
    out = np.concatenate([np.clip(out_rgb * 255, 0, 255), alpha[..., None]], axis=-1)
    return out.astype(np.uint8), colorful, l2, s2

def add_spots(recolored, colorful, l, s, density_mult, seed, fur_area_hint=None):
    h, w = l.shape
    mask = colorful & (l > SPOT_L[0]) & (l < SPOT_L[1]) & (s > SPOT_S)
    core = erode(mask, 4)
    ys, xs = np.nonzero(core)
    if len(ys) == 0:
        return recolored
    rng = __import__("random").Random(seed)
    n_spots = max(4, int(len(ys) / 9000 * density_mult))
    spots = pick_spots(ys.tolist(), xs.tolist(), n_spots, rng)
    field = np.zeros((h, w), dtype=np.float64)
    yy, xx = np.mgrid[0:h, 0:w]
    for (cy, cx, ry, rx) in spots:
        y0, y1 = max(0, cy - int(ry) - 3), min(h, cy + int(ry) + 4)
        x0, x1 = max(0, cx - int(rx) - 3), min(w, cx + int(rx) + 4)
        dy = (yy[y0:y1, x0:x1] - cy) / ry
        dx = (xx[y0:y1, x0:x1] - cx) / rx
        d = np.sqrt(dx * dx + dy * dy)
        f = np.clip((1.0 - d) * (ry / EDGE_SOFT), 0, 1)
        field[y0:y1, x0:x1] = np.maximum(field[y0:y1, x0:x1], f)
    field *= core
    out = np.array(recolored, dtype=np.float64)
    sc = np.array(SPOT_COLOR, dtype=np.float64)
    t = field[..., None]
    out[..., :3] = out[..., :3] * (1 - t) + sc * t
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")

def thumb_b64(img, max_w=480, quality=82):
    im = img.convert("RGBA")
    w, h = im.size
    if w > max_w:
        im = im.resize((max_w, int(h * max_w / w)), Image.LANCZOS)
    bg = Image.new("RGB", im.size, (250, 250, 250))
    bg.paste(im, mask=im.split()[3])
    buf = io.BytesIO()
    bg.save(buf, "JPEG", quality=quality)
    return base64.b64encode(buf.getvalue()).decode()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--density", default="medium")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    mult = SPOT_DENSITY[a.density]

    pngs = []
    for dirpath, dirnames, filenames in os.walk(a.root):
        for fn in filenames:
            if fn.lower().endswith(".png") and not fn.lower().endswith("_golden.png"):
                p = os.path.join(dirpath, fn)
                rel = os.path.relpath(p, a.root).replace("\\", "/")
                # exclude UI parts & neutral shared assets: HP bar pieces,
                # shadow blobs, anything in a Skin/ subfolder or _Common
                if ("/Skin/" in rel or "/_Common/" in rel
                        or "HpBg" in fn or "HpFill" in fn or "Shadow" in fn):
                    print(f"SKIP {rel} (UI/neutral)")
                    continue
                pngs.append(p)
    pngs.sort()
    print(f"found {len(pngs)} png(s)")

    report = []
    ok = fail = 0
    for i, p in enumerate(pngs):
        rel = os.path.relpath(p, a.root).replace("\\", "/")
        try:
            img = Image.open(p)
            orig = img.convert("RGBA")
            arr = np.array(orig)
            rec_arr, colorful, l, s = golden_transform(arr)
            rec = Image.fromarray(rec_arr, "RGBA")
            seed = zlib.crc32(rel.encode("utf-8"))
            rec = add_spots(rec, colorful, l, s, mult, seed)
            # integrity: alpha must be identical
            assert (np.array(rec)[..., 3] == arr[..., 3]).all(), "alpha changed!"
            if a.apply:
                out_path = os.path.splitext(p)[0] + "_golden.png"
                rec.save(out_path)
            report.append((os.path.dirname(rel), os.path.basename(rel),
                           thumb_b64(orig), thumb_b64(rec)))
            ok += 1
            if (i + 1) % 20 == 0:
                print(f"  {i+1}/{len(pngs)}")
        except Exception as e:
            fail += 1
            print(f"FAIL {rel}: {e}")

    # html report
    report_path = a.report or os.path.join(a.root, "..", "..", "..",
        ".workbuddy", "reskin_preview", "reskin_batch_report.html")
    report_path = os.path.normpath(report_path)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    groups = {}
    for fam, name, t1, t2 in report:
        groups.setdefault(fam, []).append((name, t1, t2))
    html = ["<html><head><meta charset='utf-8'><style>",
            "body{font-family:Segoe UI,sans-serif;background:#fafafa;margin:20px}",
            "h1{font-size:20px} h2{font-size:16px;margin:28px 0 8px;"
            "border-bottom:2px solid #e8a93e;padding-bottom:4px}",
            ".pair{display:inline-block;margin:6px 14px 6px 0;text-align:center;"
            "background:#fff;border:1px solid #ddd;border-radius:8px;padding:8px}",
            ".pair img{width:230px;image-rendering:auto;display:block;margin:2px}",
            ".lbl{font-size:12px;color:#555;margin-top:4px}",
            ".row{display:flex;gap:0}",
            "</style></head><body>",
            f"<h1>Monster Reskin Report — golden + {a.density} spots</h1>",
            f"<p>{ok} succeeded, {fail} failed. Left = original, right = golden reskin.</p>"]
    for fam in sorted(groups):
        html.append(f"<h2>{fam}</h2><div>")
        for name, t1, t2 in groups[fam]:
            html.append(
                f"<div class='pair'><div class='row'>"
                f"<div><img src='data:image/jpeg;base64,{t1}'/>"
                f"<div class='lbl'>原版 original</div></div>"
                f"<div><img src='data:image/jpeg;base64,{t2}'/>"
                f"<div class='lbl'>换皮 golden</div></div>"
                f"</div><div class='lbl'>{name}</div></div>")
        html.append("</div>")
    html.append("</body></html>")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    print(f"report: {report_path}")
    print(f"DONE ok={ok} fail={fail} applied={a.apply}")

if __name__ == "__main__":
    main()
