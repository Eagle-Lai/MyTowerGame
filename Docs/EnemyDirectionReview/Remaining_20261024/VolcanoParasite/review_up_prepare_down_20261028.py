from pathlib import Path
from datetime import datetime, timezone, timedelta
from PIL import Image
import hashlib,json,os
D=Path(__file__).resolve().parent;H=D.parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
c=read(H/'conversation_chain.json');name='VolcanoParasite'
assert c['state']=='active' and c['current_character']==name and c['owner_thread_id']==os.environ['CODEX_THREAD_ID']
raw=D/'generation/Up/raw.png';result=read(raw.with_name('result.json'));im=Image.open(raw)
assert result['status']==200 and result['bytes']==raw.stat().st_size
review={'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'raw_sha256':sha(raw),'format':im.format,'size':list(im.size),'mode':im.mode,'actual_visual_observations':['Viewed full 1536x1024 returned sheet. Three closed golden rear head cutouts with dark curved horns; no face, eyes, teeth, limbs, ground shadow or text.','Central body is a long horned golden spotted section, bottom row contains separate smaller segment and tapering rear tip. Body crosses nominal row boundary slightly, so use explicit source rectangles.','Pale underside caps are closed filled shapes. Need assembled overlap/pivot and alpha review before install. Horn count and overlap judged on combined rig, no art approval inferred.'],'decision':'accept raw for staging; not final combined/runtime approval','user_approved':False}
out=D/'generation/Up/raw_review_20261028.json';assert not out.exists();out.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
selection={'Up':'generation/Up/raw.png','Down':'generation/Down/raw.png','rectangles':{'Up_HeadNormal':[40,140,365,475],'Up_HeadAngry':[380,140,710,475],'Up_HeadDead':[715,140,1030,475],'Up_Body':[1095,30,1470,535],'Up_Segment':[365,590,670,910],'Up_Tip':[890,685,1120,910]},'note':'Explicit returned Up cell extents; preserve raw unchanged. Down rectangles pending real review.'}
assert not (D/'art_selection.json').exists();(D/'art_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
down=D/'generation/Down';assert not any((down/f).exists() for f in ['request.json','result.json','uncertain_result.json','raw.png','generation_intent.json'])
intent={'created_at':review['observed_at'],'character':name,'direction':'Down','owner_thread_id':c['owner_thread_id'],'dispatch_token':c['dispatch_token'],'max_requests':1,'model':'gpt-image-2','quality':'medium','size':'1536x1024','n':1,'transport':'curl_https_no_retry','Up_review_file':'generation/Up/raw_review_20261028.json','Up_raw_sha256':sha(raw),'prompt_sha256':sha(down/'prompt.txt')}
(down/'generation_intent.json').write_text(json.dumps(intent,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c.update(current_stage='Up_raw_reviewed_pending_Down_generation',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/VolcanoParasite/generation/Up/raw_review_20261028.json')
(H/'conversation_chain.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'Up_raw_reviewed':True,'Down_max_requests':1,'production_changes':0}))
