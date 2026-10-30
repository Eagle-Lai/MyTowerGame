"""Persist an inherited service block and stop the serial chain without dispatching another task."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter
import hashlib, json, os

D = Path(__file__).resolve().parent
HERE = D.parent
ROOT = HERE.parents[2]
REL = HERE.relative_to(ROOT).as_posix()
TOKEN = 'scarabmounted-to-shardlizard-e066b2f9cbb54a5ca5b215b2e08ea8d2'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

chain = read(HERE/'conversation_chain.json')
assert chain['state'] == 'active' and chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID']
assert chain['current_character'] == D.name and chain['dispatch_token'] == TOKEN
assert not (D/'blocked_generation_20261026.json').exists(), 'Preserve prior stop evidence'
assert (D/'reference_review.json').exists()
assert not (D/'installed_manifest.json').exists() and not (D/'runtime_summary.json').exists()
for direction in ['Up','Down']:
    folder = D/'generation'/direction
    assert (folder/'prompt.txt').is_file()
    assert not any((folder/f).exists() for f in ['request.json','result.json','raw.png','uncertain_result.json'])

baseline = read(D/'incremental_before_20261026.json')
files = {p.relative_to(ROOT).as_posix():sha(p) for folder in ['Assets','Packages','ProjectSettings','Luban'] for p in (ROOT/folder).rglob('*') if p.is_file()}
changed = [{'path':p,'before':s,'after':files.get(p)} for p,s in baseline['files'].items() if files.get(p) != s]
added = sorted(set(files)-set(baseline['files']))
assert not changed and not added, 'Production drift: investigate before stopping'
assert all(files[p] == digest for p,digest in baseline['protected_shardlizard'].items())

response = read(D/'unity_release_request_response.json')
assert response['success'] and response['project']['projectRoot'] == 'E:/MyTowerGame'
assert response['project']['unityVersion'] == '2022.3.62f3c1'
state, errors, tool_result = response['results']
probe = tool_result['structuredContent']['data']['result']
assert probe['scene'] == 'Assets/Scenes/Boot.unity'
assert not any(v for k,v in probe.items() if k != 'scene')
assert state['data']['advice']['ready_for_tools']
assert not state['data']['compilation']['is_domain_reload_pending']
assert errors['structuredContent']['data'] == []
now = datetime.now(timezone(timedelta(hours=8)))
stamp = now.strftime('%Y%m%d_%H%M%S')
release = D/f'unity_release_blocked_{stamp}.json'
write(release,dict(observed_at=response['observed_at'],project=response['project'],state=state['data'],probe=probe,error_count=0,
                  production_operations_started=False,result='safe_idle_no_unity_changes',full_response='unity_release_request_response.json'))

upstream_path = HERE/'ScarabMounted/generation/Up/result.json'
upstream = read(upstream_path)
assert upstream['status'] == 402 and upstream['error']['code'] == 'insufficient_balance'
cutoff = datetime.fromisoformat(upstream['finished'].replace('Z','+00:00'))
recent = []
for path in HERE.glob('*/generation/**/result.json'):
    result = read(path)
    if result.get('finished') and datetime.fromisoformat(result['finished'].replace('Z','+00:00')) >= cutoff:
        recent.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),finished=result['finished'],status=result.get('status'),error=result.get('error')))
assert not any(r['status'] == 200 for r in recent), 'New success evidence exists; reassess service recovery'

reason = ('Inherited upstream image-service block, not a failed ShardLizard request. ScarabMounted Up returned HTTP 402 insufficient_balance: '
          'Upstream image account has insufficient balance. No restored balance/compatible-account evidence was found in the supplied handoff or subsequent local result records. '
          'ShardLizard Up and Down have never been requested; only reviewed references, anatomy and prompts were prepared. No paid probe or retry, stage, install, Verify, Play or record was performed. '
          'Resume only after restored service evidence; preserve all upstream requests, failures and PossessedWarg unknown outcome.')
progress = read(HERE/'progress.json')
before = json.loads(json.dumps(progress))
item = next(i for i in progress['items'] if i['name'] == D.name)
assert item['index'] == 94 and item['status'] == 'reference_prepared'
assert progress['completed_count'] == 79 and progress['authorized_count'] == 108
item.update(status='blocked',blocked_record=REL+'/ShardLizard/blocked_generation_20261026.json',blocked_at=now.isoformat(),
            blocked_reason=reason,visual_reviewed=False,user_approved=False)
remaining = [i for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved']]
candidates = [i for i in remaining if i['status'] != 'blocked']
assessment = []
for candidate in candidates:
    folder = HERE/candidate['name']
    entry = dict(index=candidate['index'],name=candidate['name'],status=candidate['status'],
                 generated_raw_count=len(list(folder.glob('generation/**/raw.png'))),
                 has_staged_art=(folder/'staged_art').exists(),has_install=(folder/'installed_manifest.json').exists(),
                 has_runtime=(folder/'runtime_summary.json').exists())
    assert entry['status'] == 'not_started' and entry['generated_raw_count'] == 0
    assert not any(entry[k] for k in ['has_staged_art','has_install','has_runtime'])
    entry['decision'] = 'Further production needs the same blocked image service; do not create another reference-only blocked successor'
    assessment.append(entry)
for old in before['items']:
    if old['name'] != D.name:
        assert old == next(i for i in progress['items'] if i['name'] == old['name'])
progress.update(status='blocked',current=D.name,updated_at=now.isoformat())
gif_count = read(HERE.parent/'AllGIF/manifest.json')['count']
assert gif_count == 1210

preserved = {}
for name in ['PossessedWarg','SabretoothTiger','Scarab','ScarabMounted']:
    for path in (HERE/name/'generation').rglob('*'):
        if path.is_file() and path.name in ['prompt.txt','request.json','result.json','uncertain_result.json','raw.png']:
            preserved[path.relative_to(ROOT).as_posix()] = sha(path)
block = dict(character=D.name,index=94,status='blocked',blocked_at=now.isoformat(),owner_thread_id=chain['owner_thread_id'],
             dispatch_token=TOKEN,stage='reference reviewed; generation withheld due to inherited upstream block',blocked_reason=reason,
             paid_requests_this_thread=0,request_results={direction:dict(status='not_requested',prompt=f'generation/{direction}/prompt.txt') for direction in ['Up','Down']},
             upstream_evidence=dict(source=upstream_path.relative_to(ROOT).as_posix(),result=upstream,sha256=sha(upstream_path),
                                    later_local_result_records=recent,restoration_evidence_found=False,
                                    assessment_method='Read existing handoffs and local result records; no network/model-list/billable probe. A model listing alone would not establish balance or compatible-account availability.'),
             reference_review=read(D/'reference_review.json'),
             evidence_hashes={p:sha(D/p) for p in ['anatomy_plan.json','reference_review.json','generation/Up/prompt.txt','generation/Down/prompt.txt']},
             production_snapshot=dict(path='incremental_before_20261026.json',file_count=len(files),changed=changed,added=added,
                                      protected_six_unchanged=baseline['protected_shardlizard'],legacy_scope_reference=baseline['legacy_scope_reference']),
             preserved_upstream_artifact_hashes=preserved,production_changes=False,
             unity=dict(project=response['project'],release_file=release.name,probe=probe,error_count=0,read_only_probes=True),
             runtime=dict(verify='not_executed',normal_round='not_executed',up_death_round='not_executed',media_review='not_executed',record='not_executed',new_gifs=0),
             progress=dict(completed_count=79,authorized_count=108,allgif_count=gif_count,status_counts=dict(Counter(i['status'] for i in progress['items']))),
             remaining_dependency_assessment=assessment,successor_created=False,
             recovery_conditions=['Evidence that upstream image balance and compatible-account availability are restored; do not test with another billable character request.',
                                  'Resume this existing ShardLizard owner chat; validate owner/token and explicitly reactivate the chain before Unity or production work.',
                                  'Reuse reviewed references/anatomy/prompts; both first requests remain unsent. Do not rerun preparation.',
                                  'Before stage/install, adapt top-root trailing-down Up tail pivot/layout as recorded, then actually inspect generated art, transparency, connections and footprint.',
                                  'Install Verify, two real 84-check Play rounds, real media review, UTF-8 note, record and GIF archive are all still required.'])
write(D/'blocked_generation_20261026.json',block)
handoff = HERE/'conversation_handoffs'/f'{stamp}_ShardLizard.md'
handoff.write_text(f'''# ShardLizard 参考完成与共同服务阻断

时间：{now.isoformat()}。项目 E:/MyTowerGame / Unity 2022.3.62f3c1。唯一线程 {chain['owner_thread_id']}；token {TOKEN}。开工四项所有权校验均通过。根 AGENTS 的 FreedomTower_1 / D: 旧信息未改，未切工程。

## 实际完成的参考阶段

实际查看原图集、完整源 prefab 离线图和新保存的完整战斗 prefab 离线图，读取序列化结构、原头部三态绑定、Rat Controller 状态及事件。低伏粗壮四足蜥蜴，橄榄褐底、黄褐斑、浅色下颌/腹缘、象牙白眼睛、金黄色额/颊晶片、背部一块宽阔平顶金色晶块、粗根长分节尾。没有耳朵、毛、鞍或骑手。通用 cream 晶片描述已在本角色解剖与两个提示词中按实际原图修正。

仅执行一次 prepare；已有原始参考及共享 contact 未覆盖，战斗离线图和 contact 写入本角色 reference。保存 anatomy_plan.json、reference_review.json、Up/Down prompt.txt。Up 尾根应在切片上端、尾巴向下拖曳，未来 stage 必须覆盖 pack_character 的默认底部 Tail pivot/朝上布局，不能直接安装通用布局。当前没有生成图审阅或用户美术批准。

## 真实阻断与请求状态

本角色 Up、Down **均未请求**，没有 request/result/raw/uncertain 文件；本聊天付费调用为 **0**。阻断继承自 ScarabMounted Up 的 HTTP402 insufficient_balance / Upstream image account has insufficient balance。读取 supplied handoff 和余额错误后的本地 result，未发现恢复证据；没有以 /models 或逐角色付费请求试探余额。先前进程查询没有发现 generate.mjs/generate_character.ps1 在运行。

Scarab 两个503、SabretoothTiger 的503/402、ScarabMounted 的402及 PossessedWarg Down 结果不明保持原样；现有请求/结果/原件 SHA256 清单写入 blocked_generation_20261026.json。不能把上游402写成本角色失败请求；两方向从未发送。未 stage/install/Verify/Play/record，未生成新 GIF。

## 范围与 Unity

独立增量基线为 incremental_before_20261026.json，共 {len(files)} 文件；收尾 changed=[]、added=[]、六保护指纹全部保持。开工目标 git diff 为空，用户已有 dirty 均保留。未修改任何 Assets/Packages/ProjectSettings/Luban 文件，未改 C#，故未请求编译刷新。全局291项历史 unexpected 未重置或改写；本轮没有 Reporter 自动 Play 时间戳副作用。

通过现有 mcp_call.py Client.identity 动态发现并明确选中 MyTowerGame 完整实例，核对 E:/MyTowerGame / 2022.3.62f3c1 / HTTP8082。只读现场时间 {response['observed_at']}：Boot，非Play、非dirty、非编译/更新/域重载，无 review/balance/recording/manual 占用，ready=true，scriptCompilationFailed=false，错误0。原请求/完整响应 unity_release_request{{,_response}}.json；安全状态 {release.name}。这是安全交还探针，不是 ShardLizard 运行验收。

## 队列与停止决定

实时进度79/108，AllGIF={gif_count}，本角色新增0；完成项仍是待用户美术审核。ShardLizard=index94 标记 blocked，visual_reviewed=false、user_approved=false。另4个既有 blocked 保留，后续24项 not_started 不被伪标为已尝试或失败。

重新读取 items 并检查所有未开始候选：均无生成 raw、暂存、安装或运行结果，没有可独立恢复的后续生产阶段；都依赖同一图像服务。依用户本次指令停止串行链，chain.state=blocked，不创建 Sheep 或其他同样受阻的新聊天，不使用 fork、子代理、并发、自动重试或自动定时器。

## 恢复入口

先取得余额/兼容账户恢复的可靠证据，保存到本角色目录；在当前唯一 owner 聊天恢复，不超时接管。重新读取 chain/token/实时 progress 和 NEXT_ENEMY_TASK，按明确继续指令重新激活 chain 后再操作 Unity/生产。复用本角色已审参考、解剖与两个未请求 prompt，不重跑 prepare、不覆盖原件。之后仍需真实生成/审图、透明和布局检查、安装前新增量及六指纹、单角色 Verify、两轮各84项真实Play、实际媒体审阅、UTF-8观察、record与GIF归档。此总结不是完成记录。
''',encoding='utf-8')

live = (f'2026-10-26 串行链停止于共同图像服务阻断：79/108，AllGIF={gif_count}。ShardLizard(index94) 已实际审阅原图集/完整源与战斗prefab，保存解剖和Up/Down提示词；两方向均未请求，本聊天付费调用0。'
        '继承ScarabMounted Up HTTP402 insufficient_balance，未发现余额/兼容账户恢复证据，没有付费试探或重发。未stage/install/Verify/Play/record，生成图/运行媒体均未审。'
        f'{len(files)}文件增量changed=[]、added=[]，六保护指纹不变；Unity只读核对8082目标身份，Boot非Play非dirty空闲、编译失败false、错误0。'
        '既有4个blocked保留，后续24项not_started均无可独立恢复的生成/暂存/安装/运行阶段；不再空转创建后继。chain.state=blocked、current=ShardLizard。'
        f'恢复条件与完整总结见 `ShardLizard/blocked_generation_20261026.json`、`conversation_handoffs/{handoff.name}` 和 NEXT_ENEMY_TASK.md；未将待用户美术审核写成批准。')
prompt_path = HERE/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md'
prompt = prompt_path.read_text(encoding='utf-8')
begin = '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->'
end = '<!-- ENEMY_SERIAL_LIVE_STATE_END -->'
assert prompt.count(begin) == 1 and prompt.count(end) == 1
prefix, rest = prompt.split(begin,1)
old, suffix = rest.split(end,1)
prompt_path.write_text(prefix+begin+'\n'+live+'\n'+end+suffix,encoding='utf-8')
readme_path = HERE.parent/'README.md'
readme_path.write_text(readme_path.read_text(encoding='utf-8').rstrip()+'\n\n'+live+'\n',encoding='utf-8')

next_task = f'''# 当前唯一敌人任务：ShardLizard（共同服务阻断，停止派发）

工作目录 E:/MyTowerGame；Unity 2022.3.62f3c1；HTTP Local unityMCP / 8082。根 AGENTS 的 FreedomTower_1 / D: 为旧信息，不能切工程或改 AGENTS。

当前 chain.state=blocked；唯一 owner_thread_id={chain['owner_thread_id']}、current_character=ShardLizard(index94)、dispatch_token={TOKEN}。当前聊天可在用户明确继续且已取得服务恢复证据后恢复；不得超时接管、重复创建 ShardLizard 聊天、fork、子代理或并发角色。未派发后继，不能把状态理解成后台仍在执行。

先读根 AGENTS、ProjectVersion、原执行 prompt、CONTINUATION_PROTOCOL、IMAGE_RELAY_RECOVERY、本文件、conversation_chain、实时 progress、上级 README、冻结 PREFAB_CHANGES_SUMMARY 及最新总结 `{REL}/conversation_handoffs/{handoff.name}`。核对本运行时 CODEX_THREAD_ID 与 owner/token；只有链重新 active 且四项匹配后才能操作 Unity/生产文件。

实时79/108，AllGIF={gif_count}。ShardLizard 已完成原图集、完整源和战斗 prefab 的实际参考审阅，anatomy_plan.json / reference_review.json / generation/Up/prompt.txt / generation/Down/prompt.txt 已保存。**两方向均未请求**，本聊天付费调用0，无 request/raw/result/uncertain，无暂存/安装/Verify/Play/record。禁止重跑 prepare、覆盖原件或把继承的402伪记为本角色请求失败。金色晶片按实际图集保留；Up尾根在切片上端、向下拖曳，stage前须改本角色 Tail pivot/布局并实际审阅。

共同阻断来源 ScarabMounted Up 首次 HTTP402 insufficient_balance：Upstream image account has insufficient balance，无raw；其Down未请求。Scarab两个503、SabretoothTiger的503/402及PossessedWarg Down结果不明完整保留，不重发旧请求。没有余额/兼容账户已恢复的可靠证据前，禁止用逐角色新请求或自动付费重试试探；模型列表不构成恢复证据。收到可靠恢复证据后保存该证据，在现有owner聊天按明确继续指令重新激活链并恢复本角色。

恢复后复用现有prompt，按原授权AIHub、imagegen技能、现有generate_character.ps1/generate.mjs、gpt-image-2/medium/1536x1024/n=1执行必要的首次请求；密钥运行时注入不落盘。请求结果不明绝不重发。实际审图、透明/边缘/布局、安装前新增量及六保护指纹、单角色安装Verify、普通死亡与Up死亡两轮各84项真实Unity Play、媒体时序审阅、UTF-8观察、record与GIF归档仍全部需要完成。程序PASS不能替代视觉判断，完成状态只能completed_pending_user_art_review。

Unity安全交还证据 `{REL}/ShardLizard/{release.name}` 与 unity_release_request_response.json：核对目标E:/MyTowerGame /2022.3.62f3c1，Boot非Play非dirty空闲、无编译/更新/域重载/录像/review/manual占用、scriptCompilationFailed=false、错误0；这不是角色运行验收。安装/Play前必须重新通过mcp_call.py Client.identity动态选实例并查占用；改C#必须完成AGENTS的刷新编译/日志闭环。

保留用户dirty；禁止pull/reset/clean/checkout/commit/push，不改配置表、ConfigJson、Gen或声音。现有{len(files)}文件本轮增量changed=[]、added=[]，六保护指纹不变；全局291项历史unexpected不重置，Reporter自动Play时间戳以后应单独归因。

后续24项not_started均无可独立恢复的生成/暂存/安装/运行阶段，已在blocked_generation_20261026.json记录检查；当前停止，不创建一串同样受阻聊天。条件恢复并完成本角色后，重新读取items，只有存在可独立推进的候选才按CONTINUATION_PROTOCOL创建唯一全新本地后继、登记真实threadId/hostId并做一次有界wait；成功移交后本聊天停止生产修改。
'''
(HERE/'NEXT_ENEMY_TASK.md').write_text(next_task,encoding='utf-8')
write(HERE/'progress.json',progress)
chain.update(state='blocked',character_status_at_handoff='blocked',stopped_at=now.isoformat(),blocked_reason=reason,
             stop_reason='shared_image_service_unrestored_no_independent_production_stage',successor_created=False,
             last_handoff_file=handoff.relative_to(ROOT).as_posix(),unity_release_file=release.relative_to(ROOT).as_posix(),
             completed_count_snapshot=79,progress_sha256_at_stop=sha(HERE/'progress.json'),
             resume_character=D.name,resume_stage='reference_prepared_generation_not_requested',
             recovery_file=(D/'blocked_generation_20261026.json').relative_to(ROOT).as_posix())
write(HERE/'conversation_chain.json',chain)
print(json.dumps(dict(character=D.name,status='blocked',chain_state='blocked',completed=79,authorized=108,
                      paid_requests=0,allgif=gif_count,production_changed=changed,production_added=added,
                      preserved_blocked_other=4,not_started=len(assessment),successor_created=False,
                      handoff=handoff.relative_to(ROOT).as_posix(),release=release.relative_to(ROOT).as_posix()),ensure_ascii=False))
