from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re, subprocess, sys

D=Path(__file__).resolve().parent; H=D.parent; R=H.parents[2]
NAME='VolcanoParasite'; TOKEN='turkey-to-volcanoparasite-20261028-846ed4a4-803c-47fb-bd74-d1819f09a29c'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
now=lambda:datetime.now(timezone(timedelta(hours=8))).isoformat()
def write(p,v):
    if p.exists(): raise FileExistsError(p)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c=read(H/'conversation_chain.json')
assert (c['state'],c['owner_thread_id'],c['current_character'],c['dispatch_token'])==('active',os.environ['CODEX_THREAD_ID'],NAME,TOKEN)
t=next(x for x in read(H/'local_baseline.json')['targets'] if x['name']==NAME)
protected={p:sha(R/p) for p in [t['battle'],t['battle']+'.meta',t['source'],t['source']+'.meta',t['atlas'],t['atlas']+'.meta']}
old=read(H/'production_fingerprints_before.json')
assert all(protected[p]==old[p].upper() for p in protected)
assert all(sha(D/'reference'/Path(p).name)==s for p,s in protected.items())
assert not (R/t['art_dir']).exists()
files={p.relative_to(R).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (R/folder).rglob('*') if p.is_file()}
write(D/'incremental_before_20261028.json',{'observed_at':now(),'files':files,'protected_six':protected,'owner_thread_id':c['owner_thread_id'],'dispatch_token':TOKEN,'scope':['Assets','Packages','ProjectSettings','Luban'],'comparison':'Path union before/after; preserve existing user changes.'})
for f in ['source','battle']:
    txt=(R/t[f]).read_text(encoding='utf-8-sig')
    nodes=[]
    for m in re.finditer(r'^--- !u!(\d+) &(-?\d+)\s*\n(.*?)(?=^--- !u!|\Z)',txt,re.M|re.S):
        k,fid,body=int(m[1]),m[2],m[3]
        nodes.append({'class_id':k,'file_id':fid,'name':(re.search(r'^  m_Name: (.*)$',body,re.M).group(1) if re.search(r'^  m_Name: (.*)$',body,re.M) else None),'serialized':body})
    write(D/('original_'+f+'_structure_20261028.json'),{'path':t[f],'sha256':sha(R/t[f]),'objects':nodes})
subprocess.run([sys.executable,str(H/'character_step.py'),'prepare',NAME],check=True)
p=read(D/'anatomy_plan.json')
p.update(identity='Eyeless golden-ochre legless segmented parasite with an enormous ivory-toothed mouth, golden pale lower jaw and curved dark-brown volcanic horn spikes along its dorsal segments. No eyes, limbs, wings or separate tail.',source_observations={
 'viewed_images':['reference/VolcanoParasite.png','reference/source_prefab_offline.png'],
 'source_nodes':['Body2','Body1','Body','Jaw','Head','Shadow','AnchorBody','AnchorStatus','AnchorWeapon'],
 'head':'No eyes in original. Head carries upper teeth and three dark curved horns; separate lower jaw carries lower teeth. New axial Head cutouts include matching mouth/jaw, no invented eyes.',
 'body':'Three progressively smaller golden spotted sections with pale underside and curved dark horns. Body/Segment/Tip remain distinct overlapped crawler sections; no extra tail or feet.',
 'back':'Up must show closed rear cranium and horn backs, no eyes, nostrils or teeth.',
 'lifecycle':'BaseEnemy.Init resets/rebinds direction profile and expression, OnRecycle restores flash/alpha/spawn scale and speed. Receiver SetHead preserves actual original side sprite references. Dedicated cloned curves must keep original float/PPtr curves, event times, duration and loops.',
 'motion':'Existing crawler motion squashes/swells Body/Segment, small offset crawl wave, head lead on attack, attached fall plus BaseEnemy fade. No limb cadence.',
 'unity_occupancy':'Main is currently playing, review/balance/manual are false. No stop or production install until editor is handed over.'})
(D/'anatomy_plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for direction in ['Up','Down']:
    out=D/'generation'/direction; prompt=(out/'prompt.txt').read_text(encoding='utf-8')
    prompt+='\nVOLCANOPARASITE SPECIFICS: The original has NO EYES. Never add eyes, eyebrows, nostrils, ears, feet, legs or wings. The gold/ochre head is broad and low with massive ivory upper and lower teeth and a pale golden lower jaw only on the FRONT. Dark brown dorsal horns curve consistently backward; they are solid horns, no fire/lava/glow. The Head cells include the matching lower jaw for this single axial cutout rig. Body, Segment and Tip cells are three DIFFERENT connected crawler sections, not complete worms, heads or hollow rings. Connection shapes are solid and overlap. HeadNormal/HeadAngry/HeadDead remain equal scale; dead teeth may follow original chipped state. Body is not upright.\n'
    if direction=='Up': prompt+='REAR STRICTNESS: all three head cells are the exact same closed golden rear head with curved horn backs. No visible teeth, mouth line, eyes or face. Far head at TOP in assembled travel direction; rear tip trails at BOTTOM.\n'
    else: prompt+='FRONT STRICTNESS: center the mouth axially toward screen DOWN. No eyes. Ivory teeth and pale lower jaw are centered and symmetric, not a side-profile mouth or detached head. Rear body extends behind toward TOP.\n'
    (out/'prompt.txt').write_text(prompt,encoding='utf-8')
write(D/'reference_review_20261028.json',{'observed_at':now(),'owner_thread_id':c['owner_thread_id'],'dispatch_token':TOKEN,'protected_six':protected,'baseline_files':len(files),'observations':p['source_observations'],'anatomy_plan_sha256':sha(D/'anatomy_plan.json'),'prompt_sha256':{v:sha(D/'generation'/v/'prompt.txt') for v in ['Up','Down']},'art_review_status':'Source images reviewed; generated art not yet requested or reviewed.','user_approved':False})
write(D/'generation'/'Up'/'generation_intent.json',{'created_at':now(),'owner_thread_id':c['owner_thread_id'],'dispatch_token':TOKEN,'character':NAME,'direction':'Up','max_requests':1,'model':'gpt-image-2','quality':'medium','size':'1536x1024','n':1,'transport':'curl_https_no_retry','prompt_sha256':sha(D/'generation'/'Up'/'prompt.txt'),'inputs':{p.name:sha(p) for p in [D/'reference'/'VolcanoParasite.png',D/'reference'/'source_prefab_offline.png']},'protected_six':protected})
progress=read(H/'progress.json'); item=next(x for x in progress['items'] if x['name']==NAME)
item.update(status='reference_prepared',user_approved=False,reference_review_file=NAME+'/reference_review_20261028.json')
progress.update(current=NAME,updated_at=now());(H/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c.update(current_stage='reference_prepared_pending_Up_generation_editor_occupied',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/'+NAME+'/reference_review_20261028.json',updated_at=now())
(H/'conversation_chain.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'prepared':NAME,'baseline_files':len(files),'protected_six':len(protected),'status':item['status'],'production_changes':0}))
