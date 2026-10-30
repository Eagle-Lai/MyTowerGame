from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import os
import numpy as np
from PIL import Image

D = Path(__file__).resolve().parent
H = D.parent
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
assert chain['current_stage'] == 'down_intent_prepared'

down = D / 'generation' / 'Down'
request = read(down / 'request.json')
result = read(down / 'result.json')
intent = read(down / 'generation_intent.json')
up_review = read(D / 'generation' / 'Up' / 'review_20261028.json')
assert up_review['decision']['continue_to_down_generation'] is True
assert result['status'] == 200
assert request['model'] == 'gpt-image-2' and request['quality'] == 'medium'
assert request['size'] == '1536x1024' and request['n'] == 1
assert request['transport'] == intent['transport'] == 'node_fetch'
assert intent['owner_thread_id'] == chain['owner_thread_id'] and intent['dispatch_token'] == TOKEN
assert sha(down / 'prompt.txt') == intent['prompt_sha256']
assert result['bytes'] == (down / 'raw.png').stat().st_size

raw = Image.open(down / 'raw.png')
assert raw.format == 'PNG' and raw.size == (1536, 1024) and raw.mode == 'RGB'
rgb = np.asarray(raw)
a = rgb.astype(np.int16)
foreground = (a[:, :, 2] <= a[:, :, 1] + 8) & (a[:, :, 2] <= a[:, :, 0] + 12) & ((a[:, :, 0] - a[:, :, 1]) <= (a[:, :, 1] - a[:, :, 2]) + 26)
rgba = np.dstack([rgb, foreground.astype(np.uint8) * 255])
rgba[~foreground, :3] = 0
preview = Image.fromarray(rgba, 'RGBA')
preview_path = down / 'keyed_preview.png'
assert np.array_equal(np.asarray(preview), np.asarray(Image.open(preview_path).convert('RGBA')))

height, width = foreground.shape
row_runs = []
for row in range(2):
    y0, y1 = row * height // 2, (row + 1) * height // 2
    occupied = foreground[y0:y1].sum(axis=0) >= 4
    runs = []
    start = None
    for x, value in enumerate(np.r_[occupied, False]):
        if value and start is None:
            start = x
        if not value and start is not None:
            if x - start >= 8:
                runs.append([start, x])
            start = None
    row_runs.append(runs)
assert [len(runs) for runs in row_runs] == [4, 3], row_runs

cell_pixels = []
for row in range(2):
    for column in range(4):
        tile = foreground[row * height // 2:(row + 1) * height // 2, column * width // 4:(column + 1) * width // 4]
        cell_pixels.append(int(tile.sum()))
assert cell_pixels[7] > 0
assert row_runs[1][2][0] >= width // 2 and row_runs[1][2][1] > width * 3 // 4

part_names = [
    ['HeadNormal', 'HeadAngry', 'HeadDead', 'Body'],
    ['Wing', 'Leg', 'Tail'],
]
rectangles = {}
for row, names in enumerate(part_names):
    y0, y1 = row * height // 2, (row + 1) * height // 2
    for name, (x0, x1) in zip(names, row_runs[row]):
        rectangles['Down_' + name] = [max(0, x0 - 3), y0, min(width, x1 + 3), y1]

selection_path = D / 'art_selection.json'
assert not selection_path.exists()
selection = {
    'Up': 'generation/Up/raw.png',
    'Down': 'generation/Down/raw.png',
    'rectangles': rectangles,
    'preserve_warm_foreground': False,
    'transparent_parts': [],
    'review_note': 'Explicit Down crops follow the three separate lower-row parts. The broad tail is one contiguous silhouette extending into the unused eighth grid slot; preserve the complete fan in the Tail cutout rather than truncate feathers.',
}
selection_path.write_text(json.dumps(selection, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

report_path = down / 'review_20261028.json'
assert not report_path.exists()
report = {
    'observed_at': now(),
    'owner_thread_id': chain['owner_thread_id'],
    'dispatch_token': TOKEN,
    'request_sha256': sha(down / 'request.json'),
    'result': result,
    'raw_sha256': sha(down / 'raw.png'),
    'raw_image': {'format': raw.format, 'size': list(raw.size), 'mode': raw.mode},
    'input_background_sample_rgb': rgb[0, 0].tolist(),
    'mask': {
        'method': 'Existing pack_character.py spectral mask, unchanged',
        'keyed_preview': preview_path.name,
        'keyed_preview_sha256': sha(preview_path),
        'foreground_pixels': int(foreground.sum()),
        'cell_foreground_pixels_row_major': cell_pixels,
        'lower_row_contiguous_part_runs': row_runs[1],
        'tail_spans_the_unused_eighth_cell': True,
        'magenta_halo_visible_after_mask': False,
    },
    'selection': {
        'file': 'art_selection.json',
        'sha256': sha(selection_path),
        'rectangles': rectangles,
    },
    'visual_findings': [
        'Front-facing normal, angry and dead expressions are distinct and aligned; the long cream neck and gold wattle remain attached to each head cutout.',
        'The spotted torso, folded wing, clawed leg and broad fan tail are separate silhouettes after the existing chroma key.',
        'The tail crosses the boundary between the last two lower-row slots, but remains one contiguous run and does not overlap another part; its explicit crop preserves the full fan.',
        'Small side lobes on the body require comparison in the assembled preview against the source renderer layering before staging.',
    ],
    'decision': {
        'continue_to_local_packing': True,
        'candidate_for_local_packing': True,
        'accepted_for_staging': False,
        'user_approved': False,
    },
}
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

progress = read(H / 'progress.json')
item = next(value for value in progress['items'] if value['name'] == NAME)
assert item['status'] == 'reference_prepared' and item.get('user_approved') is False
item['stage'] = 'down_generated_reviewed_pending_local_packing'
progress.update(current=NAME, updated_at=now())
(H / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

chain = read(H / 'conversation_chain.json')
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID'] and chain['dispatch_token'] == TOKEN
chain.update(
    current_stage='both_directions_reviewed_pending_local_packing',
    last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Turkey/generation/Down/review_20261028.json',
    updated_at=now(),
)
(H / 'conversation_chain.json').write_text(json.dumps(chain, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print(json.dumps({
    'character': NAME,
    'stage': item['stage'],
    'foreground_pixels': int(foreground.sum()),
    'lower_row_runs': row_runs[1],
    'tail_occupies_eighth_cell': cell_pixels[7] > 0,
    'user_approved': item.get('user_approved'),
}, ensure_ascii=False))
