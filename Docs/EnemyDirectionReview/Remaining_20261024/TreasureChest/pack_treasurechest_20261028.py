from session_treasurechest import *
from PIL import Image,ImageDraw
import numpy as np
owner();assert not (D/'staged_art').exists()
assert all(read(D/'generation'/v/'review_20261028.json')['accepted_for_staging'] for v in ['Up','Down'])
# Use the shared extractor with two explicitly documented Container-only transformations:
# retain rear OPEN state, and bottom-align whole-object state canvases.
s=(H/'pack_character.py').read_text(encoding='utf-8')
old="if direction=='Up' and p in ['HeadAngry','HeadDead']:piece=parts['Up_HeadNormal'].copy()"
assert s.count(old)==2
s=s.replace(old,"if p=='HeadAngry':piece=parts[direction+'_HeadNormal'].copy()")
s=s.replace('(h-im.height)//2','h-im.height')
old="    heads=[direction+'_'+p for p in ['HeadNormal','HeadAngry','HeadDead']]"
assert s.count(old)==1
s=s.replace(old,"    closed_height=parts[direction+'_HeadNormal'].height\n    for state in ['HeadNormal','HeadAngry','HeadDead']:\n        im=parts[direction+'_'+state]\n        parts[direction+'_'+state]=im.resize((384,round(im.height*365/closed_height)),Image.Resampling.LANCZOS)\n"+old)
s=s.replace("w=max(parts[p].width for p in heads);h=max(parts[p].height for p in heads)","w=384;h=480;assert all(parts[p].height<=h for p in heads)")
sys.argv=[str(H/'pack_character.py'),NAME]
exec(compile(s,str(H/'pack_character.py'),'exec'),{'__file__':str(H/'pack_character.py'),'__name__':'__main__'})
manifest=read(D/'staged_art/TreasureChest_Directions.sprites.json')
for sprite in manifest['sprites']:
    if '_Head' in sprite['name']:sprite.update(pivotX=.5,pivotY=0)
write(D/'staged_art/TreasureChest_Directions.sprites.json',manifest)
layout=read(D/'staged_art/TreasureChest_Directions.layout.json');bottom=layout['referenceBottom'];h=layout['referenceHeight']
for view in layout['views']:
    for part in view['parts']:
        if part['name']=='Head':part.update(x=0,y=bottom,width=1.22*h,height=1.30*h,order=30)
        else:part.update(x=0,y=bottom,width=.001*h,height=.001*h)
layout['motion']=dict(legAngle=0,legLift=0,bodyBob=.005,bodyRoll=1.2,tailSwing=0)
write(D/'staged_art/TreasureChest_Directions.layout.json',layout)
write(D/'state_rig_processing_20261028.json',dict(observed_at=now(),parent_script='pack_character.py',parent_sha256=sha(H/'pack_character.py'),target_extractor_sha256=sha(Path(__file__)),changes=['Keep independently generated Up_HeadDead/open state','Reuse normal state for HeadAngry compatibility on both views','Bottom-align whole-state canvases, pivot bottom center','Body intentionally transparent1px reference; no invented body anatomy'],state_slots=dict(HeadNormal='whole closed chest',HeadAngry='same closed chest',HeadDead='whole open chest',Body='transparent compatibility carrier'),source_selection=read(D/'art_selection.json'),shared_script_modified=False))
print(json.dumps(dict(staged=NAME,parts=8,whole_chest_states=True)))
