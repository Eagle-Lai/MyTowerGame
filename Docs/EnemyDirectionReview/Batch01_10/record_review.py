"""Record one completed review without overwriting historical runtime evidence."""
from pathlib import Path
from PIL import Image, ImageDraw
import argparse, json, hashlib, datetime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('revision');p.add_argument('--visual-note');a=p.parse_args()
d=HERE/a.name/a.revision
checks=(d/'actual_runtime_checks.txt').read_text(encoding='utf-8')
if 'FAIL ' in checks or (d/'exception.txt').exists():raise ValueError('Failed evidence cannot be recorded as complete')
scope_file=HERE/('scope_'+a.name+'_r01.json')
if scope_file.exists():
    scope=json.loads(scope_file.read_text(encoding='utf-8'))
    assert not scope['unexpected_prefab_changes'] and not scope['original_sources_or_GUID_drift'] and not scope['shared_animation_drift']
    assert all(v['pass'] for v in scope['prefab_semantics'].values()), 'Unexpected prefab semantics'
rows=[json.loads(s) for s in (d/'actual_frames.jsonl').read_text(encoding='utf-8').splitlines()]
if not rows or any(y['frame']<=x['frame'] for x,y in zip(rows,rows[1:])):raise ValueError('Invalid real frame log')
stages=['UpWalk','DownWalk','Attack','DeathAutoRecycle','Reuse','ContinuousTurns']
sheet=Image.new('RGB',(6*240,len(stages)*268),(40,48,37));draw=ImageDraw.Draw(sheet)
for y,stage in enumerate(stages):
    samples=[r for r in rows if r['stage']==stage]
    for x in range(6):
        r=samples[round((len(samples)-1)*x/5)]
        im=Image.open(d/r['file']).convert('RGB').resize((240,240),Image.Resampling.LANCZOS)
        sheet.paste(im,(x*240,y*268+28))
        draw.text((x*240+5,y*268+5),stage+' / '+str(r['frame']),fill='white')
sheet.save(d/'motion_contact.png')
baseline=json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))
t=next((t for t in baseline['targets'] if t['name']==a.name),None)
files=[ROOT/'Assets/Prefabs/Enemy'/('Enemy_'+a.name+'.prefab')]
if t:files+=sorted(p for p in (ROOT/t['art_dir']).rglob('*') if p.is_file())
# The batch reuses the approved example's material/shader; include that dependency
# and the unchanged original per-character sources in the observed input inventory.
files+=sorted(p for p in (ROOT/'Assets/_UIAssets/Monsters/Birds/AdvancedHen/Directions').rglob('*') if p.is_file())
if t:files += [ROOT/relative for relative in t['files']]
for relative in ['Assets/Scripts/Enemy/EnemyDirectionalProfile.cs','Assets/Scripts/Enemy/EnemyDirectionalVisual.cs','Assets/Editor/EnemyDirectionPrefabBuilder.cs','Assets/Editor/EnemyDirectionalRigBuilder.cs','Assets/Editor/EnemyDirectionBatchReview.cs']:
    files+=[ROOT/relative,ROOT/(relative+'.meta')]
fingerprints={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in files if p.is_file()}
(d/'observed_input_fingerprints.json').write_text(json.dumps({'observed_at':datetime.datetime.now().isoformat(),'note':'Captured after this isolated run; no production writes during capture.','files':fingerprints},indent=2),encoding='utf-8')
progress=json.loads((HERE/'progress.json').read_text(encoding='utf-8'))
progress['status']='installing_and_reviewing';progress['explicit_unity_handoff_received']=True
record={'runtime_revision':a.revision,'runtime_verified':True,'runtime_pass_count':checks.count('PASS '),'actual_frame_count':len(rows),'installed':True,'visual_reviewed':bool(a.visual_note),'visual_note':a.visual_note,'status':'reviewed' if a.visual_note else 'runtime_verified_visual_review_pending'}
if t:
    item=next(i for i in progress['items'] if i['name']==a.name);item.update(record)
    progress['current_index']=min(item['index']+1,11)
else:progress['approved_example_regression']=record
(HERE/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'name':a.name,**record},ensure_ascii=False))
