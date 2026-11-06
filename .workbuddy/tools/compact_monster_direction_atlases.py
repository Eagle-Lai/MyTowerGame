"""Stage/apply/verify only monster direction PNGs, slice manifests and rect metadata.

Backups and staged files live outside Assets. Apply refuses any source drift.
Run with the target Unity editor's automatic asset refresh suspended through MCP,
then resume refresh and validate the imported sprites through that same editor.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import os
import sys

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from directional_atlas_packing import repack_atlas, sprite_pixels, validate_rects


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rect_metadata(raw, old_sprites, new_sprites):
    """Edit only x/y numbers, preserving IDs, pivots and all other bytes."""
    text = raw.decode("utf-8")
    before = {s["name"]: s for s in old_sprites}
    after = {s["name"]: s for s in new_sprites}
    seen = set()
    pattern = re.compile(
        r"(?m)(^    - serializedVersion: [^\r\n]+\r?\n      name: ([^\r\n]+)"
        r"\r?\n      rect:\r?\n        serializedVersion: [^\r\n]+\r?\n        x: )"
        r"(-?\d+)(\r?\n        y: )(-?\d+)"
        r"(\r?\n        width: )(\d+)(\r?\n        height: )(\d+)")

    def replace(match):
        name = match[2]
        if name not in before or name in seen:
            raise ValueError("Unexpected/duplicate metadata sprite: " + name)
        old, new = before[name], after[name]
        if tuple(int(match[i]) for i in (3, 5, 7, 9)) != tuple(old[k] for k in ("x", "y", "w", "h")):
            raise ValueError("Metadata rect differs from source manifest: " + name)
        seen.add(name)
        return match[1] + str(new["x"]) + match[4] + str(new["y"]) + match[6] + match[7] + match[8] + match[9]

    result = pattern.sub(replace, text)
    if seen != set(before):
        raise ValueError("Metadata sprite set differs from manifest")
    # Substitution above is deliberately limited to the two atlas coordinates.
    return result.encode("utf-8")


def protected_paths(root, allowed):
    bases = [root / "Assets/_UIAssets/Monsters", root / "Assets/Prefabs/Enemy"]
    return sorted({p.relative_to(root).as_posix() for base in bases for p in base.rglob("*")
                   if p.is_file() and p.relative_to(root).as_posix() not in allowed})


def pin_existing_ids(raw, pins):
    """Make Unity's existing fallback IDs explicit before rectangle relocation."""
    text = raw.decode("utf-8")
    for name, identifier in pins.items():
        block = re.compile(r"(?ms)(^    - serializedVersion: [^\r\n]+\r?\n      name: "
                           + re.escape(name) + r"\r?\n(?:(?!^    -|^    outline:).)*?^      internalID: )0(?=\r?$)")
        text, count = block.subn(lambda m: m[1] + str(identifier), text)
        if count != 1:
            raise ValueError("Cannot pin existing fallback ID: " + name)
        table = re.compile(r"(?m)(^      " + re.escape(name) + r": )0(?=\r?$)")
        text, count = table.subn(lambda m: m[1] + str(identifier), text)
        if count != 1:
            raise ValueError("Cannot pin existing name/file ID mapping: " + name)
    return text.encode("utf-8")


def summary(plan):
    entries = plan["atlases"]
    before = sum(a["before_size"][0] * a["before_size"][1] for a in entries)
    after = sum(a["after_size"][0] * a["after_size"][1] for a in entries)
    return {"atlases": len(entries), "sprites": sum(a["sprite_count"] for a in entries),
            "before_sizes": dict(Counter("x".join(map(str, a["before_size"])) for a in entries)),
            "after_sizes": dict(Counter("x".join(map(str, a["after_size"])) for a in entries)),
            "area_reduction_percent": round((1 - after / before) * 100, 4),
            "rgba32_before_mib": before * 4 / 2**20, "rgba32_after_mib": after * 4 / 2**20,
            "png_before_bytes": sum(a["png_before_bytes"] for a in entries),
            "png_after_bytes": sum(a["png_after_bytes"] for a in entries)}


