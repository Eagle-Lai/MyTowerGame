from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
out=D/'generation/Up/revision_01'
out.mkdir(exist_ok=False)
prompt='''Use case: precise-object-edit. Production 2D game sprite cutout sheet for RoyalBoar.
Image 1 original atlas and image 2 complete prefab define identity/style. Image 3 is the rejected Up sheet. Correct ONLY these concrete mistakes: body contains two small faces and a cream hair tuft; rear feet have front toe clefts; rear heads contain projecting face tusks.
Regenerate a single exact 4-column by 2-row sheet on flat #FF00FF magenta. All parts isolated, 12% padding, no grid/text. Reading order:
1,2,3: THREE IDENTICAL plain BACKS of the head. Gold round back of skull, two outer backs of pointed ears, cream/gold swept original hair viewed from behind. Absolutely NO eyes, nostrils, mouth, snout or tusks. Do NOT add cheek faces. All three exact matching dimensions/alignment.
4: One very broad rounded golden oval boar TORSO ONLY, ochre irregular oval spots, a few original short flank fur points, darker ochre lower shaded strip. NO cream hair anywhere on torso. NO protruding neck bulb. NO eyes, nose, nostrils, mouth, snouts, ears, head or facial features anywhere. NO legs, feet or tail painted on torso. Smooth closed rounded top with solid fill, not an open stump.
5: ONE short detached foreleg viewed from BEHIND, rounded solid root top center, tiny tapered golden hoof at bottom. Show a plain continuous rear heel, NO toe split/cleft/line. No human toes.
6: ONE short detached hindleg viewed from BEHIND, rounded solid hip root top center, tiny tapered golden hoof at bottom with continuous plain rear heel and NO toe split/cleft/line. No human toes.
7,8: EMPTY magenta cells; original has no independent tail.
Orthographic elevated rear view moving screen UP. Match the original round squat boar, warm bright golden/ochre/cream palette, thick dark crisp smooth outline and simple broad flat cel-shaded regions. No crown, no added equipment. No perspective side view, no body faces, no duplicate forelock, no ground shadow, no glow, no gradients in background, no blur, no labels/watermark. All interiors opaque and solid; magenta only outside outlines.
'''
(out/'prompt.txt').write_text(prompt,encoding='utf-8')
record=dict(status='rejected_pending_targeted_revision',source='generation/Up/raw.png',sha256=hashlib.sha256((D/'generation/Up/raw.png').read_bytes()).hexdigest().upper(),actual_observations='Body has two small snout/eye-like faces and a duplicate cream tuft, despite assigned detached torso. Up hoof fronts have toe clefts; original source has short plain golden hoof blocks. Head silhouette has exposed tusks. Rejected before staging/production; one targeted revision will preserve original result.',revision='generation/Up/revision_01')
(D/'raw_review_up_initial.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Targeted Up revision_01 prompt saved; original preserved')
