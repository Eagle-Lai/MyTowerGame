from session_current import *

owner();d=HERE/'generation/Up';out=d/'revision_01';assert not out.exists();out.mkdir()
assert read(d/'result.json')['status']==200
save(HERE/'generation_Up_initial_review_20261029.json',{'observed_at':now(),'raw_sha256':sha(d/'raw.png'),'viewed':'generation/Up/raw.png','accepted':False,
 'finding':'All three returned head cells are FRONTAL faces despite rear request. Body back, arms/club and smooth heel are usable references; never install these front heads as Up.',
 'action':'One necessary art correction via existing revision input branch; not a network retry; preserve successful initial raw and result.'})
prompt='''Use case: precise-object-edit / identity-preserve. Production game spritesheet correction.
Image 1 original atlas and image 2 source full character are IDENTITY references. Image 3 is the FAILED rear sheet to EDIT. Its THREE FACE HEADS are WRONG for a rear view.
CHANGE ONLY HEAD CELLS 1, 2, 3 (top row first three cells). Replace all three with IDENTICAL TRUE REAR views of the back of this same zombie skull. The camera is BEHIND the zombie. We see a plain ROUND BALD OCCIPUT, beige gray-taupe skin with one ochre patch, TWO tiny outer EAR BACKS at sides, SMALL exposed tan brain lobes at crown, solid rounded neck at bottom. No new hair or gear.
ABSOLUTELY ZERO FACE on any of these three head sprites: NO eye, eyeball, eye socket, eyebrows, nose, nose hole, lips, mouth, teeth, muzzle, tongue, inner ear cavity or front cheek seam. The whole central area is plain convex scalp, simple source cel shading. A true back of head has NO facial expression. Normal/angry/dead rear heads must be IDENTICAL FACELESS rear skulls, same silhouette and scale. Do NOT merely erase pupils from a frontal face. Redraw genuine back-of-skull shape with no front jaw or lip protrusion.
KEEP all other parts of image 3 exactly as they are: top-row 4 rear body with sutures and cream loincloth, bottom-row right arm holding one spiked club, left empty arm and smooth-heel leg. Their palette, outline, dimensions and equipment stay consistent. No duplicated head, ears, fists, weapon or cuffs on torso.
One landscape sheet FOUR columns TWO rows. Heads cells1/2/3, back body4, right arm WITH club5, empty left arm6, rear leg7, magenta8. All parts detached, 12 percent padding, closed solid opaque roots. No floor or shadows. Exact flat RGB #FF00FF outside smooth thick dark brown outlines. No text, grid, watermark, photorealism or new ornaments.
'''
(out/'prompt.txt').write_text(prompt,encoding='utf-8')
save(out/'art_correction_intent.json',{'observed_at':now(),'owner_thread_id':owner()['owner_thread_id'],'dispatch_token':owner()['dispatch_token'],'character':NAME,'direction':'Up','revision':'revision_01','max_requests':1,
 'source_raw_sha256':sha(d/'raw.png'),'source_result_sha256':sha(d/'result.json'),'reason':'Three original Up heads are frontal, must be replaced with genuine rear skulls. Existing success preserved; this is art correction, no counter reset.'})
print('One Up rear-head correction prepared')
