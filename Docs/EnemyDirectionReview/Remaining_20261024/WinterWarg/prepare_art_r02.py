from session_winterwarg import *
import shutil
owner();hist=D/'stage_history/art_r01_installed';assert not hist.exists();hist.mkdir(parents=True)
for name in ['staged_art','offline_Up.png','offline_Down.png','offline_rig_proof.png','layout_adjustments.json','runtime_summary.json','runtime_visual_strip.png']:
    p=D/name
    if p.is_dir():shutil.copytree(p,hist/name)
    else:shutil.copy2(p,hist/name)
write(D/'art_r01_runtime_visual_rejection_20261029.json',{'observed_at':now(),'status':'technical 168PASS0FAIL, visual proportions require repair','runtime':read(D/'runtime_summary.json'),'viewed':['runtime_r01/four_directions.png','runtime_visual_strip.png'],'finding':'Axial head size too small compared with the source large-head warg silhouette. Enlarge the two head slices without changing source side views or limb anatomy.','prior_runtime_retained':True},True)
a=read(D/'layout_adjustments.json');a['parts']['Up/Head'].update(y=.79,height=.57);a['parts']['Down/Head'].update(y=.42,height=.64)
a['reason']+=' art_r02 enlarges the actual axial head to restore the observed original large-head silhouette after real-Play review.'
write(D/'layout_adjustments.json',a)
# Reapply the already-reviewed layout only; do not repack or overwrite cleaned alpha.
run('adjust_layout.py',NAME);run('render_staged_rig.py',NAME)
stage('art_r02_head_proportion_repair_pending_offline_review',D/'offline_rig_proof.png')
