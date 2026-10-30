from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import os
import numpy as np
from PIL import Image

D = Path(__file__).resolve().parent
H = D.parent
R = H.parents[2]
NAME = 'Turkey'
TOKEN = 'troll-to-turkey-1e2dd1235ed84e41b82b178e45f86309'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def now():
    return datetime.now(timezone(timedelta(hours=8))).isoformat()


chain = read(H / 'conversation_chain.json')
assert chain['state'] == 'active'
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['current_character'] == NAME
assert chain['dispatch_token'] == TOKEN

up = D / 'generation' / 'Up'
request = read(up / 'request.json')
result = read(up / 'result.json')
intent = read(up / 'generation_intent.json')
assert result['status'] == 200
assert request['model'] == 'gpt-image-2' and request['quality'] == 'medium'
assert request['size'] == '1536x1024' and request['n'] == 1
assert request['transport'] == intent['transport'] == 'node_fetch'
assert intent['owner_thread_id'] == chain['owner_thread_id'] and intent['dispatch_token'] == TOKEN
assert sha(up / 'prompt.txt') == intent['prompt_sha256']
assert result['bytes'] == (up / 'raw.png').stat().st_size

raw = Image.open(up / 'raw.png')
assert raw.format == 'PNG' and raw.size == (1536, 1024) and raw.mode == 'RGB'
rgb = np.asarray(raw)
a = rgb.astype(np.int16)
foreground = (a[:, :, 2] <= a[:, :, 1] + 8) & (a[:, :, 2] <= a[:, :, 0] + 12) & ((a[:, :, 0] - a[:, :, 1]) <= (a[:, :, 1] - a[:, :, 2]) + 26)
rgba = np.dstack([rgb, foreground.astype(np.uint8) * 255])
rgba[~foreground, :3] = 0
preview = Image.fromarray(rgba, 'RGBA')
preview_path = up / 'keyed_preview.png'
assert np.array_equal(np.asarray(preview), np.asarray(Image.open(preview_path).convert('RGBA')))

cell_pixels = []
height, width = foreground.shape
for row in range(2):
    for column in range(4):
        tile = foreground[row * height // 2:(row + 1) * height // 2, column * width // 4:(column + 1) * width // 4]
        cell_pixels.append(int(tile.sum()))
assert all(count > 0 for count in cell_pixels[:7])
assert cell_pixels[7] == 0

report_path = up / 'review_20261028.json'
assert not report_path.exists()
report = {
    'observed_at': now(),
    'owner_thread_id': chain['owner_thread_id'],
    'dispatch_token': TOKEN,
    'request_sha256': sha(up / 'request.json'),
    'result': result,
    'raw_sha256': sha(up / 'raw.png'),
    'raw_image': {'format': raw.format, 'size': list(raw.size), 'mode': raw.mode},
    'input_background_sample_rgb': rgb[0, 0].tolist(),
    'mask': {
        'method': 'Existing pack_character.py spectral mask, unchanged',
        'keyed_preview': preview_path.name,
        'keyed_preview_sha256': sha(preview_path),
        'foreground_pixels': int(foreground.sum()),
        'cell_foreground_pixels_row_major': cell_pixels,
        'unused_eighth_cell_is_empty': True,
        'magenta_halo_visible_after_mask': False,
    },
    'visual_findings': [
        'Rear sheet has no visible face; the long cream neck and rounded spotted body read as the reference turkey.',
        'The standalone broad cream-and-ochre tail fan is clearly separated from the body and suitable for local packing review.',
        'The raw normal rear head has side gold lobes absent in the angry/dead cells. The existing pack_character.py intentionally copies Up_HeadNormal into Up_HeadAngry and Up_HeadDead, yielding one consistent blank rear silhouette.',
        'The single wing and leg cells remain subject to cutout and assembled-rig review; no installation decision is made from this sheet alone.',
    ],
    'decision': {
        'continue_to_down_generation': True,
        'candidate_for_local_packing': True,
        'accepted_for_staging': False,
        'user_approved': False,
    },
}
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

progress = read(H / 'progress.json')
item = next(value for value in progress['items'] if value['name'] == NAME)
assert item['status'] == 'reference_prepared' and item.get('user_approved') is False
item['stage'] = 'up_generated_reviewed_pending_down'
progress.update(current=NAME, updated_at=now())
(H / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

chain = read(H / 'conversation_chain.json')
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID'] and chain['dispatch_token'] == TOKEN
chain.update(
    current_stage='up_generated_reviewed_pending_down',
    last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Turkey/generation/Up/review_20261028.json',
    updated_at=now(),
)
(H / 'conversation_chain.json').write_text(json.dumps(chain, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print(json.dumps({
    'character': NAME,
    'stage': item['stage'],
    'foreground_pixels': int(foreground.sum()),
    'empty_cell_pixels': cell_pixels[7],
    'user_approved': item.get('user_approved'),
}, ensure_ascii=False))
