"""WhiteWolf-specific anatomy and one-request intents. Writes Docs only."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os

D = Path(__file__).resolve().parent
BASE = D.parent
OWNER = '01a183d9-2ad7-73d2-b736-3057ef92f215'
TOKEN = 'watchdog-to-whitewolf-20261029_024758-616f3dd3-f8a9-4ec4-b44b-f70f383f1fbf'
chain = json.loads((BASE/'conversation_chain.json').read_text(encoding='utf-8'))
assert (chain['state'], chain['owner_thread_id'], chain['current_character'], chain['dispatch_token']) == ('active', OWNER, 'WhiteWolf', TOKEN)
assert os.environ.get('CODEX_THREAD_ID') == OWNER
plan = json.loads((D/'anatomy_plan.json').read_text(encoding='utf-8'))
plan.update(
    identity='Original low robust shaggy WOLF: white/ivory upper fur and cheek ruff, large warm-gray coat regions and broad ochre round patches, golden eyes, upright pointed ears with ochre inner pads, long narrow muzzle, ivory fangs, jagged white back ruff, four short gray/white paws, and a LONG BUSHY curved gray tail with a white outer stripe and tip. NO collar or equipment.',
    anatomy_observations={
        'ears': 'Two tall upright pointed wolf ears, pale outer fur, ochre inner pads visible only from front.',
        'head': 'Long muzzle and pointed cheek ruff; frontal normal has stern golden eyes and ivory fangs, angry opens the long jaw, dead has closed eyes and a slack ochre tongue. No collar.',
        'body': 'Low robust warm-gray torso, broad round ochre patches and jagged white dorsal fur; no horns, armor or actual dorsal spines.',
        'feet': 'Exactly four short paws: straight foreleg and bent hock hindleg. Rear feet show heel/hock surfaces, without front toe stripes or claws.',
        'tail': 'Long curved bushy gray/white wolf tail. Detached root at TOP CENTER, tail extends DOWN to a swept pointed white tip. Root hidden under rump; pivots explicitly revised to root, not default bottom.',
        'rear': 'Faceless white/gray back of wolf head, outer pointed ears and rear neck fur. No golden eyes, inner ear pads, muzzle, fangs or facial marks. Same head in all three Up states.',
        'connections': 'Opaque neck overlaps torso, shoulder and hip caps extend under torso; four paws remain distinct. Long tail attaches to rump with root concealed.',
        'native_contract': 'Wolf Ready/Walk/Attack 0.5s, Death 0.416666657s. Preserve source float/PPtr keys, original SetHead and Attack events, duration and loop flags.'
    },
    source_review=['reference/WhiteWolf.png', 'reference/source_prefab_offline.png', 'reference/battle_prefab_offline.png', 'source_contract_20261029.json'],
)
(D/'anatomy_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
for direction in ('Up', 'Down'):
    out = D/'generation'/direction
    assert not any((out/f).exists() for f in ('request.json', 'raw.png', 'result.json', 'uncertain_result.json', 'initial_request_intent.json'))
    rear = direction == 'Up'
    view = ('TRUE AXIAL REAR/BACK, travelling AWAY toward screen UP. Only faceless back of wolf head, outer backs of upright pointed ears, white rear neck ruff. NO eyes, brows, nose, muzzle, mouth, fangs, inner-ear pads or facial marks. Neck at TOP of torso and broad rump at BOTTOM. Paws show heels from behind.' if rear else
            'TRUE AXIAL FRONT, travelling toward viewer and screen DOWN. Centered long wolf muzzle, two stern golden eyes, ivory jaw fangs, tall pointed ears with ochre inner pads, white cheek ruff. Far rump at TOP of torso, near neck/chest at BOTTOM; head overlaps below torso. Paws point toward viewer.')
    head1 = 'Plain faceless REAR wolf head, upright pointed ears seen from behind, spiky white/ivory cheek and neck ruff, warm-gray fur and simple ochre coat patches' if rear else 'Normal FRONT wolf head, golden eyes, centered LONG muzzle, brown nose, ivory jaw fangs, tall upright pointed ears with ochre inner pads, spiky ivory cheek ruff'
    head2 = 'EXACT SAME faceless REAR head as cell 1, identical outline, no expression or face' if rear else 'SAME FRONT head, size, ears and fur as cell 1; angry attack with lowered brows and open long jaw showing ivory fangs'
    head3 = 'EXACT SAME faceless REAR head as cell 1, identical outline, no expression or face' if rear else 'SAME FRONT head, size, ears and fur as cell 1; dead expression with closed golden eyelids and slack jaw and small hanging ochre tongue, ivory fangs retained'
    body = 'one low robust spotted wolf torso/back, neck at TOP CENTER and broad rump at BOTTOM' if rear else 'one low robust spotted wolf torso, far broad rump at TOP and near neck/chest at BOTTOM CENTER'
    foot = 'REAR HEEL surface, rounded plain heel at bottom with a subtle hock, toes point away and are hidden; NO front claws, toe stripes, pads or front paw face' if rear else 'FRONT paw face at bottom, short simple toe divisions and ivory claws matching source'
    prompt = f'''Use case: identity-preserve. Production 2D Unity cutout sprite parts sheet.
Image 1 is the actual original WhiteWolf atlas. Image 2 is the assembled serialized source prefab rendered offline. Preserve THIS exact character, its palette, large round spots, robust short-legged proportions, thick dark-brown outlines and simple flat cartoon art. Character: {plan['identity']}
Requested direction: {view}
Slightly elevated orthographic game view consistent with original, freshly drawn straight axial front/rear, no side profile, no three-quarter rotation. White/ivory upper fur, large warm gray regions, broad ochre circular spots, brown-black outlines, gold eyes and ivory fangs. Flat cel shadow shapes. NO fluffy realistic rendering, soft painterly shading, 3D, collar, harness, saddle, armor, horns, additional dorsal spikes or extra equipment.
Make ONE sheet in exactly FOUR equal columns by TWO equal rows, SEVEN detached parts in reading order:
1. {head1}. HEAD ONLY, including rear neck fur, no torso, paws or tail.
2. {head2}. HEAD ONLY.
3. {head3}. HEAD ONLY.
4. BODY ONLY: {body}. Complete opaque torso with jagged white dorsal ruff and gray/ochre patches. Solid neck connection; NO head, ears, face, collar, legs, painted paws or tail on body.
5. ONE detached left FORELEG, thick short shoulder root at TOP CENTER, short straight leg and broad small paw at BOTTOM. White/gray fur and ochre patch. {foot}. No body or extra leg.
6. ONE detached left HINDLEG, thick hip root at TOP CENTER, compact bent hock and broad small paw at BOTTOM. White/gray fur and ochre patch. {foot}. No body or extra leg.
7. ONE detached LONG BUSHY curved wolf TAIL. Thick solid ROOT at TOP CENTER, tail extends DOWN and curves slightly to the right, tapered swept white TIP at BOTTOM RIGHT. Long gray center with broad white outer stripe/white tip, thick dark outline. Length around TWO paw lengths, no body or rump attached. Distinctly a bushy wolf tail, not a stub, feather, tentacle or thin cat tail.
8. EMPTY magenta.
All three heads share exactly the same silhouette size, upright ear locations and alignment. Every part has solid opaque connection roots, no holes or hollow tubes. One part centered in each cell, generous 12 percent empty padding; no cell crossing. Rear has no facial features anywhere. Exactly two leg parts, one of each type, will be mirrored for four paws in Unity.
Background exactly solid RGB #FF00FF magenta immediately outside outlines. Opaque character interiors, no pink holes. No floor, shadow, halo, glow, vignette, text, labels, grid, checkerboard, watermark or assembled character. Crisp intact outlines for chroma-to-alpha extraction.
'''
    (out/'prompt.txt').write_text(prompt, encoding='utf-8')
    intent = {'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),
              'owner_thread_id':OWNER,'dispatch_token':TOKEN,'character':'WhiteWolf','direction':direction,
              'revision':'initial','max_requests':1,'endpoint':'https://aihub.dog/v1/images/edits',
              'model':'gpt-image-2','quality':'medium','size':'1536x1024','n':1,'transport':'curl_https_no_retry',
              'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
              'authorization':'Current serial successor prompt and standing project Image API authorization'}
    (out/'initial_request_intent.json').write_text(json.dumps(intent,indent=2)+'\n',encoding='utf-8')
print('WhiteWolf-specific anatomy, prompts and bounded initial intents saved. No request sent.')
