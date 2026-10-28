#!/usr/bin/env python3
"""Render official route JSON data as reviewable raster PNG placement maps."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
ROUTE_DIR = ROOT / "Docs" / "Balance_TowerSystem" / "LevelRouteAndOperations"
CANONICAL_DIR = ROOT / "Docs" / "Balance_TowerSystem" / "LongestPathTowerPNG"
COMPAT_DIR = ROUTE_DIR / "png"


def font(size: int, bold: bool = False):
    names = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
    ]
    for name in names:
        path = Path(name)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def arrow(draw, start, end, color, width=4):
    draw.line((start[0], start[1], end[0], end[1]), fill=color, width=width)
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = max((dx * dx + dy * dy) ** 0.5, 1.0)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    size = 10
    tip = end
    left = (tip[0] - ux * size - px * size * 0.65, tip[1] - uy * size - py * size * 0.65)
    right = (tip[0] - ux * size + px * size * 0.65, tip[1] - uy * size + py * size * 0.65)
    draw.polygon((tip, left, right), fill=color)


def draw_badge(draw, box, fill, outline, text, text_font, text_fill="white"):
    draw.rounded_rectangle(box, radius=10, fill=fill, outline=outline, width=3)
    x0, y0, x1, y1 = box
    bounds = draw.textbbox((0, 0), text, font=text_font)
    tw, th = bounds[2] - bounds[0], bounds[3] - bounds[1]
    draw.text(((x0 + x1 - tw) / 2, (y0 + y1 - th) / 2 - 2), text, fill=text_fill, font=text_font)


def render(route_path: Path):
    data = json.loads(route_path.read_text(encoding="utf-8"))
    level = int(data["levelId"])
    grid = data["map"]
    cols, rows = int(grid["cols"]), int(grid["rows"])
    path = [tuple(cell) for cell in data["longestPath"]["cells"]]
    tower_cells = [tuple(cell) for cell in data["longestPath"]["towerCells"]]
    tower_set = set(tower_cells)
    start = tuple(grid["start"])
    end = tuple(grid["end"])
    ascii_rows = data["longestPath"].get("ascii", [])

    cell = 88
    left, top = 60, 128
    right_panel = 360
    right = 44
    footer = 170
    map_width = cols * cell
    map_height = rows * cell
    width = left + map_width + right_panel + right
    height = top + map_height + footer
    image = Image.new("RGB", (width, height), (242, 245, 249))
    draw = ImageDraw.Draw(image)

    title_font = font(30, True)
    section_font = font(19, True)
    body_font = font(17)
    small_font = font(14)
    tiny_font = font(12)
    path_font = font(15, True)
    tower_font = font(17, True)
    route_index = {coord: idx + 1 for idx, coord in enumerate(path)}
    tower_index = {coord: idx + 1 for idx, coord in enumerate(tower_cells)}

    draw.text((left, 25), f"LEVEL L{level:02d}  |  LONGEST PATH TOWER MAP", fill=(22, 32, 47), font=title_font)
    draw.text((left, 72), "Raster PNG generated from the official route JSON; this image is the placement deliverable.", fill=(71, 83, 101), font=body_font)

    for x in range(cols):
        cx = left + x * cell + cell / 2
        label = str(x)
        bounds = draw.textbbox((0, 0), label, font=tiny_font)
        draw.text((cx - (bounds[2] - bounds[0]) / 2, top - 22), label, fill=(83, 96, 114), font=tiny_font)
    for y in range(rows):
        cy = top + y * cell + cell / 2
        label = str(y)
        bounds = draw.textbbox((0, 0), label, font=tiny_font)
        draw.text((left - 28 - (bounds[2] - bounds[0]) / 2, cy - 8), label, fill=(83, 96, 114), font=tiny_font)

    for idx in range(len(path) - 1):
        x0, y0 = path[idx]
        x1, y1 = path[idx + 1]
        start_center = (left + x0 * cell + cell / 2, top + y0 * cell + cell / 2)
        end_center = (left + x1 * cell + cell / 2, top + y1 * cell + cell / 2)
        arrow(draw, start_center, end_center, (63, 132, 182), width=4)

    for y in range(rows):
        for x in range(cols):
            coord = (x, y)
            ch = ascii_rows[y][x] if y < len(ascii_rows) and x < len(ascii_rows[y]) else "."
            if ch == "#":
                fill = (52, 62, 76)
            elif coord in tower_set:
                fill = (255, 227, 161)
            elif coord in route_index:
                fill = (195, 229, 253)
            else:
                fill = (252, 253, 254)
            x0, y0 = left + x * cell, top + y * cell
            draw.rectangle((x0, y0, x0 + cell, y0 + cell), fill=fill, outline=(143, 156, 174), width=2)
            if ch == "#":
                draw.line((x0 + 18, y0 + cell - 18, x0 + cell - 18, y0 + 18), fill=(96, 106, 119), width=3)
                draw.line((x0 + 18, y0 + 18, x0 + cell - 18, y0 + cell - 18), fill=(96, 106, 119), width=3)
                draw.text((x0 + cell / 2 - 5, y0 + cell / 2 - 9), "X", fill=(230, 234, 240), font=body_font)

            if coord in route_index and coord not in (start, end):
                label = f"P{route_index[coord]:02d}"
                bounds = draw.textbbox((0, 0), label, font=path_font)
                draw.text((x0 + cell - (bounds[2] - bounds[0]) - 7, y0 + 6), label, fill=(25, 84, 126), font=path_font)

            if coord in tower_set and coord not in (start, end):
                badge = f"T{tower_index[coord]:02d}"
                draw_badge(draw, (x0 + 13, y0 + 25, x0 + cell - 13, y0 + cell - 12), (224, 143, 26), (145, 83, 13), badge, tower_font)

            if coord == start:
                draw.ellipse((x0 + 12, y0 + 12, x0 + cell - 12, y0 + cell - 12), fill=(47, 164, 92), outline=(25, 94, 50), width=3)
                draw_badge(draw, (x0 + 27, y0 + 32, x0 + cell - 27, y0 + cell - 25), (47, 164, 92), (47, 164, 92), "START", tiny_font)
            elif coord == end:
                draw.ellipse((x0 + 12, y0 + 12, x0 + cell - 12, y0 + cell - 12), fill=(216, 70, 75), outline=(132, 31, 36), width=3)
                draw_badge(draw, (x0 + 27, y0 + 32, x0 + cell - 27, y0 + cell - 25), (216, 70, 75), (216, 70, 75), "END", tiny_font)

    panel_x = left + map_width + 28
    panel_y = top
    panel_w = right_panel - 28
    panel_h = map_height
    draw.rounded_rectangle((panel_x, panel_y, panel_x + panel_w, panel_y + panel_h), radius=12, fill=(255, 255, 255), outline=(184, 194, 207), width=2)
    draw.text((panel_x + 20, panel_y + 22), "PLACEMENT DATA", fill=(26, 42, 61), font=section_font)
    metadata = [("Path edges", str(data["longestPath"]["pathEdges"])), ("Path cells", str(len(path))), ("Tower cells", str(len(tower_cells))), ("Initial gold", "100"), ("Map", f"{cols} x {rows}"), ("Coordinates", "x = col, y = row")]
    y = panel_y + 72
    for key, value in metadata:
        draw.text((panel_x + 20, y), key, fill=(91, 104, 120), font=small_font)
        draw.text((panel_x + 20, y + 22), value, fill=(26, 42, 61), font=body_font)
        y += 57

    draw.line((panel_x + 20, y + 2, panel_x + panel_w - 20, y + 2), fill=(218, 224, 231), width=2)
    y += 22
    draw.text((panel_x + 20, y), "How to read", fill=(26, 42, 61), font=section_font)
    y += 35
    legend = [((195, 229, 253), "route cell / arrows show direction"), ((255, 227, 161), "recommended tower cell"), ((52, 62, 76), "blocked cell"), ((47, 164, 92), "start"), ((216, 70, 75), "end")]
    for color, label in legend:
        draw.rectangle((panel_x + 20, y + 2, panel_x + 40, y + 22), fill=color, outline=(110, 122, 137))
        draw.text((panel_x + 50, y), label, fill=(66, 79, 96), font=small_font)
        y += 31
    draw.text((panel_x + 20, y + 10), "Pnn = path order; Tnn = tower placement ID.", fill=(66, 79, 96), font=small_font)
    draw.text((panel_x + 20, y + 37), "Use the matching Lxx operation document for timing,", fill=(66, 79, 96), font=small_font)
    draw.text((panel_x + 20, y + 59), "tower type, cost, and post-operation balance.", fill=(66, 79, 96), font=small_font)

    footer_y = top + map_height + 26
    draw.text((left, footer_y), "PNG raster map | official route JSON | budgeted longest-path candidate", fill=(67, 82, 101), font=small_font)
    draw.text((left, footer_y + 29), "This deliverable is an image file, not an ASCII or character-only map.", fill=(67, 82, 101), font=small_font)

    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)
    COMPAT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"L{level:02d}_longest_path_towers.png"
    canonical = CANONICAL_DIR / filename
    compat = COMPAT_DIR / filename
    image.save(canonical, format="PNG", optimize=True)
    image.save(compat, format="PNG", optimize=True)
    return canonical, compat


def main():
    outputs = []
    for route in sorted(ROUTE_DIR.glob("L[0-9][0-9].json")):
        outputs.append(render(route))
    print(f"rendered {len(outputs)} PNG pairs")
    for canonical, _ in outputs:
        print(canonical)


if __name__ == "__main__":
    main()
