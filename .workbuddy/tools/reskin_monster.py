# -*- coding: utf-8 -*-
"""
Monster sprite reskin via anchor-palette remapping.
Keeps silhouette / composition / shading structure pixel-identical;
only replaces the color scheme.

Usage:
    python reskin_monster.py <input.png> <output_dir>

Generates N preset skins: <stem>_skin_<name>.png
"""
import sys, os, json
import numpy as np
from PIL import Image

# ---------------------------------------------------------------
# Source anchors (sampled from Monkey.png; same anatomy roles for
# all monsters produced by the same art pipeline).
# Order matters only for grouping; each maps 1:1 to a target below.
# ---------------------------------------------------------------
SRC_ANCHORS = {
    # body / fur
    "fur_hi":    (244, 131, 88),    # F48358 highlight
    "fur_main":  (215, 116, 78),    # D7744E main
    "fur_sh":    (166,  69, 49),    # A64531 shadow
    "fur_deep":  (151,  63, 45),    # 973F2D deep shadow
    "fur_mid2":  (195,  84, 59),    # C3543B blend toward shadow
    "fur_hi2":   (255, 141, 96),    # FF8D60 blend toward hi
    # skin / face
    "skin_hi":   (255, 230, 193),   # FFE6C1
    "skin_main": (232, 208, 174),   # E8D0AE
    "skin_sh":   (179, 148, 121),   # B39479
    "skin_mid":  (205, 171, 140),   # CDAB8C
    "ear":       (191, 172, 162),   # BFACA2 inner ear
}
# Neutral anchors are identified separately and left (almost) untouched.
NEUTRAL = {
    "outline": (0, 0, 0),
    "eyewhite": (241, 241, 241),
}

def hexc(s):
    s = s.lstrip('#')
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))

# ---------------------------------------------------------------
# Preset skins: each entry maps every body/skin anchor to a target.
# Rules: keep relative lightness ladder (hi > main > sh > deep).
# ---------------------------------------------------------------
SKIN_PRESETS = {
    # 雪猴：蓝灰毛发 + 暖粉脸（日本雪猴风）
    "snow": {
        "fur_hi":    "B8C4D4", "fur_main": "8FA0B8", "fur_sh":   "5C6E88",
        "fur_deep":  "46566E", "fur_mid2": "71829A", "fur_hi2":  "C6D1DE",
        "skin_hi":   "FFD9CE", "skin_main":"F2B5A8", "skin_sh":  "C98478",
        "skin_mid":  "DFA095", "ear":      "E8C4BC",
        "outline":   "1A1A22",   # 轻微冷色调描边
    },
    # 金毛猴：金黄毛发 + 奶油脸
    "golden": {
        "fur_hi":    "FFD97A", "fur_main": "E8A93E", "fur_sh":   "B5761F",
        "fur_deep":  "8C5A14", "fur_mid2": "CF9430", "fur_hi2":  "FFE39A",
        "skin_hi":   "FFF3D6", "skin_main":"F5DFB8", "skin_sh":  "C4A878",
        "skin_mid":  "E2CC9F", "ear":      "EBD6BC",
        "outline":   "241A0E",
    },
    # 暗夜猴：紫毛 + 薄荷绿脸（奇幻风）
    "night": {
        "fur_hi":    "C39BE0", "fur_main": "9265BC", "fur_sh":   "5F3B85",
        "fur_deep":  "472B66", "fur_mid2": "7A4FA3", "fur_hi2":  "D0AFE8",
        "skin_hi":   "D8F5E3", "skin_main":"A8DFC2", "skin_sh":  "6FAF92",
        "skin_mid":  "8CC9AC", "ear":      "BCD9C6",
        "outline":   "1C1226",
    },
}

def dist2(a, b):
    d = a.astype(np.int32) - np.int32(b)
    # perceptual-ish weighting
    return (d[..., 0] * 3) ** 2 + (d[..., 1] * 4) ** 2 + (d[..., 2] * 2) ** 2

