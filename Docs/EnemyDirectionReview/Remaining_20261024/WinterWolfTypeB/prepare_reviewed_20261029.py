from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from session_current import owner,save,sha,now
owner()
plan_path=HERE/'anatomy_plan.json'
plan=json.loads(plan_path.read_text(encoding='utf-8'))
save(HERE/'anatomy_plan_before_source_review_20261029.json',plan)
identity=('Cream-white and warm pale taupe shaggy wolf, scattered flat round ochre spots on forehead, cheek, flank and tail base; '
          'two tall pointed cream ears with dark taupe outer edges and ochre inner pads on FRONT ONLY; large ivory-white eyes with tiny dark pupils, '
          'broad cream muzzle with brown ochre nose and small ivory fangs; small brown chin tuft and larger brown throat/chest fur bib; '
          'four short cream canine paws, NOT hooves; full long white bushy downward-curving tail with ochre basal spot and taupe underside. '
          'No collar, saddle, armor, dorsal spikes, horns, rider, blue recolor or black fur banding.')
plan.update(identity=identity,source_review={'observed_at':now(),'full_atlas':'reference/WinterWolfTypeB.png','full_source':'reference/source_prefab_offline.png',
    'findings':'White/taupe base and ochre spots; ivory-white eyes rather than generic amber; original brown ventral bib and chin tuft; seven visible non-shadow renderers: head, torso, four legs, tail.',
    'head_count':1,'legs':4,'tails':1,'equipment':[],'anchors':['Body/AnchorBody','Body/AnchorWeapon','Body/AnchorStatus'],
    'source_contract':'source_animation_contract_complete_20261029.json'})
plan_path.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for direction in ['Up','Down']:
    folder=HERE/'generation'/direction
    assert not any((folder/p).exists() for p in ['request.json','raw.png','result.json','uncertain_result.json'])
    (folder/'prompt_before_source_review_20261029.txt').write_bytes((folder/'prompt.txt').read_bytes())
    up=direction=='Up'
    view=('TRUE REAR view travelling AWAY toward screen UP. Show backs of ears and back of head only. NO eyes, muzzle, nose, mouth, teeth, inner-ear pads or chin beard on rear head. '
          'All three rear head pieces are the SAME plain single rear silhouette with exactly TWO ears. Feet show plain smooth rounded rear heels, NO front toe lines, claws, paw pads or soles.' if up else
          'TRUE FRONT view travelling TOWARD viewer, screen DOWN. Show centered symmetric muzzle, two ivory-white eyes with tiny dark pupils, ochre forehead spots, two pointed ears, small brown chin tuft. '
          'Front paws have three subtle front toe divisions; no hoof clefts. Brown throat/chest bib appears at the near neck, never on the back.')
    body=('Complete elevated axial quadruped BACK torso only, narrow neck attachment at TOP, broad rump at BOTTOM, cream-white jagged fur outline and pale taupe cel shading with sparse ochre circles. '
          'Absolutely NO ears, head, face, eyes, beard, attached legs, tail or brown ventral chest bib.' if up else
          'Complete elevated axial quadruped torso only, broad far rump at TOP and narrow near chest at BOTTOM. Original white/taupe shaggy flanks with ochre spots, original brown chest bib at BOTTOM center. '
          'No head, face, ears, attached feet or tail. Wide low canine torso, not upright human chest.')
    prompt=f'''Use case: identity-preserve. Asset type: production 2D cutout game sprite sheet.
Image 1 is WinterWolfTypeB's actual original atlas. Image 2 is its complete serialized source prefab. Both are reference images; preserve their identity, color blocks, dark outline weight, compact proportions and simple cel shading.
Character: {identity}
Requested view: {view} Elevated orthographic game perspective, strictly axial, no three-quarter or side profile.
ONE sheet with exactly 4 equal columns and 2 equal rows, seven detached parts in reading order, eighth cell EMPTY:
1. One normal head only, with exactly two ears and rounded opaque neck root; no torso.
2. Same head same size/alignment, angry expression for FRONT only; plain identical rear head for REAR.
3. Same head same size/alignment, dead expression for FRONT only; plain identical rear head for REAR.
4. {body}
5. ONE short detached left foreleg, rounded opaque shoulder at TOP CENTER, cream/taupe coat, correct view-specific paw at BOTTOM. No second leg or body.
6. ONE short detached left hindleg, rounded opaque hip at TOP CENTER, single ochre upper-leg patch, cream/taupe coat, correct view-specific paw at BOTTOM. No second leg or body.
7. ONE complete original long WHITE bushy tail, ochre oval near root and taupe underside; rounded opaque ROOT at TOP CENTER, curves DOWN, continuous outline, no extra tuft or limb.
8. Empty magenta background.
Each part stays inside its own equal cell with at least 12 percent empty padding. NO extra heads or ears in torso cell. Do not draw a complete animal in any cell. Connection roots solid opaque, never open hollow tubes. All internal colors opaque, no magenta interior holes.
Style exactly original thick smooth dark brown outline and broad white/taupe/ochre flat cartoon shading. No gradients, realistic fur texture or new anatomy.
Background exactly flat RGB #FF00FF immediately outside parts. NO floor, ground shadow, cast shadow, soft glow, blurry halo, grid, labels, checkerboard, text, watermark. Crisp intact outlines suitable for true transparency.
'''
    (folder/'prompt.txt').write_text(prompt,encoding='utf-8')
save(HERE/'source_visual_review_20261029.json',{'observed_at':now(),'reviewed':['reference/WinterWolfTypeB.png','reference/source_prefab_offline.png'],
    'identity':identity,'plan_sha256':sha(plan_path),'prompt_sha256':{v:sha(HERE/'generation'/v/'prompt.txt') for v in ['Up','Down']},
    'request_scope':'One initial request per direction, sequential review; no new paid diagnostic, no automatic retry.',
    'transport':'Existing Curl CLI, direct TLS aihub.dog pinned 191.101.132.254, process-only NO_PROXY and cleared proxy variables; no system modification.'})
print('Source-reviewed WinterWolfTypeB prompts ready.')
