"""Release WinterBear and prepare exactly one fresh local WinterBoar successor."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re, sys, uuid

D=Path(__file__).resolve().parent;H=D.parent;ROOT=H.parents[2]
sys.path.insert(0,str(D))
from checkpoint_20261029 import owner,read,sha,write,now,NAME,OWNER,TOKEN,LIVE,idle,result,unwrap
chain=owner();progress=read(H/'progress.json');done=next(i for i in progress['items'] if i['name']==NAME)
assert progress['completed_count']==98 and done['status']=='completed_pending_user_art_review' and not done['user_approved']
remaining=[i for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved']]
recoverable=[i for i in remaining if i['status'] not in ['not_started','blocked']]
selected=min(recoverable or [i for i in remaining if i['status']!='blocked'],key=lambda i:i['index'])
NEXT=selected['name'];N=H/NEXT;assert NEXT=='WinterBoar' and selected['index']==110 and selected['status']=='not_started'
assert len(remaining)==10 and sum(i['status']=='not_started' for i in remaining)==9
assert next(i for i in remaining if i['name']=='PossessedWarg')['status']=='blocked'
existing=sorted(p for p in N.rglob('*') if p.is_file());assert len(existing)==8 and all(p.is_relative_to(N/'reference') for p in existing)
t=next(t for t in read(H/'local_baseline.json')['targets'] if t['name']==NEXT)
six={p:sha(ROOT/p) for k in ['battle','source','atlas'] for p in [t[k],t[k]+'.meta']}
assert all(six.values()) and all(sha(N/'reference'/Path(p).name)==v for p,v in six.items())
final=read(D/'final_validation_20261029.json');binding=read(D/'version_binding_final_20261029.json');scope=read(D/'scope_incremental_final_20261029.json')
assert (final['passes'],final['failures'],final['actual_png_frames'])==(168,0,592) and final['final_revision']=='art_r05'
assert len(binding['installed_files'])==22 and all(sha(ROOT/p)==v for p,v in binding['installed_files'].items())
assert all(sha(ROOT/p)==v for p,v in binding['production_scope_files'].items())
for file,key in [('version_binding_final_20261029.json','version_binding_sha256'),('scope_incremental_final_20261029.json','incremental_scope_sha256'),('visual_review_art_r05_20261029/review.json','visual_review_sha256'),('gif_archive_verification_20261029.json','gif_archive_sha256')]:assert sha(D/file)==final[key]
assert (scope['baseline_files'],scope['current_files'],len(scope['changes']),scope['added_count'],scope['deleted_count'])==(5505,5525,22,20,0)
assert not scope['unexpected_incremental'] and not scope['shared_CSharp_drift'] and scope['prefab_semantics']['pass']
assert final['global_archive_count']==1582 and not any(r.get('character')==NAME for r in chain.get('completed_handoffs',[]))
sys.path.insert(0,str(H));from mcp_call import Client,URL
c=Client();project=c.identity();errors=unwrap(c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'}));assert errors['data']==[]
c.tool('execute_code',{'action':'execute','code':'var t=System.Linq.Enumerable.FirstOrDefault(System.Linq.Enumerable.Select(System.AppDomain.CurrentDomain.GetAssemblies(),a=>a.GetType("MCPForUnity.Editor.Services.EditorStateCache")),x=>x!=null);if(t==null)throw new System.Exception("State cache unavailable");var m=t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic);if(m==null)throw new System.Exception("Cache refresh unavailable");m.Invoke(null,new object[]{"WinterBear final handoff snapshot"});return true;'})
state=c.resource('mcpforunity://editor/state')['data'];live=result(c.tool('execute_code',{'action':'execute','code':LIVE}));idle(live)
assert state['advice']['ready_for_tools'] and not state['tests']['is_running'] and not state['compilation']['is_compiling'] and not state['compilation']['is_domain_reload_pending']
assert not state['assets']['is_updating'] and not state['assets']['external_changes_dirty']
stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S');token='winterbear-to-winterboar-'+stamp+'-'+str(uuid.uuid4())
rel=lambda p:p.relative_to(ROOT).as_posix()
handoff=H/'conversation_handoffs'/(stamp+'_WinterBear_completed.md');assessment=N/('successor_assessment_'+stamp+'.json');prompt_path=N/('successor_prompt_'+stamp+'.txt')
release_path=D/'handoff_release_20261029.json';dispatch_path=N/'prepared_dispatch_20261029.json'
assert all(not p.exists() for p in [handoff,assessment,prompt_path,release_path,dispatch_path])
write(release_path,{'observed_at':now(),'released_by_thread_id':OWNER,'current_character':NAME,'next_character':NEXT,'next_dispatch_token':token,'transport':URL,'project':project,'editor_state':state,'live_probe':live,'console_errors':[],'safe_to_handoff':True,'protocol_history':c.history})
write(assessment,{'observed_at':now(),'completed_count':98,'authorized_count':108,'next_character':NEXT,'next_index':110,'status':'not_started','dispatch_token':token,'target':t,'protected_six':six,'reference_matches_live':True,'existing_files':[p.relative_to(N).as_posix() for p in existing],'source_art_reviewed_by_parent':False,'source_instruction':'Next owner must inspect original atlas, full source prefab, actual legs/tail and Boar native animation. Do not copy WinterBear anatomy/layout.','no_generation_staging_install_or_runtime':True,'remaining':[{k:i[k] for k in ['index','name','status']} for i in remaining],'blocked_preserved':[i for i in remaining if i['status']=='blocked']})
summary=f'''# WinterBear109 完成与 WinterBoar110 唯一串行交接

时间 {now()}。父线程{OWNER}，旧token {TOKEN}。WinterBear已record为completed_pending_user_art_review、user_approved=false；进度98/108。

## 最终美术、原生行为与历史

最终art_r05，14个非空透明切片，真实四足、短尖毛尾，保留白灰蓬毛、宽棕纹/赭点、圆耳、棕眼圈、赭鼻和奶油犬齿。Up纯后脑无脸、耳背无内耳杯、后足无正面趾线；Down三表情鼻口居中。离线r01露腿根/颈口/切片边界、r02遮挡接缝及邻格碎片、r03颈帽与尾向、r04几何切颈均否决保留；r05弧形毛领遮合、四腿根内收、短尾朝后，局部修补与父哈希见local_raster_r01..r05各manifest。Down修正版原alpha91..253而非真正透明，按180..245分离背景；Up按30..240，保留深色描边与暖色纹，无RGB色彩掩码误删。

付费结果：3次HTTP200（Up/revision_01恢复、Down首版、Down/revision_01正视修版）及1次Up原请求Curl55结果不明。原generation/Up/request/uncertain_result保留，无HTTP响应/图片/serverID，收费和结果仍未知。按既有standing_network_recovery_authorization及WinterBear/standing_recovery_application_20261029_Up.json执行有界恢复，仅用1次追加Up网络恢复；成功raw不改、不盲重发原请求。局部generate_guarded_recovery.mjs保留来源证明，共享generate.mjs未改。usage估算不是实际账单。

仅安装一次，installed_manifest.json SHA {final['manifest_sha256']}。Builder/Verify通过；22条prePlay生产哈希不变，源prefab/原atlas/meta与原左右侧面保持。Bear Ready/Attack/Walk=.5s，Death=.416666657s，60FPS，Ready/Walk loop；原float/PPtr/SetHead与Attack事件契约保留。四足原型、HP、锚点、碰撞/移动战斗与事件接收器语义通过。没有修改共享C#、其他角色、配置表、ConfigJson/Gen或无声版本。

## 真实运行与实际视觉范围

runtime_r01：84PASS/0FAIL、296张真实PNG，records SHA {final['runtime'][0]['records_sha256']}。
runtime_updeath_r01：84PASS/0FAIL、296张真实PNG，records SHA {final['runtime'][1]['records_sha256']}；第二轮指定Up死亡。共168/0、592原PNG，两个returned都clean Boot。

实际看最终离线rig、分件与Up颈/肩髋/尾根细节、两轮four_directions和runtime strip、10张时序/步态/愤怒板（256采样位/229不同PNG）、6张768完整原PNG、12GIF各5编码帧共60帧、另4张未裁切GIF整帧。可见错相四足、转向、攻击头切换、受击白闪及恢复、Down/Up全身死亡旋转缩小淡出、自动回收/同实例Down正常复用、暂停冻结与恢复、1x/2x/3x推进。无地面阴影，颈肩髋腿根连接。淡出时既有逐renderer透明可见重叠分件透叠。没有实时播放或逐帧全审；全592帧保存并哈希。内部技术视觉通过，用户美术待验收。

AllGIF由1570变1582，本角色12条均当前审核版本，源/归档SHA一致。证据WinterBear/final_validation_20261029.json、version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_art_r05_20261029/review.json、gif_archive_verification_20261029.json、unity_release_final_r05_20261029.json、runtime_summary.json、record_note_utf8.txt。

## 增量范围与Unity释放

当前磁盘完整路径并集5505→5525文件，22变化/20新增/0删除、unexpected0。仅WinterBear battle/Directions及未改ReporterEditor自动Play时间戳单列。其余5保护、共享C#与其他角色/配置无增量漂移，本角色原组件语义PASS。旧全局291unexpected/6其他角色语义失败保留且未重审，不称全局PASS。

本轮Docs暂存脚本有空目录后续链误跑、只读Pillow floodfill未生效等失败，均在未安装前发现；最终r05与两轮安装哈希一致。Down_Body有229个全透明像素隐藏RGB与atlas不同，alpha及全部可见RGBA一致，检查按可见像素准确比较；未把隐藏RGB差异当视觉失败或伪造全字节一致。

正确Unity2022.3.62f3c1/8088动态选MyTowerGame并核E:/MyTowerGame；最终refresh/compile正常、error0。交接前再次核身份/状态：单一clean Boot、非Play、tests/review/balance/recording/manual/compile/reload/update全空闲、failed=false、ready=true、external_changes_dirty=false。{rel(release_path)}。不清日志、未用桌面。

## 下一唯一角色

重读实时items，剩余10项：PossessedWarg79旧blocked和结果不明Down请求保留、9项not_started，无可恢复已开始非blocked项。选最低index的WinterBoar110。父只核其reference8文件及六保护匹配，未审新角色源图、未做其生成/暂存/安装/运行。下一owner独立查看{t['atlas']}、{t['source']}、{t['battle']}与{t['controller']}；实际没有的器官不得按熊模板新增。

新token {token}；assessment {rel(assessment)}；完整prompt {rel(prompt_path)}。chain先handoff_ready，现场list_projects选E:/MyTowerGame，再唯一fresh local create_thread，不fork/不子代理/不计时器/不改模型。创建明确成功后登记新active owner为父最后工作区写入，之后父只读。保留PossessedWarg旧阻断和本WinterBear初次Up请求不明收费证据。
'''
handoff.write_text(summary,encoding='utf-8')
# Reuse complete operational instructions while replacing only the current-character facts.
prompt=(H/'NEXT_ENEMY_TASK.md').read_text(encoding='utf-8').split('\n\n',1)[1]
prompt=prompt.replace('WinterBear','WinterBoar').replace('index109','index110').replace('index 109','index 110').replace('WinterBoar109','WinterBoar110')
prompt=prompt.replace('01a18560-5f4b-7b42-a2cf-f926c68a77ae',OWNER).replace(TOKEN,token)
prompt=re.sub(r'6\. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/[^\n]+',lambda _: '6. E:/MyTowerGame/'+rel(handoff)+'。',prompt)
prompt=re.sub(r'7\. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/WinterBoar/successor_assessment_[^\n]+',lambda _: '7. E:/MyTowerGame/'+rel(assessment)+'。',prompt)
start=prompt.index('实时97/108。');end=prompt.index('\n\n逐阶段推进：',start)
prompt=prompt[:start]+f'''实时98/108。WinterBear109已record，art_r05，completed_pending_user_art_review、user_approved=false。剩余10项：PossessedWarg79旧blocked和结果不明Down付费请求保留、9项not_started；无可恢复已开始项，选最低index的WinterBoar110。不能盲用progress.current。108是授权数量，终项Zombie118。WinterBoar仅reference8文件；assessment/prompt/dispatch/creation为调度证据，无生成/暂存/安装/运行。

WinterBoar生产路径：
- battle：{t['battle']}
- source：{t['source']}
- atlas：{t['atlas']}
- controller：{t['controller']}
父只核六保护与reference匹配，未审新源图。必须实际查看完整原atlas/源prefab，核层级、renderer/腿尾等真实解剖、原float/PPtr/事件/时长/loop与移动/战斗/回收/同实例复用，独立制定WinterBoar正背面，不套熊或其他角色参数。开工前以当前磁盘包含既有用户修改建立Assets/Packages/ProjectSettings/Luban完整SHA基线及六保护，不用Git HEAD。'''+prompt[end:]
start=prompt.index('前任WildRooster最终证据');end=prompt.index('\n\n每次实际查看',start)
prompt=prompt[:start]+'''前任WinterBear最终证据WinterBear/final_validation_20261029.json、version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_art_r05_20261029/review.json、gif_archive_verification_20261029.json。最终art_r05、22条prePlay路径不变；296+296=592真实PNG、168/0。离线r01..r04否决保留；r05局部去耳杯/弧形毛领与根部连接、短尾朝后，四足无地面阴影。3次HTTP200及1次Up初请求Curl55结果不明，按standing授权有界恢复、初请求和收费未知原样保留；成功raw复用，Down修正版alpha91..253需去半透明白底。实际审10板256采样位/229不同PNG、6原PNG、12GIF各5编码帧及4未裁切整帧，非实时播放/逐帧全审；淡出时既有逐renderer alpha可见透叠。AllGIF1582，本角色12当前审核GIF，源归档SHA匹配。5505→5525文件、路径并集22变化/20新增、unexpected0，本角色语义PASS、其余5保护/共享C#无漂移，Reporter自动时间戳单列；旧global291unexpected/6其他角色语义失败保留未重审，不称全局PASS。不运行前任prepare/stage/install/finalize或覆盖封存证据。'''+prompt[end:]
assert '实时97' not in prompt and 'WildRooster108' not in prompt and TOKEN not in prompt
assert token in prompt and t['atlas'] in prompt and 'index110' in prompt
prompt_path.write_text(prompt,encoding='utf-8');(H/'NEXT_ENEMY_TASK.md').write_text('# 下一唯一角色 WinterBoar(index 110)\n\n'+prompt,encoding='utf-8')
live_text=f'''2026-10-29 WinterBear109已record，98/108，completed_pending_user_art_review、user_approved=false。最终art_r05/14非空透明切片/四足短尾，installed_manifest.json；r01..r04离线否决保留，r05耳背/毛领/根部连接，3次HTTP200+1次Up初请求Curl55结果不明，有界恢复授权及未知收费证据保留。两轮296+296=592真实PNG、168PASS/0FAIL；实际审最终离线rig/分件、两轮四向/strip、10板256采样位/229不同PNG、6原PNG、12GIF各5编码帧与4未裁切整帧，非实时播放或逐帧全审。AllGIF1582，本角色12当前审核GIF、源归档SHA一致。5505→5525文件、路径并集22变化20新增unexpected0，本角色语义PASS、其余5保护/共享C#无漂移，Reporter自动时间戳单列；旧global291unexpected/6其他角色语义失败未重审。Unity8088正确身份、最终编译/error0、单一clean Boot/非Play/全空闲/failed=false/ready=true/external_changes_dirty=false。最终WinterBear/final_validation_20261029.json及绑定/范围/视觉/归档。交接{rel(handoff)}。下一唯一WinterBoar110 not_started、reference8文件；token={token}。剩余10含PossessedWarg旧blocked/uncertain与9项not_started。'''
for path,begin,end in [(H.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),(H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    content=path.read_text(encoding='utf-8-sig');pattern=re.escape(begin)+r'.*?'+re.escape(end);assert len(re.findall(pattern,content,re.S))==1
    content=re.sub(pattern,lambda _:begin+'\n'+live_text+'\n'+end,content,flags=re.S)
    if path.name=='README.md':content,count=re.subn(r'\d{4}-\d{2}-\d{2} 本轮当前清单为 \d+ 个文件','2026-10-29 本轮当前清单为 1582 个文件',content);assert count==1
    path.write_text(content,encoding='utf-8')
done['handoff_file']=handoff.relative_to(H).as_posix();progress.update(current=NEXT,updated_at=now());write(H/'progress.json',progress)
dispatch={'prepared_at':now(),'created':False,'parent_thread_id':OWNER,'character':NEXT,'character_index':110,'dispatch_token':token,'project_root':'E:/MyTowerGame','project_id':None,'project_live_confirmed':False,'project_association_confirmed':False,
          'handoff_file':rel(handoff),'handoff_sha256':sha(handoff),'assessment_file':rel(assessment),'assessment_sha256':sha(assessment),'unity_release_file':rel(release_path),'unity_release_sha256':sha(release_path),'prompt_file':rel(prompt_path),'prompt_sha256':sha(prompt_path),'next_task_file':rel(H/'NEXT_ENEMY_TASK.md'),'next_task_sha256':sha(H/'NEXT_ENEMY_TASK.md'),'progress_sha256':sha(H/'progress.json'),'response_file':rel(N/'successor_creation_response_20261029.json')};write(dispatch_path,dispatch)
chain.setdefault('completed_handoffs',[]).append({'character':NAME,'status':done['status'],'current_stage':'recorded_pending_user_art_review','closed_at':now(),'owner_thread_id':OWNER,'dispatch_token':TOKEN,'handoff_file':rel(handoff),'final_evidence':rel(D/'final_validation_20261029.json')})
chain.update(state='handoff_ready',parent_thread_id=OWNER,current_character=NEXT,dispatch_token=token,character_status_at_handoff='not_started',completed_count_snapshot=98,previous_handoff_file=chain.get('last_handoff_file'),last_handoff_file=rel(handoff),handoff_sha256=sha(handoff),successor_assessment=rel(assessment),progress_sha256_at_handoff=sha(H/'progress.json'),unity_release_file=rel(release_path),dispatch_ready_for=NEXT,successor_created=False,current_stage='handoff_ready_pending_single_successor_creation',resume_character=NEXT,resume_stage='Verify owner/token; inspect WinterBoar source and native Boar motion; establish baseline',handoff_ready_at=now(),updated_at=now())
write(H/'conversation_chain.json',chain)
print(json.dumps({'state':'handoff_ready','character':NEXT,'dispatch_token':token,'dispatch_file':rel(dispatch_path),'prompt_file':rel(prompt_path),'handoff_file':rel(handoff),'safe_to_handoff':True},ensure_ascii=False))
