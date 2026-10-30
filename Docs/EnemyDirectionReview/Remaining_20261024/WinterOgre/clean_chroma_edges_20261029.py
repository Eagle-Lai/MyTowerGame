"""Remove residual magenta RGB from staged edges, preserving every alpha/shape pixel."""
from pathlib import Path
import json
import shutil
import sys
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_winterogre import D, NAME, owner, read, write, sha, now, run

owner()
art = D / 'staged_art'
backup = D / 'staged_before_edge_cleanup_20261029'
assert not backup.exists()
shutil.copytree(art, backup)
spec = read(art / (NAME + '_Directions.sprites.json'))
atlas = np.array(Image.open(art / (NAME + '_Directions.png')).convert('RGBA'))
report = []
for sprite in spec['sprites']:
    p = art / (sprite['name'] + '.png')
    before = np.array(Image.open(p).convert('RGBA'))
    signed = before.astype(np.int16)
    contaminated = (np.minimum(signed[:, :, 0], signed[:, :, 2]) - signed[:, :, 1] > 18) & (signed[:, :, 3] > 0)
    clean = (before[:, :, 3] >= 128) & ~contaminated
    after = before.copy()
    distances = []
    for y, x in zip(*np.nonzero(contaminated)):
        radius = 1
        while radius <= 12:
            x0, x1 = max(0, x - radius), min(before.shape[1], x + radius + 1)
            y0, y1 = max(0, y - radius), min(before.shape[0], y + radius + 1)
            yy, xx = np.nonzero(clean[y0:y1, x0:x1])
            if len(xx):
                yy, xx = yy + y0, xx + x0
                d = (yy - y) ** 2 + (xx - x) ** 2
                i = int(d.argmin())
                after[y, x, :3] = before[yy[i], xx[i], :3]
                distances.append(float(np.sqrt(d[i])))
                break
            radius += 1
        else:
            raise ValueError('No nearby opaque source outline for ' + p.name)
    assert np.array_equal(before[:, :, 3], after[:, :, 3])
    assert np.array_equal(before[~contaminated], after[~contaminated])
    if contaminated.any():
        Image.fromarray(after, 'RGBA').save(p)
    x, y = sprite['x'], 2048 - sprite['y'] - sprite['h']
    assert after.shape[:2] == (sprite['h'], sprite['w'])
    atlas[y:y + sprite['h'], x:x + sprite['w']] = after
    report.append({'file': p.name, 'before_sha256': sha(backup / p.name),
                   'after_sha256': sha(p), 'rgb_pixels_repaired': int(contaminated.sum()),
                   'maximum_distance_pixels': max(distances, default=0), 'alpha_unchanged': True})
Image.fromarray(atlas, 'RGBA').save(art / (NAME + '_Directions.png'))
pixels = atlas.astype(np.int16)
assert not np.any((np.minimum(pixels[:, :, 0], pixels[:, :, 2]) - pixels[:, :, 1] > 18) & (pixels[:, :, 3] > 0))
write(D / 'edge_cleanup_manifest_20261029.json', {
    'observed_at': now(), 'method': 'Nearest original opaque uncontaminated outline RGB; alpha, dimensions and silhouette unchanged.',
    'sources': report, 'total_part_pixels': sum(x['rgb_pixels_repaired'] for x in report),
    'atlas_sha256': sha(art / (NAME + '_Directions.png')),
    'raw_originals_unchanged': True, 'paid_requests': 0
}, fresh=True)
run('render_staged_rig.py', NAME)
print(json.dumps({'repaired_part_pixels': sum(x['rgb_pixels_repaired'] for x in report), 'alpha_unchanged': True}))
