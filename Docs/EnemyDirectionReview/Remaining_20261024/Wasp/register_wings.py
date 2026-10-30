"""Register Wasp flap poses to one root/canvas and solidify small collar interiors.

Run only after pack_character.py Wasp. Raw paid images are never overwritten.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw
import hashlib
import json

HERE = Path(__file__).resolve().parent
ART = HERE / 'staged_art'
processing = json.loads((HERE / 'processing.json').read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
parents = {p.name: sha(p) for p in ART.glob('*.png')}
manifest_path = ART / 'Wasp_Directions.sprites.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
roots = {'Up': {'WingRaised': (323, 738), 'WingLowered': (699, 713)},
         'Down': {'WingRaised': (315, 728), 'WingLowered': (678, 728)}}
collars = {'Up': (1295, 168, 1374, 190), 'Down': (1300, 161, 1384, 174)}
canvas_size, common_root = (340, 500), (300, 250)
edits = []
for direction in ('Up', 'Down'):
    entry = next(p for p in processing if p['direction'] == direction)
    for role in ('WingRaised', 'WingLowered', 'Body'):
        rect = next(r for r in entry['rectangles'] if r['part'] == role)
        origin = (rect['source_rect'][0] + rect['tight_bounds'][0], rect['source_rect'][1] + rect['tight_bounds'][1])
        path = ART / (direction + '_' + role + '.png')
        im = Image.open(path).convert('RGBA')
        if role.startswith('Wing'):
            root = roots[direction][role]
            pivot = (root[0] - origin[0], root[1] - origin[1])
            offset = (common_root[0] - pivot[0], common_root[1] - pivot[1])
            assert offset[0] >= 0 and offset[1] >= 0
            assert offset[0] + im.width <= canvas_size[0] and offset[1] + im.height <= canvas_size[1]
            canvas = Image.new('RGBA', canvas_size)
            canvas.alpha_composite(im, offset)
            canvas.save(path)
            edits.append({'part': direction + '_' + role, 'raw_root': root, 'tight_origin': origin,
                          'new_canvas': canvas_size, 'root_px': common_root, 'offset': offset,
                          'method': 'Opaque original pixels translated without stretching, redrawing or mirroring; shared pivot.'})
        else:
            box = collars[direction]
            local = (box[0] - origin[0], box[1] - origin[1], box[2] - origin[0], box[3] - origin[1])
            ImageDraw.Draw(im).ellipse(local, fill=(205, 150, 44, 255))
            im.save(path)
            edits.append({'part': direction + '_Body', 'raw_region': box,
                          'method': 'Fill only tiny dark hollow collar interior with opaque ochre; outer outline and original abdomen/claws preserved.'})
atlas = Image.new('RGBA', (2048, 2048))
x = y = 8
row_height = 0
for sprite in manifest['sprites']:
    im = Image.open(ART / (sprite['name'] + '.png')).convert('RGBA')
    if x + im.width + 8 > 2048:
        x, y, row_height = 8, y + row_height + 8, 0
    assert y + im.height + 8 <= 2048
    atlas.alpha_composite(im, (x, y))
    sprite.update(x=x, y=2048-y-im.height, w=im.width, h=im.height)
    if '_Wing' in sprite['name']:
        sprite.update(pivotX=common_root[0] / canvas_size[0], pivotY=1-common_root[1] / canvas_size[1])
    x += im.width + 8
    row_height = max(row_height, im.height)
atlas.save(ART / 'Wasp_Directions.png')
manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
layout_path = ART / 'Wasp_Directions.layout.json'
layout = json.loads(layout_path.read_text(encoding='utf-8'))
h, bottom = layout['referenceHeight'], layout['referenceBottom']
for view in layout['views']:
    for part in view['parts']:
        role = part['role']
        if role == 'head':
            part.update(x=0, y=bottom+.66*h, width=.72*h, height=.86*h, order=15 if view['direction']=='Up' else 30)
        elif role == 'body':
            part.update(x=0, y=bottom+.27*h, width=.42*h, height=.44*h, order=20)
        elif role == 'wing':
            part.update(x=(-1 if part['name'].endswith('L') else 1)*.12*h,
                        y=bottom+.42*h, width=.54*h, height=.85*h, order=10)
layout['motion'] = {'legAngle': 0, 'legLift': 0, 'bodyBob': .012, 'bodyRoll': 0, 'tailSwing': 0}
layout_path.write_text(json.dumps(layout, indent=2) + '\n', encoding='utf-8')
report = {'observed_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
          'name': 'Wasp', 'revision': 'raster_registration_r01', 'raw_unchanged': True,
          'parents': parents, 'edits': edits,
          'after': {p.name: sha(p) for p in ART.iterdir() if p.is_file()},
          'status': 'pending_offline_visual_review'}
(HERE / 'registration_r01.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print('Wasp: both flap poses registered to a common root; staged layout written.')
