"""Lossless, deterministic packing for one monster's direction-part sprites.

Rectangles never rotate, resize, trim or share storage. Coordinates in manifests
use Unity's bottom-left origin; internal packing uses a top-left origin.
"""
from copy import deepcopy

from PIL import Image, ImageDraw


def _place(items, width, height, padding, sort_kind, score_kind):
    free = [(padding, padding, width - padding, height - padding)]
    key = (lambda item: (item[1] * item[2], max(item[1:]))) if sort_kind == 0 else (
        lambda item: (max(item[1:]), item[1] * item[2]))
    result = {}
    for name, w, h in sorted(items, key=key, reverse=True):
        w += padding
        h += padding
        candidates = []
        for x, y, fw, fh in free:
            if w <= fw and h <= fh:
                score = (min(fw - w, fh - h), max(fw - w, fh - h)) if score_kind == 0 else (
                    fw * fh - w * h, min(fw - w, fh - h))
                candidates.append((score, y, x))
        if not candidates:
            return None
        _, y, x = min(candidates)
        result[name] = (x, y, w - padding, h - padding)
        split = []
        for fx, fy, fw, fh in free:
            if x >= fx + fw or x + w <= fx or y >= fy + fh or y + h <= fy:
                split.append((fx, fy, fw, fh))
                continue
            if x > fx:
                split.append((fx, fy, x - fx, fh))
            if x + w < fx + fw:
                split.append((x + w, fy, fx + fw - x - w, fh))
            if y > fy:
                split.append((fx, fy, fw, y - fy))
            if y + h < fy + fh:
                split.append((fx, y + h, fw, fy + fh - y - h))
        free = []
        for i, a in enumerate(split):
            if a[2] <= 0 or a[3] <= 0:
                continue
            contained = any(
                i != j and b[0] <= a[0] and b[1] <= a[1]
                and b[0] + b[2] >= a[0] + a[2] and b[1] + b[3] >= a[1] + a[3]
                and (a != b or j < i)
                for j, b in enumerate(split))
            if not contained:
                free.append(a)
    return result


