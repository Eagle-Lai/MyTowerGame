from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import os
import shutil
import numpy as np
from PIL import Image, ImageDraw

D = Path(__file__).resolve().parent
H = D.parent
NAME = 'Turkey'
TOKEN = 'troll-to-turkey-1e2dd1235ed84e41b82b178e45f86309'
ART = D / 'staged_art'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


def enclosed_holes(alpha):
    pad = Image.new('L', (alpha.shape[1] + 2, alpha.shape[0] + 2), 255)
    pad.paste(Image.fromarray(np.where(alpha == 0, 255, 0).astype('uint8')), (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 127)
    return np.asarray(pad)[1:-1, 1:-1] == 255


def component_sizes(holes):
    todo = set(map(tuple, np.argwhere(holes)))
    sizes = []
    while todo:
        first = todo.pop()
        stack = [first]
        size = 0
        while stack:
            y, x = stack.pop()
            size += 1
            for neighbor in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if neighbor in todo:
                    todo.remove(neighbor)
                    stack.append(neighbor)
        sizes.append(size)
    return sizes


chain = read(H / 'conversation_chain.json')
assert chain['state'] == 'active'
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['current_character'] == NAME
assert chain['dispatch_token'] == TOKEN
assert chain['current_stage'] == 'both_directions_reviewed_pending_local_packing'

repair_dir = D / 'alpha_repair_20261028'
assert not repair_dir.exists()
before_dir = repair_dir / 'before'
before_dir.mkdir(parents=True)
for path in ART.iterdir():
    if path.is_file():
        shutil.copy2(path, before_dir / path.name)
shutil.copy2(D / 'parts_clean.png', before_dir / 'parts_clean.png')

repairs = {}
part_paths = sorted(list(ART.glob('Up_*.png')) + list(ART.glob('Down_*.png')))
assert len(part_paths) == 14
for path in part_paths:
    before = np.asarray(Image.open(path).convert('RGBA'))
    holes = enclosed_holes(before[:, :, 3])
    coords = np.argwhere(holes)
    if not len(coords):
        repairs[path.name] = {
            'before_sha256': sha(before_dir / path.name),
            'after_sha256': sha(path),
            'filled_pixels': 0,
            'components': 0,
            'largest_component': 0,
            'max_nearest_distance': 0,
            'preserved_existing_pixels': True,
        }
        continue

    opaque_yx = before[:, :, 3] == 255
    component_count = len(component_sizes(holes))
    largest_component = max(component_sizes(holes))
    assert len(coords) <= 1200 and largest_component <= 40, (path.name, len(coords), largest_component)
    after = before.copy()
    max_distance = 0.0
    for y, x in coords:
        radius = 1
        while True:
            y0, y1 = max(0, y - radius), min(before.shape[0], y + radius + 1)
            x0, x1 = max(0, x - radius), min(before.shape[1], x + radius + 1)
            candidates = np.argwhere(opaque_yx[y0:y1, x0:x1])
            if len(candidates):
                candidates[:, 0] += y0
                candidates[:, 1] += x0
                delta = candidates - np.array([y, x])
                distances = np.einsum('ij,ij->i', delta, delta)
                nearest = candidates[int(np.argmin(distances))]
                max_distance = max(max_distance, float(np.sqrt(distances.min())))
                after[y, x, :3] = before[nearest[0], nearest[1], :3]
                after[y, x, 3] = 255
                break
            radius += 1
            if radius > max(before.shape):
                raise ValueError(f'No opaque source pixel found for {path.name} at {(int(x), int(y))}')

    assert np.array_equal(before[~holes], after[~holes]), path.name
    Image.fromarray(after, 'RGBA').save(path)
    repairs[path.name] = {
        'before_sha256': sha(before_dir / path.name),
        'after_sha256': sha(path),
        'filled_pixels': int(len(coords)),
        'components': component_count,
        'largest_component': largest_component,
        'max_nearest_distance': max_distance,
        'preserved_existing_pixels': True,
    }

manifest = read(ART / 'Turkey_Directions.sprites.json')
atlas = Image.new('RGBA', (2048, 2048))
for sprite in manifest['sprites']:
    piece = Image.open(ART / (sprite['name'] + '.png')).convert('RGBA')
    assert list(piece.size) == [sprite['w'], sprite['h']], sprite['name']
    top = 2048 - sprite['y'] - sprite['h']
    atlas.alpha_composite(piece, (sprite['x'], top))
atlas_path = ART / 'Turkey_Directions.png'
atlas_before_sha = sha(before_dir / atlas_path.name)
atlas.save(atlas_path)

parts = [(name, Image.open(ART / (name + '.png')).convert('RGBA')) for name in sorted(s['name'] for s in manifest['sprites'])]
board = Image.new('RGB', (1600, 700), (40, 48, 37))
draw = ImageDraw.Draw(board)
for i, (name, piece) in enumerate(parts):
    thumb = piece.copy()
    thumb.thumbnail((195, 300), Image.Resampling.LANCZOS)
    x = i % 8 * 200 + (200 - thumb.width) // 2
    y = i // 8 * 350 + 35
    board.paste(thumb, (x, y), thumb)
    draw.text((i % 8 * 200 + 5, i // 8 * 350 + 8), name, fill='white')
board.save(D / 'parts_clean.png')

report_path = D / 'alpha_repair_20261028.json'
assert not report_path.exists()
report_path.write_text(json.dumps({
    'observed_at': now(),
    'owner_thread_id': chain['owner_thread_id'],
    'dispatch_token': TOKEN,
    'method': 'Fill only enclosed alpha-zero regions from the nearest fully opaque pixel in the same staged part. Preserve all existing non-hole RGBA pixels and the generated raw sheets.',
    'backup_directory': 'alpha_repair_20261028/before',
    'parts': repairs,
    'filled_pixels_total': sum(value['filled_pixels'] for value in repairs.values()),
    'largest_component_pixels': max(value['largest_component'] for value in repairs.values()),
    'atlas_before_sha256': atlas_before_sha,
    'atlas_after_sha256': sha(atlas_path),
    'manifest_sha256': sha(ART / 'Turkey_Directions.sprites.json'),
}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

progress = read(H / 'progress.json')
item = next(value for value in progress['items'] if value['name'] == NAME)
assert item['status'] == 'reference_prepared' and item.get('user_approved') is False
item['stage'] = 'alpha_repaired_pending_offline_recheck'
progress.update(current=NAME, updated_at=now())
(H / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

chain = read(H / 'conversation_chain.json')
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID'] and chain['dispatch_token'] == TOKEN
chain.update(
    current_stage='alpha_repaired_pending_offline_recheck',
    last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Turkey/alpha_repair_20261028.json',
    updated_at=now(),
)
(H / 'conversation_chain.json').write_text(json.dumps(chain, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print(json.dumps({
    'character': NAME,
    'repaired_parts': sum(value['filled_pixels'] > 0 for value in repairs.values()),
    'filled_pixels': report['filled_pixels_total'],
    'largest_component': report['largest_component_pixels'],
    'raw_images_unchanged': True,
    'user_approved': item.get('user_approved'),
}, ensure_ascii=False))
