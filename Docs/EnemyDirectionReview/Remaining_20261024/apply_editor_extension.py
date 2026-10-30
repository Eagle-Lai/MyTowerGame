"""Apply only staged Editor files after checking the local source baseline."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
snapshot={x['path']:x for x in json.loads((HERE/'source_snapshot.json').read_text(encoding='utf-8'))}
staged=sorted((HERE/'staged_code').glob('*.cs'))
manifest=[]
for p in staged:
    rel='Assets/Editor/'+p.name;dest=ROOT/rel
    before=hashlib.sha256(dest.read_bytes()).hexdigest().upper() if dest.exists() else None
    if rel in snapshot and before!=snapshot[rel]['sha256']:raise ValueError('Concurrent code drift: '+rel)
    if rel not in snapshot and dest.exists():raise ValueError('New Editor path already exists: '+rel)
    manifest.append({'path':rel,'before':before,'after':hashlib.sha256(p.read_bytes()).hexdigest().upper()})
for p in staged:(ROOT/'Assets/Editor'/p.name).write_bytes(p.read_bytes())
(HERE/'editor_extension_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'applied':len(manifest),'runtime_code_changes':0}))
