from session_current import *
from mcp_call import URL
import shutil,uuid,time

chain=owner();progress=read(RUN/'progress.json')
item=next(r for r in progress['items'] if r['name']==NAME)
assert item['status']=='completed_pending_user_art_review' and not item['user_approved']
assert progress['completed_count']==103
assessment=read(HERE/'successor_assessment_final_20261029.json')
NEXT=assessment['selected'];assert NEXT=='Wolf' and assessment['selected_index']==115
n=RUN/NEXT;existing=[p for p in n.rglob('*') if p.is_file()]
assert len(existing)==8 and all(p.is_relative_to(n/'reference') for p in existing)
t=next(t for t in read(RUN/'local_baseline.json')['targets'] if t['name']==NEXT)
six={p:sha(ROOT/p) for k in ['battle','source','atlas'] for p in [t[k],t[k]+'.meta']}
assert all(sha(n/'reference'/Path(p).name)==digest for p,digest in six.items())
oldblock=read(RUN/'PossessedWarg/blocked_20261026_125634_639300.json')
assert sha(RUN/'PossessedWarg/generation/Down/request.json')==oldblock['request_sha256']
assert snapshot()==read(HERE/'final_version_binding_20261029.json')['all_production_fingerprints']
project_list_file=HERE/'project_list_response_final_20261029.json'
raw=read(project_list_file)
projects=raw.get('structuredContent') or json.loads(next(r['text'] for r in raw['content'] if r['type']=='text'))
matches=[p for p in projects['projects'] if p.get('path','').replace('\\','/').rstrip('/').lower()=='e:/mytowergame']
assert len(matches)==1 and matches[0]['hostId']=='local'
pid=matches[0]['projectId']

c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
compile_errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json','filter_text':'error CS'})
def logs_data(value):
    value=value.get('structuredContent') or json.loads(value['content'][0]['text'])
    assert value['success'];return value['data']
assert logs_data(errors)==logs_data(compile_errors)==[]
state=c.resource('mcpforunity://editor/state');live=probe(c);idle(live);v=state['data'];refresh=None
if v['assets']['external_changes_dirty']:
    refresh=c.tool('refresh_unity',{'mode':'force','scope':'all','compile':'none','wait_for_ready':True})
    for attempt in range(20):
        state=c.resource('mcpforunity://editor/state');v=state['data']
        if v['advice']['ready_for_tools'] and not v['compilation']['is_compiling'] and not v['compilation']['is_domain_reload_pending'] and not v['assets']['is_updating'] and not v['assets']['external_changes_dirty']:break
        time.sleep(1)
    c.identity();live=probe(c);idle(live)
assert v['advice']['ready_for_tools'] and not v['tests']['is_running'] and not v['compilation']['is_compiling'] and not v['compilation']['is_domain_reload_pending'] and not v['assets']['is_updating'] and not v['assets']['external_changes_dirty']
assert snapshot()==read(HERE/'final_version_binding_20261029.json')['all_production_fingerprints']

stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
token='winterwolftypeb-to-wolf-'+stamp+'-'+str(uuid.uuid4())
rel=lambda p:p.relative_to(ROOT).as_posix()
handoff=RUN/'conversation_handoffs'/(stamp+'_WinterWolfTypeB_completed.md')
promptpath=n/('successor_prompt_'+stamp+'.txt')
release=HERE/'handoff_release_final_20261029.json'
dispatchpath=HERE/'prepared_successor_dispatch_final_20261029.json'
assert all(not p.exists() for p in [handoff,promptpath,release,dispatchpath])
save(release,{'observed_at':now(),'project':project,'transport':URL,'success':True,
    'editor_state':state,'final_probe':live,'errors':errors,'compile_errors':compile_errors,
    'asset_refresh_to_clear_pending_external_changes':refresh,
    'all_production_unchanged_since_final_binding':True,'next_protected_six':six,'protocol_history':c.history})
