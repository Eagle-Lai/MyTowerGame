"""Render a full-fit offline anatomy proof; this is not Unity runtime evidence."""
from pathlib import Path
from PIL import Image, ImageDraw
import json
import math

HERE = Path(__file__).resolve().parent
ART = HERE / "staged_art"
layout = json.loads((ART / "VolcanoParasite_Directions.layout.json").read_text(encoding="utf-8"))
slices = {item["name"]: item for item in json.loads((ART / "VolcanoParasite_Directions.sprites.json").read_text(encoding="utf-8"))["sprites"]}
resolution = 1200
height = layout["referenceHeight"]
bottom = layout["referenceBottom"]
ppu = 900 / height


def render(view):
    canvas = Image.new("RGBA", (resolution, resolution * 2), (0, 0, 0, 0))
    for part in sorted(view["parts"], key=lambda value: value["order"]):
        source = Image.open(ART / (part["sprite"] + ".png")).convert("RGBA")
        sprite = slices[part["sprite"]]
        scale = min(part["width"] / source.width, part["height"] / source.height)
        w, h = max(1, round(source.width * scale * ppu)), max(1, round(source.height * scale * ppu))
        piece = source.resize((w, h), Image.Resampling.LANCZOS)
        pivot_x, pivot_y = sprite["pivotX"], sprite["pivotY"]
        if part["flipX"]:
            piece = piece.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            pivot_x = 1 - pivot_x
        anchor_x, anchor_y = pivot_x * w, (1 - pivot_y) * h
        if part.get("angle"):
            radius = math.ceil(math.hypot(w, h))
            padded = Image.new("RGBA", (radius * 2, radius * 2))
            padded.alpha_composite(piece, (round(radius-anchor_x), round(radius-anchor_y)))
            piece = padded.rotate(part["angle"], resample=Image.Resampling.BICUBIC)
            anchor_x = anchor_y = radius
        x = resolution / 2 + part["x"] * ppu - anchor_x
        y = 1350 - (part["y"] - bottom) * ppu - anchor_y
        canvas.alpha_composite(piece, (round(x), round(y)))
    bbox = canvas.getbbox()
    if not bbox:
        raise ValueError("Empty staged view: " + view["direction"])
    return canvas.crop(bbox)


proof = Image.new("RGB", (2400, 900), (40, 48, 37))
draw = ImageDraw.Draw(proof)
source = Image.open(HERE / "reference" / "source_prefab_offline.png").convert("RGBA")
views = [source, render(layout["views"][0]), render(layout["views"][1])]
labels = ["Original side prefab", "Staged Up rear", "Staged Down front"]
for index, (image, label) in enumerate(zip(views, labels)):
    image.thumbnail((740, 820), Image.Resampling.LANCZOS)
    proof.paste(image, (index * 800 + (800-image.width)//2, 55 + (820-image.height)//2), image if image.mode == "RGBA" else None)
    draw.text((index*800+16, 18), label + " | offline anatomy/layout only", fill="white")
out = HERE / "offline_proof_uncropped_r03.png"
proof.save(out)
print(str(out))
