from pathlib import Path
root=Path(__file__).resolve().parent
for direction in ['Up','Down']:
    p=root/'generation'/direction/'prompt.txt'
    if (p.parent/'request.json').exists():raise ValueError('Keep paid request immutable')
    text=p.read_text(encoding='utf-8')
    text+='''
Drake-specific critical constraints: This is the ORIGINAL OCHRE duck, not a dragon. Preserve three tall pointed gold crown feathers, small original pointed tail feather fan, white/ivory neck ring, amber gold body, darker gold folded wings, orange-yellow webbed feet and original thick dark brown outline. No green head, no red comb/wattle, no horn, no blue/white belly, no extra feathers or equipment. Head is big and upright; body is compact with short neck. The folded Wing slice is slim and points DOWN from its shoulder at TOP RIGHT, not a second torso. Body is clean compact duck torso with a SHORT ivory neck ring at TOP center; no tall exposed neck stump. Tail is ONE SMALL pointed gold feather fan, root at TOP CENTER and tips fanning DOWN, separate from Body; do not paint another tail onto Body. All pieces stay completely inside their exact 4-by-2 cells with 14 percent padding.
'''
    if direction=='Up':
        text+='''Pure rear head: plain round ochre back of skull with three crown spikes, absolutely no bill, eyes, white cheek or face. Neck ring belongs only to Body. Rear feet: show smooth narrow back of orange ankles and HEEL surface; webbed toes extend AWAY behind ankle and are occluded/foreshortened. No forward-facing three-lobed toe fan, no toenails/stripes on heel. Wing feathers and tail feathers are seen from their outer backs.
'''
    else:
        text+='''Centered axial duck face: both round ivory eyes symmetrical, wide orange bill centered directly beneath eyes (not sideways). HeadAngry narrows both eyes; HeadDead has the original two blank round eyes and small tongue to one side. Front feet show broad orange webbing pointed toward viewer. No duplicate beak on torso.
'''
    p.write_text(text,encoding='utf-8')
print('Drake prompts refined')
