from pathlib import Path
import json,shutil
p=Path('Docs/EnemyDirectionReview/Remaining_20261024/MeatBug')
r=p/'layout_revision_01';r.mkdir(exist_ok=False)
for f in ['offline_rig_proof.png','offline_Up.png','offline_Down.png','layout_adjustments.json']:
 shutil.copy2(p/f,r/f)
shutil.copy2(p/'staged_art/MeatBug_Directions.layout.json',r/'MeatBug_Directions.layout.json')
a=json.loads((p/'layout_adjustments.json').read_text(encoding='utf-8'))
a['reason']+=' Offline r01 showed exposed front/rear leg roots. R02 buries roots under shell and uses short rounded LegMiddle foot for all six, matching original atlas reuse of one teardrop Leg sprite.'
for d in ['Up','Down']:
 for side in ['L','R']:
  sign=-1 if side=='L' else 1
  for j,n in enumerate(['Front','Middle','Back']):
   a['parts'][d+'/Leg'+n+side].update(sprite=d+'_LegMiddle',x=sign*([.14,.18,.18] if d=='Up' else [.19,.18,.14])[j],width=.22,height=.17)
a['parts']['Up/Head']['y']=.75
(p/'layout_adjustments.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf-8')