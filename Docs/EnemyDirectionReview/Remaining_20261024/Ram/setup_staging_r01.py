from pathlib import Path
import json
root=Path(__file__).resolve().parent
selection={'Up':'generation/Up/revision_01/raw.png','Down':'generation/Down/revision_01/raw.png','note':'Original first attempts rejected for invented cream tail/body tufts and missing front beard; both revision_01 sheets visually reviewed. Up rear head and solid dark wool torso, Down beard, tiny dark tails retained. Explicit cell rectangles include torso below nominal row boundary.','rectangles':{}}
rects=[[0,0,384,540],[384,0,768,540],[768,0,1110,540],[1110,0,1536,590],[0,590,384,1024],[384,590,768,1024],[768,590,1152,1024]]
for d in ['Up','Down']:
 for p,r in zip(['HeadNormal','HeadAngry','HeadDead','Body','LegFront','LegBack','Tail'],rects): selection['rectangles'][d+'_'+p]=r
(root/'art_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf-8')
changes={'note':'Ram only: short-hoof woolly quadruped, solid shoulder/hip roots inside torso, short tail seated in rump; restrained diagonal stepping under heavy wool. Original ivory curled horns and beard retain silhouette.','layout':{'motion':{'legAngle':7.5,'legLift':0.12,'bodyBob':0.004,'bodyRoll':0.65,'tailSwing':3.0}},'parts':{}}
for d in ['Up','Down']:
 up=d=='Up'
 changes['parts'][d+'/Body']={'y':0.55 if up else 0.63,'width':0.72,'height':0.70 if up else 0.62}
 changes['parts'][d+'/Head']={'y':0.81 if up else 0.40,'width':0.74,'height':0.40 if up else 0.50}
 changes['parts'][d+'/Tail']={'x':0.0 if up else 0.05,'y':0.24 if up else 0.84,'width':0.115,'height':0.16,'order':30 if up else 5}
 for side in ['L','R']:
  sign=-1 if side=='L' else 1
  for front in [True,False]:
   near=(not front) if up else front
   changes['parts'][d+'/'+('Fore' if front else 'Hind')+side]={'x':sign*(0.17 if near else 0.215),'y':0.235 if near else (0.45 if up else 0.41),'width':0.16,'height':0.20 if near else 0.25}
(root/'layout_adjustments.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
