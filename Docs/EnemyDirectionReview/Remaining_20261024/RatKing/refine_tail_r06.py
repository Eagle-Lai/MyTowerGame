"""Front tail placement avoids the protected unchanged HP bar in real Play."""
from pathlib import Path
import json,shutil,subprocess,sys,hashlib
D=Path(__file__).resolve().parent;R=D/'offline_tail_revision_06';assert not R.exists();R.mkdir();shutil.copytree(D/'staged_art',R/'staged_before')
for n in ['layout_adjustments.json','offline_rig_proof.png','runtime_summary.json','runtime_visual_strip.png']:shutil.copy2(D/n,R/n)
(D/'visual_review_proportions_final_20261026/review.json').write_text(json.dumps(dict(status='superseded_visual_repair_required',observations_zh='已查看返修版四方向及第一轮步态/转向时序板，并核对原始 DownWalk_00021.png。头身比例改善，但 Down 向后直伸的尾尖穿过未变更的绿色血条；不移动血条，改为从臀部向后右侧斜伸。两轮虽然各84 PASS，仍不record。本版669帧保留，未宣称全片审完。',user_approved=False),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=D/'layout_adjustments.json';adj=json.loads(p.read_text());adj['parts']['Down/Tail'].update(x=.14,y=.97,width=.17,height=.31,angle=-50)
p.write_text(json.dumps(adj,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(D.parent/'adjust_layout.py'),'RatKing'],check=True)
subprocess.run([sys.executable,str(D/'render_full_offline.py')],check=True)
(R/'reason.json').write_text(json.dumps(dict(parent='repair_proportions_r05/manifest.json',reason='Actual Down tail crossed protected HP bar. Only tail pivot placement and angle changed; no HP bar, collider, root, side rig or shared code change.',staged_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest().upper() for p in (D/'staged_art').iterdir() if p.is_file()}),indent=2)+'\n',encoding='utf-8')
