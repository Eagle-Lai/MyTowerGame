"""Single-character, inspected source-specific directions. Docs only."""
from pathlib import Path
import json, sys, runpy
from checkpoint_20261029 import D,H,ROOT,NAME,OWNER,TOKEN,read,write,sha,now,owner
owner()
plan=read(D/'anatomy_plan.json')
plan.update(identity='Golden ochre WildRooster, cream elongated face/neck and cream wing roots, four-lobed orange-gold comb, angular golden hooked beak and two-lobed golden wattle, rounded ochre torso with darker patches and three upturned golden tail feathers integrated in Body, two golden clawed legs. No separate tail renderer in original.',
    original_renderers=['Body','Head','Wing','LegL','LegR'],
    original_tail='Integral original Body artwork, not a separately bound Tail. Compatibility Tail slices are transparent and Tail nodes are removed.',
    original_reviewed=True,reviewed_at=now())
write(D/'anatomy_plan.json',plan)
for direction in ['Up','Down']:
    p=D/'generation'/direction/'prompt.txt';assert not (p.parent/'request.json').exists()
    rear=direction=='Up'
    view=('Strict REAR/BACK view travelling AWAY toward screen UP. Only the cream back of the long head and outer comb are visible: absolutely NO eyes, face, beak, nostrils, mouth, wattle or cheek expression.' if rear else 'Strict FRONT view travelling TOWARD viewer, screen DOWN. Symmetric cream face, two big cream eyes, centered angular gold hooked beak and two-lobed golden wattle, tall orange-gold comb. Never a side or three-quarter view.')
    heads=('The same plain rear head in all three cells, same silhouette, with tall 4-lobed original golden comb and cream nape, NO face. Solid cream neck root at bottom.' if rear else 'The same frontal head size and alignment in all three cells: normal big-eyed face; angry lowered brows for attack; pale blank/dead eyes for death. Each includes its own comb, cream face/neck, gold beak and wattle. Solid cream neck root at bottom.')
    feet=('Show the BACK of the leg: rounded ochre thigh at TOP CENTER, narrow golden shank descending to a heel viewed from behind. Three forward toes point AWAY/up and are hidden or strongly foreshortened; only one short rear hallux can point down/toward viewer. NO three front-facing talons at the bottom.' if rear else 'Rounded ochre thigh root at TOP CENTER, narrow golden shank, three forward clawed toes splayed down/toward viewer, one small rear hallux. Clear sole support and no extra legs.')
    prompt=f'''Use case: identity-preserve. Asset type: production cutout sprite parts sheet for WildRooster only.
Image 1: current original sprite atlas, identity/color/anatomy reference. Image 2: complete original serialized character reference, never an edit target.
Preserve the original warm golden ochre feathers, cream head and wing roots, tall four-lobed orange-gold comb, dark brown thick smooth outline, broad simple cel shades. The original Body includes THREE upturned gold tail feathers. Its cream wing root and gold outer feathers are distinct from the Body. Exactly TWO legs and TWO wings when assembled. No red, no equipment, no horns.
Requested view: {view} Elevated orthographic 2D game angle; generate the real new axial view, never rotate/flip/stretch the original side image.
Exactly FOUR equal columns by TWO equal rows on a 1536x1024 sheet. All pieces stay within cell boundaries with 12 percent padding, reading order:
1. HeadNormal only.
2. HeadAngry only.
3. HeadDead only.
Head instructions for cells 1-3: {heads}
4. ONE rounded pear-shaped golden torso/back and rump only. NO head, comb, neck, face, eyes, beak, wattle, legs or wings. Include ONLY its original three short upward-pointing golden tail feathers, fused at their root with the rear of this Body; do NOT repeat tail in any other cell. {'Broad golden rear rump with the small integral tail feathers rising from its lower central rump; no face on torso.' if rear else 'Golden front chest with small cream chest collar at TOP only, gold belly below; original small upturned tail tips can peek symmetrically behind the upper rump, never a huge fan.'}
5. ONE LEFT folded feather wing. Rounded white/cream shoulder patch at TOP RIGHT with ochre spot, three golden flight feathers fan LEFT/DOWN. Solid opaque shoulder root; no head, tail or body.
6. ONE LEFT leg, detached, view-correct anatomy. {feet}
7. EMPTY, flat magenta. There is NO separately bound original Tail; its actual feathers are in cell 4.
8. EMPTY, flat magenta.
Keep the three heads matched in size and placement. Cell 4 must fit entirely within its cell and exclude ALL head/neck elements. All connections are solid opaque shapes, not hollow cut tubes. Each part should assemble into one bird, with short attached wing roots and thigh roots tucked into lower torso. No complete bird elsewhere. No labels or grid lines.
Background exactly flat RGB #FF00FF immediately outside outlines. Interiors opaque source colors, no pink holes. NO floor, ground shadow, cast shadow, halo, blur, checkerboard, vignette, text or watermark. Crisp dark intact outlines suitable for actual alpha extraction.
'''
    p.write_text(prompt,encoding='utf-8')
    write(p.parent/'generation_intent.json',{'at':now(),'owner_thread_id':OWNER,'dispatch_token':TOKEN,'character':NAME,'direction':direction,'revision':'initial','max_requests':1,'endpoint':'https://aihub.dog/v1/images/edits','model':'gpt-image-2','quality':'medium','size':'1536x1024','n':1,'prompt_sha256':sha(p),'original_inputs':{q.name:sha(q) for q in [D/'reference/WildRooster.png',D/'reference/source_prefab_offline.png']},'prior_requests':[],'billing_note':'Usage is not an actual bill; no retry while in flight or outcome unknown.'})
write(D/'source_visual_review_20261029.json',{'at':now(),'reviewed_files':{p.name:sha(p) for p in [D/'reference/WildRooster.png',D/'reference/source_prefab_offline.png',D/'reference/source_structure.json',D/'source_inspection_20261029.json']},'observations':'实际查看完整原atlas与离线原prefab：金色四瓣冠，奶油长脸颈，金色钩喙与双瓣垂肉，白根金羽翅，圆金躯干的三枚上翘尾羽为Body一体，两根金色爪足；仅5个角色SpriteRenderer。新正背保留身份，不新增独立尾或山羊部件。Up用纯奶油后脑、后跟与单后趾，不画脸/三枚朝前爪。','native_animation':'Ready/Walk/Attack 0.5s loop; Death 0.333333343s nonloop. Attack SetHead 0 at0, 1 at1/6, Event Attack at1/3, 0 at5/12. Death SetHead2 at0. Original 72 float bindings across four unique clips and zero PPtr bindings stored in source_inspection; preserved by Builder Verify.','failed_readonly_probe':'Initial JsonUtility rejected engine types; replaced with EditorJsonUtility and primitive arrays; no Assets C# edited.'})
# Render the current battle reference without overwriting the shared contact board.
sys.argv=[str(H/'render_source_reference.py'),'--name',NAME,'--battle']
code=(H/'render_source_reference.py').read_text(encoding='utf-8').replace("contact.save(HERE/'source_reference_contact.png')", "contact.save(HERE/'WildRooster/reference/battle_reference_contact.png')")
exec(compile(code,str(H/'render_source_reference.py'),'exec'),{'__file__':str(H/'render_source_reference.py'),'__name__':'__main__'})
p=read(H/'progress.json');i=next(i for i in p['items'] if i['name']==NAME);i.update(status='reference_prepared',stage='source_reviewed_prompts_ready');p.update(current=NAME,updated_at=now());write(H/'progress.json',p)
print('Source-specific bird anatomy and two initial single-request intents ready')
