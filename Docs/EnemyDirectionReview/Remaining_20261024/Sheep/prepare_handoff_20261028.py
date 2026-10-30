"""Assess the live queue and prepare one fresh local successor after releasing Unity."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib, json, os, re, sys, time, uuid

D = Path(__file__).resolve().parent
H = D.parent
R = H.parents[2]
sys.path.insert(0, str(H))
from mcp_call import Client

def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def now(): return datetime.now(timezone(timedelta(hours=8))).isoformat()
def unwrap(v): return v.get('structuredContent') or json.loads(v['content'][0]['text'])

chain = read(H / 'conversation_chain.json')
parent = os.environ['CODEX_THREAD_ID']
assert chain['state'] == 'active' and chain['owner_thread_id'] == parent and chain['current_character'] == 'Sheep'
assert chain['dispatch_token'] == 'scarabmounted-to-sheep-fd7d7a5afb264ca7a1691363ab276f5f'
progress = read(H / 'progress.json')
assert progress['completed_count'] == 84
sheep = next(x for x in progress['items'] if x['name'] == 'Sheep')
assert sheep['status'] == 'completed_pending_user_art_review' and sheep['user_approved'] is False
binding = read(D / 'version_binding_final_20261028.json')
assert all(sha(D / p) == s for p, s in binding['files'].items())
assert all(sha(R / p) == s for p, s in binding['installed_files'].items())

unfinished = sorted((x for x in progress['items'] if x['status'] != 'completed_pending_user_art_review'), key=lambda x: x['index'])
assessment = []
for item in unfinished:
    folder = H / item['name']
    files = sorted(p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file())
    assessment.append(dict(index=item['index'], name=item['name'], status=item['status'], files=files, checkpoints=[p for p in ['anatomy_plan.json', 'installed_manifest.json', 'runtime_summary.json'] if (folder / p).is_file()], raw=[p for p in files if p.endswith('/raw.png')], runtime_directories=[p.name for p in folder.glob('runtime*') if p.is_dir()], blocked_reason=item.get('blocked_reason')))
blocked = [x for x in assessment if x['status'] == 'blocked']
assert len(blocked) == 1 and blocked[0]['name'] == 'PossessedWarg'
available = [x for x in assessment if x['status'] != 'blocked']
assert available and all(x['status'] == 'not_started' and not x['checkpoints'] and not x['raw'] and not x['runtime_directories'] and all(p.startswith('reference/') for p in x['files']) for x in available)
successor = available[0]
assert successor['name'] == 'SlugQueen' and successor['index'] == 96
target = next(x for x in read(H / 'local_baseline.json')['targets'] if x['name'] == 'SlugQueen')
six_paths = [target['battle'], target['battle'] + '.meta', target['source'], target['source'] + '.meta', target['atlas'], target['atlas'] + '.meta']
original_baseline = read(H / 'production_fingerprints_before.json')
six = {p: sha(R / p) for p in six_paths}
assert all(six[p] == original_baseline[p] for p in six_paths)
assert all(sha(H / 'SlugQueen/reference' / Path(p).name) == digest for p, digest in six.items())

client = Client()
project = client.identity()
cache_refresh = None
for attempt in range(4):
    state = client.resource('mcpforunity://editor/state')
    s = state['data']
    if not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']:
        break
    if attempt == 0 and s.get('advice', {}).get('blocking_reasons') == ['stale_status']:
        cache_refresh = unwrap(client.tool('execute_code', dict(action='execute', code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"Sheep_handoff_live_state_read"});return true;')))
        assert cache_refresh['success'] and cache_refresh['data']['result'] is True
    time.sleep(1)
else:
    raise RuntimeError('Unity not ready for handoff')
errors = unwrap(client.tool('read_console', dict(action='get', types=['error'], count='50', format='json')))
probe = unwrap(client.tool('execute_code', dict(action='execute', code='return new {playing=UnityEditor.EditorApplication.isPlayingOrWillChangePlaymode,compiling=UnityEditor.EditorApplication.isCompiling,failed=UnityEditor.EditorUtility.scriptCompilationFailed,updating=UnityEditor.EditorApplication.isUpdating,balance=FTProject.EditorTools.BalancePlayModeVerifier.Running,recording=FTProject.EditorTools.BalanceVideoRecorder.Running,review=FTProject.EditorTools.EnemyDirectionBatchReview.Running,manual=FTProject.GameClock.IsManualSimulation,dirty=System.Linq.Enumerable.Any(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty),scene=UnityEngine.SceneManagement.SceneManager.GetActiveScene().path};')))
assert probe['success'] and errors['success'] and errors['data'] == []
released = probe['data']['result']
assert released['scene'] == 'Assets/Scenes/Boot.unity' and not any(v for k, v in released.items() if k != 'scene')

stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
token = 'sheep-to-slugqueen-' + uuid.uuid4().hex
handoff = H / 'conversation_handoffs' / (stamp + '_Sheep_completed.md')
assessment_path = D / ('successor_assessment_' + stamp + '.json')
release_path = D / ('handoff_release_' + stamp + '.json')
dispatch_path = D / ('successor_dispatch_' + stamp + '.json')
assert not any(p.exists() for p in [handoff, assessment_path, release_path, dispatch_path])
rel = lambda p: p.relative_to(R).as_posix()
runtime = read(D / 'runtime_summary.json')
gifs = read(D / 'gif_archive_verification_20261028.json')
scope = read(D / 'scope_incremental_final_20261028.json')

live = ('2026-10-28 Sheep95完成，84/108，待用户美术审核user_approved=false。Up/Down初图各一次HTTP200；Up本地revision02闭合颈环并换完整后蹄，最终布局03。只给自有Walk新增Head位置三轴常量，保留125原绑定/事件/时序；现场复用y从旧0.4恢复0.7。最终r02两轮168/0、676真实帧；实际审四方向/strip、10板(256采样位/227不同帧)及2张原尺寸PNG，未播放GIF或逐帧全审。AllGIF1330，Sheep36含12当前版。5218基线并集22变化20新增，增量unexpected0，安装/暂存/原Sprite/六保护/语义通过；全局历史291unexpected及6其他角色语义失败保留新增0。Unity安全释放Boot非Play、全场景非dirty、空闲、编译失败false、error0。下一唯一SlugQueen96，仅reference/not_started。PossessedWarg旧Down仍uncertain不重发。完整交接：' + rel(handoff) + '。所有权以实时chain为准，桌面控制仍须先对话确认。')
marked = [(H.parent / 'README.md', 'ENEMY_README_LIVE'), (H / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md', 'ENEMY_SERIAL_LIVE_STATE')]
updates = {}
for path, marker in marked:
    text = path.read_text(encoding='utf-8')
    pattern = r'<!-- ' + marker + r'_BEGIN -->.*?<!-- ' + marker + r'_END -->'
    assert len(re.findall(pattern, text, re.S)) == 1
    updates[path] = re.sub(pattern, '<!-- ' + marker + '_BEGIN -->\n' + live + '\n<!-- ' + marker + '_END -->', text, flags=re.S)

handoff_text = f'''# Sheep(index95) 完成与下一唯一角色交接

时间：{now()}。工程E:/MyTowerGame，Unity2022.3.62f3c1，unityMCP/HTTP Local8082。
父聊天：{parent}。本角色旧令牌：{chain['dispatch_token']}。
状态：completed_pending_user_art_review，user_approved=false。实时进度84/108；24项未完成，包括PossessedWarg阻断1项与未开始23项。

## 实际完成

仅修改Assets/Prefabs/Enemy/Enemy_Sheep.prefab和Assets/_UIAssets/Monsters/Cattle/Sheep/Directions资源。没有共享C#、源图/源prefab、共享Goat动画、配置表、其他角色、声音或Git同步/提交/构建部署改动。
Up/Down初次正式请求各一次HTTP200，原件为generation/Up/raw.png（1384694 bytes）及generation/Down/raw.png（1434713 bytes）。未做付费返修或网络重试。最终Up选local_raster_revision_02/Up_sheet.png，局部闭合空心颈环，并从同图取完整后蹄替代前向蹄；Down选原始返回图。local_raster_revision_01有颈环残边/拼接断点而被否决。默认与第二次布局因腿过长、根露出/断开被否决；最终layout revision03四短蹄根藏入羊毛。所有旧图与布局保留。
保留奶油云状羊毛、赭斑、淡金脸与垂耳；源六个美术部件，无角无独立尾巴，不添加。两Tail切片全透明仅兼容，Up/Down Tail节点均移除。14 RGBA切片无opaque magenta。Up后脑无眼口；Down正常/愤怒/死亡头可辨。

## 原动画复用问题与定点修复

Goat源Death把Body/Head.localPosition.y从0.7降到0.4，Walk/Ready/Attack没有位置复位。runtime_head_probe_r03现场读取确认初始0.7、死亡复用后0.4；runtime_head_probe_r02采样失败为空，虽有84检查/帧图，不能作姿态证据。两者均留存并归为历史。
head_reuse_repair_r01仅给Sheep自己的Walk_Directions.anim新增Body/Head位置x/y/z三条常量[-1,0.7,0]。原125条float绑定、PPtr、事件、时长/loop全部保留；不改Goat源或共享脚本。最终runtime_r02的现场同实例读数初始/复用后均0.7。repair_side_reuse探针确认源Death没有Body旋转，不套前角色复位。原8个存活SpriteRenderer PPtr与非美术语义保留。
不要全Build覆盖本角色Walk修复。最终installed_manifest.json与preplay_version_binding_r02_20261028.json绑定一致，Verify PASS。

## 最终运行与实际视觉审阅

runtime_r02：84 PASS/0 FAIL，335帧；runtime_updeath_r02：84 PASS/0 FAIL，341帧；共168/0、676张真实Unity帧。旧r01（682帧）和两次探针（342/336帧）完整保留，不当最终版本。
实际查看最终runtime_r02/four_directions.png、runtime_visual_strip.png、visual_review_final_r02_20261028中的10张板（256采样位、227不同实际帧），另查看runtime_r02/frames/DeathAutoRecycle_00155.png及ContinuousTurns_00320.png原尺寸。涵盖四方向、连续转向、步态、攻击愤怒、受击白闪/恢复、双向死亡淡出/回收、复用、暂停/恢复和1x/2x/3x。抽样未见颈环空洞、断根、底色污染或死亡复用错位。Down死亡空白眼及吐舌实际可见，原尺寸复用后Left头身位置恢复。
审阅是PNG时序抽样；未实时播放GIF全片、未逐张审完676帧。正背面的轴向俯视比例与远侧腿被毛遮挡程度仍待用户美术确认。不得写user_approved=true。
AllGIF总数{gifs['total']}；Sheep共{gifs['character_count']}项，其中{gifs['current_count']}项当前审核版、其余历史。所有来源及归档SHA256一致，包含两轮旧版、两次诊断和两轮最终版。打开Docs/EnemyDirectionReview/AllGIF/index.html筛选Sheep与当前审核版本。

## 范围与指纹

5218项生产基线按前后路径并集核对：22变化，20新增；仅Sheep battle和Directions，另Reporter原InitializeOnLoad自动更新时间戳单列。增量unexpected=[]，安装/暂存无drift，六保护除授权battle外保持，原Sprite合同/接收器/非美术语义通过。
全局历史291 unexpected及MeatBug/Monkey/MosquitoParasite/Pig/Piggy/Porky六个既有语义失败保留，新增0；不是全局PASS。
最终全量帧哈希、选图/意图/派生/布局/安装/动画修复/现场读数/媒体/审阅绑定：Sheep/version_binding_final_20261028.json。范围：Sheep/scope_incremental_final_20261028.json与scope_Sheep_final_20261028.json；最终Unity：Sheep/final_validation_20261028.json；归档：Sheep/gif_archive_verification_20261028.json；真实UTF8备注：Sheep/record_note_utf8.txt。

## Unity已释放

按custom-tools/instances动态选MyTowerGame完整ID并核对project/info与版本。最终错误0、scriptCompilationFailed=false；Boot非Play、所有场景非dirty、无compiling/reload/updating、ready_for_tools=true，无review/balance/录像/manual任务。交接前又读取一次现场，详见{rel(release_path)}。仅stale_status时反射ForceUpdate刷新插件真实缓存，不改flags。未用桌面操作。

## 下一唯一角色与调度

现场重新评估所有未完成项，证据{rel(assessment_path)}。PossessedWarg旧Down结果仍不明，不重发。其余23项均not_started、只有reference、没有生成/staging/install/runtime；因此按index选择SlugQueen96。
源：{target['source']}；图集：{target['atlas']}；battle：{target['battle']}；controller：{target['controller']}。参考8文件及六项保护指纹与原基线一致。解剖、软体移动、头身尾/触角等必须以实际源图/完整prefab与动画为准，不套Sheep四足或前角色解剖。
新令牌：{token}。接棒只在chain.state=active、owner_thread_id等于自己、current_character=SlugQueen且令牌严格匹配后开始；handoff_ready只读等待，不靠超时接管。
沿用默认Curl的generate_character.ps1和AIHub既有授权/安全参数；先正式生成一方向并实际审图，再另一方向。正常新角色不用Mounted专属AuthorizedResume。若同类TLS故障只按standing_network_recovery_authorization_20261028.json限次追加revision，保留uncertain，不挪用旧专属授权、不无限重试。桌面控制必须先弹对话确认，默认Unity MCP。
继续原prompt两轮真实Play/审图/record/归档，完成一个角色后按协议创建唯一全新本地后继，不fork/子代理/并行/计时器/模型覆盖。创建明确成功后父线程登记一次所有权并停止全部工作区写入。
'''
next_text = f'''# 下一唯一角色 SlugQueen(index96)

在E:/MyTowerGame继续敌人四方向续作。父聊天{parent}已完成Sheep，84/108，待用户美术审核。唯一令牌`{token}`。

## 开工与所有权

必读根AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、实时conversation_chain.json/progress.json、{rel(handoff)}、{rel(assessment_path)}、standing_network_recovery_authorization_20261028.json。根AGENTS旧FreedomTower_1/D盘差异已记录，保持E:/MyTowerGame，不改规则、不转工程。
只有chain.state=active、owner为本新聊天、dispatch_token严格匹配且current_character=SlugQueen才可操作Unity和生产。handoff_ready只读等待登记，不靠超时抢锁，不fork/子代理/并行角色，不改模型，不计时器。

## SlugQueen现场与执行

SlugQueen为not_started，只有reference的Enemy_SlugQueen.prefab/SlugQueen.prefab/SlugQueen.png及其meta、source_structure.json、source_prefab_offline.png；没有anatomy、generation请求/raw、staging/install/runtime。已现场确认六项原指纹匹配。先读工作区git差异、实际源图/完整prefab、调用/动画生命周期，建立自己的增量基线与必要prepare；不覆盖参考或用户改动。
实际源为{target['source']}，battle为{target['battle']}，图集为{target['atlas']}，源Controller为{target['controller']}。所有部件、朝向与软体步态以现场为准，不套Sheep四足解剖。检查源动画是否缺死亡复用reset，若需要只补本角色自有副本，保留原曲线/事件/时序，不改共享源或C#。

generate_character.ps1默认Transport=Curl，Sheep两方向均一次HTTP200。密钥runtime-only、curl config stdin，HTTPS证书检查、无redirect/retry；原endpoint=gpt-image-2 images/edits、medium、1536x1024、n1及owner/指纹/输出存在保护保持。先一方向正式生成并实际审图，再另一方向；成功原图复用，有在途/uncertain先调查。正常新角色不用Mounted专属AuthorizedResume。standing授权覆盖同类TLS故障，每方向最多2次追加新revision，保留原uncertain和计数；鉴权/余额/上限耗尽不盲重试，不用其他角色付费探针。无需逐角色重复确认，但电脑桌面控制仍须先弹对话确认。

按原prompt完成源与生成原图实际审阅、透明去底色/切片/pivot/连接与朝向、角色动画，单角色安装Verify。检查Builder预览是否改变原Sprite/接收器绑定。两轮真实Play各84检查，分次实际审四方向/时序/步态/愤怒/死亡复用画面；PNG抽样与GIF播放/逐帧审阅要如实区分。发现缺陷保留旧revision后修复并重跑，绑定最终选图/安装/运行/全部帧哈希，前后文件并集范围审计、UTF8真实备注record与AllGIF归档。只能completed_pending_user_art_review、user_approved=false，不能以技术PASS代替用户美术批准。
已安装清单不删后重装；每次1-2图，raw/失败请求/完整帧全留。六保护除本角色battle授权外不动；全球历史291unexpected及6其他角色语义失败保持，只以本轮新增0判断，不能称全局PASS。禁止配置表、Assets/ConfigJson/Gen、声音、其他角色及共享C#改动，不Git pull/reset/clean/checkout/commit/push，不构建部署。

## Unity与续接

Unity2022.3.62f3c1 / unityMCP / HTTP Local8082。每次动态读custom-tools/instances、set现场MyTowerGame完整ID、核对project/info=E:/MyTowerGame及ProjectVersion，可复用mcp_call.py。先读error/状态，全场景dirty、Play/编译/review/录像/manual占用检查；不占8080，不操作其他工程。只有stale_status时可按Sheep/prepare_handoff_20261028.py的短反射ForceUpdate读真实snapshot，不改flags或插件。任务已授权两轮Play，不强停他人任务、不覆盖未保存场景。C#若确需改动必须完整MCP刷新编译验证。
Sheep已安全释放Boot非Play、全场景非dirty、空闲、编译失败false、error0，证据{rel(release_path)}。Sheep的Walk自有Head三轴复位已绑定，别全Build覆盖；所有旧图/初轮/诊断均为历史，最终r02才是当前版，不修改其Assets。
PossessedWarg旧Down仍uncertain不重发；历史SabretoothTiger/Scarab/Mounted失败与uncertain全部保留，不移用专属授权。完成或真实阻断后重读实时队列、写完整新交接，更新README/LIVE/NEXT/progress并安全交回Unity；按CONTINUATION_PROTOCOL动态list_projects并创建唯一全新本地后继。create明确成功后登记新thread/host/token，即停止所有工作区/chain写入，仅一次有界wait确认。只剩真实阻断才停止，不能空转并发。
'''

write(assessment_path, dict(observed_at=now(), progress_completed_count=84, unfinished=assessment, blocked_preserved=blocked, available_count=len(available), chosen=successor, target=target, chosen_protected_six=six, protected_drift=[], reason='No recoverable nonblocked stage exists; choose lowest index not_started reference-only character. PossessedWarg uncertain Down remains blocked without resend.'))
write(release_path, dict(observed_at=now(), project=project, state=state, cache_refresh=cache_refresh, errors=errors, probe=probe, protocol_history=client.history, note='No Play exit forced; previous own tester already returned. No C# changes, no new compiler request.'))
handoff.write_text(handoff_text, encoding='utf-8')
for path, text in updates.items():
    path.write_text(text, encoding='utf-8')
readme = H.parent / 'README.md'
readme.write_text(readme.read_text(encoding='utf-8') + '\n\n' + live + '\n', encoding='utf-8')
(H / 'NEXT_ENEMY_TASK.md').write_text(next_text, encoding='utf-8')
progress.update(current='SlugQueen', updated_at=now())
write(H / 'progress.json', progress)
prompt = f'''在 E:/MyTowerGame 接棒敌人四方向串行任务，只处理 SlugQueen(index96)。父聊天已完成 Sheep，当前84/108，全部完成项仍待用户美术审核。先读取 E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md、Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时 progress.json、{rel(handoff)}、{rel(assessment_path)}、standing_network_recovery_authorization_20261028.json。后三组短文件均在 Docs/EnemyDirectionReview/Remaining_20261024 下，按文件实际路径读取。
唯一 dispatch_token 为 {token}。创建聊天时链可能暂为 handoff_ready，此时只读等待父线程登记；只有 state=active、owner_thread_id 是本聊天、current_character=SlugQueen 且 token 匹配才可操作 Unity/生产或付费请求。禁止超时接管。保持 E:/MyTowerGame，不转到根规则旧写的 FreedomTower_1/D盘。
SlugQueen现场仅reference/not_started、尚未prepare/request/raw/stage/install/runtime。先核对文件、源动画生命周期和git差异、建立增量基线，按原prompt完成单角色全流程；先实际审源，再一方向正式生成并审图，再另一方向。默认Curl沿用现有生成器；Sheep Up/Down均一次HTTP200；正常新角色不用Mounted专属AuthorizedResume，网络故障仅按standing授权限次恢复，原uncertain保留。不要重发PossessedWarg旧Down，不修改Sheep或其他角色。默认Unity MCP8082，桌面/电脑控制仍须先弹对话确认；不fork/子代理/并行/计时器/模型覆盖。
原prompt要求两轮真实Play、实际分次1-2图审阅、record、GIF归档、版本绑定和范围审计。发现生成/连接/动画复用问题先保留旧版再定点修复，不能以检查计数代替真实视觉检查。只能completed_pending_user_art_review且user_approved=false。任务已直接授权串行循环：本角色完成或真实阻断后写完整交接、更新prompt/NEXT、释放Unity，按CONTINUATION_PROTOCOL主动创建且仅创建一个全新本地后继并登记所有权，然后停止全部工作区写入；不等待逐角色再次确认。'''
(D / ('successor_prompt_' + stamp + '.txt')).write_text(prompt + '\n', encoding='utf-8')
write(dispatch_path, dict(prepared_at=now(), parent_thread_id=parent, next_character='SlugQueen', dispatch_token=token, handoff_file=rel(handoff), assessment_file=rel(assessment_path), unity_release_file=rel(release_path), prompt=prompt, prompt_file=rel(D / ('successor_prompt_' + stamp + '.txt')), progress_sha256=sha(H / 'progress.json'), handoff_sha256=sha(handoff), created=False))
assert handoff.read_text(encoding='utf-8') == handoff_text
chain.setdefault('completed_handoffs', []).append(dict(character='Sheep', status=sheep['status'], current_stage='recorded_pending_user_art_review', owner_thread_id=parent, dispatch_token=chain['dispatch_token'], closed_at=now(), handoff_file=rel(handoff), final_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Sheep/final_validation_20261028.json'))
if chain.get('resume_authorization'):
    chain['previous_resume_authorization'] = chain.pop('resume_authorization')
chain.update(state='handoff_ready', parent_thread_id=parent, current_character='SlugQueen', character_status_at_handoff='not_started', completed_count_snapshot=84, previous_handoff_file=chain['last_handoff_file'], last_handoff_file=rel(handoff), dispatch_token=token, progress_sha256_at_handoff=sha(H / 'progress.json'), handoff_sha256=sha(handoff), unity_release_file=rel(release_path), successor_assessment=rel(assessment_path), prepared_dispatch_file=rel(dispatch_path), current_stage='handoff_ready_for_fresh_local_successor', handoff_ready_at=now(), updated_at=now(), blocked_reason=None, current_blocked=False, ownership_transfer_note='Sheep finished and Unity released. No production operations while handoff_ready; awaiting exactly one fresh local successor creation and explicit registration.')
write(H / 'conversation_chain.json', chain)
print(json.dumps(dict(state=chain['state'], next_character='SlugQueen', token=token, handoff_file=rel(handoff), dispatch_file=rel(dispatch_path), progress=84, release=released), ensure_ascii=False))
