"""Read-only boundary fingerprint; run after explicit handoff and before applying art/code."""
from pathlib import Path
import json,hashlib,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
output=HERE/'handoff_boundary.json'
if output.exists():raise ValueError('Boundary already recorded; do not replace evidence')
paths=set()
for folder in ['Luban','Assets/ConfigJson','Assets/Gen','Assets/Scenes','ProjectSettings']:
    paths|={p for p in (ROOT/folder).rglob('*') if p.is_file()}
for folder in ['Assets','Packages']:
    paths|={p for p in (ROOT/folder).rglob('*') if p.is_file() and p.suffix in {'.cs','.asmdef','.asmref'}}
paths|={p for p in (ROOT/'Assets/Prefabs/Enemy').glob('*') if p.is_file()}
paths|={ROOT/'Assets/BundleCollectorSetting.asset',ROOT/'Packages/manifest.json',ROOT/'Packages/packages-lock.json'}
data={'observed_at':datetime.datetime.now().isoformat(),'basis':'Explicit handoff boundary; supplements initial local baseline without replacing it.','files':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in sorted(paths) if p.is_file()}}
output.write_text(json.dumps(data,indent=2),encoding='utf-8');print('Boundary recorded: '+str(len(data['files']))+' files')
