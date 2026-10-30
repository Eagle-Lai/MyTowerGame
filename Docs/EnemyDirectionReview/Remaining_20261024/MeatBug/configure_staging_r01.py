from pathlib import Path
import json
p=Path('Docs/EnemyDirectionReview/Remaining_20261024/MeatBug')
selection={'Up':'generation/Up/revision_01/raw.png','Down':'generation/Down/revision_01/raw.png','rectangles':{},'review':'Up original rejected for ear-like additions and side-view torso; Down original rejected for antennae painted onto head plus detached feelers. Both revision_01 selected; remove grid gutters with explicit cell crops.'}
parts=['HeadNormal','HeadAngry','HeadDead','Body','LegFront','LegMiddle','LegBack','Feelers']
for d in ['Up','Down']:
 for i,part in enumerate(parts):
  col=i%4;row=i//4
  selection['rectangles'][d+'_'+part]=[col*384+8,row*512+8,(col+1)*384-8,(row+1)*512-8]
(p/'art_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
a={'reason':'MeatBug has low oval armored body, six short feet and paired long feelers. Shorten limbs and bury solid roots under shell; rotate rear feelers forward along travel. Keep original side rig and shared animation unchanged.','layout':{'motion':{'legAngle':7,'legLift':.075,'bodyBob':.002,'bodyRoll':0,'tailSwing':0}},'parts':{}}
for d in ['Up','Down']:
 a['parts'][d+'/Body']={'width':.67,'height':.70,'y':.46 if d=='Up' else .55}
 a['parts'][d+'/Head']={'width':.40,'height':.32,'y':.78 if d=='Up' else .25}
 for side in ['L','R']:
  sign=-1 if side=='L' else 1
  for j,n in enumerate(['Front','Middle','Back']):
   a['parts'][d+'/Leg'+n+side]={'x':sign*.205,'y':(.62-j*.16) if d=='Up' else (.31+j*.16),'width':.20,'height':.16,'angle':sign*(j-1)*5}
  a['parts'][d+'/Feeler'+side]={'x':sign*.11,'y':.80 if d=='Up' else .22,'width':.36,'height':.19,'angle':sign*65 if d=='Up' else 0,'order':11 if d=='Up' else 34,'phase':int(side=='R')}
(p/'layout_adjustments.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')