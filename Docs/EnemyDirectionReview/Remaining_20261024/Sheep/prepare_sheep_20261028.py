from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,os,subprocess,sys
D=Path(__file__).resolve().parent;H=D.parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c=read(H/'conversation_chain.json');assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='Sheep' and c['dispatch_token']=='scarabmounted-to-sheep-fd7d7a5afb264ca7a1691363ab276f5f'
assert not (D/'anatomy_plan.json').exists()
legacy=subprocess.run([sys.executable,str(H/'audit_scope.py'),'scope_Sheep_before_20261028.json'],capture_output=True,encoding='utf-8',check=True)
(D/'legacy_scope_before_console.txt').write_text(legacy.stdout,encoding='utf-8')
subprocess.run([sys.executable,str(H/'prepare_character.py'),'Sheep'],check=True)
# Use the existing serialized renderer while keeping its contact proof local to Sheep.
source=(H/'render_source_reference.py').read_text(encoding='utf-8').replace("contact.save(HERE/'source_reference_contact.png')","contact.save(HERE/'Sheep'/'reference'/'battle_contact.png')")
old=sys.argv;sys.argv=[str(H/'render_source_reference.py'),'--battle','--name','Sheep']
exec(compile(source,str(H/'render_source_reference.py'),'exec'),{'__file__':str(H/'render_source_reference.py'),'__name__':'__main__'})
sys.argv=old
plan=read(D/'anatomy_plan.json')
plan['identity']='Cream-white cloud-shaped fluffy sheep with ochre oval patches, pale golden cream long face, huge white oval eyes, drooping outward ears and four tiny cream legs with dark ochre hooves. No horns, beard, equipment or separate tail in the original prefab/atlas.'
plan['source_observations']={'renderers':6,'legs':4,'tail_bound':False,'horns':False,'tail_policy':'Keep compatibility Tail slice transparent and omit both Tail rig nodes; do not invent a tail.'}
plan['reviewed_reference_sha256']={n:sha(D/'reference'/n) for n in ['source_prefab_offline.png','Sheep.png','Sheep.prefab','Enemy_Sheep.prefab','battle_prefab_offline.png','battle_structure.json']}
write(D/'anatomy_plan.json',plan)
for direction in ['Up','Down']:
    p=D/'generation'/direction/'prompt.txt';text=p.read_text(encoding='utf-8')
    text=text.replace('Cream-white fluffy sheep with ochre patches, cream face, big oval eyes and drooping ears, no horns, four tiny dark hooves, small woolly tail.',plan['identity'])
    text=text.replace('7. ONE full detached original tail, root at BOTTOM center, rising UP from rump; preserve exact tail type','7. EMPTY CELL. Original character has NO separate tail slice or renderer. Do not draw any tail.')
    text+='\nCharacter-specific locks from actual source review: the short foreleg and hindleg must each be a single solid cream wool upper leg with a dark ochre hoof, not a paw or bird toe. Rear feet show the heel/back of hoof without forward-facing cleft/toes. Front feet show the front of the hoof. All limb roots opaque, closed and rounded. Do NOT add horns, beard, collar, tail, equipment or new markings. Fluffy large cream wool torso with the original broad lobes and scattered ochre ovals; face is pale gold cream, never olive. Rear head has outer drooping ears and wool only, no face/eyes/nose/mouth/tongue. Front dead expression follows source empty white eyes and small tongue, not a new skull or wound. Exactly six occupied cells: three heads then torso in row 1; foreleg, hindleg then two EMPTY cells in row 2.\n'
    p.write_text(text,encoding='utf-8')
write(D/'art_selection.json',{'Up':'generation/Up/raw.png','Down':'generation/Down/raw.png','transparent_parts':['Up_Tail','Down_Tail'],'reason':'Source atlas and full serialized source/battle prefab have six renderers and no tail. Compatibility slices only.'})
write(D/'layout_adjustments.json',{'remove':['Up/Tail','Down/Tail'],'layout':{'motion':{'legAngle':9.0,'legLift':0.13,'bodyBob':0.008,'bodyRoll':0.9,'tailSwing':0.0}},'reason':'Four short sheep hooves with alternating diagonal phases and soft wool-body bob. No independent tail in source.'})
legacy=read(H/'scope_Sheep_before_20261028.json')
p=read(H/'progress.json');i=next(i for i in p['items'] if i['name']=='Sheep');assert i['status']=='not_started'
i.update(status='reference_prepared',user_approved=False,reference_review_file='Sheep/anatomy_plan.json');p.update(current='Sheep',updated_at=datetime.now(timezone(timedelta(hours=8))).isoformat());write(H/'progress.json',p)
write(D/'reference_review_20261028.json',dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),viewed=['reference/source_prefab_offline.png','reference/Sheep.png'],observation=plan['identity'],no_tail=True,prompt_sha256={d:sha(D/'generation'/d/'prompt.txt') for d in ['Up','Down']},legacy_unexpected=len(legacy['unexpected']),legacy_semantic_failures=[n for n,s in legacy['semantics'].items() if not s['pass']]))
print(json.dumps(dict(prepared='Sheep',tail=False,legacy_unexpected=len(legacy['unexpected']),legacy_semantic_failures=[n for n,s in legacy['semantics'].items() if not s['pass']]),ensure_ascii=False))
