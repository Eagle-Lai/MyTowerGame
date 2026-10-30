from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, subprocess

root = Path(__file__).resolve().parents[4]
here = Path(__file__).resolve().parent
task = here.parent
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
progress = read(task/'progress.json')
item = next(x for x in progress['items'] if x['name'] == 'PirateBoar')
assert progress['current'] == 'PirateBoar' and item['status'] == 'blocked'
target = next(x for x in read(task/'local_baseline.json')['targets'] if x['name']=='PirateBoar')
before = read(task/'production_fingerprints_before.json')
protected = [target[k]+suffix for k in ['battle','source','atlas'] for suffix in ['', '.meta']]
drift = [p for p in protected if sha(root/p) != before[p]]
assert not drift, drift
baseline = {'observed_at': datetime.now(timezone.utc).isoformat(), 'current': progress['current'], 'completed_count':progress['completed_count'], 'item': item, 'production':{p:sha(root/p) for p in protected}, 'git_status':subprocess.check_output(['git','status','--short'],cwd=root,text=True,encoding='utf-8'), 'note':'Root AGENTS.md names FreedomTower_1; current explicit task and verified MCP identity target E:/MyTowerGame 2022.3.62f3c1.'}
(here/'session_revision_02_baseline.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for direction in ['Up','Down']:
    dest=here/'generation'/direction/'revision_02'
    dest.mkdir(exist_ok=True)
    assert not (dest/'request.json').exists()
    original=(here/'generation'/direction/'revision_01'/'prompt.txt').read_text(encoding='utf-8-sig')
    priority='''REVISION 02 CRITICAL CORRECTION. This is a sheet of disassembled animation parts. The fourth cell must be a HEADLESS, HATLESS animal body carrying ONLY a cannon and carriage. Do not add a tricorn or earring between cannon and torso. No skull symbol anywhere in cell 4. Fill that space with the plain wooden cannon carriage and unadorned golden skin. The detached head in cells 1-3 is the ONLY location of the tricorn and ear jewellery. Treat the rejected image as an error example, never as the desired design.
'''
    if direction=='Up':
        priority+='Rear leg cells 5 and 6 show the BACK HEEL: a single continuous smooth dark oval hoof heel without a central vertical line or split toes. No visible front-facing cloven toe pattern. Cannon is rear breech, not muzzle.\n'
    else:
        priority+='Cell 4 has a dark circular cannon muzzle at top, a PLAIN WOODEN support immediately underneath it, then a plain round spotted HEADLESS boar rump below. No face, hat, ears, rings or emblems in this fourth cell.\n'
    (dest/'prompt.txt').write_text(priority+original,encoding='utf-8')
print(json.dumps({'name':'PirateBoar','revision':'revision_02','fingerprint_drift':drift,'prompts':2}))
