"""Release Troll and prepare one fresh local Turkey successor, without dispatching it."""
from session_troll import *
import time,uuid

chain=owner();parent=os.environ['CODEX_THREAD_ID'];progress=read(H/'progress.json');assert progress['completed_count']==89
item=next(x for x in progress['items'] if x['name']==NAME)
assert item['status']=='completed_pending_user_art_review' and item['user_approved'] is False and item['visual_reviewed']
binding=read(D/'version_binding_final_20261028.json')
assert all(sha(D/p)==s for p,s in binding['files'].items())
assert all(sha(R/p)==s for key in ['installed_files','production_scope_files','external_evidence'] for p,s in binding[key].items())
assessment=[]
for candidate in sorted((x for x in progress['items'] if x['status'] not in ['completed_pending_user_art_review','user_approved']),key=lambda x:x['index']):
    folder=H/candidate['name'];files=sorted(p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file())
    assessment.append(dict(index=candidate['index'],name=candidate['name'],status=candidate['status'],files=files,checkpoints=[p for p in ['anatomy_plan.json','installed_manifest.json','runtime_summary.json'] if (folder/p).is_file()],raw=[p for p in files if p.endswith('/raw.png')],runtime_directories=[p.name for p in folder.glob('runtime*') if p.is_dir()],blocked_reason=candidate.get('blocked_reason')))
blocked=[x for x in assessment if x['status']=='blocked'];available=[x for x in assessment if x['status']!='blocked']
assert len(assessment)==19 and len(blocked)==1 and blocked[0]['name']=='PossessedWarg'
assert len(available)==18 and all(x['status']=='not_started' and not x['checkpoints'] and not x['raw'] and not x['runtime_directories'] and all(p.startswith('reference/') for p in x['files']) for x in available)
successor=available[0];assert successor['name']=='Turkey' and successor['index']==101
blocked_item=next(x for x in progress['items'] if x['name']=='PossessedWarg');blocked_record=read(R/blocked_item['blocked_record']);down=H/'PossessedWarg/generation/Down'
assert sha(down/'request.json')==blocked_record['request_sha256']=='B2B3C9FB4B78E2FFB5E606FCE95BB2843575982CADBE6C6E97D352346D27BA4A'
assert not any((down/p).exists() for p in ['raw.png','result.json','uncertain_result.json'])
target=next(x for x in read(H/'local_baseline.json')['targets'] if x['name']=='Turkey')
paths=[target['battle'],target['battle']+'.meta',target['source'],target['source']+'.meta',target['atlas'],target['atlas']+'.meta'];original=read(H/'production_fingerprints_before.json');six={p:sha(R/p) for p in paths}
assert all(six[p]==original[p].upper() and sha(H/'Turkey/reference'/Path(p).name)==six[p] for p in paths)
client=Client();project=client.identity();errors=unwrap(client.tool('read_console',dict(action='get',types=['error'],count='50',format='json')));assert errors['data']==[]
cache_refresh=None
for attempt in range(4):
    state=client.resource('mcpforunity://editor/state');s=state['data']
    if not s['compilation']['is_compiling'] and not s['compilation']['is_domain_reload_pending'] and not s['assets']['is_updating'] and s['advice']['ready_for_tools']:break
    if attempt==0 and s['advice'].get('blocking_reasons')==['stale_status']:
        cache_refresh=unwrap(client.tool('execute_code',dict(action='execute',code='var t=typeof(MCPForUnity.Editor.Resources.Editor.EditorState).Assembly.GetType("MCPForUnity.Editor.Services.EditorStateCache");t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Static).Invoke(null,new object[]{"Troll_handoff_live_state_read"});return true;')))
    time.sleep(1)
