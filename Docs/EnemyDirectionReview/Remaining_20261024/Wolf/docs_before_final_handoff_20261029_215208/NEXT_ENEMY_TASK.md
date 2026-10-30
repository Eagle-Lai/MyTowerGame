# Wolf115 唯一接棒执行 Prompt

在E:/MyTowerGame继续敌人四方向续作。本聊天只完成Wolf(index115)，完成后按协议创建唯一后继。当前103/108，所有completed_pending_user_art_review均仅内部完成，用户尚未美术批准。此文件为完整UTF8说明，不依赖旧聊天图片。

## 1. 唯一所有权、同步与恢复阶段

dispatch_token=winterwolftypeb-to-wolf-20261029_211300-fedb31c2-0d38-4e0f-8ea7-b7953a0a615a
父线程=01a1879d-59b4-73a3-b061-6e37d031ddcb
先读E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/Remaining_20261024/conversation_chain.json、progress.json、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、NEXT_ENEMY_TASK.md、Docs/EnemyDirectionReview/README.md及Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/20261029_211300_WinterWolfTypeB_completed.md。读本角色已有文件、git status、相关差异、实现和直接依赖/生命周期，保留全部既有未提交改动；同步不授权git pull/reset/clean/checkout、commit/push。

只有chain.state=active、owner_thread_id等于本聊天真实ID、current_character=Wolf且token完全匹配才能改生产或操作Unity。若handoff_ready，只读限次等父登记，不因超时抢占。max_active_production_tasks=1，一次一角色；禁止子代理、并行角色、fork、自动化或定时器。父会先保存明确创建响应，再最后写active新owner并停止工作区写入。

剩余5项：PossessedWarg79 blocked、Wolf115、WolfHound116、WolfMounfed117、Zombie118；108是授权角色数，末项index118，WolfMounfed保持原拼写。PossessedWarg旧Down无raw/result/服务ID、结果及费用unknown，不推定未发送或未收费，不重发。交接扫描Wolf只有8个reference文件，本父额外写了此prompt；没有generation/staged_art/install/runtime。在你开工时重新递归核实，恢复新增阶段，不盲目prepare、生成或安装。

## 2. 正确工程和Unity路由

目标E:/MyTowerGame、Unity2022.3.62f3c1，版本以ProjectVersion.txt为准。unityMCP HTTP Local http://127.0.0.1:8088/mcp；根AGENTS的FreedomTower_1/D:/8082为旧信息，8082现场属于FishTestGame、8080属于CatchFish。不得操作其他工程或为本任务改根AGENTS。用户要求控制电脑前先弹确认；本任务使用文件/命令行与Unity MCP，不擅自桌面控制。

首次/重连/域重载后读mcpforunity://custom-tools和instances，动态选MyTowerGame完整ID，set_active_instance，再project/info核路径/版本。可用已审mcp_call.py Client.identity()，loopback禁代理，不硬编码hash。MCP离线按已有授权恢复本工程已有服务/桥接，复用在线服务、不抢端口、不杀其他工程。桌面操作确需时遵守用户确认边界；恢复失败及时说明项目、版本、8088失败环节和具体启动连接步骤。

操作前先读error/errorCS，再state与实际probe，确认无他人Play、脏场景、测试、review/balance/manual/recording、编译或更新。前任交回单一clean Boot，不能据旧快照强停后来任务。当前角色两轮真实Play已有授权，不逐角色再问；结束恢复原干净场景。无UnityC#改动不为形式额外编译；如改C#，同批完成后8088 MCP refresh_unity(mode=force,scope=all,compile=request,wait_for_ready=true)，1–2秒读state直到compile/reload/update=false且ready=true，error/errorCS与scriptCompilationFailed=false；期间不写代码，断线约5秒重连重核，不清控制台。

## 3. Wolf自身源图、结构和原动画合同

battle=Assets/Prefabs/Enemy/Enemy_Wolf.prefab
source=Assets/_UIAssets/Monsters/Dogs/Wolf/Wolf.prefab
atlas=Assets/_UIAssets/Monsters/Dogs/Wolf/Wolf.png
controller=Assets/_UIAssets/Monsters/_Common/Animations/Wolf/Controller.controller
Directions=Assets/_UIAssets/Monsters/Dogs/Wolf/Directions

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

新建带时间Wolf handoff，写实际修改、revision/指纹、两轮计数、所审范围/限制、Unity状态、网络尝试/unknown及后继。更新README和主prompt的live块，保留历史；写完整UTF8 NEXT和后继prompt，无占位符/省略/分段。先确认Unity释放，再chain=handoff_ready、新唯一token、parentID/下一角色。现场list_projects核E:/MyTowerGame，唯一create_thread(target={type:project,projectId:现场ID,environment:{type:local}},prompt:完整文本)，不fork/子代理/模型或推理覆盖。创建结果不明先查真实响应/聊天不重复。明确成功响应先落盘，再父最后工作区写chain=active新owner/token，此后停止全部写入；一次有界wait_threads确认启动，最后输出真实created-thread directive。失败保留完整prompt和总结并准确报告。

禁止配置表自动改写、Assets/ConfigJson或Assets/Gen直接写入、恢复声音、构建部署、生产删除、Git提交推送、memory修改、擅控桌面。保留所有历史失败/否决/unknown/计数/安装清单。现在先核所有权、正确工程与实际源参考，完成Wolf的实际工作。
