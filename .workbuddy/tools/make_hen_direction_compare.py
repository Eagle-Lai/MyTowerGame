# -*- coding: utf-8 -*-
"""生成"左/右(原) | 正面(朝下) | 背面(朝上)"三张图集的对照预览图。"""
import os
from PIL import Image, ImageDraw, ImageFont

ART = r"D:/FreedomTower_1/Assets/_UIAssets/Monsters/Birds/AdvancedHen"
OUT = r"D:/FreedomTower_1/.workbuddy/cache/hen_dir/compare_directions.png"

W, H = 960, 800
GAP, TOP, BOT = 24, 56, 16
items = [("LEFT / RIGHT  (original AdvancedHen.png)", "AdvancedHen.png"),
         ("DOWN  (front, AdvancedHen_Down.png)", "AdvancedHen_Down.png"),
         ("UP  (back, AdvancedHen_Up.png)", "AdvancedHen_Up.png")]

canvas = Image.new("RGBA", (W * len(items) + GAP * (len(items) + 1),
                            TOP + H + BOT), (34, 36, 40, 255))
d = ImageDraw.Draw(canvas)
try:
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 26)
except Exception:
    font = ImageFont.load_default()

for i, (title, fname) in enumerate(items):
    x0 = GAP + i * (W + GAP)
    d.text((x0, 14), title, fill=(235, 235, 235, 255), font=font)
    # 棋盘底
    cell = 20
    tile = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    for yy in range(0, H, cell):
        for xx in range(0, W, cell):
            c = (96, 100, 106, 255) if ((xx // cell + yy // cell) % 2 == 0) else (126, 130, 136, 255)
            td.rectangle([xx, yy, min(xx + cell - 1, W - 1), min(yy + cell - 1, H - 1)], fill=c)
    # 标出 rect 分隔线，便于核对切图位置
    for (rx, ry, rw, rh) in [(0, 0, 320, 320), (320, 0, 320, 320), (640, 0, 320, 320),
                             (0, 320, 640, 480), (640, 320, 160, 160), (800, 320, 160, 160)]:
        td.rectangle([rx, ry, rx + rw - 1, ry + rh - 1], outline=(255, 210, 90, 160), width=2)
    tile.alpha_composite(Image.open(os.path.join(ART, fname)).convert("RGBA"), (0, 0))
    canvas.alpha_composite(tile, (x0, TOP))

canvas.convert("RGB").save(OUT, quality=95)
print("写出：", OUT, canvas.size)
