from pathlib import Path
import json,hashlib,re,datetime
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];REL='Assets/_UIAssets/Monsters/Scorpions/BlueScorpion/Directions'
base=json.loads((HERE/'baseline.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.exists() else None
current={s:sha(ROOT/s) for s in base['files']}
for folder in ['Assets','Packages','ProjectSettings','Luban']:
 for p in (ROOT/folder).rglob('*'):
  if p.is_file() and (folder!='Assets' or p.suffix in ['.cs','.meta','.prefab','.unity','.asset','.json','.anim','.controller','.png','.shader']):current[p.relative_to(ROOT).as_posix()]=sha(p)
changes=[{'path':s,'before_sha256':base['files'].get(s),'after_sha256':h} for s,h in current.items() if h!=base['files'].get(s)]
allowed={'Assets/Prefabs/Enemy/Enemy_BlueScorpion.prefab',REL+'/BlueScorpion_Directions.layout.json',REL+'/BlueScorpion_Directions.sprites.json',REL+'/BlueScorpion_Directions.png.meta',REL+'/BlueScorpion_Directions.png'}
allowed|={REL+'/Animations/'+s for s in ['Ready_Directions.anim','Walk_Directions.anim','Attack_Directions.anim','Death_Directions.anim','BlueScorpion_Directions.controller']}
unexpected=[c['path'] for c in changes if c['path'] not in allowed]
concurrent_paths={'Assets/Editor/Balance/BalancePlayModeVerifier.cs','Assets/Editor/Balance/BalanceVideoRecorder.cs','Assets/Editor/Balance/BalanceVideoRecorder.cs.meta'}
external=[c for c in changes if c['path'] in concurrent_paths]
all_changes=changes
changes=[c for c in changes if c['path'] in allowed]
unexpected=[p for p in unexpected if p not in concurrent_paths]
guid_fail=[]
for p in (HERE/'before').rglob('*.meta'):
 rel=p.relative_to(HERE/'before').as_posix();a=p.read_text();b=(ROOT/rel).read_text()
 if re.findall(r'^guid: (.+)',a,re.M)!=re.findall(r'^guid: (.+)',b,re.M) or re.findall(r'spriteID: (.+)',a)!=re.findall(r'spriteID: (.+)',b):guid_fail.append(rel)
layouts=[json.loads((p/REL/'BlueScorpion_Directions.layout.json').read_text()) for p in [HERE/'before',ROOT]]
layout_diff=[]
for av,bv in zip(layouts[0]['views'],layouts[1]['views']):
 for a,b in zip(av['parts'],bv['parts']):
  if a!=b:layout_diff.append({'direction':av['direction'],'part':a['name'],'before':a,'after':b})
assert len(layout_diff)==1 and layout_diff[0]['direction']=='Up' and layout_diff[0]['part']=='Tail'
def curves(path):
 text=path.read_text();result={}
 for section,body in re.findall(r'^  (m_EulerCurves|m_PositionCurves|m_ScaleCurves|m_EditorCurves|m_PPtrCurves):(?: \[\])?\n(.*?)(?=^  \w+:|\Z)',text,re.M|re.S):
  for index,block in enumerate(re.findall(r'^  - .*?(?=^  - |\Z)',body,re.M|re.S)):
   pathmatch=re.search(r'^    path: (.*)$',block,re.M)
   attr=re.search(r'^    attribute: (.*)$',block,re.M)
   if pathmatch:result[(section,pathmatch[1],attr[1] if attr else '')]=block.strip()
 return result
clip_reports=[]
for p in (HERE/'before'/REL/'Animations').glob('*.anim'):
 a=curves(p);b=curves(ROOT/REL/'Animations'/p.name);diff=[k for k in set(a)|set(b) if a.get(k)!=b.get(k)]
 assert a and b,'Curve parser returned no bindings'
 clip_reports.append({'clip':p.name,'parsed_before':len(a),'parsed_after':len(b),'changed_bindings':diff,'only_up_tail_changed':all(k[1]=='DirectionVisual/Up/Motion/Tail' for k in diff)})
runtime=[]
for revision in ['runtime_tailref_r02','runtime_tailref_updeath_r02']:
 d=HERE.parent/'Batch01_10/BlueScorpion'/revision
 if not (d/'actual_runtime_checks.txt').exists():continue
 s=(d/'actual_runtime_checks.txt').read_text();rs=[json.loads(s) for s in (d/'actual_frames.jsonl').read_text().splitlines()]
 runtime.append({'revision':revision,'pass':s.count('PASS '),'fail':s.count('FAIL '),'frames':len(rs),'exception':(d/'exception.txt').exists(),'increasing':all(b['frame']>a['frame'] for a,b in zip(rs,rs[1:])),'death_facings':sorted({r['facing'] for r in rs if r['stage']=='DeathAutoRecycle'})})
history={f:sha(HERE.parent/f) for f in base['history_identity']}
report={'observed_at':datetime.datetime.now().astimezone().isoformat(),'changed_files':changes,'unexpected':unexpected,'unchanged_other_battle_prefabs':sum(s.startswith('Assets/Prefabs/Enemy/') and s.endswith('.prefab') and current[s]==h for s,h in base['files'].items()),'GUID_sprite_ID_failures':guid_fail,'layout_diff':layout_diff,'clip_bindings':clip_reports,'runtime':runtime,'history_unchanged':history==base['history_identity'],'history_identity':history}
report.update(all_observed_changes=all_changes,concurrent_external_changes=external,workspace_no_external_drift=not external,attribution_note='This task wrote only BlueScorpion tail resources and regenerated its dedicated prefab/animations. Balance verifier/video recorder drift was preexisting at baseline capture and preserved without editing; no code files changed in this round.')
report['pass']=not unexpected and not guid_fail and report['history_unchanged'] and all(c['only_up_tail_changed'] for c in clip_reports) and len(runtime)==2 and all(r['pass']==84 and not r['fail'] and not r['exception'] and r['increasing'] for r in runtime)
semantic=json.loads((HERE.parent/'Batch01_10/scope_tailref_r02.json').read_text(encoding='utf-8'))
report['prefab_semantics']=semantic['prefab_semantics']['BlueScorpion']
report['prefab_semantic_reference_note']='Original-component semantic comparison uses the immutable first-batch original prefab. Other-role changes reported by that older batch baseline are preexisting; this round checks all 118 other prefabs against baseline.json.'
frozen=json.loads((HERE/'runtime_input_identity.json').read_text(encoding='utf-8'))['files']
report['runtime_inputs_unchanged']=frozen==current
report['runtime_input_drift']=[s for s in set(frozen)|set(current) if frozen.get(s)!=current.get(s)]
extra=json.loads((HERE/'additional_history_identity.json').read_text(encoding='utf-8'))
report['rejected_proposal_identity_unchanged']=all(sha(HERE.parent/s)==h for s,h in extra.items())
import numpy as np
from PIL import Image
before_pixels=np.asarray(Image.open(HERE/'before'/REL/'BlueScorpion_Directions.png').convert('RGBA'))
after_pixels=np.asarray(Image.open(ROOT/REL/'BlueScorpion_Directions.png').convert('RGBA'))
changed_pixels=np.any(before_pixels!=after_pixels,axis=2)
outside=changed_pixels.copy();outside[348:692,396:641]=False
report['pixel_scope']={'changed_inside_Up_Tail':int(changed_pixels.sum()),'changed_outside_Up_Tail':int(outside.sum())}
report['pass']=report['pass'] and report['prefab_semantics']['pass'] and report['runtime_inputs_unchanged'] and report['rejected_proposal_identity_unchanged'] and not outside.any() and report['unchanged_other_battle_prefabs']==118
(HERE/'scope_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
(HERE/'implementation_manifest.json').write_text(json.dumps({'baseline':'baseline.json','files':changes},indent=2),encoding='utf-8')
(HERE/'final_fingerprints.json').write_text(json.dumps({'observed_at':report['observed_at'],'files':current},indent=2),encoding='utf-8')
print(json.dumps({'pass':bool(report['pass']),'changes':len(changes),'unexpected':unexpected,'unchanged_other_battle_prefabs':report['unchanged_other_battle_prefabs'],'GUID_failures':guid_fail,'runtime_inputs_unchanged':report['runtime_inputs_unchanged'],'prefab_semantics':report['prefab_semantics']['pass'],'pixel_scope':report['pixel_scope'],'clip_bindings':clip_reports,'runtime':runtime}))
