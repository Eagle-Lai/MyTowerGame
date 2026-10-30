from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, sys
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D.parent))
from mcp_call import Client
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
chain=json.loads((D.parent/'conversation_chain.json').read_text(encoding='utf-8'))
baseline=json.loads((D/'incremental_before_20261028.json').read_text(encoding='utf-8'))
plan=json.loads((D/'anatomy_plan.json').read_text(encoding='utf-8'))
identity='Low, broad, shaggy dark olive-brown Warg with large amber-gold eyes, pointed ears, gold inner ears only in front, dark broad muzzle, cream fangs, round ochre coat spots, small scratch/scar marks, raised dark shaggy shoulder/back FUR, four short broad paws and one long broad swept bushy tail. No collar, armor, saddle, rider, horns, golden dorsal spikes, wings or invented organs.'
plan.update(identity=identity,source_review={'images':['reference/Warg.png','reference/source_prefab_offline.png','reference/battle_prefab_offline.png'],'observed':'Original seven renderers with shared left/right fore/hind sprites. Shoulder silhouette is raised dark fur, not hard gold spikes. Angry head has widened fang mouth; dead head tongue and blank gold eye.','user_approved':False},anatomy_notes={'Up':'Axial rear, plain back of head and ears, far forelegs and near hindlegs, rounded heel backs with NO front toe divisions or visible claws; long tail attached to rear rump.','Down':'Axial front, paired eyes and centered muzzle; far hindlegs and near forelegs, forward toes; long tail emerges behind far rump.','gait':'Diagonal pair trot, short paw lift and small body bob; anchored shoulder/hip and tail roots.','occlusion':'Body overlaps roots of far limbs; near paws remain distinguishable. Head overlaps neck, tail covers its attachment with correct depth.'})
(D/'anatomy_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for direction in ['Up','Down']:
    folder=D/'generation'/direction
    assert not any((folder/p).exists() for p in ['request.json','raw.png','result.json','uncertain_result.json','generation_intent.json'])
    prompt=(folder/'prompt.txt').read_text(encoding='utf-8')
    prompt=prompt.replace('Dark olive shaggy warg with amber eyes, pointed ears, gold spots, long tail and four clawed paws.',identity)
    prompt+='\nWARG-SPECIFIC ANATOMY (from actual inspected source): Keep the low broad canine design and big cheek ruff, never a tall upright dog or human torso. The back silhouette is raised DARK shaggy fur, NOT gold spikes or horns. Ochre markings are rounded spots and small scars, NOT tiger stripes. The normal front mouth shows clenched cream fangs; angry mouth opens wider to bite. Dead front expression follows the original blank amber eye and drooping tongue. Front and rear paws are short, broad olive fur paws with understated dark toe arcs; no invented long white talons. All parts are fully opaque inside their outlines.\n'
    if direction=='Up':
        prompt+='Rear-specific: plain outer ear backs and shaggy back of head, absolutely NO eyes, nose, mouth, teeth, tongue or inner gold ear pads. All three head cells use the same plain rear head. Body is an elevated low quadruped back, neck/shoulders at TOP, broad spotted rump at BOTTOM. All legs detached. Foreleg and hindleg paw cells show rounded rear HEEL backs, NOT toe divisions or front-facing claws. Tail cell: one broad bushy tail with solid rounded ROOT at TOP CENTER, extending DOWN then sweeping gently RIGHT; opaque connected root, no hollow ring. This tail instruction overrides generic root direction.\n'
    else:
        prompt+='Front-specific: exact frontal axial paired eyes, big centered dark nose and cream fangs, not side or three-quarter. Body is a low broad canine back/chest seen at elevated orthographic angle, far rump at TOP, neck/chest connection at BOTTOM. No face on body. Paw toes face viewer. Tail cell: one broad bushy tail with solid rounded ROOT at BOTTOM CENTER, rising UP with a gentle RIGHT sweep; root is thick and opaque, not hollow. This tail instruction overrides generic root direction.\n'
    (folder/'prompt.txt').write_text(prompt,encoding='utf-8')
    intent={'created_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'owner_thread_id':chain['owner_thread_id'],'dispatch_token':chain['dispatch_token'],'character':'Warg','direction':direction,'max_requests':1,'model':'gpt-image-2','quality':'medium','size':'1536x1024','n':1,'transport':'curl_https_no_retry','prompt_sha256':sha(folder/'prompt.txt'),'inputs':{p:sha(D/'reference'/p) for p in ['Warg.png','source_prefab_offline.png']},'protected_six':baseline['protected_six'],'existing_request_check':'No Warg requests/results or generation processes existed at preflight.'}
    (folder/'generation_intent.json').write_text(json.dumps(intent,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Structured source contract: explicit serialization is required for arrays in execute_code.
old=json.loads((D/'preflight_20261028.json').read_text(encoding='utf-8'))
code=next(x['params']['arguments']['code'] for x in reversed(old['protocol_history']) if x['method']=='tools/call' and x['params']['name']=='execute_code')
code=code.replace('return new { battle=', 'return Newtonsoft.Json.JsonConvert.SerializeObject(new { battle=')
code=code.rsplit(' };',1)[0]+' });'
c=Client();project=c.identity()
result=c.tool('execute_code',{'action':'execute','code':code})
value=result.get('structuredContent') or json.loads(result['content'][0]['text'])
assert value['success'],value
contract=json.loads(value['data']['result'])
(D/'source_contract_20261028.json').write_text(json.dumps({'project':project,'contract':contract,'protocol_history':c.history},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'name':'Warg','prompts_refined':True,'clips':[{k:v[k] for k in ['name','length','loop','events']} for v in contract['clips']],'parameters':contract['parameters']},ensure_ascii=False))
