from session_current import *
from mcp_call import URL
import shutil, subprocess

chain = owner()
progress = read(RUN/'progress.json')
queue = read(HERE/'queue_completion_audit_resolved_20261030.json')
final = read(HERE/'final_validation_20261030.json')
binding = read(HERE/'final_version_binding_20261030.json')
archive = read(RUN.parent/'AllGIF/manifest.json')
assert progress['completed_count'] == progress['authorized_count'] == len(progress['items']) == 108
assert progress['current'] is None and progress['remaining_count'] == 0
assert all(r['status'] == 'completed_pending_user_art_review' and r['user_approved'] is False for r in progress['items'])
assert queue['pass'] and queue['historical_completed_runs_checked'] == 216 and queue['selected_actual_png_files_hashed'] == 72942
assert queue['progress_sha256'] == sha(RUN/'progress.json') and queue['allgif_manifest_sha256'] == sha(RUN.parent/'AllGIF/manifest.json')
assert final['record_completed'] and final['passes'] == 168 and final['failures'] == 0 and archive['count'] == 1760
assert snapshot() == binding['all_production_fingerprints']
for p, s in binding['immutable_documents'].items():
    assert sha(ROOT/p) == s, p

stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup = HERE/('docs_before_queue_close_'+stamp)
backup.mkdir(exist_ok=False)
paths = [RUN/'progress.json', RUN/'conversation_chain.json', RUN/'NEXT_ENEMY_TASK.md',
         RUN/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md', RUN.parent/'README.md', HERE/'final_validation_20261030.json']
backups = []
for p in paths:
    dest = backup/p.relative_to(ROOT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dest)
    assert sha(p) == sha(dest)
    backups.append({'source': p.relative_to(ROOT).as_posix(), 'backup': dest.relative_to(ROOT).as_posix(), 'sha256': sha(p)})
save(backup/'manifest.json', backups)

ps = r'''$generationProcesses = @(Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and $_.Name -match '^(node|curl|powershell|pwsh)\.exe$' -and $_.CommandLine -match '(generate_character\.ps1|generate\.mjs)' } | Select-Object ProcessId, Name); ConvertTo-Json -InputObject $generationProcesses -Compress'''
check = subprocess.run(['powershell.exe', '-NoProfile', '-Command', ps], check=True, capture_output=True, text=True, encoding='utf-8')
processes = json.loads(check.stdout)
save(HERE/'image_process_snapshot_final_20261030.json', {'observed_at': now(), 'active_generation_processes': processes, 'method': 'Current Windows process inventory; only executable and PID persisted, no credentials or command lines.'})
assert not processes

owner()
c = Client()
release = {'observed_at': now(), 'transport': URL, 'project': c.identity()}
for key, args in [('errors', {}), ('compile_errors', {'filter_text': 'error CS'})]:
    result = c.tool('read_console', {'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json', **args})
    release[key] = result.get('structuredContent') or json.loads(result['content'][0]['text'])
assert release['errors']['data'] == release['compile_errors']['data'] == []
release['state'] = fresh_state(c, 'PossessedWarg queue-complete final release')
release['probe'] = probe(c)
idle(release['probe'])
release.update(success=True, console_cleared=False, no_new_Play=True, protocol_history=c.history)
save(HERE/'handoff_release_final_20261030.json', release)
closing_scope = audit()
assert closing_scope['pass'] and snapshot() == binding['all_production_fingerprints']
save(HERE/'scope_at_queue_close_20261030.json', closing_scope)

rel = lambda p: p.relative_to(ROOT).as_posix()
closed_at = now()
summary_path = RUN.parent/('PREFAB_CHANGES_SUMMARY_'+stamp+'_COMPLETE.md')
handoff_path = RUN/'conversation_handoffs'/(stamp+'_PossessedWarg_queue_complete.md')
queue_path = HERE/'queue_completion_audit_resolved_20261030.json'
release_path = HERE/'handoff_release_final_20261030.json'
closure_path = HERE/'queue_closure_manifest_20261030.json'
assert not summary_path.exists() and not handoff_path.exists() and not closure_path.exists()

live = f'''{closed_at} 续作队列已完成 **108/108**，剩余0，progress.current=null；全部仍为completed_pending_user_art_review、user_approved=false，首批10个既有用户批准身份不变。最后角色PossessedWarg79已完成单角色安装、两轮真实Play（各84PASS/0FAIL，共168PASS/0FAIL、681PNG）、实际视觉复核和record。最终版本Up_local02_Down_AI01local02_alpha01_layout03_nativeattack01；审阅14张时序板的312采样位/301不同真实PNG、5张未裁PNG，以及12个最终GIF全部458编码帧/22连续板，未实时播放或逐张看完681PNG。

AllGIF现为**1760**：本角色新增16=12最终+4修前历史；全部旧1744项及新增来源/副本SHA一致。全108项有效完成证据已逐项核验（216轮、72942原始PNG哈希、1296最终GIF），4个早期首次安装失败已按现存成功修复清单解析，旧失败保留。该审计不代表重新运行或重新视觉审核其他107角色。证据：[最终队列汇总]({summary_path.relative_to(RUN.parent).as_posix()})、[本角色最终验证](Remaining_20261024/PossessedWarg/final_validation_20261030.json)、[GIF集中入口](AllGIF/index.html)。

本角色仅新增20个Directions生产文件，battle与Reporter自动时间戳各改1，共22变化、0删除、增量unexpected0；22生产绑定与prePlay完全一致，原source/atlas/meta及原侧动画合同保持。历史全局scope失败和开工前build_info漂移单列保留，不宣称全局零漂移。旧Down请求结果/可能费用仍unknown；本次唯一有界Down revision_01为HTTP200，费用未独立核账，无新增Up或额外付费探针。8088已重新核对E:/MyTowerGame/2022.3.62f3c1，clean Boot、非Play、空闲、error0、scriptCompilationFailed=false。串行链现应为complete；队列为空，不创建后继或继续生产。实时链以conversation_chain.json为准。'''

summary = f'''# 敌人四方向续作队列完成记录

记录时间：{closed_at}。工程：E:/MyTowerGame，Unity 2022.3.62f3c1，MCP HTTP Local 8088。

108个续作角色已全部内部完成，剩余0；这108项均为`completed_pending_user_art_review`、`user_approved=false`。首批10项既有用户美术批准记录保持，不能将108项续作完成视作用户美术批准。

| 本次收口项 | 实际结果 |
|---|---|
| 最后角色 | PossessedWarg，index79 |
| 最终版本 | Up_local02_Down_AI01local02_alpha01_layout03_nativeattack01 |
| 两轮真实Play | runtime_r01 / runtime_updeath_r01，各84PASS/0FAIL，合计168PASS/0FAIL；341+340=681PNG |
| 视觉范围 | 最终离线四向/分件/atlas、两轮four_directions及strip；14板312采样位/301不同PNG、5张未裁PNG；12个最终GIF全部458编码帧/22连续板 |
| 视觉限制 | 按编码序静态审阅，未实时播放；未逐张审完全部681PNG。死亡为逐renderer重叠淡出，未声称一体alpha |
| 安装与合同 | Verify PASS；14切片pivot/PPU、依赖/collector通过；原侧float/PPtr/事件/时长loop保持；原controller未变，派生controller使用既有六状态生成策略 |
| 增量生产范围 | 5705→5725路径；22变化=20新增Directions+本角色battle+Reporter时间戳；0删除、unexpected0；22绑定与prePlay相同 |
| GIF归档 | 1744→1760；PossessedWarg 16项=12最终+4修前历史，全部旧/新增来源和副本SHA一致 |
| 全续作证据审计 | 108项、216轮、72942张原始PNG哈希、1296个最终来源/归档GIF；0未完成项 |
| 最终编辑器 | 8088身份正确、单一clean Boot、非Play、无review/balance/recording/manual/编译/更新/域重载，ready=true，error0，scriptCompilationFailed=false |

PossessedWarg复用旧Up HTTP200原图，仅发送一次本轮有界Down revision_01请求并成功HTTP200。两方向原图保留；局部耳垫、后跟、Down躯干重复口吻修补和透明整理属于本地像素衍生，不冒充AI返回。自身Walk/Attack为0.5s，Death为0.416666657s；按原生0.166666672s愤怒、0.333333343s发力适配上下攻击。4个步行GIF按真实相位累计10ms边界从480/490ms修为500ms，边界舍入不超过5ms；修前4GIF和2manifest保留。

原Down请求没有raw/result/服务查询ID，结果与可能费用永久unknown；不改写为失败、未发送、未收费或ECONNRESET。新请求结果usage为本地低置信估算，费用未独立核账。全部21份旧角色证据原字节保持，历史blocked字段及解决说明并存。

全队列审计读取每个角色的有效安装Verify、最终选定两轮实际记录/checks/PNG与12个GIF。DreadEye的repair_01、Horse和Pony的repair_controller_r01、PirateBoar的repair_shot_r01是现存成功修复证据；首次失败清单保留。该审计核查历史证据，并未重新运行或重新视觉审核其他107个角色。早期全局scope失败及父交接前build_info漂移继续按历史保留；当前通过仅为PossessedWarg本轮增量范围。

原冻结[PREFAB_CHANGES_SUMMARY_20261026.md](PREFAB_CHANGES_SUMMARY_20261026.md)、全局基线和首批用户批准记录没有改写。没有构建、设备部署或长期战斗验收，也没有新增后继聊天；空队列的串行链直接收口。

证据入口：

- [progress.json](Remaining_20261024/progress.json) 与 [conversation_chain.json](Remaining_20261024/conversation_chain.json)
- [AllGIF集中浏览](AllGIF/index.html) 与 [归档核对](Remaining_20261024/PossessedWarg/gif_archive_verification_20261030.json)
- [最终角色验证](Remaining_20261024/PossessedWarg/final_validation_20261030.json) 与 [prePlay/运行/生产版本绑定](Remaining_20261024/PossessedWarg/final_version_binding_20261030.json)
- [实际视觉审阅](Remaining_20261024/PossessedWarg/visual_review_final_20261030/review.json) 与 [连续GIF编码帧](Remaining_20261024/PossessedWarg/visual_review_final_20261030/continuous_gifs/manifest.json)
- [全108项完成证据审计](Remaining_20261024/PossessedWarg/queue_completion_audit_resolved_20261030.json)，保留[最初审计诊断](Remaining_20261024/PossessedWarg/queue_completion_audit_20261030.json)
- [图像请求账本](Remaining_20261024/PossessedWarg/generation_final_accounting_20261030.json)、[本轮增量范围](Remaining_20261024/PossessedWarg/scope_at_queue_close_20261030.json)、[最终Unity交还](Remaining_20261024/PossessedWarg/handoff_release_final_20261030.json)
- [最终交接]({handoff_path.relative_to(RUN.parent).as_posix()}) 与 [收口哈希清单](Remaining_20261024/PossessedWarg/queue_closure_manifest_20261030.json)
'''
summary_path.write_text(summary, encoding='utf-8')
handoff = f'''# PossessedWarg79完成与108项队列收口

{live}

最终owner={os.environ['CODEX_THREAD_ID']}，dispatch_token={TOKEN}。完成后chain.state=complete，current_character=null；保留旧owner/token、dispatch_history、blocked_history和已存在的失败/unknown证据，停止当前生产所有权。没有下一角色，也没有创建后继。

完整本轮汇总：{rel(summary_path)}。
全队列有效证据：{rel(queue_path)}；仅本角色两轮实测发生在本聊天，不把其他107角色历史实测说成本次重跑。
最终Unity交还：{rel(release_path)}。
收口前完整文档与chain备份：{rel(backup/'manifest.json')}。
若后续用户提出返修，应按新的明确角色范围重新建立所有权和增量基线；不要自动重跑或重发图片请求。
'''
handoff_path.write_text(handoff, encoding='utf-8')

readme_path = RUN.parent/'README.md'
text = readme_path.read_text(encoding='utf-8')
text, n = re.subn(r'<!-- ENEMY_README_LIVE_BEGIN -->.*?<!-- ENEMY_README_LIVE_END -->',
                  lambda m: '<!-- ENEMY_README_LIVE_BEGIN -->\n'+live+'\n<!-- ENEMY_README_LIVE_END -->', text, flags=re.S)
assert n == 1
old_count_text = '所有 GIF 集中于 [AllGIF/index.html](AllGIF/index.html)；2026-10-29 本轮当前清单为 1744 个文件'
assert text.count(old_count_text) == 1
text = text.replace(old_count_text, '所有 GIF 集中于 [AllGIF/index.html](AllGIF/index.html)；2026-10-30 最终当前清单为 1760 个文件')
text += '\n\n2026-10-30 队列收口：108/108内部完成、剩余0，全部续作仍待用户美术审核。PossessedWarg79最终两轮168PASS/0FAIL，AllGIF1760。完整证据与限制见[最终队列汇总]('+summary_path.relative_to(RUN.parent).as_posix()+')；历史停止说明按原日期保留，当前状态以页首实时块及progress/chain为准。\n'
readme_path.write_text(text, encoding='utf-8')
prompt_path = RUN/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md'
text = prompt_path.read_text(encoding='utf-8')
text, n = re.subn(r'<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->.*?<!-- ENEMY_SERIAL_LIVE_STATE_END -->',
    lambda m: '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->\n'+live+'\n\n队列完成后只读展示证据；不按后文历史剩余名单重复执行。新的美术返修按用户明确角色与新所有权启动。\n<!-- ENEMY_SERIAL_LIVE_STATE_END -->', text, flags=re.S)
assert n == 1
prompt_path.write_text(text, encoding='utf-8')
(RUN/'NEXT_ENEMY_TASK.md').write_text(f'''# 续作队列已完成，无下一角色

{closed_at}：E:/MyTowerGame续作108/108内部完成，remaining_count=0、progress.current=null，conversation_chain.state=complete。不要创建后继、重复生产或重发生成请求。

108项均保持completed_pending_user_art_review、user_approved=false；只有用户明确美术批准才可改变。首批10项既有用户批准记录和20261026冻结总结没有修改。

最后角色PossessedWarg79完成：Up_local02_Down_AI01local02_alpha01_layout03_nativeattack01；两轮真实Play各84PASS/0FAIL，共681PNG；已实际审阅最终四向/分件、两轮画面、14板312采样位/301不同PNG、5张未裁PNG及12GIF全部458编码帧/22连续板。未实时播放或逐张看完681PNG。

全队列有效证据审计通过：108项、216轮、72942原始PNG哈希、1296最终GIF；初次失败安装与后续成功修复分开保留，不把旧失败抹除。AllGIF1760（含历史和首批材料，不等于完成角色数）；旧1744及本次新增16来源/副本哈希一致。

本轮仅PossessedWarg battle/Directions与Reporter实际Play时间戳有增量变化；原source/atlas/meta/原侧动画合同保持。历史global scope失败和开工前build_info漂移未改判全局PASS。旧Down结果/可能费用仍unknown，本轮唯一有界Down revision_01 HTTP200；费用未独立核账，旧21份证据保持。

最后8088身份核对正确，Unity 2022.3.62f3c1，单一clean Boot、非Play、无任务/编译失败、error0。未构建、部署或做设备/长期战斗验收。未创建后继、子代理或自动化，未做Git变更或桌面控制。

当前入口：

- 完整汇总：{rel(summary_path)}
- 最终交接：{rel(handoff_path)}
- 全队列审计：{rel(queue_path)}
- 最后角色验证：{rel(HERE/'final_validation_20261030.json')}
- Unity交还：{rel(release_path)}
- GIF浏览：Docs/EnemyDirectionReview/AllGIF/index.html
- 收口清单：{rel(closure_path)}

后续若用户明确要求某角色返修，先读取当前规则、这份收口记录、progress/chain和该角色有效版本，按新的任务范围建立所有权与增量基线。历史请求unknown不因队列完成变为已知费用；没有用户新任务时保持完成状态。
''', encoding='utf-8')

progress.update(updated_at=closed_at, queue_closed_at=closed_at, queue_state='complete', last_completed_handoff=rel(handoff_path),
    completion_audit=rel(queue_path), completion_summary=rel(summary_path))
item = next(r for r in progress['items'] if r['name'] == NAME)
item['final_handoff_release'] = rel(release_path)
(RUN/'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
final.update(queue_state='complete', queue_completion_audit=rel(queue_path), queue_completion_audit_sha256=sha(queue_path),
    queue_summary=rel(summary_path), final_handoff_release=rel(release_path), final_handoff_release_sha256=sha(release_path),
    completed_count=108, remaining_count=0, progress_sha256_at_queue_close=sha(RUN/'progress.json'), closed_at=closed_at)
(HERE/'final_validation_20261030.json').write_text(json.dumps(final, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
for p, s in binding['immutable_documents'].items():
    assert sha(ROOT/p) == s, p
assert read(RUN/'progress.json')['items'][-1]['user_approved'] is False
owner()
closure_files = [RUN/'progress.json', RUN/'NEXT_ENEMY_TASK.md', prompt_path, readme_path, summary_path, handoff_path,
    HERE/'final_validation_20261030.json', HERE/'final_version_binding_20261030.json', HERE/'generation_final_accounting_20261030.json',
    HERE/'gif_archive_verification_20261030.json', queue_path, release_path, HERE/'scope_at_queue_close_20261030.json',
    HERE/'image_process_snapshot_final_20261030.json', RUN.parent/'AllGIF/manifest.json', backup/'manifest.json']
save(closure_path, {'closed_at': closed_at, 'owner_thread_id': os.environ['CODEX_THREAD_ID'], 'dispatch_token': TOKEN,
    'completed_count': 108, 'remaining_count': 0, 'user_approved_in_continuation_queue': 0,
    'final_production_matches_preplay_and_binding': True, 'immutable_documents_unchanged': binding['immutable_documents'],
    'files': {rel(p): sha(p) for p in closure_files}, 'preclose_chain_backup': next(r for r in backups if r['source'].endswith('conversation_chain.json')),
    'no_successor_created': True, 'no_more_Unity_or_production_operations_after_chain_complete': True})

chain['terminal_previous_live_state'] = {k: chain.get(k) for k in ['state', 'current_character', 'current_stage', 'last_stage_evidence', 'resume_character', 'resume_stage', 'successor_created', 'successor_thread_id', 'unity_release_file', 'last_handoff_file', 'successor_policy']}
chain['completed_handoffs'].append({'character': NAME, 'status': 'completed_pending_user_art_review', 'current_stage': 'recorded_pending_user_art_review',
    'closed_at': closed_at, 'owner_thread_id': os.environ['CODEX_THREAD_ID'], 'dispatch_token': TOKEN, 'handoff_file': rel(handoff_path), 'final_evidence': rel(HERE/'final_validation_20261030.json')})
chain['stage_history'].append({'character': NAME, 'stage': 'queue_complete_pending_user_art_review', 'observed_at': closed_at, 'evidence': rel(closure_path)})
chain.update(state='complete', current_character=None, current_stage='queue_complete_pending_user_art_review', current_blocked=False,
    completed_count_snapshot=108, remaining_count=0, last_completed_character=NAME, last_owner_character=NAME,
    character_status_at_handoff='completed_pending_user_art_review', previous_handoff_file=chain['last_handoff_file'], last_handoff_file=rel(handoff_path),
    handoff_sha256=sha(handoff_path), progress_sha256_at_handoff=sha(RUN/'progress.json'), updated_at=closed_at, completed_at=closed_at,
    unity_release_file=rel(release_path), unity_release_is_historical=False, last_stage_evidence=rel(closure_path),
    queue_completion_audit=rel(queue_path), completion_summary=rel(summary_path), queue_closure_manifest=rel(closure_path),
    successor_created=False, successor_thread_id=None, dispatch_ready_for=None, resume_character=None, resume_stage='completed',
    successor_policy='Queue exhausted at 108/108. No successor. All continuation art remains pending explicit user approval.',
    ownership_transfer_note='Final owner completed PossessedWarg79, archived actual evidence and released Unity. Queue is empty; no ownership transfer or new chat. Stop production and Unity operations.')
# Final workspace mutation: terminal chain state. All later activity must be read-only.
(RUN/'conversation_chain.json').write_text(json.dumps(chain, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'state': 'complete', 'completed': 108, 'remaining': 0, 'allGIF': archive['count'], 'user_approved': False,
    'successor_created': False, 'summary': rel(summary_path), 'handoff': rel(handoff_path), 'closure_manifest': rel(closure_path),
    'chain_sha256': sha(RUN/'conversation_chain.json'), 'Unity_release': rel(release_path)}, ensure_ascii=False))
