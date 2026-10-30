from pathlib import Path
from datetime import datetime,timezone,timedelta
import sys,json,hashlib,subprocess
HERE=Path(__file__).resolve().parent;RUN=HERE.parent;ROOT=RUN.parents[2]
sys.path.insert(0,str(RUN))
from mcp_call import Client
c=Client();project=c.identity()
regression=c.tool('execute_code',{'action':'execute','code':'FTProject.EditorTools.EnemyDirectionSpec s;FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("MimicChest",out s);string report;bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(s,out report);return new{pass=pass,report=report};'})
state=c.resource('mcpforunity://editor/state');errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
probe=c.tool('execute_code',{'action':'execute','code':'return UnityEditor.EditorUtility.scriptCompilationFailed;'})
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
manifest=json.loads((HERE/'repair_shot_r01/manifest.json').read_text())
drift=[x['path'] for x in manifest['changes'] if sha(ROOT/x['path'])!=x['after']]
assert not drift,drift
runtime=json.loads((HERE/'runtime_summary.json').read_text());assert runtime['passes']==168 and runtime['failures']==0
scope=json.loads((HERE/'scope_incremental_20261026.json').read_text());assert scope['pirate_semantics']['pass'] and not scope['unexpected_incremental']
report={'project':project,'observed_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),'final_install_manifest':'repair_shot_r01/manifest.json','installed_asset_drift':drift,'runtime_summary_sha256':sha(HERE/'runtime_summary.json'),'state':state,'errors':errors,'script_compilation_failed':probe,'mimic_chest_regression':regression,'approved_BlackWolf_regression_limit':'Existing Verify/Apply hook raised incomplete anatomy on approved BlackWolf layout. No approved production file changed. Preserved other_rig_verify.json; not attributed to PirateBoar-gated Shot branch and not repaired in this task.','protocol_history':c.history}
(HERE/'final_validation_20261026.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
note='本轮审阅 Up revision_06、Down revision_04 和 layout_revision_03。背面无脸、单耳环、耳边轮廓闭合；炮管与炮车只属身体，帽子只属头部，后蹄为连续椭圆脚跟，身体下缘完整，原角色无尾巴并保持无尾巴。实际四方向图及两轮连续帧中，头身和炮车连接稳定，前后脚交替幅度较小，符合沉重炮车步态；上下攻击后恢复正常头，受击闪白结束，普通/Up 死亡时整身倾倒缩小淡出，同实例再生恢复，暂停帧保持、1/2/3倍速和连续转向均已按原始帧序查看。未用工具实时播放GIF，采用两轮6张动作序列接触表和2张完整步态周期近景检查，另查看 Shot 四方向真实帧；标准两轮168 PASS/0 FAIL、682帧。Shot 补测4方向均进入原生状态，侧面后坐/闭眼和纵向炮车后坐可见。首次安装漏Shot检查失败已保留，最终修复清单为repair_shot_r01，运行后生产哈希一致；本轮仅一只战斗prefab改变。美术仍待用户验收。'
(HERE/'record_note_utf8.txt').write_text(note+chr(10),encoding='utf-8')
visual={'status':'completed_pending_user_art_review','review_method':'actual PNG sequences and extracted GIF cycle frames; no live GIF playback claimed','images_viewed':['runtime_r01/four_directions.png','offline_rig_proof.png','parts_clean.png','visual_review_20261026/runtime_r01_sequence_0.png','visual_review_20261026/runtime_r01_sequence_1.png','visual_review_20261026/runtime_r01_sequence_2.png','visual_review_20261026/runtime_updeath_r01_sequence_0.png','visual_review_20261026/runtime_updeath_r01_sequence_1.png','visual_review_20261026/runtime_updeath_r01_sequence_2.png','visual_review_20261026/runtime_r01_walk_cycles_close.png','visual_review_20261026/runtime_updeath_r01_walk_cycles_close.png','runtime_shot_r02/shot_sequence.png'],'note':note,'historical_block_preserved':'blocked_review.json','resolved_current_block':True}
(HERE/'visual_review_20261026/review.json').write_text(json.dumps(visual,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
subprocess.run([sys.executable,str(RUN/'record_review.py'),'PirateBoar',note],check=True)
print(json.dumps({'name':'PirateBoar','completed':True,'final_asset_drift':drift,'standard_checks':168,'actual_frames':682},ensure_ascii=False))