def reskin(img, preset):
    rgba = np.array(img.convert("RGBA"), dtype=np.float64)
    h, w = rgba.shape[:2]
    rgb = rgba[..., :3]
    alpha = rgba[..., 3]

    src_names = list(SRC_ANCHORS.keys())
    src = np.array([SRC_ANCHORS[n] for n in src_names], dtype=np.float64)  # (K,3)

    # distance of every pixel to each source anchor
    d2 = np.stack([dist2(rgb, s) for s in src], axis=-1)  # (h,w,K)

    # take 2 nearest anchors, interpolate between their targets
    idx = np.argsort(d2, axis=-1)
    d_sorted = np.take_along_axis(d2, idx, axis=-1)
    i1 = idx[..., 0]; i2 = idx[..., 1]
    dd1 = np.sqrt(d_sorted[..., 0]); dd2 = np.sqrt(d_sorted[..., 1])

    tgt = np.array([hexc(preset[n]) for n in src_names], dtype=np.float64)

    t1 = tgt[i1]; t2 = tgt[i2]
    # weight: pixel closer to anchor1 -> mostly target1
    rng = np.maximum(dd1 + dd2, 1e-6)
    w1 = np.clip(1.0 - (dd1 / rng) * 0.5, 0.0, 1.0)  # 0.5..1
    new_rgb = t1 * w1[..., None] + t2 * (1 - w1[..., None])

    # neutral pixels (black outline / eye white): map only outline tint,
    # keep near-white untouched
    neutral_src = np.array(list(NEUTRAL.values()), dtype=np.float64)
    dn = np.stack([dist2(rgb, s) for s in neutral_src], axis=-1)
    nearest_neutral = np.sqrt(dn.min(axis=-1))
    nearest_body = np.sqrt(d2.min(axis=-1))
    is_neutral = nearest_neutral < nearest_body

    # outline -> preset outline tint; eyewhite -> keep
    out_rgb = np.where(is_neutral[..., None], rgb, new_rgb)
    out_name = ["outline", "eyewhite"]
    dn_idx = dn.argmin(axis=-1)
    tint = hexc(preset.get("outline", "000000"))
    tinted = rgb * 0.0 + np.array(tint, dtype=np.float64)
    # only recolor pixels closest to outline anchor
    is_outline = is_neutral & (dn_idx == 0)
    out_rgb = np.where(is_outline[..., None], tinted, out_rgb)

    # luminance detail preservation: transfer original per-pixel
    # deviation from its anchor (keeps subtle texture/gradients)
    s1 = src[i1]
    delta = rgb - (s1 * w1[..., None] + src[i2] * (1 - w1[..., None])) * 0
    # simple version: keep original pixel's luminance offset relative to anchor1
    lum = lambda c: 0.299 * c[..., 0] + 0.587 * c[..., 1] + 0.114 * c[..., 2]
    lum_orig = lum(rgb)
    src_lum = np.array([lum(s[None, None, :])[0, 0] for s in src])
    lum_a1 = src_lum[i1]
    lum_new = lum(out_rgb)
    scale = np.where(lum_a1 > 20, np.clip(lum_orig / np.maximum(lum_a1, 1), 0.85, 1.18), 1.0)
    scale = np.where(is_neutral, 1.0, scale)
    for c in range(3):
        out_rgb[..., c] *= scale

    out = np.concatenate([np.clip(out_rgb, 0, 255), alpha[..., None]], axis=-1)
    return Image.fromarray(out.astype(np.uint8), "RGBA")

def main():
    src_path = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    img = Image.open(src_path)
    stem = os.path.splitext(os.path.basename(src_path))[0]
    outs = []
    for name, preset in SKIN_PRESETS.items():
        r = reskin(img, preset)
        p = os.path.join(out_dir, f"{stem}_skin_{name}.png")
        r.save(p)
        outs.append(p)
        print("saved", p)
    print(json.dumps({"inputs": len(SKIN_PRESETS)}))

if __name__ == "__main__":
    main()
