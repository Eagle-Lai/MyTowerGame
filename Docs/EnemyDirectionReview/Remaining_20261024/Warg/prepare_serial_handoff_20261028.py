"""Release Warg and prepare exactly one fresh local Wasp successor."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,re,sys,uuid
D=Path(__file__).resolve().parent;H=D.parent;ROOT=H.parents[2]
OWNER='01a1830c-598a-7473-8ee1-01bccdd1f9be';OLD='volcanoparasite-to-warg-20261028-7f2313bf-967a-440d-94c4-79bf845d2b6f'
PROJECT=sys.argv[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
now=lambda:datetime.now(timezone(timedelta(hours=8)))
rel=lambda p:p.relative_to(ROOT).as_posix()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
chain=read(H/'conversation_chain.json');progress=read(H/'progress.json')
assert chain['state']=='active' and chain['owner_thread_id']==OWNER and chain['dispatch_token']==OLD and chain['current_character']=='Warg'
assert PROJECT=='935c594c-f414-48e0-bd08-ed8ba342f7fd'
done=next(r for r in progress['items'] if r['name']=='Warg');assert progress['completed_count']==92 and done['status']=='completed_pending_user_art_review' and not done['user_approved']
remaining=[r for r in progress['items'] if r['status'] not in ['completed_pending_user_art_review','user_approved']]
recoverable=[r for r in remaining if r['status'] not in ['not_started','blocked']]
selected=min(recoverable or [r for r in remaining if r['status']!='blocked'],key=lambda r:r['index'])
assert selected['name']=='Wasp' and selected['index']==104 and selected['status']=='not_started'
assert next(r for r in remaining if r['name']=='PossessedWarg')['status']=='blocked'
W=H/'Wasp';assert all(p.is_relative_to(W/'reference') for p in W.rglob('*') if p.is_file())
t=next(r for r in read(H/'local_baseline.json')['targets'] if r['name']=='Wasp')
six={p:sha(ROOT/p) for key in ['battle','source','atlas'] for p in [t[key],t[key]+'.meta']}
assert all(six.values()) and all(sha(W/'reference'/Path(p).name)==v for p,v in six.items())
final=read(D/'final_validation_20261028.json');binding=read(D/'version_binding_final_20261028.json');scope=read(D/'scope_incremental_final_20261028.json')
assert (final['passes'],final['failures'],final['actual_png_frames'])==(168,0,601)
assert sha(D/'version_binding_final_20261028.json')==final['version_binding_sha256']
assert sha(D/'scope_incremental_final_20261028.json')==final['incremental_scope_sha256']
assert all(sha(ROOT/p)==v for p,v in binding['installed_files'].items())
probes=sorted(D.glob('unity_release_probe_20261028_response*.json'),key=lambda p:p.stat().st_mtime)
probe_path=probes[-1];probe=read(probe_path);state=probe['results'][1]['data'];live=probe['results'][3]['structuredContent']['data']['result']
assert probe['success'] and probe['project']['projectRoot'].lower()=='e:/mytowergame' and probe['project']['unityVersion']=='2022.3.62f3c1'
assert probe['results'][2]['structuredContent']['data']==[]
assert state['advice']['ready_for_tools'] and not state['staleness']['is_stale'] and state['activity']['phase']=='idle'
assert not state['tests']['is_running'] and not state['compilation']['is_compiling'] and not state['compilation']['is_domain_reload_pending'] and not state['assets']['is_updating']
assert all(live[k] is False for k in ['playing','compiling','failed','updating','sceneDirty','balance','recording','review','manual'])
assert live['scene']=='Assets/Scenes/Boot.unity' and live['sceneCount']==1
stamp=now().strftime('%Y%m%d_%H%M%S');token='warg-to-wasp-'+stamp+'-'+str(uuid.uuid4())
handoff=H/'conversation_handoffs'/(stamp+'_Warg_completed.md')
assessment=W/('successor_assessment_'+stamp+'.json');prompt_path=W/('successor_prompt_'+stamp+'.txt')
release_path=D/'handoff_release_20261028.json';dispatch_path=W/'prepared_dispatch_20261028.json'
assert all(not p.exists() for p in [handoff,assessment,prompt_path,release_path,dispatch_path])
write(release_path,{'observed_at':probe['observed_at'],'released_by_thread_id':OWNER,'current_character':'Warg','next_character':'Wasp','next_dispatch_token':token,'transport':probe['transport'],'project':probe['project'],'unity_instance':state['unity']['instance_id'],'editor_state':state,'live_probe':live,'console_errors':[],'safe_to_handoff':True,'external_changes_dirty':state['assets']['external_changes_dirty'],'probe_response_file':probe_path.name,'probe_response_sha256':sha(probe_path),'note':'Single clean Boot; Play/tests/review/balance/recording/manual/compile/reload/update idle. Existing MCP cache ForceUpdate obtained a fresh factual snapshot, no source modification.'})
write(assessment,{'observed_at':now().isoformat(),'completed_count':92,'authorized_count':108,'selection':'Resume started nonblocked role first, otherwise lowest incomplete nonblocked index.','remaining':[{k:r[k] for k in ['index','name','status']} for r in remaining],'next_character':'Wasp','next_index':104,'status':'not_started','dispatch_token':token,'target':t,'protected_six':six,'reference_matches_live':True,'existing_files':[p.relative_to(W).as_posix() for p in sorted(W.rglob('*')) if p.is_file()],'no_generation_staging_install_or_runtime':True,'blocked_preserved':[r for r in remaining if r['status']=='blocked'],'project_id':PROJECT,'project_id_source':'Current list_projects result: local E:/MyTowerGame; selected before dispatch.'})
summary=f'''# Warg(index 103) 完成与 Wasp(index 104) 唯一串行交接

时间：{now().isoformat()}。父线程 `{OWNER}`，旧token `{OLD}`。Warg状态 `completed_pending_user_art_review`，`user_approved=false`，实时进度 **92/108**。

## Warg 最终实现

完整审阅原图/原prefab后保留暗橄榄棕毛、金眼、奶油色獠牙、赭色圆斑、深色背部乱毛、四短足与长尾；没有虚构背部金角。Up/Down首次请求各一次HTTP200，原始1536×1024 PNG均保留复用，没有新增付费返修；usage为本地估计，不是确认账单。Up后脑无脸、内耳金色或牙；Down有正常/张口愤怒/垂舌死亡表情。

14透明分件。本地修Up两张脚的前趾分缝为后跟，仅重绘末端区域；填补4个封闭alpha像素。Up三种表情共用纯后脑。尾根圆垫通过显式source rectangles排除，实测Up上端根pivot、Down下端根pivot；四肢肩髋根内嵌，头盖住颈帽。离线初稿露出肩髋圆垫和尾垫，已否决保留为offline_rig_proof_rejected_r00.png。

R01两轮168/0、599张真实PNG，但实看四方向/strip后正背头身偏小，视觉否决，完整旧运行保留；未声称全面审完R01媒体。R02仅正背布局全部位置及宽高围绕地面基线等比放大1.6，保持原root、源图、侧向曲线/PPtr/事件/时长/loop、业务数值。短幅对角步态、头躯轻微错相、尾摆与原生攻击/死亡事件沿用现系统；无共享C#改动。

最终21路径全量指纹为 `Warg/repair_proportions_r02/manifest.json` 的final_files，已与生产逐项核对。Warg battle SHA `{binding['installed_files']['Assets/Prefabs/Enemy/Enemy_Warg.prefab']}`。不删除installed_manifest，不用初版stage/Build覆盖最终R02比例。最终staged三文件与production SHA一致。

## 最终运行和实际视觉审阅

runtime_r02 84 PASS/0 FAIL、302帧，runtime_updeath_r02 84/0、299帧，合计168/0、601张真实Unity PNG。记录SHA分别 `{final['runtime'][0]['records_sha256']}` 与 `{final['runtime'][1]['records_sha256']}`。两轮回到Boot；第二轮指定Up死亡。

实际审阅：两轮四方向图、strip、10张时序/步态/愤怒板（256采样位、228张不同真实源PNG）、6张原尺寸PNG、离线无裁切R02 proof、最终12个GIF各5个编码帧样本共60帧。观察到后脑无脸/后跟无前趾、正面金眼獠牙、愤怒张口，四足/颈尾相连；短步尾摆，攻击前压回收，白闪结束，Down垂舌与Up纯后脑死亡侧倾缩小淡出、同实例复用正常，后续左右转向无倒置，暂停/恢复/倍速有时序证据。GIF没有实时播放、没有逐GIF全帧审阅。时序板顶部裁剪由原PNG核对为审阅板裁剪；原HP位置在部分正背姿态覆盖耳/后脑或尾尖，按保护约束保留，记录为展示限制。待用户美术批准。

record已执行。AllGIF实时{final['global_archive_count']}，Warg24项（R02当前12、R01历史12），全部源/归档SHA一致。核心证据：
- Warg/final_validation_20261028.json
- Warg/version_binding_final_20261028.json
- Warg/scope_incremental_final_20261028.json
- Warg/visual_review_r02_20261028/review.json
- Warg/gif_archive_verification_20261028.json
- Warg/record_note_utf8.txt

## 增量和Unity释放

{scope['baseline_files']}→{scope['current_files']}文件路径并集，22路径变化、20新增。仅本角色battle/Directions含meta，另单列未修改ReporterEditor的Play build_info时间戳。incremental unexpected0，原组件语义通过，除允许battle改动外其余5保护不漂移，共享C#、其他角色、配置表和源资源无增量变化。旧global291 unexpected/6其他角色语义失败是历史审计，未重跑或声称全局PASS。

Unity现场动态custom-tools/instances明确选MyTowerGame，8088 /E:/MyTowerGame /2022.3.62f3c1。释放：单一clean Boot、非Play，compile/reload/update/test/review/balance/recording/manual均idle，failed=false/error0/ready=true/external_changes_dirty=false。空闲缓存时间戳曾stale，调用现有ForceUpdate重新采集事实，没有改插件或伪造状态。释放证据 `{rel(release_path)}`。本轮无桌面控制，未改Play外来任务。

## 下一唯一Wasp

16项未完成，PossessedWarg旧blocked/uncertain完整保留；其余按index，Wasp104 not_started，当前只有reference，无anatomy/请求/raw/stage/install/runtime。六保护与reference一致，详见 `{rel(assessment)}`。源prefab `{t['source']}`，图集 `{t['atlas']}`，battle `{t['battle']}`。下一聊天需自行审完整图、层级、原动画/翼槽/PPtr/事件/时长、飞行和对象池生命周期，按Wasp自身解剖处理翼根与飞行。不要照搬Warg四足或假定其他虫的翼数。

新token `{token}`。执行入口 `{rel(prompt_path)}` 与NEXT_ENEMY_TASK。handoff_ready不许生产操作；create明确成功登记active才由新owner接手。只创建一个fresh local后继，无fork/子代理/计时器/模型覆盖。父线程登记完成后停止所有工作区写入。
'''
handoff.write_text(summary,encoding='utf-8')
prompt=f'''在 E:/MyTowerGame 继续敌人四方向串行续作。本聊天唯一角色 Wasp(index 104)，用户已授权的唯一全新 local 后继，不是并行任务。

唯一 dispatch token：{token}
父线程：{OWNER}

开工完整读取并同步当前磁盘：
1. E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt。
2. E:/MyTowerGame/Docs/EnemyDirectionReview/README.md。
3. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md。
4. 同目录 CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json。
5. 同目录standing_network_recovery_authorization_20261028.json、TreasureChest/standing_recovery_application_20261028.json；核对原授权证据，不改写旧uncertain/收费结果，不无限重试。
6. E:/MyTowerGame/{rel(handoff)}。
7. E:/MyTowerGame/{rel(assessment)}。
8. Wasp/reference/source_structure.json 与完整源参考。

只有chain.state=active、owner_thread_id为本新线程、current_character=Wasp、dispatch_token与上方一致后，才可操作Unity、生产或付费生成。父线程先handoff_ready；此阶段只读等待登记，不超时抢锁。父创建成功登记后停止工作区写入。开工检查新出现的请求/安装/运行文件，恢复已有阶段，避免重复prepare、付费或安装。

当前92/108。Warg103已record、最终R02、completed_pending_user_art_review、user_approved=false；Wasp104 not_started，仅reference，无anatomy/generation/raw/staged/install/runtime。assessment/prompt/dispatch仅调度文档，不代表已开始美术。PossessedWarg旧blocked与结果不明的付费请求保留，不自动重发、不伪称完成。

Wasp源路径：
- {t['battle']}
- {t['source']}
- {t['atlas']}
metadata及reference六保护已匹配，开工仍现场核对。读完整图集、prefab层级和绑定、Controller依赖、原float/PPtr/事件/时长/loop、战斗飞行与复用生命周期。自行制定Wasp解剖、翼数、翼根、遮挡和连续振翅，不套用其他虫或四足模板。改动前建立本角色Assets/Packages/ProjectSettings/Luban全路径SHA增量基线及六保护指纹，以当前磁盘含用户改动为准，不以Git HEAD为基线。

逐阶段执行原prompt：审原图/解剖→按需逐方向AIHub并实看raw→透明分件/切片/pivot/PPU/layout与离线proof审阅→六保护及Unity空闲复核→仅Wasp安装Builder/Verify→两轮真实Unity Play各84项→分批实际看PNG/时序板/GIF并准确记抽样→最终生产与运行版本哈希绑定→UTF-8 note/record→GIF归档SHA→路径并集增量和原组件语义审计。程序PASS不能替代美术检查，视觉失败必须修复重测并保留旧revision。原始请求和成功raw复用；不确定结果先查进程/落盘/返回，再决定是否有授权的新revision，不盲重发。

AIHub https://aihub.dog/v1，gpt-image-2、medium、1536x1024、n1，复用现有generate_character.ps1/generate.mjs，密钥运行时读取、仅发aihub.dog、结束清理、不输出密钥/base64。遵守既有有界网络恢复授权及新intent/revision护栏；Usage本地估算不当已确认账单。

保护源图集/源prefab/GUID/root、HP、碰撞、锚点、移动战斗参数与原侧面动画曲线/PPtr/事件/时长/loop。新增正背必须是真正正背，Up无正面脸，飞行结构连贯，不能漂浮断翼或地面阴影。保持原生攻击、受击/致死白闪、全身死亡淡出缩小、自动回收与同实例复用、暂停/1x2x3x。使用现有方向系统，不增逐帧材料、层级查找或另一套方向系统。不改其他角色/共享C#；若确有共享缺陷，先明确依赖及最小范围并按原prompt编译回归。禁止改配置表、Assets/ConfigJson、Assets/Gen、声音；不要Git pull/reset/clean/commit、构建部署、fork、子代理、并行角色、计时器、模型/推理覆盖或长期memory更新。

正确Unity端点 http://127.0.0.1:8088/mcp，版本2022.3.62f3c1。复用Remaining_20261024/mcp_call.py，每次动态读custom-tools/instances、明确set当前MyTowerGame完整ID、project/info核E:/MyTowerGame及版本。8082当前另一工程，8080 CatchFish；根AGENTS的FreedomTower/D盘/8082为历史错配，当前任务覆盖。重连/域重载后重核。MCP离线按工程规则自主恢复，失败说明具体开启步骤，不能假称验收通过。默认Unity MCP；电脑/桌面控制须先弹对话确认，本提示不授权桌面。仅停本任务授权测试Play，不强停外来任务。

本任务授权为完成角色进行两轮真实Play测试。最终Unity须单一clean Boot、非Play、全部测试/录像/手动模拟/编译/重载/更新idle、failed=false、error0、ready=true，不清日志。C#若改必须正确工程refresh/compile/state/error闭环，编译期间不继续改代码。空闲缓存stale须取新事实，不能把旧resource或端口监听当成功。

前任Warg最终证据：Warg/final_validation_20261028.json及version_binding/scope/visual_review_r02/gif_archive。最终repair_proportions_r02/manifest.json有完整21路径，R01体量不足已否决，R02保持脚跟本地修补与尾根pivot并正背整体1.6。runtime_r02 302帧与runtime_updeath_r02 299帧，各84/0，共168/0、601真实PNG。实际审10板256采样位/228不同PNG、6原PNG、两轮四向/strip、12GIF各5编码帧；未实时播放或全GIF逐帧。AllGIF{final['global_archive_count']}，Warg24（最终12、历史12），源/归档SHA一致。5385→5405路径并集22变化20新增、unexpected0、本角色语义与源保护/共享C#无漂移；Reporter build_info单列，历史global291 unexpected及6其他角色语义失败没有重跑或称全局通过。原HP部分遮住背头/尾尖，保护原UI位置并记录，非审阅板裁剪。不要重跑前任Build或修改前任。

最终状态只能completed_pending_user_art_review、user_approved=false，不替用户批准。完成Wasp全部关卡或记录真实阻断并释放Unity后，重新评估实时队列（优先可恢复已开始，否则最低index非blocked），完整写交接、更新README/原prompt实时块/NEXT/progress。用户已授权“完成一个→总结/更新prompt→唯一全新local后继”循环，不逐角色再询问。先chain handoff_ready，再list_projects现场确认E:/MyTowerGame项目并create_thread唯一fresh local、不传model/thinking、不fork。新聊天等待active。create明确成功保存实际响应并把newowner/token active作为父最终写入；之后停止所有工作区写入，做一次有界wait_threads并报告真实created-thread。创建结果不明先查列表，不重复创建；失败保留可执行交接并如实说明。循环到108全部有效完成或只剩真实阻断，不绕过阻断付费试探。
'''
prompt_path.write_text(prompt,encoding='utf-8');(H/'NEXT_ENEMY_TASK.md').write_text('# 下一唯一角色 Wasp(index 104)\n\n'+prompt,encoding='utf-8')
live_text=f"{now().strftime('%Y-%m-%d')} Warg103已record，92/108，completed_pending_user_art_review、user_approved=false。最终R02，14透明分件，Up后跟局部修补、4封闭alpha像素修补、尾根显式裁切及pivot。R01正背头身偏小已否决保留；R02仅正背围绕地面基线整体1.6，无共享C#改动。runtime_r02 302帧/runtime_updeath_r02 299帧，各84/0、共168/0和601真实PNG。实看两轮四向/strip、10板256采样位/228不同PNG、6原PNG、12GIF各5编码帧；非实时播放或全GIF逐帧。原HP部分覆盖背头/尾尖保留，板顶部裁剪由原PNG核对。AllGIF{final['global_archive_count']}，Warg24含12当前/12历史，SHA全部匹配。5385→5405路径并集22变化20新增、unexpected0、原组件语义通过、其余5保护及共享C#无漂移；Reporter时间戳单列。旧global291unexpected/6历史语义失败非本轮增量，未重跑或称全局PASS。Unity8088正确身份，Boot单场景clean、非Play、全部空闲、failed=false/error0/ready=true/external_changes_dirty=false。最终Warg/final_validation_20261028.json及绑定/范围/视觉/归档；交接{rel(handoff)}。下一唯一Wasp104 not_started，token={token}。PossessedWarg旧blocked/uncertain保留。"
for p,begin,end in [(H.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),(H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    text=p.read_text(encoding='utf-8-sig');pattern=re.escape(begin)+r'.*?'+re.escape(end);assert len(re.findall(pattern,text,re.S))==1
    text=re.sub(pattern,lambda _:begin+'\n'+live_text+'\n'+end,text,flags=re.S)
    if p.name=='README.md':text=text.replace('2026-10-28 本轮当前清单为 1474 个文件',now().strftime('%Y-%m-%d')+' 本轮当前清单为 '+str(final['global_archive_count'])+' 个文件')
    p.write_text(text,encoding='utf-8')
done['handoff_file']=handoff.relative_to(H).as_posix();progress.update(current='Wasp',updated_at=now().isoformat());write(H/'progress.json',progress)
dispatch={'prepared_at':now().isoformat(),'created':False,'parent_thread_id':OWNER,'character':'Wasp','character_index':104,'dispatch_token':token,'project_root':'E:/MyTowerGame','project_id':PROJECT,'handoff_file':rel(handoff),'handoff_sha256':sha(handoff),'assessment_file':rel(assessment),'assessment_sha256':sha(assessment),'unity_release_file':rel(release_path),'unity_release_sha256':sha(release_path),'prompt_file':rel(prompt_path),'prompt_sha256':sha(prompt_path),'next_task_file':rel(H/'NEXT_ENEMY_TASK.md'),'next_task_sha256':sha(H/'NEXT_ENEMY_TASK.md'),'progress_sha256':sha(H/'progress.json'),'response_file':rel(W/'successor_creation_response_20261028.json'),'project_association_confirmed':False}
write(dispatch_path,dispatch)
assert not any(r.get('character')=='Warg' for r in chain.get('completed_handoffs',[]))
chain.setdefault('completed_handoffs',[]).append({'character':'Warg','status':'completed_pending_user_art_review','current_stage':'recorded_pending_user_art_review','closed_at':now().isoformat(),'owner_thread_id':OWNER,'dispatch_token':OLD,'handoff_file':rel(handoff),'final_evidence':rel(D/'final_validation_20261028.json')})
chain.update(state='handoff_ready',parent_thread_id=OWNER,owner_thread_id=OWNER,owner_host_id='local',current_character='Wasp',dispatch_token=token,character_status_at_handoff='not_started',completed_count_snapshot=92,previous_handoff_file=chain.get('last_handoff_file'),last_handoff_file=rel(handoff),handoff_sha256=sha(handoff),successor_assessment=rel(assessment),prepared_dispatch_file=rel(dispatch_path),unity_release_file=rel(release_path),progress_sha256_at_handoff=sha(H/'progress.json'),handoff_ready_at=now().isoformat(),updated_at=now().isoformat(),successor_created=False,dispatch_ready_for='Wasp',current_stage='handoff_ready_reference_only',last_stage_evidence=rel(D/'final_validation_20261028.json'),resume_character='Wasp',resume_stage='Inspect Wasp anatomy, wing slots and native flight, establish its own baseline',current_blocked=False,blocked_reason=None,stop_reason=None,stopped_at=None,ownership_transfer_note='Await one fresh local Wasp child. No production/Unity before successful active registration.')
write(H/'conversation_chain.json',chain)
print(json.dumps({'state':'handoff_ready','next_character':'Wasp','token':token,'handoff_file':rel(handoff),'prompt_file':rel(prompt_path),'dispatch_file':rel(dispatch_path)},ensure_ascii=False))