def stage(root, out, unity_baseline=None):
    if out.exists():
        raise ValueError("Output already exists; keep the previous baseline and use a new directory")
    atlases = sorted((root / "Assets/_UIAssets/Monsters").rglob("*_Directions.png"))
    if not atlases:
        raise ValueError("No monster direction atlases found")
    allowed = {p.relative_to(root).as_posix() for png in atlases for p in (
        png, png.with_suffix(".sprites.json"), png.with_suffix(".png.meta"))}
    protected = {rel: sha(root / rel) for rel in protected_paths(root, allowed)}
    unity_ids = {}
    if unity_baseline is not None:
        for line in unity_baseline.read_text(encoding="utf-8-sig").splitlines():
            path, name, guid, identifier, *_ = line.split("|")
            unity_ids[path, name] = guid, int(identifier)
    plan = {"schema": 1, "project": str(root), "padding": 8, "rotation": False,
            "resize": False, "deduplicate": False, "protected": protected, "atlases": []}
    for png in atlases:
        paths = [png, png.with_suffix(".sprites.json"), png.with_suffix(".png.meta")]
        old_manifest = read_json(paths[1])
        raw_meta = paths[2].read_bytes()
        meta_text = raw_meta.decode("utf-8-sig")
        if not re.search(r"(?m)^  nPOTScale: 0\r?$", meta_text):
            raise ValueError("Disable NPOT scaling before compacting: " + str(png))
        guid = re.search(r"(?m)^guid: ([^\r\n]+)", meta_text)[1]
        pins = {}
        for block in re.findall(r"(?ms)^    - serializedVersion:.*?(?=^    - serializedVersion:|^    outline:)", meta_text):
            name = re.search(r"(?m)^      name: ([^\r\n]+)", block)
            if name is None or not re.search(r"(?m)^      internalID: 0\r?$", block):
                continue
            name = name[1]
            key = png.relative_to(root).as_posix(), name
            if key not in unity_ids or unity_ids[key][0] != guid:
                raise ValueError("Capture existing sprite IDs through Unity MCP and pass --unity-baseline: " + repr(key))
            if unity_ids[key][1] != 0:
                pins[name] = unity_ids[key][1]
        source = Image.open(png)
        image, new_manifest = repack_atlas(source, old_manifest)
        if image.width * image.height > source.width * source.height:
            raise ValueError("Packing would increase area: " + str(png))
        files = []
        for path in paths:
            rel = path.relative_to(root).as_posix()
            before, staged = out / "before" / rel, out / "staged" / rel
            before.parent.mkdir(parents=True, exist_ok=True)
            staged.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, before)
            files.append({"path": rel, "before_sha256": sha(before)})
        image.save(out / "staged" / files[0]["path"], optimize=True)
        write_json(out / "staged" / files[1]["path"], new_manifest)
        (out / "staged" / files[2]["path"]).write_bytes(
            pin_existing_ids(rect_metadata(raw_meta, old_manifest["sprites"], new_manifest["sprites"]), pins))
        for file in files:
            file["after_sha256"] = sha(out / "staged" / file["path"])
        plan["atlases"].append({"path": files[0]["path"], "before_size": list(source.size),
                               "after_size": list(image.size), "sprite_count": len(old_manifest["sprites"]),
                               "png_before_bytes": png.stat().st_size,
                               "png_after_bytes": (out / "staged" / files[0]["path"]).stat().st_size,
                               "pinned_internal_ids": pins,
                               "files": files})
        source.close()
        if len(plan["atlases"]) % 20 == 0:
            print("Staged and preserved original pixels:", len(plan["atlases"]), flush=True)
    plan["summary"] = summary(plan)
    write_json(out / "plan.json", plan)
    result = verify(root, out, staged=True)
    write_json(out / "staged-validation.json", result)
    print(json.dumps({**plan["summary"], "validation": result}, ensure_ascii=False))


def load_plan(root, out):
    plan = read_json(out / "plan.json")
    if Path(plan["project"]).resolve() != root:
        raise ValueError("Plan belongs to another project")
    for atlas in plan["atlases"]:
        png = atlas["path"]
        if not png.startswith("Assets/_UIAssets/Monsters/") or not png.endswith("_Directions.png"):
            raise ValueError("Path outside authorized monster direction atlases")
        expected = {png, png[:-4] + ".sprites.json", png + ".meta"}
        if {f["path"] for f in atlas["files"]} != expected:
            raise ValueError("Unexpected write target")
        for file in atlas["files"]:
            if not (root / file["path"]).resolve().is_relative_to(root / "Assets/_UIAssets/Monsters"):
                raise ValueError("Path escaped monster asset directory")
    return plan


