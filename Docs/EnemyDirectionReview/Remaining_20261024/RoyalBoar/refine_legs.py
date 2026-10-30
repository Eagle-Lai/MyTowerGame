from pathlib import Path
import json,shutil
D=Path(__file__).resolve().parent
O=D/'offline_revision_02';O.mkdir(exist_ok=False)
for n in ['staged_art','offline_rig_proof.png','offline_Up.png','offline_Down.png','parts_clean.png','layout_adjustments.json']:
    p=D/n
    if p.is_dir():shutil.copytree(p,O/n)
    else:shutil.copy2(p,O/n)
p=D/'layout_adjustments.json';c=json.loads(p.read_text())
for view in ['Up','Down']:
    for side,sign in [('L',-1),('R',1)]:
        far=view+'/'+('Fore' if view=='Up' else 'Hind')+side
        c['parts'][far].update(x=sign*.385,y=.65,width=.18,height=.20,angle=sign*10)
c['reason']+=' Far shoulder hip roots inside torso edge; short far hoof tips visible on lateral edges rather than all four limbs hidden as two.'
p.write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8')
print('Offline layout03: expose far hoof tips while preserving roots')
