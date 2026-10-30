from session_current import *

owner();plan=read(HERE/'anatomy_plan.json')
save(HERE/'anatomy_plan_before_source_review_20261029.json',plan)
identity=('Stocky broad-bellied bipedal stitched ogre zombie, muted gray-taupe/olive-brown skin with ochre round patches, pale beige highlights, and large jagged sutures held by dark ochre thornlike ties through small gray-tan metal loops. '
 'One large nearly bald head, small rounded pointed ears, an exposed SMALL tan-beige lobed brain at the TOP of the skull, two huge pale cream-yellow circular eyes with tiny black pupils, long flat upper lip, a few small square ivory teeth, ochre jagged seam on cheek. '
 'Normal face is slack dull stare with closed flat mouth; angry face slanted eyebrows and wide dark open mouth with square teeth; dead face blank pale round eyes and closed slack mouth, NO hanging tongue, X marks or blood. '
 'Heavy rounded torso and belly with pale stitched patches and ochre spots. Short torn cream-beige loincloth hem with ochre patches under belly. No necklace, skull ornaments, belt buckle, armor, tail or hair. '
 'Two muscular thick arms with very wide dark olive-brown wrist cuffs and large pale bare hands. Anatomical RIGHT hand grips ONE golden-brown wooden club with a thick knotted tapered head, ivory conical spikes and wrapped narrow handle. Anatomical LEFT hand is empty. '
 'Two short thick bare legs with ochre spots, a jagged suture and small rounded toes. Thick smooth dark brown outline, broad flat warm cel shading, matching exact original source.')
plan.update(identity=identity,source_review={'observed_at':now(),'viewed':['reference/Zombie.png','reference/source_prefab_offline.png','reference/battle_prefab_offline.png'],
 'head':1,'arms':2,'legs':2,'tails':0,'equipment':['one spiked wooden club in anatomical RIGHT hand','one broad dark cuff on each wrist','torn pale loincloth hem'],
 'absent':['skull necklace','bone trinket jewelry','belt buckle','tail','boots','second weapon'],
 'head_receiver':'Battle has existing HeadRenderer and exact own-atlas Normal/Angry/Dead sprites, no repair needed; source prefab has no runtime receiver.',
 'animation_contract':'source_animation_contract_complete_20261029.json','walk_seconds':0.6666667,'attack_seconds':1.0,'death_seconds':0.5})
