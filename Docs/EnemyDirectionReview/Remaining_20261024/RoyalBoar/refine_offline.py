from pathlib import Path
from PIL import Image
import json,shutil,hashlib
D=Path(__file__).resolve().parent
R=D/'raster_revision_02';R.mkdir(exist_ok=False)
old=R/'rejected_stage_01';old.mkdir()
for n in ['staged_art','art_selection.json','parts_clean.png','offline_rig_proof.png','offline_Up.png','offline_Down.png','processing.json']:
    p=D/n
    if p.is_dir():shutil.copytree(p,old/n)
    else:shutil.copy2(p,old/n)
src=Image.open(D/'generation/Down/raw.png').convert('RGB')
rear=Image.open(D/'generation/Up/revision_01/raw.png').convert('RGB')
src.paste((255,0,255),(1120,0,1536,550))
piece=rear.crop((1060,120,1515,535));piece.thumbnail((394,420),Image.Resampling.LANCZOS)
src.paste(piece,(1126,95));src.save(R/'Down_derived_sheet.png')
s=json.loads((D/'art_selection.json').read_text())
s['Down']='raster_revision_02/Down_derived_sheet.png'
s['rectangles'].update(Up_HeadDead=[745,0,1040,550],Up_Body=[1060,0,1536,550],Down_HeadDead=[745,0,1115,550],Down_Body=[1120,0,1536,550])
(D/'art_selection.json').write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
changes=dict(remove=['Up/Tail','Down/Tail'],layout=dict(motion=dict(legAngle=8.5,legLift=.009,bodyBob=.004,bodyRoll=.85,tailSwing=0)),parts={
    'Up/Head':dict(y=.78,width=.72,height=.45,order=22),
    'Down/Head':dict(y=.405,width=.86,height=.60),
})
for view in ['Up','Down']:
    for side,sign in [('L',-1),('R',1)]:
        for front in [True,False]:
            near=front==(view=='Down')
            changes['parts'][view+'/'+('Fore' if front else 'Hind')+side]=dict(x=sign*(.30 if near else .245),y=.29 if near else .59,width=.18,height=.19,order=8)
changes['reason']='Squat fat golden boar. Rear head overlaps torso rather than only its tuft showing. Four short hooves attached beneath body; no independent tail. Compact diagonal gait, no tail channel.'
(D/'layout_adjustments.json').write_text(json.dumps(changes,indent=2)+'\n',encoding='utf-8')
(R/'correction.json').write_text(json.dumps(dict(reason='Actual stage01 rejected: Up rear head mostly hidden; Down dead head right edge clipped by initial local assembly; torso crop clipped left fur point. Safe body paste begins1120 outside all heads; direction-specific rectangles include entire silhouettes. Original sources preserved; local derived sheet only.',source_hashes={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in [D/'generation/Down/raw.png',D/'generation/Up/revision_01/raw.png']},derived_sha256=hashlib.sha256((R/'Down_derived_sheet.png').read_bytes()).hexdigest().upper()),indent=2)+'\n',encoding='utf-8')
print('Offline revision02 selection/layout prepared')