def _layout(items, padding=8, max_size=2048):
    if not items or padding < 1 or max_size < 256:
        raise ValueError("Expected nonempty parts, positive padding and max_size >= 256")
    if len({name for name, _, _ in items}) != len(items):
        raise ValueError("Duplicate sprite names")
    if any(w <= 0 or h <= 0 for _, w, h in items):
        raise ValueError("Invalid sprite dimensions")
    # NPOT is intentional: rounding every successful layout to powers of two
    # leaves a large empty tail. Four-pixel alignment also suits block formats.
    align = lambda value, step=4: (int(value) + step - 1) // step * step
    area = sum((w + padding) * (h + padding) for _, w, h in items)
    min_width = max(w for _, w, _ in items) + padding * 2
    min_height = max(h for _, _, h in items) + padding * 2
    best = None
    visited = set()

    def search(widths):
        nonlocal best
        for width in sorted(set(widths)):
            if width < min_width or width > max_size or width in visited:
                continue
            visited.add(width)
            lower = align(max(min_height, (area + width - padding - 1) // (width - padding) + padding))
            if lower > max_size:
                continue
            heights = sorted({min(max_size, align(lower * ratio + 0.999))
                              for ratio in (1, 1.03, 1.06, 1.10, 1.16, 1.25, 1.40, 1.70)}
                             | {max_size} | {h for h in (256, 512, 1024, 2048) if lower <= h <= max_size})
            for height in heights:
                fits = False
                for sort_kind in (0, 1):
                    for score_kind in (0, 1):
                        placed = _place(items, width, height, padding, sort_kind, score_kind)
                        if placed is None:
                            continue
                        fits = True
                        actual_w = align(max(x + w for x, y, w, h in placed.values()) + padding)
                        actual_h = align(max(y + h for x, y, w, h in placed.values()) + padding)
                        score = (actual_w * actual_h, max(actual_w, actual_h), actual_w)
                        if best is None or score < best[0]:
                            best = score, actual_w, actual_h, placed
                if fits:
                    break

    # Coarse width search, then refine the best aspect ratio. All successful
    # layouts are cropped to their actual occupied extent, including padding.
    search([align(min_width)] + list(range(align(min_width, 32), max_size + 1, 32)) + [max_size])
    if best is not None:
        center = best[1]
        search(range(align(max(min_width, center - 64), 4), min(max_size, center + 64) + 1, 4))
        return best[1], best[2], best[3]
    raise ValueError("Parts do not fit without resizing; raise max_size explicitly")


def build_atlas(parts, sprite_specs, padding=8, max_size=2048):
    """Pack original RGBA images, retaining sprite order and all non-rect fields."""
    names = [s["name"] for s in sprite_specs]
    if len(names) != len(set(names)) or set(names) != set(parts):
        raise ValueError("Parts and sprite names must match exactly")
    items = [(name, *parts[name].size) for name in names]
    width, height, placed = _layout(items, padding, max_size)
    atlas = Image.new("RGBA", (width, height))
    sprites = deepcopy(sprite_specs)
    for sprite in sprites:
        name = sprite["name"]
        image = parts[name]
        if image.mode != "RGBA":
            raise ValueError("Expected RGBA part: " + name)
        if (sprite["w"], sprite["h"]) != image.size:
            raise ValueError("Sprite dimensions disagree with pixels: " + name)
        x, y, w, h = placed[name]
        # No alpha mask/compositing: copy even RGB values under transparent pixels.
        atlas.paste(image, (x, y))
        sprite.update(x=x, y=height - y - h)
    validate_rects((width, height), sprites, padding)
    return atlas, sprites


def validate_rects(size, sprites, padding=8):
    width, height = size
    for i, a in enumerate(sprites):
        x, y, w, h = (a[k] for k in ("x", "y", "w", "h"))
        if min(x, y) < padding or w <= 0 or h <= 0 or x + w + padding > width or y + h + padding > height:
            raise ValueError("Out-of-bounds sprite: " + a["name"])
        for b in sprites[i + 1:]:
            if not (x + w + padding <= b["x"] or b["x"] + b["w"] + padding <= x
                    or y + h + padding <= b["y"] or b["y"] + b["h"] + padding <= y):
                raise ValueError("Sprite padding/overlap violation: " + a["name"] + "/" + b["name"])


def sprite_pixels(image, sprite):
    x, y, w, h = (sprite[k] for k in ("x", "y", "w", "h"))
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > image.width or y + h > image.height:
        raise ValueError("Source sprite outside image: " + sprite["name"])
    return image.crop((x, image.height - y - h, x + w, image.height - y))


def repack_atlas(image, manifest, padding=8, max_size=2048):
    if image.mode != "RGBA" or image.size != (manifest["width"], manifest["height"]):
        raise ValueError("RGBA source/manifest dimensions disagree")
    covered = Image.new("L", image.size)
    draw = ImageDraw.Draw(covered)
    parts = {}
    for sprite in manifest["sprites"]:
        name = sprite["name"]
        if name in parts:
            raise ValueError("Duplicate sprite name: " + name)
        parts[name] = sprite_pixels(image, sprite)
        x, y, w, h = (sprite[k] for k in ("x", "y", "w", "h"))
        draw.rectangle((x, image.height - y - h, x + w - 1, image.height - y - 1), fill=255)
    uncovered = image.getchannel("A").copy()
    uncovered.paste(0, mask=covered)
    if uncovered.getbbox():
        raise ValueError("Visible pixels exist outside declared sprites")
    atlas, sprites = build_atlas(parts, manifest["sprites"], padding, max_size)
    result = deepcopy(manifest)
    result.update(width=atlas.width, height=atlas.height, sprites=sprites)
    return atlas, result
