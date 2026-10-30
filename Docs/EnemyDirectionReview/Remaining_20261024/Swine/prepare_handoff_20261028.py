"""Prepare one fresh Tiger successor after Swine record; no production edits."""
from session_swine import *
import time, uuid

chain = owner();parent = os.environ['CODEX_THREAD_ID']
progress = read(H/'progress.json')
assert progress['completed_count'] == 86
item = next(x for x in progress['items'] if x['name'] == NAME)
assert item['status'] == 'completed_pending_user_art_review' and item['user_approved'] is False
binding = read(D/'version_binding_final_20261028.json')
assert all(sha(D/p) == s for p,s in binding['files'].items())
assert all(sha(R/p) == s for p,s in binding['installed_files'].items())
assert all(sha(R/p) == s for p,s in binding['production_scope_files'].items())
assessment = []
for candidate in sorted((x for x in progress['items'] if x['status'] not in ['completed_pending_user_art_review','user_approved']),key=lambda x:x['index']):
    folder = H/candidate['name']
    files = sorted(p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file())
    assessment.append(dict(index=candidate['index'],name=candidate['name'],status=candidate['status'],files=files,
        checkpoints=[p for p in ['anatomy_plan.json','installed_manifest.json','runtime_summary.json'] if (folder/p).is_file()],
        raw=[p for p in files if p.endswith('/raw.png')],runtime_directories=[p.name for p in folder.glob('runtime*') if p.is_dir()],
        blocked_reason=candidate.get('blocked_reason')))
blocked = [x for x in assessment if x['status'] == 'blocked']
available = [x for x in assessment if x['status'] != 'blocked']
assert len(blocked) == 1 and blocked[0]['name'] == 'PossessedWarg'
assert len(available) == 21 and all(x['status'] == 'not_started' and not x['checkpoints'] and not x['raw']
    and not x['runtime_directories'] and all(p.startswith('reference/') for p in x['files']) for x in available)
successor = available[0]
assert successor['name'] == 'Tiger' and successor['index'] == 98
blocked_item = next(x for x in progress['items'] if x['name'] == 'PossessedWarg')
blocked_record = read(R/blocked_item['blocked_record'])
down = H/'PossessedWarg/generation/Down'
assert sha(down/'request.json') == blocked_record['request_sha256']
assert not any((down/p).exists() for p in ['raw.png','result.json','uncertain_result.json'])
target = next(x for x in read(H/'local_baseline.json')['targets'] if x['name'] == 'Tiger')
paths = [target['battle'],target['battle']+'.meta',target['source'],target['source']+'.meta',target['atlas'],target['atlas']+'.meta']
original = read(H/'production_fingerprints_before.json')
six = {p:sha(R/p) for p in paths}
assert all(six[p] == original[p].upper() and sha(H/'Tiger/reference'/Path(p).name) == six[p] for p in paths)

client = Client();project = client.identity()
errors = unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')))
assert errors['data'] == []
cache_refresh = None
for attempt in range(4):
    state = client.resource('mcpforunity://editor/state');s = state['data']
    if (not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending']
            and not s['assets']['is_updating'] and s['advice']['ready_for_tools']):
        break
    if attempt == 0 and s['advice'].get('blocking_reasons') == ['stale_status']:
        cache_refresh = unwrap(client.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"Swine_handoff_live_state_read"});return true;')))
    time.sleep(1)
else:
    raise RuntimeError('Unity not ready to release')
released = probe(client)
assert released['scene'] == 'Assets/Scenes/Boot.unity' and not any(v for k,v in released.items() if k != 'scene')

stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
token = 'swine-to-tiger-'+uuid.uuid4().hex
rel = lambda p:p.relative_to(R).as_posix()
handoff = H/'conversation_handoffs'/(stamp+'_Swine_completed.md')
assessment_path = D/('successor_assessment_'+stamp+'.json')
release_path = D/('handoff_release_'+stamp+'.json')
dispatch_path = D/('successor_dispatch_'+stamp+'.json')
prompt_path = D/('successor_prompt_'+stamp+'.txt')
assert not any(p.exists() for p in [handoff,assessment_path,release_path,dispatch_path,prompt_path])
gifs = read(D/'gif_archive_verification_20261028.json')
scope = read(D/'scope_incremental_final_20261028.json')
note = (D/'record_note_utf8.txt').read_text(encoding='utf-8').strip()
live = (f'2026-10-28 Swine97完成，86/108，completed_pending_user_art_review、user_approved=false。Up/Down正式生成各一次HTTP200无付费重试；最终Up本地r03、Down本地r02，去重复头耳、恢复圆胖躯干、清除后脚淡三角痕。只给Swine自有Walk补Body Euler三轴0，136原绑定/事件/时序保持、改后139；最终仅换图集且动画SHA不变。最终runtime_r02/runtime_updeath_r02各84/0，338+339共677真实帧；实际审四方向/strip、10板(256采样位/238不同帧)、3张原尺寸运行PNG及后脚切片，未播放GIF全片或逐帧全审，不声称现场量测复用前后Euler。AllGIF{gifs["total"]}，Swine24含12当前版。5258文件基线并集22变化20新增，增量unexpected0；原8个非Shadow Sprite PPtr/六保护/语义/安装绑定通过。全局历史291unexpected及6其他角色语义失败保留、新增0，不能称全局PASS。Unity安全释放Boot非Play、全场景非dirty、空闲、编译失败false、error0。正确MCP为HTTP Local8088，动态核对E:/MyTowerGame；8082为其他工程，不得误操作。下一唯一Tiger98，仅reference/not_started；PossessedWarg旧Down仍uncertain不重发。完整交接：{rel(handoff)}。所有权以实时chain为准；桌面控制仍须先对话确认。')
handoff_text = f'''# Swine(index97) 完成与下一唯一角色交接

时间：{now()}。工程 E:/MyTowerGame，Unity 2022.3.62f3c1，HTTP MCP {URL}。
父聊天：{parent}。旧令牌：{chain['dispatch_token']}。
Swine 为 completed_pending_user_art_review，user_approved=false，record 已完成。当前86/108；22项未完成，其中PossessedWarg阻断1项，未开始21项。

## 实际修改与版本

仅本角色 battle Assets/Prefabs/Enemy/Enemy_Swine.prefab 与 Assets/_UIAssets/Monsters/Pigs/Swine/Directions 发生生产修改；源Swine.prefab/Swine.png、meta、共享Boar动画、共享C#、配置表、Assets/ConfigJson/Gen、声音及其他角色保持。没有Git同步/提交、构建或部署。前后路径并集22变化、20新增；其中未改过的ReporterEditor在Play自动更新build_info时间戳单列。
源参考与完整prefab、原始生成图实际看过。Up与Down正式请求各一次HTTP200，raw分别1360116/1465033 bytes；intent/prompt/request/result/raw均保留，无付费重试。Up最终选Swine/local_raster_revision_03/Up_sheet.png；Down选Swine/local_raster_revision_02/Down_sheet.png。保留圆胖金棕赭斑野猪、大象牙獠牙、四个短足、躯干上一对耳及细小尖尾。Up后脑无脸、无獠牙，没有重复头耳；Down正常/愤怒/死亡表情分片。
本地r01清除Up头耳；r02仅压扁生成躯干以恢复圆胖比例，不变换原侧面伪造方向；两次失败布局保留在offline_layout_revision_01/02。最终布局让后脑盖住颈帽，四足根嵌入躯干。旧runtime_r01/runtime_updeath_r01共673真实帧虽168/0，但原尺寸后脚发现淡三角残留而降为历史；旧10张审阅板确已查看，准确否决见local_raster_revision_03/rejected_previous.json。
r03对后跟内区x181..201/y828..862完整同行插值，保留外轮廓；已实际查看最终原尺寸后脚。仅替换Swine_Directions.png，没有全Build、未删除安装清单。final staged {len(scope['final_staging_alpha'])} PNG透明度/无紫底检查通过；相比首次offline_review只Up_LegFront.png和总图集变化，已绑定最终哈希。原8个非Shadow Sprite PPtr含HP保持，唯一允许删除原Shadow。
初次安装后有一次检查把预期删除的Shadow也当成必须保留，因此断言停止；安装/Verify当时已成功。随后读取实物证实只删除Shadow而恢复流程，没有重装或删清单。见original_sprite_contracts_20261028.json。

## 动画与最终运行

源Boar Death旋转Body，而Walk没有复位。side_reuse_repair_r01只给Swine自有Walk_Directions.anim补Body/localEulerAnglesRaw.x/y/z常量0：136原float绑定、PPtr/事件/时长/loop保持，改后139。最终图集替换后Walk SHA仍为3507551C0A1814E4BD53E7443632113982D59929D2A3CBAC4F13289E86DA096F。不要全Build覆盖自有修复，不改共享Boar或C#。
现场反射采样大多错过复用阶段，一次旧轮观察到行走Body Euler0；不能声称量测到了复用前后Euler0。实际断言与复用PNG提供恢复证据。
最终runtime_r02：84 PASS/0 FAIL、338帧；runtime_updeath_r02：84 PASS/0 FAIL、339帧；合计168/0、677真实Unity帧。两轮均安全返回原Boot场景。runtime_summary.json只指最终r02两轮。
实际查看最终four_directions.png、runtime_visual_strip.png及visual_review_final_r02_20261028全部10板，共256采样位、238张不同实际帧；另看runtime_r02/frames/DeathAutoRecycle_00162.png、ContinuousTurns_00323.png、runtime_updeath_r02/frames/DeathAutoRecycle_00162.png原尺寸及staged_art/Up_LegFront.png。方法为时序PNG抽样，未实时播放GIF全片、未逐张审完677帧。
真实观察备注：{note}
AllGIF总{gifs['total']}；Swine共{gifs['character_count']}，{gifs['current_count']}当前审核版，余为历史。来源/归档SHA一致，见gif_archive_verification_20261028.json与Docs/EnemyDirectionReview/AllGIF/index.html。

## 范围与证据

5258文件增量基线按before/current路径并集含新增/删除，22变化20新增，增量unexpected=[]，除授权battle外六保护无漂移；本角色非美术语义、原Sprite、当前安装/暂存/预运行绑定通过。历史全局291unexpected和MeatBug/Monkey/MosquitoParasite/Pig/Piggy/Porky六项语义失败保持、新增0；不能称全局PASS。
Swine/version_binding_final_20261028.json绑定选图、原请求与raw、本地派生、暂存、最终安装、Walk复位、运行媒体、真实已审板和全部677 PNG SHA256。另见scope_incremental_final_20261028.json、final_validation_20261028.json、visual_review_final_r02_20261028/review.json、record_note_utf8.txt、installed_manifest.json、installed_verify.txt。相对文件均在Docs/EnemyDirectionReview/Remaining_20261024下。
本次未改C#；安装/最终图集Verify通过，末次Unity身份/状态/error/编译失败探针正确。交接释放证据：{rel(release_path)}。Boot非Play、所有场景非dirty、无编译/域重载/更新、ready_for_tools=true、scriptCompilationFailed=false、error0、review/balance/recording/manual均false。未强停他人任务或进行桌面控制。

## 下一唯一角色与路由

重新读取22项未完成材料：PossessedWarg原Down request SHA保持B2B3C9FB4B78E2FFB5E606FCE95BB2843575982CADBE6C6E97D352346D27BA4A，依旧缺raw/result/uncertain，历史阻断保留不重发。其余21项仅reference且not_started，没有可恢复的非阻断阶段；按index选择Tiger98，六项原指纹及reference匹配。完整评估：{rel(assessment_path)}。
Tiger源：{target['source']}；battle：{target['battle']}；图集：{target['atlas']}；源Controller：{target['controller']}。新聊天先实际审源图/完整prefab和Feline生命周期，建立自己的增量基线，不套Swine或SabretoothTiger解剖、布局、角度或修复。
当前MCP正确端点为http://127.0.0.1:8088/mcp，来自用户本轮直接端口调整。mcp_call.py默认8088，每次动态custom-tools/instances、set现场MyTowerGame完整ID、project/info确认E:/MyTowerGame及2022.3.62f3c1。暴露的unityMCP工具仍可能连8082的D:/FishTestGame，不能误操作；不用8080。根AGENTS旧D盘/8082差异保留，当前任务显式路由优先。
唯一新令牌：{token}。新聊天创建时chain可能handoff_ready，只读等待；仅state=active、owner是自己、角色Tiger且token匹配才能生产/Unity/付费。不超时抢锁。默认Curl生成器、standing_network_recovery_authorization_20261028.json有界恢复、独立桌面确认规则保持。禁止fork/子代理/并行角色/计时器/模型或推理覆盖。
依原授权逐角色循环至全部有效完成或仅剩真实阻断。本角色完成或真实阻断后总结、更新README/prompt/NEXT/progress、释放Unity，动态list_projects只创建一个全新本地后继；明确创建成功后登记所有权即停止所有工作区写入，再一次有界wait确认。不能把继续任务授权等同用户美术批准。
'''
next_text = f'''# 下一唯一角色 Tiger(index98)

在E:/MyTowerGame继续敌人四方向串行任务。Swine已record，86/108，completed_pending_user_art_review、user_approved=false。父聊天{parent}。唯一dispatch_token：`{token}`。

## 开工与所有权

必读E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md，以及Docs/EnemyDirectionReview/Remaining_20261024下REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、本NEXT、实时conversation_chain.json/progress.json、standing_network_recovery_authorization_20261028.json；完整前任交接{rel(handoff)}及现场队列评估{rel(assessment_path)}。
仅chain.state=active、owner_thread_id为本聊天、current_character=Tiger且token严格匹配才可生产/Unity/付费。handoff_ready只读等待父登记，不靠超时抢锁。目标为E:/MyTowerGame，根AGENTS旧FreedomTower_1/D盘/8082不改变本任务目标或当前8088路由。不fork/子代理/并行角色，不改模型/推理，不建计时器。

## Tiger当前阶段与执行

Tiger仅reference/not_started：Enemy_Tiger.prefab/Tiger.prefab/Tiger.png及meta、source_structure.json、source_prefab_offline.png。六项原生产指纹与reference匹配，没有anatomy/generation/request/raw/stage/install/runtime。先针对Tiger同步git差异、真实源图/完整prefab、调用与Feline动画生命周期，建立自己的生产增量基线，必要prepare；不覆盖用户已有改动。
源{target['source']}；battle{target['battle']}；图集{target['atlas']}；源Controller {target['controller']}。解剖、足/尾/耳、步态依实际源，不套前角色方案。查Death→Walk复用是否需要仅本角色自有动画复位；保留原float/PPtr/事件/时长/loop，不改共享动画/C#。
按原prompt关卡完成：实际审源→一方向正式生成并实际审图→另一方向→透明切片/pivot/布局实际审阅→单角色安装Verify→普通与Up死亡两轮真实Play各84检查→1-2图分次实际审四向/动作/死亡复用/暂停倍速→UTF8备注record和GIF归档→原请求、派生、暂存、安装、全部实际帧版本绑定及前后路径并集审计。仅PNG抽样如实说明，不能称GIF全播或全帧审核。发现问题保留旧revision，修复后重跑。只能completed_pending_user_art_review且user_approved=false。
generate_character.ps1默认Curl；gpt-image-2 images/edits、medium、1536x1024、n1，密钥runtime-only/curl config stdin、HTTPS证书检查、无redirect/retry，owner/token/六保护/输出存在门禁保持。先查已有成功/在途/uncertain，不重复收费。Swine上下各一次HTTP200无付费重试；正常新角色不使用Mounted专属AuthorizedResume。同类TLS故障仅按standing授权每方向最多2次额外新revision，保留uncertain与计数；鉴权/余额/上限不盲重试，不用其他角色付费探针。桌面电脑控制仍必须先弹对话确认，默认Unity MCP。
安装清单不删后重装，原raw/请求/失败/完整帧保留。除授权battle外六保护不动；历史291unexpected及6其他角色语义失败保持、新增0，不称全局PASS。禁止配置表、Assets/ConfigJson/Gen、声音、其他角色、共享C#改动；不Git pull/reset/clean/checkout/commit/push，不构建部署。

## Unity 8088与自动续接

正确MCP为http://127.0.0.1:8088/mcp，用户本轮已调整；旧unityMCP工具可能连8082的D:/FishTestGame，禁止误操作，不占8080。复用mcp_call.py默认8088/MYTOWERGAME_MCP_URL，每次动态custom-tools/instances→set现场MyTowerGame完整ID→project/info核对E:/MyTowerGame/2022.3.62f3c1。先读error与状态、全场景dirty、Play/编译/review/录像/manual占用；不强停他人任务或覆盖场景。仅stale_status时可用现有短反射ForceUpdate读真实缓存，不改flags。自己的两轮Play已有授权；若确需C#改动必须正确工程完整编译验证。
Swine最终Up本地r03、Down本地r02，runtime_r02/runtime_updeath_r02为84/0各一轮、共677帧；旧673帧是后跟残痕否决历史。只给自有Walk补Body Euler三轴0、136原绑定保持；不要全Build覆盖，不改Swine Assets。最终审256采样位/238不同帧，未GIF全片播放。AllGIF{gifs['total']}，Swine24含12当前版。Unity已安全释放Boot非Play、全场景非dirty、空闲、编译失败false/error0，见{rel(release_path)}。
PossessedWarg旧Down仍uncertain不重发，历史阻断与授权范围保持。完成或真实阻断后重评实时队列，写完整新交接、更新README/LIVE/NEXT/progress、安全交回Unity，按CONTINUATION_PROTOCOL动态list_projects且只创建一个全新本地后继。create明确成功后保存响应、登记新thread/host/token作为最终父工作区写入，立即停止后续写入；一次有界wait确认。按原用户循环授权继续，不等待逐角色确认。
'''
prompt = f'''在 E:/MyTowerGame 接棒敌人四方向串行任务，只处理 Tiger(index98)。父聊天{parent}已完成Swine，当前86/108，全部本轮完成项仍待用户美术审核，user_approved=false。
先读取E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md，以及Docs/EnemyDirectionReview/Remaining_20261024下REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json、standing_network_recovery_authorization_20261028.json；完整交接{rel(handoff)}和队列评估{rel(assessment_path)}。未带完整根路径的文件均相对E:/MyTowerGame。
唯一dispatch_token：{token}。创建初期chain可能handoff_ready，此时只读等待父线程登记；仅state=active、owner_thread_id为本聊天、current_character=Tiger且token严格匹配，才可生产/Unity/付费。不超时接管。根AGENTS旧D盘和8082差异保留，不转工程。
当前正确MCP为http://127.0.0.1:8088/mcp，来自用户本轮端口调整；复用mcp_call.py默认8088，每次动态custom-tools/instances→set现场MyTowerGame完整ID→project/info核对E:/MyTowerGame及Unity2022.3.62f3c1。暴露unityMCP工具仍可能接8082的D:/FishTestGame，不得误操作其他工程，不占8080。桌面控制仍须先弹对话确认，默认Unity MCP。仅stale_status可既有短反射ForceUpdate缓存，不改flags。
Tiger仅reference/not_started，无prepare/request/raw/staging/install/runtime；六保护与参考一致。源{target['source']}，battle{target['battle']}，图集{target['atlas']}，Controller {target['controller']}。先同步当前git改动、实际审源图/完整prefab及调用/动画生命周期，建立增量基线，再按原prompt逐关卡：源审阅、一方向正式生成与实际审图、另一方向、stage布局审阅、单角色安装Verify、两轮真实Play各84检查、分次1-2图实际审四向与动作/复用/暂停倍速、UTF8记录record/GIF归档、全帧版本绑定和路径并集范围审计。解剖与自有复位按Tiger实际源定，不套Swine或SabretoothTiger。
默认Curl和既有AIHub安全参数gpt-image-2/medium/1536x1024/n1保持。已有成功复用、在途/uncertain先查；正常角色不用Mounted专属授权。同类TLS失败只按standing授权每方向最多2次额外新revision恢复、保留uncertain与计数，不重发PossessedWarg旧Down，不用其他角色付费探针。鉴权/余额/上限不盲重试。
Swine最终Up local_raster_revision_03、Down local_raster_revision_02，最终runtime_r02/runtime_updeath_r02为168/0、677真实帧，已record待用户美术审核。旧673帧后脚淡三角痕被否决保留。只给Swine自有Walk增加Body Euler三轴常量0、保留136原绑定/事件/时序，最终图集返修后动画SHA未变；不要全Build覆盖，不改其Assets。真实审阅是PNG时序抽样(10板256采样位/238不同帧)和关键原尺寸帧，未GIF全片播放或逐帧全审。全局历史291unexpected和6其他角色语义失败保持、本轮新增0，不称全局PASS。
不fork/子代理/并行角色/计时器/模型或推理覆盖。禁止配置表、Assets/ConfigJson/Gen、声音、其他角色和共享C#改动；不Git同步/提交、构建部署。只completed_pending_user_art_review、user_approved=false。依原用户明确授权，本角色完成或真实阻断后重评实时队列、完整总结、更新README/prompt/NEXT/progress、释放Unity，按CONTINUATION_PROTOCOL动态list_projects且只创建一个全新本地后继；创建明确成功后保存响应并登记所有权作为最终父工作区写入，随后停止写入，一次有界wait确认。继续串行循环直至全部有效完成或仅剩真实阻断，不等待逐角色确认。'''

