"""Character-only intake; writes evidence in Docs, never production assets."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, subprocess

D = Path(__file__).resolve().parent
HERE = D.parent
ROOT = HERE.parents[2]
TOKEN = 'scarabmounted-to-shardlizard-e066b2f9cbb54a5ca5b215b2e08ea8d2'
chain = json.loads((HERE/'conversation_chain.json').read_text(encoding='utf-8'))
assert chain['state'] == 'active'
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['dispatch_token'] == TOKEN and chain['current_character'] == D.name
assert (ROOT/'ProjectSettings/ProjectVersion.txt').read_text().splitlines()[0].endswith('2022.3.62f3c1')
assert not (D/'anatomy_plan.json').exists(), 'Resume existing preparation instead'
assert not (D/'generation').exists(), 'Inspect existing generation instead'
assert not (D/'incremental_before_20261026.json').exists(), 'Never overwrite a baseline'

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
target = next(t for t in json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets'] if t['name'] == D.name)
protected = [target['battle'], target['battle']+'.meta', target['source'], target['source']+'.meta', target['atlas'], target['atlas']+'.meta']
global_before = json.loads((HERE/'production_fingerprints_before.json').read_text(encoding='utf-8'))
fingerprints = {p: sha(ROOT/p) for p in protected}
assert all(fingerprints[p] == global_before[p] for p in protected), 'Protected source drift'
for p in protected:
    ref = D/'reference'/Path(p).name
    assert ref.is_file() and sha(ref) == fingerprints[p], 'Reference differs: '+p
files = {p.relative_to(ROOT).as_posix(): sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
snapshot = dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(), files=files,
                protected_shardlizard=fingerprints, chain_owner=chain['owner_thread_id'], dispatch_token=TOKEN,
                legacy_scope_reference=dict(source='RoyalBoar/scope_incremental_20261026.json', unexpected_count=291, legacy_pass=False, classification_note='Historical audit unchanged; this is a new additive character intake'))
(D/'incremental_before_20261026.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for filename,args in [('git_status_before.txt',['status','--short']),('target_diff_before.txt',['diff','--',target['battle'],str(Path(target['source']).parent)])]:
    result = subprocess.run(['git',*args],cwd=ROOT,capture_output=True,check=True)
    (D/filename).write_bytes(result.stdout)
print(json.dumps(dict(name=D.name,files=len(files),protected=len(fingerprints),target_diff_bytes=(D/'target_diff_before.txt').stat().st_size)))
