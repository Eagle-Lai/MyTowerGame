"""Read current ownership and preserve an additive, character-only intake baseline."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, subprocess

D = Path(__file__).resolve().parent
HERE = D.parent
ROOT = HERE.parents[2]
TOKEN = 'scarab-to-scarabmounted-f3ab213fcd7c48c289d70377847fce8f'
chain = json.loads((HERE/'conversation_chain.json').read_text(encoding='utf-8'))
assert chain['state'] == 'active'
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['dispatch_token'] == TOKEN and chain['current_character'] == D.name
assert (ROOT/'ProjectSettings/ProjectVersion.txt').read_text().splitlines()[0].endswith('2022.3.62f3c1')
target = next(t for t in json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets'] if t['name'] == D.name)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
protected = [target['battle'], target['battle']+'.meta', target['source'], target['source']+'.meta', target['atlas'], target['atlas']+'.meta']
global_baseline = json.loads((HERE/'production_fingerprints_before.json').read_text(encoding='utf-8'))
fingerprints = {p: sha(ROOT/p) for p in protected}
assert all(fingerprints[p] == global_baseline[p] for p in protected), 'Protected source drift'
assert not (D/'incremental_before_20261026.json').exists(), 'Do not overwrite intake baseline'
files = {p.relative_to(ROOT).as_posix(): sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
snapshot = dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(), files=files, protected_scarabmounted=fingerprints, chain_owner=chain['owner_thread_id'], dispatch_token=TOKEN,
                legacy_scope_reference=dict(source='RoyalBoar/scope_incremental_20261026.json', unexpected_count=291, legacy_pass=False, classification_note='Preserve existing historical scope; no baseline reset'))
(D/'incremental_before_20261026.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for filename,args in [('git_status_before.txt',['status','--short']),('target_diff_before.txt',['diff','--',target['battle'],str(Path(target['source']).parent)])]:
    result = subprocess.run(['git','-c','core.quotePath=false',*args],cwd=ROOT,capture_output=True,check=True)
    (D/filename).write_bytes(result.stdout)
print(json.dumps(dict(name=D.name,files=len(files),protected_six=fingerprints,owner=chain['owner_thread_id'])))
