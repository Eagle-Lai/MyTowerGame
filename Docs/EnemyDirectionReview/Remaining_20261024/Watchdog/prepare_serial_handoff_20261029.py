"""Release recorded Watchdog and prepare exactly one fresh local WhiteWolf successor."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re, uuid

D = Path(__file__).resolve().parent
H = D.parent
ROOT = H.parents[2]
N = H / 'WhiteWolf'
OWNER = '01a18379-8413-7bb3-bbc3-e0e5b2544d59'
OLD = 'wasp-to-watchdog-20261029_010456-a6f96d67-324e-4b30-9ff0-555b83354188'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
now = lambda: datetime.now(timezone(timedelta(hours=8)))
rel = lambda p: p.relative_to(ROOT).as_posix()

def write(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def data(value):
    if isinstance(value, str):
        return json.loads(value)
    result = value.get('structuredContent')
    if result is None:
        result = next(json.loads(c['text']) for c in value['content'] if c['type'] == 'text')
    return json.loads(result) if isinstance(result, str) else result

assert os.environ['CODEX_THREAD_ID'] == OWNER
chain = read(H / 'conversation_chain.json')
progress = read(H / 'progress.json')
assert chain['state'] == 'active' and chain['owner_thread_id'] == OWNER
assert chain['dispatch_token'] == OLD and chain['current_character'] == 'Watchdog'
done = next(r for r in progress['items'] if r['name'] == 'Watchdog')
assert progress['completed_count'] == 94 and done['status'] == 'completed_pending_user_art_review'
assert done['final_revision'] == 'art_r04' and done['user_approved'] is False
remaining = [r for r in progress['items'] if r['status'] not in ['completed_pending_user_art_review', 'user_approved']]
recoverable = [r for r in remaining if r['status'] not in ['not_started', 'blocked']]
selected = min(recoverable or [r for r in remaining if r['status'] != 'blocked'], key=lambda r: r['index'])
assert selected['name'] == 'WhiteWolf' and selected['index'] == 106 and selected['status'] == 'not_started'
assert len(remaining) == 14 and next(r for r in remaining if r['name'] == 'PossessedWarg')['status'] == 'blocked'
existing = sorted(p for p in N.rglob('*') if p.is_file())
assert len(existing) == 8 and all(p.is_relative_to(N / 'reference') for p in existing)
t = next(r for r in read(H / 'local_baseline.json')['targets'] if r['name'] == 'WhiteWolf')
six = {p: sha(ROOT / p) for key in ['battle', 'source', 'atlas'] for p in [t[key], t[key] + '.meta']}
assert all(six.values()) and all(sha(N / 'reference' / Path(p).name) == v for p, v in six.items())
final = read(D / 'final_validation_20261029.json')
binding = read(D / 'version_binding_final_20261029.json')
scope = read(D / 'scope_incremental_final_20261029.json')
snapshot = read(D / 'production_before_play_20261029.json')
assert (final['passes'], final['failures'], final['actual_png_frames']) == (168, 0, 597)
assert final['final_revision'] == snapshot['revision'] == 'art_r04'
assert [(r['pass'], r['fail'], r['frames']) for r in final['runtime']] == [(84, 0, 298), (84, 0, 299)]
assert sha(D / 'production_before_play_20261029.json') == final['manifest_sha256']
assert sha(D / 'installed_manifest.json') == snapshot['manifest_sha256']
for filename, key in [('version_binding_final_20261029.json', 'version_binding_sha256'),
                      ('scope_incremental_final_20261029.json', 'incremental_scope_sha256'),
                      ('visual_review_final_20261029/review.json', 'visual_review_sha256'),
                      ('gif_archive_verification_20261029.json', 'gif_archive_sha256')]:
    assert sha(D / filename) == final[key]
assert len(binding['installed_files']) == 22 and binding['installed_files'] == snapshot['final_files']
assert all(sha(ROOT / p) == v for p, v in binding['installed_files'].items())
assert all(sha(ROOT / p) == v for p, v in scope['protected_six'].items() if p != 'Assets/Prefabs/Enemy/Enemy_Watchdog.prefab')
assert (scope['baseline_files'], scope['current_files'], len(scope['changes']), scope['added_count'], scope['deleted_count']) == (5425, 5445, 22, 20, 0)
assert not scope['unexpected_incremental'] and not scope['protected_drift'] and not scope['shared_CSharp_drift']
assert scope['prefab_semantics']['pass'] and final['global_archive_count'] == 1522
assert not any(r.get('character') == 'Watchdog' for r in chain.get('completed_handoffs', []))
probes = sorted(D.glob('unity_release_probe_20261029_response*.json'), key=lambda p: p.stat().st_mtime)
probe_path = probes[-1]
probe = read(probe_path)
state = probe['results'][1]['data']
live = data(probe['results'][3])['data']['result']
imports = data(probe['results'][4])['data']['result']
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
assert imports['spriteMode'] == 'Multiple' and imports['spriteCount'] == 14 and imports['ppu'] == 100
assert imports['alphaIsTransparency'] and not imports['mipmaps']
assert 0 <= (now() - datetime.fromisoformat(probe['observed_at'])).total_seconds() < 180
stamp = now().strftime('%Y%m%d_%H%M%S')
token = 'watchdog-to-whitewolf-' + stamp + '-' + str(uuid.uuid4())
handoff = H / 'conversation_handoffs' / (stamp + '_Watchdog_completed.md')
assessment = N / ('successor_assessment_' + stamp + '.json')
prompt_path = N / ('successor_prompt_' + stamp + '.txt')
release_path = D / 'handoff_release_20261029.json'
dispatch_path = N / 'prepared_dispatch_20261029.json'
assert all(not p.exists() for p in [handoff, assessment, prompt_path, release_path, dispatch_path])
readme = H.parent / 'README.md'
executable = H / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md'
for path, begin, end in [(readme, '<!-- ENEMY_README_LIVE_BEGIN -->', '<!-- ENEMY_README_LIVE_END -->'),
                         (executable, '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->', '<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    assert len(re.findall(re.escape(begin) + r'.*?' + re.escape(end), path.read_text(encoding='utf-8-sig'), re.S)) == 1

write(release_path, {
    'observed_at': probe['observed_at'], 'released_by_thread_id': OWNER, 'current_character': 'Watchdog',
    'next_character': 'WhiteWolf', 'next_dispatch_token': token, 'transport': probe['transport'],
    'project': probe['project'], 'unity_instance': state['unity']['instance_id'], 'editor_state': state,
    'live_probe': live, 'sprite_imports': imports, 'console_errors': [], 'safe_to_handoff': True,
    'external_changes_dirty': False, 'probe_response_file': probe_path.name,
    'probe_response_sha256': sha(probe_path),
    'note': 'Single clean Boot; Play/tests/review/balance/recording/manual/compile/reload/update idle. Existing ForceUpdate refreshed factual state; no plugin source modified.'})
write(assessment, {
    'observed_at': now().isoformat(), 'completed_count': 94, 'authorized_count': 108,
    'selection': 'Resume started nonblocked role first, otherwise lowest incomplete nonblocked index.',
    'remaining': [{k: r[k] for k in ['index', 'name', 'status']} for r in remaining],
    'next_character': 'WhiteWolf', 'next_index': 106, 'status': 'not_started', 'dispatch_token': token,
    'target': t, 'protected_six': six, 'reference_matches_live': True,
    'existing_files': [p.relative_to(N).as_posix() for p in existing],
    'no_generation_staging_install_or_runtime': True,
    'blocked_preserved': [r for r in remaining if r['status'] == 'blocked'],
    'project_id_at_chain': chain['project_id'],
    'project_id_source': 'Historical chain association only; fresh list_projects confirmation required before dispatch.'})

summary = f'''# Watchdog(index 105) 完成与 WhiteWolf(index 106) 唯一串行交接

时间：{now().isoformat()}。父线程 `{OWNER}`，旧 token `{OLD}`。Watchdog 已 record，状态 `completed_pending_user_art_review`，`user_approved=false`。实时进度 **94/108**。

## 最终实现与生产版本

保留原矮壮深橄榄棕犬身份、赭色圆斑、折三角耳、短宽吻、象牙色牙、单一金色尖钉项圈、四足和短楔尾。Up 是无眼无口的纯后脑，三个表情共用同图，后足方向与足跟正确；Down 有正常、张口愤怒、闭眼死亡三表情。源侧面及镜像保留，轴向体形比侧面窄。头身、肩髋、四足与尾根连接，不增加原资源没有的器官。

上下成功 raw 保留复用，没有新的付费返修或未定生成请求。局部修订 r02 露出远侧足并把 Up 尾根藏入躯干；r03 埋入 Down 髋部根帽并把正面头置向胸部；最终 art_r04 清除八个溢色像素，14 片均无封闭 alpha 洞。没有生产 C# 修改；四个自有方向动画及 Controller 由既有单角色流程安装，保留原侧面 float/PPtr、事件、时长、loop 与战斗/对象池契约。

最终 revision **art_r04**。两轮 Play 前的完整22路径快照：`Watchdog/production_before_play_20261029.json`，文件SHA `{sha(D / 'production_before_play_20261029.json')}`；其中 installed_manifest SHA `{snapshot['manifest_sha256']}`。battle SHA `{binding['installed_files']['Assets/Prefabs/Enemy/Enemy_Watchdog.prefab']}`。22路径自两轮前至最终验证均未变。不要删除 installed_manifest 或重跑 stage/pack/Build/install 覆盖最终资源。暂存 atlas/sprite/layout 与生产 SHA 相同；Unity实际导入 Multiple、PPU100、alphaIsTransparency=true、mipmaps=false、14 sprites，矩形/pivot 已核对。

## 两轮真实运行与实际视觉检查

runtime_r01：84 PASS/0 FAIL，298张真实PNG，记录SHA `{final['runtime'][0]['records_sha256']}`。
runtime_updeath_r01：84 PASS/0 FAIL，299张真实PNG，记录SHA `{final['runtime'][1]['records_sha256']}`。第二轮指定Up死亡。共168/0、597张真实PNG；art_r04在两轮前完成，两轮均恢复非Play、clean Boot。本交接阶段未重复Play。

实际审阅离线rig和透明分件、两轮四方向图、runtime strip、10张时序/步态/愤怒细节板（256采样位、229张不同真实PNG）、9张原尺寸PNG，及12个最终GIF各5个编码帧共60帧；补看两轮Up/Down各1张未裁切编码整帧共4张。观察到足部错相、尾根相连、Up无脸、Down三表情、攻击前压回收、全身受击白闪恢复、Down/Up死亡侧倾缩小淡出、自动回收和同实例复用、暂停冻结/恢复、1×/2×/3×相位推进。未见断颈、悬足、重复项圈或地面阴影。

初版GIF抽样预览裁切顶部40%造成耳尖假性截断；r02裁切改为30%，并用原尺寸PNG和未裁切GIF编码帧确认耳尖完整、血条有间距。原媒体没有改写，旧预览保留。GIF是编码帧抽样，没有实时播放或逐GIF全帧审核；全部597张真实PNG保留并哈希。美术批准仍由用户决定。

record已经执行；AllGIF总计1522，Watchdog12项均当前审核版本，源与归档SHA一致。核心证据：
- Watchdog/final_validation_20261029.json
- Watchdog/version_binding_final_20261029.json
- Watchdog/scope_incremental_final_20261029.json
- Watchdog/visual_review_final_20261029/review.json
- Watchdog/gif_archive_verification_20261029.json
- Watchdog/runtime_summary.json、record_note_utf8.txt

## 范围审计与Unity释放

当前磁盘安装前基线5425→5445文件，Assets/Packages/ProjectSettings/Luban路径并集22变化、20新增、0删除。仅本角色battle/Directions含meta；未修改ReporterEditor产生的Play build_info时间戳单列。incremental unexpected0、本角色原组件语义PASS、其余5保护/共享C#/其他角色/配置表/源图/源prefab无漂移。历史全局291 unexpected和6个其他角色语义失败没有本轮重审，不能称全局PASS。

正确Unity为E:/MyTowerGame、2022.3.62f3c1、HTTP8088。通过Client.identity动态读custom-tools/instances、选现场完整MyTowerGame ID、核对project/info。释放快照时间{probe['observed_at']}；单一clean Boot、非Play，tests/review/balance/recording/manual/compile/reload/update全部idle，failed=false、error0、ready=true、external_changes_dirty=false。现有ForceUpdate刷新真实空闲快照；未修改插件、未清日志、未使用桌面控制。释放证据 `{rel(release_path)}`，probe响应SHA已绑定。

## 下一唯一WhiteWolf

剩余14项：PossessedWarg旧blocked/uncertain保留，另13项not_started；没有已开始可恢复的非blocked角色，按index选择WhiteWolf106。当前只有8个reference文件，无anatomy/generation/staged/install/runtime，六保护与reference一致，详见 `{rel(assessment)}`。

源prefab `{t['source']}`；atlas `{t['atlas']}`；battle `{t['battle']}`；共用controller `{t['controller']}`。下一聊天自行审完整源图、层级、四足/尾根/表情、原float/PPtr/事件/时长/loop及战斗/复用生命周期；按WhiteWolf自身身份设计正背，不套Watchdog、Warg或其他犬科的具体造型。开工以当前磁盘含用户改动建立增量基线，不用Git HEAD。本聊天未修改WhiteWolf生产。

新token `{token}`。完整执行入口 `{rel(prompt_path)}` 与NEXT_ENEMY_TASK。先handoff_ready；现场list_projects确认后只创建一个fresh local后继，不fork、不子代理、不计时器、不传模型/推理覆盖。明确创建成功并登记active作为父最后一次工作区写入，此后只读。Watchdog目录已有来自Wasp的incoming调度文件保持原样；本次outgoing assessment/prompt/dispatch/creation放WhiteWolf目录。
'''
handoff.write_text(summary, encoding='utf-8')

prompt = f'''在 E:/MyTowerGame 继续敌人四方向串行续作。本聊天唯一角色 WhiteWolf(index 106)，是用户已授权循环中的唯一全新 local 后继。

唯一 dispatch token：{token}
父线程：{OWNER}

开工完整读取当前磁盘：
1. E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt。
2. E:/MyTowerGame/Docs/EnemyDirectionReview/README.md、PREFAB_CHANGES_SUMMARY_20261026.md。
3. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md。
4. 同目录CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json。
5. 同目录standing_network_recovery_authorization_20261028.json、TreasureChest/standing_recovery_application_20261028.json，核对原授权证据，不改写旧uncertain/收费结果，不无限重试。
6. E:/MyTowerGame/{rel(handoff)}。
7. E:/MyTowerGame/{rel(assessment)}。
8. WhiteWolf/reference/source_structure.json及完整源参考；相关流水线脚本、共享实现的直接依赖/调用/生命周期。

只有chain.state=active、owner_thread_id为本新聊天、current_character=WhiteWolf、dispatch_token与上方一致，才能操作Unity、生产或付费生成。父先handoff_ready，此时只读等待登记，不超时抢锁。父创建成功登记后停止全部工作区写入。开工检查新出现的请求/安装/运行文件，恢复已有阶段，避免重复prepare、生成或安装。不得在handoff_ready期间创建其他任务或修改链。

当前94/108。Watchdog105已record，最终art_r04，completed_pending_user_art_review、user_approved=false。WhiteWolf106当前not_started，仅reference8文件，无anatomy/generation/raw/staged/install/runtime；本目录assessment/prompt/dispatch/creation是调度文档。剩余14项含PossessedWarg旧blocked及结果不明Down付费请求，另13项not_started。PossessedWarg保留，不自动重发、不伪称完成。

WhiteWolf源路径：
- {t['battle']}
- {t['source']}
- {t['atlas']}
- Controller: {t['controller']}
reference六保护已匹配，开工仍现场核对。读完整atlas、prefab层级/绑定、controller依赖、原float/PPtr/事件/时长/loop及战斗、回收、同实例复用。自行审WhiteWolf原身份、毛色/轮廓/表情与四足尾根，制定正背解剖；不套Watchdog、Warg或其他犬科具体造型。改动前以当前磁盘含用户改动建立本角色Assets/Packages/ProjectSettings/Luban全路径SHA增量基线及六保护，不以Git HEAD为基线，不重置历史指纹。

逐阶段执行原prompt：审原图/解剖→按需逐方向AIHub并实看raw→透明分件/切片/pivot/PPU/layout和离线proof审阅→六保护与Unity空闲复核→仅WhiteWolf安装Builder/Verify→两轮真实Unity Play各84项→分批实际看PNG/时序板/GIF并准确记抽样→最终生产与运行版本哈希绑定→UTF8 note/record→GIF归档SHA→路径并集增量及原组件语义审计。程序PASS不能代替美术检查；视觉失败须修复重测、保留旧revision。成功raw优先复用；结果不明先查进程/落盘/返回，不盲重发。不要无条件整段连跑，不删除安装清单绕过防重。

使用imagegen技能和既有AIHub入口https://aihub.dog/v1，gpt-image-2、medium、1536x1024、n=1，复用generate_character.ps1/generate.mjs；密钥运行时读取，仅发aihub.dog，不随跨域重定向，结束清理，不输出密钥或base64。遵循现有有界网络恢复授权、新intent/revision及防重护栏。Usage本地估算不当已确认账单，真实格式/尺寸以返回为准。不要重复生成已有、仍在执行或结果不明的请求。

保护原atlas、源prefab、GUID/root、HP/碰撞/锚点/移动战斗参数及原侧面动画曲线/PPtr/事件/时长/loop。Up必须纯后脑、正确后足方向；肩髋/颈/尾相连，不凭空增加原资源没有的部件。保留攻击、受击/致死白闪、全身死亡缩小淡出、自动回收、同实例复用、暂停和1×2×3×；四向及状态均无角色地面阴影。使用现有方向系统，不增逐帧材料/层级查找或另一套方向系统。不改其他角色或共享C#；不改配置表、Assets/ConfigJson、Assets/Gen、声音。禁止Git pull/reset/clean/commit、构建部署、fork、子代理、并行角色、计时器、模型/推理覆盖、长期memory更新。

正确Unity端点http://127.0.0.1:8088/mcp，版本2022.3.62f3c1。复用Remaining_20261024/mcp_call.py的Client.identity：动态读custom-tools/instances，明确set现场MyTowerGame完整ID，再project/info核E:/MyTowerGame及版本。8082是其他工程，8080是CatchFish；根AGENTS中的FreedomTower/D盘/8082为历史错配，本任务覆盖。重连/域重载后重新核对，不硬编码旧实例ID。MCP离线按工程规则自主恢复；失败报告实际环节及具体开启步骤，不能跳过或假称验证完成。默认使用Unity MCP；电脑/桌面控制须先弹对话确认，本prompt不授权桌面。只停本任务授权Play，不强停外来任务。

本任务已授权两轮真实Play测试，无需重复询问。运行时排查先读本工程错误现场、再看状态。最终Unity须单一clean Boot、非Play，tests/review/balance/recording/manual/compile/reload/update全部idle，failed=false、error0、ready=true，不清日志。若以后获得明确C#改动授权，必须正确工程refresh/compile/state/error闭环，编译期间不继续改代码。空闲缓存stale须取新事实，不能用端口监听或旧resource冒充成功。

前任Watchdog最终证据：Watchdog/final_validation_20261029.json及version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_final_20261029/review.json、gif_archive_verification_20261029.json。最终art_r04、14透明切片，深橄榄棕斑犬/折耳/单一尖钉项圈/四足短尾；Up无脸、Down三表情，r02露远足藏尾根、r03埋髋帽调头胸、art_r04去八溢色像素。完整22路径在production_before_play_20261029.json，installed_manifest SHA {snapshot['manifest_sha256']}。runtime_r01为298帧、runtime_updeath_r01为299帧，各84/0，共168/0、597真实PNG。实看离线rig/分件、两轮四向/strip、10板256采样位/229不同PNG、9原PNG、12GIF各5编码帧及4未裁切编码整帧；未实时播放或逐GIF全帧审核。初版GIF预览顶部40%裁切造成耳尖假性截断，r02降到30%并用整帧确认完整、血条有间距，原媒体未改写。AllGIF1522，Watchdog12当前版、源/归档SHA一致。5425→5445路径并集22变化20新增、unexpected0、本角色语义/其余5保护/共享C#无漂移，Reporter时间戳单列。历史global291 unexpected/6其他角色语义失败未重审，不称全局PASS。不要重跑前任stage/pack/Build/install或finalize audit/seal，勿删installed_manifest或改前任生产。

图片原件和完整帧留盘，每次1～2张清晰预览及必要细节，按IMAGE_RELAY_RECOVERY限制历史图片载荷；不把全部角色/GIF/历史原帧一次内嵌。无法播放则按帧序实看并准确记录限制，未看不能写通过；中文文件UTF8。最终状态只能completed_pending_user_art_review、user_approved=false，不替用户批准。

完成WhiteWolf全流程或记录真实阻断并释放Unity后，重新评估实时items：优先恢复已开始可恢复项，否则最低index非blocked；不盲用progress.current。完整落盘交接，更新README实时块、原执行prompt实时块、NEXT/progress；保留历史和阻断。用户已授权“一个完成→总结/更新prompt→唯一fresh local后继”循环，不逐角色再问。chain先handoff_ready，现场list_projects确认E:/MyTowerGame，再create_thread唯一全新local、不传model/thinking、不fork；新聊天等active。create明确成功保存真实响应，登记新owner/token active作为父最后一次工作区写入，此后只读；一次有界wait_threads并报告真实created-thread。创建结果不明先查列表，不重复创建；失败保留完整可执行交接并如实报告。循环至108全部有效完成或仅余真实阻断，不绕过阻断付费试探。
'''
prompt_path.write_text(prompt, encoding='utf-8')
(H / 'NEXT_ENEMY_TASK.md').write_text('# 下一唯一角色 WhiteWolf(index 106)\n\n' + prompt, encoding='utf-8')
live_text = (
    f"{now().strftime('%Y-%m-%d')} Watchdog105已record，94/108，completed_pending_user_art_review、user_approved=false。"
    "最终art_r04，14透明切片；橄榄棕斑犬、折耳、单一尖钉项圈、四足短尾；Up无脸、Down三表情。"
    "r02露远足藏尾根、r03埋髋帽调头胸、r04去8溢色像素；原侧面和战斗/复用契约保留，无生产C#修改。"
    "两轮298+299共597真实PNG、168PASS/0FAIL；实际看离线rig/分件、两轮四向/strip、10板256采样位/229不同PNG、9原PNG、12GIF各5编码帧及4未裁切编码整帧；未实时播放或逐GIF全帧。"
    "初版GIF预览顶部40%裁切造成耳尖假性截断；r02降到30%并用完整帧确认完整和HP间距，原媒体未改。"
    "AllGIF1522，Watchdog12均当前版且源/归档SHA一致。5425→5445路径并集22变化20新增、unexpected0，本角色语义通过，其余5保护/共享C#无漂移，Reporter时间戳单列。"
    "旧global291unexpected/6其他角色语义失败为历史，未重审或称全局PASS。Unity8088正确身份、单一clean Boot/非Play/全空闲/failed=false/error0/ready=true/external_changes_dirty=false。"
    f"最终Watchdog/final_validation_20261029.json及绑定/范围/视觉/归档；完整22路径在production_before_play_20261029.json。交接{rel(handoff)}。"
    f"下一唯一WhiteWolf106 not_started，仅reference8文件，token={token}。剩余14项含PossessedWarg旧blocked/uncertain，另13项not_started。")
for path, begin, end in [(readme, '<!-- ENEMY_README_LIVE_BEGIN -->', '<!-- ENEMY_README_LIVE_END -->'),
                         (executable, '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->', '<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    content = path.read_text(encoding='utf-8-sig')
    content = re.sub(re.escape(begin) + r'.*?' + re.escape(end), lambda _: begin + '\n' + live_text + '\n' + end, content, flags=re.S)
    if path == readme:
        content, count = re.subn(r'\d{4}-\d{2}-\d{2} 本轮当前清单为 \d+ 个文件',
                                now().strftime('%Y-%m-%d') + ' 本轮当前清单为 1522 个文件', content)
        assert count == 1
    path.write_text(content, encoding='utf-8')
done['handoff_file'] = handoff.relative_to(H).as_posix()
progress.update(current='WhiteWolf', updated_at=now().isoformat())
write(H / 'progress.json', progress)
dispatch = {
    'prepared_at': now().isoformat(), 'created': False, 'parent_thread_id': OWNER,
    'character': 'WhiteWolf', 'character_index': 106, 'dispatch_token': token,
    'project_root': 'E:/MyTowerGame', 'project_id': None, 'project_id_at_chain': chain['project_id'],
    'project_live_confirmed': False, 'handoff_file': rel(handoff), 'handoff_sha256': sha(handoff),
    'assessment_file': rel(assessment), 'assessment_sha256': sha(assessment),
    'unity_release_file': rel(release_path), 'unity_release_sha256': sha(release_path),
    'prompt_file': rel(prompt_path), 'prompt_sha256': sha(prompt_path),
    'next_task_file': rel(H / 'NEXT_ENEMY_TASK.md'), 'next_task_sha256': sha(H / 'NEXT_ENEMY_TASK.md'),
    'progress_sha256': sha(H / 'progress.json'),
    'response_file': rel(N / 'successor_creation_response_20261029.json'),
    'project_association_confirmed': False}
write(dispatch_path, dispatch)
chain.setdefault('completed_handoffs', []).append({
    'character': 'Watchdog', 'status': 'completed_pending_user_art_review',
    'current_stage': 'recorded_pending_user_art_review', 'closed_at': now().isoformat(),
    'owner_thread_id': OWNER, 'dispatch_token': OLD, 'handoff_file': rel(handoff),
    'final_evidence': rel(D / 'final_validation_20261029.json')})
chain.update(
    state='handoff_ready', parent_thread_id=OWNER, owner_thread_id=OWNER, owner_host_id='local',
    current_character='WhiteWolf', dispatch_token=token, character_status_at_handoff='not_started',
    completed_count_snapshot=94, previous_handoff_file=chain.get('last_handoff_file'),
    last_handoff_file=rel(handoff), handoff_sha256=sha(handoff), successor_assessment=rel(assessment),
    prepared_dispatch_file=rel(dispatch_path), unity_release_file=rel(release_path),
    progress_sha256_at_handoff=sha(H / 'progress.json'), handoff_ready_at=now().isoformat(),
    updated_at=now().isoformat(), successor_created=False, dispatch_ready_for='WhiteWolf',
    current_stage='handoff_ready_reference_only', last_stage_evidence=rel(D / 'final_validation_20261029.json'),
    resume_character='WhiteWolf', resume_stage='Inspect WhiteWolf anatomy and native four-legged motion; establish its own baseline',
    current_blocked=False, blocked_reason=None, stop_reason=None, stopped_at=None,
    ownership_transfer_note='Await one fresh local WhiteWolf child. No production/Unity before successful active registration.')
write(H / 'conversation_chain.json', chain)
print(json.dumps({'state': 'handoff_ready', 'next_character': 'WhiteWolf', 'token': token,
                  'handoff_file': rel(handoff), 'prompt_file': rel(prompt_path), 'dispatch_file': rel(dispatch_path)}, ensure_ascii=False))
