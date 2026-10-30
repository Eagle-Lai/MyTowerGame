"""Wasp-only anatomy and initial image prompts; never touches production assets."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
OWNER = '01a1833c-f96c-74a1-b7f2-2281f6ab321d'
TOKEN = 'warg-to-wasp-20261028_235853-1e651dcf-1586-4ebc-9926-3b8be7348e7d'
chain = json.loads((RUN / 'conversation_chain.json').read_text(encoding='utf-8'))
assert (chain['state'], chain['owner_thread_id'], chain['current_character'], chain['dispatch_token']) == ('active', OWNER, 'Wasp', TOKEN)
assert os.environ.get('CODEX_THREAD_ID', OWNER) == OWNER
plan = json.loads((HERE / 'anatomy_plan.json').read_text(encoding='utf-8'))
plan.update(
    identity='Original golden ochre hovering wasp, very large rounded head, two long dark segmented antennae, round gold-brown eye plates, a small tapered black-brown and gold striped abdomen with its original tiny dangling gold claws, two cream veined wings represented by raised/lowered postures.',
    anatomy_observations={
        'wing_count': 2,
        'source_wing_nodes': 'WingUpL/R and WingDownL/R are two alternating poses of the SAME left/right wings, not four wings.',
        'claws': 'Small gold claws integrated in the source abdomen; keep integrated in the new Body slice. No six-leg walking rig.',
        'heads': 'Original receiver has Angry=0 and Dead=1. Preserve original events; new directional views provide Normal/Angry/Dead. Up head states all share one faceless rear shell.',
        'flight': 'Suspended original altitude; no ground shadow. Ready/Walk alternate source wing visibility at 12 Hz, Attack includes original Event(Attack) at 0.333333343 s; all native clips 0.5 s.',
        'connections': 'Wing roots share one attachment and common sprite canvas in both postures; head and abdomen overlap at opaque collar, wings render behind torso.'
    },
    source_review=['reference/Wasp.png', 'reference/source_prefab_offline.png', 'source_contract_20261029.json'],
)
(HERE / 'anatomy_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
for direction in ('Up', 'Down'):
    d = HERE / 'generation' / direction
    assert not any((d / f).exists() for f in ('request.json', 'raw.png', 'result.json', 'uncertain_result.json'))
    rear = direction == 'Up'
    view = ('TRUE AXIAL REAR/BACK, travelling away towards screen UP. Show the plain gold back of the huge head with the two segmented antennae viewed from behind. NO eyes, eyelids, face, mouth, mandibles or frontal mask on ANY rear head. Rear head is in front of upper thorax in world travel direction, abdomen trails below it.' if rear else
            'TRUE AXIAL FRONT, travelling toward viewer and screen DOWN. Two large round ochre-brown compound eye plates flank a small gold central face/mandible plate; eye plates stay amber-brown, not white mammal eyes. Both antennae rise from the same huge rounded head. Small striped tapered abdomen trails behind the head and is partly visible below it in the elevated game view.')
    head1 = 'Plain faceless REAR gold head shell, two long dark segmented antennae' if rear else 'Normal FRONT head with two large round gold-brown eye plates, simple closed gold face plate, two long dark segmented antennae'
    head2 = 'EXACT SAME faceless REAR head as cell 1, no expression or front face' if rear else 'SAME FRONT head, size and antenna alignment as cell 1; attack expression with subtly tense eye brow lines and slightly opened gold mandible plate, do not add teeth'
    head3 = 'EXACT SAME faceless REAR head as cell 1, no expression or front face' if rear else 'SAME FRONT head, size and antenna alignment as cell 1; dead expression with subdued eye highlight and simple closed eye marks over the brown eye plates, gold face plate closed'
    prompt = f'''Use case: identity-preserve. Asset type: production 2D game cutout sprite parts sheet for Unity.
Image 1 is the actual original Wasp sprite atlas. Image 2 is its complete serialized prefab rendered offline (it may show both wing poses together). Use these for exact palette, outline weight, proportions and character identity. The original has TWO wings, with two alternative flap poses, not four independent wings.
Character: {plan['identity']}
Requested view: {view}
Same slightly elevated orthographic cartoon game camera as the reference. A genuinely newly drawn front/rear view, never a rotated side sprite or three-quarter head. Warm honey gold (#efbb52), dark olive-brown thick outlines (#352e19), broad flat ochre shadow patches, cream wings (#fff3d8) with tan vein networks. Source-like flat cel art, NOT realistic insect anatomy, thin line art, 3D or painterly shading.
Make ONE sheet exactly 4 equal columns by 2 equal rows, six detached parts in reading order:
1. {head1}; HEAD ONLY including antennae, no abdomen or wings.
2. {head2}; HEAD ONLY, no abdomen or wings.
3. {head3}; HEAD ONLY, no abdomen or wings.
4. BODY ONLY: one small complete golden thorax plus rounded tapered abdomen with broad dark brown transverse bands, original tiny gold dangling claw shapes integrated on its lower sides, small pointed abdominal tip. Opaque rounded top collar. NO head, antennae, eyes or wings. Do not invent long jointed walking legs, fur or extra organs.
5. ONE LEFT WING, RAISED pose. Elongated oval cream membrane with sparse tan net veins matching source. Solid warm ochre attachment nub at RIGHT CENTER of its cell, wing spans diagonally LEFT and UP. One continuous wing, NO torso, head, second wing or floating connector.
6. The SAME LEFT WING, LOWERED pose. Same length, same cream outline, same vein scale and same warm ochre attachment nub at the EXACT SAME RIGHT CENTER cell coordinate as cell 5. Wing now spans diagonally LEFT and DOWN. Keep identical cell canvas and root; only wing pose changes. NO torso, head or additional wing.
7 and 8. EMPTY magenta.
All heads share exactly the same head size, neck point, antenna silhouette and alignment. One part per cell, centered with at least 12 percent empty padding; no cell-crossing antennae or wings, labels or grid. Solid opaque connection roots, no holes, detached collar rings or extra patches. All wing interiors are opaque cream and all veins are tan; no pink tint or see-through checkerboard. Root is only the small nub attached to its wing. No feet anywhere except the tiny source claws integrated in Body.
Background exactly flat RGB #FF00FF magenta immediately outside each outline. Part interiors opaque source colors. NO floor, ground shadow, cast shadow, glow, halo, vignette, text, watermark or complete assembled character. Crisp intact outlines for chroma-to-alpha extraction.
'''
    (d / 'prompt.txt').write_text(prompt, encoding='utf-8')
    intent = {
        'observed_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'owner_thread_id': OWNER, 'dispatch_token': TOKEN, 'character': 'Wasp',
        'direction': direction, 'revision': 'initial', 'max_requests': 1,
        'endpoint': 'https://aihub.dog/v1/images/edits', 'model': 'gpt-image-2',
        'quality': 'medium', 'size': '1536x1024', 'n': 1,
        'transport': 'curl_https_no_retry',
        'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
        'authorization': 'Current serial Wasp successor prompt and standing project Image API authorization',
    }
    assert not (d / 'initial_request_intent.json').exists()
    (d / 'initial_request_intent.json').write_text(json.dumps(intent, indent=2) + '\n', encoding='utf-8')
print('Wasp anatomy, two initial prompts and bounded request intents saved; no request sent.')
