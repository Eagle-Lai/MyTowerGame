from pathlib import Path
import json
root=Path(__file__).resolve().parent
plan=json.loads((root/'anatomy_plan.json').read_text(encoding='utf-8'))
plan['individual_constraints']=['Two legs with two ivory toes on each front foot, plain heels from rear','Original single spiked pauldron on anatomical LEFT arm, not on torso or right arm','Broad short notched dark sword with gold inner stripe and gold handle in anatomical RIGHT hand','Gold swept mohawk, pointed ears, gray olive skin, dark angular armor, gold belt; no added helmet or cape']
(root/'anatomy_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for direction in ['Up','Down']:
    path=root/'generation'/direction/'prompt.txt'
    if (path.parent/'request.json').exists():raise ValueError('Do not modify paid request')
    text=path.read_text(encoding='utf-8')
    rear=direction=='Up'
    text=text.replace('5. ONE complete anatomical RIGHT arm, shoulder at TOP center; INCLUDE original right-hand weapon held naturally, no second arm or torso','5. ONE complete anatomical RIGHT arm, shoulder at TOP center; plain round gray upper arm, original small wrist armor/glove, gripping the original broad short NOTCHED DARK SWORD with gold inner stripe and gold handle. Arm hangs DOWN and sword angles outward '+('RIGHT' if rear else 'LEFT')+' and slightly UP from hand. No spiked pauldron on this right arm; no floating separate sword; no second arm or torso')
    text=text.replace('6. ONE complete anatomical LEFT arm including its glove/guard if original, shoulder at TOP center; no weapon or torso','6. ONE complete anatomical LEFT arm including the ONE original large dark angular shoulder pauldron with exactly three ivory spikes, gray upper arm and angular wrist guard, closed empty hand. Shoulder root at TOP center, arm hangs DOWN. No weapon or torso. The torso must NOT duplicate this pauldron')
    text=text.replace('7. ONE left leg/foot, root at TOP center, toes down towards the ground','7. ONE short thick left leg/foot, hip root at TOP center. '+('REAR heel-facing gray foot with plain rounded heel, NO visible ivory toe claws or toenails' if rear else 'FRONT-facing foot with the original TWO ivory toe claws at bottom')+'; no boot or invented armor')
    text+='\nDreadnought-specific invariants: torso is dark angular plated chest/back with original broad gold waist belt and short hanging tabs. No arms, pauldrons, head or legs baked into torso. '+('Rear belt has NO large front buckle; dark plates cover back; rear head shows plain gray nape and swept gold mohawk only, no face or ivory teeth. Anatomical right weapon arm appears screen RIGHT, spiked left arm screen LEFT.' if rear else 'Front belt has original large ivory polygon buckle at center. Anatomical right weapon arm appears screen LEFT, spiked left arm screen RIGHT.')+' Keep the original stocky wide muscular proportions and thick dark outlines. All roots opaque and rounded, no hollow cut surfaces. Sword matches original broad short blade, not a long skinny sword, axe, club or spear.\n'
    path.write_text(text,encoding='utf-8')
