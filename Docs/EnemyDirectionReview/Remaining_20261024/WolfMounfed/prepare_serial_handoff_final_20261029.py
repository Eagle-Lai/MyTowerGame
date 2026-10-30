from session_current import *
from mcp_call import URL
from PIL import Image
import shutil, uuid, time

chain = owner()
progress = read(RUN / 'progress.json')
item = next(r for r in progress['items'] if r['name'] == NAME)
assert item['status'] == 'completed_pending_user_art_review' and not item['user_approved']
assert progress['completed_count'] == 106
assessment = read(HERE / 'successor_assessment_final_20261029.json')
NEXT = assessment['selected']
assert NEXT == 'Zombie' and assessment['selected_index'] == 118
n = RUN / NEXT
existing = [p for p in n.rglob('*') if p.is_file()]
assert len(existing) == 8 and all(p.is_relative_to(n / 'reference') for p in existing)
t = next(t for t in read(RUN / 'local_baseline.json')['targets'] if t['name'] == NEXT)
six = {p: sha(ROOT / p) for k in ['battle', 'source', 'atlas'] for p in [t[k], t[k] + '.meta']}
assert all(sha(n / 'reference' / Path(p).name) == digest for p, digest in six.items())
oldblock = read(RUN / 'PossessedWarg/blocked_20261026_125634_639300.json')
assert sha(RUN / 'PossessedWarg/generation/Down/request.json') == oldblock['request_sha256']
assert not any((RUN / 'PossessedWarg/generation/Down' / s).exists() for s in ['raw.png', 'result.json'])
binding = read(HERE / 'final_version_binding_20261029.json')
runtime = read(HERE / 'runtime_summary.json')
review = read(HERE / 'visual_review_final_20261029/review.json')
archive = read(HERE / 'gif_archive_verification_20261029.json')
final = read(HERE / 'final_validation_20261029.json')
scope = read(HERE / 'scope_incremental_final_20261029.json')
assert final['record_completed'] and final['completed_count'] == 106 and archive['after'] == 1726
assert not final['original_semantics_pass'] and final['precise_head_binding_repair_pass']
assert snapshot() == binding['all_production_fingerprints']
project_list_file = HERE / 'project_list_response_final_20261029.json'
raw = read(project_list_file)
projects = raw.get('structuredContent') or json.loads(next(r['text'] for r in raw['content'] if r['type'] == 'text'))
matches = [p for p in projects['projects'] if p.get('path', '').replace('\\', '/').rstrip('/').lower() == 'e:/mytowergame']
assert len(matches) == 1 and matches[0]['hostId'] == 'local'
pid = matches[0]['projectId']

c = Client()
project = c.identity()
errors = c.tool('read_console', {'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json'})
compile_errors = c.tool('read_console', {'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json', 'filter_text': 'error CS'})
def logs_data(value):
    value = value.get('structuredContent') or json.loads(value['content'][0]['text'])
    assert value['success']
    return value['data']
assert logs_data(errors) == logs_data(compile_errors) == []
def refresh_state_cache():
    code = 'var t=System.Linq.Enumerable.FirstOrDefault(System.Linq.Enumerable.Select(System.AppDomain.CurrentDomain.GetAssemblies(),a=>a.GetType("MCPForUnity.Editor.Services.EditorStateCache")),x=>x!=null);if(t!=null){var m=t.GetMethod("ForceUpdate",System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic);if(m!=null)m.Invoke(null,new object[]{"WolfMounfed factual handoff snapshot"});}return true;'
    c.tool('execute_code', {'action': 'execute', 'code': code})
refresh_state_cache()
state = c.resource('mcpforunity://editor/state')
live = probe(c)
idle(live)
v = state['data']
refresh = None
if v['assets']['external_changes_dirty']:
    refresh = c.tool('refresh_unity', {'mode': 'force', 'scope': 'all', 'compile': 'none', 'wait_for_ready': True})
    for attempt in range(20):
        refresh_state_cache()
        state = c.resource('mcpforunity://editor/state')
        v = state['data']
        if v['advice']['ready_for_tools'] and not v['compilation']['is_compiling'] and not v['compilation']['is_domain_reload_pending'] and not v['assets']['is_updating'] and not v['assets']['external_changes_dirty']:
            break
        time.sleep(1)
    c.identity()
    live = probe(c)
    idle(live)