else:raise RuntimeError('Unity not ready to release')
released=probe(client)
scenes=unwrap(client.tool('execute_code',dict(action='execute',code='return System.Linq.Enumerable.ToArray(System.Linq.Enumerable.Select(System.Linq.Enumerable.Range(0,UnityEngine.SceneManagement.SceneManager.sceneCount),i=>new{path=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).path,dirty=UnityEngine.SceneManagement.SceneManager.GetSceneAt(i).isDirty}));')))['data']['result']
assert released['scene']=='Assets/Scenes/Boot.unity' and not any(v for k,v in released.items() if k!='scene') and scenes and all(not x['dirty'] for x in scenes)
stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S');token='troll-to-turkey-'+uuid.uuid4().hex
rel=lambda p:p.relative_to(R).as_posix()
handoff=H/'conversation_handoffs'/(stamp+'_Troll_completed.md')
release_path=D/('handoff_release_'+stamp+'.json');assessment_path=D/('successor_assessment_'+stamp+'.json');dispatch_path=D/('successor_dispatch_'+stamp+'.json');prompt_path=D/('successor_prompt_'+stamp+'.txt')
assert not any(p.exists() for p in [handoff,release_path,assessment_path,dispatch_path,prompt_path])
gifs=read(D/'gif_archive_verification_20261028.json');assert gifs['all_gif_after']==read(H.parent/'AllGIF/manifest.json')['count']==1426
scope=read(D/'scope_incremental_final_20261028.json');runtime=read(D/'runtime_summary.json');note=(D/'record_note_utf8.txt').read_text(encoding='utf-8').strip()
live=f'''2026-10-28 Troll100已record，89/108，completed_pending_user_art_review、user_approved=false。金赭斑点双足巨人、左耳单环/三牙项链/螺旋扣/右手石锤，Up真实无脸后视，Down正常/怒/死状态。Up和Down初次各HTTP200；Down躯干纠偏revision_01 Curl55结果/可能计费不明，未网络重试。最终Up原raw，Down本地r05只纠正新生成正面躯干，保留同图完整项链和扣，拒绝稿及原请求全保留。14透明分件、实测肩pivot/双腿；148个零alpha内部微孔近邻填补，原opaque/AA不变，最终内部孔0。原11Sprite保留10非Shadow含HP PPtr，仅移除Shadow；源prefab/atlas/Giant原动作和全部共享C#不变，安装Verify原水平曲线/事件/时长loop通过。两轮runtime_r01/runtime_updeath_r01各84/0，362+360=722真实PNG，前后安装/暂存/直接代码hash一致，自然回Boot。实际审四向/strip、12板288不同实帧和6张原尺寸攻击/死亡图；未GIF全播/全帧审。Up挥锤峰值被躯干遮挡、锤头显于腿间，较原侧面更窄直立及对称斑点/柔化待用户美术判断。AllGIF1426，Troll12全为当前审核版且源/归档SHA一致。5325文件并集22变化20新增，增量unexpected0；全局291历史unexpected及6旧语义失败保持、新增0，不称全局PASS。正确8088动态核对E:/MyTowerGame，Unity2022.3.62f3c1；已安全释放Boot非Play/全场景非dirty/空闲/编译失败false/error0。下一唯一Turkey101仅reference/not_started，18未开始可推进+PossessedWarg旧Down阻断。交接{rel(handoff)}；所有权看实时chain，桌面控制仍先弹对话确认。'''
handoff_text=f'''# Troll(index100) 完成与下一唯一角色交接

时间：{now()}。工程E:/MyTowerGame，Unity2022.3.62f3c1；HTTP MCP {URL}。
父聊天{parent}；原令牌{TOKEN}。已record：completed_pending_user_art_review，user_approved=false，89/108。剩余19项：18未开始可独立推进，PossessedWarg旧Down结果不明阻断1。

## 最终资源、版本与范围

仅生产Assets/Prefabs/Enemy/Enemy_Troll.prefab及Assets/_UIAssets/Monsters/Giants/Troll/Directions和目录meta。最终installed_manifest.json的20项加Directions根目录meta，共21项目标；另ReporterEditor未改而Play自动更新Assets/StreamingAssets/build_info时间戳。5325文件基线与当前路径并集22变化、20新增、0删除、unexpected_incremental=[]。全部共享C#、源prefab/atlas及meta、原Giant clips/controller、配置表、ConfigJson/Gen、声音及其他角色不变。原11个SpriteRenderer保留10非Shadow含HP原PPtr，只移除Shadow；original_sprite_contracts_20261028.json和scope_incremental_final_20261028.json有精确指纹和语义。安装Verify=true，原Ready/Walk/Attack/Death水平float曲线、事件、时长loop及重复clone root/HP/receiver检查通过。不重新install/stage。
战斗prefab最终SHA：{binding['installed_files']['Assets/Prefabs/Enemy/Enemy_Troll.prefab']}。
安装清单SHA：{sha(D/'installed_manifest.json')}。
最终封存SHA：{sha(D/'version_binding_final_20261028.json')}。
最终验证SHA：{sha(D/'final_validation_20261028.json')}。

## 美术与付费请求

源实际为秃头金赭斑点双足巨人，尖耳、解剖左耳单灰环、琥珀眼、锯齿常态嘴，怒张嘴小牙/死亡空圆眼，三牙项链、椭圆螺旋扣、破边围布、腕带、前足三牙色趾甲，解剖右手一把木柄灰白石锤；无头发/角/尾。原ArmR/FistR/Weapon层级保留给横向；竖向把手臂与石锤作一个完整生成sprite，另一臂独立，双腿错相。
Up初次HTTP200，raw1403089bytes；Down初次HTTP200，raw1469660bytes。Down躯干略三分之四，定点纠偏generation/Down/revision_01遇Curl55 Send failure Connection was reset，无HTTP/raw/result，结果及可能计费未知。request、intent、uncertain及完整Tee console保留；没有网络补发。常设有界网络恢复授权存在但本角色没有套用恢复分支，不能声称失败未计费，也不要为本已完成角色补发该请求。
最终Up选generation/Up/raw.png；Down选local_raster_revision_05/Down_sheet.png，头臂腿来自成功原raw，仅生成正面躯干局部纠偏。r05基于r02轴向warp，镜像生成正面右半，保留同图完整三牙项链/椭圆螺旋扣，局部mask和微小边缘插值；没有用原侧图伪造正背。r01横纹、r03底色误mask、r04硬接缝等否决稿全部留盘。最终14透明切片/肩pivot/腿比例已实际审；148个封闭零alpha微孔（最大组件12）用最近原opaque像素修复，所有原opaque/AA不变，14片内部孔0。默认800px离线proof框裁到极端锤尖，wide proof和真实运行全锤完整，并非生产切片截断。

## 两轮真实运行与实际视觉范围

runtime_r01：84PASS/0FAIL，362真实PNG，records SHA {runtime['runtime'][0]['records_sha256']}。
runtime_updeath_r01：84PASS/0FAIL，360真实PNG，records SHA {runtime['runtime'][1]['records_sha256']}。
共168/0、722真实PNG，每轮启动前独立绑定最终安装/暂存/直接共享实现hash，结束全匹配；自然退出Play恢复Boot，没有人工Animator.Update造帧。全部记录shadow=false；双向Death表情2/alpha递减，18个Reuse恢复alive/表情0/alpha1/flash0/speed1；Pause12+12张simulationDelta0。见lifecycle_contract_final_20261028.json及两轮_version_binding_before/_returned文件。
实际看runtime_r01/four_directions、runtime_visual_strip、visual_review_final_20261028全12板（288采样位/288不同实际帧），另两轮各UpAttack峰值/DownAttack峰值/Death淡出6张原768PNG。源帧/板SHA、状态/时间/朝向绑定在sources.json和review.json。未声称播放全GIF或逐张审完722帧。
原样UTF8审阅备注：{note}
AllGIF1426，本角色12均当前审核版本，源/归档SHA相同；gif_archive_verification_20261028.json。技术和内部视觉完成不等于用户批准。

## 范围审计与Unity释放

本角色语义通过、保护六项除目标battle零漂移、暂存/安装无drift，新增越界0。全局仍291历史unexpected及MeatBug/Monkey/MosquitoParasite/Pig/Piggy/Porky六旧语义失败，与本轮before完全相同；不能称全局PASS。
version_binding_final_20261028.json绑定原参考、成功与uncertain请求/raw、本地派生/否决稿、微孔修补、暂存、安装、两轮预Play/返回、全部722PNG、实际审板/note。记录/归档/后续交接文档在封存后新增，不冒充原生成或运行证据。
释放证据{rel(release_path)}：重新动态custom-tools/instances选MyTowerGame完整ID，project/info核对E:/MyTowerGame与2022.3.62f3c1。当前Boot非Play、全部场景非dirty、无编译/重载/更新，ready_for_tools=true，scriptCompilationFailed=false/error0，review/balance/recording/manual=false。没有强停别人的任务。8082为其他工程，8080为CatchFish，禁止借用；根AGENTS旧FreedomTower/D盘/8082不覆盖本任务。

## 下一唯一Turkey与调度

重新读取实时progress和所有未完成目录，没有可恢复且非阻断的已开始角色。18项仅reference/not_started，按index选择Turkey101；其六项battle/source/atlas及meta与原global baseline和reference一致。评估{rel(assessment_path)}。PossessedWarg原Down request SHA仍B2B3C9FB4B78E2FFB5E606FCE95BB2843575982CADBE6C6E97D352346D27BA4A，无raw/result/uncertain，保留阻断且不重发或拿它探测。
Turkey源{target['source']}；battle{target['battle']}；atlas{target['atlas']}；controller {target['controller']}。登记节点为{', '.join(target['nodes'])}，仅作定位。后继必须实际审原图/完整prefab、原Turkey动画/事件/尾翅层级及BaseEnemy池化生命周期，不能套Troll双臂石锤/Giant曲线或凭通用鸟类模板猜尾/脚/翅。
下一令牌{token}。父将先chain=handoff_ready，再动态list_projects仅建一个fresh local Turkey新聊天，保存明确响应后登记active/child owner作为父最后工作区写入。此前子只读等待；登记后父停止全部写入，最多一次有界wait_threads。无fork/子代理/并行角色/计时器/模型推理覆盖，无Git同步提交、构建部署、表格或共享C#改动。桌面控制仍需先弹确认对话。完成下一角色后沿同协议主动单一续接到108有效完成或只剩真实阻断，用户美术仍待审。
'''
next_text=f'''# 下一唯一角色 Turkey(index101)

工程E:/MyTowerGame，Unity2022.3.62f3c1；父{parent}已record Troll100，89/108，completed_pending_user_art_review、user_approved=false。
唯一dispatch_token：`{token}`。

## 开工和所有权

先读E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/README.md；再读Remaining_20261024中的REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、本NEXT、conversation_chain.json和实时progress.json、standing_network_recovery_authorization_20261028.json及TreasureChest/standing_recovery_application_20261028.json；完整交接{rel(handoff)}，队列评估{rel(assessment_path)}。
只有chain.state=active、owner_thread_id为自身、current_character=Turkey、token完全一致才可生产/Unity/付费。handoff_ready只读等待父登记，不超时抢锁。不fork/子代理/并行角色/计时器/模型推理覆盖。

## Turkey现场与执行流程

仅reference/not_started；原六文件与global baseline及reference一致，无anatomy、request/raw、stage/install/runtime。源{target['source']}；battle{target['battle']}；atlas{target['atlas']}；controller {target['controller']}。登记层级{', '.join(target['nodes'])}只作定位。先实际审原atlas、完整源prefab/战斗层级、Turkey原动作/事件/尾翅/脚和池化生命周期，制定自己的解剖和动画方案，不能照搬Troll/Giant或其他鸟角色。建立自己的路径并集增量基线，保护既有git脏改动。
按原prompt：源审阅→正式生成一方向并实看raw→另一方向→透明分件/pivot/布局实看→单角色安装Verify→普通和Up死亡两轮真实Play各84检查→1至2图分次审四向/移动/攻击/受击/死亡复用/暂停恢复倍速/转向飞行→UTF8 note/record/GIF归档→原请求/派生/暂存/安装/全部实际帧封存和路径并集审计。只completed_pending_user_art_review/user_approved=false；准确写PNG抽样范围，不称GIF全播/全帧审。
默认generate_character.ps1/Curl、gpt-image-2 images/edits、medium1536x1024、n1，HTTPS证书/无redirect retry/runtime-only DPAPI密钥与在途/输出门禁保持。已有成功/uncertain先查，不重复付费，不删manifest绕保护，不盲重prepare/stage/install。普通角色不用Mounted专属AuthorizedResume。
同类uncertain网络失败已有原人类静默有界恢复授权，接受可能重复收费、每方向最多2次额外新revision；必须读原standing授权及应用的原人类消息ID/SHA。generate.mjs现有TLS/Tiger/TreasureChest角色专属分支不可冒用；核验Turkey自己的失败现场和边界再处理。鉴权/余额/配额不盲试。PossessedWarg旧Down不在恢复范围，保留不重发。

## Unity路由与释放

正确{URL}，复用mcp_call.py。每次动态custom-tools/instances→选择现场MyTowerGame完整ID→project/info确认E:/MyTowerGame和2022.3.62f3c1。8082是其他工程，8080是CatchFish；根AGENTS旧FreedomTower/D盘/8082不能覆盖本任务。先error、editor/state、全部场景dirty和Play/编译/review/录制/manual占用，不强停别人。仅stale_status可用已有短ForceUpdate更新真实缓存，不改状态flags。自有两轮Play已授权，C#改动必须正确工程完整刷新/编译/日志验证。桌面控制仍需先弹对话确认。
父刚安全释放Boot非Play/全部场景非dirty/空闲/编译失败false/error0，证据{rel(release_path)}。后继仍需现场重核。

## Troll已完成证据和局限

最终installed_manifest.json/Up原raw/Down本地r05，14分件；原10非Shadow含HP PPtr保留，源/Giant/共享C#未动。Down纠偏付费revision01 Curl55结果及可能计费未知，无网络重试，复用成功初图本地纠偏，拒绝稿全保留；148微孔修补且原opaque/AA不变。两轮各84/0、362+360=722真实PNG；实审四向/strip、12板288不同帧和6张原尺寸攻击死亡图。Up挥锤峰值手臂被背/围布遮挡、锤头显于腿间，较原侧面更窄直立、对称斑点/柔化待用户判断。AllGIF1426、Troll12源/归档hash一致；5325基线路径并集22变化20新增，增量unexpected0；历史291unexpected/6旧语义失败不变，不称全局PASS。详见Troll/final_validation_20261028.json、version_binding_final_20261028.json、scope_incremental_final_20261028.json、visual_review_final_20261028/review.json。不重新安装/生成Troll或其他完成角色。

## 串行续接

禁止关卡/敌人数值表、ConfigJson/Gen、声音、其他角色及共享C#改动；不Git同步提交、构建部署。完成或记录真实阻断后重读实时items和目录阶段，优先可恢复非阻断再index，不盲progress.current；18未开始+PossessedWarg旧阻断当前只是快照。写全新时间戳完整交接，更新README/prompt/NEXT/progress并安全释放Unity；按协议动态list_projects，只创建一个fresh local后继，保存明确响应，再登记所有权作为父最后工作区写入；之后停止全部写入并一次有界wait。用户授权循环至108有效完成或只剩真实阻断，无需逐角色再确认，不把授权当用户美术批准。
'''
prompt=f'''在E:/MyTowerGame继续敌人四方向串行续作，本聊天只负责Turkey(index101)。这是原人类授权循环的唯一全新local后继，不是并行子任务。
父{parent}已完成Troll100，89/108，completed_pending_user_art_review，user_approved=false。请先完整读取以下磁盘文件，不继承旧图片历史：
E:/MyTowerGame/AGENTS.md
E:/MyTowerGame/ProjectSettings/ProjectVersion.txt
E:/MyTowerGame/Docs/EnemyDirectionReview/README.md
E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md
E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/CONTINUATION_PROTOCOL_20261026.md
E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/IMAGE_RELAY_RECOVERY_20261026.md
E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/NEXT_ENEMY_TASK.md
E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/conversation_chain.json
E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/progress.json
E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/standing_network_recovery_authorization_20261028.json
E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/TreasureChest/standing_recovery_application_20261028.json
E:/MyTowerGame/{rel(handoff)}
E:/MyTowerGame/{rel(assessment_path)}
唯一dispatch_token={token}。只有chain.state=active、owner_thread_id为自身、current_character=Turkey且token一致后才能生产/Unity/付费。若handoff_ready，先只读同步并等待父登记；不能超时抢锁。

Turkey只有reference/not_started，六源/战斗/atlas及meta与原基线和reference一致，无anatomy/generation/stage/install/runtime。源{target['source']}，battle{target['battle']}，atlas{target['atlas']}，controller {target['controller']}；先实际审原图/完整prefab、尾翅脚层级、原动作/事件和池化生命周期，不照搬Troll或其他鸟模板。建立自己的增量基线，保护既有未提交改动；生成一方向并审阅后再另一方向、分件布局实看、单角色安装Verify、两轮真实Play各84、分批实际PNG审阅、UTF8 note/record/GIF及版本封存/路径并集审计，不只分析或写文档。

正确Unity2022.3.62f3c1/{URL}，复用mcp_call.py动态custom-tools/instances→选现场MyTowerGame完整ID→核对E:/MyTowerGame与版本。8082其他工程、8080 CatchFish，禁止误用；根AGENTS旧FreedomTower/D盘/8082不覆盖显式目标。前任已释放Boot非Play/全场景非dirty/空闲/编译失败false/error0，仍需现场核对。只own Play已授权；桌面控制必须先弹确认对话，不自行使用。

Troll最终两轮168/0，722真实PNG，实审12板288不同帧+6张原尺寸攻击/死亡和四向/strip；未GIF全播/全帧审。Up原raw、Down本地r05只纠正新生成正面躯干；Down correction revision01 Curl55结果/可能计费未知，无网络重试；成功初图和全部否决稿/请求保留，不再付费或重装已完成Troll。后向挥锤遮挡/锤头腿间、较侧面窄直立和对称斑点仍待用户美术判断。AllGIF1426、本角色12均hash匹配。增量unexpected0，历史291unexpected/6其他角色语义失败保持，不能称全局PASS。

同类uncertain网络失败常设静默有界恢复授权已有人类证据，接受可能重复收费、每方向最多2次额外新revision；必须核验自身现场和原授权，不冒用generate.mjs原角色专属分支/额度。鉴权余额配额不盲试。PossessedWarg旧Down仍blocked、不重发不探测。
无fork/子代理/并行角色/计时器/模型或推理覆盖；不Git同步提交、构建部署，不改配置表/ConfigJson/Gen/声音/其他角色/共享C#。实际图每次1到2张，证据原件留盘，不声称用户批准。结束本唯一角色后按CONTINUATION_PROTOCOL写全新完整交接、更新README/prompt/NEXT/progress并释放Unity，动态list_projects只建一个fresh local后继、保存明确响应后登记所有权作为父最后工作区写入，再停止全部写入并一次有界wait；按原用户授权循环至108有效完成或只剩真实阻断，不等逐角色确认。
'''
write(release_path,dict(observed_at=now(),transport=URL,project=project,state=state,cache_refresh=cache_refresh,errors=errors,live=released,all_scenes=scenes,protocol_history=client.history))
write(assessment_path,dict(observed_at=now(),completed=89,authorized=108,unfinished=assessment,blocked_names=['PossessedWarg'],available_count=18,next_unique=successor,target=target,protected_six=six,old_possessedwarg_down_request_sha256=sha(down/'request.json'),selection_rule='No started recoverable nonblocked character; choose minimum index among reference-only not_started',source_production_unchanged=True))
handoff.write_text(handoff_text,encoding='utf-8');prompt_path.write_text(prompt,encoding='utf-8')
for p,start,end in [(H.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),(H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    text=p.read_text(encoding='utf-8');assert text.count(start)==text.count(end)==1
    text=re.sub(re.escape(start)+r'.*?'+re.escape(end),lambda m:start+'\n'+live+'\n'+end,text,flags=re.S);p.write_text(text,encoding='utf-8')
(H/'NEXT_ENEMY_TASK.md').write_text(next_text,encoding='utf-8')
item.update(final_validation_file=rel(D/'final_validation_20261028.json'),version_binding_file=rel(D/'version_binding_final_20261028.json'),scope_file=rel(D/'scope_incremental_final_20261028.json'),visual_review_file=rel(D/'visual_review_final_20261028/review.json'),gif_archive_file=rel(D/'gif_archive_verification_20261028.json'),handoff_file=rel(handoff),final_stage='recorded_pending_user_art_review')
progress.update(current='Turkey',updated_at=now());write(H/'progress.json',progress)
dispatch=dict(prepared_at=now(),created=False,parent_thread_id=parent,character='Turkey',dispatch_token=token,project_root='E:/MyTowerGame',handoff_file=rel(handoff),handoff_sha256=sha(handoff),assessment_file=rel(assessment_path),release_file=rel(release_path),prompt_file=rel(prompt_path),prompt_sha256=sha(prompt_path),progress_sha256=sha(H/'progress.json'),response_file=rel(D/('successor_creation_response_'+stamp+'.json')))
write(dispatch_path,dispatch)
assert read(H/'progress.json')['completed_count']==89 and read(H/'progress.json')['current']=='Turkey' and token in (H/'NEXT_ENEMY_TASK.md').read_text(encoding='utf-8')
assert all(sha(R/p)==s for key in ['installed_files','production_scope_files','external_evidence'] for p,s in binding[key].items())
chain.setdefault('completed_handoffs',[]).append(dict(character=NAME,status=item['status'],current_stage='recorded_pending_user_art_review',owner_thread_id=parent,dispatch_token=TOKEN,closed_at=now(),handoff_file=rel(handoff),final_evidence=rel(D/'final_validation_20261028.json')))
chain.update(state='handoff_ready',parent_thread_id=parent,current_character='Turkey',dispatch_token=token,character_status_at_handoff='not_started',completed_count_snapshot=89,previous_handoff_file=chain['last_handoff_file'],last_handoff_file=rel(handoff),handoff_sha256=sha(handoff),successor_assessment=rel(assessment_path),prepared_dispatch_file=rel(dispatch_path),unity_release_file=rel(release_path),progress_sha256_at_handoff=sha(H/'progress.json'),handoff_ready_at=now(),updated_at=now(),successor_created=False,dispatch_ready_for='Turkey',current_stage='handoff_ready_reference_only',last_stage_evidence=rel(D/'final_validation_20261028.json'),resume_character='Turkey',resume_stage='Inspect actual Turkey source anatomy/animations and establish own baseline',current_blocked=False,blocked_reason=None,stop_reason=None,stopped_at=None,ownership_transfer_note='Await exactly one fresh local Turkey child; no production work while handoff_ready.')
write(H/'conversation_chain.json',chain)
print(json.dumps(dict(state=chain['state'],completed=89,character='Turkey',token=token,prompt=rel(prompt_path),dispatch=rel(dispatch_path),creation_response=dispatch['response_file'],handoff=rel(handoff),released=released),ensure_ascii=False))
