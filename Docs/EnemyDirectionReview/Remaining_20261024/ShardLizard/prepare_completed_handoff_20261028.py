"""Persist completed ShardLizard evidence and prepare exactly one serial successor.

No generation, Play run, production resource write, or record replay is performed.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import subprocess
import sys
import uuid

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
sys.path.insert(0, str(H))
from mcp_call import Client


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rel(path):
    return path.relative_to(ROOT).as_posix()


def unwrap(value):
    return value.get('structuredContent') or json.loads(value['content'][0]['text'])


now = datetime.now(timezone(timedelta(hours=8)))
stamp = now.strftime('%Y%m%d_%H%M%S')
chain = read(H / 'conversation_chain.json')
assert chain['state'] == 'active'
assert chain['owner_thread_id'] == os.environ['CODEX_THREAD_ID'] == '01a178a8-fc5a-77b0-9881-0a0b40872da8'
assert chain['current_character'] == 'ShardLizard'
assert chain['dispatch_token'] == 'scarabmounted-to-shardlizard-e066b2f9cbb54a5ca5b215b2e08ea8d2'
assert not (D / 'successor_create_request.json').exists(), 'Inspect prior dispatch; never create twice'
progress = read(H / 'progress.json')
assert progress['completed_count'] == 80 and progress['authorized_count'] == 108
item = next(x for x in progress['items'] if x['name'] == 'ShardLizard')
assert item['status'] == 'completed_pending_user_art_review' and item['user_approved'] is False
assert not item['recovery_in_progress'] and not item['current_blocked']
unfinished = [x for x in progress['items'] if x['status'] not in ['completed_pending_user_art_review', 'user_approved']]
assert len(unfinished) == 28
assert [(x['index'], x['name']) for x in unfinished if x['status'] == 'blocked'] == [
    (79, 'PossessedWarg'), (91, 'SabretoothTiger'), (92, 'Scarab'), (93, 'ScarabMounted')]
assert sum(x['status'] == 'not_started' for x in unfinished) == 24
assert not any(x.get('recovery_in_progress') for x in progress['items'])

runtime = read(D / 'runtime_summary.json')
assert (runtime['passes'], runtime['failures'], runtime['actual_frames']) == (168, 0, 679)
assert [x['revision'] for x in runtime['runtime']] == ['runtime_final_r02', 'runtime_final_updeath_r02']
scope = read(D / 'scope_incremental_recovery_20261028.json')
assert not scope['unexpected_incremental'] and not scope['protected_drift']
assert scope['prefab_semantics']['pass'] and not scope['installed_asset_drift']
assert not scope['staged_production_drift'] and scope['legacy_unexpected_count'] == 291
assert scope['legacy_pass'] is False and not scope['new_unexpected_vs_preexisting_legacy']
manifest_path = D / 'repair_proportions_r03/manifest.json'
manifest = read(manifest_path)
assert all(sha(ROOT / x['path']) == x['after'].upper() for x in manifest['changes'])
prefab_sha = sha(ROOT / 'Assets/Prefabs/Enemy/Enemy_ShardLizard.prefab')
assert prefab_sha == '785BB807EA2F91233F940A0A60DE3B9FC31F15D268EC7CFCD61BE0CB45136742'
review = read(D / 'visual_review_final_20261028/review.json')
assert len(review['viewed_sheets']) == 10
assert (review['sample_slots'], review['distinct_actual_frame_samples']) == (256, 230)
archive = read(H.parent / 'AllGIF/manifest.json')
own_gifs = [x for x in archive['files'] if x['source'].startswith('Remaining_20261024/ShardLizard/')]
assert archive['count'] == 1234 and len(own_gifs) == 24
assert sum(x['status'] == '当前审核版本' for x in own_gifs) == 12

process = subprocess.run([
    'powershell', '-NoProfile', '-Command',
    "@(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'node.exe' -and $_.CommandLine -like '*generate.mjs*' } | Select-Object -ExpandProperty ProcessId) | ConvertTo-Json -Compress"
], capture_output=True, text=True, check=True)
assert not process.stdout.strip(), 'An image generator is still running'
successes = []
for direction, revision in [('Up', 'revision_02'), ('Down', '')]:
    folder = D / 'generation' / direction / revision
    request, result = read(folder / 'request.json'), read(folder / 'result.json')
    assert result['status'] == 200 and result['bytes'] > 0 and (folder / 'raw.png').is_file()
    assert request['endpoint'] == 'https://aihub.dog/v1/images/edits'
    assert (request['model'], request['quality'], request['size'], request['n']) == ('gpt-image-2', 'medium', '1536x1024', 1)
    successes.append(dict(direction=direction, request=rel(folder / 'request.json'), result=rel(folder / 'result.json'),
                          request_sha256=sha(folder / 'request.json'), result_sha256=sha(folder / 'result.json'),
                          raw=rel(folder / 'raw.png'), raw_sha256=sha(folder / 'raw.png'),
                          finished=result['finished'], http_status=200,
                          endpoint=request['endpoint'], model=request['model'], quality=request['quality'], size=request['size'], n=request['n']))
candidates = []
for name in ['SabretoothTiger', 'Scarab', 'ScarabMounted']:
    folder = H / name
    blocked = read(folder / 'blocked_generation_20261026.json')
    protected = blocked['production_snapshot']['protected_six_unchanged']
    drift = [p for p, value in protected.items() if sha(ROOT / p) != value.upper()]
    assert not drift
    assert not (folder / 'installed_manifest.json').exists()
    assert not list((folder / 'generation').rglob('raw.png'))
    outcomes = []
    for direction in ['Up', 'Down']:
        request_path, result_path = folder / 'generation' / direction / 'request.json', folder / 'generation' / direction / 'result.json'
        if request_path.exists():
            assert result_path.exists()
            request, result = read(request_path), read(result_path)
            assert 400 <= result['status'] <= 599 and result.get('error') and not result.get('bytes')
            assert request['endpoint'] == successes[0]['endpoint'] and request['model'] == successes[0]['model']
            assert (request['quality'], request['size'], request['n']) == ('medium', '1536x1024', 1)
            outcomes.append(dict(direction=direction, request=rel(request_path), result=rel(result_path),
                                 request_sha256=sha(request_path), result_sha256=sha(result_path),
                                 http_status=result['status'], error=result['error'], request_state='explicit_http_failure'))
        else:
            assert name == 'ScarabMounted' and direction == 'Down'
            outcomes.append(dict(direction=direction, request_state='never_requested'))
    assert not list((folder / 'generation').rglob('uncertain_result.json'))
    candidates.append(dict(name=name, index=blocked['index'], status='blocked', protected_six=protected,
                           protected_drift=drift, existing_results=outcomes, recovery_eligible=True,
                           existing_stage='reference/anatomy/prompts only; no generated image or installation'))
warg = H / 'PossessedWarg/generation/Down'
assert (warg / 'request.json').exists() and not (warg / 'result.json').exists() and not (warg / 'raw.png').exists()
assessment_path = D / ('successor_recovery_assessment_' + stamp + '.json')
write_new(assessment_path, dict(observed_at=now.isoformat(), source='current disk, request/result files and process inventory',
    unfinished=[dict(index=x['index'], name=x['name'], status=x['status']) for x in unfinished],
    active_generate_process_ids=[], same_service_success_evidence=successes,
    candidates=candidates, selected='SabretoothTiger', selected_index=91,
    reason='Restore the lowest-index previously started character with explicit HTTP failures and unchanged protected files. Later real production successes establish a recovery opportunity; they do not guarantee future service availability.',
    possesed_warg=dict(index=79, status='blocked', request=rel(warg / 'request.json'), result_known=False,
                      reason='Prior Down result remains unknown, no output/result/query identifier; never resend on this evidence.'),
    recovery_policy='Next owner rechecks evidence, fingerprints and process state, uses a new unused revision and one-request recovery_intent per direction. Up first. Explicit service failure or uncertain outcome stops further requests; preserve all historical attempts. No request was made by this assessment.'))

# Fresh read-only release. Discover and pin the current full instance ID on 8082.
client = Client()
project = client.identity()
errors = unwrap(client.tool('read_console', dict(action='get', types=['error'], count='50', format='json')))
state = client.resource('mcpforunity://editor/state')
code = 'return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};'
probe = unwrap(client.tool('execute_code', dict(action='execute', code=code)))
assert probe['success']
observed = probe['data']['result']
assert observed['scene'] == 'Assets/Scenes/Boot.unity'
assert not any(v for k, v in observed.items() if k != 'scene'), observed
s = state['data']
assert not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending']
assert not s['assets']['is_updating'] and s['advice']['ready_for_tools']
assert errors['success'] and errors['data'] == [], errors
release_path = D / ('unity_release_completed_' + stamp + '.json')
write_new(release_path, dict(observed_at=datetime.now(timezone(timedelta(hours=8))).isoformat(), project=project,
    state=state, errors=errors, probe=probe, error_count=0, safe_to_handoff=True,
    operations='Read-only identity, console, editor state and occupancy probes; no refresh or Play rerun.',
    protocol_history=client.history))

token = 'shardlizard-to-sabretoothtiger-' + uuid.uuid4().hex
handoff_path = H / 'conversation_handoffs' / (stamp + '_ShardLizard_completed.md')
live = f'''2026-10-28 串行续接：80/108。ShardLizard(index94)最终local_raster_revision_02、repair_proportions_r03/manifest.json；runtime_final_r02与runtime_final_updeath_r02各84 PASS/0 FAIL，340+339=679张真实帧。初版Up/Down过小已视觉否决，比例revision03放大1.6并保留尾根pivot；全部旧证据保留。实际查看10张时序/步态/愤怒细节板，256采样位/230张不同真实帧，另看四方向、strip、完整离线rig及攻击/死亡原PNG；未实时播放GIF、未逐张审完679帧。已record并归档，completed_pending_user_art_review、user_approved=false。5138文件安装前增量基线，并集22项变化含20项新增，本角色语义/安装/暂存绑定无drift，unexpected_incremental=[]；Reporter未改InitializeOnLoad时间戳单独归因。全局291项历史unexpected及6个其他角色语义失败保留，新增0，不能称全局PASS。AllGIF=1234，ShardLizard24项含12个最终审核版本。Unity只读重核E:/MyTowerGame /2022.3.62f3c1，Boot、非Play、全部场景非dirty、空闲、编译失败false、错误0。下一唯一角色SabretoothTiger(index91)：旧Up503/Down402均明确失败无raw，六保护指纹无drift；ShardLizard同服务最新两次HTTP200可支持一次有界恢复，不保证后续服务持续可用。PossessedWarg结果不明仍阻断，不重发。详见conversation_handoffs/{handoff_path.name}、{assessment_path.name}和NEXT_ENEMY_TASK.md；所有权以chain实时记录为准。'''
handoff = f'''# ShardLizard 完成与串行交接

时间：{now.isoformat()}。目标 E:/MyTowerGame / Unity 2022.3.62f3c1。本聊天 owner={chain['owner_thread_id']}，原token={chain['dispatch_token']}。无子代理、fork或并发角色。

## 记录完成的最终成果

- 续作80/108。ShardLizard(index94)已record为completed_pending_user_art_review，user_approved=false，recovery_in_progress=false、current_blocked=false；历史blocked文件保留。
- 最终安装`ShardLizard/repair_proportions_r03/manifest.json`，生产prefab SHA256 `{prefab_sha}`。初次`installed_manifest.json`仍保留，不删除、不重新初次安装。
- 最终图像派生local_raster_revision_02。Up原件generation/Up/revision_02/raw.png、Down原件generation/Down/raw.png；两次HTTP200分别完成于2026-10-28T00:59:03.813Z及01:01:53.103Z。本阶段未再付费请求。
- 初版runtime_r01/runtime_updeath_r01虽168/0、678帧，但Up/Down体量过小已被视觉否决。离线revision03将轴向部件及关节间距放大1.6并保留专用尾根pivot，再修复安装并全新运行。旧图、失败/阻断、安装和运行证据均保留。

| 最终真实Play | PASS | FAIL | 帧数 | actual_frames.jsonl SHA256 |
|---|---:|---:|---:|---|
| runtime_final_r02 | 84 | 0 | 340 | A8E2D198FB7DF11389509AB2B6D4DE7979DF1DA160564F7F1343D0F410116878 |
| runtime_final_updeath_r02 | 84 | 0 | 339 | 1251CCE4A05ED9145095AB4A12D0F2F4CDE3D8DEA60A643BDADF76D956CA2910 |

两轮合计168 PASS/0 FAIL，679帧。版本绑定`ShardLizard/version_binding_final_20261028.json`，本次运行与record证据`runtime_summary.json`、`record_note_utf8.txt`、`final_validation_20261028.json`。不要重跑finalize_recovery_20261028.py，它已经成功执行。

## 实际视觉审阅及限制

已实际查看`ShardLizard/visual_review_final_20261028/`全部10张板：6张sequence、2张walk_cycle、2张angry_detail，共256采样位、230张不同真实帧。另看最终four_directions.png、runtime_visual_strip.png、offline_proportions_revision_03/full_rig_proof.png，以及runtime_final_r02中的Attack_00139.png和DeathAutoRecycle_00165.png。来源和哈希见review.json/sources.json。

Up无脸、四肢与颈尾连接连续、单尾；Down宽脸、小额晶片、单块宽顶背晶，攻击与死亡表情可辨。抽样步态、转向、白闪、死亡倾倒淡出、回收复用、暂停恢复、2x/3x推进正常，尾尖未碰血条，无地面阴影。未实时播放GIF，未逐张审完679帧；不能扩大审阅范围或替用户批准美术。

AllGIF manifest现有1234项；本角色24项，12项为最终审核版本、12项为历史。浏览入口`Docs/EnemyDirectionReview/AllGIF/index.html`，原件与历史均保留。

## 范围、语义与Unity释放

- 安装前基线`ShardLizard/incremental_before_recovery_20261028_085812.json`含5138文件。哈希大小写归一并比较文件并集，共22项变化，含20新增。允许本角色战斗prefab、Directions及目录meta、Reporter时间戳；unexpected_incremental=[]。原图、源prefab及meta、战斗prefab.meta无drift。
- prefab语义PASS，最终安装清单和暂存打包资源与生产一致。原侧向曲线、事件、duration/loop、root/HP/collider/业务参数、依赖及YooAsset覆盖已通过Builder Verify。证据`scope_incremental_recovery_20261028.json`和`scope_ShardLizard_20261028_final.json`。
- 全局291项既有unexpected和6个其他角色既有语义失败保留，本轮新增0；没有全局PASS，不重置任何历史基线。
- Reporter副作用来自未修改的`ReporterEditor.cs`的`[InitializeOnLoad] BuildInfo.Update`，启动或编译也会写，不能限定为仅Play触发。
- 新只读释放证据`{rel(release_path)}`：动态选择8082当前完整MyTowerGame实例并核对路径/版本，Boot、非Play、全部场景非dirty、无compile/update/domain reload，无review/balance/recording/manual占用、ready=true、scriptCompilationFailed=false、error=0。
- 本轮无新增生产C#修改、APK构建或设备测试。大量既有dirty保留，无pull/reset/clean/checkout/commit/push；不改配置表、ConfigJson/Gen、声音或其他角色。

## 下一唯一角色及恢复判断

实时28项未完成：4个blocked、24个not_started。记录脚本将progress.current指回PossessedWarg属既有行为；不能盲用current调度。选择可恢复的已开始角色SabretoothTiger(index91)，早于Scarab/ScarabMounted。

当前恢复评估`{rel(assessment_path)}`记录三角色六保护指纹均无drift、无生成进程，SabretoothTiger旧Up503/Down402均明确失败且没有raw，无stage/install；Scarab旧双503，ScarabMounted旧Up402且Down从未请求。ShardLizard相同endpoint/model/quality/size/n的后续真实HTTP200提供恢复机会，不保证服务未来持续可用；下一owner按新唯一revision、每方向max_requests=1的recovery_intent和generate.mjs防重入口继续。先Up，失败/不明则保留并停止后续请求，不逐角色付费试探共同故障。

PossessedWarg(index79)旧Down请求仍无raw/result/可查询ID，保持blocked，不重发。Scarab/ScarabMounted本聊天不恢复、不请求。SabretoothTiger仍须原始参考及解剖实际审阅、两方向生成和审图、透明切片/布局、安装Verify、两轮真实Play、媒体审阅、record和归档，不能把本评估写成已完成或已出图。

新token `{token}`。接棒说明见NEXT_ENEMY_TASK.md。先handoff_ready再创建恰好一个全新local聊天，登记真实threadId/hostId后转active。创建成功后旧聊天停止所有工程/链修改，仅一次有界wait；不fork、不设模型、不并行。
'''
with handoff_path.open('x', encoding='utf-8') as stream:
    stream.write(handoff)

next_text = f'''# 当前唯一敌人任务：SabretoothTiger（明确失败后的有界恢复）

在E:/MyTowerGame继续敌人四方向串行续作。只处理SabretoothTiger(index91)。parent_thread_id={chain['owner_thread_id']}，接棒dispatch_token={token}。上一角色ShardLizard完成总结：`{rel(handoff_path)}`；恢复评估：`{rel(assessment_path)}`；新Unity释放：`{rel(release_path)}`。

## 先同步与所有权

先读根及目标目录链AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md和PREFAB_CHANGES_SUMMARY_20261026.md；再读Remaining_20261024下REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、本文件、conversation_chain.json、实时progress.json及上述交接/评估。检查现有git dirty与目标差异，保留用户改动。根AGENTS中FreedomTower_1/D:是旧路径；本任务明确目标E:/MyTowerGame /Unity2022.3.62f3c1，不切工程、不改AGENTS。

只有chain.state=active、owner_thread_id等于本聊天运行时CODEX_THREAD_ID、current_character=SabretoothTiger，且dispatch_token完全等于`{token}`后，才能操作Unity或生产文件。handoff_ready时只读等待父聊天登记；所有权不超时失效，不抢锁。禁止fork、子代理、并行角色、重复创建聊天。当前为80/108；progress.current可能仍是PossessedWarg，不按它盲调度。

## 当前实际阶段和恢复入口

SabretoothTiger旧状态blocked，已准备reference/anatomy_plan.json及Up/Down提示词，prompt_review.json记有实际源参考观察。读取SabretoothTiger/blocked_generation_20261026.json、anatomy_plan.json、prompt_review.json、reference/全部有关材料与两方向prompt/request/result。重新实际查看原图集、完整源prefab离线参考及序列化结构，不能把上个聊天的审图当本聊天已看。角色是灰白剑齿虎，深棕宽纹和赭色斑点、长象牙犬齿、颊毛、四爪足、条纹尾；Up后脑不画脸或獠牙，Down保留正常/攻击/死亡表情，尾根按方向接在正确端。不凭名称添加鬃毛或装备。

旧Up为明确HTTP503 No available compatible accounts；旧Down为明确HTTP402 insufficient_balance，均无raw，没有stage/install/Play。六保护文件当前无drift，但开工重核并建立本轮生产增量基线；不能用旧5138基线承接其他角色新增文件。保留所有旧请求/结果/blocked，不重复prepare、不覆盖旧文件，不把blocked历史抹除。

恢复依据：ShardLizard在同一https://aihub.dog/v1/images/edits、gpt-image-2、medium、1536x1024、n=1上，两次真实生产结果于2026-10-28T00:59:03.813Z与01:01:53.103Z为HTTP200，已落raw。这支持恢复index最早的明确失败角色，但不保证后续余额/上游持续可用。评估时无运行的node generate.mjs。开工检查是否已有新结果、uncertain_result或进行中的请求，再决定动作；结果不明不能重发，不能用付费探针测试服务。

先读取generate_character.ps1及generate.mjs实际实现。两方向均已有明确失败且无raw，应使用各自全新未使用revision（检查后可从revision_01开始），复制或针对真实参考修订完整prompt.txt，并编写recovery_intent.json：character、direction、revision、owner_thread_id、本token、max_requests=1、非空reason，以及原父request/result的**小写**SHA256；附既有请求证据、新基线和恢复依据。--recover-failed会验证active所有权、token、父哈希及所有既有尝试，并用原图集和完整源参考；不要调用要求旧raw存在的普通revision入口。先用-Preflight只读预检，随后只发一次Up正式请求：

    & 'Docs/EnemyDirectionReview/Remaining_20261024/generate_character.ps1' -Character SabretoothTiger -Direction Up -Revision revision_01 -RecoverFailed -Preflight
    & 'Docs/EnemyDirectionReview/Remaining_20261024/generate_character.ps1' -Character SabretoothTiger -Direction Up -Revision revision_01 -RecoverFailed

上述revision_01须先确认未被使用；若已存在请求，恢复检查该结果而非再发。Up成功落盘后实际审图，按需要定点返修；Down同样用独立新revision/intent并按阶段执行，不把两方向无条件连跑。若明确402/503/鉴权/配额等共同服务失败或结果不明，立即保存准确阻断并停止进一步付费尝试；不另开revision自动重试或通过其他角色试探。密钥按AGENTS仅运行时注入，不输出、不写盘。

## 完整单角色验收

按原执行prompt读取character_step.py、prepare/pack/install/repair/record、runtime_runner及revision入口、collect_gifs、local_baseline与生产指纹，并有针对性读取原动画/业务调用与共享Builder。生成图实际审阅通过后，透明/边缘/切片/Pivot/PPU/连接/遮挡/正背比例检查，保存离线四方向全身图与观察；不使用缩略图掩盖断肢。确认本角色未安装且指纹无drift后才沿用单角色stage/install流程。已有安装清单时从对应修复阶段恢复，绝不删除清单绕过保护。

普通死亡和Up死亡两轮各84项真实Unity Play，真实PNG/GIF媒体按时序实际审阅，必要返修用新revision重跑；最终168 PASS/0 FAIL与视觉通过、版本绑定、增量审计同时满足才record。保持原侧图曲线/事件/duration/loop、root/GUID/HP/血条/collider/业务参数、闪白/死亡淡出/同实例对象池/暂停倍速；无地面阴影。仅改本角色战斗prefab及Directions。记录实际看过的帧/板数量，不把技术PASS等同美术批准；完成仅标completed_pending_user_art_review、user_approved=false。

Unity优先使用现有Remaining_20261024/mcp_call.py的Client，HTTP Local8082，identity()动态读custom-tools/instances、选当前完整MyTowerGame实例并核对project/info及版本。原生connector此前路由8084/FishTestGame，不盲用、不杀共享8084服务、不打印Logs/shardlizard_mcp8082_launch_private.json内容。不用CatchFish8080。安装/Play前重新确认无其他任务占用。若修改生产C#，按AGENTS完成该工程MCP刷新、编译/域重载结束、scriptCompilationFailed=false和错误日志闭环；无关代码不动。

全局历史291项unexpected与6个其他角色语义失败保留，新增必须独立归因，不能宣称全局PASS或重置基线。文件并集含新增/删除，哈希大小写归一。ReporterEditor未修改的InitializeOnLoad BuildInfo.Update在启动/编译也会写build_info，允许副作用须有内容与源指纹证据，不笼统扩允许范围。

## 上一角色保护与串行后续

ShardLizard已完成，最终repair_proportions_r03，168/0、679帧，实审10板/256位/230不同帧及必要原图；record和GIF已归档。保留installed_manifest及全部历史，不重跑finalize_recovery_20261028.py，不重生成/重安装/重测。AllGIF=1234，其中ShardLizard24项，最终12/历史12。

PossessedWarg旧Down结果仍不明，保持blocked且不重发。Scarab双503和ScarabMounted Up402/Down未请求保留，后继再按实时证据判断；本聊天不并行恢复它们。其他24项not_started。禁止pull/reset/clean/checkout/commit/push；不改配置表、ConfigJson/Gen、声音或其他角色。

完成本角色，或保存真实阻断并安全交回Unity后，按CONTINUATION_PROTOCOL：重读实时items，优先可恢复的已开始角色；写新时间戳总结，更新README、原prompt实时块、NEXT_ENEMY_TASK和chain；确认非Play/全部场景非dirty/无编译录像review占用，再生成新token转handoff_ready。只有仍有可独立推进的工作才调用list_projects并创建恰好一个全新local聊天，不fork、不设模型。登记真实threadId/hostId/token后转active，旧聊天停止修改，仅一次有界wait。只剩真实共同阻断则停止并准确报告，不空转创建聊天。用户已直接授权此串行循环，无需逐角色确认。
'''
(H / 'NEXT_ENEMY_TASK.md').write_text(next_text, encoding='utf-8')
prompt_path = H / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md'
prompt = prompt_path.read_text(encoding='utf-8')
begin, end = '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->', '<!-- ENEMY_SERIAL_LIVE_STATE_END -->'
assert prompt.count(begin) == prompt.count(end) == 1
prompt_path.write_text(prompt.split(begin)[0] + begin + '\n' + live + '\n' + end + prompt.split(end)[1], encoding='utf-8')
readme_path = H.parent / 'README.md'
readme = readme_path.read_text(encoding='utf-8')
readme = readme.replace('2026-10-26 本轮当前清单为 1210 个文件', '2026-10-28 本轮当前清单为 1234 个文件', 1)
readme_path.write_text(readme + '\n' + live + '\n', encoding='utf-8')

request = dict(target=dict(type='project', projectId='935c594c-f414-48e0-bd08-ed8ba342f7fd', environment=dict(type='local')),
               prompt=next_text, title='SabretoothTiger 四方向恢复与串行续作')
write_new(D / 'successor_create_request.json', request)
assert handoff_path.read_text(encoding='utf-8') == handoff
assert (H / 'NEXT_ENEMY_TASK.md').read_text(encoding='utf-8') == request['prompt']
assert token in request['prompt'] and rel(handoff_path) in request['prompt']
chain.setdefault('stage_history', []).append(dict(character='ShardLizard', status=item['status'],
    current_stage=chain.get('current_stage'), resume_stage=chain.get('resume_stage'),
    owner_thread_id=chain['owner_thread_id'], dispatch_token=chain['dispatch_token'], closed_at=now.isoformat(),
    handoff_file=rel(handoff_path), final_evidence=rel(D / 'final_validation_20261028.json')))
chain.update(state='handoff_ready', parent_thread_id=os.environ['CODEX_THREAD_ID'],
    current_character='SabretoothTiger', dispatch_token=token, character_status_at_handoff='blocked',
    current_stage='reference_prepared_explicit_http_failure_recovery_ready',
    resume_character='SabretoothTiger', resume_stage='Recover prior explicit Up503/Down402 using unused revisions; no output or installation exists',
    completed_count_snapshot=80, previous_handoff_file=chain['last_handoff_file'], last_handoff_file=rel(handoff_path),
    progress_sha256_at_handoff=sha(H / 'progress.json'), handoff_ready_at=now.isoformat(),
    unity_release_file=rel(release_path), dispatch_ready_for='SabretoothTiger', successor_created=False,
    last_stage_evidence=rel(assessment_path), recovery_file=rel(assessment_path), updated_at=now.isoformat())
write(H / 'conversation_chain.json', chain)
print(json.dumps(dict(state=chain['state'], completed=80, next='SabretoothTiger', token=token,
    handoff=rel(handoff_path), release=rel(release_path), recovery_assessment=rel(assessment_path),
    request=rel(D / 'successor_create_request.json'), prefab_sha256=prefab_sha, allgif=1234,
    unity=observed, production_writes=False), ensure_ascii=False))
