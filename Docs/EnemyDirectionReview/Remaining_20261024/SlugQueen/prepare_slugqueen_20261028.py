from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, subprocess, sys
D=Path(__file__).resolve().parent;H=D.parent;R=H.parents[2]
sys.path.insert(0,str(H))
from mcp_call import Client
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
c=read(H/'conversation_chain.json')
assert c['state']=='active' and c['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and c['current_character']=='SlugQueen' and c['dispatch_token']=='sheep-to-slugqueen-5dd11f24cb8646d0ac5a622d232ec22d'
assert not (D/'anatomy_plan.json').exists()
v=subprocess.run([sys.executable,str(H/'audit_scope.py'),'scope_SlugQueen_before_20261028.json'],capture_output=True,encoding='utf-8',check=True)
(D/'legacy_scope_before_console.txt').write_text(v.stdout,encoding='utf-8')
subprocess.run([sys.executable,str(H/'prepare_character.py'),'SlugQueen'],check=True)
source=(H/'render_source_reference.py').read_text(encoding='utf-8').replace("contact.save(HERE/'source_reference_contact.png')","contact.save(HERE/'SlugQueen'/'reference'/'battle_contact.png')")
sys.argv=[str(H/'render_source_reference.py'),'--battle','--name','SlugQueen']
exec(compile(source,str(H/'render_source_reference.py'),'exec'),{'__file__':str(H/'render_source_reference.py'),'__name__':'__main__'})
plan=read(D/'anatomy_plan.json')
plan['identity']='Legless low olive-brown slug queen, three broad rounded arching body lobes tapering to a small rear rump, ochre oval patches and cream short highlights. Rounded broad short head with gold eyes, circular protruding short snout. One tiny gold crown with dark oval jewel shapes is INTEGRATED ON THE HEAD only. No legs, feelers, wings, shell or separate tail.'
plan['source_observations']={'renderers':2,'body_lobes':3,'crown':'one, integrated in head','legs':0,'source_review':'Actual original atlas and full source prefab viewed. Normal stern gold eyes and round snout; angry open tooth mouth; dead blank round gold eyes and slack snout.'}
plan['reviewed_reference_sha256']={n:sha(D/'reference'/n) for n in ['source_prefab_offline.png','SlugQueen.png','SlugQueen.prefab','Enemy_SlugQueen.prefab','battle_prefab_offline.png','battle_structure.json']}
write(D/'anatomy_plan.json',plan)
for direction in ['Up','Down']:
    p=D/'generation'/direction/'prompt.txt';text=p.read_text(encoding='utf-8')
    text=text.replace('Legless brown segmented slug queen with ochre spots, small golden crown and short snout, stern gold eyes, large rounded arched back. Preserve crown, no legs.',plan['identity'])
    text=text.replace('including its original ears/horns/crest/hat','including its ONE tiny original gold crown; NO ears, horns, hair or extra crown')
    text=text.replace('complete central/back body section, original dorsal details and belly; no head or rear tip','ONE broad central domed olive-brown body lobe, with ochre patch and short cream highlight; NO head, crown, face, front lobe or rear tip')
    text=text.replace('ONE detached middle body segment, matching rounded back and pale belly','ONE rounded front collar body lobe to overlap under the head, solid opaque rounded root, olive-brown with cream highlight; NO crown or face')
    text=text.replace('ONE detached rear tip/rump, corresponding to the actual back of this creature','ONE rounded tapered rear body lobe/rump, closed olive-brown shape with original highlight; no long tail or appendage')
    text+='\nSlugQueen source-specific locks: exactly ONE crown, attached to each HEAD state only, never on any body lobe. No added spines, shell plates, slime, ground shadow, antennae, limbs, teeth on back, hair or purple recolor. Body consists of exactly three broad overlapping SOFT lobes, not tiny many-ring segments. Detached Body, Segment and Tip will form those three lobes only. Keep all connection interiors solid closed shapes, same warm olive-brown material, dark smooth outline and restrained ochre oval patches. The crown must be small relative to head. '
    if direction=='Up':text+='Rear head is a simple plain outer rounded back with the SAME one tiny crown; NO eyes, snout, mouth, teeth or face. Head at top, front collar immediately below, main dome centrally and tapered rear lobe below. Heads 1/2/3 have identical plain rear silhouettes.\n'
    else:text+='Front head centered below its small crown, wide gold eyes and circular short protruding snout. Normal stern eyelids; angry original angular eyes plus small tooth-filled open snout; dead blank round gold eyes and slack circular snout, no X eyes or new tongue. All three head states have matching dimensions. Head near bottom, front collar behind it, main dome above and tapered rear lobe at far top.\n'
    p.write_text(text,encoding='utf-8')
client=Client();project=client.identity()
code='''var controller=UnityEditor.AssetDatabase.LoadAssetAtPath<UnityEngine.RuntimeAnimatorController>("Assets/_UIAssets/Monsters/_Common/Animations/Larva/Controller.controller");return new {clips=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(System.Linq.Enumerable.Distinct(controller.animationClips),a=>new{name=a.name,path=UnityEditor.AssetDatabase.GetAssetPath(a),length=a.length,loop=a.isLooping,bindings=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetCurveBindings(a),b=>new{path=b.path,property=b.propertyName,keys=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetEditorCurve(a,b).keys,k=>new{time=k.time,value=k.value}))})),events=System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(UnityEditor.AnimationUtility.GetAnimationEvents(a),e=>new{time=e.time,function=e.functionName,intParameter=e.intParameter}))})),dependencies=UnityEditor.AssetDatabase.GetDependencies("Assets/Prefabs/Enemy/Enemy_SlugQueen.prefab",true)};'''
contracts=client.tool('execute_code',{'action':'execute','code':code})
write(D/'source_animation_contracts_20261028.json',dict(project=project,contracts=contracts,history=client.history))
legacy=read(H/'scope_SlugQueen_before_20261028.json')
write(D/'reference_review_20261028.json',dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),viewed=['reference/source_prefab_offline.png','reference/SlugQueen.png'],observation=plan['identity'],prompt_sha256={d:sha(D/'generation'/d/'prompt.txt') for d in ['Up','Down']},legacy_unexpected=len(legacy['unexpected']),legacy_semantic_failures=[n for n,s in legacy['semantics'].items() if not s['pass']],port_note='User moved MyTowerGame to HTTP Local 8088 in this chat; 8082 is FishTestGame. mcp_call.py default updated; every call still dynamically checks target identity.'))
p=read(H/'progress.json');item=next(i for i in p['items'] if i['name']=='SlugQueen');assert item['status']=='not_started'
item.update(status='reference_prepared',user_approved=False,reference_review_file='SlugQueen/anatomy_plan.json');p.update(current='SlugQueen',updated_at=datetime.now(timezone(timedelta(hours=8))).isoformat());write(H/'progress.json',p)
print(json.dumps(dict(prepared='SlugQueen',kind='crawler',legacy_unexpected=len(legacy['unexpected']),source_contracts=True)))
