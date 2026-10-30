from pathlib import Path
import json, shutil, sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from session_current import owner,save,sha,now,ROOT
owner()
plan=json.loads((HERE/'anatomy_plan.json').read_text(encoding='utf-8'))
save(HERE/'anatomy_plan_before_source_review_20261029.json',plan)
identity=('Compact low quadruped wolf, dark gray-taupe and olive-brown fur with lighter gray-khaki jagged cheek and throat tufts, sparse round ochre spots. '
 'Large angular canine skull, two tall triangular pointed ears, thick brows, ivory eyes with small black pupils, dark brown nose, cream canine teeth. '
 'One golden ochre leather riding saddle is integrated with the BODY: raised golden rim, darker segmented rectangular seat, three short ivory conical spikes on its REAR rim, '
 'and ONE silver-gray circular X-shaped screw/buckle on the left girth side. No rider. No collar. '
 'Four short sturdy spotted legs with rounded paws. Long broad thick gray-taupe tail curves out from the rump and DOWN to a pointed rightward tuft, lighter gray-khaki inner fur. '
 'No winter-white mane or bib, no head armor, no handheld weapon, no horns or invented equipment.')
plan.update(identity=identity,source_review={'observed_at':now(),'full_atlas':'reference/WolfMounted.png','full_source':'reference/source_prefab_offline.png',
 'findings':'Own complete atlas and serialized source actually viewed. Seven visible creature renderers: head, torso containing saddle/spikes/single side buckle and small cream-gray throat tuft, four short paws, broad curved drooping tail. Source Shadow is a separate renderer and will be suppressed only on this battle prefab.',
 'head_count':1,'legs':4,'tails':1,'equipment':['one gold saddle with segmented seat and three ivory rear-rim spikes, body only','one silver-gray X buckle on left girth side, body only'],
 'head_equipment':[],'rider':False,'source_contract':'source_animation_contract_complete_20261029.json'})
(HERE/'anatomy_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for direction in ['Up','Down']:
 folder=HERE/'generation'/direction
 assert not any((folder/p).exists() for p in ['request.json','raw.png','result.json','uncertain_result.json'])
 (folder/'prompt_before_source_review_20261029.txt').write_bytes((folder/'prompt.txt').read_bytes())
 up=direction=='Up'
 view=('TRUE REAR, moving AWAY toward screen UP. Back of skull and TWO plain outer ear backs only. NO eyes, eyebrows, nose, mouth, teeth, face, muzzle or front inner-ear pads on ANY rear head. '
       'All three rear heads identical. Paws show smooth rounded BACK HEELS, no toes, claws, pads, soles or front toe lines.' if up else
       'TRUE FRONT, moving TOWARD viewer screen DOWN. Centered muzzle below two ivory eyes with small black pupils, matching ochre forehead spots, two pointed ears. '
       'Normal toothy closed snarl, angry open biting jaw, dead rolled pale eyes and hanging tan tongue. All heads aligned and same size. Paws show subtle front toe divisions.')
 body=('Elevated axial BACK torso, narrow solid neck TOP CENTER and broad near rump BOTTOM. Golden saddle seat across upper middle, its REAR raised rim with THREE short ivory spikes near the BOTTOM of the saddle; ONE round silver-gray X buckle on screen LEFT girth side. No chest tuft visible from behind.' if up else
       'Elevated axial FRONT torso, broad far rump TOP and narrower near neck/chest BOTTOM CENTER. Golden saddle across upper back, its rear raised rim with THREE short ivory spikes near TOP, ONE round silver-gray X buckle on screen RIGHT girth side. Small original pale gray-khaki jagged throat tuft at lower neck only, not a broad white bib.')
 prompt=f'''Use case: identity-preserve. Asset type: production 2D game cutout sprite parts sheet.
Image 1 is this character's actual original WolfMounted.png atlas. Image 2 is the entire character rendered from its actual serialized prefab. Both are REFERENCES for exact identity, colors, simple shapes, anatomy, saddle and thick dark brown outlines. Preserve THIS mounted wolf; never use a wolfhound collar or winter-wolf coat.
Character WolfMounfed: {identity}
Requested view: {view} Elevated orthographic game perspective; strictly axial front or rear, no three-quarter head, no rotated/mirrored side sprite.
ONE sheet, exactly FOUR equal columns by TWO equal rows. Seven detached parts in reading order; cell 8 empty:
1. ONE normal detached head only, exactly TWO ears, no torso, saddle, collar or neck equipment. Rounded opaque neck connection.
2. Same head, same alignment and size, angry FRONT expression or IDENTICAL plain rear head for REAR.
3. Same head, same alignment and size, dead FRONT expression or IDENTICAL plain rear head for REAR.
4. {body} Preserve gray-taupe olive-brown spotted fur. Complete low quadruped torso INCLUDING the whole unique saddle and its buckle and spikes. No head, ears, eyes, attached feet, tail or rider.
5. ONE detached short left foreleg, rounded solid shoulder root TOP CENTER, paw at BOTTOM; view-appropriate front toes or smooth rear heel. One ochre round spot on upper leg. No extra leg.
6. ONE detached short left hindleg, rounded solid hip root TOP CENTER, paw BOTTOM; same correct view. No extra leg.
7. ONE full original long broad thick curved drooping tail. Solid narrow ROOT at TOP CENTER; it curves gently outward and DOWN, ending in pointed tuft toward lower RIGHT. Gray-taupe outer fur and lighter khaki-gray inner band, thick smooth outline. No curled-up wolfhound tail or thin bare rat tail.
8. EMPTY magenta background.
Each part centered fully inside its cell with 12 percent clear padding. No complete assembled animal, labels, grid or cell-crossing parts. Interiors and all rounded connections SOLID OPAQUE; no hollow tubes or magenta holes. Saddle/spikes/buckle ONLY on torso, never head or legs. Exactly one head, two ears and four legs when assembled from the parts.
Style exactly matches source: broad simple flat cel-shaded regions, muted gray-taupe/olive-brown and ochre-gold spots/leather, gray-khaki highlights, cream teeth, smooth thick dark brown outlines. No realistic fur, gray winter redesign, white mane, new jewelry or new equipment.
Background exactly flat RGB #FF00FF immediately outside outlines. NO floor, ground shadow, cast shadow, glow, blurry halo, checkerboard, text or watermark. Crisp intact silhouettes for transparency extraction.
'''
 (folder/'prompt.txt').write_text(prompt,encoding='utf-8')
contracts=HERE/'reference/exact_original_animation_contract'
contracts.mkdir()
for p in (ROOT/plan['controller']).parent.iterdir():
 if p.is_file() and (p.suffix in ['.anim','.controller'] or p.name.endswith(('.anim.meta','.controller.meta'))):shutil.copy2(p,contracts/p.name)
save(HERE/'source_visual_review_20261029.json',{'observed_at':now(),'reviewed':['reference/WolfMounted.png','reference/source_prefab_offline.png'],
 'identity':identity,'plan_sha256':sha(HERE/'anatomy_plan.json'),'prompt_sha256':{v:sha(HERE/'generation'/v/'prompt.txt') for v in ['Up','Down']},
 'serialized_contract_files':{p.name:sha(p) for p in contracts.iterdir()},'request_scope':'One initial request per direction, sequential raw review. No paid diagnostic or automatic retries.',
 'transport':'Existing generator, Curl direct TLS, --resolve aihub.dog:443:191.101.132.254; process-only proxy environment restored finally.'})
print('WolfMounfed own-source prompts ready')
