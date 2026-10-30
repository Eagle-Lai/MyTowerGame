"""Persist this actual 402 failure, release evidence and one serial handoff."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, uuid

D=Path(__file__).resolve().parent
HERE=D.parent
ROOT=HERE.parents[2]
REL=HERE.relative_to(ROOT).as_posix()
now=datetime.now(timezone(timedelta(hours=8)))
stamp=now.strftime('%Y%m%d_%H%M%S')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
write=lambda p,v:p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
chain=read(HERE/'conversation_chain.json')
assert chain['state']=='active' and chain['owner_thread_id']==os.environ['CODEX_THREAD_ID']
assert chain['current_character']==D.name and chain['dispatch_token']=='scarab-to-scarabmounted-f3ab213fcd7c48c289d70377847fce8f'
assert not (D/'blocked_generation_20261026.json').exists()
request=read(D/'generation/Up/request.json')
result=read(D/'generation/Up/result.json')
assert result['status']==402 and result['error']['code']=='insufficient_balance'
assert not (D/'generation/Up/raw.png').exists()
assert not (D/'generation/Down/request.json').exists()
assert not (D/'installed_manifest.json').exists()
baseline=read(D/'incremental_before_20261026.json')
files={p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
changes=[{'path':p,'before':s,'after':files.get(p)} for p,s in baseline['files'].items() if files.get(p)!=s]
added=sorted(set(files)-set(baseline['files']))
assert not changes and not added, 'Unexpected production changes; do not hand off'
response=read(D/'unity_release_request_response.json')
assert response['success'] and response['project']['projectRoot']=='E:/MyTowerGame'
state,errors,probe_result=response['results']
probe=probe_result['structuredContent']['data']['result']
assert probe['scene']=='Assets/Scenes/Boot.unity'
assert not any(value for key,value in probe.items() if key!='scene')
assert state['data']['advice']['ready_for_tools']
assert not state['data']['compilation']['is_domain_reload_pending']
assert errors['structuredContent']['data']==[]
release_path=D/('unity_release_blocked_'+stamp+'.json')
write(release_path,dict(observed_at=response['observed_at'],project=response['project'],state=state['data'],probe=probe,error_count=0,errors=[],production_operations_started=False,result='safe_to_handoff_no_unity_changes',full_response='unity_release_request_response.json'))
reason=('Up first-time image request returned explicit HTTP 402 insufficient_balance: Upstream image account has insufficient balance. No raw.png returned. Down was not requested after the balance failure; its prepared prompt remains. Do not resend this request or start further paid attempts without evidence that upstream balance/availability is restored. Preserve the original request/result. No stage, install, Play or production changes were performed.')
progress=read(HERE/'progress.json')
before_completed=progress['completed_count']
item=next(i for i in progress['items'] if i['name']==D.name)
item.update(status='blocked',blocked_record=REL+'/'+D.name+'/blocked_generation_20261026.json',blocked_at=now.isoformat(),blocked_reason=reason,visual_reviewed=False,user_approved=False)
eligible=[i for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved','blocked']]
started=[i for i in eligible if i['status']!='not_started']
next_item=min(started or eligible,key=lambda i:i['index'])
assert next_item['name']=='ShardLizard' and next_item['index']==94
assert before_completed==79
progress.update(updated_at=now.isoformat(),current=next_item['name'])
write(HERE/'progress.json',progress)
gif_count=read(HERE.parent/'AllGIF/manifest.json')['count']
blocked=dict(character=D.name,index=93,status='blocked',blocked_at=now.isoformat(),owner_thread_id=chain['owner_thread_id'],dispatch_token=chain['dispatch_token'],stage='reference prepared; initial Up generation failed',blocked_reason=reason,
    request_results={'up':result,'down':{'status':'not_requested','reason':'Stopped further paid requests after the upstream balance error','prompt':'generation/Down/prompt.txt'}},
    artifacts={'anatomy_plan':'anatomy_plan.json','up_prompt':'generation/Up/prompt.txt','up_request':'generation/Up/request.json','up_result':'generation/Up/result.json','down_prompt':'generation/Down/prompt.txt','installation_baseline':'incremental_before_20261026.json'},
    evidence_hashes={p:sha(D/p) for p in ['anatomy_plan.json','generation/Up/prompt.txt','generation/Up/request.json','generation/Up/result.json','generation/Down/prompt.txt']},
    reference_review=read(D/'anatomy_plan.json')['reference_review'],generated_visual_review='Not performed: no generated image returned.',
    production_snapshot={'path':'incremental_before_20261026.json','file_count':len(files),'changed_files_before_block':changes,'added_files_before_block':added,'protected_six_unchanged':baseline['protected_scarabmounted'],'legacy_scope_reference':baseline['legacy_scope_reference']},
    production_changes=False,unity={'project':response['project'],'release_file':release_path.name,'state':'Boot, non-Play, non-dirty, idle, no recorder/review/manual simulation, compile failed false, errors 0; only read-only probes used'},
    runtime={'normal_round':'not_executed','up_death_round':'not_executed','verify':'not_executed','media_review':'not_executed','record':'not_executed','new_gifs':0},
    progress={'completed_count':79,'authorized_count':108,'next':'ShardLizard','allgif_count':gif_count},
    next_recovery='After upstream image-account balance and compatible-account availability are restored, inspect preserved requests and use a new unique recovery path. Do not overwrite or resend the original attempt. Down has never been requested. Full image review, staging, install Verify, two real 84-check Play rounds, media review, record and GIF archive remain required.')
write(D/'blocked_generation_20261026.json',blocked)
handoff=HERE/'conversation_handoffs'/f'{stamp}_ScarabMounted.md'
handoff.write_text(f'''# ScarabMounted 阻断与串行交接

时间：{now.isoformat()}。项目 E:/MyTowerGame / Unity 2022.3.62f3c1。唯一执行线程 {chain['owner_thread_id']}；未使用 fork、子代理或并发角色。

## 实际阶段、素材与请求

- 接棒锁 state=active、owner 为本运行时 CODEX_THREAD_ID、current_character=ScarabMounted、token 完全匹配后才开始工作。
- 实际查看原始图集、完整源和战斗 prefab 离线图，读取序列化结构及目标未提交差异。六足深橄榄色甲虫，橙眼、长触角、浅金弯颚、奶油色关节足、皮鞍，无骑手、尾巴或翅膀；触角随头部，不新增独立 Feelers。Battle Head 原本引用 Scarab 图集，保持原绑定契约。
- 仅执行一次 prepare；保存 anatomy_plan 与 Up/Down 提示词。没有覆盖旧请求或生成结果。
- Up 首次请求：`ScarabMounted/generation/Up/request.json`；实际返回 HTTP 402 `insufficient_balance`，message=`Upstream image account has insufficient balance`；结果为 `generation/Up/result.json`，无 raw.png。
- **Down 未请求**：收到余额错误后停止后续付费调用；只有 prompt.txt。不得描述为 Down 失败、已收费或已有结果。
- 使用现有已授权 AIHub generate_character.ps1/generate.mjs：gpt-image-2、medium、1536x1024、n=1；密钥仅在运行时注入且已清理。没有重发 Up，也没有重发 Scarab 两个503、SabretoothTiger 或 PossessedWarg 的旧请求。

## 生产范围与 Unity 安全交还

- 安装前独立增量快照 `ScarabMounted/incremental_before_20261026.json` 共 {len(files)} 文件；收尾复核 changed=[]、added=[]，六项生产/源资源保护指纹全部不变。目标开工前 git diff 为空，用户其余 dirty 全部保留。
- 未 stage、安装、Verify、进入 Play、刷新 Unity、修改 C# 或生产 prefab。普通死亡/Up死亡两轮均未执行；未做生成图或运行媒体审阅、record 或 GIF 新增，不存在完成证据。
- 通过现有 mcp_call.py 的 Client.identity 动态发现完整实例并核对 E:/MyTowerGame / 2022.3.62f3c1。收尾只读现场：Boot、非Play、非dirty、非编译/更新/域重载、无 review/balance/recording/manual 占用、ready=true、scriptCompilationFailed=false、错误0。证据 `ScarabMounted/{release_path.name}`，完整请求/响应 `unity_release_request{{,_response}}.json`。
- 未运行 pull/reset/clean/checkout/commit/push；未改 Luban 表、ConfigJson、Gen、声音系统或其他角色。

## 实时状态与未完成项

- `progress.json`：completed_count=79 / authorized_count=108；ScarabMounted=index93、blocked、visual_reviewed=false、user_approved=false。AllGIF={gif_count}，本角色新增0。
- 原 PossessedWarg(index79)、SabretoothTiger(index91)、Scarab(index92) blocked 完整保留。RoyalBoar 等完成项仍待用户美术批准。
- 完整阻断和哈希：`ScarabMounted/blocked_generation_20261026.json`。上游余额/兼容账户可用性恢复后，读取旧结果，按新唯一恢复路径继续；不得覆盖原请求或把失败当成功。Down 尚未请求。安装 Verify、两轮各84项真实Play、实际媒体时序审阅和record/GIF全部仍需完成。

## 下一唯一角色

重新读取实时 items 后，除已有 blocked 外没有可恢复的已开始角色；按 index 下一候选为 ShardLizard(index94)，现仅有参考目录，not_started。后继先评估上游402/503共同阻断；未确认恢复时不得用逐角色新请求试探余额、不得付费重试。可开展独立的参考工作；若已无可独立推进的工作，则依协议保留共同阻断并停止，避免无效请求或空转派发。

新任务必须核对本总结、NEXT_ENEMY_TASK、实时 progress 与 conversation_chain；只有 state=active、owner 等于其运行时线程、角色/token完全匹配才可操作Unity/生产文件。只处理ShardLizard，禁止重复创建或并行角色。当前聊天在所有权转移后停止工程修改。
''',encoding='utf-8')
live=f'2026-10-26 串行续接更新：79/108。ScarabMounted(index93) 已完成参考实际审阅、解剖与 Up/Down 提示词；Up 首次请求明确 HTTP402 insufficient_balance（Upstream image account has insufficient balance），无 raw.png。Down 在余额错误后未请求，仅保留提示词；没有重发任何旧请求。角色 blocked，未 stage/install/Verify/Play/record、未改生产，{len(files)} 文件增量快照与六保护指纹不变，changed=[]、added=[]。Unity只读核对 E:/MyTowerGame / 2022.3.62f3c1，安全交还Boot、非Play、非dirty、空闲、编译失败false、错误0。PossessedWarg、SabretoothTiger、Scarab既有blocked保留；AllGIF实时{gif_count}。下一唯一角色ShardLizard(index94)，先评估上游共同阻断，未确认恢复不得继续付费探测。详见 `ScarabMounted/blocked_generation_20261026.json` 与 `conversation_handoffs/{handoff.name}`；实时事实以progress/chain为准。'
prompt_path=HERE/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md'
text=prompt_path.read_text(encoding='utf-8')
begin='<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->'
end='<!-- ENEMY_SERIAL_LIVE_STATE_END -->'
assert text.count(begin)==1 and text.count(end)==1
text=text.split(begin)[0]+begin+'\n'+live+'\n'+end+text.split(end)[1]
prompt_path.write_text(text,encoding='utf-8')
readme=HERE.parent/'README.md'
with readme.open('a',encoding='utf-8') as f:f.write('\n'+live+'\n')
token='scarabmounted-to-shardlizard-'+uuid.uuid4().hex
next_text=f'''# 当前唯一敌人任务：ShardLizard

在 E:/MyTowerGame 继续敌人四方向串行续作。本聊天只负责 ShardLizard(index94)。接棒 token：{token}；parent_thread_id：{chain['owner_thread_id']}。上一角色交接：`{REL}/conversation_handoffs/{handoff.name}`。

先读取根 AGENTS.md、ProjectSettings/ProjectVersion.txt、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、本文件、conversation_chain.json、实时 progress.json、上级README与PREFAB_CHANGES_SUMMARY_20261026.md、上一交接及ShardLizard已有材料与未提交差异。根AGENTS的FreedomTower_1/D:为旧信息；实际目标E:/MyTowerGame / Unity2022.3.62f3c1，不切工程、不改AGENTS。

只有chain.state=active、owner_thread_id等于本聊天运行时CODEX_THREAD_ID、current_character=ShardLizard、dispatch_token完全等于上述token后，才可操作Unity或生产文件；handoff_ready时只读等待，不超时接管。禁止fork、子代理、并发角色或重复创建ShardLizard聊天。优先恢复现有阶段，禁止重复prepare、付费生成或安装。

上游共同阻断：ScarabMounted(index93)的Up首次请求返回HTTP402 insufficient_balance，message为Upstream image account has insufficient balance，无raw.png；Down未请求。参考已实际审阅、解剖和双向prompt已保存，状态blocked。Scarab(index92)的两个HTTP503 No available compatible accounts、SabretoothTiger(index91)及PossessedWarg(index79)的既有blocked、原request/result保持，全部不得重发、伪造成功或覆盖。收到402后已停止后续付费调用。后继必须先评估余额/兼容账户恢复条件；没有已恢复的证据时，不得通过逐角色新请求或自动重试试探服务。可做不依赖生成的本角色参考工作；若只剩共同阻断，按协议保留准确阻断并停止，不空转创建一串同样受阻聊天。

实时progress=79/108，current=ShardLizard，AllGIF={gif_count}。ShardLizard为not_started，目前仅有reference目录，先核对实际材料。已完成项均保持completed_pending_user_art_review，不能替代用户批准。

上游条件恢复后按原prompt完成本角色：实际原图集/完整prefab/解剖审阅，分件生成和实际审图，透明/边缘/布局检查，安装前增量和六保护指纹，单角色安装Verify，普通死亡与Up死亡两轮各84项真实Unity Play，真实媒体按时序审阅及必要返修，UTF-8观察，record与GIF归档。程序PASS不能替代视觉判断。已有请求结果不明不得重发；所有原件/失败保留。图片API使用已授权AIHub、imagegen技能和原参数gpt-image-2/medium/1536x1024/n=1，密钥运行时注入。

Unity通过现有Remaining_20261024/mcp_call.py的Client.identity动态发现完整实例并确认E:/MyTowerGame /2022.3.62f3c1、HTTP Local8082，不用CatchFish8080。上一安全交还证据为`{REL}/ScarabMounted/{release_path.name}`：Boot、非Play、非dirty、无编译/更新/录像/review/manual占用、scriptCompilationFailed=false、错误0。安装/Play前重新查身份与占用；若改C#必须完成AGENTS的MCP刷新编译/错误闭环。

保留用户dirty；禁止pull/reset/clean/checkout/commit/push，不改配置表、ConfigJson、Gen或声音系统。全局291项历史unexpected不得重置；只记录本轮真实增量。finalize_serial_character.py的ReporterEditor自动Play时间戳应单独归因。

完成或真实阻断后准确更新progress、README、原prompt实时块、NEXT_ENEMY_TASK和conversation_chain，安全交还Unity，写时间戳总结；重新读取items，依CONTINUATION_PROTOCOL只在仍有可独立推进的候选时创建一个唯一全新本地后继并登记真实threadId/hostId，创建后只做一次有界wait，当前聊天停止生产修改。只剩共同阻断时停止并报告。不得把未安装/未运行/未视觉审阅写成完成。
'''
(HERE/'NEXT_ENEMY_TASK.md').write_text(next_text,encoding='utf-8')
assert handoff.read_text(encoding='utf-8') and (HERE/'NEXT_ENEMY_TASK.md').read_text(encoding='utf-8')==next_text
chain.update(state='handoff_ready',dispatch_token=token,current_character='ShardLizard',character_status_at_handoff=next_item['status'],completed_count_snapshot=79,parent_thread_id=os.environ['CODEX_THREAD_ID'],handoff_ready_at=now.isoformat(),last_handoff_file=handoff.relative_to(ROOT).as_posix(),unity_release_file=release_path.relative_to(ROOT).as_posix(),progress_sha256_at_handoff=sha(HERE/'progress.json'),dispatch_ready_for='ShardLizard')
write(HERE/'conversation_chain.json',chain)
dispatch=dict(dispatch_token=token,parent_thread_id=os.environ['CODEX_THREAD_ID'],character='ShardLizard',handoff_file=handoff.relative_to(ROOT).as_posix(),project_id=chain['project_id'],prompt=next_text)
write(D/'successor_dispatch_prepared.json',dispatch)
print(json.dumps({'status':'blocked','reason':reason,'completed':79,'next':'ShardLizard','handoff':str(handoff),'token':token,'unity_release':str(release_path),'production_changed':changes,'production_added':added,'chain_state':'handoff_ready'},ensure_ascii=False))
