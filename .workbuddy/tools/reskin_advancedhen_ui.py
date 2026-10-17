# -*- coding: utf-8 -*-
"""
Reskin UI sprites for Enemy_AdvancedHen.prefab (2026-10-17).
Generates 3 style-matched replacement sprites (same pixel sizes as originals):
  HpBg_Skin.png    100x20  (was Art/Generated/HP_Bar_Bg.png)
  HpFill_Skin.png  100x20  (was Art/Generated/HP_Bar_Fill.png, runtime green tint kept -> bake near-white)
  Shadow_Skin.png  256x64  (was _UIAssets/Monsters/_Common/Sprites/Shadow.png)
Output: Assets/_UIAssets/Monsters/Birds/AdvancedHen/Skin/
Only Enemy_AdvancedHen.prefab references are re-pointed; originals stay untouched.
"""
import os
from PIL import Image, ImageDraw, ImageFilter

OUT = r"E:/MyTowerGame/Assets/_UIAssets/Monsters/Birds/AdvancedHen/Skin"
os.makedirs(OUT, exist_ok=True)


def rounded_mask(size, radius, inset=0):
    w, h = size
    d = ImageDraw.Draw(Image.new("L", size, 0))
    d.rounded_rectangle([inset, inset, w - 1 - inset, h - 1 - inset], radius=radius, fill=255)
    return d  # returns Draw; call .image? no -> build mask separately


def pill_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


# ---------- 1) HP bar background: dark slate pill + subtle rim light ----------
W, H = 100, 20
bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
mask = pill_mask((W, H), radius=H // 2)

body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(body)
# vertical gradient: #232c3a top -> #141a24 bottom (matches dark HUD tone)
top, bot = (35, 44, 58), (18, 24, 34)
for y in range(H):
    t = y / (H - 1)
    c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
    bd.line([(0, y), (W, y)], fill=c + (255,))
# soft top sheen
sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(sheen)
sd.rounded_rectangle([2, 2, W - 3, H // 2], radius=H // 4, fill=(255, 255, 255, 18))
body = Image.alpha_composite(body, sheen)

bg.paste(body, (0, 0), mask)
# rim: 1px lighter outline for readability on bright maps
rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(rim).rounded_rectangle([0, 0, W - 1, H - 1], radius=H // 2, outline=(96, 118, 148, 255), width=1)
rim.putalpha(Image.composite(rim.getchannel("A"), Image.new("L", (W, H), 0), mask))
bg = Image.alpha_composite(bg, rim)
bg.save(os.path.join(OUT, "HpBg_Skin.png"))

# ---------- 2) HP fill: near-white pill w/ vertical depth (runtime green tint preserved) ----------
fill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
fmask = pill_mask((W, H), radius=(H - 4) // 2)
fbody = Image.new("RGBA", (W, H), (0, 0, 0, 0))
fd = ImageDraw.Draw(fbody)
ftop, fbot = (255, 255, 255), (196, 206, 216)  # bottom gray -> tinted green reads as depth
for y in range(H):
    t = y / (H - 1)
    c = tuple(int(ftop[i] + (fbot[i] - ftop[i]) * t) for i in range(3))
    fd.line([(0, y), (W, y)], fill=c + (255,))
# glossy top highlight
gl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(gl)
gd.rounded_rectangle([2, 2, W - 3, 7], radius=3, fill=(255, 255, 255, 70))
fbody = Image.alpha_composite(fbody, gl)
fill.paste(fbody, (0, 0), fmask)
fill.save(os.path.join(OUT, "HpFill_Skin.png"))

# ---------- 3) Shadow: feathered radial ellipse (soft edge falloff) ----------
SW, SH = 256, 64
sh = Image.new("L", (SW, SH), 0)
sd = ImageDraw.Draw(sh)
cx, cy, rx, ry = SW // 2, SH // 2, SW // 2 - 6, SH // 2 - 4
for i in range(24):  # 24 concentric ellipses -> smooth gradient
    t = i / 23.0
    a = int(255 * (1.0 - t) ** 1.6)
    sd.ellipse([cx - rx * (1 - t), cy - ry * (1 - t), cx + rx * (1 - t), cy + ry * (1 - t)], fill=a)
sh = sh.filter(ImageFilter.GaussianBlur(2))
shadow = Image.new("RGBA", (SW, SH), (10, 12, 16, 0))
shadow.putalpha(sh)
shadow.save(os.path.join(OUT, "Shadow_Skin.png"))

for n in ["HpBg_Skin.png", "HpFill_Skin.png", "Shadow_Skin.png"]:
    im = Image.open(os.path.join(OUT, n))
    print("OK", n, im.size, im.mode)
