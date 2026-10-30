"""Release WinterOgre, persist the complete next prompt, then freeze for one local successor."""
from session_winterogre import *
from mcp_call import URL
import re, shutil, uuid

chain=owner();progress=read(H/'progress.json')
done=next(i for i in progress['items'] if i['name']==NAME)
assert progress['completed_count']==100 and done['status']=='completed_pending_user_art_review' and done['user_approved'] is False
remaining=[i for i in progress['items'] if i['status'] not in ['completed_pending_user_art_review','user_approved']]
recoverable=[i for i in remaining if i['status'] not in ['not_started','blocked']]
selected=min(recoverable or [i for i in remaining if i['status']!='blocked'],key=lambda i:i['index'])
NEXT=selected['name'];N=H/NEXT
assert NEXT=='WinterWarg' and selected['index']==112 and selected['status']=='not_started'
assert len(remaining)==8 and sum(i['status']=='not_started' for i in remaining)==7
assert next(i for i in remaining if i['name']=='PossessedWarg')['status']=='blocked'
existing=[p for p in N.rglob('*') if p.is_file()]
assert len(existing)==8 and all(p.is_relative_to(N/'reference') for p in existing)
t=next(x for x in read(H/'local_baseline.json')['targets'] if x['name']==NEXT)
six={p:sha(ROOT/p) for k in ['battle','source','atlas'] for p in [t[k],t[k]+'.meta']}
assert all(sha(N/'reference'/Path(p).name)==s for p,s in six.items())
final=read(D/'final_validation_20261029.json');binding=read(D/'version_binding_final_20261029.json')
assert (final['passes'],final['failures'],final['actual_png_frames'])==(168,0,716)
assert all(sha(ROOT/p)==s for p,s in binding['production_scope_files'].items())
assert all(sha(ROOT/p)==s for p,s in binding['installed_files'].items())
for file,key in [('version_binding_final_20261029.json','version_binding_sha256'),
                 ('scope_incremental_final_20261029.json','incremental_scope_sha256'),
                 ('visual_review_art_r01_20261029/review.json','visual_review_sha256'),
                 ('gif_archive_verification_20261029.json','gif_archive_sha256')]:
    assert sha(D/file)==final[key]
assert read(H.parent/'AllGIF/manifest.json')['count']==final['global_archive_count']==1612
c=Client();project=c.identity()
errors_response=c.tool('read_console',{'action':'get','types':['error'],'count':'50','format':'json'})
errors=errors_response.get('structuredContent') or json.loads(errors_response['content'][0]['text'])
state=c.resource('mcpforunity://editor/state')['data'];live=probe(c);idle(live)
assert state['advice']['ready_for_tools'] and not state['tests']['is_running']
assert not state['compilation']['is_compiling'] and not state['compilation']['is_domain_reload_pending']
assert not state['assets']['is_updating'] and not state['assets']['external_changes_dirty']
assert errors['data']==[]

