from pathlib import Path
import json
root=Path(__file__).resolve().parent
plan=json.loads((root/'anatomy_plan.json').read_text(encoding='utf-8'))
plan['individual_constraints']=['Cream-white duck, small pointed white crest, ochre cheek and rump patch, no collar','Two small folded cream-white wings with three tips','One small upturned white tail, no duplicate tail baked into body','Rear plain rounded orange heel with NO front webbed toes; front orange webbed foot']
(root/'anatomy_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
for direction in ['Up','Down']:
    path=root/'generation'/direction/'prompt.txt'
    if (path.parent/'request.json').exists():raise ValueError('Paid request already exists')
    rear=direction=='Up'
    text=path.read_text(encoding='utf-8')
    text+=chr(10)+'Duck-specific anatomy: bright CREAM-WHITE feathers with sparse original OCHRE patches, white small pointed crest. Do not copy golden Drake colors or invent a colored neck ring. Head is detached at base of round skull; narrow cream neck is part of body, solid at top. Torso has NO wings or tail baked in. ONE tiny detached upturned white tail fan only in cell 7. Cell 5 is ONE small cream folded wing with three feather tips and solid root at TOP RIGHT. Cell 6 is ONE leg including small round white thigh at top and thin orange shank ending in '+('a compact plain rounded REAR HEEL; webbed front toes are occluded, NO claws, NO pointed web toes facing viewer' if rear else 'a broad FRONT orange webbed foot with three rounded toes aimed toward viewer')+'. Use original funny large round eyes and broad flat orange bill on front only. Back head is plain white with crest and cheek-edge patch, no bill or face. Keep broad simple clean cel shaded regions, no textures or extra anatomy.'+chr(10)
    path.write_text(text,encoding='utf-8')
