"""Release reviewed Tiger and prepare one fresh local TreasureChest successor."""
from session_tiger import *
import time, uuid

chain = owner();parent = os.environ['CODEX_THREAD_ID']
progress = read(H/'progress.json')
assert progress['completed_count'] == 87
item = next(x for x in progress['items'] if x['name'] == NAME)
assert item['status'] == 'completed_pending_user_art_review' and item['user_approved'] is False
binding = read(D/'version_binding_final_20261028.json')
assert all(sha(D/p) == s for p,s in binding['files'].items())
assert all(sha(R/p) == s for p,s in binding['installed_files'].items())
assert all(sha(R/p) == s for p,s in binding['production_scope_files'].items())
assert all(sha(R/p) == s for p,s in binding['external_evidence'].items())
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
assert len(available) == 20 and all(x['status'] == 'not_started' and not x['checkpoints'] and not x['raw']
    and not x['runtime_directories'] and all(p.startswith('reference/') for p in x['files']) for x in available)
successor = available[0]
assert successor['name'] == 'TreasureChest' and successor['index'] == 99
blocked_item = next(x for x in progress['items'] if x['name'] == 'PossessedWarg')
blocked_record = read(R/blocked_item['blocked_record'])
down = H/'PossessedWarg/generation/Down'
assert sha(down/'request.json') == blocked_record['request_sha256'] == 'B2B3C9FB4B78E2FFB5E606FCE95BB2843575982CADBE6C6E97D352346D27BA4A'
assert not any((down/p).exists() for p in ['raw.png','result.json','uncertain_result.json'])
target = next(x for x in read(H/'local_baseline.json')['targets'] if x['name'] == 'TreasureChest')
paths = [target['battle'],target['battle']+'.meta',target['source'],target['source']+'.meta',target['atlas'],target['atlas']+'.meta']
original = read(H/'production_fingerprints_before.json');six = {p:sha(R/p) for p in paths}
assert all(six[p] == original[p].upper() and sha(H/'TreasureChest/reference'/Path(p).name) == six[p] for p in paths)

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
        cache_refresh = unwrap(client.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"Tiger_handoff_live_state_read"});return true;')))
    time.sleep(1)
else:
    raise RuntimeError('Unity not ready to release')
released = probe(client)
assert released['scene'] == 'Assets/Scenes/Boot.unity' and not any(v for k,v in released.items() if k != 'scene')

stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
token = 'tiger-to-treasurechest-'+uuid.uuid4().hex
rel = lambda p:p.relative_to(R).as_posix()
handoff = H/'conversation_handoffs'/(stamp+'_Tiger_completed.md')
assessment_path = D/('successor_assessment_'+stamp+'.json')
release_path = D/('handoff_release_'+stamp+'.json')
dispatch_path = D/('successor_dispatch_'+stamp+'.json')
prompt_path = D/('successor_prompt_'+stamp+'.txt')
assert not any(p.exists() for p in [handoff,assessment_path,release_path,dispatch_path,prompt_path])
gifs = read(D/'gif_archive_verification_20261028.json')
scope = read(D/'scope_incremental_final_20261028.json')
note = (D/'record_note_utf8.txt').read_text(encoding='utf-8').strip()
live = (f'2026-10-28 Tiger98已record，87/108，completed_pending_user_art_review、user_approved=false。Up初次Curl55发送中断无HTTP/原raw/result，结果及可能计费仍不明并完整保留；回读原始人类常设授权后，仅为Tiger Up确切故障证据应用同类不明网络失败的有界恢复，revision_01第1次额外请求HTTP200，未用第2次。Down初次HTTP200。最终Up本地r01去后足侧爪痕、Down原raw，14切片27封闭针孔定点近邻修复。原9个非Shadow Sprite含HP PPtr保持；Feline Walk已有Body Euler三轴且Death为0，无额外动画修补或C#改动。两轮runtime_r01/runtime_updeath_r01各84/0、338帧，共168/0、676真实PNG；实看四向/strip、10板256采样位/228不同实际帧和3张原尺寸关键帧，未GIF全片播放或逐张全审。正背相对原侧图更窄/质感更平滑，待用户美术判断。AllGIF{gifs["total"]}，Tiger12均当前审核版。5278文件前后路径并集22变化20新增，增量unexpected0；全局历史291unexpected及6其他角色语义失败保持、新增0，不称全局PASS。Unity安全释放Boot非Play、全场景非dirty、空闲、编译失败false、error0。正确MCP8088动态核对E:/MyTowerGame；8082为其他工程。下一唯一TreasureChest99仅reference/not_started；PossessedWarg旧Down结果不明不重发。完整交接：{rel(handoff)}。所有权以实时chain为准；桌面控制仍须先对话确认。')
handoff_text = f'''# Tiger(index98) 完成与下一唯一角色交接

时间：{now()}。工程 E:/MyTowerGame，Unity2022.3.62f3c1，HTTP MCP {URL}。
父聊天：{parent}。旧令牌：{chain['dispatch_token']}。
Tiger状态 completed_pending_user_art_review、user_approved=false，record已完成；87/108。剩余21项：PossessedWarg阻断1项、未开始20项。

## 实际修改与最终版本

仅生产 battle Assets/Prefabs/Enemy/Enemy_Tiger.prefab 与 Assets/_UIAssets/Monsters/Felines/Tiger/Directions（含目录meta）变动；源Tiger.prefab/Tiger.png及meta、共享Feline、共享C#、配置表、Assets/ConfigJson/Gen、声音及其他角色保持。5278文件基线与当前路径并集22变化、20新增，未改ReporterEditor在Play自动更新build_info时间戳单列；新增越界0。没有Git同步/提交、构建、部署或桌面控制。
源与完整prefab实际审过：金橙虎、赭条斑/圆斑、奶油色嘴与层状颊毛、头上一对圆耳、四宽爪足、一条长细条纹尾。无额卷、鬃毛、鞍具或剑齿。原10 SpriteRenderer中含HP的9个非Shadow PPtr保持，只移除授权战斗Shadow，见original_sprite_contracts_20261028.json。
Up最终local_raster_revision_01/Up_sheet.png；Down最终generation/Down/raw.png。Up同后跟完好半侧镜像清除后足侧爪痕，变更矩形(582,810,710,910)，原raw不变。显式14切片矩形保留Down超过半页的完整颈部，裁去两方向尾根多余圆垫，尾干实心根按实际最后非透明行量pivot。最终Up Body宽.76、Head y.84，四足根藏身，细尾沿背；Down Head y.39、尾y.86/angle-25，远足尖在耳旁可见。布局全部在layout_adjustments.json，不能直接套下一角色。
分件后发现27个封闭1至4像素透明针孔，以3像素内最近原不透明邻色定点填充，同时修复native切片/atlas；14切片内部透明孔0。paid raw保持，修复在chroma_pinhole_repair_20261028.json。不要重跑stage覆盖修复。原始默认/第一版布局保留；最终offline_rig_proof.png、parts_clean.png和后跟前后细节均实际查看。preinstall_review_20261028.json绑定最终17个暂存文件；安装后全未漂移。安装Verify通过、重复clone不重复方向组、root/HP/event保持、无missing script、YooAsset收集器存在，未构建资源包。

## 网络结果与授权证据

Up初次generation/Up于16:18:56发生Curl55 Send failure: Connection was aborted，无HTTP/raw/result/provider ID；原结果和可能计费仍不明，未标未收费。初次request/intent/console/uncertain完整保留。
确实回读原人类消息：聊天01a18093-7687-7313-aaba-7419090cc829，turn01a180aa-774c-7ee3-8d35-d144e9389b9a，message01a180aa-7768-7222-bc85-7aa51e801cdd：“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”。该回复承接无HTTP/图像、结果不明、接受可能重复计费的有界补发说明，未限某个TLS字面错误。
standing_network_recovery_authorization_20261028.json原件未改；Tiger/standing_recovery_application_20261028.json记录本次应用及原请求证据SHA。generate.mjs仅保留旧TLS分支并增加Tiger Up revision_01/revision_02确切Curl55证据分支，需owner/token/application/原人类消息ID/standing SHA/原console匹配，两次额外上限与输出/在途门禁不变，没有全局放开。已用第1次额外请求，generation/Up/revision_01 HTTP200、raw1421271 bytes；第2次未用。Down初次HTTP200、raw1553528 bytes。均gpt-image-2/medium/1536x1024/n1、images/edits、Curl HTTPS证书检查、无redirect/retry、runtime-only密钥。无其他请求。
obsolete finalize_blocked_20261028.py从未执行，现已加无条件异常门禁并标过时；不要运行它。不要重发成功结果，也不把本次成功当作服务始终可用保证。新角色正常生成使用默认门禁；若再次出现同类故障，先按现场证据和已有人类常设授权判断，不把Tiger专属代码分支直接拿去处理其他角色。PossessedWarg旧不明请求不在本次恢复应用范围。

## 动画、真实运行和审阅

源Feline Ready .5s loop21float、Attack .5s 36float、Walk .5s loop24float、Death .25s 39float；Attack保留SetHead0/1/0与Event("Attack")，Death保留SetHead2。Walk已含Body Euler x/y/z，z为原-10/+10步态；Death Body三轴均0，故无需Swine式复位，没有改自有或共享动画来补轴。原水平曲线/PPtr/事件/时长/loop Verify通过，见source_animation_contracts_20261028.json和source_death_reuse_contract_20261028.json。没有单独捕获的预Play版本绑定，也未现场量测复用前后Euler，不能伪称已测。installed_manifest早于两轮，最终同份安装/暂存全匹配。
runtime_r01：84 PASS/0 FAIL、338实际帧，records SHA C29B81BE47E1BEB40EA90AFD70F4218BBE32D023DE28CFC8C98595CB282B09EC。
runtime_updeath_r01：84 PASS/0 FAIL、338实际帧，records SHA C3CAFD26137B6F8C39ED3A15DF8322345692E0ADCD4CF87D4089E0CA6EF81D97。
共168/0、676实际PNG，均安全返回Boot。逐条真实frame/realtime严格递增，原文件全部留存并SHA绑定。
实际查看runtime_r01/four_directions.png、runtime_visual_strip.png、visual_review_final_20261028全部10板，共256采样位、228张不同实际帧；另看runtime_r01/frames/DeathAutoRecycle_00164.png、runtime_updeath_r01/frames/DeathAutoRecycle_00164.png及runtime_r01/frames/ContinuousTurns_00303.png原尺寸。
实际观察：{note}
AllGIF共{gifs['total']}；Tiger12，全部当前审核版，来源/归档SHA一致。见gif_archive_verification_20261028.json和Docs/EnemyDirectionReview/AllGIF/index.html。这里只做真实PNG时序抽样，未实时GIF全片播放、未逐张审完676帧。

## 范围、绑定与Unity释放

增量unexpected=[]、除授权battle外六保护无漂移、本角色语义通过；原9非Shadow PPtr、当前安装/暂存一致。全局历史291unexpected和MeatBug/Monkey/MosquitoParasite/Pig/Piggy/Porky六项语义失败保持、本轮新增0，不能称全局PASS。
Tiger/version_binding_final_20261028.json绑定初次不明请求、恢复请求及原raw、授权应用、本地派生、最终暂存/安装、实际审阅媒体和全部676 PNG SHA。另见scope_incremental_final_20261028.json、final_validation_20261028.json、visual_review_final_20261028/review.json、record_note_utf8.txt、installed_manifest.json、installed_verify.txt。相对角色证据均在Docs/EnemyDirectionReview/Remaining_20261024/Tiger。
本次无C#变动。最终正确8088身份、状态、error/编译失败探针通过。交接释放：{rel(release_path)}；Boot非Play、所有场景非dirty，无编译/域重载/更新，ready_for_tools=true，scriptCompilationFailed=false、error0，review/balance/recording/manual均false。没有强停别人任务。

## 下一唯一角色与循环授权

现场重新评估21个未完成目录：PossessedWarg原Down request SHA B2B3C9FB4B78E2FFB5E606FCE95BB2843575982CADBE6C6E97D352346D27BA4A保持，缺raw/result/uncertain的历史现场不改、不重发。其余20项均仅reference/not_started，无可恢复非阻断阶段。按index选TreasureChest99，六项生产指纹与原reference一致；详细评估{rel(assessment_path)}。
源{target['source']}；battle{target['battle']}；图集{target['atlas']}；Controller {target['controller']}。这属于Inanimate/Container，必须实际审完整源prefab、Normal/Broken及动画调用生命周期，不套Tiger四足/耳/尾或动物死亡表情。由下一所有者建立自己的增量基线，保持所有原非美术行为。
用户本轮已明确调至http://127.0.0.1:8088/mcp。复用mcp_call.py默认8088，每次动态custom-tools/instances、set现场MyTowerGame完整ID、project/info确认E:/MyTowerGame和2022.3.62f3c1。暴露unityMCP工具可能仍接8082的D:/FishTestGame，不误操作，不用8080；根AGENTS旧D:/FreedomTower_1/8082内容不改变本任务现场目标。仅stale_status阻塞可用现有短反射ForceUpdate读真实缓存，不改状态flags。
唯一新令牌：{token}。创建初期chain可能handoff_ready，只读等待父登记；只有active、owner为自身、current_character=TreasureChest且token匹配后才生产/Unity/付费，不超时抢锁。默认Curl和全部既有密钥/参数/输出/在途门禁保持，桌面电脑控制仍需先弹对话确认。
不fork/子代理/并行角色/计时器/模型或推理覆盖，不Git同步/提交、构建部署，不动配置表、ConfigJson/Gen、声音或其他角色共享C#。依用户原明确逐角色循环授权，本角色完成或真实阻断后完整总结、更新README/prompt/NEXT/progress、释放Unity，动态list_projects只建一个全新本地后继。保存明确创建响应、登记所有权为父最后工作区写入，之后停止一切工作区/chain写入，再一次有界wait确认。继续至全部有效完成或仅剩真实阻断，不等待逐角色确认，不把继续授权当美术批准。
'''
next_text = f'''# 下一唯一角色 TreasureChest(index99)

在 E:/MyTowerGame 继续敌人四方向串行任务。Tiger已record，87/108，completed_pending_user_art_review、user_approved=false。父聊天{parent}。
唯一dispatch_token：`{token}`。

## 开工与所有权

先读E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md，以及Docs/EnemyDirectionReview/Remaining_20261024下REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、本NEXT、实时conversation_chain.json/progress.json、standing_network_recovery_authorization_20261028.json、Tiger/standing_recovery_application_20261028.json；完整前任交接{rel(handoff)}及现场队列评估{rel(assessment_path)}。
仅chain.state=active、owner_thread_id为本聊天、current_character=TreasureChest、token完全匹配后才可生产/Unity/付费。handoff_ready只读等父登记，不超时抢锁。目标E:/MyTowerGame，Unity2022.3.62f3c1；根AGENTS旧D盘/8082不改变当前任务显式目标和8088路由。不fork/子代理/并行角色/计时器，不改模型/推理。

## TreasureChest现场与完整执行

TreasureChest仅reference/not_started，六原生产指纹与reference匹配；无anatomy、generation/request/raw/stage/install/runtime。源{target['source']}；battle{target['battle']}；图集{target['atlas']}；Controller {target['controller']}。
先同步git当前差异、真实源图/完整prefab、调用与Container动画生命周期，建立自己的生产增量基线，不覆盖用户改动。实际检查Inanimate Normal/Broken结构及原动画事件/状态；不要套Tiger耳足尾或动物死亡面片，不凭角色名猜外形。先源审阅→一方向正式生成并实看原图→另一方向→透明分件/pivot/布局实看→单角色安装Verify→普通与Up死亡两轮真实Play各84检查→1至2图分次审四向/步态或本体动画/攻击/受击/死亡复用/暂停倍速→UTF8备注record和GIF归档→原请求/派生/暂存/安装/全部实际帧版本绑定及前后路径并集审计。若真实特殊结构不适配现有动物面片，以保留原非美术行为为先，定点修本角色，保留证据，不伪造检查通过。只能completed_pending_user_art_review且user_approved=false。
默认generate_character.ps1/Curl、gpt-image-2 images/edits、medium、1536x1024、n1、runtime-only密钥及curl config stdin、HTTPS证书检查、无redirect/retry保持。先查已有成功/在途/uncertain，不重复付费；不删安装清单绕保护、不盲重跑prepare/stage/install。普通新角色不用Mounted专属AuthorizedResume。
同类不明网络失败已有原人类常设授权：“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”，接受可能重复计费、每方向最多2次额外新revision；证据及确切边界见Tiger授权应用/交接。standing原件未改，generate.mjs原TLS分支仍在，Curl55兼容分支目前严格仅Tiger Up；若新角色同类故障须先核验自己的失败现场及授权，不能直接冒用Tiger应用或角色身份。鉴权/余额/限额不盲重试。PossessedWarg旧Down不在本次恢复范围、不重发，也不用其他角色付费探针。
禁止配置表、Assets/ConfigJson/Gen、声音、其他角色与共享C#改动；不Git pull/reset/clean/checkout/commit/push，不构建/部署。桌面电脑控制仍须先弹对话确认，默认Unity MCP。

## Unity与前任证据

正确端点http://127.0.0.1:8088/mcp，用户本轮已调整。复用mcp_call.py默认8088/MYTOWERGAME_MCP_URL，每次动态custom-tools/instances→set现场MyTowerGame完整ID→project/info核对E:/MyTowerGame及2022.3.62f3c1。暴露unityMCP工具可能仍连8082的D:/FishTestGame，不误操作其他工程，不用8080。先读error、状态、全场景dirty、Play/编译/review/录像/manual占用，不强停他人任务。仅stale_status可用现有短反射ForceUpdate读真实缓存，不改flags。自己的两轮Play已有授权，确需C#改动必须正确工程完整编译验证。
Tiger最终Up本地r01、Down原raw；27针孔已定点修复，stage会覆盖，不重跑。两轮runtime_r01/runtime_updeath_r01各84/0、338帧，共676；实际审10板256位/228不同帧和3张原尺寸关键帧，未GIF全片播放/逐张全审。原9非Shadow含HP引用保持，无Swine式Walk补轴/C#变动；Feline Walk已有三轴、Death为0。初次UpCurl55仍结果不明，第1次额外恢复HTTP200，Down初次HTTP200，原件全留。AllGIF{gifs['total']}，Tiger12当前版。全局历史291unexpected及6其他角色语义失败保持，本轮新增0，不称全局PASS。Unity安全释放证据{rel(release_path)}：Boot非Play、全场景非dirty、空闲、编译失败false/error0。

## 串行续接

本角色完成或准确记录真实阻断后重评实时队列，优先可恢复非阻断项再index。写完整时间戳交接，更新README实时块、执行prompt实时块、NEXT/progress，释放Unity，依CONTINUATION_PROTOCOL动态list_projects只创建一个全新本地后继。创建明确成功后保存响应，登记新thread/host/token作为最终父工作区写入，然后停止任何工作区/chain写入，一次有界wait确认。按用户原循环授权继续到全部有效完成或仅剩真实阻断，不等待逐角色确认。只剩阻断就保留恢复条件并停止，不能谎称后台持续运行。
'''
prompt = f'''在 E:/MyTowerGame 接棒敌人四方向串行任务，只处理 TreasureChest(index99)。父聊天{parent}已完成Tiger，当前87/108，本轮完成项仍待用户美术审核，user_approved=false。
先读取E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md；再读Docs/EnemyDirectionReview/Remaining_20261024下REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json、standing_network_recovery_authorization_20261028.json、Tiger/standing_recovery_application_20261028.json；完整交接{rel(handoff)}和队列评估{rel(assessment_path)}。相对路径均相对E:/MyTowerGame。
唯一dispatch_token：{token}。创建初期chain可能handoff_ready，此时只读等待父登记；只有active、owner_thread_id为本聊天、current_character=TreasureChest且token严格匹配后才可生产/Unity/付费，不超时抢锁。
用户本轮正确MCP为http://127.0.0.1:8088/mcp。复用mcp_call.py默认8088，每次动态custom-tools/instances→set现场MyTowerGame完整ID→project/info核对E:/MyTowerGame/Unity2022.3.62f3c1。暴露unityMCP工具可能仍连8082的D:/FishTestGame，禁止误操作，不用8080；根AGENTS旧D:/FreedomTower_1/8082不改变任务目标。默认MCP，桌面电脑控制仍需先弹对话确认。仅stale_status可用既有短反射ForceUpdate缓存，不改状态flags。
TreasureChest仅reference/not_started，六保护指纹与原reference相同，无prepare/request/raw/stage/install/runtime。源{target['source']}；battle{target['battle']}；图集{target['atlas']}；Controller {target['controller']}。先同步git改动、实际审源图/完整prefab、Container Normal/Broken和动画调用生命周期，建立自己的增量基线，不套Tiger耳足尾/动物表情或Swine补轴。按原prompt逐阶段完成参考、正式两方向与实看原图、透明分件/pivot/布局审阅、单角色安装Verify、两轮真实Play各84检查、分次1至2图审四向及动作/死亡复用/暂停倍速、UTF8记录record/GIF归档、原请求至全部真实帧版本绑定与路径并集审计；PNG抽样如实说明，不能称GIF全播或全帧审核。
默认Curl和gpt-image-2/medium/1536x1024/n1安全参数保持，先查成功/在途/uncertain、不重复付费，不删安装清单。普通角色不用Mounted专属授权。同类不明网络故障已有原人类常设静默有界恢复授权，接受可能重复计费、每方向最多2次额外新revision；本次Tiger应用与交接保存原人类消息ID及证据。generate.mjs保留旧TLS分支、Curl55扩展仅Tiger Up确切证据，后继遇同类故障先核验自己的现场与授权，不能冒用Tiger应用。鉴权/余额/限额不盲重试。PossessedWarg旧Down仍不明、不重发、不作探针。
Tiger两轮各84/0、338实际帧，共168/0、676；12GIF已归档，全库1390。实看10板256位/228不同帧及3原尺寸关键帧，未GIF全片/全帧审，原9非Shadow含HP PPtr保持。Up初次Curl55结果/可能计费仍不明，revision_01第1次额外请求HTTP200；Down初次HTTP200，原件保持。最终Up本地r01、Down原raw，27针孔定点修复不要重stage，未改C#或补自有Walk轴。正背较原侧窄/平滑仍待美术判断。全局历史291unexpected及6其他角色语义失败保持，本轮新增0，不称全局PASS。Unity已安全释放Boot非Play、全场景非dirty、空闲、编译失败false/error0。
不fork/子代理/并行角色/计时器/模型或推理覆盖。不改配置表、Assets/ConfigJson/Gen、声音、其他角色和共享C#，不Git同步/提交、构建/部署。只completed_pending_user_art_review、user_approved=false。依用户原明确循环授权，本角色完成或真实阻断后重评队列、写完整新交接、更新README/prompt/NEXT/progress、释放Unity，按协议动态list_projects且只创建一个全新本地后继；保存明确创建响应、登记所有权为最终父工作区写入，之后停止写入，一次有界wait确认。继续至全部有效完成或仅剩真实阻断，不等待逐角色确认。'''

