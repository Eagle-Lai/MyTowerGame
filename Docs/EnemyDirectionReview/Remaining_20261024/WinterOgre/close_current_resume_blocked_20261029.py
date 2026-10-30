"""Close this continuation after its two separately recorded attempts; no retry."""
from pathlib import Path
import sys,copy,re
sys.path.insert(0,str(Path(__file__).resolve().parent))
from session_winterogre import *

def unpack(v):
    value=v.get('structuredContent') or json.loads(v['content'][0]['text'])
    assert value.get('success'),value
    return value

def data(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8')

owner()
stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
write(D/'current_resume_closeout_stamp_20261029.json',dict(stamp=stamp,observed_at=now()),fresh=True)
chain_before=read(H/'conversation_chain.json');progress_before=read(H/'progress.json')
assert progress_before['completed_count']==99 and progress_before['authorized_count']==108
attempts=[]
for relative in ['generation/Up','generation/Up/revision_01','generation/Up/revision_02','generation/Up/revision_03','generation/Up/revision_04']:
    folder=D/relative;request=read(folder/'request.json')
    assert not (folder/'raw.png').exists() and not (folder/'result.json').exists()
    assert (request['endpoint'],request['model'],request['quality'],request['size'],request['n'])==('https://aihub.dog/v1/images/edits','gpt-image-2','medium','1536x1024',1)
    attempts.append(dict(path=relative,request=request,uncertain=read(folder/'uncertain_result.json'),
        http_status=None,image=None,query_id=None,charge='unknown_not_reclassified',
        evidence_sha256={p.name:sha(p) for p in sorted(folder.iterdir()) if p.is_file()}))
assert sum(a['request'].get('recovery',{}).get('mode')=='standing_user_authorized_network_recovery' for a in attempts)==2
assert sum(a['request'].get('recovery',{}).get('mode')=='current_turn_bounded_resume_after_transport_diagnosis' for a in attempts)==2
assert 'curl transport failed 52' in attempts[-1]['uncertain']['message']
assert not (D/'generation/Down/request.json').exists()
assert not any((D/'generation').rglob('raw.png'))
process_check=subprocess.run(['powershell','-NoProfile','-Command',
    "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -in @('node.exe','curl.exe') -and $_.CommandLine -match '(generate\\.mjs|WinterOgre)' } | ForEach-Object { @{pid=$_.ProcessId;name=$_.Name} }) | ConvertTo-Json -Compress"],capture_output=True,text=True,check=True)
assert not process_check.stdout.strip() or json.loads(process_check.stdout)==[]

# Correct target identity and error scene first; no state-changing editor work.
c=Client();release=dict(observed_at=now(),transport='http://127.0.0.1:8088/mcp',project=c.identity())
release['errors_response']=c.tool('read_console',dict(action='get',types=['error'],count='50',format='json',include_stacktrace=True))
errors=unpack(release['errors_response'])['data']
assert len(errors)==2 and all('[WebSocket] Connection failed.' in e['message'] and 'McpLog.cs' in e['file'] for e in errors),errors
release['compile_errors_response']=c.tool('read_console',dict(action='get',types=['error'],filter_text='error CS',count='50',format='json'))
assert unpack(release['compile_errors_response'])['data']==[]
release['cache_refresh']=c.tool('execute_code',dict(action='execute',code=
    'var t=System.Linq.Enumerable.FirstOrDefault(System.Linq.Enumerable.Select(System.AppDomain.CurrentDomain.GetAssemblies(),a=>a.GetType("MCPForUnity.Editor.Services.EditorStateCache")),x=>x!=null);'
    'var m=t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic);'
    'm.Invoke(null,new object[]{"WinterOgre current continuation blocked closeout; no Play or install"});return true;'))
release['state']=c.resource('mcpforunity://editor/state');release['live']=probe(c);idle(release['live'])
s=release['state']['data']
assert not s['tests']['is_running'] and s['advice']['ready_for_tools'] and not s['staleness']['is_stale']
assert not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending']
assert not s['assets']['is_updating'] and not s['assets']['external_changes_dirty']
release.update(error_count=2,error_cs_count=0,error_free_release=False,
    safe_to_stop_with_recorded_transport_error_limitation=True,no_play_mode_change=True,no_console_clear=True,
    no_compile_or_refresh_request=True,
    limitation='Two retained MCP WebSocket connection errors; current 8088 endpoint works, compilationFailed=false. The error0 condition is unmet.',
    protocol_history=c.history)
release_file=D/('unity_release_blocked_'+stamp+'.json');write(release_file,release,fresh=True)

baseline=read(D/'incremental_before_20261029.json');current=snapshot()
changes=[dict(path=p,before=baseline['files'].get(p),after=current.get(p)) for p in sorted(set(baseline['files'])|set(current)) if baseline['files'].get(p)!=current.get(p)]
previous_scope=read(D/'scope_incremental_blocked_20261029_134607.json')
assert changes==previous_scope['changes'] and len(current)==len(baseline['files'])==5545
assert all(current[p]==v for p,v in baseline['protected_six'].items())
scope_file=D/('scope_incremental_blocked_'+stamp+'.json')
write(scope_file,dict(observed_at=now(),basis='Current disk union over Assets/Packages/ProjectSettings/Luban, not Git HEAD',
    baseline='incremental_before_20261029.json',baseline_sha256=sha(D/'incremental_before_20261029.json'),
    baseline_files=5545,current_files=5545,changes=changes,added=[],deleted=[],unexpected_incremental=[],
    classified_automatic_side_effects=previous_scope['classified_automatic_side_effects'],
    protected_six=baseline['protected_six'],protected_six_unchanged=True,shared_CSharp_drift=[],other_character_and_configuration_drift=[],
    global_audit='Historical 291 unexpected and six other-character semantic failures were not rerun or reclassified; no global PASS claimed.'),fresh=True)

remaining=[i for i in progress_before['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved']]
assert len(remaining)==9
assessment=[]
for item in remaining:
    folder=H/item['name'];files=sorted(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    stages={key:[p.relative_to(folder).as_posix() for p in folder.rglob(key)] for key in ['raw.png','result.json','installed_manifest.json','runtime_summary.json']}
    if item['name'] not in [NAME,'PossessedWarg']:
        assert item['status']=='not_started' and len(files)==8 and all(p.relative_to(folder).parts[0]=='reference' for p in files)
    assessment.append(dict(name=item['name'],index=item['index'],status_before_closeout=item['status'],
        existing_files=[p.relative_to(folder).as_posix() for p in files],stage_evidence=stages,
        recoverable_without_paid_request=False))
assess_file=D/('successor_assessment_blocked_'+stamp+'.json')
write(assess_file,dict(observed_at=now(),remaining=assessment,selected_successor=None,
    reason='No independent staged/install/runtime work; seven reference-only characters share the image service. PossessedWarg original Down remains unknown. No direction or character paid probes.'),fresh=True)
usage_files=sorted(D.glob('read_only_service_recheck_*Z.json'))
usage_observations=[]
for p in usage_files:
    q=read(p);u=next(x for x in q['responses'] if '/v1/usage?' in x['url'])
    usage_observations.append(dict(file=p.name,sha256=sha(p),observed_at=q['observed_at'],http_status=u['http_status'],
        daily_usage=u.get('body',{}).get('daily_usage'),balance=u.get('body',{}).get('balance')))
tooling_file=D/('docs_tooling_change_'+stamp+'.json')
diff=subprocess.run(['git','diff','--no-index','--',str(D/'generate_entry_before_recovery.mjs'),str(H/'generate.mjs')],capture_output=True,text=True,encoding='utf-8')
assert diff.returncode in [0,1]
write(tooling_file,dict(observed_at=now(),scope='Docs-only generation CLI. No Unity C# changes.',
    generator_before_sha256=sha(D/'generate_entry_before_recovery.mjs'),generator_after_sha256=sha(H/'generate.mjs'),
    generator_diff=diff.stdout,wrapper_sha256=sha(H/'generate_character.ps1'),
    changes='Exact WinterOgre Up revision_03 and revision_04 current-turn guards, fixed existing local-proxy opt-in only for reviewed WinterOgre Up04/initialDown. Curl config disabled, HTTPS endpoint/credential stdin/no redirects/no retries preserved. Automatic limit remains2.',
    proxy_fix_evidence='transport_fix_20261029.json'),fresh=True)

reason=('WinterOgre Up initial/revision_01/revision_03 ended Curl55 send-aborted; revision_02 ended fetch failed/ECONNRESET before TLS; proxy revision_04 ended Curl52 empty reply. '
    'All five lack HTTP status, raw/result or query ID. Original automatic2/2 plus both separately documented single-request current-turn decisions are consumed. Stop paid requests; Down unrequested; no independent continuation.')
blocked_file=D/('blocked_generation_recovery_'+stamp+'.json')
blocked=dict(observed_at=now(),character=NAME,index=111,status='blocked',user_approved=False,
    owner_thread_id=OWNER,dispatch_token=TOKEN,reason=reason,attempts=attempts,
    prior_uncertain=3,current_continuation_requests=2,total_requests=5,total_HTTP200=0,total_uncertain=5,
    allowance_usage=dict(standing_automatic=dict(used=2,limit=2,reset=False),
        current_turn_direct=dict(used=1,limit=1,file='authorized_resume_20261029.json'),
        post_transport_fix=dict(used=1,limit=1,file='authorized_proxy_resume_20261029.json')),
    authorization_basis='Existing direct standing silent-network-recovery grant plus latest direct continue request. The two distinct numerical bounds were agent decisions, not user monetary budgets; no old counter or document was reset.',
    cost='Unknown for all five; authenticated key usage shows only aggregates. Daily image count/cost stayed15/$1.05 at all three observations while wallet balance changed; cannot correlate individual request charges or assert no charge.',
    usage_observations=usage_observations,
    nonbillable_control=dict(direct='unauthenticated_upload_diagnosis_20261029_142135.json',proxy='unauthenticated_upload_diagnosis_20261029_142408.json',
        finding='Direct unauthenticated multipart stalled after71446 bytes/Curl55; existing-proxy control uploaded660604 bytes and returned401/TLSverify0. Authorized post-fix Curl request still returned empty reply. Not proof of a working image-generation upstream.'),
    down='Prompt only; no request',source_review='reference_review_20261029.json',source_contract='source_contract_20261029.json',
    character_production_changes=False,staging='not_executed',install_verify='not_executed',runtime='not_executed',record='not_executed',new_gifs=0,
    completed_count=99,allgif_count=read(H.parent/'AllGIF/manifest.json')['count'],
    scope=scope_file.name,unity_release=release_file.name,successor_assessment=assess_file.name,docs_tooling=tooling_file.name,
    unity_error_count=2,unity_error_free_release=False,no_successor_created=True,
    recovery='No new paid request from repeating GET/models, GET/usage, unauthenticated401 controls or opening another chat. Recover an existing result or obtain concrete provider/request disposition or a separately diagnosed and resolved failure with a new bounded execution decision. Preserve all five unknown outcomes, consumed allowances and owner/token.')
assert blocked['allgif_count']==1594
write(blocked_file,blocked,fresh=True)

handoff=H/'conversation_handoffs'/(stamp+'_WinterOgre_blocked.md')
relative_handoff=handoff.relative_to(ROOT).as_posix();relative_block=blocked_file.relative_to(ROOT).as_posix()
live=(f'2026-10-29 WinterOgre111续作后仍blocked，99/108，AllGIF1594、无新增媒体。原3次unknown保留，本轮新增Up revision_03 Curl55和修复传输后的revision_04 Curl52空回复，共5次均无HTTP/raw/result/查询ID，费用仍未知。'
    '原自动2/2与本轮两个独立max1决定均已用尽，不重置，不再付费，不拿Down/其他角色探针；Down从未请求。'
    '非计费对照定位直连上传71446字节后中断；经系统现有代理完整上传660604字节得到401、证书校验0，但正式请求仍无回复，不能宣称图像服务恢复。鉴权models/usage200、余额有效；汇总图像请求15/$1.05未变不能证明单次未收费。'
    '未stage/install/Verify/Play/record、未改角色生产资源/共享C#；5545路径并集仅Reporter旧自动时间戳，六保护/其他角色/配置无漂移，历史global291unexpected/6语义失败未重审。'
    'Unity8088现场身份正确，单一clean Boot、非Play、全空闲、failed=false/ready=true，保留2条MCP连接Error，error0未满足，不清日志。'
    f'7个not_started只有reference8文件，PossessedWarg旧Downunknown保留；无独立可恢复项，chain=blocked保留owner/token，未建后继。证据WinterOgre/{blocked_file.name}，交接{relative_handoff}；完整入口NEXT_ENEMY_TASK.md。')
handoff_text=f'''# WinterOgre 网络恢复继续尝试后阻断交接

时间：{now()}。工程E:/MyTowerGame，Unity2022.3.62f3c1，MCP8088。owner `{OWNER}`，token `{TOKEN}`。本记录追加，不覆盖13:46首次封存或任何旧请求。

## 本轮动作与结果

用户在已知阻断后直接要求“继续任务”。先只读检查真实队列，原3次请求无新结果，其他7个未开始角色仅各8个reference文件。原自动恢复2/2不改。使用powershell-idioms与既有imagegen身份保留规范；当前用户API/模型授权覆盖实际AIHub路径，不切其他端点或质量。

非计费检查：Curl/Node小请求可达，models及公开KeyUsageView使用的/v1/usage鉴权均200、密钥有效/余额充足。基于当前直接继续与此前“同类故障可静默继续、接受可能重复收费”直接授权，先记录一个代理选择的max1决定（不是用户新增预算），Up revision_03/Curl于{attempts[3]['request']['started']}正式发送，{attempts[3]['uncertain']['finished']} Curl55无HTTP/raw，单次消耗并保留。

继续不计费排查：不带任何密钥的同一multipart上传也Curl55，已发71446字节、18.98s；通过现场系统已配置的127.0.0.1:7897代理，完整660604字节、0.38s、HTTP401、TLS验证0。没有改系统代理、注册表、DNS或全局环境。由此只确认直连上传路径问题及非鉴权代理对照，不宣称图片上游成功。

Docs CLI新增明确-UseSystemLocalProxy/Curl CONNECT选项，限定当前角色Up04/初始Down，保持HTTPS同一aihub.dog端点、证书验证、Bearer仅stdin、无重试/重定向。重新记录修复后一个独立max1决定，旧自动计数与revision_03的消耗均保留；Up revision_04于{attempts[4]['request']['started']}发送，{attempts[4]['uncertain']['finished']}以Curl52 Empty reply from server退出。仍无HTTP/raw/result/查询ID，停止付费，没有额外Up05、Down或其他角色请求。

本轮正式请求2次，0成功、2uncertain；角色累计5次，全部uncertain。原序列为Curl55、Curl55、ECONNRESET/TLS前断开，新增为Curl55、Curl52。没有活动生成进程。旧与新request/console/intent/uncertain均在原路径，逐文件SHA见 `{relative_block}`。服务公开key用量三次均当日15次/$1.05，钱包余额变化；聚合结果不能关联单次，也不能据此宣称未收费，全部费用未知。

## 角色阶段和范围

仍99/108：99项completed_pending_user_art_review（未代用户批准）、PossessedWarg79与WinterOgre111两项blocked，112..118七项not_started。WinterOgre没有生成图可审，没有stage/install/Verify/Play/两轮168检查/record或新媒体，AllGIF1594不变。没有修改本角色生产prefab/图集、共享C#、其他角色或配置。

源图实际审阅和独立anatomy/prompt已保留：金色斑驳秃头尖耳、裸脚双足、白毛腰裙与双巨大护腕、空拳；Weapon renderer原本禁用，不能新增图集拐杖。源契约source_contract与original_serialized_objects不改：Giant Ready/Walk loop、Attack/Death时序/事件、全部float/PPtr与ArmR/FistR/Weapon层级保留。当前通用pack模板把持武器ArmR放大，不适合本角色双空拳，未来必须在本角色布局阶段实看修正，不能重跑prepare或盲安装。

5545文件当前磁盘路径并集与开工基线比较，仍仅Assets/StreamingAssets/build_info旧Reporter自动时间戳一项；before B0F0E60D467FF1667D356F9F300769E32AC0DB6A99769DB65CD1580D5EF55A73，after 97518424ECA99D1F6E29D6946E56A9D899EFD32F740CD3B09C9D096415D466B3。ReporterEditor.cs SHA不变，既有InitializeOnLoad/compile-to-idle回调不需Play；本任务未请求Play/直接写/回滚该文件。新增/删除0、六保护匹配、共享C#/其他角色/配置无漂移、unexpected_incremental=[]。历史global291unexpected及6其他角色语义失败未重审，不称全局PASS。

Unity通过8088动态custom-tools/instances、set_active_instance、project/info核E:/MyTowerGame和2022.3.62f3c1；读取错误后状态/实时探针，单一clean Boot、非Play、tests/review/balance/recording/manual/compile/reload/update全idle，scriptCompilationFailed=false、ready=true、external_changes_dirty=false。2条旧MCP WebSocket连接Error保留，当前端到端可用、error CS为空，error0条件仍未满足，不清日志。不请求无必要编译或刷新，不用其他工程结果。详见 `{release_file.name}`。

## 停链与恢复入口

七个not_started都没有独立生成/暂存/安装/运行工作，PossessedWarg只有成功Up与结果不明Down，不能独立完成；不拿其他角色付费探针。链blocked保留本owner/token，没有后继、子代理、fork或计时器。没有git改写/提交、构建部署、桌面控制或长期memory写入。

完整恢复prompt为 `../NEXT_ENEMY_TASK.md`，中文UTF8、单文件一次复制。所有已消耗次数保留，不再以模型列表/余额正常或无鉴权401作为新增正式请求的充分恢复证据。先找回已有结果或取得服务方针对这些请求的处置/恢复说明；没有request ID不能编造查询或判定未处理。新的实质故障修复及允许范围须明确记录，不能反复复制max1文件自动扩张。未来真正恢复后按原逐阶段审图/分件/布局/安装/两轮真实Play/视觉/record/GIF/审计完成后才串行交接；原两轮Play授权仍有效，未代用户美术批准。

关键证据：`{blocked_file.name}`、`{scope_file.name}`、`{release_file.name}`、`{assess_file.name}`、`{tooling_file.name}`、transport_fix_20261029.json、两份authorized_resume/authorized_proxy_resume及全部read_only_service_recheck/unauthenticated_upload_diagnosis原件。13:46旧封存及第一次审计失败证据完整保留。
'''
original_next=(D/'next_task_blocked_before_resume_20261029.md').read_text(encoding='utf-8')
tail=original_next[original_next.index('## WinterOgre身份、生产路径与原契约'):]
next_text=f'''# WinterOgre(index111) 五次结果不明后的阻断恢复入口

在E:/MyTowerGame继续敌人四方向串行任务。当前停在真实图像服务/传输阻断，未完成角色，不自动新增付费请求。

## 当前状态和唯一所有权

chain.state=blocked，owner_thread_id `{OWNER}`，dispatch_token `{TOKEN}`，角色WinterOgre111，user_approved=false。99/108：99项completed_pending_user_art_review，PossessedWarg79及WinterOgre111两项blocked，WinterWarg112/WinterWolfTypeA113/WinterWolfTypeB114/Wolf115/WolfHound116/WolfMounfed117/Zombie118七项not_started。108是授权数量，终项Zombie118。AllGIF1594、当前角色新增0，没有后继。

blocked期间只读核对文件和既有服务结果；不得生产/Unity/付费操作。不能凭超时抢锁或新聊天重置计数。真正满足恢复条件后，由正确owner明确记录恢复决定再active；其他聊天只读并按用户授权协议完成所有权交接。

## 先完整读取

1. E:/MyTowerGame/AGENTS.md及ProjectSettings/ProjectVersion.txt。
2. Docs/EnemyDirectionReview/README.md、PREFAB_CHANGES_SUMMARY_20261026.md。
3. Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、实时conversation_chain.json/progress.json及本文件。
4. {relative_handoff}。
5. {relative_block}、WinterOgre/{scope_file.name}、WinterOgre/{release_file.name}、WinterOgre/{assess_file.name}、WinterOgre/{tooling_file.name}。
6. standing_network_recovery_authorization_20261028.json、WinterOgre/standing_recovery_application_20261029_Up.json、authorized_resume_20261029.json、authorized_proxy_resume_20261029.json、transport_fix_20261029.json（后四个在WinterOgre下）。
7. WinterOgre下全部read_only_service_recheck和unauthenticated_upload_diagnosis证据，尤其最新read_only_service_recheck_20261029T063122Z.json。
8. WinterOgre/reference_review_20261029.json、anatomy_plan.json、source_contract_20261029.json、original_serialized_objects_20261029.json、incremental_before_20261029.json（files是dict）。
9. WinterOgre/generation/Up及revision_01/02/03/04的request、intent、console、uncertain_result原件；Down只有prompt。

## 五次请求与所有已消耗边界

Up initial与revision_01为Curl55；revision_02为fetch failed/ECONNRESET、TLS建立前断开；本轮revision_03为Curl55；通过修复代理路径的revision_04为Curl52 Empty reply from server。五次全部没有HTTP状态、raw.png、result.json或服务查询ID，费用仍未知。原自动2/2不变；本轮在当前继续指令及既有同类故障静默恢复授权下分别记录的两个代理选择max1决定也都已消耗，不能冒称用户指定预算或未消耗。没有Down请求。

三次鉴权/v1/models与/v1/usage均HTTP200、密钥有效/余额充足，但只有聚合数据：图像key当日15次/$1.05始终未变、账户余额变动，不能关联五个具体请求或推定免费。无密钥小POST401不证明图片服务恢复。无密钥大multipart直连上传71446字节即Curl55，经系统现有127.0.0.1:7897代理完整上传660604字节、HTTP401、证书验证0；这仅证明代理完成了非鉴权上传对照，正式代理请求仍空回复，不是图像上游成功证据。

停止新的付费请求，不新建Up05、不重置自动2/2或两个max1、不用Down或其他角色探针。先检查原结果是否实际回来、是否仍有活动生成进程、能否取得服务方针对既有请求的处置/恢复说明；无query ID不编造查询，不把任何unknown改成失败/未收费。仅再次看到GET200、余额正常或401不足以再次执行。不要反复复制单次授权文件自动增加次数。新的实质故障修复及允许的有界执行范围必须明确落盘；既有成功raw若找回必须复用。

不要运行任何已完成的prepare/baseline/网络准备/封存/finalize脚本，不覆盖原记录或删除清单绕过防重。当前role没有生成图可审、没有stage/install/Verify/Play/两轮168检查/record/运行媒体，不能借前任结果宣称通过。其余7项各只有8个reference文件，无独立可恢复工作；PossessedWarg旧Downunknown保持，不重发。

Docs CLI保留-UseSystemLocalProxy选项：当前仅允许WinterOgre Up04和首次Down，Curl显式--proxy http://127.0.0.1:7897 --noproxy空，不改系统设置，HTTPS同一AIHub端点、证书验证开启、Bearer仅stdin、无重试/重定向。Up04已有request/uncertain，不可重发；首次Down也不能拿来探针。当前默认直连的小请求可通而上传不通，不能删除代理修复证据或用其他模型/端点/质量绕过。

需要真实允许的新Image API工作时先读imagegen技能，保持AIHub https://aihub.dog/v1、gpt-image-2/medium/1536x1024/n1，DPAPI密钥C:/Users/Administrator/.codex/secrets/aihub-image-key.clixml只运行时解密且仅发aihub.dog、不跨域带密钥、不输出或写明文，结束清理；按实际格式尺寸保存，usage估算不是账单。

'''+tail

# Freeze previous live files before publishing, then block the chain last.
backup=D/('current_resume_docs_before_'+stamp);assert not backup.exists();backup.mkdir()
tracked=[H/'progress.json',H/'conversation_chain.json',H/'NEXT_ENEMY_TASK.md',H.parent/'README.md',H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md']
for p in tracked:(backup/p.name).write_bytes(p.read_bytes())
assert not handoff.exists();handoff.write_bytes(handoff_text.encode('utf-8'))
(H/'NEXT_ENEMY_TASK.md').write_bytes(next_text.encode('utf-8'))
for file,begin,end in [(H.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),(H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    raw=file.read_bytes();a=raw.index(begin.encode())+len(begin);b=raw.index(end.encode(),a)
    changed=raw[:a]+b'\n'+live.encode('utf-8')+b'\n'+raw[b:]
    if file.name=='README.md':changed+=b'\n\n'+live.encode('utf-8')+b'\n'
    file.write_bytes(changed)
progress=copy.deepcopy(progress_before);item=next(i for i in progress['items'] if i['name']==NAME)
item.update(status='blocked',user_approved=False,blocked_at=now(),blocked_record=relative_block,blocked_reason=reason,
    recovery_stage='Five_uncertain_including_post_proxy_fix_request',total_uncertain_requests=5,current_continuation_requests=2,
    allowance_usage=blocked['allowance_usage'],unity_release_file=release_file.relative_to(ROOT).as_posix())
progress.update(status='blocked',current=NAME,updated_at=now(),completed_count=99)
assert [i for i in progress['items'] if i['name']!=NAME]==[i for i in progress_before['items'] if i['name']!=NAME]
write(H/'progress.json',progress)
for p in [handoff,H/'NEXT_ENEMY_TASK.md']:
    t=p.read_text(encoding='utf-8');assert '\ufffd' not in t and OWNER in t and TOKEN in t
chain=copy.deepcopy(chain_before)
chain.update(state='blocked',current_blocked=True,current_stage='WinterOgre_five_uncertain_after_proxy_transport_fix',
    blocked_reason=reason,stop_reason=reason,stopped_at=now(),updated_at=now(),successor_created=False,dispatch_ready_for=None,
    completed_count_snapshot=99,previous_handoff_file=chain_before['last_handoff_file'],last_handoff_file=relative_handoff,
    handoff_sha256=sha(handoff),recovery_file=relative_block,last_stage_evidence=relative_block,
    unity_release_file=release_file.relative_to(ROOT).as_posix(),successor_assessment=assess_file.relative_to(ROOT).as_posix(),
    progress_sha256_at_stop=sha(H/'progress.json'),
    resume_stage='Read-only existing-result/provider disposition inspection; no new paid request from repeating successful GET or unauthorized control',
    resume_conditions=['Recover an existing raw/result, or obtain concrete disposition/recovery information for the authorized image operation.',
        'Retain all five unknown outcomes and charges; automatic2/2 and both separately recorded max1 decisions are consumed.',
        'Do not repeatedly extend allowances on unchanged GET200/401 evidence. A substantive repair and any permitted bounded execution must be explicit.'])
chain.setdefault('stage_history',[]).append(dict(character=NAME,status='blocked',closed_at=now(),owner_thread_id=OWNER,dispatch_token=TOKEN,
    final_evidence=relative_block,handoff_file=relative_handoff,total_uncertain=5,successor_created=False))
receipt=D/('current_resume_closeout_receipt_'+stamp+'.json');chain['closeout_receipt_file']=receipt.relative_to(ROOT).as_posix()
write(receipt,dict(observed_at=now(),status='blocked',completed_count=99,current_continuation_requests=2,total_uncertain=5,
    handoff=relative_handoff,blocked_record=relative_block,successor_created=False,owner_thread_id=OWNER,dispatch_token=TOKEN,
    delivered_sha256={p.relative_to(ROOT).as_posix():sha(p) for p in [handoff,H/'NEXT_ENEMY_TASK.md',H.parent/'README.md',H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md',H/'progress.json',blocked_file,scope_file,release_file,assess_file,tooling_file]},
    planned_chain_sha256=hashlib.sha256(data(chain)).hexdigest().upper(),final_workspace_write='conversation_chain.json active -> blocked; same owner/token'),fresh=True)
owner();(H/'conversation_chain.json').write_bytes(data(chain))
print(json.dumps(dict(status='blocked',completed_count=99,current_turn_requests=2,total_uncertain=5,
    unity_errors=2,compiler_failed=False,production_delta=changes,handoff=relative_handoff,
    blocked_record=relative_block,complete_recovery_prompt=(H/'NEXT_ENEMY_TASK.md').relative_to(ROOT).as_posix(),successor_created=False)))
