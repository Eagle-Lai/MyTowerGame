"""Read-only audit of this polish against its own local baseline."""
from pathlib import Path
import json,hashlib,re,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];BATCH=HERE.parent/'Batch01_10'
baseline=json.loads((HERE/'baseline.json').read_text());names=baseline['names']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.exists() else None
def permitted(s):
 if s in ['Assets/Editor/EnemyDirectionalRigBuilder.cs','Assets/Editor/EnemyDirectionalAnimationPolish.cs','Assets/Editor/EnemyDirectionalAnimationPolish.cs.meta','Assets/Editor/EnemyDirectionBatchReview.cs']:return True
 if s in [f'Assets/Prefabs/Enemy/Enemy_{n}.prefab' for n in names]:return True
 return any(s.startswith(f'Assets/_UIAssets/Monsters/{"Scorpions" if n=="BlueScorpion" else "Dogs"}/{n}/Directions/') and not s.endswith('.png') for n in names)
current={s:sha(ROOT/s) for s in baseline['files']}
for folder in ['Assets','Packages','ProjectSettings','Luban']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file():
   s=p.relative_to(ROOT).as_posix()
   if s not in current and (folder!='Assets' or p.suffix in ['.cs','.meta','.prefab','.unity','.asset','.json','.anim','.controller','.png','.shader']):current[s]=sha(p)
changes=[{'path':s,'before_sha256':baseline['files'].get(s),'after_sha256':h,'bytes':(ROOT/s).stat().st_size if h else 0} for s,h in current.items() if h!=baseline['files'].get(s)]
unexpected=[c['path'] for c in changes if not permitted(c['path'])]
guid_fail=[];sprite_id_fail=[]
for s in current:
 if not s.endswith('.meta') or not (HERE/'before'/s).exists():continue
 a=(HERE/'before'/s).read_text();b=(ROOT/s).read_text()
 if re.findall(r'^guid: (.+)',a,re.M)!=re.findall(r'^guid: (.+)',b,re.M):guid_fail.append(s)
 if re.findall(r'spriteID: (.+)',a)!=re.findall(r'spriteID: (.+)',b):sprite_id_fail.append(s)
identities={s:sha(BATCH/s) for s in baseline['approved_batch_identity']}
runtime=[]
for n in names:
 for revision in ['runtime_polish_r01','runtime_polish_updeath_r02']:
  d=BATCH/n/revision
  if not (d/'actual_runtime_checks.txt').exists():continue
  checks=(d/'actual_runtime_checks.txt').read_text();rs=[json.loads(s) for s in (d/'actual_frames.jsonl').read_text().splitlines()]
  runtime.append({'name':n,'revision':revision,'pass':sum(s.startswith('PASS ') for s in checks.splitlines()),'fail':sum(s.startswith('FAIL ') for s in checks.splitlines()),'exception':(d/'exception.txt').exists(),'actual_frames':len(rs),'strictly_increasing':all(b['frame']>a['frame'] for a,b in zip(rs,rs[1:])),'death_facings':sorted(set(r['facing'] for r in rs if r['stage']=='DeathAutoRecycle'))})
report={'observed_at':datetime.datetime.now().astimezone().isoformat(),'baseline':'baseline.json (current disk, 11537 files; approved freeze drift=0)','changed_files':changes,'unexpected':unexpected,'prefabs_changed':[c['path'] for c in changes if c['path'].endswith('.prefab')],'unchanged_other_prefabs':len([s for s in current if s.startswith('Assets/Prefabs/Enemy/') and s.endswith('.prefab') and s not in [c['path'] for c in changes]]),'GUID_failures':guid_fail,'sprite_ID_failures':sprite_id_fail,'approved_history_unchanged':identities==baseline['approved_batch_identity'],'approved_history_identity':identities,'runtime':runtime,'runtime_complete':len(runtime)==6,'pass':not(unexpected or guid_fail or sprite_id_fail) and identities==baseline['approved_batch_identity'] and len(runtime)==6 and all(r['pass']==84 and not r['fail'] and not r['exception'] and r['strictly_increasing'] for r in runtime)}
(HERE/'scope_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(HERE/'implementation_manifest.json').write_text(json.dumps({'baseline':'baseline.json','files':changes},ensure_ascii=False,indent=2),encoding='utf-8')
(HERE/'final_fingerprints.json').write_text(json.dumps({'observed_at':report['observed_at'],'files':current},indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ['pass','unexpected','prefabs_changed','unchanged_other_prefabs','GUID_failures','sprite_ID_failures','runtime']},ensure_ascii=False))
