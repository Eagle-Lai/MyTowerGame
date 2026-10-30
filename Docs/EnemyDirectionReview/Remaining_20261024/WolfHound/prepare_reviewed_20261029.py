from pathlib import Path
import sys,json,shutil
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from session_current import owner,save,sha,now,ROOT
owner()
plan=json.loads((HERE/'anatomy_plan.json').read_text(encoding='utf-8'))
save(HERE/'anatomy_plan_before_source_review_20261029.json',plan)
identity=('Stocky low quadruped wolfhound with dark olive-brown coat, broad lighter khaki-brown jagged fur patches and warm ochre round spots. '
 'Large angular canine head, two upright triangular pointed ears with ochre inner pads visible FRONT ONLY, thick angular brows, large ivory eyes with tiny black pupils, '
 'broad dark brown nose with muted tan highlight, cream fangs and mouth. The original has a thick ochre-gold SPIKED COLLAR behind/around the base of the head, with short ivory triangular spikes. '
 'One collar only: keep it entirely with the HEAD piece, never repeat it on the torso. Four short sturdy brown legs with rounded dog paws. '
 'Short-to-medium thick upswept curved shaggy tail, pointed jagged tuft and lighter khaki inner fur; NOT a long thin or drooping tail. '
 'No white chest bib, gray winter coat, saddle, rider, helmet, horn or new equipment.')
plan.update(identity=identity,source_review={'observed_at':now(),'full_atlas':'reference/WolfHound.png','full_source':'reference/source_prefab_offline.png',
 'findings':'Full own atlas and full serialized source viewed. Stocky khaki/olive-brown spotted wolfhound, pointed ears, ivory small-pupil eyes and fangs; original gold collar with ivory spikes belongs to head slice. Seven non-shadow renderers: head, torso, four short paws, upswept shaggy tail. No separate chest bib.',
 'head_count':1,'legs':4,'tails':1,'equipment':['one ochre-gold collar with ivory spikes, assigned to head only'],
 'anchors':['Body/AnchorBody','Body/AnchorWeapon','Body/AnchorStatus'],'source_contract':'source_animation_contract_complete_20261029.json'})
(HERE/'anatomy_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for direction in ['Up','Down']:
 folder=HERE/'generation'/direction
 assert not any((folder/p).exists() for p in ['request.json','raw.png','result.json','uncertain_result.json'])
 (folder/'prompt_before_source_review_20261029.txt').write_bytes((folder/'prompt.txt').read_bytes())
 up=direction=='Up'
 view=('TRUE REAR/BACK, moving away toward screen UP. Plain shaggy back of skull and two outer ear backs ONLY. Absolutely NO eyes, brows, nose, mouth, fangs, muzzle, front ear pads or chest bib. '
       'Three head cells must use the SAME rear silhouette with exactly two ears and the single original spiked collar around the neck base. Paws show smooth rounded BACK HEELS with NO toe lines, claws, soles or paw pads.' if up else
       'TRUE FRONT, moving toward viewer screen DOWN. Symmetrical centered broad muzzle below two ivory eyes with small black pupils; original ochre spots and two pointed ears. '
       'Normal closed snarl with cream fangs; angry open jaw with fangs; dead pale rolled eyes and hanging tan tongue. Same ears/skull/collar size and alignment. Front-facing paws with simple subtle toe divisions.')
 body=('Detached complete elevated axial BACK torso, narrow solid neck TOP CENTER, broader rounded rump BOTTOM. Broad flat khaki-brown jagged upper fur over dark olive-brown flanks, sparse ochre round spots.' if up else
       'Detached complete elevated axial FRONT-view quadruped torso, broad far rump TOP, narrower near neck/chest BOTTOM CENTER; head will overlap below torso. Broad flat khaki-brown jagged fur over dark olive-brown flanks, sparse ochre spots.')
 prompt=f'''Use case: identity-preserve. Asset type: production 2D cutout game sprite parts sheet.
Image 1 is WolfHound's actual original atlas. Image 2 is the entire WolfHound rendered from its actual serialized prefab. Both are reference images for exact identity, palette, outline, materials and compact proportions.
Character: {identity}
Requested view: {view} Elevated orthographic game perspective, strictly axial front or rear; no three-quarter head, no side sprite rotated or mirrored.
ONE sheet, exactly FOUR equal columns by TWO equal rows. Seven separate parts in reading order, cell 8 empty:
1. ONE detached normal head, exactly two ears and ONE original gold spiked collar at its neck base. Collar and head must stay in this cell. Solid opaque connection, no torso.
2. Same detached head/collar, same alignment and size, angry FRONT expression or identical plain rear head for REAR.
3. Same detached head/collar, same alignment and size, dead FRONT expression or identical plain rear head for REAR.
4. {body} NO head, ears, face, collar, spikes, attached feet or tail. Low stocky dog anatomy, not upright human torso.
5. ONE detached short left foreleg, rounded shoulder root TOP CENTER, paw BOTTOM, appropriate FRONT toes or smooth REAR heel. No extra leg.
6. ONE detached short left hindleg, rounded hip root TOP CENTER, paw BOTTOM, appropriate FRONT toes or smooth REAR heel. No extra leg.
7. ONE full original thick shaggy UPSWEPT curved tail with dark olive-brown outside and khaki inner fur, narrow solid ROOT at BOTTOM CENTER and pointed tuft curves UP and to RIGHT. No extra tail, no long drooping tail.
8. Empty magenta background.
Each part entirely inside its cell with 12 percent clear padding. No assembled creature, duplicate organs, labels, grid or cell-crossing parts. Connections must be solid opaque shapes, never hollow tubes or magenta holes. Keep the sole collar on each head, no collar or spikes on torso/legs/tail.
Exact source broad simple flat cel-shaded color regions and smooth thick dark brown outlines; preserve spotted khaki/olive-brown identity, no gray winter fur or white chest patch, no realistic fur.
Background flat RGB #FF00FF immediately outside each outline. NO floor or ground shadow, cast shadow, glow, blurred halo, checkerboard, text or watermark. Crisp intact silhouettes for transparency extraction.
'''
 (folder/'prompt.txt').write_text(prompt,encoding='utf-8')
contracts=HERE/'reference'/'exact_original_animation_contract'
contracts.mkdir()
source=ROOT/plan['controller']
for p in source.parent.iterdir():
 if p.is_file() and (p.suffix in ['.anim','.controller'] or p.name.endswith(('.anim.meta','.controller.meta'))):shutil.copy2(p,contracts/p.name)
save(HERE/'source_visual_review_20261029.json',{'observed_at':now(),'reviewed':['reference/WolfHound.png','reference/source_prefab_offline.png'],
 'identity':identity,'plan_sha256':sha(HERE/'anatomy_plan.json'),'prompt_sha256':{v:sha(HERE/'generation'/v/'prompt.txt') for v in ['Up','Down']},
 'serialized_contract_files':{p.name:sha(p) for p in contracts.iterdir()},
 'request_scope':'One initial request per direction, sequential raw review. No paid diagnostic or automatic retries.',
 'transport':'Existing generate_character.ps1/generate.mjs Curl direct TLS; user --resolve aihub.dog:443:191.101.132.254. Process-only NO_PROXY=aihub.dog, temporarily cleared proxy variables, restored finally.'})
print('WolfHound own-source prompts ready')
