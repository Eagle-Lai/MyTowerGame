"""Capture an additive restart baseline; never overwrite prior evidence."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
out = HERE / ('resume_' + stamp)
out.mkdir(exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
inventory = json.loads((HERE / 'local_baseline.json').read_text(encoding='utf-8'))
baseline = json.loads((HERE / 'production_fingerprints_before.json').read_text(encoding='utf-8'))
progress = json.loads((HERE / 'progress.json').read_text(encoding='utf-8'))
manifest = json.loads((HERE.parent / 'AllGIF/manifest.json').read_text(encoding='utf-8'))
git = subprocess.run(['git', 'status', '--porcelain=v1', '-z'], cwd=ROOT, capture_output=True, check=True).stdout
(out / 'git_status_before.bin').write_bytes(git)
paths = [p for p in (ROOT / 'Assets/Prefabs/Enemy').glob('*') if p.is_file()]
paths += [ROOT / p for p in baseline if p.endswith('.cs') and (ROOT / p).is_file()]
source_state = {}
for name in ['PossessedWarg', 'PirateBoar']:
    t = next(t for t in inventory['targets'] if t['name'] == name)
    source_state[name] = {p: {'sha256': sha(ROOT / p), 'matches_original_baseline': sha(ROOT / p) == baseline[p]}
                          for p in [t['battle'], t['battle']+'.meta', t['source'], t['source']+'.meta', t['atlas'], t['atlas']+'.meta']}
    paths += [ROOT / p for p in source_state[name]]
    art = ROOT / t['art_dir']
    if art.exists():
        paths += [p for p in art.rglob('*') if p.is_file()]
record = {'observed_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
          'project': str(ROOT), 'unity_version': (ROOT/'ProjectSettings/ProjectVersion.txt').read_text().splitlines()[0],
          'completed_count': progress['completed_count'], 'authorized_count': progress['authorized_count'],
          'gif_count': manifest['count'], 'source_state': source_state,
          'fingerprints': {p.relative_to(ROOT).as_posix(): sha(p) for p in set(paths)},
          'execution_policy': 'One character at a time. No overlapping production prefab writes or Unity reviews.',
          'rules_discrepancy': 'Root AGENTS.md still names D:/FreedomTower_1. Current user request and prompt explicitly target E:/MyTowerGame. AGENTS.md preserved.'}
(out / 'baseline.json').write_text(json.dumps(record, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
request = HERE / 'PossessedWarg/generation/Down/request.json'
recovery = {'observed_at': record['observed_at'], 'name': 'PossessedWarg', 'stage': 'generation_recovery',
            'status': 'blocked', 'category': 'uncertain_paid_request', 'request_sha256': sha(request),
            'request_started': json.loads(request.read_text())['started'],
            'local_evidence': 'Down has request.json only; no raw/result/uncertain_result and no active generate process was found. Local process absence does not establish provider failure or billing state.',
            'up_visual_observation': 'Existing Up raw viewed: rear cranium has no face, but ears show inner pads and feet show front toe divisions. Needs a new reviewed repair; not accepted for installation.',
            'decision': 'Do not resend Up or Down or delete request. Retain all evidence. Continue PirateBoar serially while provider result remains unconfirmed.',
            'next_step': 'Recover the original Down output or obtain definite provider failure/result status before any replacement paid request.',
            'source_fingerprints': source_state['PossessedWarg'],
            'production_modified': False, 'runtime_performed': False}
(out/'PossessedWarg_recovery.json').write_text(json.dumps(recovery,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
item = next(i for i in progress['items'] if i['name']=='PossessedWarg')
item.update(status='blocked', recovery_record=(out/'PossessedWarg_recovery.json').relative_to(ROOT).as_posix())
progress['current'] = 'PirateBoar'
progress['updated_at'] = record['observed_at']
(HERE/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'baseline':str(out/'baseline.json'), 'completed':progress['completed_count'], 'gif_count':manifest['count'], 'source_state':source_state},ensure_ascii=False))
