from session_current import *
from mcp_call import URL
from PIL import Image
import shutil,uuid,time

chain=owner();progress=read(RUN/'progress.json')
item=next(r for r in progress['items'] if r['name']==NAME)
assert item['status']=='completed_pending_user_art_review' and not item['user_approved']
assert progress['completed_count']==105
assessment=read(HERE/'successor_assessment_final_20261029.json')
NEXT=assessment['selected'];assert NEXT=='WolfMounfed' and assessment['selected_index']==117
n=RUN/NEXT;existing=[p for p in n.rglob('*') if p.is_file()]
assert len(existing)==8 and all(p.is_relative_to(n/'reference') for p in existing)
t=next(t for t in read(RUN/'local_baseline.json')['targets'] if t['name']==NEXT)
six={p:sha(ROOT/p) for k in ['battle','source','atlas'] for p in [t[k],t[k]+'.meta']}
assert all(sha(n/'reference'/Path(p).name)==digest for p,digest in six.items())
oldblock=read(RUN/'PossessedWarg/blocked_20261026_125634_639300.json')
assert sha(RUN/'PossessedWarg/generation/Down/request.json')==oldblock['request_sha256']
assert not any((RUN/'PossessedWarg/generation/Down'/s).exists() for s in ['raw.png','result.json'])
binding=read(HERE/'final_version_binding_20261029.json')
runtime=read(HERE/'runtime_summary.json');review=read(HERE/'visual_review_final_20261029/review.json')
archive=read(HERE/'gif_archive_verification_20261029.json');final=read(HERE/'final_validation_20261029.json')
scope=read(HERE/'scope_incremental_final_20261029.json')
assert final['record_completed'] and final['completed_count']==105 and archive['after']==1710
assert snapshot()==binding['all_production_fingerprints']
project_list_file=HERE/'project_list_response_final_20261029.json';raw=read(project_list_file)
projects=raw.get('structuredContent') or json.loads(next(r['text'] for r in raw['content'] if r['type']=='text'))
matches=[p for p in projects['projects'] if p.get('path','').replace('\\','/').rstrip('/').lower()=='e:/mytowergame']
assert len(matches)==1 and matches[0]['hostId']=='local';pid=matches[0]['projectId']

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
assert snapshot()==binding['all_production_fingerprints']

stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
token='wolfhound-to-wolfmounfed-'+stamp+'-'+str(uuid.uuid4())
rel=lambda p:p.relative_to(ROOT).as_posix()
handoff=RUN/'conversation_handoffs'/(stamp+'_WolfHound_completed.md')
promptpath=n/('successor_prompt_'+stamp+'.txt')
release=HERE/'handoff_release_final_20261029.json'
dispatchpath=HERE/'prepared_successor_dispatch_final_20261029.json'
accounting=HERE/'generation_final_accounting_20261029.json'
assert all(not p.exists() for p in [handoff,promptpath,release,dispatchpath,accounting])
assert set(p.relative_to(HERE).as_posix() for p in (HERE/'generation').rglob('request.json'))=={'generation/Up/request.json','generation/Down/request.json'}
attempts=[]
for direction in ['Up','Down']:
    folder=HERE/'generation'/direction;result=read(folder/'result.json');request=read(folder/'request.json')
    assert result['status']==200 and request['model']=='gpt-image-2' and request['n']==1
    assert request['resolve_transport']['ip']=='191.101.132.254'
    with Image.open(folder/'raw.png') as im:fmt,size,mode=im.format,list(im.size),im.mode
    attempts.append({'folder':folder.relative_to(HERE).as_posix(),'request_sha256':sha(folder/'request.json'),
        'status':result['status'],'raw_sha256':sha(folder/'raw.png'),'raw_bytes':(folder/'raw.png').stat().st_size,
        'response_sha256':sha(folder/'result.json'),'actual_format':fmt,'actual_size':size,'actual_mode':mode,
        'transport':request['transport'],'resolve_transport':request['resolve_transport'],
        'charge':'Not independently verified; usage in response is a local estimate.'})
save(accounting,{'observed_at':now(),'requests':attempts,'authenticated_image_requests':2,'http200':2,
    'unknown':0,'additional_network_recovery_used':0,'new_paid_art_revisions':0,'paid_diagnostics':0,
    'local_revisions_are_not_AI_returns':True,'counters_reset':False,
    'other_character_unknowns':'PossessedWarg original Down, WinterWolfTypeA old three Down outcomes and WinterWolfTypeB initial Up remain unchanged. No reissue or inference about charge.'})
