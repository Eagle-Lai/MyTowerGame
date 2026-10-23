"""Preserve the approved batch identity and current local revision before polishing."""
from pathlib import Path
import json, hashlib, shutil, datetime
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
BATCH=HERE.parent/'Batch01_10'
NAMES=['BlackBear','BlackWolf','BlueScorpion']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.exists() else None
if (HERE/'baseline.json').exists():raise RuntimeError('Baseline already exists; never replace it')
old=json.loads((BATCH/'final_frozen_fingerprints.json').read_text(encoding='utf-8'))['files']
paths=set(old)
for folder in ['Assets','Packages','ProjectSettings','Luban']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and (folder!='Assets' or p.suffix in ['.cs','.meta','.prefab','.unity','.asset','.json','.anim','.controller','.png','.shader']):paths.add(p.relative_to(ROOT).as_posix())
files={s:sha(ROOT/s) for s in sorted(paths)}
targets=['Assets/Editor/EnemyDirectionalRigBuilder.cs']
for name in NAMES:
 family='Scorpions' if name=='BlueScorpion' else 'Dogs'
 base=ROOT/f'Assets/_UIAssets/Monsters/{family}/{name}/Directions'
 targets += [p.relative_to(ROOT).as_posix() for p in base.rglob('*') if p.is_file()]
 targets += [f'Assets/Prefabs/Enemy/Enemy_{name}.prefab']
for rel in targets:
 dest=HERE/'before'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dest)
source=[{'path':s,'sha256':h,'content':(ROOT/s).read_text(encoding='utf-8-sig')} for s,h in files.items() if s.endswith('.cs') and h]
(HERE/'source_snapshot.json').write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf-8')
data={'observed_at':datetime.datetime.now().astimezone().isoformat(),'names':NAMES,'files':files,'approved_batch_identity':{s:sha(BATCH/s) for s in ['implementation_manifest.json','final_frozen_fingerprints.json']},'drift_since_approved_freeze':[{'path':s,'frozen':h,'current':files[s]} for s,h in old.items() if files[s]!=h],'note':'Current disk is authoritative; no restore/reset. before/ holds complete proposed mutation inputs.'}
(HERE/'baseline.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
for name in NAMES:
 d=BATCH/name/'runtime_r01';records=[json.loads(s) for s in (d/'actual_frames.jsonl').read_text().splitlines()]
 board=Image.new('RGB',(1600,1240),(40,48,37));draw=ImageDraw.Draw(board)
 for row,stage in enumerate(['UpWalk','DownWalk','Attack']):
  samples=[r for r in records if r['stage']==stage and r['alpha']>.99]
  for col,phase in enumerate([.0,.25,.5,.75]):
   r=min(samples,key=lambda r:abs(r['normalizedTime']%1-phase))
   im=Image.open(d/r['file']).convert('RGB');im=im.crop((155,155,613,675)).resize((380,430))
   board.paste(im,(col*400,row*410+30));draw.text((col*400+10,row*410+8),f'BEFORE {name} {stage} phase {r["normalizedTime"]%1:.2f}',fill='white')
 board.save(HERE/f'{name}_before_contact.png')
print(json.dumps({'baseline_files':len(files),'source_files':len(source),'drift':len(data['drift_since_approved_freeze']),'backed_up':len(targets)}))
