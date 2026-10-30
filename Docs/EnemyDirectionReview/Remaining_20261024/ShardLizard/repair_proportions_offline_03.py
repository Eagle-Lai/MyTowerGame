"""Correct the undersized axial views actually observed in first real Play."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, sys
D=Path(__file__).resolve().parent
H=D.parent
chain=json.loads((H/'conversation_chain.json').read_text(encoding='utf-8'))
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and chain['current_character']==D.name
assert chain['dispatch_token']=='scarabmounted-to-shardlizard-e066b2f9cbb54a5ca5b215b2e08ea8d2'
R=D/'offline_proportions_revision_03'
assert not R.exists()
R.mkdir()
for name in ['art_selection.json','layout_adjustments.json','offline_rig_proof.png','parts_clean.png','processing.json','runtime_summary.json','runtime_visual_strip.png']:
    shutil.copy2(D/name,R/name)
shutil.copytree(D/'staged_art',R/'staged_before')
observations={'status':'superseded_visual_repair_required','actually_viewed':['runtime_r01/four_directions.png','runtime_visual_strip.png'],
    'observations_zh':'首轮虽然168 PASS/0 FAIL，但四方向实际图中正背投影的头身与四肢明显偏小，转向体量跳变。本轮678帧及全部GIF保留，不作为最终视觉通过版本。使用相同r02图像，仅将正背部件尺寸、横向关节间距乘1.6，纵向关节围绕referenceHeight的0.5位置展开1.6；保持原侧面、根节点、血条和碰撞器。预计尾尖仍在血条下，实际新Play再次核对。',
    'original_manifest':'installed_manifest.json','new_manifest':'repair_proportions_r03/manifest.json','user_approved':False}
(R/'review.json').write_text(json.dumps(observations,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
adj=json.loads((D/'layout_adjustments.json').read_text(encoding='utf-8'))
for p in adj['parts'].values():
    for k in ['x','width','height']:
        if k in p:p[k]*=1.6
    if 'y' in p:p['y']=.5+(p['y']-.5)*1.6
adj['reason']+=' Actual real-Play four-direction review showed axial views too small; revision03 scales only the axial part dimensions and joint spacing by1.6 around normalized y0.5. Original root/HP/collider/side rig unchanged.'
adj['layout']['motion'].update(legLift=.065,bodyBob=.012)
(D/'layout_adjustments.json').write_text(json.dumps(adj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run([sys.executable,str(H/'adjust_layout.py'),D.name],check=True)
subprocess.run([sys.executable,str(H/'render_staged_rig.py'),D.name],check=True)
print(json.dumps({'revision':R.name,'next':'View offline proof before repair_character.py ShardLizard repair_proportions_r03'}))
