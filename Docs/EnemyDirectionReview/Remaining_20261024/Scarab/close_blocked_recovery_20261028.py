"""Close this bounded recovery accurately. Docs-only; no paid calls or production edits."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re, sys, subprocess

D=Path(__file__).resolve().parent; HERE=D.parent; ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE))
from mcp_call import Client
OWNER='01a18093-7687-7313-aaba-7419090cc829'
TOKEN='sabretoothtiger-to-scarab-a14cefa3c87b4f9187c899d88ead8c0c'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def new(p,x):
    assert not p.exists(),str(p)
    write(p,x)
now=datetime.now(timezone(timedelta(hours=8))); stamp=now.isoformat(); slug=now.strftime('%Y%m%d_%H%M%S')
chain=read(HERE/'conversation_chain.json')
assert (chain['state'],chain['owner_thread_id'],chain['dispatch_token'],chain['current_character'])==('active',OWNER,TOKEN,'Scarab')
assert os.environ.get('CODEX_THREAD_ID')==OWNER
assert not (D/'installed_manifest.json').exists() and not (D/'runtime_summary.json').exists()
basepath=D/'incremental_before_recovery_20261028.json'; baseline=read(basepath)
current={p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
before={p:s.upper() for p,s in baseline['files'].items()}
changes=[dict(path=p,before=before.get(p),after=current.get(p)) for p in sorted(set(before)|set(current)) if before.get(p)!=current.get(p)]
protected=baseline['protected_scarab']; drift=[p for p,s in protected.items() if sha(ROOT/p)!=s.upper()]
assert not changes,changes
assert not drift,drift
global_scope=read(HERE/'scope_Scarab_recovery_20261028.json')
previous_scope=read(HERE/'scope_SabretoothTiger_20261028_final.json')
unexpected_added=sorted({e['path'] for e in global_scope['unexpected']}-{e['path'] for e in previous_scope['unexpected']})
assert not unexpected_added,unexpected_added
scope=dict(observed_at=stamp,baseline=basepath.relative_to(ROOT).as_posix(),baseline_sha256=sha(basepath),baseline_files=len(before),current_files=len(current),comparison='Union of before/current paths including additions and deletions',changes=changes,unexpected_incremental=[],protected_six=protected,protected_drift=drift,global_scope='scope_Scarab_recovery_20261028.json',global_pass=global_scope['pass'],historical_unexpected_count=len(global_scope['unexpected']),unexpected_added=unexpected_added,global_semantic_failures=[n for n,v in global_scope['semantics'].items() if not v['pass']],claim='No production changes. Historical global failures preserved; no global PASS claimed.')
new(D/'scope_incremental_recovery_20261028.json',scope)
generation=[]
for direction in ['Up','Down']:
    for revision in ['', 'revision_01']:
        folder=D/'generation'/direction/revision
        entry=dict(direction=direction,revision=revision or 'original',request=str((folder/'request.json').relative_to(ROOT)).replace('\\','/'),request_sha256=sha(folder/'request.json'))
        for filename in ['result.json','uncertain_result.json','raw.png','console.txt','recovery_intent.json','prompt.txt']:
            if (folder/filename).is_file(): entry[filename]=dict(path=(folder/filename).relative_to(ROOT).as_posix(),sha256=sha(folder/filename),bytes=(folder/filename).stat().st_size)
        if (folder/'result.json').exists(): entry.update(outcome='http_response',result=read(folder/'result.json'))
        else: entry.update(outcome='uncertain',result=read(folder/'uncertain_result.json'))
        generation.append(entry)
assert generation[1]['result']['status']==200
assert generation[-1]['outcome']=='uncertain' and not (D/'generation/Down/revision_01/raw.png').exists()
active=subprocess.run(['powershell','-NoProfile','-Command',"@(Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('node.exe','python.exe') -and $_.CommandLine -match '(generate\\.mjs|runtime_runner\\.py|runtime_runner_revision\\.py)' } | Select-Object ProcessId,Name,CommandLine) | ConvertTo-Json -Compress"],capture_output=True,text=True,check=True).stdout.strip()
assert not active or active=='[]',active
unity=dict(observed_at=stamp,project='E:/MyTowerGame',expected_version='2022.3.62f3c1',target_editor_operations_performed=False,production_install=False,Play_performed=False,computer_control_policy='User explicitly requires a confirmation dialog before any computer/desktop control. User chose to reconnect MyTowerGame manually; no desktop input is authorized or performed in this resumed turn.',prior_release='Docs/EnemyDirectionReview/Remaining_20261024/SabretoothTiger/unity_release_completed_20261028_113344.json',prior_release_sha256=sha(HERE/'SabretoothTiger/unity_release_completed_20261028_113344.json'))
client=None
try:
    client=Client(); client.resource('mcpforunity://custom-tools'); instances=client.resource('mcpforunity://instances')
    unity['instances']=instances
    listing=instances.get('data',instances).get('instances',[])
    targets=[i for i in listing if i.get('name')=='MyTowerGame']
    if len(targets)!=1:
        unity.update(current_target_state_verified=False,status='MyTowerGame not registered on HTTP Local 8082. No tools invoked against FishTestGame.',required_manual_action='In E:/MyTowerGame Unity 2022.3.62f3c1, Window > MCP for Unity: HTTP Local http://127.0.0.1:8082, Start Session/Connect. Do not stop the shared server or another project.')
    else:
        unity['project_identity']=client.identity()
        unity['state']=client.resource('mcpforunity://editor/state')
        unity['errors']=client.tool('read_console',dict(action='get',types=['error'],count='50',format='json'))
        unity['probe']=client.tool('execute_code',dict(action='execute',code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};'))
        unity.update(current_target_state_verified=True,status='Read-only target identity/state/error/probe completed; no scene or Play changes.')
except Exception as e:
    unity.update(current_target_state_verified=False,status='Target MCP verification not completed',error=str(e))
unity['protocol_history']=client.history if client else []
unity_path=D/('unity_blocked_recovery_'+slug+'.json'); new(unity_path,unity)
progress=read(HERE/'progress.json')
unfinished=[i for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved']]
readiness=[]
for item in unfinished:
    d=HERE/item['name']
    readiness.append(dict(index=item['index'],name=item['name'],status=item['status'],installed_manifest=(d/'installed_manifest.json').exists(),runtime_summary=(d/'runtime_summary.json').exists(),staged_art=(d/'staged_art').exists(),raw_images=[p.relative_to(d).as_posix() for p in (d/'generation').rglob('raw.png')] if (d/'generation').exists() else [],uncertain_records=[p.relative_to(d).as_posix() for p in (d/'generation').rglob('uncertain_result.json')] if (d/'generation').exists() else []))
assert not any(x['installed_manifest'] or x['runtime_summary'] or x['staged_art'] for x in readiness),readiness
reason='Scarab Down revision_01 is uncertain after fetch failed / ECONNRESET before secure TLS connection. No HTTP status, raw image, result.json or server query ID was returned. Do not infer no charge or resend. Paid generation stopped; no independent installed/staged/runtime work remains among unfinished characters. Do not use another character as a paid probe.'
handoff_rel='Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/'+slug+'_Scarab_blocked.md'
block_rel='Docs/EnemyDirectionReview/Remaining_20261024/Scarab/blocked_generation_recovery_'+slug+'.json'
block=dict(character='Scarab',index=92,status='blocked',blocked_at=stamp,owner_thread_id=OWNER,dispatch_token=TOKEN,stage='Up HTTP200 and actual raw/parts review; Down revision_01 uncertain; not staged/installed/runtime',blocked_reason=reason,generation=generation,active_generator_or_runner_processes=[],production_scope='Scarab/scope_incremental_recovery_20261028.json',production_changes=False,scope=scope,unity_evidence=unity_path.relative_to(ROOT).as_posix(),unity_current_target_state_verified=unity['current_target_state_verified'],up_visual_review='Scarab/up_raw_visual_review_20261028.json',up_local_repair='Scarab/local_raster_revision_01/processing.json',visual_review_limitations='Actual Up raw, before/after rear cap and cleaned 7-part proof viewed. Lower cap closure is simplified with a visible tone transition. No assembled rig/Down/generated runtime media reviewed, no approval.',remaining_readiness=readiness,common_dependency='All remaining production needs unprovided image results/new paid calls; latest request uncertain, so no fresh successor paid probe.',historical_protection=dict(PossessedWarg='Original Down uncertain unchanged; no resend',ScarabMounted='Original Up402 unchanged; no recovery request',SabretoothTiger='Old Down revision_01 uncertain unchanged; Down-only $0.07 authorization already consumed, not reused'),completed_count=progress['completed_count'],authorized_count=progress['authorized_count'],AllGIF_count=read(HERE.parent/'AllGIF/manifest.json')['count'],handoff_file=handoff_rel,recovery_conditions=['Locate the original Scarab Down revision_01 result through a reliable service query if one becomes available, or obtain an explicit bounded user decision accepting possible duplicate charge before any resend. Never overwrite/reclassify the original uncertain request.','Reuse preserved Up revision_01 and documented local rear-cap cleanup; full assembled rig review still required. Do not repeat prepare or Up generation.','Restore and select the actual MyTowerGame instance on 8082, verify E:/MyTowerGame and exact version before editor operations. Desktop control requires user confirmation.','After both real views are present, complete stage/visual review, install Verify, two real Play rounds, actual media review, version/scope binding, record and GIF archive.'])
new(ROOT/block_rel,block)
handoff=f'''# Scarab 有界恢复阻断交接

- 时间：{stamp}；目标 E:/MyTowerGame，Unity 2022.3.62f3c1，unityMCP / HTTP Local 8082。根AGENTS旧D盘标题不改、不转工程。
- 本聊天 {OWNER}，唯一token `{TOKEN}`。本角色 index92，进度仍81/108、AllGIF1246；未记完成或用户批准。
- Up revision_01单次HTTP200，1421781 bytes，实际1536×1024 RGB。已实际查看完整原图；后脑无橙眼但错误残留正面金色口器。原图保留，local_raster_revision_01去除下缘口器、沿原橄榄色闭合后脑，三状态复用同一后头。实际查看前后图及7分件去背预览；后脑下缘绘制简化、色调接缝如实记录，仍需完整离线rig与运行复核。没有假造Down。
- Down revision_01仅一次正式请求，2026-10-28T03:48:23.081Z开始，03:48:33.135Z uncertain记录。stderr为fetch failed / ECONNRESET，建立TLS前断开；无HTTP状态、raw、result或可查询ID。不推定未收费、不改为明确失败、不重发、不新revision或另角色付费探针。
- 两方向2026-10-26原HTTP503及所有request/result均保留。两次恢复intent、预检、正式request、console、Up raw与Down uncertain证据全在Scarab/generation各revision_01。
- 5178文件前后并集变化0、六保护指纹无漂移；全局历史291unexpected和6其他角色语义失败保留，新增unexpected0，不称全局PASS。审计Scarab/scope_incremental_recovery_20261028.json。
- 未stage完整角色、未install/Verify/Play/record，无运行帧与新GIF，未修改生产资源、共享C#、表、ConfigJson/Gen、声音、其他角色。未pull/reset/clean/checkout/commit/push、构建或部署。
- Unity本轮未操作任何目标编辑器/场景/Play；MCP当前目标状态核对结果：{unity['status']}。证据 `{unity_path.relative_to(ROOT).as_posix()}`；上一角色Boot非Play非dirty释放仅为历史，不冒充本轮确认。用户选择手工连接MyTowerGame，禁止未确认的电脑控制。
- 27个未完成项没有installed/staged/runtime可独立恢复阶段；PossessedWarg原Down仍uncertain、ScarabMounted原Up402保留；其他24项not_started需要新图片。当前共同付费依赖尚不确定，因此链blocked，保留当前owner/token，不创建后继或后台计时器。

## 恢复入口

先读本总结、`{block_rel}`、NEXT、原执行prompt、CONTINUATION_PROTOCOL、IMAGE_RELAY_RECOVERY、实时chain/progress、Up实际原图/局部修补及Down request/uncertain/console。不得重跑prepare或Up；Down原结果未可靠确认或没有用户明确有界补发授权时不再发送。既有普通继续指令不等于接受结果不明请求的重复计费。

目标MCP恢复后重新动态发现并明确选择完整MyTowerGame实例、核对E:/MyTowerGame及2022.3.62f3c1。不要操作FishTestGame，不抢占/重启共享8082。需要桌面操作先弹出确认。本次未完成安装和运行，不能宣称完整角色通过。解除阻断并完成全部验收后，才能按协议创建唯一全新本地后继并登记所有权。
'''
assert not (ROOT/handoff_rel).exists(); (ROOT/handoff_rel).write_text(handoff,encoding='utf-8')
item=next(i for i in progress['items'] if i['name']=='Scarab')
item.update(status='blocked',blocked_record=block_rel,blocked_at=stamp,blocked_reason=reason,visual_reviewed=False,user_approved=False,recovery_stage='up_returned_reviewed_down_revision_01_uncertain_not_installed',up_visual_evidence='Scarab/up_raw_visual_review_20261028.json',up_local_repair='Scarab/local_raster_revision_01/processing.json')
progress.update(updated_at=stamp,current='Scarab'); write(HERE/'progress.json',progress)
next_text=f'''# 当前唯一角色：Scarab(index92)，Down结果不明，禁止自动重发

工程E:/MyTowerGame，Unity2022.3.62f3c1，unityMCP8082。进度81/108，AllGIF1246。当前owner `{OWNER}`、token `{TOKEN}`，链blocked，未创建后继。

## 开工必读

根AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、实时conversation_chain.json/progress.json、`{handoff_rel}`、`{block_rel}`、Scarab/scope_incremental_recovery_20261028.json，以及Scarab/generation两方向全部原始与revision_01请求材料。

只有chain.active且owner/token与恢复授权匹配后才能操作生产/Unity。blocked不因时间失效、不抢锁。根AGENTS的FreedomTower_1/D盘标题为旧文案，不改规则、不转工程。

## 当前事实与恢复条件

Up revision_01单次HTTP200，已实际审原图、去口器前后图、7分件去背预览。原图1421781 bytes、1536×1024 RGB。复用Scarab/local_raster_revision_01/Up_sheet.png及processing.json，不能冒充AI原图；后脑下缘简化、色差接缝仍需完整离线rig/运行检查。没有完整stage、installed_manifest、runtime_summary或新GIF，不重复prepare/Up生成。

Down revision_01正式请求仅一次，2026-10-28T03:48:33.135Z记录fetch failed，stderr ECONNRESET/建立TLS前断开。无HTTP状态/raw/result/查询ID，结果不明，不推定未收费、不重发、不新revision。必须先可靠定位原结果，或由用户明确给出接受可能重复收费的单次有界补发授权；普通“继续”不等于补发授权。两方向2026-10-26明确HTTP503原记录全部保留。

用户2026-10-28新约束：默认仅通过目标Unity MCP；不要控制电脑。如确需桌面操作，必须先弹出对话取得确认。用户已选择自己在MyTowerGame窗口连接HTTP Local8082，不能将此选择当电脑控制授权。当前MCP核对见`{unity_path.relative_to(ROOT).as_posix()}`。仅发现其他工程时不向其执行工具，不杀进程/抢共享端口。目标连接后动态发现选择完整实例，核对路径、版本、占用及全部场景dirty。

所有后续付费请求已停止；其他未完成项没有已stage/install/runtime可独立恢复阶段，不用别的角色作付费探针。PossessedWarg旧Down仍uncertain不重发；ScarabMounted旧Up402保留；SabretoothTiger旧Down revision_01仍uncertain，Down一次$0.07授权已消耗，不转用。

解除阻断后继续原prompt完整单角色流程：两方向实际图像审阅、切片透明度/关节/足尖、离线rig、安装Verify、两轮各84真实Play、实际PNG时序或媒体审阅、增量范围及版本绑定、record与GIF归档。最终仅completed_pending_user_art_review，不能替用户批准。全局291unexpected与6历史其他角色语义失败保留，本轮5178文件变化0、六保护无drift。禁止修改表/ConfigJson/Gen、音频、其他角色/共享C#；不pull/reset/clean/checkout/commit/push，不构建部署。

完成后写新交接和实时prompt/NEXT，确认Unity安全释放，按协议创建唯一全新本地后继并登记owner/token；只剩真实阻断时停，不建后台计时器、不fork/子代理/并行角色。
'''
(HERE/'NEXT_ENEMY_TASK.md').write_text(next_text,encoding='utf-8')
prompt=HERE/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md'; text=prompt.read_text(encoding='utf-8')
live=f'''2026-10-28 Scarab(index92)有界恢复停止：81/108、AllGIF1246。Up revision_01单次HTTP200、实际审原图和7分件，保留原图及去除错误背面口器的local_raster_revision_01；下缘简化仍待完整rig/运行审核。Down revision_01单次请求fetch failed/ECONNRESET、建立TLS前断开，无HTTP/raw/result/查询ID，结果不明禁止自动重发，不推定未收费。未完整stage/install/Verify/Play/record，无新GIF。5178文件变化0、六保护无drift，历史291unexpected/6语义失败保留、新增0。目标MyTowerGame MCP状态见本轮Unity证据；未使用其他工程验证。用户要求默认只用Unity MCP，电脑操作必须先弹窗确认，已选择手工连接。chain=blocked，保留owner/token，无后继或计时器，禁止其他角色付费探针。交接：{handoff_rel}；恢复以实时NEXT/chain及原请求证据为准。'''
text=re.sub(r'(?s)(<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->).*?(<!-- ENEMY_SERIAL_LIVE_STATE_END -->)',lambda m:m.group(1)+'\n'+live+'\n'+m.group(2),text,count=1)
prompt.write_text(text,encoding='utf-8')
readme=HERE.parent/'README.md'
with readme.open('a',encoding='utf-8') as f:f.write('\n\n'+live+'\n')
chain.update(state='blocked',current_character='Scarab',character_status_at_handoff='blocked',current_stage='up_returned_reviewed_down_revision_01_uncertain_not_installed',last_handoff_file=handoff_rel,current_blocked=True,blocked_reason=reason,stop_reason='scarab_down_revision_01_uncertain_econnreset_before_tls',stopped_at=stamp,updated_at=stamp,successor_created=False,completed_count_snapshot=progress['completed_count'],recovery_file=block_rel,unity_release_file=unity_path.relative_to(ROOT).as_posix(),resume_character='Scarab',resume_stage='Resolve preserved Down revision_01 uncertain outcome; reuse Up, restore target MCP, then full staging/runtime',progress_sha256_at_stop=sha(HERE/'progress.json'),computer_control_policy='Unity MCP by default. Any desktop/computer control requires an explicit confirmation dialog first. User chose manual reconnect on 2026-10-28.')
chain.setdefault('stage_history',[]).append(dict(character='Scarab',status='blocked',current_stage=chain['current_stage'],owner_thread_id=OWNER,dispatch_token=TOKEN,closed_at=stamp,handoff_file=handoff_rel,final_evidence=block_rel))
write(HERE/'conversation_chain.json',chain)
assert read(HERE/'conversation_chain.json')['owner_thread_id']==OWNER
assert read(HERE/'progress.json')['completed_count']==81
print(json.dumps(dict(handoff=handoff_rel,block=block_rel,production_changes=changes,protected_drift=drift,completed_count=81,chain='blocked',successor_created=False,unity_current_target_state_verified=unity['current_target_state_verified']),ensure_ascii=False))
