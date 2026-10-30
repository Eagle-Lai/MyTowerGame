from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
source = HERE / 'generation/Up/raw.png'
output_dir = HERE / 'generation/Up/revision_01'
output = output_dir / 'raw.png'
record = output_dir / 'patch.json'
output_dir.mkdir(parents=True, exist_ok=True)
if output.exists() or record.exists():
    raise SystemExit('Revision output exists; preserve it and choose a new revision.')

image = Image.open(source).convert('RGB')
pixels = np.asarray(image).copy()
source_hash = hashlib.sha256(source.read_bytes()).hexdigest().upper()

# Smooth the three front-facing toe grooves on the single rear paw cell.
grooves = [(151, 825, 862), (197, 825, 866), (238, 827, 862)]
for center, top, bottom in grooves:
    for y in range(top, bottom + 1):
        progress = (y - top) / max(1, bottom - top)
        radius = max(1, round(3.5 * min(1.0, progress * 5, (1 - progress) * 4)))
        left = center - radius - 2
        right = center + radius + 2
        if left < 2 or right >= pixels.shape[1] - 2:
            raise ValueError('Retouch crosses image boundary')
        start = pixels[y, left - 1].astype(np.float32)
        end = pixels[y, right + 1].astype(np.float32)
        for x in range(left, right + 1):
            amount = (x - left) / (right - left)
            pixels[y, x] = np.rint(start * (1 - amount) + end * amount).astype(np.uint8)

Image.fromarray(pixels, 'RGB').save(output)
record.write_text(json.dumps({
    'revision': 'Up_revision_01_local_rear_paw_smoothing',
    'parent': 'generation/Up/raw.png',
    'parent_sha256': source_hash,
    'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest().upper(),
    'method': 'Row-wise local color interpolation over three internal toe grooves only; paw silhouette and surrounding cells retained.',
    'regions': [{'center_x': x, 'top_y': y0, 'bottom_y': y1} for x, y0, y1 in grooves],
    'api_request': False,
}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'output': str(output), 'sha256': hashlib.sha256(output.read_bytes()).hexdigest().upper()}))
