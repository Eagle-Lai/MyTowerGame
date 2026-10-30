"""Record deterministic frame samples from the twelve final review GIFs."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib
import json

HERE = Path(__file__).resolve().parent
SAMPLE_DIR = HERE / "gif_samples_r03_20261028"
SAMPLE_DIR.mkdir(exist_ok=False)
revisions = ["runtime_r03", "runtime_updeath_r03"]
evidence = []
for revision in revisions:
    source_dir = HERE / revision
    files = ["UpWalk.gif", "DownWalk.gif", "up_down_walk.gif", "walk_turn.gif", "attack_death_reuse.gif", "pause_speed.gif"]
    cells = []
    for filename in files:
        path = source_dir / filename
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        gif = Image.open(path)
        indices = sorted(set(round((gif.n_frames - 1) * i / 4) for i in range(5)))
        for index in indices:
            gif.seek(index)
            frame = gif.convert("RGB")
            frame.thumbnail((300, 220), Image.Resampling.LANCZOS)
            cell = Image.new("RGB", (320, 250), (40, 48, 37))
            cell.paste(frame, ((320-frame.width)//2, 22+(220-frame.height)//2))
            ImageDraw.Draw(cell).text((6, 5), filename + " frame " + str(index), fill="white")
            cells.append(cell)
            evidence.append({"revision": revision, "file": filename, "gif_sha256": digest,
                             "frame_index_zero_based": index, "frame_count": gif.n_frames,
                             "duration_ms": gif.info.get("duration"),
                             "sample_sha256": hashlib.sha256(frame.tobytes()).hexdigest().upper()})
    sheet = Image.new("RGB", (1600, ((len(cells)+4)//5)*250), (40, 48, 37))
    for index, cell in enumerate(cells):
        sheet.paste(cell, ((index % 5)*320, (index//5)*250))
    sheet.save(SAMPLE_DIR / (revision + "_samples.png"))
(SAMPLE_DIR / "samples.json").write_text(json.dumps({
    "method": "Five evenly spaced encoded GIF frame samples per file; not full playback review.",
    "samples": evidence,
}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"samples": len(evidence), "directory": str(SAMPLE_DIR)}, ensure_ascii=False))