updates = {}
for path,marker in [(H.parent/'README.md','ENEMY_README_LIVE'),(H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','ENEMY_SERIAL_LIVE_STATE')]:
    text = path.read_text(encoding='utf-8');pattern = r'<!-- '+marker+r'_BEGIN -->.*?<!-- '+marker+r'_END -->'
    assert len(re.findall(pattern,text,re.S)) == 1
    text = re.sub(pattern,'<!-- '+marker+'_BEGIN -->\n'+live+'\n<!-- '+marker+'_END -->',text,flags=re.S)
    if path.name == 'README.md':
        text = re.sub(r'2026-10-28 本轮当前清单为 \d+ 个文件',f'2026-10-28 本轮当前清单为 {gifs["total"]} 个文件',text)
    updates[path] = text
write(assessment_path,dict(observed_at=now(),progress_completed_count=87,unfinished=assessment,blocked_preserved=blocked,
    possessed_warg_down_request_sha256=sha(down/'request.json'),missing_outcome_unchanged=True,
    available_count=len(available),chosen=successor,target=target,chosen_protected_six=six,protected_drift=[],
    reason='No recoverable nonblocked stage exists. Lowest reference-only not_started is TreasureChest99; PossessedWarg uncertain Down preserved without resend.'))
write(release_path,dict(observed_at=now(),transport=URL,project=project,state=state,cache_refresh=cache_refresh,
    errors=errors,live=released,protocol_history=client.history,
    note='Own two rounds already safely returned; no forced Play exit, desktop control or C# changes.'))
handoff.write_text(handoff_text,encoding='utf-8')
for path,text in updates.items(): path.write_text(text,encoding='utf-8')
(H/'NEXT_ENEMY_TASK.md').write_text(next_text,encoding='utf-8')
progress.update(current='TreasureChest',updated_at=now());write(H/'progress.json',progress)
prompt_path.write_text(prompt+'\n',encoding='utf-8')
write(dispatch_path,dict(prepared_at=now(),parent_thread_id=parent,next_character='TreasureChest',dispatch_token=token,
    handoff_file=rel(handoff),assessment_file=rel(assessment_path),unity_release_file=rel(release_path),prompt=prompt,
    prompt_file=rel(prompt_path),progress_sha256=sha(H/'progress.json'),handoff_sha256=sha(handoff),created=False))
assert handoff.read_text(encoding='utf-8') == handoff_text and (H/'NEXT_ENEMY_TASK.md').read_text(encoding='utf-8') == next_text
chain.setdefault('completed_handoffs',[]).append(dict(character=NAME,status=item['status'],current_stage='recorded_pending_user_art_review',
    owner_thread_id=parent,dispatch_token=chain['dispatch_token'],closed_at=now(),handoff_file=rel(handoff),
    final_evidence='Docs/EnemyDirectionReview/Remaining_20261024/Tiger/final_validation_20261028.json'))
chain.update(state='handoff_ready',parent_thread_id=parent,current_character='TreasureChest',character_status_at_handoff='not_started',
    completed_count_snapshot=87,previous_handoff_file=chain['last_handoff_file'],last_handoff_file=rel(handoff),dispatch_token=token,
    progress_sha256_at_handoff=sha(H/'progress.json'),handoff_sha256=sha(handoff),unity_release_file=rel(release_path),
    successor_assessment=rel(assessment_path),prepared_dispatch_file=rel(dispatch_path),current_stage='handoff_ready_for_fresh_local_successor',
    handoff_ready_at=now(),updated_at=now(),blocked_reason=None,current_blocked=False,mcp_endpoint=URL,successor_created=False,
    dispatch_ready_for='TreasureChest',resume_character='TreasureChest',resume_stage='Inspect Container Normal/Broken and lifecycle; single-character workflow',
    ownership_transfer_note='Tiger recorded and Unity released on8088. No production operations while handoff_ready; await one fresh local TreasureChest chat and explicit registration.')
write(H/'conversation_chain.json',chain)
print(json.dumps(dict(state=chain['state'],next_character='TreasureChest',token=token,handoff_file=rel(handoff),
    dispatch_file=rel(dispatch_path),progress=87,release=released),ensure_ascii=False))
