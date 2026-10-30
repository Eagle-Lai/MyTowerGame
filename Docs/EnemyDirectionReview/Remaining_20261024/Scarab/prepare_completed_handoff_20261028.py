"""Persist complete review and one successor intent, then release production ownership."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re, subprocess, sys, uuid

D=Path(__file__).resolve().parent
HERE=D.parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
from mcp_call import Client
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
def now(): return datetime.now(timezone(timedelta(hours=8)))
def unwrap(v): return v.get('structuredContent') or json.loads(v['content'][0]['text'])

chain=read(HERE/'conversation_chain.json')
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']=='Scarab' and chain['dispatch_token']=='sabretoothtiger-to-scarab-a14cefa3c87b4f9187c899d88ead8c0c'
assert not (D/'successor_dispatch_intent_20261028.json').exists(), 'Inspect existing dispatch before retry'
progress=read(HERE/'progress.json')
item=next(i for i in progress['items'] if i['name']=='Scarab')
assert progress['completed_count']==82 and item['status']=='completed_pending_user_art_review' and not item['user_approved']
binding=read(D/'version_binding_final_20261028.json')
assert all(sha(D/p)==s.upper() for p,s in binding['files'].items())
assert all(sha(ROOT/p)==s.upper() for p,s in binding['installed_files'].items())
gifs=read(D/'gif_archive_verification_20261028.json')
assert gifs['total']==read(HERE.parent/'AllGIF/manifest.json')['count'] and gifs['current_count']==12 and gifs['character_count']==24
scope=read(D/'scope_incremental_final_20261028.json')
assert scope['unexpected_incremental']==[] and scope['new_unexpected_vs_preexisting_legacy']==[] and scope['new_semantic_failures']=={}
assert not any((ROOT/p).stat().st_mtime>now().timestamp()+60 for p in binding['installed_files'])

next_name='ScarabMounted'
next_item=next(i for i in progress['items'] if i['name']==next_name)
assert next_item['index']==93 and next_item['status']=='blocked'
next_dir=HERE/next_name
old=read(next_dir/'blocked_generation_20261026.json')
protected=old['production_snapshot']['protected_six_unchanged']
drift=[p for p,s in protected.items() if sha(ROOT/p)!=s.upper()]
assert not drift,drift
up=read(next_dir/'generation/Up/result.json')
assert up['status']==402 and up['error']['code']=='insufficient_balance'
assert not (next_dir/'generation/Up/raw.png').exists()
assert not list((next_dir/'generation/Down').rglob('request.json'))
assert not list(next_dir.rglob('installed_manifest.json'))
assert len(list(next_dir.rglob('request.json')))==1, 'Re-evaluate new successor attempts'
ps='Get-CimInstance Win32_Process | Where-Object { ($_.Name -in @(\'python.exe\',\'node.exe\',\'Unity.exe\')) -and ($_.CommandLine -match \'MyTowerGame|generate.mjs|runtime_runner|balance_pipeline\') } | Select-Object Name,ProcessId,@{Name=\'is_generation\';Expression={$_.CommandLine -match \'generate.mjs\'}},@{Name=\'is_runtime\';Expression={$_.CommandLine -match \'runtime_runner|start_runtime\'}},@{Name=\'is_balance\';Expression={$_.CommandLine -match \'balance_pipeline\'}} | ConvertTo-Json -Compress'
process_result=subprocess.run(['powershell.exe','-NoProfile','-Command',ps],capture_output=True,text=True,encoding='utf-8',check=True)
processes=json.loads(process_result.stdout)
if isinstance(processes,dict): processes=[processes]
assert not any(p['is_generation'] or p['is_runtime'] or p['is_balance'] for p in processes), processes
stamp=now().strftime('%Y%m%d_%H%M%S')
assessment_path=D/('successor_recovery_assessment_'+stamp+'.json')
assessment=dict(observed_at=now().isoformat(),candidate=next_name,index=93,
    unfinished=[dict(index=i['index'],name=i['name'],status=i['status']) for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved']],
    existing_state='Reference and both prompts prepared. Original Up explicit HTTP402; Down not requested. No stage/install/runtime.',
    preserved_evidence={p.relative_to(next_dir).as_posix():sha(p) for p in [next_dir/'anatomy_plan.json',next_dir/'blocked_generation_20261026.json',next_dir/'generation/Up/request.json',next_dir/'generation/Up/result.json',next_dir/'generation/Up/prompt.txt',next_dir/'generation/Down/prompt.txt']},
    protected_six=protected,protected_drift=drift,process_snapshot=processes,
    recent_same_service_success=[dict(direction=direction,result='Scarab/'+path,result_sha256=sha(D/path),**read(D/path)) for direction,path in [('Up','generation/Up/revision_01/result.json'),('Down','generation/Down/revision_02/result.json')]],
    recovery_policy='Recent two same-service HTTP200 results support one bounded explicit-failure recovery assessment, not a guarantee of account balance. Preserve old 402 and use a fresh revision/intent, Up first; successful reviewed Up before Down. No paid request made by this handoff.',
    network_recovery='Latest standing_network_recovery_authorization_20261028.json covers the same transient ECONNRESET/TLS case with preserved originals and bounded fresh revisions; no repeated confirmation. Auth/balance failures require evidence, not endless retries.',
    source_binding='Mounted source body/legs use its atlas; battle Head originally shares Scarab atlas. Preserve original PPtr and events. One saddle, no rider, six legs, no tail/wings.',
    same_family_runtime_warning='Scarab original Death Body z reaches -180; source Walk lacks Body rotation. Scarab r01 side view stayed inverted after reuse despite 168 PASS. Its own copied Walk gained only missing Body Euler 0 reset tracks, all source curves/events/timing retained, and r02 fixed it. Inspect Mounted for the same issue; use only its own clip if needed, do not edit Scarab or shared source. See Scarab/side_reuse_repair_r02/repair.json and repair_side_reuse_20261028.py.',
    PossessedWarg='Old Down still uncertain. Do not resend or reclassify.',SabretoothTiger='Old Down revision_01 remains uncertain; its one-off $0.07 authorization is consumed.')
write(assessment_path,assessment)

c=Client();project=c.identity()
errors=unwrap(c.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
cache_refresh=unwrap(c.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"Scarab_handoff_live_state_read"});return true;')))
assert cache_refresh['success'] and cache_refresh['data']['result'] is True
state=c.resource('mcpforunity://editor/state')
probe=unwrap(c.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))
assert probe['success'];observed=probe['data']['result']
assert not any(v for k,v in observed.items() if k!='scene') and observed['scene']=='Assets/Scenes/Boot.unity',observed
s=state['data'];assert not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']
assert errors['success'] and errors['data']==[]
release_path=D/('unity_release_completed_'+stamp+'.json')
write(release_path,dict(observed_at=now().isoformat(),project=project,state=state,errors=errors,probe=probe,cache_refresh=cache_refresh,protocol_history=c.history,
    cache_note='Installed plugin deliberately does not rebuild snapshot while idle; ForceUpdate only refreshed actual snapshot via MCP, no readiness flags, package code or editor state changed. No desktop control.'))

token='scarab-to-scarabmounted-'+uuid.uuid4().hex
handoff_path=HERE/'conversation_handoffs'/(stamp+'_Scarab_completed.md')
handoff=f'''# Scarab 完成与 ScarabMounted 唯一串行交接

- 时间：{now().isoformat()}；实际工程 E:/MyTowerGame，Unity2022.3.62f3c1，unityMCP / HTTP Local8082。根AGENTS中FreedomTower_1/D盘标题为旧文案，不改规则、不转工程。
- Scarab(index92)已安装、Verify、两轮最终真实Play、实际PNG视觉审阅、record和GIF归档；总进度82/108，completed_pending_user_art_review，user_approved=false。
- Up复用revision_01 HTTP200并采用local_raster_revision_01去除错误背面口器；原图保留。Down旧revision_01仍uncertain，未推定未收费、未改分类，原request/console/uncertain哈希已核对。最新用户明确允许同类网络问题静默继续，按standing_network_recovery_authorization_20261028.json在新revision_02只发一次，HTTP200、1446258 bytes。无新付费需求，未查实际账单，不声称具体费用。
- 14分件、放大头部和触角、修正六足根部pivot与三足错相；Up无眼口，Down三表情。后脑下缘补色简洁且有色调过渡，组合大部分被胸甲遮挡；正背更接近轴向俯视，保留给用户美术判断。
- 初轮runtime_r01/runtime_updeath_r01虽168/0、692帧，实际审阅发现死亡后同实例复用的侧身倒置，已内部否决，旧证据不删。源Death把Body z翻到-180而源/copied Walk无Body旋转绑定。side_reuse_repair_r02仅给Scarab自己的Walk副本添加Body x/y/z常量0，不改已有原侧图float/PPtr曲线、事件、时长/loop、共享源动画或C#。Verify再次PASS。全Build会重新生成副本，今后若重建须保留此明确修复；不能用旧安装清单覆盖。
- 最终runtime_r02与runtime_updeath_r02各84 PASS/0 FAIL、346帧，合计168/0、692张真实Unity帧。实际查看最终四方向、strip和10张时序/步态/愤怒板，256采样位、227张不同实际帧。修复后两轮ContinuousTurns左右侧身均直立，头/甲壳/六足连接完整，触角不碰血条；白闪结束、死亡全身倾斜淡出、回收同实例复用恢复、暂停/1x/2x/3x有帧及检查支持；抽样未见地面阴影。未播放GIF全片、未逐张审完692帧。
- 证据：Scarab/installed_manifest.json、side_reuse_repair_r02/repair.json、visual_review_final_r02_20261028/review.json、record_note_utf8.txt、version_binding_final_20261028.json。最终绑定全部实际PNG、records、checks、媒体、所选原图/修补与安装/暂存哈希，漂移0。
- 5178文件前基线并集22项变化、20项新增，生产只当前Scarab战斗prefab和Directions(含目录meta)，Reporter未改代码的Play时间戳单独归因；本角色语义PASS、六保护除授权battle外无drift、unexpected_incremental=[]。全局历史291unexpected及6其他角色语义失败(MeatBug/Monkey/MosquitoParasite/Pig/Piggy/Porky)仍保留，新增0，不称全局PASS。范围证据Scarab/scope_incremental_final_20261028.json及scope_Scarab_20261028_final.json。
- AllGIF实时{gifs['total']}项，Scarab24项，12个r02为当前审核版本、12个r01为历史；全部来源/归档SHA一致，见Scarab/gif_archive_verification_20261028.json。
- Unity刚经动态实例/路径/版本重核，已回Boot、非Play、全部场景非dirty，编译/更新/录像/审阅/手动模拟无占用、scriptCompilationFailed=false、错误0。释放：{release_path.relative_to(ROOT).as_posix()}。没有桌面控制、共享C#改动、表/ConfigJson/Gen/音频改动、构建部署或Git同步提交。

## 下一唯一角色 ScarabMounted(index93)

dispatch_token：`{token}`。候选评估：{assessment_path.relative_to(ROOT).as_posix()}。先等chain.active且owner为新聊天、token/current匹配才能操作生产/Unity。

旧Up明确HTTP402 insufficient_balance，无raw；Down从未请求。anatomy/reference/prompt已备，不重跑prepare、不覆盖旧request/result。六保护指纹现场无drift，无生成/运行/平衡进程占用。Scarab最新Up/Down同服务HTTP200支持一次有界恢复评估，不保证余额或上游持续可用。后继先重看源参考/当前进程及证据，按明确失败恢复路径使用新的revision与intent，先Up单次正式请求，成功并实际审图才继续Down；网络故障按最新standing授权有界恢复，不重复弹确认，鉴权/余额或限额耗尽则真实记录阻断，避免盲目付费探针。

解剖为橄榄赭色甲壳、双触角、橙眼、六足、唯一棕色鞍、无骑手/尾/翅。保持旧battle Head共享Scarab atlas原绑定，不因美术任务修原PPtr。注意同Scarab家族的死亡复用Body倒置；先读本角色源曲线，如需修只给本角色自有Walk缺失旋转增加reset，保留所有已有曲线/事件/时长，再实际运行确认。不得改Scarab或共享动画。

PossessedWarg旧Down仍uncertain，不重发、不改分类；SabretoothTiger旧Down仍uncertain，其一次$0.07专用授权已消耗。没有其他角色生产并行。用户电脑控制限制仍保留：优先目标Unity MCP，如确需桌面控制必须先弹对话确认。

完成或真实阻断后按原prompt及CONTINUATION_PROTOCOL_20261026.md写新完整交接，更新LIVE/NEXT/progress，安全交回Unity，创建唯一全新本地后继。不是fork，不子代理，不改模型，不计时器。创建成功后旧聊天登记新owner/token并立即停止全部工作区/链写入。
'''
handoff_path.write_text(handoff,encoding='utf-8')
live=f'2026-10-28 Scarab(index92)已完成：82/108，最终side_reuse_repair_r02、runtime_r02/runtime_updeath_r02各84/0共692真实帧。实际审四方向/strip及10时序板(256采样位/227不同帧)，初轮复用侧身倒置已修并保留否决证据。record完成，仅completed_pending_user_art_review、user_approved=false。AllGIF{gifs["total"]}，Scarab24含12当前版且哈希一致。5178文件并集22变化20新增，增量unexpected0、安装/六保护/语义通过；全局历史291unexpected/6其他角色语义失败保留新增0。Down旧revision_01仍uncertain，最新同类网络故障静默恢复授权下revision_02单次HTTP200。Unity已安全释放Boot非Play、全场景非dirty、空闲、编译失败false、错误0；未用桌面控制。下一唯一ScarabMounted93，旧Up402、Down未请求，按新评估有界恢复，不重prepare。完整交接：{handoff_path.relative_to(ROOT).as_posix()}。所有权以实时chain为准，电脑控制仍须先对话确认。'
prompt_path=HERE/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md'
prompt=prompt_path.read_text(encoding='utf-8')
prompt,count=re.subn(r'(?<=<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->).*?(?=<!-- ENEMY_SERIAL_LIVE_STATE_END -->)','\n'+live+'\n',prompt,flags=re.S)
assert count==1;prompt_path.write_text(prompt,encoding='utf-8')
next_text=f'''# 下一唯一角色：ScarabMounted(index93)

在E:/MyTowerGame串行继续。父聊天{chain['owner_thread_id']}已完成Scarab，进度82/108，待用户美术审核，未获批准。唯一dispatch_token：`{token}`。

## 开工必读与所有权

根AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、实时conversation_chain.json/progress.json、{handoff_path.relative_to(ROOT).as_posix()}、{assessment_path.relative_to(ROOT).as_posix()}和standing_network_recovery_authorization_20261028.json。

只有chain.state=active、owner是本新聊天ID、dispatch_token严格匹配、current_character=ScarabMounted后才可操作Unity/生产。handoff_ready期间保持只读；不靠超时抢锁。只处理这一角色，不fork/子代理/并行角色。根AGENTS旧FreedomTower_1/D盘路径是已记录差异，不改规则、不转工程。

## 恢复现有阶段

ScarabMounted/anatomy_plan.json、reference和两方向prompt已备。读blocked_generation_20261026.json及generation/Up/request.json/result.json：原Up明确HTTP402 insufficient_balance，无raw；Down未请求。本次评估六保护无漂移，无stage/install/runtime；不重跑prepare、不删旧请求、不直接重复旧输出路径。重新核对原图集、完整源/战斗prefab和processes。Scarab最新Up revision_01及Down revision_02同服务HTTP200，可支持一次有界恢复评估，不保证上游余额持续可用。用generate_character.ps1 / generate.mjs已有明确失败恢复入口、新revision和intent，先预检、再Up一次正式请求；成功并实际审图后才做Down。

用户最新直接授权“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”已写standing_network_recovery_authorization_20261028.json。同类fetch failed/ECONNRESET建立TLS前失败保留原uncertain，以唯一新revision及intent有界恢复；每方向最多2次新增恢复为执行保守上限，不是用户指定金额。不要重复弹同类确认。遇鉴权/余额/上游无账户错误或限额耗尽要记录真实阻断，不无界重发、不拿其他角色作付费探针。成功原图一律复用。此网络授权不扩大成电脑控制许可：只用目标Unity MCP；必要桌面操作仍先弹对话确认。

本角色是六足甲虫：双长带纹触角、橙镜片眼、象牙色口器、橄榄赭色甲壳、三对奶油色关节腿、唯一棕皮鞍，无骑手/尾/翅。Up后脑无眼口，Down三个头状态均带触角，鞍仅在Body一次。旧battle Head共享Scarab atlas为源绑定事实，保持原PPtr/事件，不借此任务修它。

Scarab本轮发现同家族Death把Body z翻到-180而Walk无Body旋转，死亡复用后侧身倒置。技术168/0不能发现；本角色必须针对性审阅。参考Scarab/side_reuse_repair_r02/repair.json和repair_side_reuse_20261028.py，如同样缺失，仅给Mounted自己的Walk副本增加Body三轴归零常量轨，不动已有源曲线/事件/时长/loop、共享源或其他角色；最终再做两轮真实Play与实际时序审阅。

## Unity与完整完成标准

Unity2022.3.62f3c1、unityMCP HTTP Local http://127.0.0.1:8082/mcp。每次动态读custom-tools/instances，选现场MyTowerGame完整ID，再核对project/info=E:/MyTowerGame和ProjectVersion。可复用mcp_call.py直接HTTP客户端；注入资源路由曾只列FishTestGame，不向错误工程操作。不得抢8080或杀共享服务。若editor/state仅stale_status，当前插件无状态变化时不更新缓存；可按Scarab/finalize_recovery_20261028.py中MCP短反射调用ForceUpdate重建真实snapshot，绝不篡改ready/compilation flags，不修改插件。操作前读取error并核对全部场景dirty、Play/编译/录像/review/manual占用。

本任务已授权两轮逐角色Play，但不强停他人任务、不覆盖未保存场景。完整做实际原图审阅、透明度/切片/足尖与pivot/连接离线审阅、单角色安装Verify、两轮各84真实Play、实际媒体审阅、前后并集范围审计和版本绑定、UTF8实际备注record、GIF归档。原始raw/失败请求/运行帧完整保留，1-2图分次查看。只completed_pending_user_art_review，user_approved=false；禁止用技术PASS替代视觉判断。已有安装清单时走返修新revision，不删除重装；发现问题先修再重测。

以新开工前Assets/Packages/ProjectSettings/Luban并集基线为准，保留新增/删除与Reporter自动时间戳归因；六保护除授权battle外不动。全局既有291unexpected和6其他角色语义失败保留，增量新增0才可据实报告，不能称全局PASS。禁止配置表、ConfigJson/Gen、音频、其他角色、共享C#改动；不pull/reset/clean/checkout/commit/push，不构建部署。

PossessedWarg旧Down仍uncertain，不重发；SabretoothTiger旧Down仍uncertain，其一次$0.07专用授权已消耗；Scarab旧Down uncertain不重新分类。不要操作这些角色。

完成或真实阻断后写新的完整交接、更新README/LIVE/NEXT/progress，确认Unity安全交还Boot、非Play、全部场景非dirty且空闲，再按CONTINUATION_PROTOCOL主动创建唯一全新本地后继；动态list_projects，target.environment=local，不指定模型，不fork/子代理/计时器。create明确成功后登记新thread/host/token，旧聊天立即停止全部工作区和chain写入，只做一次有界wait确认启动。只剩真实阻断才停止，不等用户逐角色确认。
'''
(HERE/'NEXT_ENEMY_TASK.md').write_text(next_text,encoding='utf-8')
readme=HERE.parent/'README.md';content=readme.read_text(encoding='utf-8')
content=content.replace('本轮当前清单为 1246 个文件',f'本轮当前清单为 {gifs["total"]} 个文件')
live_marker='<!-- ENEMY_README_LIVE_BEGIN -->'
readme_live='\n'+live_marker+'\n'+live+'\n<!-- ENEMY_README_LIVE_END -->\n'
if live_marker in content:
    content=re.sub(r'\n<!-- ENEMY_README_LIVE_BEGIN -->.*?<!-- ENEMY_README_LIVE_END -->\n',readme_live,content,flags=re.S)
else:
    first,rest=content.split('\n',1);content=first+'\n'+readme_live+rest
content+='\n'+live+'\n';readme.write_text(content,encoding='utf-8')
progress.update(current=next_name,status='in_progress',updated_at=now().isoformat());write(HERE/'progress.json',progress)
chain.setdefault('stage_history',[]).append(dict(character='Scarab',status=item['status'],current_stage='recorded_pending_user_art_review',closed_at=now().isoformat(),owner_thread_id=chain['owner_thread_id'],dispatch_token=chain['dispatch_token'],handoff_file=handoff_path.relative_to(ROOT).as_posix(),final_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Scarab/final_validation_20261028.json'))
chain.update(state='handoff_ready',parent_thread_id=chain['owner_thread_id'],dispatch_token=token,current_character=next_name,dispatch_ready_for=next_name,
    character_status_at_handoff='blocked_explicit_http_failure_recovery_eligible',current_stage='ScarabMounted_explicit_402_recovery_pending_owner',resume_character=next_name,
    resume_stage='Read preserved Mounted evidence and assess one bounded fresh Up request before full single-character workflow',completed_count_snapshot=82,
    previous_handoff_file=chain['last_handoff_file'],last_handoff_file=handoff_path.relative_to(ROOT).as_posix(),unity_release_file=release_path.relative_to(ROOT).as_posix(),
    handoff_ready_at=now().isoformat(),updated_at=now().isoformat(),stopped_at=None,stop_reason=None,blocked_reason=None,current_blocked=False,successor_created=False,
    progress_sha256_at_handoff=sha(HERE/'progress.json'),ownership_transfer_note='Scarab recorded with repaired final runtime evidence, documentation persisted and Unity safely released; waiting for one fresh local Mounted successor registration.')
intent=dict(created_at=now().isoformat(),parent_thread_id=chain['parent_thread_id'],next_character=next_name,index=93,dispatch_token=token,
    handoff_file=handoff_path.relative_to(ROOT).as_posix(),assessment=assessment_path.relative_to(ROOT).as_posix(),unity_release=release_path.relative_to(ROOT).as_posix(),
    project_root='E:/MyTowerGame',project_id='935c594c-f414-48e0-bd08-ed8ba342f7fd',state='handoff_ready_pending_single_create_thread',max_successors=1)
write(D/'successor_dispatch_intent_20261028.json',intent)
write(HERE/'conversation_chain.json',chain)
assert handoff_path.read_text(encoding='utf-8')==handoff and (HERE/'NEXT_ENEMY_TASK.md').read_text(encoding='utf-8')==next_text
print(json.dumps(intent,ensure_ascii=False))
