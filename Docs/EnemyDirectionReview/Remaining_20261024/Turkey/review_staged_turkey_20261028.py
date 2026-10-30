from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib
import json
import os
import numpy as np
from PIL import Image, ImageDraw

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


def inventory():
    return {
        path.relative_to(R).as_posix(): sha(path)
        for folder in ['Assets', 'Packages', 'ProjectSettings', 'Luban']
        for path in (R / folder).rglob('*')
        if path.is_file()
    }


chain = read(H / 'conversation_chain.json')
assert chain['state'] == 'active'
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['current_character'] == NAME
assert chain['dispatch_token'] == TOKEN
assert chain['current_stage'] in {
    'both_directions_reviewed_pending_local_packing',
    'alpha_repaired_pending_offline_recheck',
}

baseline = read(D / 'incremental_before_20261028.json')
assert inventory() == baseline['files'], 'Unity project files changed before installation'
assert not (D / 'staged_review_20261028.json').exists()

art = D / 'staged_art'
part_paths = sorted(list(art.glob('Up_*.png')) + list(art.glob('Down_*.png')))
assert len(part_paths) == 14, len(part_paths)
alpha = {}
for path in part_paths:
    im = Image.open(path).convert('RGBA')
    channel = np.asarray(im)[:, :, 3]
    padded = Image.new('L', (im.width + 2, im.height + 2), 255)
    holes = Image.fromarray(np.where(channel == 0, 255, 0).astype('uint8'))
    padded.paste(holes, (1, 1))
    ImageDraw.floodfill(padded, (0, 0), 127)
    internal_holes = int((np.asarray(padded) == 255).sum())
    assert internal_holes == 0, (path.name, internal_holes)
    assert channel.max() == 255 and channel.min() == 0
    alpha[path.name] = {
        'size': [im.width, im.height],
        'internal_transparent_holes': internal_holes,
        'sha256': sha(path),
    }

layout = read(art / 'Turkey_Directions.layout.json')
manifest = read(art / 'Turkey_Directions.sprites.json')
assert len(manifest['sprites']) == 14
assert [view['direction'] for view in layout['views']] == ['Up', 'Down']
for view in layout['views']:
    parts = view['parts']
    assert sum(part['role'] == 'leg' for part in parts) == 2
    assert sum(part['role'] == 'wing' for part in parts) == 2
    assert sum(part['role'] == 'tail' for part in parts) == 1
assert layout['anatomy'] == {'legs': 2, 'wings': 2, 'claws': 0, 'tails': 1, 'arms': 0, 'feelers': 0}

for path in [D / 'offline_Up.png', D / 'offline_Down.png', D / 'offline_rig_proof.png']:
    assert path.is_file()

report = {
    'observed_at': now(),
    'owner_thread_id': chain['owner_thread_id'],
    'dispatch_token': TOKEN,
    'baseline_sha256': sha(D / 'incremental_before_20261028.json'),
    'baseline_files': len(baseline['files']),
    'project_files_unchanged_before_install': True,
    'source_prefab_render_sha256': sha(D / 'reference' / 'source_prefab_offline.png'),
    'staged_art': {path.name: sha(path) for path in sorted(art.iterdir()) if path.is_file()},
    'alpha': alpha,
    'alpha_pass': True,
    'layout_anatomy': layout['anatomy'],
    'offline_proof': {
        'file': 'offline_rig_proof.png',
        'sha256': sha(D / 'offline_rig_proof.png'),
        'reference': 'source_prefab_offline.png',
        'runtime_evidence': False,
        'observations': [
            'Up has a plain rear head silhouette, paired legs and wings, and a broad center fan over the rear rump.',
            'Down preserves three different front expressions; the tail remains behind the torso and paired wings/feet remain distinct.',
            'Down body shoulder lobes sit under the wing roots and do not create detached extra limbs in the assembled preview.',
            'This is an offline composition proof only; Unity installation and actual Play-mode evidence remain outstanding.',
        ],
    },
    'decision': {
        'candidate_for_preinstall_review': True,
        'accepted_for_install': False,
        'user_approved': False,
    },
}
report_path = D / 'staged_review_20261028.json'
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

progress = read(H / 'progress.json')
item = next(value for value in progress['items'] if value['name'] == NAME)
assert item['status'] == 'reference_prepared' and item.get('user_approved') is False
item['stage'] = 'local_pack_reviewed_pending_preinstall'
progress.update(current=NAME, updated_at=now())
(H / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

chain = read(H / 'conversation_chain.json')
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID'] and chain['dispatch_token'] == TOKEN
chain.update(
    current_stage='local_pack_reviewed_pending_preinstall',
    last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Turkey/staged_review_20261028.json',
    updated_at=now(),
)
(H / 'conversation_chain.json').write_text(json.dumps(chain, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

print(json.dumps({
    'character': NAME,
    'stage': item['stage'],
    'parts': len(part_paths),
    'alpha_holes': sum(value['internal_transparent_holes'] for value in alpha.values()),
    'anatomy': layout['anatomy'],
    'asset_files_unchanged': True,
    'user_approved': item.get('user_approved'),
}, ensure_ascii=False))
