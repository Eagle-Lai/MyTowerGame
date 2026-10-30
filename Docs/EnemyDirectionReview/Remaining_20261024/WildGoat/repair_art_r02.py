"""Local WildGoat sprite repair; preserve successful AI originals and all r01 evidence."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFilter
import hashlib, json, os, shutil
import numpy as np

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
chain = read(H / 'conversation_chain.json')
assert chain['state'] == 'active' and chain['current_character'] == 'WildGoat'
assert chain['owner_thread_id'] == os.environ.get('CODEX_THREAD_ID') == '01a1841b-d4fc-7eb2-9ace-b66dc688e0c2'
out = D / 'local_raster_r02'
assert not out.exists(), 'Repair exists; inspect rather than overwrite'
out.mkdir()
staged = D / 'staged_art'
shutil.copytree(staged, out / 'previous_staged_art')
for filename in ['offline_rig_proof.png', 'offline_Up.png', 'offline_Down.png', 'parts_clean.png', 'runtime_summary.json', 'runtime_visual_strip.png']:
    shutil.copy2(D / filename, out / ('r01_' + filename))
raw = {s: sha(D / 'generation' / s / 'raw.png') for s in ['Up', 'Down']}
spec_path = staged / 'WildGoat_Directions.sprites.json'
layout_path = staged / 'WildGoat_Directions.layout.json'
spec = read(spec_path)
parts = {s['name']: s for s in spec['sprites']}
old_down = Image.open(staged / 'Down_Body.png').convert('RGBA')
up_body = Image.open(staged / 'Up_Body.png').convert('RGBA')
# Only the face-free axial torso is reused. The genuine Down head remains untouched.
# The neutral pear-shaped torso is inverted vertically so the neck/chest points Down.
down = up_body.transpose(Image.Transpose.FLIP_TOP_BOTTOM).resize(old_down.size, Image.Resampling.LANCZOS)
down.save(staged / 'Down_Body.png')
repairs = {'Down_Body': {'reason': 'Rejected r01 body contained duplicated horns and fur/limb fragments behind the true Down head.',
                         'source': 'previous_staged_art/Up_Body.png',
                         'method': 'Reuse only face-free axial spotted torso; vertical inversion places cream neck/chest toward Down; resize to existing slice dimensions.',
                         'before_sha256': sha(out / 'previous_staged_art/Down_Body.png'),
                         'after_sha256': sha(staged / 'Down_Body.png')}}
for key in ['Up_LegFront', 'Up_LegBack']:
    p = staged / (key + '.png')
    im = Image.open(p).convert('RGBA')
    a = np.array(im)
    # Keep the original silhouette and black outer contour; repaint only hoof interiors
    # as a short rounded heel, removing the tall front-facing toe cleft.
    alpha = Image.fromarray(a[:, :, 3])
    inner = np.array(alpha.filter(ImageFilter.MinFilter(9))) > 250
    yy, xx = np.indices(a.shape[:2])
    start = int(im.height * .76)
    mask = inner & (yy >= start)
    shade = np.clip((yy - start) / max(1, im.height - start), 0, 1)
    for ch, (top, bottom) in enumerate([(133, 91), (110, 72), (67, 39)]):
        values = np.rint(top + (bottom - top) * shade).astype(np.uint8)
        a[:, :, ch][mask] = values[mask]
    a[:, :, 3] = np.array(alpha)
    im = Image.fromarray(a)
    # A shallow hock rim describes the back of the hoof without forward toe wedges.
    overlay = Image.new('RGBA', im.size)
    dr = ImageDraw.Draw(overlay)
    dr.arc((int(im.width*.20), int(im.height*.76), int(im.width*.80), int(im.height*.88)),
           185, 355, fill=(183, 156, 103, 220), width=max(2, im.width//45))
    overlay.putalpha(Image.fromarray(np.minimum(np.array(overlay.getchannel('A')), np.array(alpha))))
    im.alpha_composite(overlay)
    im.save(p)
    repairs[key] = {'reason': 'Rear view used a tall front-facing cloven toe wedge.',
                    'method': 'Local repaint of existing hoof interior to rounded rear heel; preserve limb silhouette and outer black contour.',
                    'before_sha256': sha(out / 'previous_staged_art' / (key + '.png')), 'after_sha256': sha(p)}
layout = read(layout_path)
for view in layout['views']:
    for part in view['parts']:
        if part['role'] == 'leg':
            part['x'] = (-1 if part['name'].endswith('L') else 1) * (
                .74 if view['direction'] == 'Up' else (.64 if part['name'].startswith('Fore') else .75))
layout_path.write_text(json.dumps(layout, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
atlas = Image.open(staged / 'WildGoat_Directions.png').convert('RGBA')
for key in repairs:
    s = parts[key]
    im = Image.open(staged / (key + '.png')).convert('RGBA')
    assert im.size == (s['w'], s['h'])
    box = (s['x'], atlas.height - s['y'] - s['h'])
    atlas.paste(im, box)
atlas.save(staged / 'WildGoat_Directions.png')
contact = Image.new('RGB', (1600, 700), (40, 48, 37))
draw = ImageDraw.Draw(contact)
for i, s in enumerate(spec['sprites']):
    im = Image.open(staged / (s['name'] + '.png')).convert('RGBA')
    im.thumbnail((192, 310), Image.Resampling.LANCZOS)
    x, y = (i % 8)*200, (i // 8)*350
    contact.paste(im, (x+(200-im.width)//2, y+32+(310-im.height)//2), im)
    draw.text((x+5, y+10), s['name'], fill='white')
contact.save(D / 'parts_clean.png')
assert all(sha(D / 'generation' / s / 'raw.png') == digest for s, digest in raw.items())
unchanged = [s['name'] for s in spec['sprites'] if s['name'] not in repairs]
assert all(sha(staged / (key+'.png')) == sha(out / 'previous_staged_art' / (key+'.png')) for key in unchanged)
report = {'character': 'WildGoat', 'revision': 'art_r02', 'at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
          'raw_unchanged': True, 'raw_sha256': raw, 'repairs': repairs,
          'layout_change': 'Move only this character leg roots inward, under the torso silhouette, to prevent floating joint caps.',
          'staged_inputs': {p.name: sha(p) for p in staged.glob('WildGoat_Directions*')},
          'unchanged_parts': unchanged,
          'status': 'local_repair_pending_offline_visual_check', 'user_approved': False}
(out / 'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
(out / 'rejected_r01_visual.json').write_text(json.dumps({'status': 'rejected_visual', 'runtime': '168 PASS / 0 FAIL is preserved as old r01 technical evidence only',
 'reasons': ['Down body has duplicated horns and fur/limb fragments behind the head.', 'Up hooves show forward toe wedges.', 'Rounded leg roots need deeper torso overlap.'],
 'reviewed': ['offline_rig_proof.png', 'parts_clean.png', 'offline_Down.png', 'runtime_r01/four_directions.png'],
 'user_approved': False}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'revision': 'art_r02', 'repaired': list(repairs), 'raw_unchanged': True, 'production_edited': False}))