def check_protected(root, plan):
    changed = [rel for rel, digest in plan["protected"].items() if not (root / rel).is_file() or sha(root / rel) != digest]
    if changed:
        raise ValueError("Protected files changed: " + repr(changed[:10]))


def verify(root, out, staged=False):
    plan = load_plan(root, out)
    target = out / "staged" if staged else root
    checked = 0
    for atlas in plan["atlases"]:
        png, manifest_file, meta_file = (f["path"] for f in atlas["files"])
        before = Image.open(out / "before" / png)
        after = Image.open(target / png)
        old, new = read_json(out / "before" / manifest_file), read_json(target / manifest_file)
        validate_rects(after.size, new["sprites"], plan["padding"])
        if after.size != (new["width"], new["height"]) or list(after.size) != atlas["after_size"]:
            raise ValueError("Wrong output dimensions: " + png)
        normalized = deepcopy(new)
        normalized.update(width=old["width"], height=old["height"])
        if len(old["sprites"]) != len(new["sprites"]):
            raise ValueError("Sprite count changed: " + png)
        for original, compact in zip(old["sprites"], new["sprites"]):
            if sprite_pixels(before, original).tobytes() != sprite_pixels(after, compact).tobytes():
                raise ValueError("Sprite pixels changed: " + png + "/" + original["name"])
            checked += 1
        for original, compact in zip(old["sprites"], normalized["sprites"]):
            compact.update(x=original["x"], y=original["y"])
        if normalized != old:
            raise ValueError("Non-coordinate manifest data changed: " + png)
        expected_meta = pin_existing_ids(
            rect_metadata((out / "before" / meta_file).read_bytes(), old["sprites"], new["sprites"]),
            atlas.get("pinned_internal_ids", {}))
        if (target / meta_file).read_bytes() != expected_meta:
            raise ValueError("Metadata changed beyond rect coordinates: " + png)
        for file in atlas["files"]:
            if sha(target / file["path"]) != file["after_sha256"]:
                raise ValueError("Output changed since staging: " + file["path"])
        before.close()
        after.close()
    check_protected(root, plan)
    return {"atlases_checked": len(plan["atlases"]), "sprites_pixel_identical": checked,
            "metadata_changes": "rect x/y only", "protected_files_unchanged": len(plan["protected"])}


def apply(root, out):
    plan = load_plan(root, out)
    verify(root, out, staged=True)
    files = [file for atlas in plan["atlases"] for file in atlas["files"]]
    for file in files:
        if sha(root / file["path"]) != file["before_sha256"]:
            raise ValueError("Source changed since baseline; no files written: " + file["path"])
    written = []
    try:
        for file in files:
            destination = root / file["path"]
            with tempfile.NamedTemporaryFile(dir=destination.parent, suffix=".compact.tmp", delete=False) as temp:
                temporary = Path(temp.name)
                temp.write((out / "staged" / file["path"]).read_bytes())
            try:
                os.replace(temporary, destination)
            finally:
                temporary.unlink(missing_ok=True)
            written.append(file)
        result = verify(root, out)
    except Exception:
        for file in reversed(written):
            if sha(root / file["path"]) == file["after_sha256"]:
                shutil.copy2(out / "before" / file["path"], root / file["path"])
        raise
    write_json(out / "applied-validation.json", result)
    print(json.dumps({**plan["summary"], "validation": result}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["stage", "apply", "verify"])
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--unity-baseline", type=Path,
                        help="Existing sprite identity snapshot captured through the target Unity MCP")
    args = parser.parse_args()
    root, out = args.project.resolve(), args.out.resolve()
    if out == root or out.is_relative_to(root / "Assets") or out.is_relative_to(root / "Packages"):
        raise ValueError("Backups/staging must stay outside imported asset directories")
    if args.action == "stage":
        stage(root, out, args.unity_baseline)
    elif args.action == "apply":
        apply(root, out)
    else:
        result = verify(root, out)
        write_json(out / "applied-validation.json", result)
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
