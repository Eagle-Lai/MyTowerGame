"""Obsolete historical draft. Recovery succeeded; use finalize_tiger_20261028.py."""
raise RuntimeError('Obsolete blocked finalizer: Tiger Up recovery succeeded and Tiger is installed. Do not execute this draft.')
from session_tiger import *
import time

chain = owner()
assert not any((D/p).exists() for p in ['staged_art','installed_manifest.json','runtime_summary.json'])
up = D/'generation/Up'
assert (up/'request.json').is_file() and (up/'uncertain_result.json').is_file()
assert not any((up/p).exists() for p in ['raw.png','result.json'])
assert not (D/'generation/Down/request.json').exists()
uncertain = read(up/'uncertain_result.json')
assert 'curl transport failed 55' in uncertain['message'] and 'Connection was aborted' in uncertain['message']
process_check = subprocess.run(['powershell','-NoProfile','-Command',
    "@(Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'node.exe' -and $_.CommandLine -match 'generate\\.mjs') -or ($_.Name -eq 'curl.exe' -and $_.CommandLine -match 'aihub.dog') } | Select-Object Name,ProcessId) | ConvertTo-Json -Compress"],
    capture_output=True,encoding='utf-8',check=True)
assert not process_check.stdout.strip(), process_check.stdout
baseline = read(D/'incremental_before_20261028.json')
current = inventory()
changes = [{'path':p,'before':baseline['files'].get(p),'after':current.get(p)}
    for p in sorted(set(baseline['files'])|set(current)) if baseline['files'].get(p)!=current.get(p)]
assert not changes, changes
six = {p:sha(R/p) for p in baseline['protected_six']}
assert six == baseline['protected_six']
legacy = audit('blocked')
legacy_before = read(H/'scope_Tiger_before_20261028.json')
prior_unexpected = {x['path']:x for x in legacy_before['unexpected']}
assert not [x for x in legacy['unexpected'] if x != prior_unexpected.get(x['path'])]
assert len(legacy['unexpected']) == 291

progress = read(H/'progress.json')
assert progress['completed_count']==86
unfinished = []
for candidate in sorted((x for x in progress['items'] if x['status'] not in ['completed_pending_user_art_review','user_approved']),key=lambda x:x['index']):
    folder=H/candidate['name']
    files=sorted(p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file())
    unfinished.append(dict(index=candidate['index'],name=candidate['name'],status=candidate['status'],files=files,
        checkpoints=[p for p in ['anatomy_plan.json','installed_manifest.json','runtime_summary.json'] if (folder/p).is_file()],
        raw=[p for p in files if p.endswith('/raw.png')],runtime_directories=[p.name for p in folder.glob('runtime*') if p.is_dir()],
        blocked_reason=candidate.get('blocked_reason')))
others=[x for x in unfinished if x['name'] not in ['Tiger','PossessedWarg']]
assert len(others)==20 and all(x['status']=='not_started' and not x['checkpoints'] and not x['raw'] and not x['runtime_directories'] and all(p.startswith('reference/') for p in x['files']) for x in others)
warg=H/'PossessedWarg/generation/Down'
assert sha(warg/'request.json')=='B2B3C9FB4B78E2FFB5E606FCE95BB2843575982CADBE6C6E97D352346D27BA4A'
assert not any((warg/p).exists() for p in ['raw.png','result.json','uncertain_result.json'])

client=Client();project=client.identity()
errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
cache_refresh=None
for attempt in range(4):
    state=client.resource('mcpforunity://editor/state');s=state['data']
    if not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']:
        break
    if attempt==0 and s['advice'].get('blocking_reasons')==['stale_status']:
        cache_refresh=unwrap(client.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"Tiger_blocked_release_live_state_read"});return true;')))
    time.sleep(1)
else:
    raise RuntimeError('Unity state not ready for release')
live=probe(client)
assert live['scene']=='Assets/Scenes/Boot.unity' and not any(v for k,v in live.items() if k!='scene')
assert errors['data']==[]

stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
rel=lambda p:p.relative_to(R).as_posix()
blocked_path=D/('blocked_generation_'+stamp+'.json')
assessment_path=D/('successor_assessment_'+stamp+'.json')
scope_path=D/('scope_incremental_blocked_'+stamp+'.json')
release_path=D/('handoff_release_blocked_'+stamp+'.json')
binding_path=D/('evidence_binding_blocked_'+stamp+'.json')
handoff=H/'conversation_handoffs'/(stamp+'_Tiger_blocked.md')
reason=('Tiger Up initial Curl request ended with curl (55) Send failure: Connection was aborted. '
    'No HTTP status, raw.png, result.json or provider request/job ID was returned; the outcome and possible charge remain uncertain. '
    'No active generator or late result was found. The current standing authorization is explicitly scoped to fetch failed / ECONNRESET before secure TLS; '
    'the observed Curl upload/send error does not establish that condition. No retry, Down request, alternate-character paid probe or recovery-guard change was performed.')
diagnostic=dict(observed_at='2026-10-28T16:20:25+08:00',method='Unauthenticated curl.exe --head --max-time 20 --proto =https https://aihub.dog/v1/models',
    http_status=404,time_connect_seconds=.027402,time_appconnect_seconds=.057435,size_request_bytes=83,
    diagnostic_request_id='b18fb096-ce33-4aa7-9894-ea6201019551',
    interpretation='Separate nonpaid HEAD established TLS and received HTTP404. This diagnostic ID belongs only to HEAD; it is not an ID for the uncertain image request. It does not resolve the original request delivery/charge.')
write(assessment_path,dict(observed_at=now(),progress_completed_count=86,unfinished=unfinished,
    blocked_preserved=['PossessedWarg'],new_blocked='Tiger',not_started_count=len(others),
    deferred_next_candidate=others[0],chosen=None,successor_created=False,
    reason='No independent staged, installed or runtime stage exists. All 20 other unfinished characters are reference-only and require new image requests. Do not use another character to probe the unresolved send failure. Preserve those items as not_started rather than claiming individual generation failures.',
    possessed_warg_down_request_sha256=sha(warg/'request.json')))
scope=dict(observed_at=now(),baseline='incremental_before_20261028.json',baseline_count=len(baseline['files']),current_count=len(current),
    path_union_count=len(set(baseline['files'])|set(current)),changed=changes,added=[],deleted=[],unexpected_incremental=[],protected_six=six,protected_drift=[],
    legacy_scope='scope_Tiger_blocked_20261028.json',historical_unexpected_count=len(legacy['unexpected']),unexpected_added=[],
    semantic_failures=[n for n,v in legacy['semantics'].items() if not v['pass']],global_pass=False,production_changes=False)
write(scope_path,scope)
write(release_path,dict(observed_at=now(),transport=URL,project=project,state=state,cache_refresh=cache_refresh,errors=errors,live=live,protocol_history=client.history,
    note='No Play was entered, no source/C# changed, no forced scene or Play operation and no desktop control. Only own read-only editor probes and optional stale-state cache refresh.'))
gif_count=read(H.parent/'AllGIF/manifest.json')['count']
assert gif_count==1378
blocked=dict(observed_at=now(),character=NAME,index=98,status='blocked',user_approved=False,owner_thread_id=os.environ['CODEX_THREAD_ID'],dispatch_token=TOKEN,
    reason=reason,request=read(up/'request.json'),uncertain=uncertain,attempts=1,additional_network_attempts_used=0,
    attempt_files={p.name:sha(p) for p in up.iterdir() if p.is_file()},no_active_generation_process=True,late_result_found=False,
    diagnostic=diagnostic,down='prompt_prepared_not_requested',staging='not_executed',install_verify='not_executed',runtime='not_executed',record='not_executed',new_gifs=0,
    source_review='reference_review_20261028.json',full_prefabs='full_prefab_inspection_20261028.json',animation_contract='source_animation_contracts_20261028.json',
    animation_decision='Feline Walk already binds Body Euler x/y/z; Death Body Euler is zero. No animation change made or currently justified.',
    production_changes=False,scope=rel(scope_path),unity_release=rel(release_path),completed_count=86,allgif_count=gif_count,
    successor_decision='No independent recoverable stage; no fresh successor created while image transport outcome is unresolved.',
    recovery='Inspect for any actual provider result first. Preserve request/uncertain/console and do not claim no charge. A fresh Up revision needs an explicit bounded decision covering this Curl55 send failure or conclusive recovery of the original. Do not modify the existing standing authorization or broaden the generator guard on inference.')
write(blocked_path,blocked)
write(binding_path,dict(observed_at=now(),character=NAME,status='blocked',files={p.relative_to(D).as_posix():sha(p) for p in D.rglob('*') if p.is_file() and p!=binding_path},
    production_files=six,original_request_sha256=sha(up/'request.json'),original_outcome='uncertain_preserved',frames=0,gifs=0,production_changes=False))
