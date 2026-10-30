"""Release TreasureChest and prepare exactly one fresh local Troll successor."""
from session_treasurechest import *
import time,uuid

chain=owner();parent=os.environ['CODEX_THREAD_ID'];progress=read(H/'progress.json');assert progress['completed_count']==88
item=next(x for x in progress['items'] if x['name']==NAME)
assert item['status']=='completed_pending_user_art_review' and item['user_approved'] is False
binding=read(D/'version_binding_final_20261028.json')
assert all(sha(D/p)==s for p,s in binding['files'].items())
assert all(sha(R/p)==s for key in ['installed_files','production_scope_files','external_evidence'] for p,s in binding[key].items())
assessment=[]
for candidate in sorted((x for x in progress['items'] if x['status'] not in ['completed_pending_user_art_review','user_approved']),key=lambda x:x['index']):
    folder=H/candidate['name'];files=sorted(p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file())
    assessment.append(dict(index=candidate['index'],name=candidate['name'],status=candidate['status'],files=files,checkpoints=[p for p in ['anatomy_plan.json','installed_manifest.json','runtime_summary.json'] if (folder/p).is_file()],raw=[p for p in files if p.endswith('/raw.png')],runtime_directories=[p.name for p in folder.glob('runtime*') if p.is_dir()],blocked_reason=candidate.get('blocked_reason')))
blocked=[x for x in assessment if x['status']=='blocked'];available=[x for x in assessment if x['status']!='blocked']
assert len(assessment)==20 and len(blocked)==1 and blocked[0]['name']=='PossessedWarg'
assert len(available)==19 and all(x['status']=='not_started' and not x['checkpoints'] and not x['raw'] and not x['runtime_directories'] and all(p.startswith('reference/') for p in x['files']) for x in available)
successor=available[0];assert successor['name']=='Troll' and successor['index']==100
blocked_item=next(x for x in progress['items'] if x['name']=='PossessedWarg');blocked_record=read(R/blocked_item['blocked_record']);down=H/'PossessedWarg/generation/Down'
assert sha(down/'request.json')==blocked_record['request_sha256']=='B2B3C9FB4B78E2FFB5E606FCE95BB2843575982CADBE6C6E97D352346D27BA4A'
assert not any((down/p).exists() for p in ['raw.png','result.json','uncertain_result.json'])
target=next(x for x in read(H/'local_baseline.json')['targets'] if x['name']=='Troll')
paths=[target['battle'],target['battle']+'.meta',target['source'],target['source']+'.meta',target['atlas'],target['atlas']+'.meta'];original=read(H/'production_fingerprints_before.json');six={p:sha(R/p) for p in paths}
assert all(six[p]==original[p].upper() and sha(H/'Troll/reference'/Path(p).name)==six[p] for p in paths)
client=Client();project=client.identity();errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')));assert errors['data']==[]
cache_refresh=None
for attempt in range(4):
    state=client.resource('mcpforunity://editor/state');s=state['data']
    if not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']:break
    if attempt==0 and s['advice'].get('blocking_reasons')==['stale_status']:
        cache_refresh=unwrap(client.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"TreasureChest_handoff_live_state_read"});return true;')))
    time.sleep(1)