assert v['advice']['ready_for_tools'] and not v['tests']['is_running'] and not v['compilation']['is_compiling'] and not v['compilation']['is_domain_reload_pending'] and not v['assets']['is_updating'] and not v['assets']['external_changes_dirty']
assert snapshot() == binding['all_production_fingerprints']

stamp = datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
token = 'wolfmounfed-to-zombie-' + stamp + '-' + str(uuid.uuid4())
rel = lambda p: p.relative_to(ROOT).as_posix()
handoff = RUN / 'conversation_handoffs' / (stamp + '_WolfMounfed_completed.md')
promptpath = n / ('successor_prompt_' + stamp + '.txt')
release = HERE / 'handoff_release_final_20261029.json'
dispatchpath = HERE / 'prepared_successor_dispatch_final_20261029.json'
accounting = HERE / 'generation_final_accounting_20261029.json'
assert all(not p.exists() for p in [handoff, promptpath, release, dispatchpath, accounting])
assert {p.relative_to(HERE).as_posix() for p in (HERE / 'generation').rglob('request.json')} == {'generation/Up/request.json', 'generation/Down/request.json'}
attempts = []
for direction in ['Up', 'Down']:
    folder = HERE / 'generation' / direction
    result = read(folder / 'result.json')
    request = read(folder / 'request.json')
    assert result['status'] == 200 and request['model'] == 'gpt-image-2' and request['n'] == 1
    assert request['resolve_transport']['ip'] == '191.101.132.254'
    with Image.open(folder / 'raw.png') as im:
        fmt, size, mode = im.format, list(im.size), im.mode
    attempts.append({'folder': folder.relative_to(HERE).as_posix(), 'request_sha256': sha(folder / 'request.json'),
                     'status': result['status'], 'raw_sha256': sha(folder / 'raw.png'), 'raw_bytes': (folder / 'raw.png').stat().st_size,
                     'response_sha256': sha(folder / 'result.json'), 'actual_format': fmt, 'actual_size': size, 'actual_mode': mode,
                     'transport': request['transport'], 'resolve_transport': request['resolve_transport'],
                     'charge': 'Not independently verified; usage in response is a local estimate.'})
save(accounting, {'observed_at': now(), 'requests': attempts, 'authenticated_image_requests': 2, 'http200': 2,
                  'unknown': 0, 'additional_network_recovery_used': 0, 'new_paid_art_revisions': 0, 'paid_diagnostics': 0,
                  'local_revisions_are_not_AI_returns': True, 'counters_reset': False,
                  'other_character_unknowns': 'PossessedWarg original Down, WinterWolfTypeA old three Down outcomes and WinterWolfTypeB initial Up remain unchanged. No reissue or inference about charge.'})
save(release, {'observed_at': now(), 'project': project, 'transport': URL, 'success': True,
               'editor_state': state, 'final_probe': live, 'errors': errors, 'compile_errors': compile_errors,
               'asset_refresh_to_clear_pending_external_changes': refresh,
               'all_production_unchanged_since_final_binding': True, 'next_protected_six': six, 'protocol_history': c.history})