save(release,{'observed_at':now(),'project':project,'transport':URL,'success':True,
    'editor_state':state,'final_probe':live,'errors':errors,'compile_errors':compile_errors,
    'asset_refresh_to_clear_pending_external_changes':refresh,
    'all_production_unchanged_since_final_binding':True,'next_protected_six':six,'protocol_history':c.history})
backup=HERE/('docs_before_final_handoff_'+stamp);backup.mkdir()
for p in [RUN/'conversation_chain.json',RUN/'progress.json',RUN/'NEXT_ENEMY_TASK.md',RUN/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md',RUN.parent/'README.md']:
    shutil.copy2(p,backup/p.name)

summary=f'''# WolfHound116 完成与 WolfMounfed117 唯一串行交接

时间 {now()}。父线程 {chain['owner_thread_id']}；旧token {chain['dispatch_token']}。WolfHound已record为completed_pending_user_art_review、user_approved=false，总进度105/108。剩余PossessedWarg79 blocked、WolfMounfed117、Zombie118。下一唯一WolfMounfed。创建明确成功并登记新owner/token前，后继只读。

最终美术{binding['art_revision']}：Up/Down各自初次成功图的本地02衍生。Up原raw第2/3头误为正脸，使用第1个无脸后脑作为三表情，未再请求。local01处理外alpha及后趾线，后爪水平补色边界被否决；local02改整个连通躯干/Up腿内部，保原轮廓并重画源色阔毛束与赭圆斑，无矩形补色接缝。保卡其/橄榄棕底色、尖耳、小黑瞳象牙眼、犬齿、仅属于头的单条金色象牙尖刺项圈、四短犬腿和上弯蓬松厚尾，无冬狼灰毛/白胸围。Up无脸/前耳垫、后跟无趾线；Down正面前趾/愤怒/死亡头。14透明分件、2048atlas、PPU100；alpha01查0孔洞/0尘点。腿角6.5、抬腿.025、bodyBob.0045、bodyRoll.6、tailSwing4；layout03远侧Up前腿/Down后腿多数由躯干遮挡，足尾根埋入身体。原raw、本地01/02、修前stage/alpha/layout全部保留，不能full-stage覆盖最终暂存。

仅安装本角色battle及Directions，installed_manifest永久保留，安装与最终现场Verify全PASS，含收集器、原曲线事件/时长与组件语义。battle SHA {binding['production_fingerprints']['Assets/Prefabs/Enemy/Enemy_WolfHound.prefab']}。22生产绑定包含battle.meta、Directions根.meta及其全部文件，17暂存文件和安装manifest/Verify与prePlay一致。现场14sprite rect/pivot/PPU一致，Multiple、alphaTransparency=true、mipmap=false；依赖与共享Wolf原动画合同一致：Ready/Walk/Attack .5s，Death .416666657s，float绑定24/33/48/39、PPtr均0，事件保持。完整结构化合同及原动画/controller原件已存，无Unity C#改动。

最终两轮真实Play：runtime_r01为84PASS0FAIL、{runtime['runtime'][0]['frames']}张PNG，records SHA {runtime['runtime'][0]['records_sha256']}；runtime_updeath_r01为84PASS0FAIL、{runtime['runtime'][1]['frames']}张PNG，records SHA {runtime['runtime'][1]['records_sha256']}。总168PASS0FAIL、{runtime['actual_frames']}PNG，均自动返回clean Boot。覆盖四向/斜向滞回/近零、状态/头事件、连续转向相位、受击/致死闪白结束、死亡旋转收缩淡出、自动回收同实例复用、暂停恢复/1x2x3x及测试器Flying探针。原记录、所有PNG/检查/媒体SHA在final_version_binding_20261029.json。

实看完整原atlas/source、离线四方向与全部分件、两轮four_directions、runtime strip和14张时序/原生循环/GIF解码板。{review['png_sample_positions']}采样位、{review['unique_png_samples']}张不同真实PNG，12最终GIF各5编码帧共60。另看未裁Up、Down愤怒攻击、Up死亡、复用及双向GIF整帧。所审样本项圈/足尾根连接、短步尾摆错相、原左右步态、攻击头事件与蓄力发力、白闪结束、死亡及复用正常，无地面影/矩形补色缝。死亡按renderer淡出，重叠分件可见；未实时播放或逐张审完{runtime['actual_frames']}帧，不声称一体alpha。仍待用户美术审核。

自身Walk合同500ms，4个Up/Down GIF原460–470ms仅Docs按真实normalized phase累计10ms边界修至500ms，4修前GIF和两manifest保留。两个原500ms双向GIF未重写。AllGIF {archive['before']}→{archive['after']}，本角色16来源=12当前审核版本+4历史时长版，源/集中副本SHA一致，全部旧来源哈希保留。

图像共2请求：Up初次HTTP200、raw1529005bytes；Down初次HTTP200、raw1413412bytes，实际均PNG RGBA1536×1024。0unknown、0额外网络恢复、0付费美术返修/诊断，费用未独立核实。复用generate_character.ps1/generate.mjs和WolfHound专用owner/token包装，保留用户--resolve aihub.dog:443:191.101.132.254，仅调用进程内NO_PROXY=aihub.dog并暂清HTTP_PROXY/HTTPS_PROXY/ALL_PROXY，finally恢复；未改共享生成器、hosts、系统代理或TLS。local01/02是本地像素衍生，非AI返回。其他角色旧unknown和standing耗用保持，PossessedWarg Down不重发。

全路径Assets/Packages/ProjectSettings/Luban {scope['before_count']}→{scope['after_count']}，并集{len(scope['changes'])}变化/{scope['added']}新增/{scope['deleted']}删除/unexpected0，仅本battle、Directions含根meta，及未改ReporterEditor在真实Play域初始化写的build_info；设备名、本地时间格式及run时间窗匹配。源prefab/atlas/meta、原动画、共享C#、其他角色及配置受保护，首批批准证据未变；历史global scope失败未重标PASS。安装前以全路径精确SHA及六保护为门，未装前语义工具仅诊断，装后通过。

Unity HTTP8088动态核E:/MyTowerGame/2022.3.62f3c1，单一clean Boot非Play，failed/compiling/reload/update/tests/review/balance/recording/manual=false、ready=true、external_changes_dirty=false，error/errorCS0。未清日志、未桌面控制、未构建部署。handoff_release_final_20261029.json为最新释放。最终入口WolfHound/final_validation_20261029.json、final_version_binding_20261029.json、scope_incremental_final_20261029.json、visual_review_final_20261029/review.json、gif_archive_verification_20261029.json、gif_quantization_fix_20261029.json、generation_final_accounting_20261029.json、runtime_summary.json。

下一WolfMounfed117递归扫描仅8个reference文件，六保护匹配。拼写WolfMounfed保持，atlas是WolfMounted.png，目录是Mounts/WolfMount。父未审其实际源图；后继必须独立审源/层级并捕获完整原动画合同，不继承WolfHound的项圈、颜色、器官或布局，不从名字推定骑手/装备。battle={t['battle']}；source={t['source']}；atlas={t['atlas']}；controller={t['controller']}；Directions={t['art_dir']}。新token {token}；完整prompt {rel(promptpath)}。只创建一个fresh local聊天，明确创建响应先落盘，再父最后写chain active新owner，随后停止全部工作区写入；不fork/子代理/并行/自动化/模型覆盖。
'''
handoff.write_text(summary,encoding='utf-8')

prompt='# WolfMounfed117 唯一接棒执行 Prompt\n\n在E:/MyTowerGame继续敌人四方向续作。本聊天只完成WolfMounfed(index117)，完成后按串行协议创建唯一后继。当前105/108，所有completed_pending_user_art_review仅内部完成，用户尚未美术批准。本文为完整UTF8执行说明，不依赖旧聊天图片。\n\n## 1. 唯一所有权和现场同步\n\ndispatch_token=__NEW_TOKEN__\n父线程=__NEW_PARENT__\n先读E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/Remaining_20261024/conversation_chain.json、progress.json、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、NEXT_ENEMY_TASK.md、Docs/EnemyDirectionReview/README.md及__NEW_HANDOFF__。读本角色已有证据、git status、相关差异、实现、直接依赖/生命周期；保留全部既有未提交改动。同步不授权git pull/reset/clean/checkout、commit/push。\n\n只有chain.state=active、owner_thread_id等于本聊天真实ID、current_character=WolfMounfed且token完全匹配，才能改生产或操作Unity。若handoff_ready，仅只读限次等待父登记，不因超时抢占。max_active_production_tasks=1；一聊天一角色，禁止子代理、并行角色、fork、定时器和自动化。父先保存明确创建响应，再以最后一次工作区写入登记新owner active，随后停止全部工作区写入。\n\n剩余3项：PossessedWarg79 blocked、WolfMounfed117、Zombie118。108为授权数量，末项index118，WolfMounfed保持原拼写。PossessedWarg旧Down无raw/result/服务查询ID、结果及费用unknown，不推定未发送/未收费，不重发。交接时WolfMounfed仅8个reference文件，父额外写此prompt，没有generation/staged_art/install/runtime。开工重新递归核实，恢复已出现阶段，不盲目prepare、生成或安装。\n\n## 2. 工程身份与Unity8088\n\n目标E:/MyTowerGame，Unity2022.3.62f3c1，以ProjectVersion.txt为准。unityMCP HTTP Local http://127.0.0.1:8088/mcp。根AGENTS的FreedomTower_1/D:/8082为旧信息，8082属于FishTestGame、8080属于CatchFish；不操作其他工程，也不为此改根AGENTS。用户要求桌面/电脑控制先弹确认，本任务优先文件/命令行与Unity MCP，不擅控桌面。\n\n首次/重连/域重载后读mcpforunity://custom-tools和mcpforunity://instances，动态选MyTowerGame完整ID，set_active_instance，再project/info核路径/版本。可复用Remaining_20261024/mcp_call.py Client.identity()，loopback禁代理、不硬编码实例hash。服务离线按既有授权恢复目标已有服务/桥接，复用在线服务、不抢端口、不杀其他工程；确需桌面操作仍须用户确认。失败及时说明E:/MyTowerGame、版本、8088故障环节和具体开启/连接步骤。\n\n操作前先读error/errorCS，再state及实际probe，确认无他人Play、脏场景、测试、review/balance/manual/recording、编译/更新。前任交回单一clean Boot不能替代现场核对，不能强停后来任务。本角色两轮真实Play已有授权，不逐角色再问；结束恢复原干净场景。无Unity C#改动不为形式额外编译。如改C#，同批完成后8088 MCP refresh_unity(mode=force,scope=all,compile=request,wait_for_ready=true)，每1–2秒读state直到compile/reload/update=false且ready=true，error/errorCS0、scriptCompilationFailed=false；期间不改代码，断线约5秒重连重核，不清控制台。\n\n## 3. WolfMounfed自身源参考和原动画合同\n\nbattle=Assets/Prefabs/Enemy/Enemy_WolfMounfed.prefab\nsource=Assets/_UIAssets/Monsters/Mounts/WolfMount/WolfMounfed.prefab\natlas=Assets/_UIAssets/Monsters/Mounts/WolfMount/WolfMounted.png\ncontroller=Assets/_UIAssets/Monsters/_Common/Animations/Wolf/Controller.controller\nDirections=Assets/_UIAssets/Monsters/Mounts/WolfMount/Directions\n\nWolfMounfed保持实际拼写，atlas文件名WolfMounted.png、目录Mounts/WolfMount。父未审本角色实际源图。按真实源层级核对是否有骑手/鞍具/武器及其归属；只保留源确有的器官装备，不按名称推定，也不继承WolfHound项圈。\n\n读local_baseline.json、production_fingerprints_before.json、Batch01_10/user_approval_20261023.json与AllGIF/manifest.json。建立Assets/Packages/ProjectSettings/Luban全路径SHA基线，以及battle/source/atlas和三meta六保护；Directions根.meta单列，新增删除都计入。定向读BaseEnemy、EnemyDirectionalVisual/Profile、MonsterAnimEventReceiver、EnemyDirectionalRigBuilder、EnemyDirectionPrefabBuilder、EnemyDirectionBatchReview、RemainingCatalog/Motion及直接调用/缓存/回收复用。\n\n必须实看完整原atlas与source_prefab_offline，读层级、各器官、锚点、渲染顺序、左右原图。不能按WolfMounfed名字或复制WolfHound/Wolf/WinterWolfTypeB的颜色、器官、比例、布局。捕获自身Ready/Walk/Attack/Death和controller完整结构化合同：状态/参数/过渡、所有float和PPtr绑定、完整key/tangent/weight、事件、loop/时长/rate；不以ToString对象冒充合同。Up为真后脑无五官/前向耳垫，后跟平滑；Down真正面/前趾。不加原型没有的装备，不留重复头耳、断颈或浮动器官。保护首批10项用户批准、BlueScorpion最终尾及否决历史。\n\n## 4. Image API正式入口、防重复与网络恢复\n\n已有用户AIHub授权，https://aihub.dog/v1/images/edits，gpt-image-2、medium、n=1、1536x1024。密钥仅运行时从AIHUB_IMAGE_API_KEY或C:/Users/Administrator/.codex/secrets/aihub-image-key.clixml DPAPI读取，仅送https://aihub.dog，不输出、不落盘、不进命令行参数、不跨域转发，结束清临时环境。使用现有generate_character.ps1/generate.mjs，先读入口及保护，逐方向审阅。\n\n用户固定Curl参数--resolve aihub.dog:443:191.101.132.254必须保留。WolfHound本次Up/Down初次均HTTP200，raw1529005/1413412bytes，实际PNG RGBA1536×1024，共2请求0unknown0恢复。读image_transport_edge_map_20261029_1830.md、docs_tooling_edge_resolve_20261029_182840.json、WolfHound/generate_initial_direct_20261029.ps1与generation_final_accounting_20261029.json；必要再读WinterWolfTypeB/docs_generator_recovery_20261029.json及patch。包装脚本含角色专用owner/token，须独立适配WolfMounfed，不直接执行WolfHound/Wolf/B脚本。\n\n普通入口verifiedDirectTransport可能false。调用进程内临时NO_PROXY=aihub.dog，暂清HTTP_PROXY/HTTPS_PROXY/ALL_PROXY，finally恢复；确保Curl直连固定域名边缘，不用--system-local-proxy、不改hosts/系统代理、不禁TLS。Preflight只核输入/路由，不发图请求。若改Docs工具，先留SHA/backup/patch，仅定点改合法入口，不弱化owner/token、源指纹、已成功图、请求结果或计数保护。\n\n任何request/raw/result/uncertain/revision先查材料和在途进程。成功不重生；unknown不当成失败或未收费，超时不盲重发。B初次Up Curl55仍unknown、standing额外1/2；A旧三Down unknown、standing2/2及A Down03专用max1不得借给WolfMounfed或重置。若同类网络故障，先核WinterWolfTypeA/standing_authorization_original_messages_20261029.json中的原人类回复“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”、范围、已用计数和合法入口，再按现有授权推进。代理执行界限不是用户金额预算，不删日志/改名绕防重，不以非鉴权401或外部WorkBuddy推理倒推未计费。没有合法恢复路径则准确阻断，不借其他角色付费探测。\n\n## 5. 制作、安装与两轮真实Play\n\nPython统一C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8；子Python用sys.executable。先读character_step.py、prepare_character.py、pack_character.py、adjust_layout.py、render_staged_rig.py、install_character.py、runtime_runner.py、runtime_runner_revision.py、build_runtime_media.py、record_review.py、collect_gifs.py。仅未准备时character_step.py prepare WolfMounfed。按自身源完善anatomy_plan及prompt，实看每张raw后再art_selection。局部像素修订保父图、区域、方法和SHA，明确是本地衍生，不冒充新AI返回。\n\n按实际测量矩形分件，不假定格界；去品红、查透明微洞/尘点/描边污染、切片、PPU/pivot/render order和根部遮挡。前任14分件/2048只是前任事实，按本角色实际和工具合同处理。平涂不得留矩形缝/碎斑/重复器官；全身离线四向与细节均须实际看，耳脚尾不裁。足尾根连接，四足对角短步、躯干/尾错相，攻击蓄力发力、死亡连接，无地面影。保原左右曲线/事件/loop/时长。full-stage/pack会覆盖后续alpha修订，先保父版本再执行。\n\n安装前重核owner、8088身份、error→state→严格空闲和全路径保护。未安装前语义工具可能因缺Directions返回false，只作诊断；以六保护+完整路径精确SHA作门。只装WolfMounfed并Builder/Verify，不全目录重建、不删installed_manifest。安装后绑定battle/meta、Directions所有文件及根.meta、全部暂存文件、安装manifest和Verify的SHA，绑定后才运行。\n\n普通死亡与Up死亡两轮真实Play，每轮84检查，共168PASS0FAIL；初次runtime_r01/runtime_updeath_r01，返修用未占用revision并保旧轮。保actual_frames.jsonl/checks/原始PNG/Unity frame/realtime/normalizedTime/SHA，覆盖四向及斜向滞回/近零、原生状态/头事件、连续转向保相位、受击/致死闪白结束、死亡旋转收缩淡出、自动回收同实例复用、暂停恢复、1x2x3x及适用Flying探针。禁止Animator.Update或离线合成冒充实际Play。断言PASS仍须审画，有视觉错误就保旧返修、重绑定并重跑最终两轮。\n\n## 6. 审阅、时长、范围与记录归档\n\n实际查看最终两轮four_directions、runtime strip、足量时序真实PNG、原生循环和每个最终GIF的解码帧，覆盖动作。一次1–2图，原始完整证据留盘；先看未裁原图，再看保耳脚尾crop。记录实际采样位/不同PNG/GIF编码帧数、路径/SHA和观察。不能播放就如实写逐序抽样，不声称实时播放或全帧看完。WolfHound本轮605PNG、305采样位/293不同PNG只是历史，不能抄成新角色计数。\n\n解码GIF实际总时长并比WolfMounfed自己的Walk合同，不从前任推定.5s。Pillow逐帧10ms截断可能缩短；需要时仅Docs保修前GIF/manifest，按真实normalized phase累计边界量化到10ms并保持合同总时长，不合成姿态。可读WolfHound/prepare_visual_closeout_20261029.py；WolfHound只修4个460–470ms Up/Down至500ms，原500ms双向GIF未重写。数量必须现场计算。\n\n最终全路径并集含新增/删除/Directions根.meta；源/meta、原动画、共享C#、其他角色及配置保护。Reporter build_info仅在ReporterEditor不变、精确设备/本地时间格式符合且在实际Play时间窗时单列。历史global scope失败不重标PASS。最终生产/暂存/manifest/Verify须匹配prePlay，同版绑定runtime记录/PNG/媒体。再现场核import/rect/pivot/PPU/alpha/依赖/Verify收集器、errors0/failedfalse、单一clean Boot非Play全空闲；不构建发布包。\n\nUTF8真实visual_note先写WolfMounfed/record_note_utf8.txt，再文件读取传character_step.py record WolfMounfed，避免PowerShell中文参数损坏。只能completed_pending_user_art_review、user_approved=false。record会collect_gifs；逐个核本角色全部GIF源/集中副本SHA、最终/修前/否决分类，保所有旧来源哈希。起点AllGIF1710只是此刻，不假定每角色12。保存final_validation/version_binding/scope/review/archive和Unity release，进度递增，首批批准不变。\n\n## 7. 串行后继与父停止写入\n\n完成WolfMounfed或准确记录真实阻断后安全交回Unity。重读progress并递归未完成材料，优先独立可恢复已开始项，再按index正常下一Zombie118；PossessedWarg旧unknown保留，不机械用progress.current。全部108有效完成或只剩真实阻断才停止，待用户美术审核不暂停链。\n\n新建带时间WolfMounfed handoff，写实际修改/revision/指纹、两轮计数、所审范围/限制、Unity状态、网络尝试/unknown/计数及后继。更新README和主prompt live块，保留历史；写完整UTF8 NEXT与后继prompt，不省略、不占位、不分段。先确认Unity释放，再chain=handoff_ready、新唯一token、parentID/下一角色；现场list_projects核E:/MyTowerGame，唯一create_thread(target={type:project,projectId:现场ID,environment:{type:local}},prompt:完整文本)，不fork、不子代理、不模型/推理覆盖。创建结果不明先查真实响应/聊天，不重复派发。明确成功响应先落盘，再父最后工作区写chain active新owner/token，随后停止全部工作区写入；一次有界wait_threads确认启动，最终输出真实created-thread directive。失败保完整文件并准确报告。\n\n禁止配置表自动改写、Assets/ConfigJson或Assets/Gen直接写、恢复声音、构建部署、生产删除、Git提交推送、memory修改或擅控桌面。保留历史失败/否决/unknown/计数/安装清单。现在先核所有权、工程和实际源参考，完成WolfMounfed的实际工作。\n'
prompt=prompt.replace('__NEW_TOKEN__',token).replace('__NEW_PARENT__',chain['owner_thread_id']).replace('__NEW_HANDOFF__',rel(handoff))
assert '__NEW_' not in prompt

promptpath.write_text(prompt,encoding='utf-8');(RUN/'NEXT_ENEMY_TASK.md').write_text(prompt,encoding='utf-8')
live_text=f'{now()} WolfHound116已record，105/108，completed_pending_user_art_review/user_approved=false；最终{binding["art_revision"]}，两轮168PASS0FAIL/{runtime["actual_frames"]}PNG，实审14板{review["png_sample_positions"]}采样位/{review["unique_png_samples"]}不同PNG及12GIF各5编码帧。自身Walk500ms，4个Up/Down GIF460–470ms仅Docs修至500ms，4修前保留。AllGIF{archive["after"]}，本角色16=12最终+4历史，源/副本SHA一致。{scope["before_count"]}→{scope["after_count"]}全路径并集{len(scope["changes"])}变化/{scope["added"]}新增/{scope["deleted"]}删除/unexpected0，22生产绑定与prePlay一致；源/meta/原动画/共享C#/其他角色/配置保护。Unity8088 clean Boot非Play/error0。图像2请求2HTTP200/0unknown/0额外恢复，后续本地02像素衍生；其他角色旧unknown和计数保留。下一唯一WolfMounfed117；PossessedWarg79旧Down仍unknown。详见{rel(handoff)}；以实时progress/chain为准。'
for path,begin,end in [(RUN.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),(RUN/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    text=path.read_text(encoding='utf-8');assert text.count(begin)==text.count(end)==1
    a=text.index(begin)+len(begin);b=text.index(end,a);text=text[:a]+'\n'+live_text+'\n'+text[b:]
    if path.name=='README.md':text=text.replace('2026-10-29 本轮当前清单为 1694 个文件','2026-10-29 本轮当前清单为 1710 个文件')
    path.write_text(text,encoding='utf-8')
assert promptpath.read_text(encoding='utf-8')==(RUN/'NEXT_ENEMY_TASK.md').read_text(encoding='utf-8')
item['handoff_file']=rel(handoff);item['successor_character']=NEXT
progress.update(current=NEXT,updated_at=now());(RUN/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
dispatch={'prepared_at':now(),'character':NEXT,'index':117,'dispatch_token':token,'parent_thread_id':chain['owner_thread_id'],
    'project_id':pid,'project_live_confirmed':True,'project_list_response_file':rel(project_list_file),'project_list_response_sha256':sha(project_list_file),
    'created':False,'response_file':rel(HERE/('successor_creation_response_final_'+stamp+'.json')),'progress_sha256':sha(RUN/'progress.json')}
for key,path in [('prompt',promptpath),('handoff',handoff),('assessment',HERE/'successor_assessment_final_20261029.json'),('unity_release',release),('next_task',RUN/'NEXT_ENEMY_TASK.md')]:
    dispatch[key+'_file']=rel(path);dispatch[key+'_sha256']=sha(path)
save(dispatchpath,dispatch)
chain.setdefault('completed_handoffs',[]).append({'character':NAME,'status':item['status'],'current_stage':'recorded_pending_user_art_review',
    'closed_at':now(),'owner_thread_id':chain['owner_thread_id'],'dispatch_token':chain['dispatch_token'],'handoff_file':rel(handoff),'final_evidence':rel(HERE/'final_validation_20261029.json')})
chain.update(state='handoff_ready',parent_thread_id=chain['owner_thread_id'],current_character=NEXT,dispatch_token=token,
    character_status_at_handoff='not_started',completed_count_snapshot=105,previous_handoff_file=chain.get('last_handoff_file'),
    last_handoff_file=rel(handoff),handoff_sha256=sha(handoff),successor_assessment=dispatch['assessment_file'],progress_sha256_at_handoff=sha(RUN/'progress.json'),
    unity_release_file=rel(release),prepared_dispatch_file=rel(dispatchpath),creation_response_file=dispatch['response_file'],dispatch_ready_for=NEXT,
    successor_created=False,current_stage='handoff_ready_pending_single_successor_creation',resume_character=NEXT,
    resume_stage='Verify new owner/token; inspect WolfMounfed original source and native contract; establish baseline',
    current_blocked=False,blocked_reason=None,blocked_owner_retained=False,no_successor_creation_reason=None,
    handoff_ready_at=now(),updated_at=now(),last_stage_evidence=rel(HERE/'final_validation_20261029.json'))
(RUN/'conversation_chain.json').write_text(json.dumps(chain,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'state':'handoff_ready','character':NEXT,'token':token,'project_id':pid,'prompt_file':str(promptpath),'dispatch_file':str(dispatchpath),'handoff_file':str(handoff)},ensure_ascii=False))