text=f'''# Tiger(index98) 首次生成结果不明阻断交接

时间：{now()}。工程 E:/MyTowerGame / Unity2022.3.62f3c1 / HTTP MCP {URL}。
本聊天owner={os.environ['CODEX_THREAD_ID']}，dispatch_token={TOKEN}。进度仍86/108；Tiger为blocked、user_approved=false。没有stage/install/Verify/Play/record或生产修改，AllGIF仍{gif_count}，新GIF为0。

已实际查看原Tiger.png、source_prefab_offline.png和battle_prefab_offline.png，读取完整source/battle prefab及直接调用链。Tiger为金橙色条纹/赭斑四足虎，奶油口鼻与颊毛，一对圆耳在头部，四大爪和细长条纹尾；普通/攻击/死亡表情以原图为准。没有照搬Swine或SabretoothTiger解剖。准备了本角色anatomy与Up/Down提示词。Feline源动画MCP契约：Ready0.5s/21绑定、Attack0.5s/36绑定、Walk0.5s/24绑定、Death0.25s/39绑定；Attack的SetHead(0/1/0)/Event和Death的SetHead(2)留证。Walk本来已有Body三轴Euler，Death Body Euler为0，本轮没有自有或共享动画修补。

Up仅1次正式gpt-image-2/medium/1536x1024/n1、Curl无重试请求；于本地16:18:56结束，错误`curl (55) Send failure: Connection was aborted`。request、generation_intent、prompt、console、uncertain_result全部保留，没有raw/result/原生成服务查询ID；无在途node/curl或迟到结果。不能判断请求未送达或未计费。Down只有prompt，未请求；没有付费重试或其他角色探针。
现有standing_network_recovery_authorization_20261028.json的scope明确为`same transient fetch failed / ECONNRESET before secure TLS`，generate.mjs第78行按同样错误证据检查。本次只有Curl55发送中断，无法确认发生在TLS前，因此未篡改guard或扩大授权。额外网络恢复计数仍0。单次不带凭据的HEAD诊断HTTPS已建TLS并收到404；其诊断ID不是原生成请求ID，不能证明原请求未计费。

5278文件增量基线，before/current路径并集差异0、新增0、删除0；六保护及参考匹配。未改Assets、Packages、ProjectSettings、Luban、配置表、ConfigJson/Gen、声音、其他角色或共享C#，未Git同步/提交、构建部署或桌面控制。全局历史291unexpected和MeatBug/Monkey/MosquitoParasite/Pig/Piggy/Porky六项语义失败保持，新增0，不能称全局PASS。
Unity在8088重新动态核对custom-tools/instances、选现场完整MyTowerGame ID、project/info为E:/MyTowerGame/2022.3.62f3c1；最终Boot非Play、所有场景非dirty、无编译/域重载/资源更新、ready_for_tools=true、scriptCompilationFailed=false、error0、review/balance/recording/manual均false。未操作8082其他工程或8080。

现场队列22项未完成：PossessedWarg旧Down结果不明继续原状（SHA B2B3C9FB4B78E2FFB5E606FCE95BB2843575982CADBE6C6E97D352346D27BA4A），Tiger本次结果不明，另20项仅reference/not_started，无可独立恢复的stage/install/runtime。未把其他20项伪标blocked或失败。下一索引候选TreasureChest99暂不派发，避免借换角色付费探测共同发送故障；本轮未创建后继或计时器，链保持本owner/token并标blocked。

详细阻断：{rel(blocked_path)}。
完整增量范围：{rel(scope_path)}；全局历史审计scope_Tiger_blocked_20261028.json。
Unity释放：{rel(release_path)}。队列评估：{rel(assessment_path)}。本轮证据与六保护哈希：{rel(binding_path)}。

恢复时先读实时chain/progress和以上材料；不能重新prepare、覆盖或重发原Up请求、拿Up替代Down或改变既有账单不确定性。优先查实际原请求结果；若无可恢复结果，需覆盖本次Curl55结果不明且接受可能重复计费的明确有界新revision决定，然后只修Docs生成入口的相应授权检查。其后按原prompt完成Up实际审图、Down、stage真实透明度/切片/pivot/根部/尾巴连接、单角色安装Verify、两轮真实Play各84、实际PNG/GIF审阅、完整版本/范围、UTF8 record/GIF归档和唯一新聊天接棒。桌面控制仍须先对话确认；默认8088目标Unity MCP。Swine最终r02及旧673帧否决历史完整保留，不改其Assets。
'''
handoff.write_text(text,encoding='utf-8')
live_text=(f'2026-10-28 Tiger98首次Up生成阻断，进度86/108、user_approved=false。Curl55发送中断，无HTTP/raw/result/原服务ID，结果及计费仍不明；请求和uncertain保留，Down未请求，付费重试0。现有standing只涵盖fetch failed/ECONNRESET before secure TLS，本次不能证明该条件，未改guard或使用其他角色探针。5278文件并集差异0，六保护无漂移，未stage/install/Play/record，新GIF0，AllGIF{gif_count}。Unity已在8088动态核对E:/MyTowerGame并释放Boot非Play/全场景非dirty/空闲/编译失败false/error0。历史291unexpected与6项其他角色语义失败保持、新增0。另20项仅reference无独立可恢复阶段，PossessedWarg旧Down不重发；chain=blocked、未创建后继。完整交接：{rel(handoff)}。Swine最终r02实现完成待用户美术审核的状态保持。')
for path,marker in [(H.parent/'README.md','ENEMY_README_LIVE'),(H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','ENEMY_SERIAL_LIVE_STATE')]:
    original=path.read_text(encoding='utf-8')
    pattern=r'<!-- '+marker+r'_BEGIN -->.*?<!-- '+marker+r'_END -->'
    assert len(re.findall(pattern,original,re.S))==1
    updated=re.sub(pattern,'<!-- '+marker+'_BEGIN -->\n'+live_text+'\n<!-- '+marker+'_END -->',original,flags=re.S)
    if path.name=='README.md': updated+='\n\n'+live_text+'\n'
    path.write_text(updated,encoding='utf-8')
(H/'NEXT_ENEMY_TASK.md').write_text('# 当前唯一角色 Tiger(index98)：Curl55结果不明，链阻断\n\n'+text+'\n只有直接恢复授权或原请求结果明确后才恢复active；保留当前owner和dispatch_token，不超时抢锁。当前没有已创建的后继聊天。\n',encoding='utf-8')
item=next(x for x in progress['items'] if x['name']==NAME)
item.update(status='blocked',user_approved=False,current_stage='Up_initial_Curl55_uncertain_not_installed',blocked_reason=reason,blocked_record=rel(blocked_path),
    reference_review_file='Tiger/reference_review_20261028.json',runtime=[],actual_frames=0,visual_reviewed=False)
progress.update(status='blocked',current=NAME,updated_at=now())
write(H/'progress.json',progress)
chain.setdefault('historical_stops',[]).append(dict(state='blocked',character=NAME,stopped_at=now(),stop_reason='tiger_up_curl55_send_failure_outcome_uncertain',
    blocked_reason=reason,last_stage_evidence=rel(blocked_path),last_handoff_file=rel(handoff)))
chain.update(state='blocked',current_character=NAME,character_status_at_handoff='blocked',current_stage='Up_initial_Curl55_uncertain_not_installed',
    resume_character=NAME,resume_stage='Resolve initial Up outcome or explicit bounded Curl55 recovery; do not resend original',
    last_stage_evidence=rel(blocked_path),last_handoff_file=rel(handoff),previous_handoff_file=chain['last_handoff_file'],unity_release_file=rel(release_path),
    successor_assessment=rel(assessment_path),successor_created=False,dispatch_ready_for=None,current_blocked=True,blocked_reason=reason,
    stop_reason='tiger_up_curl55_send_failure_outcome_uncertain',stopped_at=now(),updated_at=now(),progress_sha256_at_stop=sha(H/'progress.json'),
    completed_count_snapshot=86,mcp_endpoint=URL,ownership_transfer_note='No successor created: uncertain original upload/send failure, no independent existing stage. Current owner/token retained; no timeout takeover.')
write(H/'conversation_chain.json',chain)
assert inventory()==current
assert read(H/'progress.json')['completed_count']==86 and read(H/'conversation_chain.json')['state']=='blocked'
print(json.dumps(dict(blocked=rel(blocked_path),handoff=rel(handoff),scope=rel(scope_path),unity_release=rel(release_path),
    completed_count=86,production_changes=0,allgif_count=gif_count,successor_created=False,live=live),ensure_ascii=False))