attempts=[]
for folder in [HERE/'generation/Up',HERE/'generation/Up/revision_01',HERE/'generation/Down']:
    result=read(folder/'result.json') if (folder/'result.json').exists() else None
    attempts.append({'folder':folder.relative_to(HERE).as_posix(),
        'request_sha256':sha(folder/'request.json'),'status':result['status'] if result else 'unknown',
        'raw_sha256':sha(folder/'raw.png') if (folder/'raw.png').exists() else None,
        'raw_bytes':(folder/'raw.png').stat().st_size if (folder/'raw.png').exists() else None,
        'response_sha256':sha(folder/('result.json' if result else 'uncertain_result.json')),
        'charge':'not independently verified' if result else 'unknown'})
save(HERE/'generation_final_accounting_20261029.json',{'observed_at':now(),'requests':attempts,
    'authenticated_image_requests':3,'http200':2,'unknown':1,'additional_network_recovery_used':1,
    'additional_network_recovery_limit':2,'new_paid_art_revisions':0,'paid_diagnostics':0,
    'standing_authorization_evidence':'WinterWolfTypeA/standing_authorization_original_messages_20261029.json',
    'local_revisions_are_not_AI_returns':True,'unknown_initial_Up_retained':True,'counters_reset':False})
backup=HERE/('docs_before_final_handoff_'+stamp);backup.mkdir()
for p in [RUN/'conversation_chain.json',RUN/'progress.json',RUN/'NEXT_ENEMY_TASK.md',RUN/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md',RUN.parent/'README.md']:
    shutil.copy2(p,backup/p.name)
binding=read(HERE/'final_version_binding_20261029.json')
runtime=read(HERE/'runtime_summary.json');review=read(HERE/'visual_review_final_20261029/review.json')
archive=read(HERE/'gif_archive_verification_20261029.json')
summary=f'''# WinterWolfTypeB114 完成与 Wolf115 唯一串行交接

时间 {now()}。父线程 {chain['owner_thread_id']}；旧token {chain['dispatch_token']}。WinterWolfTypeB已record，completed_pending_user_art_review、user_approved=false；总进度103/108。剩余PossessedWarg79 blocked、Wolf115、WolfHound116、WolfMounfed117、Zombie118。下一唯一Wolf。未创建明确成功并登记新owner/token前后继保持只读。

最终美术{binding['art_revision']}：Up为revision_01成功图的本地03衍生，选择无五官后脑，移除后趾线；Down为初次成功图的本地03并在暂存Body04清理两处破碎耳状/圆斑残痕。保留象牙白/浅taupe毛、赭圆斑、高尖耳、小黑瞳象牙眼、宽口鼻和赭鼻、尖牙、棕色下巴与胸毛、四短犬腿和长斑尾；无项圈鞍背刺。Up后脑无正面耳垫、后跟平滑；Down前趾及原生愤怒头可见。14透明分件、2048atlas、PPU100；alpha01填551微孔像素、去12微尘像素；后续仅局部Body04保原alpha和轮廓，布局04埋前腿根。所有旧raw/本地/否决stage/修前alpha/布局完整保留；不能full-stage覆盖清理版。art_selection指向两张local03，Body04额外暂存修订以staged_body_cleanup_r04_20261029.json为准。

安装只改本角色battle和Directions，installed_manifest永久保留、Verify全PASS含收集器/原曲线事件/时序。battle SHA{binding['production_fingerprints']['Assets/Prefabs/Enemy/Enemy_WinterWolfTypeB.prefab']}。22生产绑定包含battle.meta与Directions根.meta、17暂存文件、安装清单/Verify与prePlay完全一致。现场14sprite的rect/pivot/PPU逐项一致，Multiple、alphaTransparency=true、mipmap=false；依赖和原Wolf Ready/Walk/Attack/Death合同匹配。源图/prefab/meta、原控制器与曲线/事件/loop/时长不变，无UnityC#修改或发布构建。

最终两轮真实Play：runtime_r01 84PASS0FAIL、295原始PNG，records SHA{runtime['runtime'][0]['records_sha256']}；runtime_updeath_r01 84PASS0FAIL、297PNG，records SHA{runtime['runtime'][1]['records_sha256']}。总168PASS0FAIL、592PNG；均安装后真实Play并安全回Boot，完整SHA在final_version_binding_20261029.json。包括方向滞回/近零、四向及连续转向相位、原生状态/头事件、白闪结束、死亡旋转收缩淡出、自动回收同实例复用、暂停恢复和1x2x3x/Flying探针。

实际看过两轮four_directions、runtime strip及14张完整时序/原生循环/GIF编码帧板：301采样位、289张不同真实PNG，12最终GIF各5编码帧共60；另看未裁Up、Down愤怒攻击、Up死亡连接、复用、最终双向GIF整帧。所审样本四腿/尾连接、原侧向步态、攻击/受击/死亡/复用及暂停转向正常、无地面影。没有实时播放GIF或逐张审完592帧。死亡逐renderer alpha会显示重叠层，未伪称一体alpha。

按B自身Walk .5s合同，原Up/Down GIF解码460–470ms仅Docs按真实normalized phase累计10ms边界修至500ms；PNG/生产不改，保留6修前GIF和两manifest。AllGIF1660→1678，本角色18来源=12当前审核版本+6旧时长，所有源/集中副本SHA一致，旧来源哈希保留。用户美术未批准。

图像请求共3：Up初次Curl55无HTTP/raw/result/查询ID，结果与费用unknown永久保留；standing同类网络恢复Up revision_01单次HTTP200，raw1477910bytes；Down初次HTTP200，raw1556767bytes，两张1536x1024 RGB。额外网络恢复用1/2，无付费美术返修或付费诊断，不重置计数。非鉴权固定边缘对照HTTP401只证明传输，不倒推旧请求未发送或未收费。Docs generate.mjs仅定点增加B Up Curl55 revision01/02 standing恢复，原backup/patch/SHA和全部owner/token/计数/成功图防重保护保留。用户固定--resolve aihub.dog:443:191.101.132.254仍在；正式请求只在本进程NO_PROXY=aihub.dog并暂清HTTP_PROXY/HTTPS_PROXY/ALL_PROXY，finally恢复；未改hosts/系统代理/TLS。A的Down03专用授权不能套用Wolf，通用standing遇同类故障须核原人类消息、适用范围与已有耗用。A旧3unknown和standing2/2不变；PossessedWarg旧Down仍unknown，未重发。

全路径并集Assets/Packages/ProjectSettings/Luban5605→5625，22变化/20新增/0删除/unexpected0，仅本battle、Directions含根meta与未改ReporterEditor的自动Play build_info时间戳。共享C#、其他角色、配置、源meta无本轮漂移；历史global范围失败未重新分类为PASS。安装前首次语义门因未安装Directions而停止，生产0变化；修正为六保护及5605路径精确SHA门后安装，原诊断保留在preinstall_final。最终语义通过。

Unity HTTP8088动态核E:/MyTowerGame/2022.3.62f3c1，单一clean Boot、非Play、failed/compile/reload/update/tests/review/recording/balance/manual=false、ready=true、external_changes_dirty=false，error/errorCS0。无C#改动未请求额外编译，未清日志、未桌面控制。handoff_release_final是最新释放探针。最终入口：WinterWolfTypeB/final_validation_20261029.json、final_version_binding_20261029.json、scope_incremental_final_20261029.json、visual_review_final_20261029/review.json、gif_archive_verification_20261029.json、gif_quantization_fix_20261029.json、generation_final_accounting_20261029.json与runtime_summary.json。

下一Wolf115仅8个reference文件，六保护匹配。父未审Wolf实际源图，不继承B的颜色/比例/器官。battle={t['battle']}；source={t['source']}；atlas={t['atlas']}；controller={t['controller']}；Directions={t['art_dir']}。自行完整查看源和捕获动画合同。新token {token}；完整接棒prompt {rel(promptpath)}。只创建一个fresh local聊天，不fork/子代理/并行/定时器/模型覆盖。创建明确成功响应先落盘，再最后写chain转active新owner，此后父只读。进度快照不能代替现场核对。
'''
handoff.write_text(summary,encoding='utf-8')

prompt=f'''# Wolf115 唯一接棒执行 Prompt

在E:/MyTowerGame继续敌人四方向续作。本聊天只完成Wolf(index115)，完成后按协议创建唯一后继。当前103/108，所有completed_pending_user_art_review均仅内部完成，用户尚未美术批准。此文件为完整UTF8说明，不依赖旧聊天图片。

## 1. 唯一所有权、同步与恢复阶段

dispatch_token={token}
父线程={chain['owner_thread_id']}
先读E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/Remaining_20261024/conversation_chain.json、progress.json、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、NEXT_ENEMY_TASK.md、Docs/EnemyDirectionReview/README.md及{rel(handoff)}。读本角色已有文件、git status、相关差异、实现和直接依赖/生命周期，保留全部既有未提交改动；同步不授权git pull/reset/clean/checkout、commit/push。

只有chain.state=active、owner_thread_id等于本聊天真实ID、current_character=Wolf且token完全匹配才能改生产或操作Unity。若handoff_ready，只读限次等父登记，不因超时抢占。max_active_production_tasks=1，一次一角色；禁止子代理、并行角色、fork、自动化或定时器。父会先保存明确创建响应，再最后写active新owner并停止工作区写入。

剩余5项：PossessedWarg79 blocked、Wolf115、WolfHound116、WolfMounfed117、Zombie118；108是授权角色数，末项index118，WolfMounfed保持原拼写。PossessedWarg旧Down无raw/result/服务ID、结果及费用unknown，不推定未发送或未收费，不重发。交接扫描Wolf只有8个reference文件，本父额外写了此prompt；没有generation/staged_art/install/runtime。在你开工时重新递归核实，恢复新增阶段，不盲目prepare、生成或安装。

## 2. 正确工程和Unity路由

目标E:/MyTowerGame、Unity2022.3.62f3c1，版本以ProjectVersion.txt为准。unityMCP HTTP Local http://127.0.0.1:8088/mcp；根AGENTS的FreedomTower_1/D:/8082为旧信息，8082现场属于FishTestGame、8080属于CatchFish。不得操作其他工程或为本任务改根AGENTS。用户要求控制电脑前先弹确认；本任务使用文件/命令行与Unity MCP，不擅自桌面控制。

首次/重连/域重载后读mcpforunity://custom-tools和instances，动态选MyTowerGame完整ID，set_active_instance，再project/info核路径/版本。可用已审mcp_call.py Client.identity()，loopback禁代理，不硬编码hash。MCP离线按已有授权恢复本工程已有服务/桥接，复用在线服务、不抢端口、不杀其他工程。桌面操作确需时遵守用户确认边界；恢复失败及时说明项目、版本、8088失败环节和具体启动连接步骤。

操作前先读error/errorCS，再state与实际probe，确认无他人Play、脏场景、测试、review/balance/manual/recording、编译或更新。前任交回单一clean Boot，不能据旧快照强停后来任务。当前角色两轮真实Play已有授权，不逐角色再问；结束恢复原干净场景。无UnityC#改动不为形式额外编译；如改C#，同批完成后8088 MCP refresh_unity(mode=force,scope=all,compile=request,wait_for_ready=true)，1–2秒读state直到compile/reload/update=false且ready=true，error/errorCS与scriptCompilationFailed=false；期间不写代码，断线约5秒重连重核，不清控制台。

## 3. Wolf自身源图、结构和原动画合同

battle={t['battle']}
source={t['source']}
atlas={t['atlas']}
controller={t['controller']}
Directions={t['art_dir']}

读local_baseline.json、production_fingerprints_before.json、Batch01_10/user_approval_20261023.json与AllGIF/manifest.json。建立Assets/Packages/ProjectSettings/Luban全路径SHA基线及battle/source/atlas和三meta六保护；Directions根.meta单列，既有新增/删除也纳入范围。定向读BaseEnemy、EnemyDirectionalVisual/Profile、MonsterAnimEventReceiver、EnemyDirectionalRigBuilder、PrefabBuilder、BatchReview、RemainingCatalog/Motion与直接调用及回收复用。

必须实看完整原atlas与源prefab并读层级、四腿/头/尾、锚点、渲染层级、左右原图。不能按Wolf名字或WinterWolfTypeB复制颜色、器官、体形或布局。捕获自身Ready/Walk/Attack/Death和controller的结构化合同，含状态/参数/过渡、所有float与PPtr绑定和完整key/tangent/weight、事件、loop/时长/rate；不使用ToString对象冒充合同。Up为真后脑无五官/前向耳垫及平滑后跟，Down真正面/前趾；不加原型没有的装备，不留重复头耳、断颈、漂浮器官。保护首批10项批准、BlueScorpion最终尾与否决历史。

## 4. Image API正式入口与防重复

用户已授权AIHub图片任务；https://aihub.dog/v1/images/edits，gpt-image-2、medium、n=1、1536x1024。密钥仅运行时从AIHUB_IMAGE_API_KEY或C:/Users/Administrator/.codex/secrets/aihub-image-key.clixml DPAPI读取，仅送https://aihub.dog，不输出/落盘/进入进程参数/跨域转发，结束清临时环境。使用现有generate_character.ps1/generate.mjs，先读入口与保护，逐方向审核，不盲批量请求。

用户修改的Curl固定参数--resolve aihub.dog:443:191.101.132.254必须保留。最近B Up revision_01/Down初次均通过直接TLS域名路线HTTP200，raw1477910/1556767bytes，确为任务生成而非付费诊断。读image_transport_edge_map_20261029_1830.md、docs_tooling_edge_resolve_20261029_182840.json、WinterWolfTypeB/generate_initial_direct_20261029.ps1、generation_final_accounting_20261029.json、standing_recovery_application_20261029_Up.json、docs_generator_recovery_20261029.json及patch。B脚本有B专用owner/token，不能直接替Wolf执行。

普通首次入口verifiedDirectTransport可能false，调用请求的进程内临时NO_PROXY=aihub.dog，暂清HTTP_PROXY/HTTPS_PROXY/ALL_PROXY并finally恢复，确保Curl直连固定边缘；不要--system-local-proxy，不改系统hosts/代理，不禁TLS。Preflight只核输入/路由，不发图请求。需要改Docs工具先留SHA/backup/patch，定点改当前合法入口，不弱化owner/token/源指纹/已成功图/请求结果/计数保护。

任何request/raw/result/uncertain/revision先查实际材料与在途进程。成功图不重生；失败与unknown分别保存，超时不盲重发。B Up初次Curl55仍unknown，standing额外1/2；A旧三Down unknown、standing2/2及A Down03专用max1不得借给Wolf或重置。遇同类网络故障先核WinterWolfTypeA/standing_authorization_original_messages_20261029.json原人类回复“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”、适用范围、已用计数和恢复入口，再在现有授权内推进；不能把代理自定界限伪称用户金额预算，不能删日志或改名绕防重。无合法恢复路径时准确阻断，不能借别的角色付费探测。不根据非鉴权401或外部WorkBuddy推理倒推旧请求未计费。

## 5. 分阶段制作、安装和两轮真实Play

Python统一C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8，子Python用sys.executable。先读character_step.py、prepare_character.py、pack_character.py、adjust_layout.py、render_staged_rig.py、install_character.py、runtime_runner.py、runtime_runner_revision.py、build_runtime_media.py、record_review.py、collect_gifs.py。仅未准备时character_step.py prepare Wolf。按真实源完善anatomy_plan和prompt，实际审每张raw再art_selection；局部修订记录父图/区域/方法/SHA并保修前，明确是本地像素衍生，不冒充新AI返回。

依实际矩形分件，不假定生成格界；去品红、检查微洞/尘点、描边污染、切片、PPU/pivot/render order和根部遮挡。前任14分件/2048仅是前任事实，按Wolf自身需要和工具合同处理。局部补色不得留硬接缝、碎斑和重复器官。实看完整四方向离线组合与细节，耳脚尾不能裁掉；足/尾根连接，四足对角步态、躯干和尾错相、短步、攻击蓄力发力、死亡保持连接，无地面影。原左右曲线/事件/loop/时长保留。full stage/pack会覆盖后续alpha修订，先留父版本再执行。

安装前重新核owner、8088身份、error→state→严格空闲和全路径保护。安装前语义工具若要求已装Directions，不能误当未装角色门；用六保护+全路径SHA门，保留原诊断。只安装Wolf Builder并Verify，禁止全目录重建或删除installed_manifest。安装后绑定battle/meta、Directions所有文件及根.meta、暂存全部文件和manifest/Verify的SHA，绑定完成才运行。

两轮真实Play普通死亡/Up死亡每轮84PASS0FAIL，共168；保存全部actual_frames.jsonl、checks、原始PNG、Unity frame/realtime/normalizedTime与SHA。覆盖四向/斜向滞回/近零、原生状态及头事件、连续转向保相位、受击/致死白闪结束、死亡旋转收缩淡出、自动回收同实例复用、暂停恢复/1x2x3x及适用Flying探针。不能用Animator.Update或离线合成冒充真实Play。画面问题即使断言PASS也返修保旧版，重新绑定并重跑最终两轮。

## 6. 审画、时长、范围、record和GIF归档

实看最终两轮four_directions、runtime strip、按时序足量真实PNG、原生循环与最终GIF解码帧，覆盖全部动作；一次1–2图，完整原件留盘。先看未裁原图，再用保耳脚尾的crop。记录实际采样位/不同PNG/GIF编码帧数、路径/SHA与观察。不能播放时如实说逐序抽样，不声称实时播放或全帧审完。

解码GIF实际总时长，与Wolf自己的Walk原合同对比，不复制B .5s。Pillow逐帧向10ms截断会变短；必要仅Docs保留修前GIF/manifest后，用实际normalized phase累计边界量化到10ms并保原生总时长，不合成姿态。B的Up/Down原460–470ms已修500ms，6旧时长GIF保留。可参考B prepare_visual_closeout_20261029.py，但角色/合同/计数必须用Wolf现场数据，不继承B 592/301/289。

最终全路径并集含新增删除及Directions根.meta；源/meta、原动画、共享C#、其他角色、配置都保护。Reporter build_info仅在ReporterEditor不变、格式吻合且由实际Play触发时单列；不能把历史global scope失败重标PASS。最终生产/暂存和安装manifest/Verify应匹配prePlay，runtime PNG/记录/媒体绑定同版；再现场核import/rect/pivot/PPU/alpha/依赖/Verify收集器、errors0/failedfalse、单一clean Boot非Play全空闲。无发布构建。

UTF8真实visual_note写Wolf/record_note_utf8.txt，再文件读取传character_step.py record Wolf，避免PowerShell中文参数破损。只能completed_pending_user_art_review、user_approved=false。record会collect_gifs，逐个核本角色全部GIF源与集中副本SHA、最终/修前/否决状态，保留所有旧来源哈希；前任AllGIF1678仅是起点，不假定每角色12或最终数量。保存final_validation、version_binding、scope、review、archive及Unity release，进度正确递增、首批批准不变。

## 7. 唯一后继交接与停止父写入

完成Wolf或准确记录真实阻断后先安全交回Unity。重读progress并递归未完成材料，优先独立可恢复已开始项，再按index正常下一WolfHound116；PossessedWarg旧unknown保留，不机械用progress.current。仍有可独立工作就继续链，全部108有效完成或只剩真实阻断才停止；待用户美术审核不暂停循环。

新建带时间Wolf handoff，写实际修改、revision/指纹、两轮计数、所审范围/限制、Unity状态、网络尝试/unknown及后继。更新README和主prompt的live块，保留历史；写完整UTF8 NEXT和后继prompt，无占位符/省略/分段。先确认Unity释放，再chain=handoff_ready、新唯一token、parentID/下一角色。现场list_projects核E:/MyTowerGame，唯一create_thread(target={{type:project,projectId:现场ID,environment:{{type:local}}}},prompt:完整文本)，不fork/子代理/模型或推理覆盖。创建结果不明先查真实响应/聊天不重复。明确成功响应先落盘，再父最后工作区写chain=active新owner/token，此后停止全部写入；一次有界wait_threads确认启动，最后输出真实created-thread directive。失败保留完整prompt和总结并准确报告。

禁止配置表自动改写、Assets/ConfigJson或Assets/Gen直接写入、恢复声音、构建部署、生产删除、Git提交推送、memory修改、擅控桌面。保留所有历史失败/否决/unknown/计数/安装清单。现在先核所有权、正确工程与实际源参考，完成Wolf的实际工作。
'''
promptpath.write_text(prompt,encoding='utf-8')
(RUN/'NEXT_ENEMY_TASK.md').write_text(prompt,encoding='utf-8')
live_text=f'{now()} WinterWolfTypeB114已record，103/108，completed_pending_user_art_review/user_approved=false；Up/Down本地03、alpha01/Body04/layout04，最终两轮168PASS0FAIL/592PNG，实审14板301采样位289不同PNG与12GIF各5编码帧。B原生Walk500ms，Up/Down GIF460–470ms已仅Docs修至500ms，6修前保留；AllGIF1678，本角色18=12最终+6历史，源/副本SHA一致。5605→5625全路径并集22变化/20新增/unexpected0，22生产绑定与prePlay一致，源/meta/共享C#/其他角色/配置保护；Unity8088 clean Boot非Play/error0。图像3请求=Up初次unknown+Up01/Down初次HTTP200，standing额外1/2，旧unknown和计数保留。下一唯一Wolf115；PossessedWarg79旧Down仍unknown。详见{rel(handoff)}；实时以progress/chain为准。'
for path,begin,end in [(RUN.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),(RUN/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    text=path.read_text(encoding='utf-8');assert text.count(begin)==text.count(end)==1
    a=text.index(begin)+len(begin);b=text.index(end,a)
    text=text[:a]+'\n'+live_text+'\n'+text[b:]
    if path.name=='README.md':text=text.replace('2026-10-29 本轮当前清单为 1660 个文件','2026-10-29 本轮当前清单为 1678 个文件')
    path.write_text(text,encoding='utf-8')
item['handoff_file']=rel(handoff);item['successor_character']=NEXT
progress.update(current=NEXT,updated_at=now())
(RUN/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
dispatch={'prepared_at':now(),'character':NEXT,'index':115,'dispatch_token':token,
    'parent_thread_id':chain['owner_thread_id'],'project_id':pid,'project_live_confirmed':True,
    'project_list_response_file':rel(project_list_file),'project_list_response_sha256':sha(project_list_file),
    'created':False,'response_file':rel(HERE/('successor_creation_response_final_'+stamp+'.json')),
    'progress_sha256':sha(RUN/'progress.json')}
for key,path in [('prompt',promptpath),('handoff',handoff),('assessment',HERE/'successor_assessment_final_20261029.json'),('unity_release',release),('next_task',RUN/'NEXT_ENEMY_TASK.md')]:
    dispatch[key+'_file']=rel(path);dispatch[key+'_sha256']=sha(path)
save(dispatchpath,dispatch)
chain.setdefault('completed_handoffs',[]).append({'character':NAME,'status':item['status'],
    'current_stage':'recorded_pending_user_art_review','closed_at':now(),'owner_thread_id':chain['owner_thread_id'],
    'dispatch_token':chain['dispatch_token'],'handoff_file':rel(handoff),'final_evidence':rel(HERE/'final_validation_20261029.json')})
chain.update(state='handoff_ready',parent_thread_id=chain['owner_thread_id'],current_character=NEXT,
    dispatch_token=token,character_status_at_handoff='not_started',completed_count_snapshot=103,
    previous_handoff_file=chain.get('last_handoff_file'),last_handoff_file=rel(handoff),handoff_sha256=sha(handoff),
    successor_assessment=dispatch['assessment_file'],progress_sha256_at_handoff=sha(RUN/'progress.json'),
    unity_release_file=rel(release),prepared_dispatch_file=rel(dispatchpath),creation_response_file=dispatch['response_file'],
    dispatch_ready_for=NEXT,successor_created=False,current_stage='handoff_ready_pending_single_successor_creation',
    resume_character=NEXT,resume_stage='Verify new owner/token; inspect Wolf original source and native contract; establish baseline',
    current_blocked=False,blocked_reason=None,blocked_owner_retained=False,no_successor_creation_reason=None,
    handoff_ready_at=now(),updated_at=now(),last_stage_evidence=rel(HERE/'final_validation_20261029.json'))
(RUN/'conversation_chain.json').write_text(json.dumps(chain,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'state':'handoff_ready','character':NEXT,'token':token,'project_id':pid,
    'prompt_file':str(promptpath),'dispatch_file':str(dispatchpath),'handoff_file':str(handoff)},ensure_ascii=False))