else:raise RuntimeError('Unity not ready to release')
released=probe(client);own_review=unwrap(client.tool('execute_code',dict(action='execute',code='return FTProject.EditorTools.TreasureChestDirectionReview.Running;')))['data']['result']
assert released['scene']=='Assets/Scenes/Boot.unity' and not any(v for k,v in released.items() if k!='scene') and own_review is False
stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S');token='treasurechest-to-troll-'+uuid.uuid4().hex
rel=lambda p:p.relative_to(R).as_posix()
handoff=H/'conversation_handoffs'/(stamp+'_TreasureChest_completed.md');assessment_path=D/('successor_assessment_'+stamp+'.json');release_path=D/('handoff_release_'+stamp+'.json');dispatch_path=D/('successor_dispatch_'+stamp+'.json');prompt_path=D/('successor_prompt_'+stamp+'.txt')
assert not any(p.exists() for p in [handoff,assessment_path,release_path,dispatch_path,prompt_path])
gifs=read(D/'gif_archive_verification_20261028.json');scope=read(D/'scope_incremental_final_20261028.json');runtime=read(D/'runtime_summary.json');note=(D/'record_note_utf8.txt').read_text(encoding='utf-8').strip()
live=f'''2026-10-28 TreasureChest99已record，88/108，completed_pending_user_art_review、user_approved=false。源为无脸无肢的金赭木/灰铁箍宝箱，Container整物Normal闭合/Broken开箱；Up真实后视图局部轴向纠偏、Down原raw。Up初次Curl56和额外r01 Curl55仍结果/可能计费不明，原证据保留；按原人类常设授权仅定点两次有界恢复，r02 HTTP200、已耗尽两次额外上限，Down初次HTTP200。透明载体+六整物状态图，6905个低alpha外缘像素去除，内部透明孔0。原4非Shadow含HP PPtr、源prefab/atlas/Container/共享C#不变；仅本角色Directions/Editor适配器/审阅器与asmref编译通过。原Idle无复位曲线，专用非死亡副本补Body零位及闭合复位；18复用实帧通过。r01历史两轮168/0、719帧，实看Up盖碰HP后定点将新竖向Death抬升和切线降为源0.4倍，不动原水平Body/HP。最终runtime_r02和runtime_updeath_r02各84/0、339+358=697真实PNG，最终四向/strip、12板288不同实帧和两张原尺寸死亡峰值已审，箱盖与HP有间隔；未GIF全播/全帧审。较亮平滑正面及开箱锁扣/后铰链造型待用户美术判断。AllGIF{gifs['total']}，本角色24（最终12、历史12），源/归档SHA一致。5298文件基线路径并集29变化27新增，增量unexpected0；全局历史291unexpected及6旧语义失败保持、新增0。Unity已安全交回Boot非Play/全场景非dirty、空闲、编译失败false/error0/own和generic review false。正确8088动态核对E:/MyTowerGame，8082其他工程勿动。下一唯一Troll100仅reference/not_started，19未开始可推进+PossessedWarg旧Down阻断。完整交接{rel(handoff)}；所有权看实时chain，桌面控制仍先弹对话确认。'''
handoff_text=f'''# TreasureChest(index99) 完成与下一唯一角色交接

时间：{now()}。工程E:/MyTowerGame，Unity2022.3.62f3c1，HTTP MCP {URL}。
父聊天{parent}；旧令牌{chain['dispatch_token']}。已record为completed_pending_user_art_review、user_approved=false；88/108。剩余20：19仅reference未开始，PossessedWarg阻断1。

## 最终实现和边界

生产仅Assets/Prefabs/Enemy/Enemy_TreasureChest.prefab及Assets/_UIAssets/Monsters/Inanimate/TreasureChest/Directions和目录meta。本角色专用Editor/TreasureChestDirectionAdapter.cs、TreasureChestDirectionReview.cs、FTProject.Editor.asmref参与既有FTProject.Editor程序集；共享C#完全未改。初次缺asmref的6条编译错误保存在editor_compile_result_attempt01_20261028.json，修好后完整正确8088刷新编译、scriptCompilationFailed=false/error0；最终结果editor_compile_result_20261028.json，修复请求motion_repair_revision_01/compile_request.json。
5298原文件与当前路径并集29变化27新增：28目标安装文件及未改ReporterEditor自动Play时间戳build_info。源prefab/atlas及meta、原Container clips/controller、配置表、ConfigJson/Gen、声音、其他角色保持；增量unexpected=[]。无Git同步/提交、构建部署或桌面控制。
原5 SpriteRenderer为Normal/Broken/Shadow/Bg/Fill，仅移除授权Shadow，其他4个原Sprite PPtr含HP保持；原receiver HeadRenderer=null、HeadSprites=[]。见original_sprite_contracts_20261028.json、death_reuse_contract_final_20261028.json和scope_incremental_final_20261028.json。

## 美术和请求结果

源实际审阅：金赭木、宽灰铁箍、正面方锁孔、粗深轮廓，开箱空腔/铰链盖，无脸眼牙舌四肢。策略是完整Normal/Broken状态，而不是动物分头/身/肢。Up/Down各HeadNormal闭箱、HeadAngry同闭箱兼容状态、HeadDead整箱打开；Body为透明1px兼容载体。六画布384x480，pivot(.5,0)，闭箱实际384x365，开箱匹配宽度保持相对高度，状态底线一致。
Up初次generation/Up Curl56接收重置无HTTP/raw/result；revision_01第1额外请求Curl55发送中断无HTTP/raw/result；两者结果/可能计费均不明，保留，不宣称未收费。初次console.txt明确是session22645回显摘录，非全量日志。revision_02第2额外请求HTTP200、raw1292122bytes；Down初次HTTP200、raw1291755bytes。每方向最多两次额外额度，Up已完全耗尽，不再重发；成功raw不重发。
原人类常设授权确已回读：thread01a18093-7687-7313-aaba-7419090cc829，turn01a180aa-774c-7ee3-8d35-d144e9389b9a，message01a180aa-7768-7222-bc85-7aa51e801cdd：“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”。承接结果不明网络失败、接受可能重复计费、有界补发的情况。本角色standing_recovery_application_20261028.json绑定现场及原standing授权SHA；standing原件未改。
generate.mjs保留原TLS/Tiger Curl55分支，仅额外放行TreasureChest Up rev01/rev02确切Curl56及rev02承接rev01确切Curl55；owner/token/原授权ID/SHA/console/输出在途与两次上限不变，未全局开放。参数保持gpt-image-2 images/edits、medium、1536x1024、n1、Curl HTTPS不redirect/retry、runtime-only DPAPI密钥。后继遇同类故障需核验自己的现场和授权，不能冒用TreasureChest专属分支或额度；鉴权/余额/配额不盲试。PossessedWarg旧Down未纳入此次恢复，不重发。
最终Up local_raster_revision_01/Up_sheet.png：新生成的真实后视图铰链正确但略三分之四，只镜像该新后面左半消除右侧深度，原侧面未翻造为背面，原raw保留。精确矩形/父子SHA见derivation.json。Down generation/Down/raw.png，实际3个大top单元，显式切片不假设4列。6905个Lanczos alpha1..23外缘像素仅去除，无内部填色/不透明重涂，六整物图内部透明孔0，见chroma_quality_20261028.json。暂存PNG/layout/sprites和安装一致，不重跑stage覆盖。parts_clean/offline_rig_proof/state_alignment_proof/preinstall_review已留。

## 动画、视觉返修和最终真实运行

原Container仅Idle1s loop、无float/PPtr/events；Death1/3s、8float、无PPtr/events，Body位移/欧拉摆动与Normal0/Broken1。专用适配器复制Idle/Death保留原水平keys、原事件、时长loop，额外兼容Walk/Attack .5s与Ready复用Idle；兼容SetHead攻击1/.09和0/.48、死亡2/.03不是原生事件。非Death副本补Body位置/欧拉三轴0、Normal1/Broken0，以防原Idle空曲线复用后残留。原8条Death Body曲线不改。安装Verify原契约通过，重复clone的root/HP/receiver/方向组及收集器检查通过。
r01旧两轮各84/0，共719帧，留为历史未批准版本。实际原尺寸死亡帧发现Up开盖跳跃碰未动的HP，因此motion_repair_revision_01只将新Up/Down Death Motion.y源抬升键和切线降0.4倍，保留源Body/HP和竖向原摆动。本角色Adapter同步，完整刷新编译/error0后显式RepairVerticalDeathLift、Verify通过，最终installed_manifest_r02.json共28目标文件含Editor/asmref。
最终runtime_r02：84PASS/0FAIL，339实际PNG，records SHA {runtime['runtime'][0]['records_sha256']}。
最终runtime_updeath_r02：84PASS/0FAIL，358实际PNG，records SHA {runtime['runtime'][1]['records_sha256']}。
共168/0、697真实PNG。每轮启动前已绑定最终安装/暂存/C#哈希，结束后全匹配，自然回Boot，不人工Animator.Update造片。两轮所有Death状态实帧Normalfalse/Brokentrue且正确方向HeadDead；18个Reuse实帧闭合、Body位置/Euler全0，见death_reuse_contract_final_20261028.json。
最终实际看四方向、runtime_visual_strip、visual_review_final_20261028全12板288个不同实帧和两轮DeathAutoRecycle_00181.png原768尺寸峰值；覆盖全部四向、Idle/Ready/Walk/Run、上下Attack、Hurt、双死亡淡出/回收/Reuse、Pause/Resume/2x/3x、ContinuousTurns和Flying。仅PNG时序抽样，未实时GIF全播、未全审697帧。实际观察及局限：{note}
AllGIF{gifs['total']}，TreasureChest24：最终12、历史12，所有源/归档SHA一致，见gif_archive_verification_20261028.json。

## 范围、封存和Unity释放

本角色语义通过、保护六项除battle零漂移、增量unexpected0。全局291历史unexpected及MeatBug/Monkey/MosquitoParasite/Pig/Piggy/Porky六旧失败完全保持，新增0，不能称全局PASS。
version_binding_final_20261028.json绑定原参考、所有不明/成功请求和raw、授权应用、本地派生、暂存、最终28安装文件及专用Editor/asmref、旧版返修历史、每轮预Play绑定、全部697最终PNG、实际审板与note；final_validation_20261028.json记录最终Unity与hash。新生成的record/交接调度文档在封存后建立，不冒称付费或运行证据。
释放证据{rel(release_path)}：正确8088动态custom-tools/instances选择MyTowerGame完整ID，核对E:/MyTowerGame与2022.3.62f3c1；Boot非Play/全场景非dirty、无编译/域重载/更新、ready_for_tools=true，scriptCompilationFailed=false、error0，own/generic review、balance、recording、manual全false。未强停别人任务。

## 下一唯一Troll与续接

重新评估20未完成目录，19均not_started且只有reference，无可恢复非阻断阶段，按index选Troll100；六项源/战斗/atlas及meta与全局原基线和reference一致。评估{rel(assessment_path)}。PossessedWarg原Down requestSHA不变，仍无raw/result/uncertain，不重复付费。
Troll源{target['source']}；battle{target['battle']}；atlas{target['atlas']}；controller {target['controller']}。源层级含Body/LegL/Head/ArmR/LegR/ArmL/WeaponAnchor/Weapon/FistR/AnchorStatus/BodyAnchor，必须实际审图/完整prefab、原Giant动作与武器生命周期后制定自己的解剖方案，不能照搬本宝箱整物策略或先验动物四足。
新token {token}。新聊天初期可能handoff_ready，只读等待父登记；active且owner自身/current_character=Troll/token匹配才生产/Unity/付费，不超时抢锁。
正确MCP为8088，8082当前另一个D:/FishTestGame，不用8080。根AGENTS旧D:/FreedomTower_1/8082不改变任务显式路由。默认复用mcp_call.py动态身份；仅stale_status可用既有短ForceUpdate更新真实缓存，不改flags。桌面控制仍须先弹对话确认。自己的两轮Play已有授权，参与编译C#改动必须正确工程刷新/编译/日志闭环。
不fork/子代理/并行角色/计时器/模型推理覆盖；不Git pull/reset/clean/checkout/commit/push、构建部署；不改配置表、ConfigJson/Gen、声音、其他角色或共享C#。完成或准确真实阻断后完整交接/更新README/prompt/NEXT/progress、释放Unity、动态list_projects并仅建一个全新本地后继；明确创建响应保存，所有权登记是父最后工作区写入，之后仅一次有界wait。按原人类串行循环授权继续至108有效完成或只剩真实阻断，不待逐角色确认，不把待用户美术审核写为批准。
'''
next_text=f'''# 下一唯一角色 Troll(index100)

工程E:/MyTowerGame，Unity2022.3.62f3c1；父{parent}已record TreasureChest99，88/108，user_approved=false。
唯一dispatch_token：`{token}`。

## 开工和唯一所有权

先读E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md；再读Docs/EnemyDirectionReview/Remaining_20261024中的REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、本NEXT、conversation_chain.json和实时progress.json、standing_network_recovery_authorization_20261028.json及TreasureChest/standing_recovery_application_20261028.json；完整前任交接{rel(handoff)}、队列评估{rel(assessment_path)}。
只有chain.state=active、owner_thread_id为自身、current_character=Troll、token完全一致才可生产/Unity/付费；handoff_ready只读等待父登记，不超时抢锁。不fork/子代理/并行角色/计时器/模型推理覆盖。

## Troll现场和完整执行

仅reference/not_started；原六文件与基线/reference一致，没有anatomy、generation/request/raw/stage/install/runtime。源{target['source']}；battle{target['battle']}；atlas{target['atlas']}；controller {target['controller']}。层级提示Body/Head/双Leg/Arm/WeaponAnchor/Weapon/FistR等，先实际审原图、完整prefab、Giant原动作/事件/武器与池化生命周期，建立自己的增量基线，保护已有git改动。不能照搬宝箱的整物载体或猜四足。
按原prompt：源审阅→一方向正式生成并实看raw→另一方向→透明分件/pivot/布局并实看→单角色安装Verify→普通和Up死亡两轮真实Play各84检查→1至2图分次审四向、移动、攻击/武器、受击、死亡复用、暂停/恢复/倍速、转向/飞行→UTF8 note/record/GIF归档→原请求/派生/暂存/安装/全部实际帧版本绑定及前后路径并集审计。只completed_pending_user_art_review/user_approved=false；如实说明PNG采样范围，不声称GIF全播/全帧审。
默认generate_character.ps1/Curl、gpt-image-2 images/edits medium1536x1024 n1、HTTPS证书检查、无redirect/retry、runtime-only密钥及输出/在途门禁保持。先查成功/在途/uncertain，不重付费；不删安装清单绕保护、不盲重跑prepare/stage/install。普通角色不用Mounted专属AuthorizedResume。
同类结果不明网络失败已有原人类常设静默有界恢复授权，接受可能重复计费、每方向最多2次额外新revision。详情原standing授权和TreasureChest应用含原人类消息ID/SHA。generate.mjs只含原TLS、Tiger确切Curl55及TreasureChest确切Curl56/Curl55角色专属分支，后继故障先核验自己的现场和授权，不直接冒用前角色身份/额度。TreasureChest Up两次额外已用尽；PossessedWarg旧Down不在恢复范围，保留不重发。鉴权/余额/配额不盲试。

## Unity和前任证据

正确http://127.0.0.1:8088/mcp，复用mcp_call.py；每次动态custom-tools/instances→选现场MyTowerGame完整ID→project/info确认E:/MyTowerGame和2022.3.62f3c1。8082是D:/FishTestGame，8080是CatchFish，禁止误操作；根AGENTS旧D盘/8082不改变显式任务目标。先error、状态、全场景dirty与Play/编译/review/录制/manual占用，不能强停别人；仅stale_status可用既有短ForceUpdate读真实缓存。自有Play已有授权，C#改动须完整正确工程刷新/编译/日志验证；桌面控制仍需先弹对话确认。
TreasureChest最终installed_manifest_r02包含目标Editor/asmref，原4非Shadow含HP PPtr与源Container/共享C#保持；副本闭合复位经18Reuse帧量测。r01历史719帧盖碰HP，最终竖向死亡抬升降0.4，原水平Body/HP不变。最终两轮各84/0，339+358=697真实帧；实看四向/strip、12板288不同帧和2死亡峰值原尺寸，盖避开HP，未GIF全播/逐张全审。最终12GIF+历史12全部归档，全库{gifs['total']}。Down更亮平滑及锁扣/铰链细节待用户美术判断。Up最初Curl56和rev01 Curl55仍结果不明/可能计费，rev02HTTP200；Down初次HTTP200，所有原件保留。不可重跑前任stage/installation或付费。范围新增越界0，291历史unexpected及6旧语义失败保持，不称全局PASS；最终验证和版本封存在TreasureChest/final_validation_20261028.json及version_binding_final_20261028.json。Unity已释放Boot非Play/非dirty/空闲/error0，证据{rel(release_path)}。

## 串行续接

禁止配置表、Assets/ConfigJson/Gen、声音、其他角色与共享C#改动；不Git同步/提交、构建部署。完成或准确真实阻断后重评实时队列，优先可恢复非阻断再index，写全新时间戳交接、更新README/prompt/NEXT/progress、释放Unity；按CONTINUATION_PROTOCOL动态list_projects，只建一个全新本地后继，保存明确响应，登记所有权作为父最后工作区写入，之后停止写入并一次有界wait。用户已授权循环到108有效完成或仅剩真实阻断，不等待逐角色再确认，不把继续授权当用户美术批准。
'''
prompt=f'''在E:/MyTowerGame接棒敌人四方向串行任务，只处理Troll(index100)。父聊天{parent}完成TreasureChest99，当前88/108，仍待用户美术审核/user_approved=false。
先读E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md；再读Docs/EnemyDirectionReview/Remaining_20261024下REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、NEXT_ENEMY_TASK.md、conversation_chain.json、实时progress.json、standing_network_recovery_authorization_20261028.json和TreasureChest/standing_recovery_application_20261028.json；完整交接{rel(handoff)}和队列评估{rel(assessment_path)}。路径均相对E:/MyTowerGame。
唯一dispatch_token：{token}。创建初期可能handoff_ready，只读等父登记；仅active/owner自身/current_character=Troll/token严格一致才生产/Unity/付费，不超时抢锁。
正确MCP http://127.0.0.1:8088/mcp，复用mcp_call.py动态custom-tools/instances→set现场MyTowerGame完整ID→project/info核对E:/MyTowerGame/Unity2022.3.62f3c1。暴露unityMCP工具可能仍8082/D:/FishTestGame，不误操作，禁8080。根AGENTS旧D:/FreedomTower_1/8082不变更当前显式目标。先error/状态/全场景dirty/Play/编译/review/录制/manual占用，只stale_status可既有短ForceUpdate真实缓存，不改flags。自有两轮Play有授权，C#改动完整MCP编译验证，桌面控制仍先弹对话确认。
Troll仅reference/not_started，六原文件与reference/基线一致，无prepare/request/raw/stage/install/runtime。源{target['source']}；battle{target['battle']}；atlas{target['atlas']}；controller {target['controller']}。源层级含Body/Head/双Leg/Arm/WeaponAnchor/Weapon/FistR，先审真实原图/完整prefab、Giant事件/武器/池化生命周期并建立自己的生产增量基线，保护现有git改动，不套宝箱整物载体或猜动物四足。严格原prompt逐阶段源审阅、两方向正式生成及实看raw、透明分件/pivot/布局、单角色安装Verify、两轮真实Play各84检查、1至2图分次视觉审阅（四向/移动/攻击武器/受击/死亡复用/暂停倍速/转向飞行）、UTF8 note record/GIF、从原请求至全部真实帧SHA绑定和前后路径并集审计。只completed_pending_user_art_review/user_approved=false，PNG抽样如实描述，不称GIF全播/全帧审。
默认Curl/gpt-image-2 images/edits medium1536x1024 n1及HTTPS/no redirect/retry、runtime-only密钥、输出在途门禁保持，先查已有成功/在途/uncertain，不重复付费，不删安装清单或盲重跑。普通角色不用Mounted专属授权。同类不明网络故障已有原人类常设静默有界恢复、接受可能重复计费、每方向最多2额外新revision，原消息ID和SHA见standing授权及前任应用。generate.mjs仅原TLS/Tiger Curl55/TreasureChest确切Curl56及Curl55角色专属分支；新故障需核验自己的证据和授权，不能冒用前角色身份或额度。TreasureChest Up两次已耗尽。鉴权/余额/配额不盲试；PossessedWarg旧Down仍保留结果不明、不重发、不做探针。
前任TreasureChest为无脸肢宝箱，原Container Normal/Broken整物状态，专用Editor适配/审阅器和asmref已编译通过，原4非Shadow含HP PPtr及源/共享C#不变。r01历史719帧发现Up开盖碰HP，最终仅新竖向Death lift键/切线降源0.4倍，原Body/HP不改；18Reuse实帧闭合与Body位置/Euler零。最终installed_manifest_r02与两轮预Play绑定一致，runtime_r02和runtime_updeath_r02各84/0，339+358=697真PNG，实看四向/strip、12板288不同实帧和2原尺寸死亡峰值，盖与HP有间隔；未GIF全播/全帧审。24GIF含最终12/历史12，AllGIF{gifs['total']}。正面更亮平滑、锁扣/后铰链细节待用户美术审核。Up初次Curl56及额外r01 Curl55仍结果/计费不明、r02 HTTP200，Down初次HTTP200，全原证据保留。5298基线路径并集29变化27新增，新增越界0；全局291历史unexpected与6旧语义失败不变，不称全局PASS。Unity已安全释放Boot非Play/全场景非dirty/空闲/error0/编译失败false。
不fork/子代理/并行角色/计时器/模型推理覆盖，不Git同步/提交、构建部署，不改配置表、ConfigJson/Gen、声音、其他角色或共享C#。按原人类明确循环授权，角色完成或真实阻断后完整交接、重评队列、更新README/prompt/NEXT/progress、释放Unity，动态list_projects仅建一个全新本地后继；保存明确创建响应、登记所有权为父最后工作区写入，之后停止写入，一次有界wait。持续至108有效完成或仅剩真实阻断，不等逐角色再确认，不把继续授权当美术批准。'''
updates={}
for path,marker in [(H.parent/'README.md','ENEMY_README_LIVE'),(H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','ENEMY_SERIAL_LIVE_STATE')]:
    text=path.read_text(encoding='utf-8');pattern=r'<!-- '+marker+r'_BEGIN -->.*?<!-- '+marker+r'_END -->';assert len(re.findall(pattern,text,re.S))==1
    text=re.sub(pattern,'<!-- '+marker+'_BEGIN -->\n'+live+'\n<!-- '+marker+'_END -->',text,flags=re.S)
    if path.name=='README.md':text=re.sub(r'2026-10-28 本轮当前清单为 \d+ 个文件',f'2026-10-28 本轮当前清单为 {gifs["total"]} 个文件',text)
    updates[path]=text
write(assessment_path,dict(observed_at=now(),progress_completed_count=88,unfinished=assessment,blocked_preserved=blocked,possessed_warg_down_request_sha256=sha(down/'request.json'),missing_outcome_unchanged=True,available_count=len(available),chosen=successor,target=target,chosen_protected_six=six,protected_drift=[],reason='No recoverable nonblocked stages. Lowest reference-only not_started is Troll100; PossessedWarg uncertain Down preserved without resend.'))
write(release_path,dict(observed_at=now(),transport=URL,project=project,state=state,cache_refresh=cache_refresh,errors=errors,live=released,own_review=own_review,protocol_history=client.history,note='Final own r02 rounds already naturally returned. No forced Play exit/desktop. Target C# compiled and passed before final rounds; no later production edits.'))
handoff.write_text(handoff_text,encoding='utf-8')
for path,text in updates.items():path.write_text(text,encoding='utf-8')
(H/'NEXT_ENEMY_TASK.md').write_text(next_text,encoding='utf-8');progress.update(current='Troll',updated_at=now());write(H/'progress.json',progress);prompt_path.write_text(prompt+'\n',encoding='utf-8')
write(dispatch_path,dict(prepared_at=now(),parent_thread_id=parent,next_character='Troll',dispatch_token=token,handoff_file=rel(handoff),assessment_file=rel(assessment_path),unity_release_file=rel(release_path),prompt=prompt,prompt_file=rel(prompt_path),progress_sha256=sha(H/'progress.json'),handoff_sha256=sha(handoff),created=False))
assert handoff.read_text(encoding='utf-8')==handoff_text and (H/'NEXT_ENEMY_TASK.md').read_text(encoding='utf-8')==next_text
chain.setdefault('completed_handoffs',[]).append(dict(character=NAME,status=item['status'],current_stage='recorded_pending_user_art_review',owner_thread_id=parent,dispatch_token=chain['dispatch_token'],closed_at=now(),handoff_file=rel(handoff),final_evidence='Docs/EnemyDirectionReview/Remaining_20261024/TreasureChest/final_validation_20261028.json'))
chain.update(state='handoff_ready',parent_thread_id=parent,current_character='Troll',character_status_at_handoff='not_started',completed_count_snapshot=88,previous_handoff_file=chain['last_handoff_file'],last_handoff_file=rel(handoff),dispatch_token=token,progress_sha256_at_handoff=sha(H/'progress.json'),handoff_sha256=sha(handoff),unity_release_file=rel(release_path),successor_assessment=rel(assessment_path),prepared_dispatch_file=rel(dispatch_path),current_stage='handoff_ready_for_fresh_local_successor',handoff_ready_at=now(),updated_at=now(),blocked_reason=None,current_blocked=False,mcp_endpoint=URL,successor_created=False,dispatch_ready_for='Troll',resume_character='Troll',resume_stage='Inspect source Giant anatomy/weapon lifecycle and establish own baseline',ownership_transfer_note='TreasureChest recorded and Unity safely released on8088. No production during handoff_ready; await one fresh local Troll chat and explicit registration.')
write(H/'conversation_chain.json',chain)
print(json.dumps(dict(state=chain['state'],next_character='Troll',token=token,handoff_file=rel(handoff),dispatch_file=rel(dispatch_path),progress=88,release=released),ensure_ascii=False))
