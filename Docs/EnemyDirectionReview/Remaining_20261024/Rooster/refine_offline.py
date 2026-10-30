"""Archive rejected initial stage and set Rooster-only offline layout."""
from pathlib import Path
import json, shutil
D=Path(__file__).resolve().parent
archive=D/'rejected_stage_01'
archive.mkdir(exist_ok=False)
for name in ['staged_art','parts_clean.png','processing.json','layout_adjustments.json','offline_Up.png','offline_Down.png','offline_rig_proof.png']:
    p=D/name
    if p.is_dir():shutil.copytree(p,archive/name)
    elif p.exists():shutil.copy2(p,archive/name)
(archive/'review.json').write_text(json.dumps(dict(status='rejected_offline_not_installed',observations=['Both wings detached at generic x +/- .23','Duplicate neck attachment cylinders','Up leg is inverted with front toe fan toward torso']),indent=2)+'\n',encoding='utf-8')
parts={}
for direction in ['Up','Down']:
    for side,sign in [('L',-1),('R',1)]:
        parts[direction+'/Wing'+side]=dict(x=sign*.145,y=.51,width=.20,height=.30)
        parts[direction+'/Leg'+side]=dict(x=sign*.13,y=.20,width=.18,height=.23)
    parts[direction+'/Head']=dict(y=.735,height=.56)
changes=dict(remove=['Up/Tail','Down/Tail'],parts=parts,
    reason='Five bound source renderers; integrated rump only. Wings root inside torso; longer overlapping neck hides Body attachment. Up feet receive documented local rear-heel retouch.')
(D/'layout_adjustments.json').write_text(json.dumps(changes,indent=2)+'\n',encoding='utf-8')
