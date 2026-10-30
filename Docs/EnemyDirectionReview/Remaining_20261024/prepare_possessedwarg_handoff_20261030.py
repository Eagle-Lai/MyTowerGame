"""Prepare one documented continuation. Writes Docs only; never calls Unity or Image API."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import re
import shutil
import subprocess
import uuid

ROOT = Path('E:/MyTowerGame')
RUN = ROOT / 'Docs/EnemyDirectionReview/Remaining_20261024'
PARENT = '01a18832-7895-7a23-ba81-c2c410a5a454'
OLD_TOKEN = 'wolfmounfed-to-zombie-20261029_230534-9abf79b2-282d-4c43-bc85-2b10f14a62f1'
PROJECT = '935c594c-f414-48e0-bd08-ed8ba342f7fd'
TZ = timezone(timedelta(hours=8))


def now():
    return datetime.now(TZ).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def rel(path):
    return Path(path).relative_to(ROOT).as_posix()


def text_new(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(content)


def save_new(path, value):
    text_new(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def replace_text(path, content):
    path = Path(path)
    temporary = path.with_name(path.name + '.possessedwarg_handoff_tmp')
    text_new(temporary, content)
    temporary.replace(path)


def replace_json(path, value):
    replace_text(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


assert os.environ.get('CODEX_THREAD_ID') == PARENT, 'Wrong parent chat'
version = (ROOT / 'ProjectSettings/ProjectVersion.txt').read_text().splitlines()[0].split(':', 1)[1].strip()
assert version == '2022.3.62f3c1', version
chain_path = RUN / 'conversation_chain.json'
progress_path = RUN / 'progress.json'
chain_sha = sha(chain_path)
progress_sha = sha(progress_path)
chain = read(chain_path)
progress = read(progress_path)
assert chain['state'] == 'blocked' and chain['owner_thread_id'] == PARENT
assert chain['dispatch_token'] == OLD_TOKEN and chain['current_character'] == 'PossessedWarg'
assert chain['max_active_production_tasks'] == 1 and len(chain['dispatch_history']) == 37
remaining = [item for item in progress['items'] if item['status'] not in ('completed_pending_user_art_review', 'user_approved')]
assert len(remaining) == 1 and remaining[0]['name'] == 'PossessedWarg' and remaining[0]['index'] == 79
assert progress['completed_count'] == 107 and progress['authorized_count'] == 108
target = next(item for item in read(RUN / 'local_baseline.json')['targets'] if item['name'] == 'PossessedWarg')
character_dir = RUN / 'PossessedWarg'
old_files = {path.relative_to(character_dir).as_posix(): sha(path) for path in character_dir.rglob('*') if path.is_file()}
old_assessment = read(RUN / 'Zombie/successor_assessment_final_20261029.json')['remaining'][0]
assert len(old_files) == 21 and old_files == old_assessment['files'], 'Original character evidence changed'
assert sorted(path.name for path in (character_dir / 'generation/Down').iterdir()) == ['prompt.txt', 'request.json']
assert not (character_dir / 'installed_manifest.json').exists()
assert not (ROOT / target['art_dir']).exists(), 'Existing production Directions need reconciliation'
original_down = read(character_dir / 'generation/Down/request.json')
assert original_down['started'] == '2026-10-26T00:54:57.839Z'
assert old_files['generation/Down/request.json'] == 'B2B3C9FB4B78E2FFB5E606FCE95BB2843575982CADBE6C6E97D352346D27BA4A'
assert old_files['generation/Up/raw.png'] == '8B015639A80D16F54901C294CECF061A08479E5E7029206FB6C05057DB106868'
blocked = read(character_dir / 'blocked_20261026_125634_639300.json')
protected = {path: sha(ROOT / path) for path in blocked['source_fingerprints']}
assert len(protected) == 6 and all(value == blocked['source_fingerprints'][path]['sha256'] for path, value in protected.items())
process_script = r"Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(node|python|curl|powershell|pwsh)(\.exe)?$' -and $_.CommandLine -match 'generate_character\.ps1|generate\.mjs|aihub\.dog/v1/images' } | Select-Object ProcessId,Name | ConvertTo-Json -Compress"
process_result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', process_script], capture_output=True, text=True, check=True)
processes = json.loads(process_result.stdout) if process_result.stdout.strip() else []
assert not processes, 'Generation process is still running; no dispatch'
production = {path.relative_to(ROOT).as_posix(): sha(path) for folder in ('Assets', 'Packages', 'ProjectSettings', 'Luban') for path in (ROOT / folder).rglob('*') if path.is_file()}
prior_production = read(RUN / 'Zombie/final_version_binding_20261029.json')['all_production_fingerprints']
drift = [{'path': path, 'before': prior_production.get(path), 'after': production.get(path)} for path in sorted(set(prior_production) | set(production)) if prior_production.get(path) != production.get(path)]
assert len(production) == 5705 and len(drift) == 1 and drift[0]['path'] == 'Assets/StreamingAssets/build_info', 'Unreconciled production drift since Zombie closeout'
reporter_path = 'Assets/Reporter/Editor/ReporterEditor.cs'
assert production[reporter_path] == prior_production[reporter_path], 'Reporter source changed'
build_info_text = (ROOT / 'Assets/StreamingAssets/build_info').read_text(encoding='utf-8')
stamp_match = re.fullmatch(r'Build from ' + re.escape(os.environ['COMPUTERNAME']) + r' at (\d{4}/\d{1,2}/\d{1,2} \d{1,2}:\d{2}:\d{2})', build_info_text)
assert stamp_match, 'Unexpected build_info contents'
metadata_stamp = datetime.strptime(stamp_match.group(1), '%Y/%m/%d %H:%M:%S').replace(tzinfo=TZ)
assert datetime(2026, 10, 30, tzinfo=TZ) <= metadata_stamp <= datetime.now(TZ), 'Unexpected build_info timestamp'
manifest = read(ROOT / 'Docs/EnemyDirectionReview/AllGIF/manifest.json')
assert manifest['count'] == len(manifest['files']) == 1744

stamp = datetime.now(TZ).strftime('%Y%m%d_%H%M%S')
timestamp = now()
resume = RUN / ('resume_' + stamp + '_PossessedWarg')
resume.mkdir(exist_ok=False)
token = 'zombie-to-possessedwarg-' + stamp + '-' + str(uuid.uuid4())
backup_files = [chain_path, progress_path, RUN / 'NEXT_ENEMY_TASK.md', ROOT / 'Docs/EnemyDirectionReview/README.md', RUN / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md', RUN / 'generate.mjs', RUN / 'generate_character.ps1', ROOT / 'Assets/StreamingAssets/build_info', ROOT / reporter_path]
backups = []
for source in backup_files:
    destination = resume / 'before' / source.relative_to(ROOT)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    backups.append({'source': rel(source), 'backup': rel(destination), 'sha256': sha(source)})
status = subprocess.run(['git', '-c', 'core.quotepath=false', 'status', '--porcelain=v1'], cwd=ROOT, capture_output=True, encoding='utf-8', check=True)
text_new(resume / 'git_status_before.txt', status.stdout)
save_new(resume / 'production_paths_before.json', production)
save_new(resume / 'original_character_files.json', old_files)
save_new(resume / 'backup_manifest.json', backups)
save_new(resume / 'preexisting_production_drift.json', {'observed_at': timestamp, 'changes_since_Zombie_closeout': drift, 'current_build_info': build_info_text, 'metadata_timestamp': metadata_stamp.isoformat(), 'reporter_source_sha256': production[reporter_path], 'reporter_source_unchanged': True, 'interpretation': 'Only pre-existing generated metadata differs. ReporterEditor InitializeOnLoad writes this format. Its specific trigger was not independently observed; parent did not operate Unity or write this file. Preserve current bytes and linked old baseline; no claim of zero global drift or a new production PASS.', 'initial_equality_guard': 'Stopped preparation before scheduling writes; this exact difference was inspected and preserved before proceeding.'})
grant_path = RUN / 'WinterWolfTypeA/standing_authorization_original_messages_20261029.json'
standing_path = RUN / 'standing_network_recovery_authorization_20261028.json'
edge_path = RUN / 'image_transport_edge_map_20261029_1830.md'
tooling_path = RUN / 'docs_tooling_edge_resolve_20261029_182840.json'
decision_path = resume / 'bounded_resume_decision.json'
decision = {
    'schema_version': 1, 'recorded_at': timestamp, 'chain_id': chain['chain_id'],
    'parent_thread_id': PARENT, 'planned_dispatch_token': token,
    'current_direct_user_statement': '继续任务',
    'standing_direct_user_statement': '继续任务。后续同样的情况，不再需要我确认，可以继续静默执行',
    'standing_source_thread_id': '01a18093-7687-7313-aaba-7419090cc829',
    'standing_source_user_message_id': '01a180aa-7768-7222-bc85-7aa51e801cdd',
    'standing_original_messages_file': rel(grant_path), 'standing_original_messages_sha256': sha(grant_path),
    'standing_recovery_record': rel(standing_path), 'standing_recovery_record_sha256': sha(standing_path),
    'authorization_interpretation': 'The direct current continuation and original standing permission after disclosure of possible duplicate charge support one bounded new PossessedWarg Down production request. This is an agent execution judgment applying the continuing task authorization, not a newly quoted user amount or request count.',
    'not_automatic_network_recovery': 'No factual ECONNRESET, curl failure or uncertain_result exists for the original PossessedWarg request. Do not manufacture it or enter a branch requiring such evidence.',
    'character': 'PossessedWarg', 'index': 79, 'direction': 'Down', 'revision': 'revision_01',
    'max_requests': 1, 'limit_origin': 'Conservative agent execution bound; user did not specify a monetary budget or numeric retry allowance in the current message.',
    'accept_possible_duplicate_charge': True, 'original_outcome': 'unknown', 'original_possible_charge': 'unknown',
    'original_request_started': original_down['started'],
    'original_request_file': rel(character_dir / 'generation/Down/request.json'),
    'original_request_sha256': old_files['generation/Down/request.json'],
    'prior_unknown_requests': 1, 'resets_automatic_counter': False,
    'counter_policy': 'Preserve all historical request records and consumed recovery counters. This independent once-only application does not reset, borrow or reclassify any prior allowance.',
    'parameters': {'endpoint': 'https://aihub.dog/v1/images/edits', 'model': 'gpt-image-2', 'quality': 'medium', 'size': '1536x1024', 'n': 1},
    'transport': 'curl_https_no_retry', 'force_direct': True, 'edge_ip': '191.101.132.254',
    'edge_assessment_file': rel(edge_path), 'edge_assessment_sha256': sha(edge_path),
    'edge_tooling_file': rel(tooling_path), 'edge_tooling_sha256': sha(tooling_path),
    'rejected_external_inference': 'The external edge note says PossessedWarg Down was unsent. Missing outcome does not establish unsent or uncharged; both remain unknown.',
    'generator_before_sha256': sha(RUN / 'generate.mjs'),
    'preserved_evidence_file': rel(resume / 'original_character_files.json'),
    'preserved_evidence_sha256': sha(resume / 'original_character_files.json'),
    'protected_six': protected,
    'image_requests_sent_by_parent_this_turn': 0, 'paid_diagnostic_requests': 0,
    'parent_Unity_operations_this_turn': 0,
    'stop_conditions': ['Existing matching Down success or live generator: recover existing result and do not send.', 'Only a fresh revision_01 with active matching successor owner/token and checked intent may send.', 'One attempted new request consumes this bound; failure or unknown result stops additional paid resume requests.', 'No proxy/system/hosts/TLS changes, paid transport probe, silent retry, concurrency or external messaging.'],
}
save_new(decision_path, decision)
save_new(resume / 'synchronization.json', {
    'observed_at': timestamp, 'parent_thread_id': PARENT, 'project_root': str(ROOT), 'unity_version_file': version,
    'prior_chain_sha256': chain_sha, 'prior_progress_sha256': progress_sha,
    'completed': 107, 'authorized': 108, 'remaining': remaining,
    'protected_six': protected, 'character_files_count': len(old_files),
    'production_paths': len(production), 'production_drift_since_Zombie_closeout': drift,
    'image_generation_processes': processes, 'allgif_count': manifest['count'],
    'mcp_endpoint': 'http://127.0.0.1:8088/mcp', 'Unity_state': 'Not observed in this parent turn. Previous release is historical only; successor must rediscover identity, read errors and freshly establish idle state.',
    'parent_production_mutations': 0, 'parent_Unity_calls': 0, 'parent_image_requests': 0,
})

handoff_path = RUN / ('conversation_handoffs/' + stamp + '_PossessedWarg_authorized_resume.md')
prompt_path = resume / 'successor_prompt_utf8.txt'
decision_rel = rel(decision_path)
resume_rel = rel(resume)
handoff_rel = rel(handoff_path)
prompt = f'''# PossessedWarg79 唯一接棒：四方向恢复与108项队列收口

在 E:/MyTowerGame 继续执行敌人四方向任务，本聊天只负责 PossessedWarg（index79）。当前有效完成107/108，唯一未完成为本角色；所有续作 completed_pending_user_art_review 只表示内部完成，用户尚未美术批准。直接恢复实际工作并完成原任务，不停在分析或计划。本文为完整UTF-8接力说明，不依赖旧聊天图片。

## 1. 唯一所有权与任务边界

父聊天：{PARENT}。本次 dispatch_token：{token}。
工程项目ID：{PROJECT}；本地目录 E:/MyTowerGame；Unity版本文件应为2022.3.62f3c1；当前有效HTTP MCP为 http://127.0.0.1:8088/mcp。

先读取 E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/conversation_chain.json。只有 state=active、current_character=PossessedWarg、owner_thread_id等于本聊天实际CODEX_THREAD_ID、dispatch_token等于上述完整令牌，才能修改工作区或操作Unity。handoff_ready期间只读，父聊天登记成功后再继续；没有超时抢锁。创建是异步的，父聊天会先保存真实创建响应，再将active所有权作为最后一次工作区写入。不要使用Zombie/session_current.py的owner()，它硬编码旧角色和旧令牌。

一聊天一角色，一次一个生产任务；不fork、不派子代理、不并行角色、不建自动化、不发跨聊天消息。此处新聊天由2026-10-26用户明确要求的逐角色自动新聊天循环授权。你是最后一个角色：全部有效完成后直接收口，不为已空队列创建后继；真实阻断则如实保存并停止相应操作。禁止Git提交/推送/拉取/清理/覆盖、构建部署、memory写入、数值表与导出产物修改、声音恢复和其他工程操作。

## 2. 开工读取与增量基线

完整读取当前根及目标目录链的AGENTS.md、ProjectSettings/ProjectVersion.txt，并读取以下当前文件：

- E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md
- E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/CONTINUATION_PROTOCOL_20261026.md
- E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/IMAGE_RELAY_RECOVERY_20261026.md
- E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/NEXT_ENEMY_TASK.md
- E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/progress.json
- E:/MyTowerGame/Docs/EnemyDirectionReview/README.md
- E:/MyTowerGame/Docs/EnemyDirectionReview/PREFAB_CHANGES_SUMMARY_20261026.md
- E:/MyTowerGame/{handoff_rel}
- E:/MyTowerGame/{decision_rel}
- E:/MyTowerGame/{resume_rel}/synchronization.json
- E:/MyTowerGame/{resume_rel}/original_character_files.json
- E:/MyTowerGame/{resume_rel}/production_paths_before.json
- E:/MyTowerGame/{resume_rel}/backup_manifest.json
- E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/standing_authorization_original_messages_20261029.json
- E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/standing_network_recovery_authorization_20261028.json

定向读取PossessedWarg的21份旧材料、六保护指纹、现有业务组件/调用与生命周期、生成/暂存/安装/record/运行/归档入口及直接依赖。先git status/diff只读，重新核现场；大量历史修改保留。父聊天本轮扫描Assets/Packages/ProjectSettings/Luban共5705路径，相比Zombie最终指纹仅Assets/StreamingAssets/build_info改变，当前内容为“{build_info_text}”。ReporterEditor源码SHA未变，其InitializeOnLoad会写此格式；具体触发未独立观察，父没有操作Unity或写该文件。差异与当前原字节备份见E:/MyTowerGame/{resume_rel}/preexisting_production_drift.json和backup_manifest.json，不能宣称全局零漂移。新接力基线保留当前值并链接旧基线，不回滚文件；AllGIF清单1744项。这些是交接快照，不代替你的开工现场核对。不要修改全局历史基线来掩盖差异。父聊天本轮没有操作Unity、发送图像请求或修改生产。

Python固定使用 C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8。所有中文记录UTF-8，工具先实际阅读，不整段无条件连跑。

## 3. 已知图像现场与本次有界恢复依据

旧Up成功：E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/PossessedWarg/generation/Up/raw.png，1386935 bytes，SHA256=8B015639A80D16F54901C294CECF061A08479E5E7029206FB6C05057DB106868。同目录request/result保留。旧观察称后脑无脸，但有前向内耳垫和脚趾线，尚未接受；必须自己实际查看，再据实修正，不直接沿用旧结论。复用该成功图，不重发初次Up；必要的美术返修必须有实际问题、来源与新revision，不能假冒恢复请求。

旧Down仅prompt.txt和request.json，开始2026-10-26T00:54:57.839Z，request SHA256=B2B3C9FB4B78E2FFB5E606FCE95BB2843575982CADBE6C6E97D352346D27BA4A。没有raw/result/uncertain_result/console、保存的服务响应或provider request/job ID。结果和可能费用始终unknown；不能改成未发送、未收费、明确失败或ECONNRESET。原请求与全部21份旧证据保持原字节，补充计划和审阅另建文件。仍无stage、install或runtime，不重复prepare，不伪造Down为Up副本。

用户本轮直接说“继续任务”。此前在明确告知Down ECONNRESET、结果不明及可能重复计费后，用户原话“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”，原消息ID为01a180aa-7768-7222-bc85-7aa51e801cdd、源聊天01a18093-7687-7313-aaba-7419090cc829。父聊天结合当前继续指令与真实standing grant，执行判断允许本角色Down revision_01一次新的有界生产请求；不是虚构用户本轮说过金额、次数或新的同意重复费用原话。完整依据与来源SHA已在bounded_resume_decision.json固定。

旧standing自动网络恢复分支只接受有实际错误证据的失败，本角色不具备该前提，不冒用该分支。本次是独立、一次性、有记录的授权应用；不重置或借用任何角色的历史计数，不更改旧unknown。若现场出现匹配成功Down或在途生成进程，先回收已有结果，取消新请求。若唯一新请求失败或结果unknown，保留新旧全部材料并停止继续付费恢复，不以美术返修或新目录再补发。

## 4. 先补齐严格工具入口，再执行恰好一次Down恢复

读取并沿用 E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/generate_character.ps1 与 generate.mjs。当前普通revision需要原Down/raw.png，缺失时必失败；--authorized-uncertain-retry仅限SabretoothTiger Down02，不可借用；--authorized-network-recovery需要真实错误与outcome，不可伪造；--authorized-resume目前只登记WinterOgre、ScarabMounted、WinterWolfTypeA，尚未包含本角色。

允许在Docs工具中做严格定点扩展：仅PossessedWarg / Down / revision_01 / --authorized-resume。保留修改前SHA、完整备份、patch与范围说明；不移除任何其他分支的保护，不另写绕过主入口的付费生成器。PS1已有-AuthorizedResume传参及进程防重，通常无需修改PS1。先应用imagegen技能并告知，原AIHub入口与用户授权优先于通用CLI约定。

你登记与实际owner绑定的authorized_resume记录和该新目录的recovery_intent.json，引用父decision路径/SHA、standing原消息路径/SHA、新owner/token、角色/方向/revision、max_requests=1、旧Down request SHA、完整21旧文件SHA、六保护指纹、修改后generator SHA、固定参数及直连路由。入口必须验证这些事实：

1. 实时chain为active且owner/token/角色匹配，实际进程身份与授权一致。
2. 仅精确本角色Down01且授权只一次；目录无request/raw/result/uncertain_result；旧Down原始证据没有变化；无任何可复用的成功Down；无在途生成。
3. 父授权依据、intent和证据SHA可核对，旧结果/费用保持unknown，无伪造错误、篡改计数或重用他人额度。
4. 只使用原atlas与完整source参考作为恢复输入，不要求缺失旧Down/raw，不以Up充作Down；实际源图审阅后编写完整新Down prompt，原Down prompt不改。
5. 正式请求前重新核目标Unity身份和空闲，保存新鲜且owner/token匹配的preflight；--preflight只能验证输入/路由，不写request、不联网计费。
6. n=1、gpt-image-2、quality=medium、size=1536x1024、endpoint=https://aihub.dog/v1/images/edits。Curl固定--resolve aihub.dog:443:191.101.132.254，HTTPS域名和证书验证保留；不得--system-local-proxy、不改hosts/系统代理、不禁TLS、不发付费诊断。只在调用进程临时清HTTP_PROXY/HTTPS_PROXY/ALL_PROXY并设置NO_PROXY=aihub.dog，finally恢复原环境。密钥仅运行时DPAPI读取，不能打印、写盘或发送到其他域名。
7. 独占写request及请求intentSHA后只尝试一次，无自动HTTP重试。保存真实HTTP状态、结果、raw或unknown，不能因输出缺失声称未计费。发生创建/超时不明先查本地与可核服务证据，不盲目重复。

本次执行命令的参数为 generate_character.ps1 -Character PossessedWarg -Direction Down -Revision revision_01 -AuthorizedResume -Transport Curl；前提全部满足后执行一次。工具扩展前不得直接调用它碰运气。图像返回保存实际格式/尺寸，原始响应图永久保留；后续像素修补有父图SHA、范围、方法和新版本标识。

## 5. Unity路由、身份和占用

根AGENTS中的FreedomTower_1 / D:/FreedomTower_1 / 8082是旧说明。本任务明确E:/MyTowerGame；8082属于另一个工程，8080属于CatchFish，不操作。当前8088路由见原执行prompt第8节与现有mcp_call.py。

active后先读现场错误，再fresh editor/state与实际probe。复用Client.identity()：读取mcpforunity://custom-tools和mcpforunity://instances，动态选择MyTowerGame完整Name@hash，set_active_instance，再读mcpforunity://project/info核projectRoot/version。新连接、重连、域重载后重新做。不要硬编码旧实例、依赖窗口焦点或用历史release当当前空闲结论。

确认非Play、未编译/更新/域重载、无其他review/录像/数值验证/手动模拟、无未保存场景；不抢占、不强停其他任务。本任务自己的两轮Play已授权，不再逐轮询问。服务断线先分段等约5秒再限次恢复，复用已有服务不杀进程。只能文件/命令行/Unity MCP，禁止未经确认控制桌面；确需电脑控制必须先明确弹确认。无法恢复就准确提示E:/MyTowerGame、2022.3.62f3c1、unityMCP HTTP Local8088的实际失败环节与开启动作，验证标未完成。

必要C#改动必须极小、先读调用关系与回归边界；按本工程MCP强制刷新编译、等待全ready、查error/errorCS及scriptCompilationFailed，不清控制台。编译期间不继续改代码。

## 6. 按本角色原设、原Wolf合同制作和安装

战斗：Assets/Prefabs/Enemy/Enemy_PossessedWarg.prefab。
source：Assets/_UIAssets/Monsters/Dogs/PossessedWarg/PossessedWarg.prefab。
atlas：Assets/_UIAssets/Monsters/Dogs/PossessedWarg/PossessedWarg.png。
Directions：Assets/_UIAssets/Monsters/Dogs/PossessedWarg/Directions。
原controller：Assets/_UIAssets/Monsters/_Common/Animations/Wolf/Controller.controller。

不要相信通用anatomy_plan的色彩/琥珀眼/金背刺等描述，先实际看自身atlas、完整source/battle和源结构，按实际绑定与器官整理新审阅计划。检查四足、尾巴、头部三表情、附件和前后遮挡；Up是真背面无脸、前向耳垫和前趾线，Down是真正面。不得用侧图旋转/镜像伪造上下。保色彩、描边、器官数量与身份，禁止凭文件名重新设计或引入其他狼的具体造型。

复用已读工具进行透明处理、切片和离线四方向预览；检查品红残留、孔洞、完整描边、连接根、pivot/PPU、sorting、四爪及尾根。局部改图要留版本/父SHA，不覆盖raw。不增加原设没有的器官。保留原左右侧图/曲线、原控制器state/Speed/Attack/兼容Action、时长loop、float/PPtr与事件合同。按本角色原生Wolf行走及攻击蓄力/发力时序制作；肢体错相但连接根固定，不把上一角色短步或死亡修法机械套用。

先审自身MonsterAnimEventReceiver/HeadSprites与原生头事件、方向系统/对象池生命周期；不能因为别的角色修过就自动套修。若原组件语义直接通过，保留原绑定。只有现场发现真实缺陷才最小定点修复并留证。根GUID、源atlas/source/meta、非美术组件、碰撞器、HP/血条/锚点和业务参数保持；每方向及攻击/死亡/复用均无地面影。

两方向原图及分件通过实际视觉审阅后再stage、单角色install、Verify。已有安装清单出现时先恢复对应阶段，禁止删除清单绕过防重。安装前后对六保护、当前生产路径全并集及prefab原组件语义做增量审计，不把历史全局失败改成全局PASS。只允许本角色battle及Directions美术变化；Reporter的build_info若自动变化须用未变Reporter源码、实际时间/设备精确归因。意外变化停止查明，不扩大白名单掩盖。

## 7. 两轮真实Play与视觉审阅必须全部完成

最终生产revision冻结并保存prePlay绑定后，使用现有测试器执行普通死亡轮与指定Up死亡轮，每轮84检查，共168PASS/0FAIL；失败或返修使用新未占用runtime revision，保留旧失败轮，不用旧summary冒充本次。记录实际帧号、normalizedTime、日志、PNG和SHA。运行前后核生产绑定与源合同一致；不以离线图、手动Animator.Update或预期文案代替真实Play。

覆盖四方向行走、连续转向、纯纵向出生/路径、斜向主轴/滞回、近零位移保持、原生状态与三表情头事件、攻击蓄力/发力、受击及致死闪白结束、死亡连接/旋转/收缩淡出、自动回收与同实例再生、真实帧暂停恢复及1x/2x/3x。死亡按实际renderer淡出机制描述，不虚称一体alpha。没有运行或没有看过的行为不写PASS。

实际审最终离线四向/透明分件/atlas、两轮four_directions与runtime_visual_strip、按时序选的真实原始PNG。审12个最终动作GIF的足够连续帧或播放，覆盖上下步态、转向、攻击/受击/死亡/复用和倍速；工具无法播放可按编码帧序审阅并如实说明。原生Walk周期必须从本角色当前合同实测，GIF用真实相位/真实帧编码；需要10ms量化时保存修前GIF/manifest并报告误差，不能照抄500/670ms旧角色值。保存视觉板清单、采样位置/不同PNG数、GIF编码抽帧数量及限制，不宣称逐帧看完未看的全量。

一次只加载1至2张清晰预览和必要局部，完整原图及真实帧留盘，避免32MiB图片历史问题。程序通过但视觉有缺陷必须修并重跑最终两轮，直到本角色满足原prompt或有真实无法自主解决的阻断。

## 8. record、GIF与最终收口

只有最终版本一致、Verify与增量scope通过、两轮168PASS/0FAIL且实际视觉审阅完成，才能用现有record入口。中文真实观察先存record_note_utf8.txt再传入，读取回写确认无乱码、未引用旧runtime。状态仅completed_pending_user_art_review、user_approved=false，不能解释继续授权为美术批准。

AllGIF当前1744项，包含历史，不能当角色完成数。先保清单及来源/归档SHA，新增GIF保留原件并通过collect_gifs.py集中归档，不能覆盖同名不同内容；逐项核新增与全部旧来源/副本SHA，最终清单从实时文件读取。保存生成账本（旧Down仍unknown、新请求实际结果、费用未独立核实则如实说）、最终生产/源/动画/暂存与runtime版本绑定、scope、视觉审阅、安装Verify、Unity释放和归档证据。

完成后重读全部108条的有效完成证据与剩余项。若本角色成功则107升108，更新progress、README、主prompt实时块、NEXT和带时间总结；chain标complete，保留全部旧blocked/unknown/请求费用事实与用户待美术审核状态，不创建空后继。可新增本次总收口汇总，不改PREFAB_CHANGES_SUMMARY_20261026.md冻结快照或首批用户批准证据。

最后以新的8088身份、错误→state/probe核实安全交还单一clean Boot、非Play、无任务、无编译失败，记录真实状态。若真实阻断保留准确阶段、请求状态和恢复条件，不谎称后台工作或108完成。最终回复简洁给实际进度、结果/限制、AllGIF入口及本次证据链接。当前任务不包含发布包、设备或长期战斗验收。
'''
text_new(prompt_path, prompt)
handoff = f'''# PossessedWarg79：一次有界恢复接力

时间：{timestamp}。父聊天：{PARENT}；新令牌：{token}。当前107/108；本聊天已经完成Zombie118，不能在同一聊天生产第二个角色，按用户明确授权的串行新聊天规则仅准备唯一PossessedWarg后继。

本轮用户直接“继续任务”，并有真实standing原话“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”。原消息来源、SHA及本次解释见 {decision_rel}。本次允许Down revision_01一次新生产请求是代理结合当前指令与原授权作出的有界执行选择；不是用户本轮给出金额或次数的新原话。旧Down结果与可能费用unknown，原request与全部21材料不变；没有事实可将它改为ECONNRESET、未发送或未收费，不进入要求此类证据的自动网络恢复分支，不重置或借用历史计数。

父本轮只做文件/命令行只读同步和Docs调度准备；生产修改0、Unity调用0、图像请求0、付费诊断0。六保护一致，Assets/Packages/ProjectSettings/Luban5705路径相比Zombie最终指纹仅build_info时间元数据改变，当前“{build_info_text}”，Reporter源码未变；具体触发未独立观察，不宣称全局零漂移，保留当前字节和新旧基线，见{resume_rel}/preexisting_production_drift.json。AllGIF1744。没有在途图像生成。Unity本轮未观察：Zombie昨日释放记录仅作历史；新owner必须先动态核8088身份、错误、fresh状态/probe与占用，不能继承昨日空闲结论。

完整接力提示：{rel(prompt_path)}。开工快照：{resume_rel}/synchronization.json；完整生产基线：{resume_rel}/production_paths_before.json；21旧材料指纹：{resume_rel}/original_character_files.json；原chain/progress/NEXT/README/主prompt及生成器备份：{resume_rel}/backup_manifest.json。旧停止记录与历史总结保留。

调度先handoff_ready，所有生产/Unity停止。仅创建一个全新本地PossessedWarg聊天，保存真实返回后将新threadId/hostId与该token登记active；父随后停止全部工作区写入。不fork、不子代理、不自动化、不并发、不发送跨聊天消息。创建结果不明先查响应/聊天列表，不重复创建。后继按完整提示严格扩展Docs工具、复用Up、一次恢复Down、单角色安装、两轮真实84、视觉与GIF审阅、record/范围/版本/归档；仅待用户美术审核。成功则108/108并chain complete，不空建后继；失败如实阻断。
'''
text_new(handoff_path, handoff)
dispatch_path = resume / 'prepared_dispatch.json'
save_new(dispatch_path, {'prepared_at': timestamp, 'parent_thread_id': PARENT, 'dispatch_token': token, 'character': 'PossessedWarg', 'project_id': PROJECT, 'project_root': 'E:/MyTowerGame', 'target': {'type': 'project', 'projectId': PROJECT, 'environment': {'type': 'local'}}, 'title': 'PossessedWarg79 四方向恢复与队列收口', 'prompt_file': rel(prompt_path), 'prompt_sha256': sha(prompt_path), 'handoff_file': handoff_rel, 'handoff_sha256': sha(handoff_path), 'decision_file': decision_rel, 'decision_sha256': sha(decision_path), 'creation_status': 'not_requested', 'max_new_threads': 1})

live = f'{timestamp} 用户本轮继续任务。107/108，唯一未完成PossessedWarg79恢复接力已准备；新dispatch_token={token}。基于当前直接继续与已核真实standing grant，登记Down revision_01一次有界生产补发，旧请求结果/费用unknown永久保留，不伪造网络错误、不重置计数、不付费诊断。依据{decision_rel}；完整新提示{rel(prompt_path)}；总结{handoff_rel}。chain.state及真实owner以conversation_chain.json为准，handoff_ready只读，active且新owner/token匹配才生产。父本轮没有Unity或图片调用、没有生产改动；5705路径仅build_info有既存时间戳差异，已保留并单列、未称全局零漂移；AllGIF1744。旧停止说明和107项待用户美术审核证据完整保留；成功才108/108并complete，不创建空后继。'
assert sha(chain_path) == chain_sha and sha(progress_path) == progress_sha, 'Scheduling changed during preparation'
next_content = '# PossessedWarg79 完整恢复接力\n\n' + live + '\n\n' + prompt
replace_text(RUN / 'NEXT_ENEMY_TASK.md', next_content)
for path, begin, end in [(RUN / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md', '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->', '<!-- ENEMY_SERIAL_LIVE_STATE_END -->'), (ROOT / 'Docs/EnemyDirectionReview/README.md', '<!-- ENEMY_README_LIVE_BEGIN -->', '<!-- ENEMY_README_LIVE_END -->')]:
    original = path.read_text(encoding='utf-8-sig')
    assert original.count(begin) == original.count(end) == 1, path
    updated = re.sub(re.escape(begin) + r'.*?' + re.escape(end), lambda match: begin + '\n' + live + '\n' + end, original, flags=re.S)
    updated += '\n\n2026-10-30 PossessedWarg恢复接力：' + live + '\n'
    replace_text(path, updated)

previous_stop = {key: progress.get(key) for key in ('status', 'stopped_at', 'stop_reason', 'current', 'completed_count', 'last_completed_handoff')}
progress.setdefault('historical_stops', []).append(previous_stop)
for key in ('stopped_at', 'stop_reason'):
    progress.pop(key, None)
progress.update(status='in_progress', current='PossessedWarg', updated_at=timestamp, resume_decision=decision_rel, resume_handoff=handoff_rel)
item = next(item for item in progress['items'] if item['name'] == 'PossessedWarg')
item.update(status='reference_prepared', previous_status_before_resume='blocked', current_stage='authorized_resume_pending_owner', original_down_outcome='unknown', original_down_charge='unknown', resume_decision=decision_rel, resume_handoff=handoff_rel, resumed_at=timestamp)
replace_json(progress_path, progress)
old_stop = {key: chain.get(key) for key in ('state', 'owner_thread_id', 'dispatch_token', 'current_character', 'stopped_at', 'stop_reason', 'stop_record', 'recovery_file', 'last_handoff_file', 'blocked_reason', 'blocked_owner_retained', 'no_successor_creation_reason', 'current_stage')}
chain.setdefault('historical_stops', []).append(old_stop)
for key in ('stopped_at', 'stop_reason', 'blocked_reason', 'blocked_character', 'blocked_owner_retained', 'no_successor_creation_reason', 'parent_writes_stopped_at'):
    chain.pop(key, None)
chain.update(state='handoff_ready', owner_thread_id=PARENT, parent_thread_id=PARENT, dispatch_token=token, current_character='PossessedWarg', character_status_at_handoff='reference_prepared', current_stage='authorized_resume_pending_owner', current_blocked=False, updated_at=timestamp, handoff_ready_at=timestamp, dispatch_ready_for='PossessedWarg', successor_created=False, prepared_dispatch_file=rel(dispatch_path), creation_response_file=None, previous_handoff_file=chain['last_handoff_file'], last_handoff_file=handoff_rel, handoff_sha256=sha(handoff_path), progress_sha256_at_handoff=sha(progress_path), resume_character='PossessedWarg', resume_stage='One bounded authorized Down01 resume after fresh successor identity, evidence and tool guards', recovery_file=decision_rel, resumed_at=timestamp, resumed_by_thread_id=PARENT, resumed_with_dispatch_token=token, ownership_transfer_note='Scheduling preparation only. No active production owner until one new local successor is created and its exact identity is registered. Parent performs no Unity or image calls.', mcp_endpoint='http://127.0.0.1:8088/mcp')
chain.setdefault('stage_history', []).append({'at': timestamp, 'character': 'PossessedWarg', 'stage': 'authorized_resume_handoff_ready', 'parent_thread_id': PARENT, 'dispatch_token': token, 'evidence': decision_rel})
replace_json(chain_path, chain)
save_new(resume / 'preparation_result.json', {'prepared_at': timestamp, 'resume_directory': rel(resume), 'dispatch_token': token, 'prompt_file': rel(prompt_path), 'prompt_sha256': sha(prompt_path), 'decision_file': decision_rel, 'handoff_file': handoff_rel, 'prepared_dispatch_file': rel(dispatch_path), 'chain_sha256': sha(chain_path), 'progress_sha256': sha(progress_path), 'state': chain['state'], 'production_mutations': 0, 'Unity_operations': 0, 'image_requests': 0})
print(json.dumps({'resume_directory': rel(resume), 'dispatch_token': token, 'prompt_file': rel(prompt_path), 'prompt_characters': len(prompt), 'state': chain['state'], 'production_paths': len(production), 'production_drift': len(drift), 'character_files': len(old_files), 'protected_six': True, 'allgif': manifest['count']}, ensure_ascii=False))
