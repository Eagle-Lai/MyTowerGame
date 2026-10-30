from session_current import *
from mcp_call import URL
import shutil,uuid,time

chain=owner();progress=read(RUN/'progress.json')
item=next(r for r in progress['items'] if r['name']==NAME)
assert item['status']=='completed_pending_user_art_review' and not item['user_approved'] and progress['completed_count']==102
assessment=read(HERE/'successor_assessment_final_20261029.json')
NEXT=assessment['selected'];assert NEXT=='WinterWolfTypeB'
n=RUN/NEXT;existing=[p for p in n.rglob('*') if p.is_file()]
assert len(existing)==8 and all(p.is_relative_to(n/'reference') for p in existing)
t=next(t for t in read(RUN/'local_baseline.json')['targets'] if t['name']==NEXT)
six={p:sha(ROOT/p) for k in ['battle','source','atlas'] for p in [t[k],t[k]+'.meta']}
assert all(sha(n/'reference'/Path(p).name)==h for p,h in six.items())
oldblock=read(RUN/'PossessedWarg/blocked_20261026_125634_639300.json')
assert sha(RUN/'PossessedWarg/generation/Down/request.json')==oldblock['request_sha256']
assert snapshot()==read(HERE/'final_version_binding_20261029.json')['all_production_fingerprints']
c=Client();project=c.identity()
errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
compile_errors=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json','filter_text':'error CS'})
def logs_data(result):
    value=result.get('structuredContent') or json.loads(result['content'][0]['text'])
    assert value['success'];return value['data']
assert logs_data(errors)==logs_data(compile_errors)==[]
state=c.resource('mcpforunity://editor/state');live=probe(c);idle(live);v=state['data'];refresh=None
if v['assets']['external_changes_dirty']:
    refresh=c.tool('refresh_unity',{'mode':'force','scope':'all','compile':'none','wait_for_ready':True})
    for attempt in range(20):
        state=c.resource('mcpforunity://editor/state');v=state['data']
        if v['advice']['ready_for_tools'] and not v['compilation']['is_compiling'] and not v['compilation']['is_domain_reload_pending'] and not v['assets']['is_updating'] and not v['assets']['external_changes_dirty']:break
        time.sleep(1)
    live=probe(c);idle(live)
