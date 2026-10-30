from pathlib import Path
import json,shutil
root=Path(__file__).resolve().parent
old=root/'staging_r01_rejected'
old.mkdir(exist_ok=False)
for name in ['art_selection.json','layout_adjustments.json','offline_rig_proof.png','offline_Up.png','offline_Down.png','processing.json']:
 shutil.copy2(root/name,old/name)
shutil.copytree(root/'staged_art',old/'staged_art')
selection=json.loads((root/'art_selection.json').read_text(encoding='utf-8'))
for d in ['Up','Down']:
 for p,r in zip(['HeadNormal','HeadAngry','HeadDead'],[[0,0,365,540],[375,0,725,540],[745,0,1090,540]]):selection['rectangles'][d+'_'+p]=r
selection['note']+='; r02: exclude neighboring horn pixels from head cells.'
(root/'art_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf-8')
changes=json.loads((root/'layout_adjustments.json').read_text(encoding='utf-8'))
changes['note']+=' r01 offline layout REJECTED: exposed leg roots and rear neck cap. r02: shorten and move all four roots inside opaque torso, head above rear neck cap, move front head to overlap neck and retain beard.'
for d in ['Up','Down']:
 up=d=='Up'
 changes['parts'][d+'/Body']={'y':0.55 if up else 0.62,'width':0.76,'height':0.70 if up else 0.74}
 changes['parts'][d+'/Head']={'y':0.83 if up else 0.45,'width':0.74,'height':0.40 if up else 0.50,'order':25 if up else 35}
 changes['parts'][d+'/Tail']={'x':0.0 if up else 0.05,'y':0.24 if up else 0.89,'width':0.10,'height':0.14,'order':30 if up else 5}
 for side in ['L','R']:
  sign=-1 if side=='L' else 1
  for front in [True,False]:
   near=(not front) if up else front
   changes['parts'][d+'/'+('Fore' if front else 'Hind')+side]={'x':sign*(0.13 if near else 0.18),'y':(0.29 if near else 0.51) if up else (0.39 if near else 0.56),'width':0.13,'height':0.20 if near else 0.22}
(root/'layout_adjustments.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