(HERE/'anatomy_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for direction in ['Up','Down']:
 d=HERE/'generation'/direction;assert not any((d/f).exists() for f in ['request.json','raw.png','result.json','uncertain_result.json'])
 (d/'prompt_before_source_review_20261029.txt').write_bytes((d/'prompt.txt').read_bytes())
 up=direction=='Up'
 view=('TRUE REAR/BACK view travelling AWAY toward screen UP. Three heads must be IDENTICAL plain back-of-skull views with the small brain on crown and outer backs of two ears. NO eyes, brow, nose, lips, teeth, face, front inner-ear structure or front cheek details on ANY rear head. Rear feet have smooth rounded HEELS, NO front toes, toenails, sole pads or front toe division lines.' if up else
       'TRUE FRONT view travelling TOWARD viewer screen DOWN. Straight centered axial face, two large cream-yellow circular eyes with small black pupils, small rounded ears, small exposed beige brain crown, flat lip and small square teeth. HeadNormal slack closed mouth; HeadAngry brows down and dark wide open mouth; HeadDead blank round pale eyes with no pupils and slack closed mouth. NO tongue or X marks. Front bare foot has small rounded toes.')
 body=('Rounded broad upper back/shoulder blades and lower back, irregular pale stitched patches and ochre spots, torn pale loincloth hem at BOTTOM; NO pectoral outlines, front belly fold or face. Solid neck root TOP CENTER.' if up else
       'Broad barrel chest and heavy rounded belly with the original pale stitched patches, thornlike suture ties and ochre spots; original torn pale loincloth hem BOTTOM. Solid neck root TOP CENTER. NO necklace or belt buckle.')
 prompt=f'''Use case: identity-preserve. Asset type: production 2D game cutout sprite parts sheet.
Image 1 is the actual original Zombie sprite atlas. Image 2 is this exact character assembled from its actual original serialized prefab. Both are reference images for exact identity, palette, thick outlines, equipment and proportions. Never invent skull jewelry from the filename.
Character: {identity}
Requested view: {view} Same elevated orthographic game perspective as source, strictly axial front or rear, not side or three-quarter. No rotation or mirroring of a side sprite as a fake view.
ONE sheet exactly FOUR equal columns by TWO equal rows. Seven detached parts in reading order, eighth cell empty:
1. ONE complete detached NORMAL head only, small exposed brain at crown and exactly TWO ears belong to head. Solid rounded neck at bottom. No torso or club.
2. SAME head size and alignment with ANGRY front expression, or IDENTICAL FACELESS REAR head for rear view.
3. SAME head size and alignment with DEAD front expression, or IDENTICAL FACELESS REAR head for rear view.
4. ONE complete detached TORSO ONLY. {body} No head, brain, ears, arms, cuffs, hands, legs or held weapon on torso.
5. ONE COMPLETE anatomical RIGHT arm from round solid shoulder root at TOP CENTER down to cuff and hand, INCLUDE ONE hand gripping ONE original spiked wooden club naturally. Arm hangs down; club is beside the arm, its knotted spiked head points obliquely outward and UP. Entire club and every spike fit inside cell, weapon never crosses other cells. Exactly one arm, cuff, hand and club, no torso or second fist. {'Back of hand visible; club extends outward to screen RIGHT.' if up else 'Knuckles/front of gripping hand visible; club extends outward to screen LEFT.'}
6. ONE COMPLETE anatomical LEFT arm, matching length and thickness, round solid shoulder root TOP CENTER, same one dark cuff and one EMPTY pale fist at BOTTOM. No weapon, torso or second hand. {'Back of hand visible.' if up else 'Front hand/finger shapes visible.'}
7. ONE short thick LEFT leg, round solid hip root TOP CENTER, pale gray-tan skin/ochre spots and one suture, bare foot BOTTOM. {'Smooth REAR heel, no front toes or toe lines.' if up else 'Front foot with small rounded toe divisions.'} No boots or second leg.
8. EMPTY flat magenta.
Every part centered fully in its cell, 12 percent clear padding. Heads aligned and same scale. All shoulder/hip/neck roots solid opaque rounded shapes, no holes or open tubes. Match when layered into ONE head, TWO arms, TWO legs, ONE right-hand club. Body does not duplicate cuffs/arms/feet. No complete assembled creature in sheet.
Style exact source: muted gray-taupe/olive-brown with ochre spots, pale beige highlights and loincloth, tan brain, dark olive-brown cuffs, golden wooden spiked club; broad flat cel shading and thick smooth dark brown contours. No green/blue neon zombie, red gore, skull necklace, new equipment or realistic texture.
Background EXACT flat RGB #FF00FF immediately outside outlines; all interiors source-colored OPAQUE. NO magenta holes, floor, ground shadow, cast shadow, glow, blur, checkerboard, grid, label, text or watermark. Crisp closed outlines for transparent extraction.
'''
 (d/'prompt.txt').write_text(prompt,encoding='utf-8')
save(HERE/'source_visual_review_20261029.json',{'observed_at':now(),'identity':identity,'viewed':plan['source_review']['viewed'],'findings':plan['source_review'],
 'plan_sha256':sha(HERE/'anatomy_plan.json'),'prompt_sha256':{d:sha(HERE/'generation'/d/'prompt.txt') for d in ['Up','Down']},'user_approved':False,
 'api':'User explicitly specified existing AIHub generate_character.ps1/generate.mjs; preserve resolve and per-process direct proxy environment.'})
print('Zombie own-source plan/prompts ready; existing receiver intact; native Walk 2/3s, Attack 1s.')
