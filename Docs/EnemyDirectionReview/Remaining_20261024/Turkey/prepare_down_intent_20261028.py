from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import os

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
assert chain['current_stage'] == 'up_generated_reviewed_pending_down'
up_review = read(D / 'generation' / 'Up' / 'review_20261028.json')
assert up_review['decision']['continue_to_down_generation'] is True
assert up_review['decision']['user_approved'] is False

baseline = read(D / 'incremental_before_20261028.json')
current = {
    path.relative_to(R).as_posix(): sha(path)
    for folder in ['Assets', 'Packages', 'ProjectSettings', 'Luban']
    for path in (R / folder).rglob('*')
    if path.is_file()
}
assert current == baseline['files'], 'Project file inventory drifted since the Turkey baseline'

down = D / 'generation' / 'Down'
assert not any((down / filename).exists() for filename in [
    'generation_intent.json', 'request.json', 'result.json', 'uncertain_result.json', 'raw.png'
])
prompt = down / 'prompt.txt'
intent = {
    'created_at': now(),
    'owner_thread_id': chain['owner_thread_id'],
    'dispatch_token': TOKEN,
    'character': NAME,
    'direction': 'Down',
    'max_requests': 1,
    'model': 'gpt-image-2',
    'quality': 'medium',
    'size': '1536x1024',
    'n': 1,
    'transport': 'node_fetch',
    'prompt_sha256': sha(prompt),
    'inputs': {
        'atlas_sha256': sha(D / 'reference' / 'Turkey.png'),
        'source_render_sha256': sha(D / 'reference' / 'source_prefab_offline.png'),
    },
    'protected_six': baseline['protected_six'],
    'up_review': 'generation/Up/review_20261028.json',
    'up_review_sha256': sha(D / 'generation' / 'Up' / 'review_20261028.json'),
}
(down / 'generation_intent.json').write_text(json.dumps(intent, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

progress = read(H / 'progress.json')
item = next(value for value in progress['items'] if value['name'] == NAME)
assert item['status'] == 'reference_prepared' and item.get('user_approved') is False
item['stage'] = 'down_intent_prepared'
progress.update(current=NAME, updated_at=now())
(H / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

chain = read(H / 'conversation_chain.json')
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID'] and chain['dispatch_token'] == TOKEN
chain.update(
    current_stage='down_intent_prepared',
    last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Turkey/generation/Down/generation_intent.json',
    updated_at=now(),
)
(H / 'conversation_chain.json').write_text(json.dumps(chain, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print(json.dumps({'character': NAME, 'direction': 'Down', 'max_requests': 1, 'transport': intent['transport']}))
