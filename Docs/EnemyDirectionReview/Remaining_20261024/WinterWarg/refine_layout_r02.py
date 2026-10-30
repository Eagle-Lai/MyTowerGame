from session_winterwarg import *
import shutil
owner()
history=D/'stage_history/layout_r01';assert not history.exists();history.mkdir(parents=True)
for name in ['staged_art','offline_Up.png','offline_Down.png','offline_rig_proof.png','parts_clean.png','layout_adjustments.json','processing.json']:
    p=D/name
    if p.is_dir():shutil.copytree(p,history/name)
    else:shutil.copy2(p,history/name)
a=read(D/'layout_adjustments.json')
for side,sign in [('L',-1),('R',1)]:
    a['parts']['Up/Fore'+side].update(x=sign*.14,y=.60,height=.27,angle=sign*25)
    a['parts']['Down/Hind'+side].update(x=sign*.14,y=.72,height=.27,angle=sign*27)
a['reason']+=' Layout r02 buries far shoulder/hip caps more deeply and reduces the lateral paw reach observed in r01.'
write(D/'layout_adjustments.json',a)
run('character_step.py','stage',NAME)
stage('staged_layout_r02_pending_visual_review',D/'offline_rig_proof.png')
