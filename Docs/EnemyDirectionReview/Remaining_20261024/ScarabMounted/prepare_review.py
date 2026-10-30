"""Persist actual reference observations and refine the first direction prompts."""
from pathlib import Path
import hashlib, json
D=Path(__file__).resolve().parent
plan=json.loads((D/'anatomy_plan.json').read_text(encoding='utf-8'))
plan['reference_review']={
    'method':'Actually viewed original 1024x512 atlas and full source and battle prefab renders; read serialized source and battle structures.',
    'observed_identity':'Dark olive oval segmented beetle with ochre spots, two long dark banded antennae attached to the head, two orange lens eyes, pale-gold curved mandibles, six long cream jointed legs with ochre pointed tips, tan leather saddle with raised rear cantle; no rider, wings, tail or independent feelers.',
    'source_bindings':'Body and all six legs use ScarabMounted atlas 61c99d3081db09a40a7cb3ef485b597a. Battle Head uses original Scarab atlas 306903ba18c180f46ac3783156892cb4; preserve original PPtr bindings and events. Do not repair this pre-existing shared-head binding as part of the direction art task.',
    'reference_files':['reference/ScarabMounted.png','reference/source_prefab_offline.png','reference/battle_prefab_offline.png','reference/source_structure.json','reference/battle_structure.json'],
    'up_anatomy':'Rear head plate and backs of both antennae, no orange eyes or mouth/mandible front details; closed spotted back with one saddle, six rear-oriented pointed legs.',
    'down_anatomy':'Centered paired orange eyes and two long antennae integrated into all three detached head states, pale-gold paired mandibles, torso with one saddle only, three mirrored pairs of cream legs.',
    'excluded':'No rider, tail, wings, extra heads, extra legs, duplicated saddle or ground shadow.'}
(D/'anatomy_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for direction in ['Up','Down']:
    folder=D/'generation'/direction
    assert not (folder/'request.json').exists()
    p=folder/'prompt.txt'
    text=p.read_text(encoding='utf-8')
    text+='\nCharacter-specific observed constraints: Preserve the TWO long dark olive banded antennae as part of EACH detached head slice, not extra independent cells. Head is an insect plate, not a mammal skull; no ears, hair or nose. Original pale-gold mandibles attach to the front face. Body has ochre round spots, layered closed wing-cases and exactly ONE tan leather saddle with its raised rear cantle; no rider, invented harness hardware or additional ornaments. Six cream angular jointed legs with ochre pointed tips: cells 5-7 are three distinct LEFT legs to be mirrored into three pairs, not six legs in each cell. No tail or wings.\n'
    if direction=='Up':
        text+='The three rear head slices are the SAME plain rear plate and rear antenna backs. Do not draw front eyes, orange lenses, teeth or forward-facing mouth on these rear plates. Rear saddle cantle is near the rump (lower part of this rear body view).\n'
    else:
        text+='Head states keep identical antenna/root alignment; normal has paired orange lens eyes, angry narrows the eyes and opens mandibles, dead follows the original drooping eye state. Saddle rear cantle is toward the far upper rump, not attached to the near head.\n'
    p.write_text(text,encoding='utf-8')
print(json.dumps({'name':D.name,'reference_review_saved':True,'prompt_directions':['Up','Down']}))
