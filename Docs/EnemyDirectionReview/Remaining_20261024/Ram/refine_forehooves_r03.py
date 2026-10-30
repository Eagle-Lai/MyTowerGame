from pathlib import Path
import json,shutil
root=Path(__file__).resolve().parent
old=root/'staging_r02_rejected'
old.mkdir(exist_ok=False)
for name in ['art_selection.json','layout_adjustments.json','offline_rig_proof.png','processing.json','staging_r02_checks.json']:shutil.copy2(root/name,old/name)
shutil.copytree(root/'staged_art',old/'staged_art')
changes=json.loads((root/'layout_adjustments.json').read_text(encoding='utf-8'))
for side,sign in [('L',-1),('R',1)]:
 changes['parts']['Up/Fore'+side]={'x':sign*0.255,'y':0.43,'width':0.13,'height':0.27}
changes['note']+=' r02 rejected for far front hooves almost completely hidden; r03 offset far front roots into outer solid flank and extend short lower legs so both hoof pairs remain visible.'
(root/'layout_adjustments.json').write_text(json.dumps(changes,indent=2),encoding='utf-8')
