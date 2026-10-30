from pathlib import Path
import json, hashlib
here=Path(__file__).resolve().parent
findings={
 'Up':'Rear heels corrected and body has no hat. Rejected: both ears have earrings although original has only one.',
 'Down':'Body hat corrected. Rejected: body still has an earring at right carriage/neck and one painted protruding foot below rump.'}
for direction in ['Up','Down']:
 old=here/'generation'/direction/'revision_02'
 review={'revision':'revision_02','status':'rejected_pending_revision_03','observation':findings[direction],'sha256':hashlib.sha256((old/'raw.png').read_bytes()).hexdigest().upper()}
 (old/'visual_review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
 dest=here/'generation'/direction/'revision_03';dest.mkdir(exist_ok=True)
 assert not (dest/'request.json').exists()
 prompt=(here/'generation'/direction/'revision_01/prompt.txt').read_text(encoding='utf-8-sig')
 if direction=='Up':
  priority='''FINAL CORRECTION: Rear head cells 1,2,3 must each have EXACTLY ONE GOLD EARRING on the IMAGE-LEFT ear only. IMAGE-RIGHT EAR MUST BE COMPLETELY BARE, with NO GOLD RING. No duplicate ear jewellery. Body cell 4 is headless, hatless, earless and has no earrings. Its cannon sits directly on a PLAIN RECTANGULAR WOODEN CARRIAGE. Rear feet show single smooth continuous dark heel ovals without split toes.
'''
 else:
  priority='''FINAL CORRECTION: Cell 4 must be a completely HEADLESS, HATLESS, EARLESS and FOOTLESS TORSO with cannon and plain wooden carriage on top. Lower body ends in one smooth ROUND OVAL contour. NO FOOT OR TOE OR PROTRUSION BELOW THE BODY. No earring on body or carriage. Chain is plain gray metal rectangles, no gold rings. The ONLY ear and gold earring belong to heads in cells 1,2,3. The ONLY legs are detached in cells 5,6. No extra legs. Cannon muzzle on top -> plain rectangular wooden carriage -> spotted oval rump, nothing else.
'''
 (dest/'prompt.txt').write_text(priority+prompt,encoding='utf-8')
print('PirateBoar revision_03 prompts prepared; revision_02 evidence retained')
