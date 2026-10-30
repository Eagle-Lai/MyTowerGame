from session_winterogre import *
import re

owner()
assert not (D/'anatomy_plan.json').exists()
run('prepare_character.py',NAME)
source=(H/'render_source_reference.py').read_text(encoding='utf-8').replace("contact.save(HERE/'source_reference_contact.png')","contact.save(HERE/'WinterOgre'/'reference'/'battle_contact.png')")
sys.argv=[str(H/'render_source_reference.py'),'--battle','--name',NAME]
exec(compile(source,str(H/'render_source_reference.py'),'exec'),{'__file__':str(H/'render_source_reference.py'),'__name__':'__main__'})
identity='Stocky bald GOLDEN-OCHRE ogre with irregular dark ochre skin patches, sharply pointed ears, stern amber eyes with black pupils, broad flat nose and a closed zigzag mouth with several small ivory triangular teeth. No hair, horns, beard, necklace or earrings. Thick round bare belly. Wide brown belt with small gold diamond studs and one large cream square buckle containing a gold diamond; short ragged WHITE/CREAM FUR loincloth. Two thick short bare golden legs ending in rounded bare feet with three small front toe divisions; NO fur boots. Two thick muscular golden arms, BOTH wearing matching enormous brown leather wrist cuffs with gold diamond/square studs and WHITE/CREAM FUR rims; empty closed fists visible below cuff, NO held weapon. No tail, rider or extra limbs. Angry head opens a dark mouth with ivory teeth; dead head has large blank pale round eyes and drooping tan tongue, following original expression.'
plan=read(D/'anatomy_plan.json')
plan.update(identity=identity,source_observations=dict(viewed=['reference/WinterOgre.png','reference/source_prefab_offline.png'],legs=2,arms=2,feet='bare golden feet; no boots; Up smooth heels without front toe lines',weapon='Atlas includes striped crook sprite, but source AND battle Weapon SpriteRenderer m_Enabled=0. Preserve original ArmR/FistR/Weapon hierarchy, disabled renderer and animation scale bindings. Vertical arms have empty fists, no crook.',torso='Front cream square buckle with gold diamond; back plain belt and ivory fur skirt, no front buckle on rear.',head='Bald spotted head; ears assigned only to head. No duplicated ears/head on body. Up plain back of head, no face or inner ear pads.',native_contract='source_contract_20261029.json',lifecycle='BaseEnemy.Init Rebind and ResetForSpawn; receiver normal head reset, OnRecycle alpha/spawn scale/anim speed reset; no shared code edits.'))
write(D/'anatomy_plan.json',plan)
for direction in ['Up','Down']:
    p=D/'generation'/direction/'prompt.txt'
    text=p.read_text(encoding='utf-8')
    text=text.replace('Stocky golden ogre with bald head, pointed ears, cream fur loincloth and boots, huge fur-rimmed spiked wrist guards, open empty fists; original has NO handheld weapon.',identity)
    text+='\nWinterOgre-specific: image 1 striped crook is an UNUSED atlas sprite: both original prefabs disable its renderer. Absolutely NO handheld weapon in either arm. BOTH arm cells are complete shoulder-to-empty-closed-fist arms of the SAME length and thickness, including ONE enormous brown diamond-studded cuff with dense white fur rims; solid shoulder root TOP center, arm hangs DOWN, small empty fist below cuff, no torso. Cell5 anatomical RIGHT arm, cell6 anatomical LEFT arm. Feet are BARE golden feet, no boots or ankle fur. Front-only square belt buckle belongs on Body, ears belong on Head only. No duplicated cuffs on torso. Keep the source ochre rather than green or blue.\n'
    text+=('REAR: plain bald spotted back of head with TWO outer pointed ear backs; NO eyes/nose/mouth/teeth/tongue or inner ear pads in any head cell. Body is rounded spotted shoulder blades and lower back, plain rear belt and white fur skirt; NO belly crease/pectoral outlines/front buckle. Arms show back of hands, anatomical RIGHT arm viewer RIGHT; anatomical LEFT arm viewer LEFT. The leg cell ends with a rounded smooth HEEL; no forward toenail/toe lines on the back.\n' if direction=='Up' else 'FRONT: straight centered axial face, stern amber eyes, wide nose and small ivory triangular lower teeth; angry head opens mouth; dead head round pale blank eyes with tan tongue sticking down, not X marks. Front body has bare belly and original cream square buckle with gold diamond. Front foot shows three small rounded golden toes. Anatomical RIGHT arm viewer LEFT and LEFT arm viewer RIGHT.\n')
    p.write_text(text,encoding='utf-8')
serial={}
for key in ['source','battle']:
    target=next(t for t in read(H/'local_baseline.json')['targets'] if t['name']==NAME)
    path=ROOT/target[key]
    blocks=[{'class_id':int(m[1]),'file_id':int(m[2]),'yaml':m[3]} for m in re.finditer(r'^--- !u!(\d+) &(-?\d+)\s*\n(.*?)(?=^--- !u!|\Z)',path.read_text(encoding='utf-8-sig'),re.M|re.S)]
    serial[key]={'path':target[key],'sha256':sha(path),'all_serialized_objects':blocks}
write(D/'original_serialized_objects_20261029.json',serial,fresh=True)
write(D/'reference_review_20261029.json',dict(observed_at=now(),viewed=plan['source_observations']['viewed'],observation=identity,weapon_observation=plan['source_observations']['weapon'],native_contract='source_contract_20261029.json',source_sha256={p.name:sha(p) for p in (D/'reference').iterdir() if p.is_file()},prompt_sha256={d:sha(D/'generation'/d/'prompt.txt') for d in ['Up','Down']},root_rule_difference='Historical FreedomTower D:/8082 overridden by explicit E:/MyTowerGame/8088 task. No root rule change.',image_workflow='imagegen identity-preservation guidance, explicitly authorized existing AIHub API/Curl workflow.'),fresh=True)
p=read(H/'progress.json');i=next(x for x in p['items'] if x['name']==NAME);assert i['status']=='not_started';i.update(status='reference_prepared',user_approved=False,reference_review_file='WinterOgre/reference_review_20261029.json');p.update(current=NAME,updated_at=now());write(H/'progress.json',p)
stage('reference_prepared_pending_Up_generation','Docs/EnemyDirectionReview/Remaining_20261024/WinterOgre/reference_review_20261029.json')
print(json.dumps(dict(prepared=NAME,parts=plan['parts'],weapon='disabled in both original prefabs; empty fists retained')))
