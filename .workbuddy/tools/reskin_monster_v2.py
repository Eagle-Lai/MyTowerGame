# -*- coding: utf-8 -*-
"""
Reskin v2: golden palette remap + procedural spots on fur regions.
Silhouette/composition unchanged; spots only cover fur-classified pixels.

Usage:
    python reskin_monster_v2.py <input.png> <out.png> [--spots light|medium|dense] [--seed N]
"""
import sys, os, argparse, random
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reskin_monster import SRC_ANCHORS, NEUTRAL, SKIN_PRESETS, hexc, reskin, dist2

FUR_KEYS = ["fur_hi", "fur_main", "fur_sh", "fur_deep", "fur_mid2", "fur_hi2"]
SPOT_DENSITY = {"light": 0.5, "medium": 1.0, "dense": 1.8}  # multiplier
ERODE_ITERS = 4          # keep spots away from outline edges
EDGE_SOFT = 2.0          # px of antialiased edge
MIN_GAP = 1.35           # min gap between spot centers (x radius)

def fur_mask(img):
    rgba = np.array(img.convert("RGBA"), dtype=np.float64)
    rgb = rgba[..., :3]
    all_anchors = list(SRC_ANCHORS.keys()) + list(NEUTRAL.keys())
    mats = np.array([SRC_ANCHORS[k] for k in SRC_ANCHORS] +
                    [NEUTRAL[k] for k in NEUTRAL], dtype=np.float64)
    d2 = np.stack([dist2(rgb, s) for s in mats], axis=-1)
    nearest = d2.argmin(axis=-1)
    fur_idx = [all_anchors.index(k) for k in FUR_KEYS]
    is_fur = np.isin(nearest, fur_idx)
    return is_fur, rgba[..., 3]

def erode(mask, iters):
    m = mask.copy()
    for _ in range(iters):
        p = np.pad(m, 1, constant_values=False)
        m = (p[1:-1, 1:-1] & p[:-2, 1:-1] & p[2:, 1:-1] &
             p[1:-1, :-2] & p[1:-1, 2:])
    return m

def pick_spots(cand_ys, cand_xs, n, rng):
    """Poisson-ish rejection: no center inside another spot's ellipse."""
    chosen = []
    tries = 0
    while len(chosen) < n and tries < n * 200:
        tries += 1
        i = rng.randrange(len(cand_ys))
        y, x = cand_ys[i], cand_xs[i]
        ry, rx = rng.uniform(11, 24), rng.uniform(13, 30)
        ok = True
        for (cy, cx, cry, crx) in chosen:
            dx = (x - cx) / (crx * MIN_GAP)
            dy = (y - cy) / (cry * MIN_GAP)
            if dx * dx + dy * dy < 1.0:
                ok = False
                break
        if ok:
            chosen.append((y, x, ry, rx))
    return chosen

def add_spots(recolor_img, orig_img, spot_color, density_mult, seed):
    is_fur, alpha = fur_mask(orig_img)
    core = erode(is_fur, ERODE_ITERS)
    ys, xs = np.nonzero(core)
    if len(ys) == 0:
        return recolor_img

    rng = random.Random(seed)
    h, w = is_fur.shape
    fur_area = int(is_fur.sum())
    # ~1 spot per 9000 fur px at medium density
    n_spots = max(3, int(fur_area / 9000 * density_mult))
    spots = pick_spots(ys.tolist(), xs.tolist(), n_spots, rng)

    # build soft field
    field = np.zeros((h, w), dtype=np.float64)
    yy, xx = np.mgrid[0:h, 0:w]
    for (cy, cx, ry, rx) in spots:
        y0, y1 = max(0, cy - int(ry) - 3), min(h, cy + int(ry) + 4)
        x0, x1 = max(0, cx - int(rx) - 3), min(w, cx + int(rx) + 4)
        dy = (yy[y0:y1, x0:x1] - cy) / ry
        dx = (xx[y0:y1, x0:x1] - cx) / rx
        d = np.sqrt(dx * dx + dy * dy)  # 1.0 at ellipse edge
        f = np.clip((1.0 - d) * (ry / EDGE_SOFT), 0, 1)
        field[y0:y1, x0:x1] = np.maximum(field[y0:y1, x0:x1], f)

    field *= core  # clip to fur region

    out = np.array(recolor_img, dtype=np.float64)
    sc = np.array(spot_color, dtype=np.float64)
    t = field[..., None]
    out[..., :3] = out[..., :3] * (1 - t) + sc * t
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input"); ap.add_argument("output")
    ap.add_argument("--preset", default="golden")
    ap.add_argument("--spots", default="medium", choices=["light", "medium", "dense", "none"])
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    img = Image.open(a.input)
    preset = SKIN_PRESETS[a.preset]
    recolored = reskin(img, preset)
    if a.spots != "none":
        spot_color = hexc(preset["fur_deep"])
        recolored = add_spots(recolored, img, spot_color, SPOT_DENSITY[a.spots], a.seed)
    os.makedirs(os.path.dirname(a.output) or ".", exist_ok=True)
    recolored.save(a.output)
    print("saved", a.output)

if __name__ == "__main__":
    main()
