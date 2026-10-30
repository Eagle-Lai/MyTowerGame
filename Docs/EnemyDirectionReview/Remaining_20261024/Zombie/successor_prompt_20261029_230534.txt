# Zombie118 唯一接棒执行 Prompt

在E:/MyTowerGame继续敌人四方向续作，本聊天只完成Zombie(index118)。当前106/108，所有completed_pending_user_art_review仅内部完成，尚未用户美术批准。本文是完整UTF8执行说明，不依赖旧聊天图片。完成Zombie后重读队列；只剩真实阻断则准确封存并停止，不创建多余聊天。

## 1. 所有权与开工同步

dispatch_token=wolfmounfed-to-zombie-20261029_230534-9abf79b2-282d-4c43-bc85-2b10f14a62f1
父线程=01a1880d-25f4-7861-84f0-dc33ad910bda
交接总结=Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/20261029_230534_WolfMounfed_completed.md
先读E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/Remaining_20261024/conversation_chain.json、progress.json、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、NEXT_ENEMY_TASK.md、Docs/EnemyDirectionReview/README.md和上述交接总结。定向读当前角色文件、git status/相关差异、实现、调用者/依赖/缓存/生命周期；保留全部既有未提交改动。同步不授权git pull/reset/clean/checkout/commit/push。

只有chain.state=active、owner_thread_id为本聊天真实ID、current_character=Zombie且token完全匹配，才能写生产或操作Unity。handoff_ready期间只读限次等待父登记；时间经过不授权抢占。max_active_production_tasks=1，一聊天一角色，禁止子代理/并行角色/fork/定时器/自动化。父先保存明确创建响应，再以最后一次工作区写入登记新owner active，之后停止全部工作区写入。

剩余2项：PossessedWarg79 blocked、Zombie118。108是授权数量，末项index118。PossessedWarg旧Down无raw/result/服务查询ID，结果和费用unknown；不推定未发/未收费，不重发。父递归核Zombie仅8个reference文件，额外写本prompt，没有generation/staged_art/install/runtime；开工重新递归核现场，若已出现阶段则恢复，不盲目prepare/付费生成/安装。

## 2. 工程身份及MCP8088

目标E:/MyTowerGame、Unity2022.3.62f3c1，以ProjectVersion.txt为准。unityMCP HTTP Local http://127.0.0.1:8088/mcp。根AGENTS的FreedomTower_1/D:/8082为旧说明；8082属于FishTestGame、8080属于CatchFish，不操作其他工程，也不为此改根AGENTS。桌面/电脑控制需先弹明确确认；本任务用文件/命令行/Unity MCP，不擅控桌面。

首次/重连/域重载后读mcpforunity://custom-tools及mcpforunity://instances，现场选MyTowerGame完整ID、set_active_instance，再project/info核路径版本。可复用Remaining_20261024/mcp_call.py Client.identity()，loopback禁代理，不硬编码实例hash。服务离线按已有授权恢复目标既有服务/桥接，复用服务，不抢端口/杀其他工程；确需桌面操作仍先确认。无法恢复时说明工程路径、版本、8088故障环节和具体开启/连接步骤。

操作前先读error/errorCS，再state及实际probe，确认无他人Play、脏场景、测试/review/balance/manual/recording/compile/update。前任clean Boot不替代现场核对，不强停后来任务。两轮真实Play已有授权，无需逐角色再问；结束恢复原干净场景。无Unity C#改动不为形式额外编译。若改C#，同批完成后8088 refresh_unity(mode=force,scope=all,compile=request,wait_for_ready=true)，每1–2秒读state直到compile/reload/update=false、ready=true；error/errorCS0、scriptCompilationFailed=false，期间不改代码，断线约5秒重连重核，不清控制台。

## 3. Zombie自身源及动画合同

battle=Assets/Prefabs/Enemy/Enemy_Zombie.prefab
source=Assets/_UIAssets/Monsters/Giants/Zombie/Zombie.prefab
atlas=Assets/_UIAssets/Monsters/Giants/Zombie/Zombie.png
controller=Assets/_UIAssets/Monsters/_Common/Animations/Giant/Controller.controller
Directions=Assets/_UIAssets/Monsters/Giants/Zombie/Directions

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
