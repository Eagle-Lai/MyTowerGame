"""Wasp-only chroma-edge and back-head occlusion revision; preserve prior evidence."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, shutil
import numpy as np
from PIL import Image

D = Path(__file__).resolve().parent
A = D / 'staged_art'
R = D / 'staged_refinement_r02'
assert not R.exists(), 'Revision already exists; inspect it instead of repeating.'
R.mkdir()
shutil.copytree(A, R / 'before_art')
for name in ('offline_rig_proof.png', 'offline_Up.png', 'offline_Down.png', 'parts_clean.png'):
    shutil.copy2(D / name, R / name)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
changes = []
for p in A.glob('*.png'):
    if p.name == 'Wasp_Directions.png':
        continue
    a = np.array(Image.open(p).convert('RGBA'))
    rgb = a[:, :, :3].astype(np.int16)
    spill = (a[:, :, 3] > 0) & (rgb[:, :, 2] > rgb[:, :, 1] + 6) & (rgb[:, :, 0] > rgb[:, :, 1] + 10)
    a[spill] = 0
    before = sha(p)
    Image.fromarray(a).save(p)
    changes.append({'part': p.name, 'removed_magenta_pixels': int(spill.sum()), 'before': before, 'after': sha(p)})
layout_path = A / 'Wasp_Directions.layout.json'
layout = json.loads(layout_path.read_text(encoding='utf-8'))
for v in layout['views']:
    if v['direction'] == 'Up':
        next(p for p in v['parts'] if p['role'] == 'head')['order'] = 30
layout_path.write_text(json.dumps(layout, indent=2)+'\n', encoding='utf-8')
manifest = json.loads((A / 'Wasp_Directions.sprites.json').read_text(encoding='utf-8'))
atlas = Image.new('RGBA', (2048, 2048))
for s in manifest['sprites']:
    im = Image.open(A / (s['name'] + '.png')).convert('RGBA')
    atlas.alpha_composite(im, (s['x'], 2048-s['y']-s['h']))
atlas.save(A / 'Wasp_Directions.png')
(R / 'manifest.json').write_text(json.dumps({'revision': 'staged_refinement_r02',
    'observed_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
    'changes': changes, 'occlusion': 'Up back head now covers the abdomen collar; fixed wing roots remain behind torso.',
    'raw_images_unchanged': True, 'status': 'pending_offline_visual_review',
    'final_art': {p.name: sha(p) for p in A.iterdir() if p.is_file()}}, indent=2)+'\n', encoding='utf-8')
print(json.dumps(changes))
