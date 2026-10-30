"""Preserve four complete decoded GIF frames for WildRooster visual inspection."""
from pathlib import Path
from PIL import Image
import hashlib
import json

D = Path(__file__).resolve().parent
OUT = D / 'gif_samples_art_r03_20261029_full'
OUT.mkdir(exist_ok=False)
sources = []
for run in ['runtime_r01', 'runtime_updeath_r01']:
    for direction in ['Up', 'Down']:
        path = D / run / (direction + 'Walk.gif')
        with Image.open(path) as gif:
            index = gif.n_frames // 2
            gif.seek(index)
            output = OUT / (run + '_' + direction + 'Walk_f' + str(index) + '.png')
            gif.convert('RGB').save(output)
            sources.append({
                'source': path.relative_to(D).as_posix(),
                'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest().upper(),
                'frame': index, 'frame_count': gif.n_frames,
                'output': output.relative_to(D).as_posix(),
                'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest().upper(),
                'size': list(gif.size),
                'method': 'Complete decoded encoded GIF frame, no crop or resizing; not playback.'})
(OUT / 'sources.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(sources, ensure_ascii=False))