assert v['advice']['ready_for_tools'] and not v['tests']['is_running'] and not v['compilation']['is_compiling'] and not v['compilation']['is_domain_reload_pending'] and not v['assets']['is_updating'] and not v['assets']['external_changes_dirty']
stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
token='winterwolftypea-to-winterwolftypeb-'+stamp+'-'+str(uuid.uuid4())
rel=lambda p:p.relative_to(ROOT).as_posix()
handoff=RUN/'conversation_handoffs'/(stamp+'_WinterWolfTypeA_completed.md')
promptpath=n/('successor_prompt_'+stamp+'.txt')
release=HERE/'handoff_release_final_20261029.json'
dispatchpath=HERE/'prepared_successor_dispatch_final_20261029.json'
assert all(not p.exists() for p in [handoff,promptpath,release,dispatchpath])
assert snapshot()==read(HERE/'final_version_binding_20261029.json')['all_production_fingerprints']
save(release,{'observed_at':now(),'project':project,'transport':URL,'success':True,'editor_state':state,'final_probe':live,'errors':errors,'compile_errors':compile_errors,'asset_refresh_to_clear_pending_external_changes':refresh,'all_production_unchanged_since_final_binding':True,'next_protected_six':six,'protocol_history':c.history})
backup=HERE/('docs_before_final_handoff_'+stamp);backup.mkdir()
for p in [RUN/'conversation_chain.json',RUN/'progress.json',RUN/'NEXT_ENEMY_TASK.md',RUN/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md',RUN.parent/'README.md']:shutil.copy2(p,backup/p.name)

summary=f'''# WinterWolfTypeA113 完成与 WinterWolfTypeB114 唯一串行交接

时间 {now()}。父线程 {chain['owner_thread_id']}，旧token {chain['dispatch_token']}。WinterWolfTypeA已通过record，状态completed_pending_user_art_review，user_approved=false。总进度102/108，剩余6项：PossessedWarg79 blocked、WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118。唯一下一角色WinterWolfTypeB，未创建后继前保持handoff_ready；只有创建明确成功并登记新owner/token后后继可开始生产。

最终美术Up_local03_Down03_alpha_r01_layout_r01：Up为成功原图的本地03像素修订，移除重复躯干耳和后趾线，平涂后跟内侧保留描边；Down03 HTTP200，实际分件区域避开额外后脑。14透明分件、2048atlas、PPU100，填69封闭色键微孔，尾宽0.30。棕橄榄背/赭圆斑/高尖耳/白眉白口鼻宽白胸/四短犬腿白爪/整条象牙taupe尾；无项圈鞍背刺，原左右侧图保留。原件、修前alpha、布局和选图证据均保留，不重跑prepare或full stage覆盖清理版。

安装清单installed_manifest.json永久保留，Builder/Verify全PASS。battle SHA711B88DCA3A10F847A5A3BDEED7AAD18781C92C37B4AC0CFE2F9A7666344AE43；22个生产绑定含Directions根.meta和battle.meta，与preplay一致；17个暂存文件不变。原source/atlas及meta、battle.meta、Wolf原float/PPtr/事件/loop/时长和非美术语义受保护。现场导入14sprite的rect/pivot/PPU与暂存逐项匹配，Multiple/alphaTransparency=true/mipmap=false；依赖和现有YooAsset收集器Verify通过，无发布构建。

最终两轮真实Play：runtime_r01 84PASS/0FAIL、331PNG、records SHA470BBD1A87E173BA6ECBD9AE51CA940C5EF18A52C2D77A5148A4C09345FEB1AA；runtime_updeath_r01 84PASS/0FAIL、337PNG、records SHAE8C5C2C88104EFD44150B4CB1AC6735B55C85B3C080D2E90F4575CE708EF9608。总168PASS0FAIL、668原始PNG，均最终版本安装后运行并返回Boot；完整指纹在final_version_binding_20261029.json。

实际看过两轮four_directions、runtime_visual_strip、14张完整角色时序/原生循环/GIF抽帧板，313个采样位/301不同真实PNG，12最终GIF各5编码帧共60帧；另看未裁原生Up、Down张嘴攻击、Up死亡连接、Down复用及最终双向GIF整帧。所审样本四向步态、原生状态、攻击/白闪恢复、Up/Down死亡旋转淡出、回收复用、暂停恢复/1x2x3x、连续转向与Flying保持连接，无地面阴影。未实时播放或全帧审完668张。原逐renderer死亡alpha会显出重叠层，不把它伪报为一体alpha。

GIF实解码发现Up470ms/Down480ms；仅Docs以真实native phase累计10ms量化修至原Walk500ms，PNG及生产不变。六个修前GIF/manifest保留。AllGIF1642→1660，本角色18来源=12最终+6旧时长，源与集中副本SHA全匹配，所有旧来源哈希保留。状态只待用户审核。

用户已改generate.mjs，Curl固定 --resolve aihub.dog:443:191.101.132.254。当前Down03直连HTTP200、raw1550181bytes，无本轮付费诊断。前三次Down结果和费用仍unknown，standing2/2已消耗且不重置；本次独立max1为代理执行界限，不是用户金额预算。authorized_edge_resume和原始日志、user-edge-fix-before副本及patch保留；不能把A专用恢复权限复制给B。WorkBuddy边缘报告是外部证据，不倒推旧请求未发送/未计费，也不采信PossessedWarg未发送说法。B首次请求直接使用Curl+固定域名TLS，不走system-local-proxy；注意首次普通请求的verifiedDirectTransport=false，须在当前进程设置NO_PROXY=aihub.dog并暂清HTTP_PROXY/HTTPS_PROXY/ALL_PROXY等，结束恢复原值，确保不会经代理绕开固定边缘。不得改系统hosts、TLS或跨域送密钥。

完整路径并集Assets/Packages/ProjectSettings/Luban5585→5605，22变化、20新增、0删除、unexpected0：仅当前battle、Directions含根meta以及未改ReporterEditor确证自动Play时间戳build_info。共享C#、其他角色和配置无本轮漂移；历史全局scope失败保留，未称全局PASS。无UnityC#改动，未额外编译。最终正确8088身份、clean Boot、非Play/dirty、failed/compile/reload/update/tests/review/recording/balance/manual=false、ready=true、external_changes_dirty=false，error/errorCS0；未清日志、未控制桌面。

最终入口：WinterWolfTypeA/final_validation_20261029.json、final_version_binding_20261029.json、scope_incremental_final_20261029.json、visual_review_final_20261029/review.json、gif_archive_verification_20261029.json、gif_quantization_fix_20261029.json、unity_release_final_20261029.json、handoff_release_final_20261029.json、runtime_summary.json与record_note_utf8.txt。旧blocked交接仅历史，不覆盖或回退。

下一WinterWolfTypeB仅8个reference文件，六保护匹配；本父未审其源图或生成/暂存/安装/运行。实际battle={t['battle']}；source={t['source']}；atlas={t['atlas']}；controller={t['controller']}；Directions={t['art_dir']}。独立查看完整源atlas/prefab与原动画、四腿尾根和锚点，不复制A的色彩/耳/体形/布局。PossessedWarg旧request哈希与阻断一致，无Down raw/result/可查询ID，继续保留unknown。新token {token}；完整prompt {rel(promptpath)}。只创建一个fresh local新聊天，不fork/子代理/并行/定时器/模型覆盖；创建成功响应先落盘，父最后写chain转active新owner，此后父只读。
'''
handoff.write_text(summary,encoding='utf-8')
prompt=f'''# WinterWolfTypeB114 唯一接棒执行 Prompt

在E:/MyTowerGame继续敌人四方向续作。当前唯一目标WinterWolfTypeB(index114)，先读文件并核对链所有权，再实际完成一个角色，最后按协议创建唯一后继。总进度102/108，状态completed_pending_user_art_review仅表示内部完成，用户未美术批准。本文件是完整UTF8接棒说明，不依赖旧聊天图片。

## 1. 唯一所有权和开工同步

dispatch_token={token}
父线程={chain['owner_thread_id']}
先读E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/Remaining_20261024/conversation_chain.json、progress.json、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、NEXT_ENEMY_TASK.md、Docs/EnemyDirectionReview/README.md和{rel(handoff)}。先读本角色已有reference及实际材料、git status和相关差异。全工程既有未提交工作必须保留；同步不授权git pull/reset/clean/checkout、commit/push。

只有chain.state=active、owner_thread_id等于本新聊天实际ID、current_character=WinterWolfTypeB且token完全匹配后才能改生产或操作Unity。若handoff_ready，限次只读等父登记，不能超时抢占；token或owner不匹配则不动生产。max_active_production_tasks=1，一次只做一个角色，不启动子代理、并行角色、fork、自动化或定时器。父会先记录create_thread明确成功响应，再最后写入active新owner并停止工作区写入。

实时队列剩余6项：PossessedWarg79 blocked、WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118。108是授权项数，末项index118，WolfMounfed原拼写保留。PossessedWarg Down旧请求结果未知，不把request存在解释为未发送/未收费，不重发。当前已递归核实B只有8个reference文件，无generation/staged_art/install/runtime；在你开工时再核实，恢复新增阶段而不盲目从prepare开始。

## 2. 正确Unity路由与用户边界

目标E:/MyTowerGame、Unity2022.3.62f3c1，现场版本文件为准；unityMCP HTTP http://127.0.0.1:8088/mcp。根AGENTS的FreedomTower_1/D:/8082是旧信息；8082当前属于FishTestGame、8080属于CatchFish，不改根AGENTS、不操作其他工程。用户要求控制电脑前弹确认；本任务用文件/命令行和Unity MCP，不得擅自控制桌面。

首次/重连/域重载动态读mcpforunity://custom-tools及instances，选MyTowerGame完整ID，set_active_instance，再读project/info核路径版本。可复用已审mcp_call.py Client.identity()直连8088，loopback禁代理，不硬编码实例hash。离线按项目规则自主恢复已有服务桥接、不抢端口、不杀其他工程；桌面控制确需时遵守用户确认要求。无法恢复须说明工程/版本/服务8088和具体启动连接动作。

操作前先读取error/errorCS日志，再读editor/state和实际probe，确保无他人Play、录像、测试、review、balance/manual、编译或脏场景。前任已交回clean Boot，不能据旧快照强停后来任务。当前角色两轮真实Play已有授权，不逐角色再问。测试完成安全交回原干净场景。

## 3. 源参考、身份与原动画合同

battle={t['battle']}
source={t['source']}
atlas={t['atlas']}
controller={t['controller']}
Directions={t['art_dir']}

读local_baseline.json、production_fingerprints_before.json、Batch01_10/user_approval_20261023.json和AllGIF/manifest.json；建立Assets/Packages/ProjectSettings/Luban全路径SHA基线及本角色battle/source/atlas与三meta六保护，Directions根.meta也单列。按当前实现查看BaseEnemy、EnemyDirectionalVisual/Profile、MonsterAnimEventReceiver、EnemyDirectionalRigBuilder、PrefabBuilder、BatchReview、RemainingCatalog/Motion及直接调用和生命周期。

实看完整atlas和源prefab，不根据WinterWolfTypeA名字猜色彩或器官，不复制前任布局。先读自身骨架、四足/尾/头/锚点、渲染层级、左右原图；捕获自身原native Ready/Walk/Attack/Death及controller状态参数、所有float/PPtr曲线、key/事件/loop/时长和rate。不得用ToString对象冒充结构化合同。Up真后脑无脸/后跟，Down真正面/前趾；无重复头耳、漂浮肢体、断颈或原型没有装备。首批10项批准、BlueScorpion最终尾方案和否决历史保护不变。

## 4. 已修复图像传输与请求保护

用户说“我已做generate.mjs修改”，现Curl参数含--resolve aihub.dog:443:191.101.132.254。前任WinterWolfTypeA Down03已通过这条直接TLS域名路线HTTP200，raw1550181bytes，非付费诊断；仅作为工作路线的当前证据，不把外部WorkBuddy推理当旧请求状态。读image_transport_edge_map_20261029_1830.md、docs_tooling_edge_resolve_20261029_182840.json以及WinterWolfTypeA/authorized_edge_resume_20261029.json、edge_resume_success_and_raw_review_20261029.json、docs_generator_edge_resume_guard_20261029.json与patch。保留用户修改和所有防重/owner/token/计数保护。

用generate_character.ps1/generate.mjs既有首次入口，Curl/gpt-image-2/medium/n1/1536x1024，逐方向审核，不批量盲跑。不要--system-local-proxy。普通首次入口verifiedDirectTransport可能为false；在调用请求的进程内临时设置NO_PROXY=aihub.dog，并暂清HTTP_PROXY/HTTPS_PROXY/ALL_PROXY，finally恢复原值，确保Curl直连固定边缘；不改系统hosts/代理设置，不禁TLS。可先-Preflight核输入/路由，preflight不发图请求。后续若确需改Docs工具，先保存原SHA与backup/patch，仅做必要定点变更，不弱化防重。

Key仅运行时从AIHUB_IMAGE_API_KEY或C:/Users/Administrator/.codex/secrets/aihub-image-key.clixml DPAPI读取，授权只到https://aihub.dog/v1；不得输出、明文落盘、放进进程参数或跨域转发，结束清理临时环境。任何request/raw/result/uncertain/revision先检查实际结果及在途进程，成功图不重生；失败与结果未知分开保存，超时不盲发。当前A前三次Down结果/费用仍unknown、standing2/2已消耗不能重置；A本轮Down03专用max1许可不能套到B。已有原始standing授权遇同类故障先核适用范围、已有耗用与证据，任何工具恢复入口都不可通过改名/删除日志绕过保护；网络发生新未知且无合法恢复路径则准确阻断，不能用别的角色付费探测。

## 5. 逐阶段完成美术、安装和真实运行

Python统一C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8，子进程用sys.executable。读character_step.py、prepare_character.py、pack_character.py、adjust_layout.py、render_staged_rig.py、install_character.py、runtime_runner.py、runtime_runner_revision.py、build_runtime_media.py、record_review.py、collect_gifs.py后分阶段执行。未准备时才character_step.py prepare WinterWolfTypeB。完善anatomy_plan与prompt，实际审每个原始AI图，确认方向、器官和原风格再art_selection；stage前确认不会覆盖已有清理或返修证据。

按实际源矩形分件，不假定生成格界；去品红、查透明微洞/尘点、边缘污染/描边/连接根、切片、PPU、pivot和render order。2048/14分件仅是前任事实，按B自身需要与工具合同决定。局部修补留父版本、范围、方法、SHA和修前图，不伪称新的AI返回。实看完整四向离线组合及必要局部，不能裁掉耳脚尾后通过。四足对角步态、短步/躯干/尾错相且根部固定，攻击蓄力发力、死亡保持连接；原左右曲线/事件/loop/时长全部保留，无地面影。

安装前再次核身份/空闲/生产保护，保存全路径并集基线。只安装本角色Builder并Verify，禁止全目录重建或删除installed_manifest绕过保护。绑定安装后battle及Directions全部文件和根.meta、battle.meta、暂存及manifest/verify SHA，之后才能运行。两轮真实Play普通死亡/Up死亡每轮84PASS0FAIL，总168PASS0FAIL；完整保存actual_frames.jsonl、checks、全部原始PNG、Unity frame/realtime/normalizedTime与SHA。覆盖四向、斜向滞回/近零保持、原生状态及头事件、连续转向相位、受击/致死白闪结束、死亡旋转收缩淡出、自动回收同实例复用、暂停恢复/1x2x3x及适用Flying。不能用Animator.Update或离线合成冒充真实Play。画面有问题即使PASS也返修保留旧版并重跑最终两轮。

若改UnityC#，同批完成后再8088 MCP refresh_unity(mode=force,scope=all,compile=request,wait_for_ready=true)，1–2秒读取state直到compile/reload/update=false且ready=true，error/errorCS和scriptCompilationFailed=false；编译期间不写代码，重载断线约5秒再重连重核，不清控制台。无C#改动不为形式额外改代码或编译。

## 6. 最终视觉、版本封存、record及GIF归档

实看最终两轮four_directions、runtime strip、按时序足量PNG及最终GIF编码帧，覆盖上述动作。一次1–2图，原件完整留盘。先看未裁原图，再选能保耳脚尾的crop；最终记录实际样本数、路径、SHA和观察结论。不能播放时明确以逐序抽样代替，不声称实时播放或全帧审完。

先解码GIF实际累计时长并与B原Walk合同比较。Pillow逐帧毫秒向10ms截断会缩短周期；必要只在B Docs保留修前GIF/manifest后，以真实normalized phase累计边界量化，保原生总时长，不合成姿态、不复制A的500ms假定。前任A的两个native500ms已从470/480修到500，修前6GIF也归档。

最终全路径并集审计包括新增删除和Directions根.meta，保护源/meta/原动画/共享C#/其他角色/配置；Reporter build_info仅在ReporterEditor不变且格式与实际Play证据对应时单列。旧全局scope失败不重写成PASS。最终生产/暂存必须匹配preplay，runtime记录与PNG及最终媒体绑定同一版本；再现场确认import/sprite/pivot/PPU/透明设置、依赖和Verify收集器、error0/failedfalse/clean Boot非Play/空闲，不能拿其他工程结果。无发布构建。

UTF8记录真实visual_note到本角色record_note_utf8.txt，文件读取传character_step.py record WinterWolfTypeB，避免PS中文参数破损。只completed_pending_user_art_review、user_approved=false。record触发collect_gifs，逐个核本角色全部GIF源与集中副本SHA，区分最终与修前/否决，所有历史保留，不假定每角色12或总数1660。前任当前全局1660，后续以manifest为准。保存final_validation、version_binding、scope、review、archive、Unity release证据，进度正确递增且保留首批批准。

## 7. 完成后的唯一新聊天交接

完成B或准确记录真实阻断后安全交回Unity。重读progress及递归材料，优先独立可恢复已开始项，再按index正常下一Wolf115；PossessedWarg原unknown保持，不机械使用progress.current。能独立推进就继续链，全部108有效完成或仅剩真实阻断才停止。不要因待用户美术审核暂停循环。

写conversation_handoffs带时间B总结，含真实修改、revision/指纹、运行计数、所审画面、范围、Unity状态、请求消耗和后继。更新README及主执行prompt的live块，保历史；写一个完整UTF8 NEXT和后继prompt，不分段不省略不放占位符。先确认Unity释放，再chain=handoff_ready、新唯一token、parentID、下一角色。现场list_projects确认E:/MyTowerGame，唯一create_thread(target={{type:project,projectId:现场ID,environment:{{type:local}}}},prompt:完整文本)，不fork/子代理/模型推理覆盖。创建结果不明先查真实响应/聊天不重试。明确成功响应落盘，父最后工作区写chain=active新owner/token并停止所有写入；一次有界wait_threads确认启动，最后给真实created-thread directive。创建失败保留完整prompt与总结，准确报告。

禁止配置表自动改写、Assets/ConfigJson或Assets/Gen直接写入、恢复声音、构建部署、生产删除、Git提交推送、memory修改、桌面擅控。所有已有失败/否决/unknown/计数与安装清单保留。现在从身份、所有权、现场和自身完整源图开始，完成实际工作。
'''
promptpath.write_text(prompt,encoding='utf-8')
(RUN/'NEXT_ENEMY_TASK.md').write_text(prompt,encoding='utf-8')
live_text=f"{now()} WinterWolfTypeA113已record，102/108，completed_pending_user_art_review/user_approved=false；Up本地03/Down03/alpha_r01/尾宽0.30，最终两轮168PASS0FAIL/668PNG，实审14板313采样位301不同PNG及12GIF各5帧。native500ms GIF已仅Docs修正470/480截短；AllGIF1660，本角色18=12最终+6旧时长，源/副本SHA一致。5585→5605范围unexpected0，22生产绑定与prePlay一致，原源/meta/共享C#/其他角色/配置保护；Unity8088 clean Boot非Play/error0。用户generate.mjs固定191.101.132.254直连HTTP200已验证，旧A三unknown/standing2/2保留。下一唯一WinterWolfTypeB114；PossessedWarg79原Down仍unknown。详见{rel(handoff)}；实时以progress/chain为准。"
for path,begin,end in [(RUN.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),(RUN/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    text=path.read_text(encoding='utf-8');assert text.count(begin)==text.count(end)==1
    a=text.index(begin)+len(begin);b=text.index(end,a);text=text[:a]+'\n'+live_text+'\n'+text[b:]
    if path.name=='README.md':text=text.replace('2026-10-29 本轮当前清单为 1642 个文件','2026-10-29 本轮当前清单为 1660 个文件')
    path.write_text(text,encoding='utf-8')
item['handoff_file']=rel(handoff);item['successor_character']=NEXT
progress.update(current=NEXT,updated_at=now());(RUN/'progress.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
dispatch={'prepared_at':now(),'character':NEXT,'index':114,'dispatch_token':token,'parent_thread_id':chain['owner_thread_id'],'project_id':None,'project_live_confirmed':False,'created':False,'response_file':rel(HERE/('successor_creation_response_final_'+stamp+'.json')),'progress_sha256':sha(RUN/'progress.json')}
for key,path in [('prompt',promptpath),('handoff',handoff),('assessment',HERE/'successor_assessment_final_20261029.json'),('unity_release',release),('next_task',RUN/'NEXT_ENEMY_TASK.md')]:dispatch[key+'_file']=rel(path);dispatch[key+'_sha256']=sha(path)
save(dispatchpath,dispatch)
chain.setdefault('completed_handoffs',[]).append({'character':NAME,'status':item['status'],'current_stage':'recorded_pending_user_art_review','closed_at':now(),'owner_thread_id':chain['owner_thread_id'],'dispatch_token':chain['dispatch_token'],'handoff_file':rel(handoff),'final_evidence':rel(HERE/'final_validation_20261029.json')})
chain.update(state='handoff_ready',parent_thread_id=chain['owner_thread_id'],current_character=NEXT,dispatch_token=token,character_status_at_handoff='not_started',completed_count_snapshot=102,previous_handoff_file=chain.get('last_handoff_file'),last_handoff_file=rel(handoff),handoff_sha256=sha(handoff),successor_assessment=dispatch['assessment_file'],progress_sha256_at_handoff=sha(RUN/'progress.json'),unity_release_file=rel(release),prepared_dispatch_file=rel(dispatchpath),creation_response_file=dispatch['response_file'],dispatch_ready_for=NEXT,successor_created=False,current_stage='handoff_ready_pending_single_successor_creation',resume_character=NEXT,resume_stage='Verify new owner/token; inspect WinterWolfTypeB original source and native contract; establish baseline',current_blocked=False,blocked_reason=None,blocked_owner_retained=False,no_successor_creation_reason=None,handoff_ready_at=now(),updated_at=now(),last_stage_evidence=rel(HERE/'final_validation_20261029.json'))
(RUN/'conversation_chain.json').write_text(json.dumps(chain,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'state':'handoff_ready','character':NEXT,'token':token,'prompt_file':str(promptpath),'dispatch_file':str(dispatchpath),'handoff_file':str(handoff)},ensure_ascii=False))
