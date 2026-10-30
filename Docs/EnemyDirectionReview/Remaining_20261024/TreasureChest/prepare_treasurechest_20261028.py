from session_treasurechest import *
owner();assert inventory()==read(D/'incremental_before_20261028.json')['files']
assert not (D/'anatomy_plan.json').exists()
subprocess.run([sys.executable,str(H/'prepare_character.py'),NAME],check=True)
source=(H/'render_source_reference.py').read_text(encoding='utf-8').replace("contact.save(HERE/'source_reference_contact.png')","contact.save(HERE/'TreasureChest'/'reference'/'battle_contact.png')")
sys.argv=[str(H/'render_source_reference.py'),'--battle','--name',NAME]
exec(compile(source,str(H/'render_source_reference.py'),'exec'),{'__file__':str(H/'render_source_reference.py'),'__name__':'__main__'})
plan=read(D/'anatomy_plan.json')
identity='Golden ochre wooden treasure chest, rounded arched lid, two broad dull gray iron bands, thick dark outlines and simple broad cel shading. Square centered gray keyhole lock on FRONT only. Empty golden wooden cavity when opened. No face, eyes, mouth, teeth, tongue, limbs or creature anatomy.'
plan.update(identity=identity,source_observations=dict(original_visible_art='one whole closed chest SpriteRenderer Normal, one whole opened chest SpriteRenderer Broken; no split lid/head',receiver='HeadRenderer null; HeadSprites empty',clips='Idle1s no curves/events; Death1/3s toggles Normal off/Broken on and moves/wobbles Body; no source events',state_aware_rig='HeadNormal/HeadAngry are whole closed chest, HeadDead is whole open chest. Body slice intentionally transparent compatibility carrier. Generic Head names are state slots, not animal anatomy.',actual_views=['reference/source_prefab_offline.png','reference/TreasureChest.png']))
write(D/'anatomy_plan.json',plan)
for direction in ['Up','Down']:
    view=('TRUE REAR view of chest: the front lock faces AWAY from camera. Show back of box, two iron bands and small hinge fixtures. Absolutely NO front keyhole, front clasp or front lock visible. Symmetric axial rear, not three quarter. Open state shows rear exterior of raised hinged lid and consistent box rear.' if direction=='Up' else 'TRUE FRONT view of chest: the square keyhole lock is centered on front. Symmetric axial front, not three quarter. Open state shows interior underside of raised curved lid and empty dark golden box cavity, exactly like original opened sprite, no treasure or teeth.')
    prompt=f'''Use case: identity preservation. Production 2D game sprite STATE sheet for TreasureChest.
Image1: actual original atlas, containing CLOSED and OPEN whole chest. Image2: actual complete closed original prefab. Match these exact warm ochre/golden wood colors, proportions, gray iron bands, outlines and broad simple cel shading. This is an inanimate container, not a mimic creature.
Identity: {identity}
Requested view: {view} Same slightly elevated orthographic game perspective as original. Create a real new front/rear view; do not mirror or rotate side atlas pixels.
One sheet with exactly 4 equal columns and 2 equal rows. Only top-row cells1,2,3 contain art. Each whole chest centered and fully inside its own cell with 12 percent padding. Cell4 and the entire bottom row completely empty magenta.
Cell1: COMPLETE WHOLE CLOSED chest, including its rounded lid and lower box. Solid opaque complete object; no detached parts.
Cell2: EXACT SAME COMPLETE CLOSED chest as cell1, same scale/alignment/shape. This is a compatibility attack-state copy; NO face, mouth or invented attack anatomy.
Cell3: COMPLETE WHOLE OPEN chest, same box base dimensions and ground baseline as cell1, lid hinged upward as original second sprite. Clear open lid/box relation; empty cavity; gray iron bands continuous on lid and base. No detached lid floating away. No cracks, broken planks or changed materials: original Broken state means simply opened.
No separate lid cutouts, no limbs. Whole-object states intentionally follow original Normal/Broken sprite structure. Keep a consistent closed/open width, box bottom and pivot; opened lid may make the total sprite taller. Outer rear surface is plain wood and bands, never a face. NO eyes, teeth, tongue, feet, horns or treasure.
Style strictly original: thick smooth very dark outline, flat broad golden/ochre cel shaded regions with sparse dark wood grain. Avoid realistic texture, orange recolor, luminous gold and bevel-heavy metal.
Background exactly flat RGB #FF00FF magenta immediately outside outlines. All wood/metal interiors fully opaque, no magenta holes. No ground shadow, floor, glow, halo, checkerboard, text, labels, grid or watermark.
'''
    (D/'generation'/direction/'prompt.txt').write_text(prompt,encoding='utf-8')
write(D/'reference_review_20261028.json',dict(observed_at=now(),identity=identity,source_observations=plan['source_observations'],prompt_sha256={d:sha(D/'generation'/d/'prompt.txt') for d in ['Up','Down']},compatibility_issue='Shared builder required Ready/Walk/Attack but Container only Idle/Death; shared harness assumes head refs except MimicChest. Resolve with target-only Editor adapter/harness, shared C# unchanged.',source_contract='source_animation_contracts_20261028.json',user_art_approved=False))
p=read(H/'progress.json');i=next(x for x in p['items'] if x['name']==NAME);assert i['status']=='not_started';i.update(status='reference_prepared',user_approved=False,reference_review_file='TreasureChest/reference_review_20261028.json');p.update(current=NAME,updated_at=now());write(H/'progress.json',p)
c=owner();c.update(current_stage='reference_prepared_pending_Up_generation',last_stage_evidence='Docs/EnemyDirectionReview/Remaining_20261024/TreasureChest/reference_review_20261028.json',updated_at=now());write(H/'conversation_chain.json',c)
print(json.dumps(dict(prepared=NAME,states='whole closed / closed attack / open',body='transparent compatibility carrier')))
