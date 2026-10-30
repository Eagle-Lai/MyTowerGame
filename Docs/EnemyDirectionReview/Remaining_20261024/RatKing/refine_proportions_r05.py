"""Repair undersized front/back projection seen in real Play; retain first-run evidence."""
from pathlib import Path
import json,shutil,subprocess,sys
D=Path(__file__).resolve().parent;R=D/'offline_proportions_revision_05';assert not R.exists();R.mkdir()
shutil.copytree(D/'staged_art',R/'staged_before')
for n in ['layout_adjustments.json','offline_rig_proof.png','runtime_summary.json','runtime_visual_strip.png']:shutil.copy2(D/n,R/n)
(D/'visual_review_serial_20261026/review.json').write_text(json.dumps(dict(status='superseded_visual_repair_required',observations_zh='已实际查看 runtime_r01/four_directions.png 和第一轮 movement/turns 时序板。正背头、身明显偏小；Builder 的 min(width/spriteWidth,height/spriteHeight) 由过低的高度上限约束，使转向体量变化过大。本轮虽然两次各84 PASS，仍不得record；保存两轮全部原帧和媒体，修改本角色布局后重跑。初版678帧没有全部完成视觉审阅，不作最终版本证据。',user_approved=False),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
adj=json.loads((D/'layout_adjustments.json').read_text())
parts={
 'Up/Body':dict(y=.52,width=.88,height=.86),
 'Up/Head':dict(y=1.0,width=.78,height=.56,order=25),
 'Up/Tail':dict(x=0,y=.12,width=.18,height=.35,order=5,angle=180),
 'Down/Body':dict(y=.72,width=.88,height=.86),
 'Down/Head':dict(y=.37,width=.78,height=.64),
 'Down/Tail':dict(x=.02,y=1.13,width=.17,height=.35,order=5,angle=0)
}
for side,sign in [('L',-1),('R',1)]:
    parts['Up/Fore'+side]=dict(x=sign*.20,y=.72,width=.18,height=.26,angle=0)
    parts['Up/Hind'+side]=dict(x=sign*.24,y=.26,width=.20,height=.28,angle=sign*8)
    parts['Down/Fore'+side]=dict(x=sign*.23,y=.39,width=.20,height=.28,angle=sign*15)
    parts['Down/Hind'+side]=dict(x=sign*.23,y=.78,width=.18,height=.26,angle=sign*20)
adj['parts']=parts
(D/'layout_adjustments.json').write_text(json.dumps(adj,indent=2)+'\n',encoding='utf-8')
(R/'reason.json').write_text(json.dumps(dict(parent='installed_manifest.json',initial_runtime=['runtime_r01','runtime_updeath_r01'],reason='Actual front/back head and body disproportionately small vs original side projection. Increase uniform individual sprite dimensions and joint spacing; do not scale prefab root, HP bar, collider or side rig.',planned_new_manifest='repair_proportions_r05/manifest.json'),indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(D.parent/'adjust_layout.py'),'RatKing'],check=True)
subprocess.run([sys.executable,str(D.parent/'render_staged_rig.py'),'RatKing'],check=True)