updates = {}
for path,marker in [(H.parent/'README.md','ENEMY_README_LIVE'),(H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','ENEMY_SERIAL_LIVE_STATE')]:
    text = path.read_text(encoding='utf-8')
    pattern = r'<!-- '+marker+r'_BEGIN -->.*?<!-- '+marker+r'_END -->'
    assert len(re.findall(pattern,text,re.S)) == 1
    text = re.sub(pattern,'<!-- '+marker+'_BEGIN -->\n'+live+'\n<!-- '+marker+'_END -->',text,flags=re.S)
    if path.name == 'README.md':
        text = re.sub(r'2026-10-28 本轮当前清单为 \d+ 个文件',f'2026-10-28 本轮当前清单为 {gifs["total"]} 个文件',text)
        text += '\n\n'+live+'\n'
    updates[path] = text
write(assessment_path,dict(observed_at=now(),progress_completed_count=86,unfinished=assessment,
    blocked_preserved=blocked,possessed_warg_down_request_sha256=sha(down/'request.json'),missing_outcome_unchanged=True,
    available_count=len(available),chosen=successor,target=target,chosen_protected_six=six,protected_drift=[],
    reason='No recoverable nonblocked stage exists; lowest reference-only not_started is Tiger98. PossessedWarg uncertain Down preserved without resend.'))
write(release_path,dict(observed_at=now(),transport=URL,project=project,state=state,cache_refresh=cache_refresh,
    errors=errors,live=released,protocol_history=client.history,
    note='Own two final tester rounds already safely returned. No forced Play exit, desktop control or C# changes.'))
handoff.write_text(handoff_text,encoding='utf-8')
for path,text in updates.items():
    path.write_text(text,encoding='utf-8')
(H/'NEXT_ENEMY_TASK.md').write_text(next_text,encoding='utf-8')
progress.update(current='Tiger',updated_at=now())
write(H/'progress.json',progress)
prompt_path.write_text(prompt+'\n',encoding='utf-8')
write(dispatch_path,dict(prepared_at=now(),parent_thread_id=parent,next_character='Tiger',dispatch_token=token,
    handoff_file=rel(handoff),assessment_file=rel(assessment_path),unity_release_file=rel(release_path),
    prompt=prompt,prompt_file=rel(prompt_path),progress_sha256=sha(H/'progress.json'),handoff_sha256=sha(handoff),created=False))
assert handoff.read_text(encoding='utf-8') == handoff_text
assert (H/'NEXT_ENEMY_TASK.md').read_text(encoding='utf-8') == next_text
chain.setdefault('completed_handoffs',[]).append(dict(character=NAME,status=item['status'],
    current_stage='recorded_pending_user_art_review',owner_thread_id=parent,dispatch_token=chain['dispatch_token'],
    closed_at=now(),handoff_file=rel(handoff),final_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Swine/final_validation_20261028.json'))
chain.update(state='handoff_ready',parent_thread_id=parent,current_character='Tiger',character_status_at_handoff='not_started',
    completed_count_snapshot=86,previous_handoff_file=chain['last_handoff_file'],last_handoff_file=rel(handoff),
    dispatch_token=token,progress_sha256_at_handoff=sha(H/'progress.json'),handoff_sha256=sha(handoff),
    unity_release_file=rel(release_path),successor_assessment=rel(assessment_path),prepared_dispatch_file=rel(dispatch_path),
    current_stage='handoff_ready_for_fresh_local_successor',handoff_ready_at=now(),updated_at=now(),
    blocked_reason=None,current_blocked=False,mcp_endpoint=URL,successor_created=False,dispatch_ready_for='Tiger',
    resume_character='Tiger',resume_stage='Inspect reference and Feline lifecycle, then single-character workflow',
    ownership_transfer_note='Swine recorded and Unity released on8088. No production operations while handoff_ready; await one fresh local Tiger chat and explicit registration.')
write(H/'conversation_chain.json',chain)
print(json.dumps(dict(state=chain['state'],next_character='Tiger',token=token,handoff_file=rel(handoff),
    dispatch_file=rel(dispatch_path),progress=86,release=released),ensure_ascii=False))
