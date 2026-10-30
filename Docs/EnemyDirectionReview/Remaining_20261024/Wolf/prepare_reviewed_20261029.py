from pathlib import Path
import sys,json
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from session_current import owner,save,sha,now
owner()
plan=json.loads((HERE/'anatomy_plan.json').read_text(encoding='utf-8'))
save(HERE/'anatomy_plan_before_source_review_20261029.json',plan)
identity=('Compact shaggy gray-brown and olive-brown wolf, warm ochre round spots on forehead, cheeks, shoulders, flank and tail. '
          'Slate-gray face and back fur highlights over darker olive-brown base, jagged cheek and back fur, two large pointed ears with tan inner pads on FRONT ONLY. '
          'Large ivory-white eyes with small black pupils and white highlights, thick dark brown angular brows, broad dark brown nose with tan highlight, '
          'cream mouth and prominent cream fangs. Small light gray/cream chest fur tuft ONLY under the front neck. '
          'Four short sturdy canine legs with rounded paws and subtle toe lines, long broad crescent-curved gray/brown bushy tail with an ochre patch. '
          'No collar, saddle, armor, horns, rider, separate dorsal spikes, white winter coat or invented equipment.')
plan.update(identity=identity,source_review={'observed_at':now(),'full_atlas':'reference/Wolf.png','full_source':'reference/source_prefab_offline.png',
    'findings':'Own full atlas and serialized complete source viewed. Gray/olive brown broad color blocks and ochre spots; ivory eyes and fangs, two tall ears; lighter chest tuft; seven visible non-shadow renderers, one head, torso, four short legs, broad curved tail.',
    'head_count':1,'legs':4,'tails':1,'equipment':[],'anchors':['Body/AnchorBody','Body/AnchorWeapon','Body/AnchorStatus'],
    'source_contract':'source_animation_contract_complete_20261029.json'})
(HERE/'anatomy_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for direction in ['Up','Down']:
    folder=HERE/'generation'/direction
    assert not any((folder/p).exists() for p in ['request.json','raw.png','result.json','uncertain_result.json'])
    (folder/'prompt_before_source_review_20261029.txt').write_bytes((folder/'prompt.txt').read_bytes())
    up=direction=='Up'
    view=('TRUE REAR view moving away toward screen UP. Plain shaggy back of head and outer ear backs ONLY: absolutely NO eyes, brows, nose, muzzle, mouth, fangs, inner-ear pads or front chest bib. '
          'All three head cells have the SAME single rear silhouette with exactly two ears. Feet are plain smooth rounded rear heels with NO toe lines, claws, paw pads or soles.' if up else
          'TRUE FRONT view moving toward viewer screen DOWN. Centered broad muzzle and dark brown nose, two ivory-white eyes with small black pupils, original angular brows and ochre forehead/cheek spots; two pointed ears. '
          'Normal head has closed snarl, angry head opens jaws showing cream fangs, dead head has rolled pale eyes and hanging ochre tongue. All states same ear/skull size and alignment. Paws show subtle forward toe divisions.')
    body=('Detached complete elevated axial canine BACK torso: narrow neck at TOP CENTER, wider rounded rump BOTTOM, jagged slate-gray upper fur over dark olive-brown flanks and sparse ochre circles. '
          'No head, ears, face, chest bib, attached legs or tail. Solid narrow neck attachment.' if up else
          'Detached complete elevated axial canine torso: broad far rump TOP, narrower near neck/chest BOTTOM CENTER; dark olive-brown with slate-gray flank/back fur and sparse ochre circles. '
          'Small original light gray/cream chest tuft at BOTTOM only. NO head, ears, eye-like motifs, attached legs or tail. Low compact quadruped, not upright human torso.')
    prompt=f'''Use case: identity-preserve. Asset type: production 2D cutout game sprite sheet.
Image 1 is Wolf's actual original atlas. Image 2 is the full serialized Wolf source prefab rendered offline. Both are references for exact character identity, color regions, outline weight, compact proportions and simple cel shading.
Character: {identity}
Requested view: {view} Strict axial front/rear elevated orthographic game perspective; no three-quarter, side profile, side-sprite rotation or mirror shortcut.
ONE sheet exactly 4 equal columns by 2 equal rows, seven detached parts in reading order, eighth cell EMPTY:
1. One normal head only, exactly two ears; opaque rounded neck root, no torso.
2. Same head same size/alignment, angry FRONT expression; identical plain rear silhouette for REAR.
3. Same head same size/alignment, dead FRONT expression; identical plain rear silhouette for REAR.
4. {body}
5. ONE short detached left foreleg, opaque rounded shoulder root at TOP CENTER, matching gray/brown fur, view-specific single paw BOTTOM. No other limb or torso.
6. ONE short detached left hindleg, opaque rounded hip root at TOP CENTER, matching gray/brown coat, view-specific single paw BOTTOM. No other limb or torso.
7. ONE full original long broad gray/brown crescent-curved bushy tail with ochre patch, opaque narrow ROOT at UPPER LEFT, curves DOWN and toward RIGHT to its pointed tip. Continuous thick dark outline, one tail only.
8. Empty magenta background.
Each part must remain inside its own equal cell with 12 percent empty padding. No assembled animal, grid, labels, extra head/ear shapes on torso or duplicate organs. Solid opaque roots, no hollow tubes or magenta interior holes.
Exact source flat cartoon palette and broad cel shading, dark smooth outline; no realistic fur or new markings/equipment. Keep gray/olive brown coat and cream mouth/eyes, not white winter fur.
Background flat RGB #FF00FF immediately outside every part. No floor, ground shadow, cast shadow, glow, blurry halo, checkerboard, text or watermark. Crisp intact outlines for transparency extraction.
'''
    (folder/'prompt.txt').write_text(prompt,encoding='utf-8')
save(HERE/'source_visual_review_20261029.json',{'observed_at':now(),'reviewed':['reference/Wolf.png','reference/source_prefab_offline.png'],
    'identity':identity,'plan_sha256':sha(HERE/'anatomy_plan.json'),'prompt_sha256':{v:sha(HERE/'generation'/v/'prompt.txt') for v in ['Up','Down']},
    'request_scope':'One initial request per direction; sequential raw review, no paid diagnostic or automatic retry.',
    'transport':'Existing Curl CLI direct TLS aihub.dog with user --resolve 191.101.132.254; process-only NO_PROXY and cleared proxy variables, finally restored.'})
print('Wolf own-source prompts ready')
