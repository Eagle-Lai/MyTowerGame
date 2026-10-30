"""WinterBoar-only source audit and first image prompts; no production writes."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re

D = Path(__file__).resolve().parent
B = D.parent
R = B.parents[2]
C = json.loads((B/'conversation_chain.json').read_text(encoding='utf-8'))
assert C['state']=='active' and C['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert C['current_character']=='WinterBoar'
assert C['dispatch_token']=='winterbear-to-winterboar-20261029_121124-c33ba1f5-87c8-4aee-8729-55b098f67a75'
T = next(t for t in json.loads((B/'local_baseline.json').read_text(encoding='utf-8'))['targets'] if t['name']=='WinterBoar')

def write(p, v):
    assert not p.exists(), p
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

sources = {}
for key in ['source','battle']:
    p=R/T[key]
    text=p.read_text(encoding='utf-8-sig')
    blocks=[{'kind':int(m[1]),'id':int(m[2]),'text':m[3]} for m in re.finditer(r'^--- !u!(\d+) &(-?\d+)\s*\n(.*?)(?=^--- !u!|\Z)',text,re.M|re.S)]
    sources[key]={'path':T[key], 'sha256':hashlib.sha256(p.read_bytes()).hexdigest().upper(), 'all_serialized_blocks':blocks}
write(D/'source_serialized_audit_20261029.json', sources)

identity='Very round WHITE and light warm-gray shaggy boar, scattered mustard-ochre flank spots, large swept DARK BROWN bristle mane, fierce white eyes with thick dark brows, broad golden-ochre pig snout and TWO very long outward-upturned IVORY tusks. Four very short rounded pale hoof-like feet. No separate tail exists in the actual original prefab or atlas: DO NOT ADD A TAIL.'
plan={'name':'WinterBoar','kind':'quadruped','controller_family':'Boar','identity':identity,'parts':['HeadNormal','HeadAngry','HeadDead','Body','LegFront','LegBack'],'columns':3,'rows':2,'source':T['source'],'atlas':T['atlas'],'art_dir':T['art_dir'],'controller':T['controller'], 'source_review':{'atlas':'Complete original atlas and complete original prefab render actually viewed in this chat','bound_renderers':6,'legs':4,'independent_tail':False,'source_body_features':'mane and one visible side ear are integrated in original Body; new views allocate both ears only to head, mane only to body','native_contract':'Ready/Attack/Death/Walk 0.5s at 60fps; Ready and Walk loop; Attack SetHead1@0, Event Attack@0.333333343, SetHead0@0.5; Death SetHead2@0','lifecycle':'BaseEnemy.Init/Rebind/ResetForSpawn, movement-facing with hysteresis, shared flash property blocks, TickDeathFade and OnRecycle reviewed; no shared C# modifications'},'reviewed_at':datetime.now(timezone(timedelta(hours=8))).isoformat()}
write(D/'anatomy_plan.json',plan)
for direction in ['Up','Down']:
    rear=direction=='Up'
    view=('TRUE REAR/BACK view, moving AWAY toward screen UP. Camera elevated about 30 degrees. See only OUTER BACKS of two triangular ears and cream rear skull; NO eyes, brows, nostrils, nose, mouth, teeth, tusks or inner-ear cups on rear head. Brown dorsal mane is on BODY ONLY, running AXIALLY down the upper spine.' if rear else 'TRUE straight-on FRONT view, moving TOWARD viewer toward screen DOWN, same elevated orthographic game camera about 30 degrees. Face symmetrical, nose centrally beneath the two eyes, two enormous symmetric ivory tusks extend outward and upward. NOT side view, NOT three-quarter. The body recedes above the near head, NOT an upright humanoid torso.')
    head=('Small rounded cream shaggy REAR SKULL with two triangular OUTER ear backs. Solid rounded neck root at lower edge. No face or inner ear markings; no mane duplicated here. All three head cells IDENTICAL.' if rear else 'Complete fierce boar FACE: white eyes with thick swept dark-brown brows, centered broad golden snout with TWO nostrils, two huge ivory outward-upturned tusks, white cheek bristles. Two small triangular ears at upper corners. Head only, no torso, legs or dorsal mane. Solid cream neck root behind upper head for overlap.')
    body=('Broad plump cream-white spotted quadruped BACK/RUMP, neck/shoulders at TOP, broad near rump at BOTTOM. Dark swept bristle mane runs DOWN THE CENTER upper back, tapering toward rump. Shaggy edge and sparse ochre spots at sides. NO face, ears, tusks, head, tail, legs or feet. Solid opaque cream shoulder/neck area for rear head overlap; no hollow collar.' if rear else 'Broad plump cream-white spotted quadruped TORSO, broad far rump at TOP, narrow near shoulder/neck at BOTTOM, with DARK BROWN bristle mane visible on top of far back. Sparse ochre patches and gray underside. NO ears, eyes, brows, snout, tusks, head, legs, feet or tail. Solid opaque cream near chest/neck for head overlap, no open hollow collar.')
    foot=('REAR HEEL of the short pale hoof-like foot, travel points AWAY/UP. Plain smooth heel face, NO front toe lines, NO claws facing viewer.' if rear else 'FRONT face of short rounded pale hoof-like foot, aimed TOWARD/DOWN. Simple original cream hoof-like oval, tiny subtle central cleft only if needed; no added claws.')
    slots=[head,head if rear else head+' Same identity/alignment, angrier brows and clenched snout.',head if rear else head+' Same identity/alignment, original dead blank upward eyes and relaxed snout; tusks remain intact.',body,'ONE separate very short LEFT FORELEG, rounded shoulder root at TOP CENTER, cream fur with warm gray side shade; '+foot,'ONE separate very short LEFT HINDLEG, rounded hip root at TOP CENTER, cream fur with warm gray side shade; '+foot]
    prompt='''Use case: identity-preserve. Asset type: production 2D game cutout sprite parts sheet.
Image 1: ORIGINAL atlas, identity/style reference. Image 2: complete ORIGINAL prefab render, identity and proportions reference. Preserve these exact colors, outline weight and broad simple cartoon cel shading; do not redesign as a bear or realistic hog.
Character WinterBoar: '''+identity+'\nRequested direction: '+view+'''
Sheet exactly THREE equal columns by TWO equal rows. Six detached parts, in reading order:
'''+ '\n'.join(str(i+1)+'. '+s for i,s in enumerate(slots))+'''
Each part entirely inside its own 512x512 nominal cell, 12 percent clear padding, no grid or text. Heads have identical scale and alignment. Torso fills its own cell. This is a CUTOUT PARTS sheet, never an assembled creature. All limbs detached. Keep roots solid and rounded, with enough overlap to hide joints. Match original short-legged round-bodied silhouette. Ear assignment: BOTH ears only on head slices; NO second ears on torso. Mane assignment: dorsal bristle crest only on torso. Actual source has no independent tail; none anywhere. Front and rear views are anatomically distinct.
Background uniformly flat RGB #FF00FF magenta right outside outlines. Entire part interiors opaque in source cream/ochre/brown colors. No magenta holes. NO floor, NO ground shadow, NO cast shadow, NO glow, NO blur, NO halo, NO checkerboard, NO text, NO watermark. Crisp smooth dark contour, simple solid cel regions, no noisy texture or extra anatomy.
'''
    out=D/'generation'/direction
    out.mkdir(parents=True,exist_ok=True)
    assert not any((out/x).exists() for x in ['request.json','raw.png','result.json','prompt.txt'])
    (out/'prompt.txt').write_text(prompt,encoding='utf-8')
    write(out/'generation_intent.json',{'character':'WinterBoar','direction':direction,'mode':'initial','owner_thread_id':C['owner_thread_id'],'dispatch_token':C['dispatch_token'],'max_requests':1,'model':'gpt-image-2','quality':'medium','size':'1536x1024','n':1,'source_review':'source_serialized_audit_20261029.json and anatomy_plan.json'})
progress=json.loads((B/'progress.json').read_text(encoding='utf-8'))
item=next(x for x in progress['items'] if x['name']=='WinterBoar')
assert item['status']=='not_started'
item.update(status='reference_prepared',stage='source_reviewed_prompts_ready',anatomy_plan='WinterBoar/anatomy_plan.json')
progress['current']='WinterBoar'
progress['updated_at']=datetime.now(timezone(timedelta(hours=8))).isoformat()
(B/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for key,s in sources.items():
    print(key, 'blocks',len(s['all_serialized_blocks']))
    for b in s['all_serialized_blocks']:
        if b['kind'] in [1,4,114,95,58,61]:
            print(b['kind'],b['id'],b['text'] if b['kind'] in [114,95,58,61] else '\n'.join(l for l in b['text'].splitlines() if any(k in l for k in ['m_Name:','m_LocalPosition:','m_LocalRotation:','m_LocalScale:','m_Father:'])))
print('WinterBoar source reviewed; no paid requests sent.')
