"""Rat-only offline proportions; preserve the superseded staged evidence."""
from pathlib import Path
import json,shutil
D=Path(__file__).resolve().parent
for revision in [1,2,3,4,5]:
    archive=D/f'offline_revision_{revision:02d}_before'
    if archive.exists():continue
    archive.mkdir()
    for filename in ['layout_adjustments.json','processing.json','offline_Up.png','offline_Down.png','offline_rig_proof.png','parts_clean.png']:
        source=D/filename
        if source.exists():shutil.copy2(source,archive/filename)
    source=D/'staged_art'
    if source.exists():shutil.copytree(source,archive/'staged_art')
parts={
 'Up/Body':dict(y=.52,width=.66,height=.62),
 'Up/Head':dict(y=.84,width=.63,height=.34,order=25),
 'Up/Tail':dict(x=0,y=.30,width=.16,height=.28,order=5,angle=180),
 'Down/Body':dict(y=.59,width=.66,height=.62),
 'Down/Head':dict(y=.40,width=.52,height=.44),
 'Down/Tail':dict(x=.02,y=.88,width=.14,height=.28,order=5,angle=0),
}
for side,sign in [('L',-1),('R',1)]:
    parts['Up/Fore'+side]=dict(x=sign*.10,y=.47,width=.13,height=.20,angle=0)
    parts['Up/Hind'+side]=dict(x=sign*.18,y=.35,width=.15,height=.23,angle=sign*10)
    parts['Down/Fore'+side]=dict(x=sign*.13,y=.40,width=.15,height=.25,angle=sign*20)
    parts['Down/Hind'+side]=dict(x=sign*.15,y=.66,width=.16,height=.27,angle=sign*50)
(D/'layout_adjustments.json').write_text(json.dumps(dict(layout={},parts=parts),indent=2),encoding='utf-8')
print('Rat offline layout revision staged; no production mutation')
