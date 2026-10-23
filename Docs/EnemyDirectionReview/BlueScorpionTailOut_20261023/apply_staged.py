"""Run only after a safe Unity handoff, with the editor idle and no recording active."""
from pathlib import Path
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
REL='Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions'
b=json.loads((HERE/'baseline.json').read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.exists() else None
protected={p:s for p,s in b['files'].items() if p.startswith('Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/') or p=='Assets/Prefabs/Enemy/Enemy_BlueScorpion.prefab' or p.startswith('Assets/Editor/EnemyDirection') or p.startswith('Assets/Scripts/Enemy/EnemyDirection')}
drift=[p for p,s in protected.items() if sha(ROOT/p)!=s]
if drift:raise RuntimeError('Protected files drifted; do not overwrite: '+str(drift))
files=list((HERE/'staged').glob('*'))
assert {p.suffix for p in files}=={'.json','.png'} and len(files)==3
for p in files:shutil.copy2(p,ROOT/REL/p.name)
print(json.dumps({'applied':[p.name for p in files],'protected_files_checked':len(protected)}))
