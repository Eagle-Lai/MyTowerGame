"""Merge Monkey Up/Down part PNGs into one sprite atlas (Monkey.png style).

Sources live outside Assets (Docs/EnemyDirectionReview/Monkey/source) so the parts are not
imported twice; the atlas itself is written into the Directions folder and sliced by
EnemyDirectionPrefabBuilder from the manifest JSON produced here.

Layout: 6 columns (HeadNormal, HeadAngry, HeadDead, Body, Wing, Leg) x 2 rows (Up, Down).
Column width = widest of the two directions, row height = tallest in that row, plus padding.
"""
import json
import os

from PIL import Image

SRC = r"D:\FreedomTower_1\Docs\EnemyDirectionReview\Monkey\source"
ROOT = r"D:\FreedomTower_1\Assets\_UIAssets\Monsters\Apes\Monkey\Directions"
PARTS = ["HeadNormal", "HeadAngry", "HeadDead", "Body", "Wing", "Leg"]
DIRS = ["Up", "Down"]
PAD = 8


def main():
    images = {}
    for d in DIRS:
        for p in PARTS:
            images[(d, p)] = Image.open(os.path.join(SRC, d, p + ".png")).convert("RGBA")

    col_w = []
    for p in PARTS:
        widest = 0
        for d in DIRS:
            widest = max(widest, images[(d, p)].width)
        col_w.append(widest + PAD * 2)

    row_h = []
    for d in DIRS:
        tallest = 0
        for p in PARTS:
            tallest = max(tallest, images[(d, p)].height)
        row_h.append(tallest + PAD * 2)

    total_w = sum(col_w)
    total_h = sum(row_h)
    atlas = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))

    sprites = []
    y_top = 0
    for ri, d in enumerate(DIRS):
        x_left = 0
        for ci, p in enumerate(PARTS):
            im = images[(d, p)]
            cell_w = col_w[ci]
            cell_h = row_h[ri]
            pad_x = (cell_w - im.width) // 2
            pad_y = (cell_h - im.height) // 2
            ox = x_left + pad_x
            oy = y_top + pad_y
            atlas.paste(im, (ox, oy), im)
            sprites.append({
                "name": d + "_" + p,
                # Slice the content only (the transparent padding stays in the texture so
                # neighbouring cells cannot bleed in). Unity rects use a bottom-left origin.
                "x": ox,
                "y": total_h - (oy + im.height),
                "w": im.width,
                "h": im.height,
                "contentW": im.width,
                "contentH": im.height,
            })
            x_left += cell_w
        y_top += row_h[ri]

    png_path = os.path.join(ROOT, "Monkey_Directions.png")
    atlas.save(png_path)
    manifest = {
        "texture": "Monkey_Directions.png",
        "width": total_w,
        "height": total_h,
        "ppu": 100,
        "columns": PARTS,
        "rows": DIRS,
        "sprites": sprites,
    }
    with open(os.path.join(ROOT, "Monkey_Directions.sprites.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    print("atlas %dx%d -> %s" % (total_w, total_h, png_path))
    for s in sprites:
        print("  %-16s rect=(%d,%d) %dx%d content %dx%d"
              % (s["name"], s["x"], s["y"], s["w"], s["h"], s["contentW"], s["contentH"]))


if __name__ == "__main__":
    main()
