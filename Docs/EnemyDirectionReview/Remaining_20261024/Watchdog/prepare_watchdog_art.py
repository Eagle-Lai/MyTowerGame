"""Watchdog-only anatomy and bounded initial generation intents. No production writes."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os

D = Path(__file__).resolve().parent
BASE = D.parent
OWNER = '01a18379-8413-7bb3-bbc3-e0e5b2544d59'
TOKEN = 'wasp-to-watchdog-20261029_010456-a6f96d67-324e-4b30-9ff0-555b83354188'
chain = json.loads((BASE/'conversation_chain.json').read_text(encoding='utf-8'))
assert (chain['state'], chain['owner_thread_id'], chain['current_character'], chain['dispatch_token']) == ('active', OWNER, 'Watchdog', TOKEN)
assert os.environ.get('CODEX_THREAD_ID') == OWNER
plan = json.loads((D/'anatomy_plan.json').read_text(encoding='utf-8'))
plan.update(
    identity='Original stocky dark olive-brown watchdog, ochre circular coat patches, broad short dog muzzle with ivory jaw fangs, two FOLDED/FLOPPY triangular ears, thick gold collar with ivory conical spikes, four broad short paws and a TINY short wedge/stub tail with an ochre patch.',
    anatomy_observations={
        'ears': 'Source ears are folded triangular dog ears, not erect pointed wolf ears.',
        'head_collar': 'The original Head sprite includes the thick gold spiked collar. Keep collar integrated in every head state, no duplicate collar on Body.',
        'body': 'Low stocky spotted torso, no mane, dorsal spikes, armor or fur ruff.',
        'feet': 'Exactly four short broad paws. Up feet show rear heel/hock surfaces, not front toe/claw marks. Two mirrored forelegs and two mirrored hindlegs.',
        'tail': 'Tiny pointed wedge/stub with ochre patch, not a long bushy wolf tail. Root at top of detached piece, stub extends downward from rump in rear view.',
        'rear': 'Only back of head and outer backs of folded ears; all three Up head states reuse one faceless rear head. Gold collar remains at neck base.',
        'connections': 'Opaque head/neck/collar overlap torso. Foreleg shoulder and hindleg hip roots extend under torso. Short tail root hidden under rump.',
        'native_contract': 'Wolf Ready/Walk/Attack 0.5s, Death 0.416666657s. Preserve all native curves/PPtr/events, including Attack Event at 0.333333343 and SetHead sequence.'
    },
    source_review=['reference/Watchdog.png', 'reference/source_prefab_offline.png', 'reference/battle_prefab_offline.png', 'source_contract_20261029.json'],
)
(D/'anatomy_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
for direction in ('Up', 'Down'):
    out = D/'generation'/direction
    assert not any((out/f).exists() for f in ('request.json', 'raw.png', 'result.json', 'uncertain_result.json', 'initial_request_intent.json'))
    rear = direction == 'Up'
    view = ('TRUE AXIAL REAR/BACK, travelling AWAY toward screen UP. Plain faceless back of dog head, outer folded ears and back of gold spiked collar. NO eyes, brows, nose, muzzle, mouth, teeth, inner-ear pads or facial marks on rear head. Neck at top of torso, broad rump at bottom; paws show heels from behind.' if rear else
            'TRUE AXIAL FRONT, travelling toward viewer and screen DOWN. Centered broad short muzzle, two stern cream eyes, ivory jaw fangs, folded triangular ears and gold spiked collar below head. Far rump at top of torso, near neck/chest at bottom so head overlaps torso below it. Paws point toward viewer.')
    head1 = 'Plain faceless REAR head, outer backs of two folded triangular ears, dark olive-brown fur with ochre patches, gold collar with ivory conical spikes at lower neck edge' if rear else 'Normal FRONT head, two stern cream eyes, centered short broad muzzle, ivory jaw fangs, folded triangular ears, thick gold collar with ivory conical spikes below jaw'
    head2 = 'EXACT SAME faceless REAR head as cell 1, same collar and ears, no expression' if rear else 'SAME FRONT head, size, ears and collar as cell 1, angry attack expression with lowered brows and opened mouth showing original ivory fangs'
    head3 = 'EXACT SAME faceless REAR head as cell 1, same collar and ears, no expression' if rear else 'SAME FRONT head, size, ears and collar as cell 1, dead expression with closed eyes and slack muzzle, original ivory fangs retained'
    body = 'one low stocky spotted dog torso/back and rump, neck at TOP center, broad rump at BOTTOM' if rear else 'one low stocky spotted dog torso, far broad rump at TOP, narrower near neck/chest at BOTTOM'
    foot = 'REAR HEEL surface of foot; plain rounded heel at bottom, toes project away and are hidden, NO forward toe stripes, front claws or front paw face' if rear else 'FRONT of broad paw at bottom, short simple toe divisions matching source'
    prompt = f'''Use case: identity-preserve. Production 2D Unity cutout sprite parts sheet.
Image 1 is the actual original Watchdog sprite atlas; image 2 is its serialized prefab rendered offline. Preserve this exact character's palette, proportions, broad dark outlines and simple flat cartoon shapes. Character: {plan['identity']}
Requested direction: {view}
Same slightly elevated orthographic game camera as the original. A freshly drawn straight axial front or rear projection, no side profile or three-quarter turn. Stocky short-legged DOG, no wolf identity. Dark olive-brown body, large simple ochre circular spots, thick dark brown outlines, cream/ivory details, warm gold collar. Broad flat cel shadow regions; no realistic fur, 3D, soft painterly shading, extra armor, mane or dorsal spikes.
Make ONE sheet in exactly 4 equal columns by 2 equal rows, seven detached parts in reading order:
1. {head1}. HEAD AND ITS COLLAR ONLY; no torso or paws.
2. {head2}. HEAD AND ITS COLLAR ONLY.
3. {head3}. HEAD AND ITS COLLAR ONLY.
4. BODY ONLY: {body}. A complete opaque rounded torso, neck connection solid; NO head, collar, ears, legs, painted paws or tail.
5. ONE detached left FORELEG with thick short shoulder root at TOP CENTER and one broad short paw at bottom. {foot}. Solid rounded root; no body or other leg.
6. ONE detached left HINDLEG with thick short hip root at TOP CENTER and one broad short paw at bottom. {foot}. Slight hock shape appropriate for dog; no body or other leg.
7. ONE TINY short wedge/stub TAIL, dark olive-brown with ochre patch. Thick solid attachment ROOT at TOP CENTER, little triangular stub points DOWN. Compact short triangle, length similar to one paw, not a long curved or bushy tail. No rump or body attached.
8. EMPTY magenta.
All three heads share EXACT same silhouette size, ear locations, collar placement and alignment. Gold collar is ONLY on head cells; do not put another collar on torso. Every part has opaque solid connection roots, never holes or hollow tubes. One part per cell centered with generous 12 percent empty padding, no touching parts or cell-crossing spikes. Body has no hole at neck. Rear has NO facial features anywhere.
Background exactly solid RGB #FF00FF magenta immediately outside outlines. Part interiors opaque original colors; no pink holes. No floor, shadow, glow, halo, vignette, text, grid lines, labels, watermark, checkerboard or complete assembled character. Crisp intact outlines for chroma-to-alpha extraction.
'''
    (out/'prompt.txt').write_text(prompt, encoding='utf-8')
    intent = {'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),
              'owner_thread_id':OWNER,'dispatch_token':TOKEN,'character':'Watchdog','direction':direction,
              'revision':'initial','max_requests':1,'endpoint':'https://aihub.dog/v1/images/edits',
              'model':'gpt-image-2','quality':'medium','size':'1536x1024','n':1,'transport':'curl_https_no_retry',
              'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
              'authorization':'Current serial successor prompt and standing project Image API authorization'}
    (out/'initial_request_intent.json').write_text(json.dumps(intent,indent=2)+'\n',encoding='utf-8')
print('Watchdog anatomy, tailored prompts and single-request intents saved; no request sent.')
