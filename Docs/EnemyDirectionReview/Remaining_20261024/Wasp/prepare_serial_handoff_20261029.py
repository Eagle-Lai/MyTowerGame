"""Release the completed Wasp and prepare one fresh local Watchdog successor."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, re, uuid

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
OWNER = '01a1833c-f96c-74a1-b7f2-2281f6ab321d'
OLD = 'warg-to-wasp-20261028_235853-1e651dcf-1586-4ebc-9926-3b8be7348e7d'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
now = lambda: datetime.now(timezone(timedelta(hours=8)))
rel = lambda p: p.relative_to(ROOT).as_posix()

def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def data(value):
    return value.get('structuredContent') or json.loads(value['content'][0]['text'])

chain = read(H / 'conversation_chain.json')
progress = read(H / 'progress.json')
assert chain['state'] == 'active' and chain['owner_thread_id'] == OWNER
assert chain['dispatch_token'] == OLD and chain['current_character'] == 'Wasp'
done = next(r for r in progress['items'] if r['name'] == 'Wasp')
assert progress['completed_count'] == 93 and done['status'] == 'completed_pending_user_art_review'
assert not done['user_approved']
remaining = [r for r in progress['items'] if r['status'] not in ['completed_pending_user_art_review', 'user_approved']]
recoverable = [r for r in remaining if r['status'] not in ['not_started', 'blocked']]
selected = min(recoverable or [r for r in remaining if r['status'] != 'blocked'], key=lambda r: r['index'])
assert selected['name'] == 'Watchdog' and selected['index'] == 105 and selected['status'] == 'not_started'
assert next(r for r in remaining if r['name'] == 'PossessedWarg')['status'] == 'blocked'
W = H / 'Watchdog'
assert all(p.is_relative_to(W / 'reference') for p in W.rglob('*') if p.is_file())
t = next(r for r in read(H / 'local_baseline.json')['targets'] if r['name'] == 'Watchdog')
six = {p: sha(ROOT / p) for key in ['battle', 'source', 'atlas'] for p in [t[key], t[key] + '.meta']}
assert all(six.values()) and all(sha(W / 'reference' / Path(p).name) == v for p, v in six.items())
final = read(D / 'final_validation_20261029.json')
binding = read(D / 'version_binding_final_20261029.json')
scope = read(D / 'scope_incremental_final_20261029.json')
assert (final['passes'], final['failures'], final['actual_png_frames']) == (168, 0, 596)
assert final['final_revision'] == 'art_r02_flap_r03'
assert sha(D / 'version_binding_final_20261029.json') == final['version_binding_sha256']
assert sha(D / 'scope_incremental_final_20261029.json') == final['incremental_scope_sha256']
assert all(sha(ROOT / p) == v for p, v in binding['installed_files'].items())
probes = sorted(D.glob('unity_release_probe_20261029_response*.json'), key=lambda p: p.stat().st_mtime)
probe_path = probes[-1]
probe = read(probe_path)
state = probe['results'][1]['data']
live = data(probe['results'][3])['data']['result']
assert probe['success'] and probe['transport'] == 'http://127.0.0.1:8088/mcp'
assert probe['project']['projectRoot'].lower() == 'e:/mytowergame'
assert probe['project']['unityVersion'] == '2022.3.62f3c1'
assert data(probe['results'][2])['data'] == []
assert state['advice']['ready_for_tools'] and not state['staleness']['is_stale'] and state['activity']['phase'] == 'idle'
assert not state['tests']['is_running'] and not state['compilation']['is_compiling']
assert not state['compilation']['is_domain_reload_pending'] and not state['assets']['is_updating']
assert not state['assets']['external_changes_dirty']
assert all(live[k] is False for k in ['playing', 'compiling', 'failed', 'updating', 'sceneDirty', 'balance', 'recording', 'review', 'manual'])
assert live['scene'] == 'Assets/Scenes/Boot.unity' and live['sceneCount'] == 1
assert (now() - datetime.fromisoformat(probe['observed_at'])).total_seconds() < 180
stamp = now().strftime('%Y%m%d_%H%M%S')
token = 'wasp-to-watchdog-' + stamp + '-' + str(uuid.uuid4())
handoff = H / 'conversation_handoffs' / (stamp + '_Wasp_completed.md')
assessment = W / ('successor_assessment_' + stamp + '.json')
prompt_path = W / ('successor_prompt_' + stamp + '.txt')
release_path = D / 'handoff_release_20261029.json'
dispatch_path = W / 'prepared_dispatch_20261029.json'
assert all(not p.exists() for p in [handoff, assessment, prompt_path, release_path, dispatch_path])
write(release_path, {
    'observed_at': probe['observed_at'], 'released_by_thread_id': OWNER, 'current_character': 'Wasp',
    'next_character': 'Watchdog', 'next_dispatch_token': token, 'transport': probe['transport'],
    'project': probe['project'], 'unity_instance': state['unity']['instance_id'], 'editor_state': state,
    'live_probe': live, 'console_errors': [], 'safe_to_handoff': True,
    'external_changes_dirty': False, 'probe_response_file': probe_path.name,
    'probe_response_sha256': sha(probe_path),
    'note': 'Single clean Boot; Play/tests/review/balance/recording/manual/compile/reload/update idle. Existing ForceUpdate obtained fresh facts; no plugin source modified.'})
write(assessment, {
    'observed_at': now().isoformat(), 'completed_count': 93, 'authorized_count': 108,
    'selection': 'Resume started nonblocked role first, otherwise lowest incomplete nonblocked index.',
    'remaining': [{k: r[k] for k in ['index', 'name', 'status']} for r in remaining],
    'next_character': 'Watchdog', 'next_index': 105, 'status': 'not_started', 'dispatch_token': token,
    'target': t, 'protected_six': six, 'reference_matches_live': True,
    'existing_files': [p.relative_to(W).as_posix() for p in sorted(W.rglob('*')) if p.is_file()],
    'no_generation_staging_install_or_runtime': True,
    'blocked_preserved': [r for r in remaining if r['status'] == 'blocked'],
    'project_id_at_chain': chain['project_id'],
    'project_id_source': 'Historical chain association only; fresh list_projects confirmation required before dispatch.'})
summary = f'''# Wasp(index 104) 完成与 Watchdog(index 105) 唯一串行交接

时间：{now().isoformat()}。父线程 `{OWNER}`，旧 token `{OLD}`。Wasp 已 record，状态 `completed_pending_user_art_review`，`user_approved=false`。实时进度 **93/108**。

## 最终实现与生产版本

保留原金黄色蜂形身份、大头、成对长分节触角、琥珀眼板、黑金条纹腹部及腹部原有小爪。两片奶油色脉络翼；Raised/Lowered 是同一对翼的姿态，不是四翼，不建立四足步态。Up 为无眼无口的后脑，三个表情共用同图；Down 有正常、愤怒张口、闭眼死亡三表情。

Up/Down 原始生成各一次成功，1536×1024 raw 保留复用，无待定请求、无付费返修。本地修订：翼姿注册到共同 340×500 画布、翼根像素 (300,250)、归一化 pivot (300/340,0.5)；填闭腹部微小 alpha 洞；art_r02 去除洋红溢色，Up Head order30 遮挡颈圈。flap_r03 仅改 Wasp 四个方向动画：Ready/Walk/Attack 每 1/12 秒交替翼姿，末 Raised key 为 .483333319，Death 为 Lowered。所有 clip 仍 .5 秒、60fps，侧面 float/PPtr、其他绑定、事件、设置和 loop 保持。无生产 C# 修改。

最终 revision **art_r02_flap_r03**。完整 22 路径最终快照在 `Wasp/flap_cadence_r03/manifest.json` 的 final_files，包含 battle/meta、Directions.meta 与 Directions 资源。battle SHA `{binding['installed_files']['Assets/Prefabs/Enemy/Enemy_Wasp.prefab']}`。不要删除 installed_manifest、重跑 stage/pack/Build/install 或用初版清单覆盖最终版本。暂存 atlas/sprite/layout 三文件与生产 SHA 相同，Unity 实际导入 Multiple、PPU100、alphaIsTransparency=true、mipmaps=false、12 sprite；矩形/pivot 与规范逐项吻合。

## 两轮真实运行与实际视觉检查

runtime_r01：84 PASS/0 FAIL，299 张真实 PNG，记录 SHA `{final['runtime'][0]['records_sha256']}`。
runtime_updeath_r01：84 PASS/0 FAIL，297 张真实 PNG，记录 SHA `{final['runtime'][1]['records_sha256']}`。第二轮指定 Up 死亡。总计 168/0、596 张真实 PNG，两轮均回到非 Play、clean Boot；art_r02/flap_r03 均在这两轮之前完成。

实际查看离线 proof/翼根/透明分件、两轮 four_directions、runtime strip、10 张时序/振翅/愤怒板（256 采样位、232 张不同真实源 PNG）、8 张原尺寸 PNG，及 12 GIF 各 5 个编码帧共 60 帧。观察到翼根被头身正确遮挡、Up 无脸、Down 愤怒与死亡表情正确，原侧面半透明翼姿保留、四向体量一致；攻击前压回收、全身受击白闪恢复、Down/Up 死亡倾斜缩小淡出、自动回收及同实例复用正常，连续转向无倒置，暂停冻结/恢复和 1×/2×/3×有时序证据。原尺寸图血条与触角留有间距、无身体裁切、无地面阴影或断肢。未实时播放 GIF、未逐 GIF 全帧审核；所有596 PNG保留并哈希。美术批准仍由用户决定。

record 已执行，AllGIF 实时 {final['global_archive_count']}，Wasp12项均当前审核版本，源与归档 SHA 一致。核心证据：
- Wasp/final_validation_20261029.json
- Wasp/version_binding_final_20261029.json
- Wasp/scope_incremental_final_20261029.json
- Wasp/visual_review_final_20261029/review.json
- Wasp/gif_archive_verification_20261029.json
- Wasp/runtime_summary.json、record_note_utf8.txt

## 范围审计与 Unity 释放

当前磁盘安装前基线 {scope['baseline_files']} → {scope['current_files']}，Assets/Packages/ProjectSettings/Luban 全路径并集22变化、20新增、0删除。仅本角色battle/Directions含meta，另单列未修改ReporterEditor产生的Play build_info时间戳。incremental unexpected0、本角色原组件语义通过；其余5保护、共享C#、其他角色、配置表、源图/源prefab无漂移。历史全局291 unexpected和6个其他角色语义失败没有在本轮重审或声称全局PASS。

正确 Unity 为 E:/MyTowerGame、2022.3.62f3c1、HTTP8088。通过现有 Client.identity 动态读 custom-tools/instances、明确选现场完整ID、核对project/info。当前单场景 clean Boot、非Play，编译/重载/更新/tests/review/balance/recording/manual全部idle，failed=false、error0、ready=true、external_changes_dirty=false。现有 ForceUpdate刷新真实空闲快照；未修改插件、未清日志、未使用桌面控制。释放证据 `{rel(release_path)}`，其 probe 响应 SHA 已绑定。

## 下一唯一 Watchdog

余15项，其中 PossessedWarg 旧 blocked/uncertain 保留；14项not_started，按index选择 Watchdog105。当前只有8个reference文件，没有anatomy/generation/staged/install/runtime，六保护与reference一致，详见 `{rel(assessment)}`。源prefab `{t['source']}`；atlas `{t['atlas']}`；battle `{t['battle']}`；共用controller `{t['controller']}`。

下一聊天自行审完整源图、层级、四足/尾根/表情、原float/PPtr/事件/时长/loop、战斗与对象池生命周期；按Watchdog实际身份设计正背，不复制Warg或PossessedWatchdog具体造型。开工建立当前磁盘增量基线，不能把旧全局差异或Git HEAD当新基线。此聊天不修改Watchdog生产。

新 token `{token}`。执行入口 `{rel(prompt_path)}` 与 NEXT_ENEMY_TASK。chain先handoff_ready；现场list_projects后只创建一个fresh local后继，不fork、不子代理、不计时器、不覆盖模型/推理。明确创建成功并登记active后，父线程停止全部工作区写入。
'''
handoff.write_text(summary, encoding='utf-8')
prompt = f'''在 E:/MyTowerGame 继续敌人四方向串行续作。本聊天唯一角色 Watchdog(index 105)，是用户已授权循环中的唯一全新 local 后继。

唯一 dispatch token：{token}
父线程：{OWNER}

开工完整读取当前磁盘：
1. E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt。
2. E:/MyTowerGame/Docs/EnemyDirectionReview/README.md、PREFAB_CHANGES_SUMMARY_20261026.md。
3. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md。
4. 同目录 CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json。
5. 同目录standing_network_recovery_authorization_20261028.json、TreasureChest/standing_recovery_application_20261028.json，核对原授权证据，不改写旧uncertain/收费结果，不无限重试。
6. E:/MyTowerGame/{rel(handoff)}。
7. E:/MyTowerGame/{rel(assessment)}。
8. Watchdog/reference/source_structure.json及完整源参考，相关流水线脚本及实现/调用/生命周期。

只有 chain.state=active、owner_thread_id为本新聊天、current_character=Watchdog、dispatch_token与上方一致，才可操作Unity、生产或付费生成。父线程先handoff_ready，此时只读等待登记，不超时抢锁。父创建成功登记后停止全部工作区写入。开工检查新出现的请求/安装/运行文件，恢复已有阶段，避免重复prepare、生成、安装。

当前93/108。Wasp104已record，最终art_r02_flap_r03，completed_pending_user_art_review、user_approved=false。Watchdog105当前not_started，仅reference8文件，无anatomy/generation/raw/staged/install/runtime；assessment/prompt/dispatch仅调度文档。PossessedWarg旧blocked和结果不明的Down付费请求保留，不自动重发、不伪称完成。

Watchdog源路径：
- {t['battle']}
- {t['source']}
- {t['atlas']}
- Controller: {t['controller']}
reference六保护已匹配，开工仍现场核对。读完整atlas、prefab层级/绑定、controller依赖、原float/PPtr/事件/时长/loop及战斗/回收/同实例复用。自行制定Watchdog正背解剖、四足后跟与尾根、装备/头身分配；不套Warg或PossessedWatchdog具体造型。改动前建立本角色Assets/Packages/ProjectSettings/Luban全路径SHA增量基线及六保护，以当前磁盘含用户改动为准，不以Git HEAD为基线。

逐阶段执行原prompt：审原图/解剖→按需逐方向AIHub并实看raw→透明分件/切片/pivot/PPU/layout和离线proof审阅→六保护与Unity空闲复核→仅Watchdog安装Builder/Verify→两轮真实Unity Play各84项→分批实际看PNG/时序板/GIF并准确记抽样→最终生产与运行版本哈希绑定→UTF8 note/record→GIF归档SHA→路径并集增量及原组件语义审计。程序PASS不能代替美术检查；视觉失败须修复重测，保留旧revision。复用已有成功raw，结果不明先查进程/落盘/返回，不盲重发。

AIHub https://aihub.dog/v1，gpt-image-2、medium、1536x1024、n=1，复用generate_character.ps1/generate.mjs；密钥运行时读取，仅发aihub.dog，结束清理，不输出密钥或base64。遵循现有有界网络恢复授权、新intent/revision及防重护栏。Usage本地估算不当已确认账单。

保护原atlas、源prefab、GUID/root、HP/碰撞/锚点/移动战斗参数及原侧面动画曲线/PPtr/事件/时长/loop。Up必须纯后脑、正确后足方向；肩髋/颈/尾相连，不额外发明原资源没有的部件。保留攻击、受击/致死白闪、全身死亡缩小淡出、自动回收、同实例复用、暂停和1×2×3×。使用现有方向系统，不增逐帧材料/层级查找或另一套方向系统。不改其他角色或共享C#；不改配置表、Assets/ConfigJson、Assets/Gen、声音。禁止Git pull/reset/clean/commit、构建部署、fork、子代理、并行角色、计时器、模型/推理覆盖、长期memory更新。

正确Unity端点 http://127.0.0.1:8088/mcp，版本2022.3.62f3c1。复用Remaining_20261024/mcp_call.py的Client.identity：动态读custom-tools/instances，明确set当前MyTowerGame完整ID，再project/info核E:/MyTowerGame及版本。8082是其他工程，8080是CatchFish；根AGENTS中FreedomTower/D盘/8082是历史错配，本任务覆盖。重连/域重载后重新核对。MCP离线按工程规则自主恢复；失败报告具体环节与开启步骤，不能假称验证完成。默认使用Unity MCP；电脑/桌面控制须先弹对话确认，本prompt不授权桌面。只停本任务授权Play，不强停外来任务。

本任务已授权两轮真实Play测试，无需重复询问。最终Unity须单一clean Boot、非Play，tests/review/balance/recording/manual/compile/reload/update全部idle，failed=false、error0、ready=true，不清日志。若以后获得明确C#改动授权，必须正确工程refresh/compile/state/error闭环，编译期间不继续改代码。空闲缓存stale须取新事实，不能以端口监听或旧resource冒充成功。

前任Wasp最终证据：Wasp/final_validation_20261029.json及version_binding_final/scope_incremental_final/visual_review_final_20261029/review.json/gif_archive_verification。art_r02清洋红、翼根共画布340×500/pivot(300/340,.5)、后头order30；flap_r03仅四自有动画以1/12秒切翼，Death下翼，时长.5秒60fps及其他绑定/事件/设置/侧向均不变。完整22路径最终清单在flap_cadence_r03/manifest.json。runtime_r01 299帧、runtime_updeath_r01 297帧，各84/0，共168/0和596真实PNG。实际看两轮四向/strip、10板256采样位/232不同PNG、8原PNG及12GIF各5编码帧；未实时播放或逐GIF全帧。血条与触角有间距、无裁切。AllGIF{final['global_archive_count']}，Wasp12当前版且源/归档SHA一致。5405→5425路径并集22变化20新增、unexpected0、本角色语义/源保护/共享C#无漂移；Reporter时间戳单列。历史global291 unexpected/6其他角色语义失败未重跑，不称全局PASS。不要重跑前任stage/pack/Build/install，勿删installed_manifest或改前任生产。

最终状态只能completed_pending_user_art_review、user_approved=false，不替用户批准。完成Watchdog全流程或记录真实阻断并释放Unity后，重新评估实时队列：优先恢复已开始可恢复项，否则最低index非blocked。完整落盘交接，更新README实时块、原执行prompt实时块、NEXT/progress。用户已授权“一个完成→总结/更新prompt→唯一fresh local后继”循环，不逐角色再问。chain先handoff_ready，现场list_projects确认E:/MyTowerGame，再create_thread唯一全新local、不传model/thinking、不fork；新聊天等待active。create明确成功保存真实响应，登记new owner/token active作为父最后一次工作区写入，此后只读；一次有界wait_threads并报告真实created-thread。创建结果不明先查列表，不重复创建；失败保留完整可执行交接并如实报告。循环至108全部有效完成或仅余真实阻断，不绕过阻断付费试探。
'''
prompt_path.write_text(prompt, encoding='utf-8')
(H / 'NEXT_ENEMY_TASK.md').write_text('# 下一唯一角色 Watchdog(index 105)\n\n' + prompt, encoding='utf-8')
live_text = (
    f"{now().strftime('%Y-%m-%d')} Wasp104已record，93/108，completed_pending_user_art_review、user_approved=false。"
    "最终art_r02_flap_r03，12透明切片；两翼升降共340×500画布/pivot(300/340,.5)，后脑无脸，Down三表情。"
    "art_r02清洋红并以Up头order30遮颈圈；flap_r03仅四自有动画1/12秒换翼，Death下翼，.5秒60fps及侧向/其他绑定/事件/设置不变。"
    "两轮299+297共596真实PNG、168PASS/0FAIL；实际看10板256采样位/232不同PNG、8原PNG、四向/strip、12GIF各5编码帧；未实时播放或逐GIF全帧。"
    f"AllGIF{final['global_archive_count']}，Wasp12均当前版、源/归档SHA一致。5405→5425路径并集22变化20新增、unexpected0、本角色语义通过，其余5保护/共享C#无漂移，Reporter时间戳单列。"
    "旧global291unexpected/6其他角色语义失败为历史，未重跑或称全局PASS。Unity8088正确身份，单一clean Boot/非Play/全空闲/failed=false/error0/ready=true/external_changes_dirty=false。"
    f"最终Wasp/final_validation_20261029.json及绑定/范围/视觉/归档；交接{rel(handoff)}。下一唯一Watchdog105 not_started，token={token}。PossessedWarg旧blocked/uncertain保留。")
for path, begin, end in [
    (H.parent / 'README.md', '<!-- ENEMY_README_LIVE_BEGIN -->', '<!-- ENEMY_README_LIVE_END -->'),
    (H / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md', '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->', '<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    content = path.read_text(encoding='utf-8-sig')
    pattern = re.escape(begin) + r'.*?' + re.escape(end)
    assert len(re.findall(pattern, content, re.S)) == 1
    content = re.sub(pattern, lambda _: begin + '\n' + live_text + '\n' + end, content, flags=re.S)
    if path.name == 'README.md':
        content, count = re.subn(r'\d{4}-\d{2}-\d{2} 本轮当前清单为 \d+ 个文件',
                                now().strftime('%Y-%m-%d') + ' 本轮当前清单为 ' + str(final['global_archive_count']) + ' 个文件', content)
        assert count == 1
    path.write_text(content, encoding='utf-8')
done['handoff_file'] = handoff.relative_to(H).as_posix()
progress.update(current='Watchdog', updated_at=now().isoformat())
write(H / 'progress.json', progress)
dispatch = {
    'prepared_at': now().isoformat(), 'created': False, 'parent_thread_id': OWNER,
    'character': 'Watchdog', 'character_index': 105, 'dispatch_token': token,
    'project_root': 'E:/MyTowerGame', 'project_id': None, 'project_id_at_chain': chain['project_id'],
    'project_live_confirmed': False, 'handoff_file': rel(handoff), 'handoff_sha256': sha(handoff),
    'assessment_file': rel(assessment), 'assessment_sha256': sha(assessment),
    'unity_release_file': rel(release_path), 'unity_release_sha256': sha(release_path),
    'prompt_file': rel(prompt_path), 'prompt_sha256': sha(prompt_path),
    'next_task_file': rel(H / 'NEXT_ENEMY_TASK.md'), 'next_task_sha256': sha(H / 'NEXT_ENEMY_TASK.md'),
    'progress_sha256': sha(H / 'progress.json'),
    'response_file': rel(W / 'successor_creation_response_20261029.json'),
    'project_association_confirmed': False}
write(dispatch_path, dispatch)
assert not any(r.get('character') == 'Wasp' for r in chain.get('completed_handoffs', []))
chain.setdefault('completed_handoffs', []).append({
    'character': 'Wasp', 'status': 'completed_pending_user_art_review',
    'current_stage': 'recorded_pending_user_art_review', 'closed_at': now().isoformat(),
    'owner_thread_id': OWNER, 'dispatch_token': OLD, 'handoff_file': rel(handoff),
    'final_evidence': rel(D / 'final_validation_20261029.json')})
chain.update(
    state='handoff_ready', parent_thread_id=OWNER, owner_thread_id=OWNER, owner_host_id='local',
    current_character='Watchdog', dispatch_token=token, character_status_at_handoff='not_started',
    completed_count_snapshot=93, previous_handoff_file=chain.get('last_handoff_file'),
    last_handoff_file=rel(handoff), handoff_sha256=sha(handoff), successor_assessment=rel(assessment),
    prepared_dispatch_file=rel(dispatch_path), unity_release_file=rel(release_path),
    progress_sha256_at_handoff=sha(H / 'progress.json'), handoff_ready_at=now().isoformat(),
    updated_at=now().isoformat(), successor_created=False, dispatch_ready_for='Watchdog',
    current_stage='handoff_ready_reference_only', last_stage_evidence=rel(D / 'final_validation_20261029.json'),
    resume_character='Watchdog', resume_stage='Inspect Watchdog anatomy and native four-legged motion; establish its own baseline',
    current_blocked=False, blocked_reason=None, stop_reason=None, stopped_at=None,
    ownership_transfer_note='Await one fresh local Watchdog child. No production/Unity before successful active registration.')
write(H / 'conversation_chain.json', chain)
print(json.dumps({'state': 'handoff_ready', 'next_character': 'Watchdog', 'token': token,
                  'handoff_file': rel(handoff), 'prompt_file': rel(prompt_path), 'dispatch_file': rel(dispatch_path)}, ensure_ascii=False))