stamp=datetime.now(timezone(timedelta(hours=8))).strftime('%Y%m%d_%H%M%S')
token='winterogre-to-winterwarg-'+stamp+'-'+str(uuid.uuid4())
rel=lambda p:p.relative_to(ROOT).as_posix()
handoff=H/'conversation_handoffs'/(stamp+'_WinterOgre_completed.md')
assessment=N/('successor_assessment_'+stamp+'.json')
prompt_path=N/('successor_prompt_'+stamp+'.txt')
release=D/'handoff_release_final_20261029.json'
dispatch_path=N/'prepared_dispatch_20261029.json'
assert all(not p.exists() for p in [handoff,assessment,prompt_path,release,dispatch_path])
backup=D/'docs_before_final_handoff_20261029';assert not backup.exists();backup.mkdir()
for p in [H/'NEXT_ENEMY_TASK.md',H/'conversation_chain.json',H/'progress.json',H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md',H.parent/'README.md']:
    shutil.copy2(p,backup/p.name)
write(release,{'observed_at':now(),'released_by_thread_id':OWNER,'current_character':NAME,'next_character':NEXT,
    'next_dispatch_token':token,'transport':URL,'project':project,'editor_state':state,'live_probe':live,
    'current_console_errors':errors,'earlier_errors_preserved_in_evidence':True,'safe_to_handoff':True,'protocol_history':c.history},fresh=True)
write(assessment,{'observed_at':now(),'completed_count':100,'authorized_count':108,'next_character':NEXT,'next_index':112,
    'status':'not_started','dispatch_token':token,'target':t,'protected_six':six,'reference_matches_live':True,
    'existing_files':[p.relative_to(N).as_posix() for p in existing],'source_art_reviewed_by_parent':False,
    'source_instruction':'Next owner must inspect WinterWarg original atlas/full prefab, four legs, Tail, anchors and Wolf contract independently. Do not copy Giant anatomy/motion.',
    'no_generation_staging_install_or_runtime':True,'remaining':[{k:i[k] for k in ['index','name','status']} for i in remaining],
    'blocked_preserved':[i for i in remaining if i['status']=='blocked']},fresh=True)

summary=f'''# WinterOgre111 完成与 WinterWarg112 唯一串行交接

时间 {now()}。父线程 {OWNER}，旧 token {TOKEN}。WinterOgre 已 record 为 completed_pending_user_art_review，user_approved=false；实时进度100/108。下一唯一角色 WinterWarg112，七项未开始，PossessedWarg79历史阻断保留。

## 完成内容与版本

最终 art_r01，14个透明分件，2048×2048 atlas，PPU100。原金赭斑点、秃顶尖耳、矮壮双足、白毛裙、大型棕白护腕与两只空拳保持。Up是真背面、无脸、脚后跟光滑；Down有正面正常/愤怒/死亡头和脚趾。原Weapon renderer禁用；图集未用手杖不装到角色，ArmR/FistR/Weapon层级保留。轴向正背面比原侧面窄，原左右侧面不改。初始肩部突出和长腿布局已修复，旧offline_initial_layout_20261029保留。224个品红边缘RGB像素以邻近干净RGB修正，alpha/形状不变，原raw及staged_before_edge_cleanup_20261029保留，不冒充未经修绘生成图。

只安装本角色，installed_manifest.json SHA {final['manifest_sha256']}。20项安装变化；21条prePlay生产指纹两轮后完全一致。Directions.meta根目录meta另行检查为本角色新增文件，GUID唯一，未被安装清单的目录内扫描收录；不是扩大允许列表。完整路径并集5545→5565文件、22变化/20新增/0删除，unexpected0：本角色battle和Directions（含根meta）及未改ReporterEditor自动Play时间戳。源atlas、source prefab与meta、battle meta、root/HP/业务/锚点/事件接收器保持；本角色原组件semantic PASS；共享C#、其他角色、配置表与Assets/ConfigJson/Gen无本轮漂移。旧全局范围失败保留未重审，不能称全工程PASS。

原Giant契约Ready0.5s/Walk0.6666667s循环、Attack1s/Death0.5s非循环；float18/30/27/24，PPtr0。Attack SetHead0@0、1@0.25、Event("Attack")@0.766666651、0@0.783333361；Death SetHead2@0。原曲线/事件/时长/loop由Builder及当前源契约核对，原动画文件无本轮漂移。导入14切片Multiple/PPU100/alphaTransparency=true/mipmap=false，逐rect/pivot核对、依赖和现YooAsset收集器通过，没有做发布构建。

## 真实运行与实际视觉审阅

runtime_r01：84PASS/0FAIL、357张真实PNG，records SHA {final['runtime'][0]['records_sha256']}。
runtime_updeath_r01：84PASS/0FAIL、359张真实PNG，records SHA {final['runtime'][1]['records_sha256']}；指定Up死亡。总168PASS/0FAIL、716真实PNG，完整帧哈希在version_binding_final_20261029.json。两轮均安全回到clean Boot。

实际审过两轮four_directions、runtime strip、12张时序/步态板（281采样位、263不同真实PNG）、8张完整768PNG、12最终GIF各5编码帧共60帧、另4张未裁切GIF帧。覆盖四方向/连续转向/原生状态/空拳攻击/受击白闪及恢复/Down与Up全身死亡旋转缩小淡出/自动回收与同实例Down正常复用/暂停冻结恢复/1x2x3x。未实时播放或逐帧全审，固定裁图对极端展开可能不全，已另看整帧；淡出保留原逐renderer alpha透出重叠分件限制。内部技术视觉通过，用户美术仍待验收。

通用build_runtime_media.py假定0.5s；本角色独立用真实recorded normalizedTime与原Walk0.6666667s修正UpWalk/DownWalk/up_down_walk。GIF10ms精度下编码670ms，无新姿态、无共享脚本或原动画改动。原6个错误时长GIF保留在media_before_native_loop_fix_20261029。AllGIF1594→1612，本角色18来源=12当前审核+6历史，所有源/归档SHA一致。

## 五次结果不明与服务恢复

旧Up initial/revision_01/revision_03：Curl55，`Send failure: Connection was aborted`；revision_02：TypeError `fetch failed`（诊断ECONNRESET）；revision_04：Curl52，`Empty reply from server`。均未获得HTTP状态/raw/result/可查询ID，5项结果和费用仍不明，不能说未计费。自动2/2及旧两个独立max1保持消耗。

新的WorkBuddy已存在T2成功输出已独立检查：同端点/模型/medium/1536×1024/n1/双参考图直连HTTP200和PNG，只是白底红圆对照，不是角色图；没有新增付费诊断。基于此与继续授权记录恢复边界，Up revision_05和首次Down各一次正式调用均HTTP200，原raw实际审看并保留。7897规则实际DIRECT，不能沿用“更换外部代理出口成功”的旧推断；usage聚合及空batch不能归属旧5次或证明退款。service_recovery_assessment_20261029.json、authorized_verified_service_resume_20261029.json及所有失败原件保留。WinterOgre完成不消除旧不确定费用记录，也不阻止独立下一角色按原授权首次生成。

## 最终入口与Unity释放

WinterOgre/final_validation_20261029.json、version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_art_r01_20261029/review.json、gif_archive_verification_20261029.json、native_walk_media_fix_20261029.json、unity_release_final_20261029.json、runtime_summary.json、record_note_utf8.txt。finalize已audit和seal，不重跑。当前Unity E:/MyTowerGame、2022.3.62f3c1、http://127.0.0.1:8088/mcp，动态选MyTowerGame。最终和交接前均clean Boot非Play，failed/compile/reload/update/tests/review/recording/balance/manual全空闲，ready=true，external_changes_dirty=false，当前error与errorCS为0；较早2条MCP WebSocket错误保留在早期证据，未清控制台。没有共享Unity C#改动，本收尾未另请求编译。

下一角色WinterWarg仅原reference8文件，六保护与当前一致，父未审源图、未生成/暂存/安装/运行。请独立审查Dogs/WinterWarg原atlas、完整源prefab、battle和Wolf Controller，核四足、尾根/耳/锚点/攻击及原生契约，不套Giant布局。新token {token}。完整接棒prompt {rel(prompt_path)}；assessment {rel(assessment)}；Unity释放 {rel(release)}。先handoff_ready再现场list_projects，唯一fresh local create_thread，不fork/子代理/定时器/模型覆盖。明确成功后保存响应，父最后工作区写入active新owner/token；之后父只读。
'''
handoff.write_text(summary,encoding='utf-8')

prompt=f'''在 E:/MyTowerGame 继续敌人四方向续作，只负责 WinterWarg(index112)。这是既有用户授权的逐角色串行循环接棒，完成后主动创建唯一下一全新本地聊天，不逐角色再次请求确认。当前父线程 {OWNER}。本次 dispatch_token：{token}。

先完整读取以下现有文件；绝对路径均以 E:/MyTowerGame 为根：
1. E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt。
2. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md。
3. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md。
4. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/NEXT_ENEMY_TASK.md、conversation_chain.json、progress.json。
5. E:/MyTowerGame/Docs/EnemyDirectionReview/README.md、PREFAB_CHANGES_SUMMARY_20261026.md。
6. E:/MyTowerGame/{rel(handoff)}。
7. E:/MyTowerGame/{rel(assessment)}、{rel(dispatch_path)}。
8. 现有character_step.py、generate_character.ps1/generate.mjs、prepare_character.py、pack_character.py、adjust_layout.py、install_character.py、runtime_runner.py/runtime_runner_revision.py、build_runtime_media.py、record_review.py、collect_gifs.py；local_baseline.json与生产基线、首批user_approval_20261023.json、AllGIF/manifest.json，以及当前角色实际材料。

所有权必须核对：链state=active、owner_thread_id等于本新聊天实际CODEX_THREAD_ID、current_character=WinterWarg、dispatch_token精确匹配后，才允许生产修改和Unity操作。新聊天可能先于父登记启动；handoff_ready时只做独立只读同步，短暂分段等待，不超时抢锁、不修改链或创建第二后继。若父响应落盘/转移失败，报告具体现场。父一旦active转移即停止所有工作区写入。

实时进度100/108：WinterOgre111已完成art_r01/168PASS0FAIL/716真实PNG，completed_pending_user_art_review且user_approved=false。剩余8项：PossessedWarg79历史Down结果不明blocked；WinterWarg112、WinterWolfTypeA113、WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118七项not_started。108是授权数量，终项Zombie118。不要盲用progress.current或旧prompt快照。WinterWarg只有reference8文件，父仅核六保护，不把调度文件当作已prepare/生成/安装结果。

WinterWarg实际生产路径：battle={t['battle']}；source={t['source']}；atlas={t['atlas']}；controller={t['controller']}；Directions={t['art_dir']}。先实际查看原atlas和完整source prefab及battle层级/renderer/Body/Head/四腿/Tail/耳/锚点、原float/PPtr曲线/事件/时长/loop与移动/战斗/回收/同实例复用；制定自身解剖、正背面和步态，不套WinterOgre双足Giant或其他狗的布局。以当前磁盘和既有修改建立Assets/Packages/ProjectSettings/Luban全路径SHA基线（含新增/删除并集）及battle/source/atlas和各meta六保护；不能用Git HEAD消除已有变更。

工程路由明确为Unity2022.3.62f3c1 / unityMCP / http://127.0.0.1:8088/mcp。根AGENTS的FreedomTower_1/D:/8082是旧信息，8082现在属D:/FishTestGame，不得误操作或改写根规则。读mcpforunity://custom-tools与instances，从现场完整MyTowerGame ID set_active_instance，再读project/info核E:/MyTowerGame与版本。每次重连/域重载重核。桌面工具握手有问题但8088在线时可审阅复用mcp_call.py Client.identity()，其代理禁用和动态身份检查保持。离线按项目规则自主恢复已有HTTP Local服务/桥接，不抢端口/杀别人工程。进入Play前先读目标日志，再核场景和占用；本任务自己的两轮真实Play已有授权，不强停其他验证/录像或覆盖脏场景。

阶段流程必须实际执行：参考/解剖/prompt并审源图 → 仅缺少且没有在途/uncertain请求时首次生成Up，再实际审原raw → Down首次生成并实审 → 透明分件/Atlas/Pivot/PPU/布局/离线组合实际审图 → 单角色Builder安装及Verify → 两轮真实Play（普通死亡和指定Up死亡，每轮84PASS0FAIL）→ 实际媒体审阅 → record → GIF源/集中SHA核对 → 完整总结和唯一后继。每阶段落盘准确revision、计数、哈希、范围和未完成项。出现视觉问题即使程序PASS也须修复并用新运行revision，不删除旧清单或失败证据绕保护。

本机pipeline使用 C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8。PATH Python3.13是isolated，忽略脚本目录/PYTHONPATH，会使install子进程找不到mcp_call；不要再用。脚本run子进程沿用sys.executable。PowerShell中文用UTF8文件传长备注，勿把JSON.stringify当shell转义。

初次准备入口：character_step.py prepare WinterWarg；仅已有参考时先确认prepare不覆盖。图像任务先读当前imagegen SKILL.md，沿用已授权AIHub https://aihub.dog/v1 与现有生成器，gpt-image-2/quality=medium/n=1/size=1536x1024，优先既有Curl传输并Preflight。运行时从AIHUB_IMAGE_API_KEY或DPAPI clixml读取密钥，只发aihub.dog、不输出明文、不跨域携带；不改系统代理或复制角色特定恢复许可。已有request/raw/result/uncertain或在途进程先检查，不能盲重发。出现传输不明准确分类，不推断未计费。既有standing_recovery授权如确实适用，读取原用户证据、核范围并按现有生成器的角色支持和计数执行；不得自动重置计数或把代理自己设的max1说成用户预算。WinterOgre旧五次不确定仍保留，已恢复Up05和首次Down两个HTTP200不意味着旧请求免费。

stage入口character_step.py stage WinterWarg。必须实际检查两方向raw、14或实际需要的分件数量、alpha/去底/描边/孔洞/切片/Atlas/Pivot/PPU/顺序和组合；原色、脸、毛、装备、真实器官和tail根连接，Up无脸/后跟正确、Down面部与脚趾正确，左右原侧面保留，四向及状态/死亡/复用无地面阴影。独立读取Wolf原Walk时长；build_runtime_media.py把0.5s写死，若原clip不同仅在角色Docs中用真实相位修正并保留旧媒体，不能谎标周期或合成动作。

安装前再核六保护和范围指纹、Unity身份与空闲。单角色现有Builder安装，installed_manifest存在就恢复而非删除；记录完整prePlay生产指纹，Directions.meta位于art_dir外可能被目录内扫描遗漏，要单列核对。两轮实际运行必须用最终生产版本，保存actual_frames.jsonl、actual_runtime_checks.txt、全部原PNG、revision/SHA和安全返回场景。覆盖四方向步态、连续转向/相位延续、纯纵向与斜向/滞回、原生状态/头事件/攻击、受击和致死白闪结束、全身死亡旋转收缩淡出、自动回收/同实例正常复用、暂停恢复1x2x3x。不能用手动Animator.Update或离线图假冒Play。C#确需最小修改时查调用/依赖，完成同批后按8088目标MCP refresh/request compile、轮询ready/compile/reload/update、error和errorCS及scriptCompilationFailed闭环；不把历史错误清空。

实际查看两轮four_directions、runtime strip、按时间的足够原PNG和所有最终GIF编码帧。若工具不能实时播放，按序抽样并如实记录范围/限制；一次1～2张清晰预览和必要原尺寸局部，原件留盘，勿累计整个队列图片。运行PASS不能代替视觉通过。把实际中文观察写record_note_utf8.txt，先核runtime_summary最终版本/168/0/帧SHA再record。最终只能completed_pending_user_art_review、user_approved=false；用户自己批准才user_approved。现有record_review.py会调用collect_gifs.py，核全部实际来源及集中副本SHA，区分当前审核/历史与否决，数量由现场manifest算，不写死每角色12。完整路径并集审计归因本角色与确证Reporter时间戳，原prefab语义/GUID/root/HP/锚点/移动战斗/原动画合同/导入/依赖/收集覆盖保持；不称旧全局失败已通过或宣称构建回读。

前任WinterOgre的最终证据在WinterOgre/final_validation_20261029.json、version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_art_r01_20261029/review.json、gif_archive_verification_20261029.json。281板采样位/263不同PNG、8完整原PNG、60编码帧及4整帧；未实时播放或全审。AllGIF1612，本角色12最终+6历史共18。完整增量5545→5565文件，22变化/20新增/0删除、unexpected0；原组件semantic PASS、源与其他共享资源不变。最终clean Boot非Play/failed=false/ready=true/currenterror0，早期MCP错误保留在原证据。不要运行前任prepare/stage/install/finalize，或清理旧5次uncertain。PossessedWarg阻断仍独立保留。

边界：不git pull/reset/clean/checkout覆盖、不commit/push、不构建部署、不删除资源/场景、不改保护表Luban/Config/Datas/Levels/**、EnemyData.xlsx、__tables__.xlsx，不直接写Assets/ConfigJson或Gen、不恢复声音系统；不创建子代理/fork/并行角色/计时器/定时任务，不改长期memory，不改模型或推理设置。用户长期偏好完整单次可复制prompt，后继说明交付为完整UTF8文件、不占位或分段省略。

完成WinterWarg或准确记录真实阻断后，先安全交回Unity，核实时items优先恢复可恢复已开始项，再选最低index独立未开始角色，PossessedWarg无新可恢复证据就保留。新建带时间总结，更新README/live prompt、NEXT_ENEMY_TASK完整说明和progress，chain=handoff_ready并产生唯一token；按协议现场list_projects确认E:/MyTowerGame项目，再唯一create_thread(target={{type:"project",projectId:现场ID,environment:{{type:"local"}}}},prompt:完整新提示)。不fork、不model/thinking override。先保存明确成功响应，再最后工作区写入active新owner/token和创建记录；此后父只读，用一次有界wait_threads确认启动，最终给真实::created-thread。创建结果不明先查返回/实际聊天列表，不能盲目再创建。创建失败保留完整NEXT和总结并如实报告。循环至108有效完成或只剩确实阻断，不逐角色等用户确认。
'''
prompt_path.write_text(prompt,encoding='utf-8')
(H/'NEXT_ENEMY_TASK.md').write_text('# 下一唯一角色 WinterWarg(index112)\n\n'+prompt,encoding='utf-8')
live_text=f'''2026-10-29 WinterOgre111已record，100/108，art_r01，completed_pending_user_art_review、user_approved=false。两轮357+359=716真实PNG、168PASS/0FAIL；实审两轮四向/strip、12板281采样位263不同PNG、8原PNG、12GIF的60编码帧与4整帧，非实时播放/逐帧全审。14透明分件，空拳原设、Up无脸/后跟，原Weapon renderer禁用。GIF行走按原Walk0.6666667s修为670ms，原6旧时长GIF保留。AllGIF1612，本角色12当前审核+6历史、SHA一致。旧5Up传输结果和费用仍不明；新服务证据恢复后Up05/首次Down均HTTP200，旧2/2与两个max1不重置，代理DIRECT更正保留。完整路径并集5545→5565，22变化20新增0删除unexpected0，含本角色Directions根meta及确证Reporter时间戳；本角色语义PASS、源/meta与共享C#无增量漂移；旧全局失败未重审。Unity2022.3/8088正确身份、clean Boot非Play/全空闲/failed=false/ready=true/当前errorCS和error0，早期错误证据保留。最终WinterOgre/final_validation_20261029.json；交接{rel(handoff)}。下一唯一WinterWarg112 not_started、reference8文件，token={token}；PossessedWarg旧blocked及七项未开始。完整入口NEXT_ENEMY_TASK.md。'''
for path,begin,end in [(H.parent/'README.md','<!-- ENEMY_README_LIVE_BEGIN -->','<!-- ENEMY_README_LIVE_END -->'),
                       (H/'REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md','<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->','<!-- ENEMY_SERIAL_LIVE_STATE_END -->')]:
    text=path.read_text(encoding='utf-8-sig');pattern=re.escape(begin)+r'.*?'+re.escape(end)
    assert len(re.findall(pattern,text,re.S))==1
    text=re.sub(pattern,lambda _:begin+'\n'+live_text+'\n'+end,text,flags=re.S)
    if path.name=='README.md':
        text,count=re.subn(r'\d{4}-\d{2}-\d{2} 本轮当前清单为 \d+ 个文件','2026-10-29 本轮当前清单为 1612 个文件',text);assert count==1
    path.write_text(text,encoding='utf-8')
done['handoff_file']=handoff.relative_to(H).as_posix();progress.update(current=NEXT,updated_at=now())
write(H/'progress.json',progress)
dispatch={'prepared_at':now(),'created':False,'parent_thread_id':OWNER,'character':NEXT,'character_index':112,
    'dispatch_token':token,'project_root':'E:/MyTowerGame','project_id':None,'project_live_confirmed':False,
    'project_association_confirmed':False,'handoff_file':rel(handoff),'handoff_sha256':sha(handoff),
    'assessment_file':rel(assessment),'assessment_sha256':sha(assessment),'unity_release_file':rel(release),'unity_release_sha256':sha(release),
    'prompt_file':rel(prompt_path),'prompt_sha256':sha(prompt_path),'next_task_file':rel(H/'NEXT_ENEMY_TASK.md'),
    'next_task_sha256':sha(H/'NEXT_ENEMY_TASK.md'),'progress_sha256':sha(H/'progress.json'),
    'response_file':rel(N/'successor_creation_response_20261029.json')}
write(dispatch_path,dispatch,fresh=True)
assert not any(i['character']==NAME for i in chain.get('completed_handoffs',[]))
chain.setdefault('completed_handoffs',[]).append({'character':NAME,'status':done['status'],'current_stage':'recorded_pending_user_art_review',
    'closed_at':now(),'owner_thread_id':OWNER,'dispatch_token':TOKEN,'handoff_file':rel(handoff),'final_evidence':rel(D/'final_validation_20261029.json')})
for key in ['resume_conditions','current_turn_resume_file','previous_resume_authorization','closeout_receipt_file']:
    chain.pop(key,None)
chain.update(state='handoff_ready',parent_thread_id=OWNER,current_character=NEXT,dispatch_token=token,character_status_at_handoff='not_started',
    completed_count_snapshot=100,previous_handoff_file=chain.get('last_handoff_file'),last_handoff_file=rel(handoff),handoff_sha256=sha(handoff),
    successor_assessment=rel(assessment),progress_sha256_at_handoff=sha(H/'progress.json'),unity_release_file=rel(release),
    prepared_dispatch_file=rel(dispatch_path),creation_response_file=dispatch['response_file'],dispatch_ready_for=NEXT,successor_created=False,
    current_stage='handoff_ready_pending_single_successor_creation',resume_character=NEXT,
    resume_stage='Verify owner/token; independently inspect WinterWarg source anatomy and Wolf contract; establish baseline',
    handoff_ready_at=now(),updated_at=now())
write(H/'conversation_chain.json',chain)
print(json.dumps({'state':'handoff_ready','character':NEXT,'dispatch_token':token,'dispatch_file':rel(dispatch_path),
    'prompt_file':rel(prompt_path),'handoff_file':rel(handoff),'safe_to_handoff':True},ensure_ascii=False))
