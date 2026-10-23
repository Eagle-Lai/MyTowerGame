"""Read-only final comparison of the frozen production boundary with exact authorized exceptions."""
from pathlib import Path
import json,hashlib,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
data=json.loads((HERE/'handoff_boundary.json').read_text(encoding='utf-8'))
baseline=json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))
allowed={'Assets/Scripts/Enemy/EnemyDirectionalProfile.cs','Assets/Scripts/Enemy/EnemyDirectionalVisual.cs','Assets/Editor/EnemyDirectionPrefabBuilder.cs'}
allowed|={t['battle'] for t in baseline['targets']}
changed=[];unexpected=[]
for relative,expected in data['files'].items():
    p=ROOT/relative;current=hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.exists() else None
    if current!=expected:
        item={'path':relative,'before':expected,'after':current};changed.append(item)
        if relative not in allowed:unexpected.append(item)
report={'boundary':'handoff_boundary.json','changed':changed,'unexpected':unexpected,'frozen_inputs_unchanged':not unexpected,'note':'New direction resources and the two new Editor scripts are inventoried separately in the implementation manifest.'}
(HERE/'handoff_boundary_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'changed':len(changed),'unexpected':unexpected}))