backup = HERE / ('docs_before_final_handoff_' + stamp)
backup.mkdir()
for p in [RUN / 'conversation_chain.json', RUN / 'progress.json', RUN / 'NEXT_ENEMY_TASK.md', RUN / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md', RUN.parent / 'README.md']:
    shutil.copy2(p, backup / p.name)

summary = f'''# WolfMounfed117 完成与 Zombie118 唯一串行交接

时间 {now()}。父线程 {chain['owner_thread_id']}；旧token {chain['dispatch_token']}。WolfMounfed已record为completed_pending_user_art_review、user_approved=false，总进度106/108。剩余PossessedWarg79 blocked、Zombie118；下一唯一Zombie。创建明确成功并登记新owner/token前，后继只读。

最终美术{binding['art_revision']}，生产版本{binding['asset_revision']}。Up/Down各自初次HTTP200图的本地01衍生，原raw保留。Up第2/3头误为正脸，采用第1个无脸后脑用于三表情；整条腿的内部按源灰褐平面/高光与赭斑重画，保外轮廓，去前趾线并做平滑后跟。Down躯干误带两只前爪，按记录的弧形胸下轮廓移除，保鞍具和四条独立腿。自身灰褐/橄榄斑狼、尖耳、小黑瞳象牙眼、犬齿、四短腿、宽长下垂尾；一个分段金鞍及后缘三象牙刺、解剖左侧一个银灰X圆扣均属于BODY，无骑手/项圈。layout02埋足尾根且远腿多数遮挡，Up尾根在臀下，Down尾下垂在后。14透明分件、2048atlas、PPU100，alpha01为0孔洞/0尘点。原图、本地01、alpha/layout修前均保留，不能full-stage/pack覆盖最终暂存。

仅安装本角色battle及Directions，installed_manifest永久保留。初轮runtime_r01在静态检查因原battle的HeadSprites=[]抛IndexOutOfRange，后续UpWalk超时；该失败轮0帧及两异常保留。没有修改共享C#或测试器。最小修复仅填当前battle已有MonsterAnimEventReceiver.HeadSprites为自身原WolfMounted atlas的HeadNormal/HeadAngry/HeadDead；HeadRenderer及其他原字段未改。通用原组件语义报告仍为false，原文与单个original_component_changed保留；独立严格门核空数组→精确3个本atlasGUID/fileID、组件其余canonical字段不变、无其他原组件差异、修复manifest和prefab SHA一致，scoped pass=true。不得把它改写为original_semantics_pass=true或弱化共享审计。

battle SHA {binding['production_fingerprints']['Assets/Prefabs/Enemy/Enemy_WolfMounfed.prefab']}。22生产绑定包含battle/meta、Directions根meta及全部文件，17暂存文件、初安装manifest/Verify与修复manifest/Verify均绑定到preplay_version_binding_r02_20261029.json。最终现场Verify PASS，14sprite rect/pivot/PPU100一致、Multiple/alphaTransparency=true/mipmap=false、依赖通过。完整原controller/Ready/Walk/Attack/Death结构化合同及原件保留；Ready/Walk/Attack=.5s、Death=.416666657s，float24/33/48/39、PPtr0，原事件保持。source prefab/atlas/meta和原动画未改。

最终两轮真实Play：runtime_r02为84PASS0FAIL、{runtime['runtime'][0]['frames']}PNG，records SHA {runtime['runtime'][0]['records_sha256']}；runtime_updeath_r02为84PASS0FAIL、{runtime['runtime'][1]['frames']}PNG，records SHA {runtime['runtime'][1]['records_sha256']}。合计168PASS0FAIL、600真实PNG，均自动返回clean Boot。覆盖四向/斜向滞回/近零、状态/头事件、连续转向保相位、受击/致死白闪结束、死亡旋转收缩淡出、自动回收同实例复用、暂停恢复/1x2x3x及测试器Flying探针。旧失败轮不能作为最终轮。final_version_binding含所有实际PNG/JSONL/检查/媒体SHA与版本绑定。

实际查看完整原atlas/source、最终离线四向和14分件、两轮four_directions、runtime strip及14张时序/原生循环/GIF解码板。{review['png_sample_positions']}采样位/{review['unique_png_samples']}张不同真实PNG，12最终GIF各5编码帧共60；另看未裁Up、Down愤怒攻击、Up死亡、复用、双向GIF整帧。所审样本足尾根连接、短步尾摆错相、原左右步态、攻击头事件与蓄力发力、白闪结束、死亡和复用正常，无地面影、重复器官或矩形补色缝。死亡按renderer淡出，重叠分件可见。未实时播放GIF，也未逐张审完全部600PNG，不声称一体alpha；仍待用户美术审核。

自身Walk500ms，4个Up/Down GIF原470ms，仅Docs按真实normalized phase累计10ms边界修至500ms，4份修前GIF及两manifest保留；两个原500ms双向GIF未重写。AllGIF {archive['before']}→{archive['after']}，本角色16来源=12当前审核版+4历史时长版，源/集中副本SHA一致，全部旧来源哈希保留。

图像正式认证请求2：Up初次HTTP200/raw1424303bytes，Down初次HTTP200/raw1593885bytes，实际均PNG RGBA1536×1024。0unknown、0额外网络恢复、0付费美术返修/诊断，费用未独立核实。使用原generate_character.ps1/generate.mjs与WolfMounfed专用owner/token包装；保用户--resolve aihub.dog:443:191.101.132.254，进程内NO_PROXY=aihub.dog并暂清HTTP_PROXY/HTTPS_PROXY/ALL_PROXY、finally恢复。未改共享生成器/hosts/系统代理/TLS；本地像素衍生不是AI返回。其他角色旧unknown及standing耗用保留，PossessedWarg Down不重发。

Assets/Packages/ProjectSettings/Luban路径5665→5685，并集22变化/20新增/0删除/unexpected0；仅本battle、Directions含根meta及Reporter build_info。ReporterEditor未改，build_info的机器名/精确本地时间格式/真实Play时间窗匹配才单列。源/meta、原动画、共享C#、其他角色、配置、首批批准保护；历史global scope失败不重标PASS。当前generic semantic false及本次定点修复差异已明确记录。

Unity8088动态核E:/MyTowerGame/2022.3.62f3c1，最新释放单一clean Boot非Play，failed/compile/reload/update/tests/review/balance/recording/manual=false，ready=true/external_changes_dirty=false，error/errorCS0。未主动清控制台；首轮异常已归档，后续Play的编辑器设置可能自动清日志。无构建部署/桌面控制。入口WolfMounfed/final_validation_20261029.json、final_version_binding_20261029.json、scope_incremental_final_20261029.json、visual_review_final_20261029/review.json、gif_archive_verification_20261029.json、gif_quantization_fix_20261029.json、generation_final_accounting_20261029.json、head_binding_repair_r02_20261029.json及handoff_release_final_20261029.json。

下一Zombie118：递归仅8个reference文件，六保护SHA一致。父只核路径/源指纹，未审实际atlas/source图。battle={t['battle']}；source={t['source']}；atlas={t['atlas']}；controller={t['controller']}；Directions={t['art_dir']}。baseline节点名含Body/LegL/LegR/Head/ArmL/ArmR/WeaponAnchor/Weapon/FistR/Shadow，但可见性、装备归属、锚点及源造型须由后继实查，不能将节点名当可见器官，也不继承狼的四足、鞍或尾。

新token {token}，完整prompt {rel(promptpath)}。唯一fresh local后继，保存明确创建响应后父最后写chain active登记新owner/token，然后停止全部工作区写入。Zombie完成后重读队列；若只剩PossessedWarg真实阻断，则链记录blocked和恢复条件后停止，不再为了循环创建多余角色聊天、不重发unknown。
'''
handoff.write_text(summary, encoding='utf-8')

prompt = f'''# Zombie118 唯一接棒执行 Prompt

在E:/MyTowerGame继续敌人四方向续作，本聊天只完成Zombie(index118)。当前106/108，所有completed_pending_user_art_review仅内部完成，尚未用户美术批准。本文是完整UTF8执行说明，不依赖旧聊天图片。完成Zombie后重读队列；只剩真实阻断则准确封存并停止，不创建多余聊天。

## 1. 所有权与开工同步

dispatch_token={token}
父线程={chain['owner_thread_id']}
交接总结={rel(handoff)}
先读E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/Remaining_20261024/conversation_chain.json、progress.json、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、NEXT_ENEMY_TASK.md、Docs/EnemyDirectionReview/README.md和上述交接总结。定向读当前角色文件、git status/相关差异、实现、调用者/依赖/缓存/生命周期；保留全部既有未提交改动。同步不授权git pull/reset/clean/checkout/commit/push。

只有chain.state=active、owner_thread_id为本聊天真实ID、current_character=Zombie且token完全匹配，才能写生产或操作Unity。handoff_ready期间只读限次等待父登记；时间经过不授权抢占。max_active_production_tasks=1，一聊天一角色，禁止子代理/并行角色/fork/定时器/自动化。父先保存明确创建响应，再以最后一次工作区写入登记新owner active，之后停止全部工作区写入。

剩余2项：PossessedWarg79 blocked、Zombie118。108是授权数量，末项index118。PossessedWarg旧Down无raw/result/服务查询ID，结果和费用unknown；不推定未发/未收费，不重发。父递归核Zombie仅8个reference文件，额外写本prompt，没有generation/staged_art/install/runtime；开工重新递归核现场，若已出现阶段则恢复，不盲目prepare/付费生成/安装。

## 2. 工程身份及MCP8088

目标E:/MyTowerGame、Unity2022.3.62f3c1，以ProjectVersion.txt为准。unityMCP HTTP Local http://127.0.0.1:8088/mcp。根AGENTS的FreedomTower_1/D:/8082为旧说明；8082属于FishTestGame、8080属于CatchFish，不操作其他工程，也不为此改根AGENTS。桌面/电脑控制需先弹明确确认；本任务用文件/命令行/Unity MCP，不擅控桌面。

首次/重连/域重载后读mcpforunity://custom-tools及mcpforunity://instances，现场选MyTowerGame完整ID、set_active_instance，再project/info核路径版本。可复用Remaining_20261024/mcp_call.py Client.identity()，loopback禁代理，不硬编码实例hash。服务离线按已有授权恢复目标既有服务/桥接，复用服务，不抢端口/杀其他工程；确需桌面操作仍先确认。无法恢复时说明工程路径、版本、8088故障环节和具体开启/连接步骤。

操作前先读error/errorCS，再state及实际probe，确认无他人Play、脏场景、测试/review/balance/manual/recording/compile/update。前任clean Boot不替代现场核对，不强停后来任务。两轮真实Play已有授权，无需逐角色再问；结束恢复原干净场景。无Unity C#改动不为形式额外编译。若改C#，同批完成后8088 refresh_unity(mode=force,scope=all,compile=request,wait_for_ready=true)，每1–2秒读state直到compile/reload/update=false、ready=true；error/errorCS0、scriptCompilationFailed=false，期间不改代码，断线约5秒重连重核，不清控制台。

## 3. Zombie自身源及动画合同

battle={t['battle']}
source={t['source']}
atlas={t['atlas']}
controller={t['controller']}
Directions={t['art_dir']}

父未审Zombie实际源图。baseline节点名含Body、LegL、LegR、Head、ArmL、ArmR、WeaponAnchor、Weapon、FistR、Shadow等，必须现场核可见性/层级/锚点/归属；节点名称不等于原图确有该器官或装备。实看完整原atlas和source_prefab_offline、原左右图、渲染顺序、全身轮廓、头/手/脚/装备。只保源确有的东西，不能复制WolfMounfed的狼头、四足、金鞍、尾或前任布局，也不从Zombie名称推颜色/破损/武器。

读local_baseline.json、production_fingerprints_before.json、Batch01_10/user_approval_20261023.json和AllGIF/manifest.json。建立Assets/Packages/ProjectSettings/Luban全路径SHA并集基线，battle/source/atlas及三meta六保护；Directions根.meta单列，新增删除都审。定向读BaseEnemy、EnemyDirectionalVisual/Profile、MonsterAnimEventReceiver、EnemyDirectionalRigBuilder/PrefabBuilder/BatchReview、RemainingCatalog/Motion及直接调用、事件/闪白/缓存/回收复用。

捕获自身Giant controller及实际Ready/Walk/Attack/Death等全部相关原clip的完整结构化合同：状态/参数/过渡、所有float/PPtr绑定及完整key/tangent/weight、事件、loop/length/frameRate。不用ToString冒充，不套狼的.5s/绑定数/头事件。Up真后脑无五官/前向耳眼结构，手脚朝向与背面一致；Down真正面及源表情，装备左右归属一致。不加源无装备、不留重复头/手/武器、浮动断肢。保护首批10项用户批准及BlueScorpion最终尾和否决历史。

前任WolfMounfed首轮发现battle已有HeadSprites=[]导致测试静态检查越界，只修当前prefab已有接收器为自身原atlas的3个sprite，未改C#；其generic语义报告仍false，另有严格定点修复门。Zombie必须先查自己源/战斗接收器和原事件，不能照抄该修复或弱化测试/共享审计。若确需最小绑定修复，保修前、原因、精确差异、manifest/Verify与版本绑定，诚实保留原组件差异；全部修好后才绑定并跑最终两轮。

## 4. Image API入口、防重与网络

已有AIHub授权：https://aihub.dog/v1/images/edits，gpt-image-2、medium、n=1、1536x1024。密钥仅运行时从AIHUB_IMAGE_API_KEY或C:/Users/Administrator/.codex/secrets/aihub-image-key.clixml的DPAPI读取，仅送https://aihub.dog，不输出/落盘/进命令行/跨域转发，结束清临时环境。使用现有generate_character.ps1/generate.mjs，先读入口保护，逐方向请求并审阅。

必须保用户Curl参数--resolve aihub.dog:443:191.101.132.254。WolfMounfed本次Up/Down初次均HTTP200，raw1424303/1593885bytes，实际PNG RGBA1536×1024，共2请求0unknown0恢复。读image_transport_edge_map_20261029_1830.md、docs_tooling_edge_resolve_20261029_182840.json、WolfMounfed/generate_initial_direct_20261029.ps1及generation_final_accounting_20261029.json；必要读WinterWolfTypeB/docs_generator_recovery_20261029.json及patch。包装有角色owner/token，须独立适配Zombie，不直接执行前任脚本。

普通入口verifiedDirectTransport可能false。仅调用进程内临时NO_PROXY=aihub.dog，暂清HTTP_PROXY/HTTPS_PROXY/ALL_PROXY并finally恢复，确保Curl直连固定域名边缘；不用--system-local-proxy，不改hosts/系统代理，不禁TLS。Preflight只核输入/路由，不发图请求。若改Docs工具先保SHA/backup/patch，只定点改合法入口，不弱化owner/token、源指纹、已成功图或结果/计数保护。

先查任何request/raw/result/uncertain/revision和在途进程；成功图不重生，unknown不作失败/未收费，超时不盲重发。WinterWolfTypeB初次Up Curl55仍unknown、standing额外1/2；A旧3次Down unknown、standing2/2及A Down03专用max1不可借给Zombie/重置。若同类故障，先核WinterWolfTypeA/standing_authorization_original_messages_20261029.json中原人类回复“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”、范围/已用计数/合法入口，再按授权推进。代理执行界限不是用户金额预算；不删日志/改名绕保护，不用非鉴权401或外部WorkBuddy推理倒推未收费。没有合法恢复路径则准确阻断，不借其他角色付费探测。

## 5. 制作、安装与两轮真实Play

Python统一C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8；子Python用sys.executable。先读character_step.py、prepare_character.py、pack_character.py、adjust_layout.py、render_staged_rig.py、install_character.py、runtime_runner.py、runtime_runner_revision.py、build_runtime_media.py、record_review.py、collect_gifs.py。仅未准备时character_step.py prepare Zombie；按实际源完善anatomy_plan/prompt，实看每张raw后选择。局部像素修改保父图/区域/方法/SHA，标为本地衍生，不冒充AI返回。

按实际矩形分件，不假定格界。去品红、查透明孔洞/尘点/描边污染、slice/PPU/pivot/render order/遮挡，源与新图比例协调；前任14分件/2048只是狼的事实，不套Zombie。完整离线四向及细节实看，头手脚装备不裁、根部连，按实际双足/双臂结构做错相短步与源攻击蓄力发力，不套四足对角步或不存在的尾摆。保原左右曲线/事件/loop/时长，无地面影、矩形补色缝或重复器官。full-stage/pack会覆盖后续alpha修订，先保父版。

安装前重核owner、8088身份、error→state→严格空闲、全路径和六保护。未安装前语义工具缺Directions可能false仅诊断，以六保护+完整路径精确SHA为门。仅安装Zombie并Builder/Verify，不全目录重建、不删installed_manifest。生产battle/meta、Directions所有文件与根meta、全部暂存、安装manifest/Verify及任何精确绑定修复SHA在prePlay绑定后才运行。

普通死亡与Up死亡两轮真实Play，每轮84检查，共168PASS0FAIL；初轮runtime_r01/runtime_updeath_r01，返修用新revision并保旧轮。保actual_frames.jsonl/checks/原PNG/Unity frame/realtime/normalizedTime/SHA，覆盖四向/斜向滞回/近零、实际原状态/头手武器事件、连续转向保相位、受击/致死白闪结束、死亡旋转收缩淡出、自动回收同实例复用、暂停恢复/1x2x3x及适用Flying探针。禁止Animator.Update或离线合成冒充Play。测试期望须依据Zombie实际合同，不照抄狼事件；发现真实缺陷最小修复，禁止减项或伪造PASS。断言通过仍须审画，视觉错误保旧返修、重绑定、重跑最终两轮。

## 6. 视觉审阅、范围与record归档

实看两轮four_directions、runtime strip、足量按时序原PNG、原生循环及每个最终GIF的解码帧，覆盖各动作。一次1–2图，完整原证据留盘；先看未裁再看保头手脚装备的crop，准确记录采样位/不同PNG/GIF帧数/路径/SHA及观察。不能播放就写逐序抽样，不声称实时播放或全帧看完。WolfMounfed600PNG/301采样位/290不同PNG只是历史，不可抄为Zombie计数。

解码GIF实际总时长并比Zombie自身Walk合同，不从前任推.5s。Pillow逐帧10ms截断可能缩短；需修时仅Docs保原GIF/manifest，按真实normalized phase累计边界量化10ms并保持合同总时长，不合成姿态。可读WolfMounfed/prepare_visual_closeout_20261029.py，其本轮4个470→500ms、两个原500ms双向GIF未改只是历史，Zombie数量现场算。

最终全路径并集含新增/删除/Directions根meta，保护源/meta、原动画、共享C#、其他角色/配置。Reporter build_info只在ReporterEditor未改、精确机器名/本地时间格式/实际Play时间窗匹配才单列；历史global scope失败不重标PASS。任何原组件修复差异如实保留，精确门不能冒充generic pass。最终生产/暂存/安装与修复manifest/Verify须匹配prePlay，同版绑定实际记录/PNG/媒体SHA。现场核import/rect/pivot/PPU/alpha/依赖/Verify收集器、errors0/failedfalse、单一clean Boot非Play全空闲，不构建发布包。

UTF8真实visual_note先写Zombie/record_note_utf8.txt，再从文件读传character_step.py record Zombie，避免PowerShell中文参数损坏。仅completed_pending_user_art_review、user_approved=false。record会collect_gifs，逐个核本角色所有GIF源/集中副本SHA、最终/修前/否决分类，保全部旧来源哈希；起点AllGIF1726仅父本轮事实，现查数量。保存final_validation/version_binding/scope/review/archive/network accounting及Unity release。成功后应107/108，仅PossessedWarg阻断；不误写108/108或全部完成。

## 7. 最终串行收口

完成Zombie或记录真实阻断后先安全交回Unity，重读实时progress并递归所有未完成材料，优先可独立恢复的已开始项，再按index；不机械用progress.current。PossessedWarg旧Down仍unknown且无合法恢复时，只剩真实阻断，应记录chain=blocked、准确恢复条件、最终已完成数量、所有权及时间，总结后停止；不重发旧unknown、不用其他角色探测，不为了循环空建后继或创建定时器。待用户美术审核不算阻断，但也不能写用户批准。

写带时间Zombie handoff，记录实际修改/revision/指纹、两轮计数、审阅范围/限制、Unity状态、网络尝试/unknown/耗用及剩余阻断；更新README和主prompt实时块，保历史，并把NEXT_ENEMY_TASK完整写成实际停止状态和可执行恢复条件。若现场确有独立可恢复的未完成角色且已有合法授权，才按协议handoff_ready/new token、live list_projects、唯一fresh local create_thread完整prompt；明确创建响应先落盘，再父最后写chain active新owner/token后停止全部写入，一次有界wait_threads确认启动。结果不明先查真实响应/列表，不重复创建；不fork/子代理/并行/模型或推理覆盖。

禁止自动改配置表、直接写Assets/ConfigJson或Assets/Gen、恢复声音、构建部署、生产删除、Git提交推送、memory修改或擅控桌面。保所有历史失败/否决/unknown/计数/安装清单。现在核所有权、现场身份及实际Zombie源参考，完成Zombie本身的实际工作。
'''
assert token in prompt and 'index118' in prompt and len(prompt) > 7500
promptpath.write_text(prompt, encoding='utf-8')
(RUN / 'NEXT_ENEMY_TASK.md').write_text(prompt, encoding='utf-8')
live_text = (
    f'{now()} WolfMounfed117已record，106/108，completed_pending_user_art_review/user_approved=false；最终{binding["asset_revision"]}，'
    f'两轮runtime_r02/runtime_updeath_r02共168PASS0FAIL/600PNG，实审14板301采样位/290不同PNG、12GIF各5编码帧。'
    f'Walk500ms，4个Up/Down GIF470→500ms仅Docs修时长，原件保留；AllGIF{archive["after"]}，本角色16=12最终+4历史，源/副本SHA一致。'
    '5665→5685全路径并集22变化/20新增/0删除/unexpected0，22生产绑定与prePlay一致。原battle空HeadSprites补为自身atlas三表情，'
    'generic原组件语义报告仍false且保留，严格精确修复门通过；首轮0帧失败和两异常保留，无C#改动。源/meta/原动画/共享C#/其他角色/配置保护。'
    f'Unity8088 clean Boot非Play/error0；图像2请求2HTTP200/0unknown/0恢复，本地01衍生，其他角色unknown/计数保留。'
    f'下一唯一Zombie118，完成后若只剩PossessedWarg79旧Down unknown则准确blocked收口，不空建后继。详见{rel(handoff)}，以实时progress/chain为准。'
)
for path, begin, end in [(RUN.parent / 'README.md', '<!-- ENEMY_README_LIVE_BEGIN -->', '<!-- ENEMY_README_LIVE_END -->'),
                         (RUN / 'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md', '<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->', '<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    text = path.read_text(encoding='utf-8')
    assert text.count(begin) == text.count(end) == 1
    a = text.index(begin) + len(begin)
    b = text.index(end, a)
    text = text[:a] + '\n' + live_text + '\n' + text[b:]
    if path.name == 'README.md':
        text = text.replace('2026-10-29 本轮当前清单为 1710 个文件', '2026-10-29 本轮当前清单为 1726 个文件')
    path.write_text(text, encoding='utf-8')
assert promptpath.read_text(encoding='utf-8') == (RUN / 'NEXT_ENEMY_TASK.md').read_text(encoding='utf-8')
item['handoff_file'] = rel(handoff)
item['successor_character'] = NEXT
progress.update(current=NEXT, updated_at=now())
(RUN / 'progress.json').write_text(json.dumps(progress, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
dispatch = {'prepared_at': now(), 'character': NEXT, 'index': 118, 'dispatch_token': token, 'parent_thread_id': chain['owner_thread_id'],
            'project_id': pid, 'project_live_confirmed': True, 'project_list_response_file': rel(project_list_file),
            'project_list_response_sha256': sha(project_list_file), 'created': False,
            'response_file': rel(HERE / ('successor_creation_response_final_' + stamp + '.json')), 'progress_sha256': sha(RUN / 'progress.json')}
for key, path in [('prompt', promptpath), ('handoff', handoff), ('assessment', HERE / 'successor_assessment_final_20261029.json'),
                  ('unity_release', release), ('next_task', RUN / 'NEXT_ENEMY_TASK.md')]:
    dispatch[key + '_file'] = rel(path)
    dispatch[key + '_sha256'] = sha(path)
save(dispatchpath, dispatch)
chain.setdefault('completed_handoffs', []).append({'character': NAME, 'status': item['status'], 'current_stage': 'recorded_pending_user_art_review',
    'closed_at': now(), 'owner_thread_id': chain['owner_thread_id'], 'dispatch_token': chain['dispatch_token'],
    'handoff_file': rel(handoff), 'final_evidence': rel(HERE / 'final_validation_20261029.json')})
chain.update(state='handoff_ready', parent_thread_id=chain['owner_thread_id'], current_character=NEXT, dispatch_token=token,
    character_status_at_handoff='not_started', completed_count_snapshot=106, previous_handoff_file=chain.get('last_handoff_file'),
    last_handoff_file=rel(handoff), handoff_sha256=sha(handoff), successor_assessment=dispatch['assessment_file'],
    progress_sha256_at_handoff=sha(RUN / 'progress.json'), unity_release_file=rel(release), prepared_dispatch_file=rel(dispatchpath),
    creation_response_file=dispatch['response_file'], dispatch_ready_for=NEXT, successor_created=False,
    current_stage='handoff_ready_pending_single_successor_creation', resume_character=NEXT,
    resume_stage='Verify new owner/token; inspect Zombie original source and Giant native contract; establish baseline',
    current_blocked=False, blocked_reason=None, blocked_owner_retained=False, no_successor_creation_reason=None,
    handoff_ready_at=now(), updated_at=now(), last_stage_evidence=rel(HERE / 'final_validation_20261029.json'))
(RUN / 'conversation_chain.json').write_text(json.dumps(chain, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'state': 'handoff_ready', 'character': NEXT, 'token': token, 'project_id': pid,
                  'prompt_file': str(promptpath), 'prompt_characters': len(prompt), 'dispatch_file': str(dispatchpath),
                  'handoff_file': str(handoff)}, ensure_ascii=False))
