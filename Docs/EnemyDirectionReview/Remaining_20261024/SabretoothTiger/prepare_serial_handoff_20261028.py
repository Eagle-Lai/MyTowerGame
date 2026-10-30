"""Persist safe closeout and one successor dispatch intent; no paid or production writes."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re, subprocess, sys, uuid

D=Path(__file__).resolve().parent
HERE=D.parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
from mcp_call import Client
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
def now(): return datetime.now(timezone(timedelta(hours=8)))
def unwrap(r): return r.get('structuredContent') or json.loads(r['content'][0]['text'])
chain=read(HERE/'conversation_chain.json')
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID'] and chain['current_character']=='SabretoothTiger'
assert chain['dispatch_token']=='shardlizard-to-sabretoothtiger-cffa9cb0c6fe47429c981a1e421b9a8e'
assert not (D/'successor_dispatch_intent_20261028.json').exists(), 'Do not create a second successor'
progress=read(HERE/'progress.json')
item=next(i for i in progress['items'] if i['name']=='SabretoothTiger')
assert item['status']=='completed_pending_user_art_review' and progress['completed_count']==81 and not item['user_approved']
scope=read(D/'scope_incremental_authorized_recovery_20261028.json')
assert not scope['unexpected_incremental'] and not scope['installed_asset_drift']
manifest=read(D/'installed_manifest.json')
assert all(sha(ROOT/x['path'])==x['after'].upper() for x in manifest['changes'])
visual=read(D/'visual_review_final_20261028/review.json')
assert visual['sample_slots']==256 and visual['distinct_actual_frame_samples']==229
gifs=read(D/'gif_archive_verification_20261028.json')
assert gifs['total']==1246 and gifs['current_count']==12

process_run=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(node|python)' -and $_.CommandLine -match 'generate\\.mjs|generate_character|runtime_runner' } | Select-Object ProcessId,Name,CommandLine) | ConvertTo-Json -Depth 3 -Compress"],capture_output=True,text=True,encoding='utf-8')
assert process_run.returncode==0,process_run.stderr
active=json.loads(process_run.stdout.strip() or '[]')
assert not active,active
next_name='Scarab'
candidate=next(i for i in progress['items'] if i['name']==next_name)
assert candidate['index']==92 and candidate['status']=='blocked'
prior=read(HERE/next_name/'blocked_generation_20261026.json')
protected=prior['production_snapshot']['protected_six_unchanged']
drift=[p for p,s in protected.items() if sha(ROOT/p)!=s.upper()]
assert not drift,drift
directions=[]
for direction in ['Up','Down']:
    folder=HERE/next_name/'generation'/direction
    assert not (folder/'raw.png').exists() and not (HERE/next_name/'installed_manifest.json').exists()
    assert not list(folder.glob('revision_*')), 'Inspect any newer candidate attempts before dispatch'
    request=read(folder/'request.json');result=read(folder/'result.json')
    assert result['status']==503 and result.get('error') and not result.get('bytes')
    directions.append(dict(direction=direction,request_state='explicit_http_failure',status=503,
        request=(folder/'request.json').relative_to(ROOT).as_posix(),request_sha256=sha(folder/'request.json'),
        result=(folder/'result.json').relative_to(ROOT).as_posix(),result_sha256=sha(folder/'result.json')))
successes=[]
for direction,revision in [('Up','revision_01'),('Down','revision_02')]:
    folder=D/'generation'/direction/revision
    request=read(folder/'request.json');result=read(folder/'result.json')
    assert result['status']==200 and request['endpoint']=='https://aihub.dog/v1/images/edits' and request['model']=='gpt-image-2'
    successes.append(dict(direction=direction,revision=revision,finished=result['finished'],http_status=200,
        endpoint=request['endpoint'],model=request['model'],quality=request['quality'],size=request['size'],n=request['n'],
        request=(folder/'request.json').relative_to(ROOT).as_posix(),request_sha256=sha(folder/'request.json'),
        result=(folder/'result.json').relative_to(ROOT).as_posix(),result_sha256=sha(folder/'result.json'),raw_sha256=sha(folder/'raw.png')))
stamp=now().strftime('%Y%m%d_%H%M%S')
assessment_path=D/('successor_recovery_assessment_'+stamp+'.json')
assessment=dict(observed_at=now().isoformat(),unfinished=[dict(index=i['index'],name=i['name'],status=i['status']) for i in progress['items'] if i['status']!='completed_pending_user_art_review'],
    chosen=next_name,index=92,reason='Earliest started recoverable item after unresolved PossessedWarg. Both Scarab requests failed explicitly; latest real production requests succeeded on the same service.',
    protected_six=protected,protected_drift=drift,prior_requests=directions,active_generator_or_runner_processes=active,same_service_success_evidence=successes,
    policy='The successor may assess one request per direction in fresh revisions using normal explicit-failure recovery. Recheck current service evidence, source fingerprints and processes first; Up first, stop on service failure or uncertainty. No request made by this assessment.',
    single_retry_authorization='SabretoothTiger Down-only $0.07 authorization is consumed and is not transferred or expanded.',
    PossessedWarg='Original Down result still uncertain. Do not resend or reclassify; preserve blocked status and evidence.',
    ScarabMounted='Historical Up HTTP402 remains blocked, no recovery request dispatched by this handoff.')
write(assessment_path,assessment)

c=Client();project=c.identity()
state=c.resource('mcpforunity://editor/state')
errors=unwrap(c.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};'
probe=unwrap(c.tool('execute_code',dict(action='execute',code=code)))
assert probe['success']
observed=probe['data']['result']
assert not any(v for k,v in observed.items() if k!='scene') and observed['scene']=='Assets/Scenes/Boot.unity',observed
s=state['data']
assert not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']
assert errors['success'] and errors['data']==[],errors
release_path=D/('unity_release_completed_'+stamp+'.json')
write(release_path,dict(observed_at=now().isoformat(),project=project,state=state,errors=errors,probe=probe,protocol_history=c.history))

handoff_path=HERE/'conversation_handoffs'/(stamp+'_SabretoothTiger_completed.md')
token='sabretoothtiger-to-scarab-'+uuid.uuid4().hex
text=f'''# SabretoothTiger 完成及 Scarab 唯一串行交接

- 时间：{now().isoformat()}；工程 E:/MyTowerGame，Unity 2022.3.62f3c1，MCP unityMCP / 8082。根 AGENTS 的 FreedomTower_1 路径为已记录旧文案，不改规则、不换工程。
- 当前角色 SabretoothTiger(index91) 已完成单角色安装、Verify、两轮真实 Play、实际视觉审阅、record、GIF 归档。进度81/108，completed_pending_user_art_review，user_approved=false。
- Up复用revision_01；Down经用户明确授权补发一次revision_02，HTTP200，1,579,303 bytes。用量页2026/10/28 10:54:16收费$0.070000，符合$0.07上限；这次授权已消耗。旧Down revision_01仍uncertain，原请求/意图/错误证据保留，不推定未收费。证据：authorized_down_retry_20261028.json、authorized_retry_billing_20261028.json。
- 生产仅修改 Assets/Prefabs/Enemy/Enemy_SabretoothTiger.prefab 与其 Felines/SabretoothTiger/Directions；显式切片、后跟朝向、颈肩遮挡、腿根和尾根pivot已在暂存阶段修正。没有修改C#、配置表、音频或其他角色。原生成图、原prefab/atlas及meta保留。
- 最终 installed_manifest.json 20项安装变化，指纹和暂存图/布局/切片绑定无漂移；5158文件前基线的并集变化22项，含20项新增、本角色prefab和Reporter自动时间戳。unexpected_incremental=[]、六保护中除授权战斗prefab外全部不变。本角色语义通过。全局291项历史unexpected与6个其他角色语义失败仍在，新增0，不宣称全局PASS。
- runtime_r01 84 PASS / 0 FAIL / 340帧；runtime_updeath_r01 84 PASS / 0 FAIL / 341帧，合计168/0、681帧。version_binding_final_20261028.json绑定全部实际帧与安装/暂存/媒体哈希。
- 实际查看四方向和strip、10张时序/步态/愤怒细节板，256采样位、229张不同真实帧。Up后脑无脸，后爪改闭合后跟；Down剑齿、正常/攻击/死亡可辨。头身腿尾运动中相连，远足部分被轴向身体遮挡；局部后跟绘制简洁，最终美术由用户判断。白闪结束、死亡倾倒淡出、回收复用恢复、暂停和倍速有检查及帧支持，抽样未见地面阴影。未播放GIF全片，未逐张审完681帧。
- AllGIF共1246项，SabretoothTiger 12项均当前审核版本；来源及归档SHA256一致，见gif_archive_verification_20261028.json。visual_review_final_20261028/review.json和record_note_utf8.txt为实际观察。
- Unity刚经动态实例选择和身份检查，已回Boot、非Play、全部场景非dirty、编译/更新/录像/审阅/手动模拟均无占用，scriptCompilationFailed=false、error日志0。释放证据：{release_path.relative_to(ROOT).as_posix()}。

## 下一唯一角色

Scarab(index92)，唯一dispatch_token：`{token}`。待active新owner登记后才能操作生产或Unity。

Scarab两方向旧请求均明确HTTP503、没有raw，历史证据和六保护指纹不变，没有新revision/安装；可按明确失败恢复路径评估新的有界恢复。最新SabretoothTiger Up/Down两次同服务HTTP200支持恢复机会，不保证服务持续可用。后继重新检查进程、源指纹与证据，先Up、全新revision与单次intent，失败/结果不明立即停请求；成功才继续Down及完整流程。不得重发旧请求，不把SabretoothTiger一次$0.07授权扩展到Scarab，不使用其他角色作付费探针。

PossessedWarg(index79)旧Down仍结果不明，不重发。ScarabMounted(index93)旧Up402保留，尚未恢复。余下未开始角色按实时队列，不能并发。候选评估：{assessment_path.relative_to(ROOT).as_posix()}。

## 后继要求

按 CONTINUATION_PROTOCOL_20261026.md 创建唯一全新本地聊天，不fork、不子代理、不改模型设置。create_thread结果明确成功后旧owner登记新thread/host/token并停止全部工作区及链写入。新owner先读原prompt、本交接、NEXT、chain/progress与所有相关证据；仅state=active且owner/token匹配后开工。本聊天无进一步付费或生产工作。
'''
handoff_path.write_text(text,encoding='utf-8')
live=f'2026-10-28：SabretoothTiger(index91)已完成安装、两轮真实Play168/0、681帧、实际PNG抽样审阅、record及12项当前GIF归档；进度81/108，user_approved=false。Down唯一授权补发revision_02已HTTP200，实际$0.07，授权消耗；旧revision_01仍uncertain。下一唯一Scarab(index92)，明确503旧请求可按新revision有界恢复评估；PossessedWarg结果不明不重发。完整交接：{handoff_path.relative_to(ROOT).as_posix()}。所有权与token以chain实时登记为准。'
prompt_path=HERE/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md'
prompt=prompt_path.read_text(encoding='utf-8')
prompt,count=re.subn(r'(?<=<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->).*?(?=<!-- ENEMY_SERIAL_LIVE_STATE_END -->)','\n'+live+'\n',prompt,flags=re.S)
assert count==1
prompt_path.write_text(prompt,encoding='utf-8')
next_text=f'''# 下一唯一角色：Scarab(index92)

在 E:/MyTowerGame 串行继续。父聊天 {chain['owner_thread_id']} 已完成 SabretoothTiger，进度81/108，待用户美术审核；没有用户批准。唯一dispatch_token：`{token}`。

## 必须先读

根 AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md、原执行prompt、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、实时conversation_chain.json/progress.json，以及 `{handoff_path.relative_to(ROOT).as_posix()}`、`{assessment_path.relative_to(ROOT).as_posix()}`。

根AGENTS旧FreedomTower_1路径不适用本任务；实际明确目标E:/MyTowerGame、2022.3.62f3c1、unityMCP8082。先发现完整实例ID并选择，再核对project/info。保留当前未提交修改，不pull/reset/clean/checkout/commit/push，不修改规则。

## 所有权和当前阶段

只有chain.state=active、owner为本新聊天ID、dispatch_token严格匹配上述token，且current_character=Scarab后才操作Unity/生产。handoff_ready期间保持只读；无需用户逐角色再次确认。父聊天只会创建这一个后继。不要fork、子代理或并行角色生产。

Scarab有anatomy_plan/reference及两方向prompt/request/result；2026-10-26两方向旧请求均明确HTTP503、无raw，新revision/安装/运行均不存在。先读取实际文件、原始图集及完整源/战斗prefab，重新核对六保护指纹、进程与服务恢复证据；不重跑prepare，不删除旧请求。{assessment_path.relative_to(ROOT).as_posix()}绑定现有证据。同服务最新SabretoothTiger Up revision_01和Down revision_02均真实HTTP200；可按明确失败恢复路径评估新revision_01，先Up、单次intent、预检，再一次正式请求。只在Up成功并实际审图后处理Down。若明确服务错误或结果不明，立即停止后续付费，不盲目探测。恢复评估不是成功保证。

SabretoothTiger的一次Down补发$0.07授权已消耗，仅绑定它的revision_02，不转移到其他角色。旧Down revision_01原请求仍uncertain不得更改分类。PossessedWarg旧Down仍结果不明不重发；ScarabMounted历史402保留。本聊天不操作上述角色生产。

## 完成标准

完整执行原prompt：参考和解剖、原图实际审阅、切片/透明度/足尖尾根关节离线审阅、单角色安装Verify、两轮各84真实Play、实际媒体视觉检查、范围与版本绑定、record及GIF归档。技术PASS不替代视觉检查。用户未批准时仅completed_pending_user_art_review。图片按1-2张分次查看，原始帧与付费证据留盘。现有installed_manifest时改用返修入口，不删除清单重装。

全局历史291unexpected及6个其他角色语义失败保留；只据本轮并集快照判断增量，不重置基线伪称全局PASS。不碰配置表/ConfigJson/Gen、声音、其他角色或共享C#；确需代码修改按正确MCP完成编译闭环。不构建APK、不部署设备。

完成或真实阻断后写完整新交接、更新prompt/NEXT/progress，确认Unity恢复Boot非Play、全部场景无dirty无占用，再按协议创建唯一新本地后继、登记新owner/token并停止写入。只剩真实阻断才停止，不创建后台计时器。
'''
(HERE/'NEXT_ENEMY_TASK.md').write_text(next_text,encoding='utf-8')
readme=HERE.parent/'README.md'
content=readme.read_text(encoding='utf-8').replace('本轮当前清单为 1234 个文件','本轮当前清单为 1246 个文件')
content+='\n2026-10-28 SabretoothTiger授权恢复完成：81/108。Up复用revision_01、Down用户明确授权唯一补发revision_02 HTTP200，服务用量页实际$0.07，上限符合且授权已消耗；旧Down revision_01仍uncertain保留。最终installed_manifest与局部后跟/关节/尾根修正；两轮各84 PASS/0 FAIL，共681真实帧，实际审10张时序板、256采样位/229不同帧及四方向/strip，未播放GIF全片。后跟绘制简洁、远足轴向遮挡如实记录，completed_pending_user_art_review，user_approved=false。5158文件并集22变化(20新增)，仅本角色prefab/Directions及Reporter未改代码自动时间戳，语义通过、安装暂存无drift、增量unexpected0；全局历史291unexpected/6其他角色语义失败保留、新增0。AllGIF1246，本角色12当前审核版本且哈希一致。Unity动态重核后交还Boot、非Play、全场景非dirty、空闲、编译失败false、错误0。下一唯一Scarab92，历史明确503可评估新revision恢复；PossessedWarg结果不明不重发。交接见 '+handoff_path.relative_to(HERE).as_posix()+'，所有权以chain为准。\n'
readme.write_text(content,encoding='utf-8')
progress.update(current=next_name,status='in_progress',updated_at=now().isoformat())
write(HERE/'progress.json',progress)
chain.setdefault('stage_history',[]).append(dict(character='SabretoothTiger',status=item['status'],current_stage='recorded_pending_user_art_review',closed_at=now().isoformat(),owner_thread_id=chain['owner_thread_id'],dispatch_token=chain['dispatch_token'],handoff_file=handoff_path.relative_to(ROOT).as_posix(),final_evidence='Docs/EnemyDirectionReview/Remaining_20261024/SabretoothTiger/final_validation_20261028.json'))
chain['historical_stop_before_authorized_recovery']={k:chain.get(k) for k in ['stopped_at','stop_reason','blocked_reason','recovery_file']}
chain.update(state='handoff_ready',parent_thread_id=chain['owner_thread_id'],dispatch_token=token,current_character=next_name,dispatch_ready_for=next_name,
    character_status_at_handoff='blocked_explicit_http_failure_recovery_eligible',current_stage='Scarab_explicit_503_recovery_pending_owner',resume_stage='Read preserved Scarab evidence; recheck recovery conditions before new unique bounded requests',
    completed_count_snapshot=81,last_handoff_file=handoff_path.relative_to(ROOT).as_posix(),previous_handoff_file=chain['last_handoff_file'],
    unity_release_file=release_path.relative_to(ROOT).as_posix(),handoff_ready_at=now().isoformat(),updated_at=now().isoformat(),
    stopped_at=None,stop_reason=None,blocked_reason=None,current_blocked=False,successor_created=False,progress_sha256_at_handoff=sha(HERE/'progress.json'))
write(HERE/'conversation_chain.json',chain)
intent=dict(created_at=now().isoformat(),parent_thread_id=chain['parent_thread_id'],next_character=next_name,index=92,dispatch_token=token,
    handoff_file=handoff_path.relative_to(ROOT).as_posix(),assessment=assessment_path.relative_to(ROOT).as_posix(),unity_release=release_path.relative_to(ROOT).as_posix(),
    project_root='E:/MyTowerGame',project_id='935c594c-f414-48e0-bd08-ed8ba342f7fd',state='handoff_ready_pending_single_create_thread',max_successors=1)
write(D/'successor_dispatch_intent_20261028.json',intent)
assert handoff_path.read_text(encoding='utf-8')==text and (HERE/'NEXT_ENEMY_TASK.md').read_text(encoding='utf-8')==next_text
print(json.dumps(intent,ensure_ascii=False))
