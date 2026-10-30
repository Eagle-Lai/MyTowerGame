"""Apply documented, per-character art-direction adjustments to staged art only."""
from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent
name=sys.argv[1];directory=HERE/name
changes=json.loads((directory/'layout_adjustments.json').read_text(encoding='utf-8'))
path=directory/'staged_art'/(name+'_Directions.layout.json')
layout=json.loads(path.read_text(encoding='utf-8'))
for field,value in changes.get('layout',{}).items():
    if field not in layout and field!='motion':raise ValueError('Unknown layout field '+field)
    layout[field]=value
for view in layout['views']:
    view['parts']=[part for part in view['parts'] if view['direction']+'/'+part['name'] not in changes.get('remove',[])]
    for part in view['parts']:
        update=changes.get('parts',{}).get(view['direction']+'/'+part['name'],{})
        for field,value in update.items():
            if field not in part:raise ValueError('Unknown layout field '+field)
            part[field]=value*layout['referenceHeight']+(layout['referenceBottom'] if field=='y' else 0) if field in ['x','y','width','height'] else value
    counts={k:sum(p['role']==r for p in view['parts']) for k,r in [('legs','leg'),('wings','wing'),('claws','claw'),('tails','tail'),('arms','arm'),('feelers','feeler')]}
    if view is layout['views'][0]:layout['anatomy']=counts
    elif counts!=layout['anatomy']:raise ValueError('Different part counts across views require explicit builder support')
path.write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8')
sprite_path=directory/'staged_art'/(name+'_Directions.sprites.json')
sprites=json.loads(sprite_path.read_text(encoding='utf-8'))
for sprite in sprites['sprites']:
    for field,value in changes.get('sprites',{}).get(sprite['name'],{}).items():
        if field not in ['pivotX','pivotY']:raise ValueError('Only reviewed pivot changes supported')
        sprite[field]=value
sprite_path.write_text(json.dumps(sprites,indent=2)+'\n',encoding='utf-8')
print(name+' staged character-specific adjustments applied')
