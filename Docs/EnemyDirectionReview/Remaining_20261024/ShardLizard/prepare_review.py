"""Record actual reference observations and correct the unrequested direction prompts."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json, os

D = Path(__file__).resolve().parent
HERE = D.parent
chain = json.loads((HERE/'conversation_chain.json').read_text(encoding='utf-8'))
assert chain['state'] == 'active' and chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['current_character'] == D.name
assert chain['dispatch_token'] == 'scarabmounted-to-shardlizard-e066b2f9cbb54a5ca5b215b2e08ea8d2'
assert not (D/'reference_review.json').exists(), 'Preserve earlier review'
for direction in ['Up','Down']:
    assert not any((D/'generation'/direction/f).exists() for f in ['request.json','result.json','raw.png','uncertain_result.json'])

identity = ('Low chunky olive-brown lizard with ochre round patches and a pale scalloped lower flank/jaw, '
            'a broad blunt head with ivory eyes and angular golden forehead and cheek chips, '
            'one large flat-topped faceted GOLDEN dorsal shard with pale upper edge and ochre spot, '
            'four short stout reptile feet, and a long thick-rooted tapering segmented tail with small golden diamond chips and dorsal ridges. '
            'Thick dark olive outlines and simple warm cel shading. No ears, fur, saddle, rider, wings or extra organs.')
review = dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),
    method='Actually viewed original atlas, complete serialized source-prefab offline render and complete battle-prefab offline render; read both structures and original sprite/controller/event bindings. These are reference images, not Play evidence.',
    observed_identity=identity,
    source_bindings='Seven visible renderers: HeadNormal, Body, Tail, two LegFront and two LegBack. Source and battle use atlas GUID 172753c318ee91e4b8c57bf3f262cded. Battle receiver already binds HeadNormal/HeadAngry/HeadDead to the same atlas. Preserve these original side bindings.',
    controller='Existing Rat controller; Idle/Ready/Walk/Run/Attack/Death and Attack/Action/State/Speed. Attack has SetHead and Event; Death has SetHead. The Rat family is a controller contract, not permission to replace lizard anatomy with a rat.',
    reference_files=['reference/ShardLizard.png','reference/source_prefab_offline.png','reference/battle_prefab_offline.png','reference/source_structure.json','reference/battle_structure.json'],
    corrections='The generic preparation called the crystal shards cream. Actual images show warm golden cores with pale top facets and dark edges. The large back shard must not become a saddle, mane or cluster of new crystals. No mammal ears or fur.',
    up_anatomy='Axial rear head with no eyes, mouth, teeth or nostrils. Gold back shard belongs only to torso. Four splayed feet seen from their backs, no front toe faces on rear heels. Tail attaches at near lower rump and trails down toward viewer.',
    down_anatomy='Axial broad snout with paired ivory eyes and small original angular golden chips. Three aligned normal/angry/dead head states; angry opens jaw and dead follows original drooping/tongue state. Tail attaches at far upper rump and recedes upward behind torso.',
    future_layout_gate='Up tail art will have top-center root; pack_character defaults to bottom Tail pivot and an upward slice. Before staging/installing, set a character-specific top-root pivot and trailing-down Up tail layout, inspect overlap and keep tail root connected through gait/attack/death. Do not install the generic layout without actual visual review.',
    generated_visual_review=False,user_approved=False)
(D/'reference_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
plan_path = D/'anatomy_plan.json'
plan = json.loads(plan_path.read_text(encoding='utf-8'))
plan['identity'] = identity
plan['reference_review'] = review
plan_path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

for direction in ['Up','Down']:
    rear = direction == 'Up'
    view = ('REAR/BACK, travelling away toward screen UP. Show only the rear head plate, closed neck, dorsal torso and rump; NO eyes, mouth, teeth, nostrils or face on the back.' if rear else
            'FRONT, travelling toward viewer and screen DOWN. Broad snout centered below paired ivory eyes; neck is behind the head, not a detached floating ring.')
    heads = ['the SAME plain rear head silhouette, including only reference golden chips visible from behind; no facial features']*3 if rear else [
        'normal broad blunt lizard head, paired ivory eyes, small golden forehead/cheek chips and closed pale lower jaw',
        'same head size, alignment and chip placement; angry eyes and open biting jaw following the original HeadAngry',
        'same head size, alignment and chip placement; original drooping-eye/dead tongue expression following HeadDead']
    torso = ('neck at far TOP and broad near rump at BOTTOM' if rear else 'broad far rump at TOP and narrow near neck at BOTTOM')
    foot = ('rear heels and backs of feet, toes aim away toward screen UP and are largely occluded; no front-facing claw fan or reversed toe sole' if rear else
            'front of original short splayed reptile foot, toes forward/down; preserve source foot color and modest toe marks, no hooves or mammal paws')
    tail = ('ROOT at TOP CENTER, full tail trailing DOWN, tapering to its pointed tip with original small gold chips and segment ridges' if rear else
            'ROOT at BOTTOM CENTER, full tail receding UP toward far rump, tapering to its pointed tip with original small gold chips and segment ridges')
    prompt = f'''Use case: identity-preserve. Asset type: production 2D game cutout sprite parts sheet.
Image 1 is the CURRENT ORIGINAL ShardLizard sprite atlas. Image 2 is the complete CURRENT ORIGINAL character rendered from its serialized source prefab. Both are references for identity, palette, anatomy, outline and proportions.
Character ShardLizard: {identity}
Requested view: {view} Same elevated orthographic game perspective as the reference; create actual axial front/rear art, never rotate, mirror or stretch the side sprite to fake it.
Exactly FOUR equal columns by TWO equal rows. Seven detached parts in reading order, eighth cell empty:
1. HeadNormal: {heads[0]}; solid opaque neck root, NO torso.
2. HeadAngry: {heads[1]}; same head alignment and solid opaque neck root, NO torso.
3. HeadDead: {heads[2]}; same head alignment and solid opaque neck root, NO torso.
4. Body: complete low horizontal lizard torso/back ONLY, {torso}; retain ONE original broad flat-topped golden dorsal shard with pale edge/ochre spot and the small original embedded body chips; NO head, feet or tail, no extra spikes or shards.
5. LegFront: ONE detached LEFT foreleg, stout gently bent limb, rounded shoulder root at TOP CENTER; {foot}.
6. LegBack: ONE detached LEFT hindleg with original broad bent thigh, rounded hip root at TOP CENTER; {foot}. These two limb slices will be mirrored into exactly four legs, not extra limbs painted onto torso.
7. Tail: ONE complete detached thick-rooted lizard tail, {tail}; no torso or legs, no fluffy tuft, no upright scorpion arch.
Each part centered in its cell with 12 percent clear padding; no grid, labels or cell-crossing parts. No assembled creature. All three heads have identical scale, root position and alignment. Connection roots must be solid opaque shapes, never hollow tubes. Torso shard only on Body, head chips only on head, tail chips only on Tail; no duplicated adornment at neck joins.
Exact original warm olive-brown/gold/cream colors, thick smooth dark outlines, broad simple cel-shaded regions. No rat ears/fur despite the controller family, no horns, equipment, saddle, rider, new crystal fan or invented organs. Four short reptile legs and one attached tail in the eventual rig.
Background exactly flat RGB #FF00FF immediately outside every outline, with opaque source-colored interiors and no magenta holes. NO floor, ground shadow, cast shadow, glow, soft halo, vignette, checkerboard, text or watermark. Crisp complete outlines for later removal of magenta to real transparency.
'''
    (D/'generation'/direction/'prompt.txt').write_text(prompt,encoding='utf-8')
print(json.dumps(dict(name=D.name,reference_review_saved=True,directions=['Up','Down'],paid_requests=0)))
