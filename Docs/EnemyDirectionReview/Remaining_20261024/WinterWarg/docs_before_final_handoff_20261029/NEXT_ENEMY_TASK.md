# 下一唯一角色 WinterWarg(index112)

在 E:/MyTowerGame 继续敌人四方向续作，只负责 WinterWarg(index112)。这是既有用户授权的逐角色串行循环接棒，完成后主动创建唯一下一全新本地聊天，不逐角色再次请求确认。当前父线程 01a18619-6aa0-7a31-ac62-10a82077950b。本次 dispatch_token：winterogre-to-winterwarg-20261029_163224-4c489e91-3117-4716-a1e2-87af74077d40。

先完整读取以下现有文件；绝对路径均以 E:/MyTowerGame 为根：
1. E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt。
2. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md。
3. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md。
4. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/NEXT_ENEMY_TASK.md、conversation_chain.json、progress.json。
5. E:/MyTowerGame/Docs/EnemyDirectionReview/README.md、PREFAB_CHANGES_SUMMARY_20261026.md。
6. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/20261029_163224_WinterOgre_completed.md。
7. E:/MyTowerGame/Docs/EnemyDirectionReview/Remaining_20261024/WinterWarg/successor_assessment_20261029_163224.json、Docs/EnemyDirectionReview/Remaining_20261024/WinterWarg/prepared_dispatch_20261029.json。
8. 现有character_step.py、generate_character.ps1/generate.mjs、prepare_character.py、pack_character.py、adjust_layout.py、install_character.py、runtime_runner.py/runtime_runner_revision.py、build_runtime_media.py、record_review.py、collect_gifs.py；local_baseline.json与生产基线、首批user_approval_20261023.json、AllGIF/manifest.json，以及当前角色实际材料。

所有权必须核对：链state=active、owner_thread_id等于本新聊天实际CODEX_THREAD_ID、current_character=WinterWarg、dispatch_token精确匹配后，才允许生产修改和Unity操作。新聊天可能先于父登记启动；handoff_ready时只做独立只读同步，短暂分段等待，不超时抢锁、不修改链或创建第二后继。若父响应落盘/转移失败，报告具体现场。父一旦active转移即停止所有工作区写入。

实时进度100/108：WinterOgre111已完成art_r01/168PASS0FAIL/716真实PNG，completed_pending_user_art_review且user_approved=false。剩余8项：PossessedWarg79历史Down结果不明blocked；WinterWarg112、WinterWolfTypeA113、WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118七项not_started。108是授权数量，终项Zombie118。不要盲用progress.current或旧prompt快照。WinterWarg只有reference8文件，父仅核六保护，不把调度文件当作已prepare/生成/安装结果。

WinterWarg实际生产路径：battle=Assets/Prefabs/Enemy/Enemy_WinterWarg.prefab；source=Assets/_UIAssets/Monsters/Dogs/WinterWarg/WinterWarg.prefab；atlas=Assets/_UIAssets/Monsters/Dogs/WinterWarg/WinterWarg.png；controller=Assets/_UIAssets/Monsters/_Common/Animations/Wolf/Controller.controller；Directions=Assets/_UIAssets/Monsters/Dogs/WinterWarg/Directions。先实际查看原atlas和完整source prefab及battle层级/renderer/Body/Head/四腿/Tail/耳/锚点、原float/PPtr曲线/事件/时长/loop与移动/战斗/回收/同实例复用；制定自身解剖、正背面和步态，不套WinterOgre双足Giant或其他狗的布局。以当前磁盘和既有修改建立Assets/Packages/ProjectSettings/Luban全路径SHA基线（含新增/删除并集）及battle/source/atlas和各meta六保护；不能用Git HEAD消除已有变更。

工程路由明确为Unity2022.3.62f3c1 / unityMCP / http://127.0.0.1:8088/mcp。根AGENTS的FreedomTower_1/D:/8082是旧信息，8082现在属D:/FishTestGame，不得误操作或改写根规则。读mcpforunity://custom-tools与instances，从现场完整MyTowerGame ID set_active_instance，再读project/info核E:/MyTowerGame与版本。每次重连/域重载重核。桌面工具握手有问题但8088在线时可审阅复用mcp_call.py Client.identity()，其代理禁用和动态身份检查保持。离线按项目规则自主恢复已有HTTP Local服务/桥接，不抢端口/杀别人工程。进入Play前先读目标日志，再核场景和占用；本任务自己的两轮真实Play已有授权，不强停其他验证/录像或覆盖脏场景。

阶段流程必须实际执行：参考/解剖/prompt并审源图 → 仅缺少且没有在途/uncertain请求时首次生成Up，再实际审原raw → Down首次生成并实审 → 透明分件/Atlas/Pivot/PPU/布局/离线组合实际审图 → 单角色Builder安装及Verify → 两轮真实Play（普通死亡和指定Up死亡，每轮84PASS0FAIL）→ 实际媒体审阅 → record → GIF源/集中SHA核对 → 完整总结和唯一后继。每阶段落盘准确revision、计数、哈希、范围和未完成项。出现视觉问题即使程序PASS也须修复并用新运行revision，不删除旧清单或失败证据绕保护。

本机pipeline使用 C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8。PATH Python3.13是isolated，忽略脚本目录/PYTHONPATH，会使install子进程找不到mcp_call；不要再用。脚本run子进程沿用sys.executable。PowerShell中文用UTF8文件传长备注，勿把JSON.stringify当shell转义。

初次准备入口：character_step.py prepare WinterWarg；仅已有参考时先确认prepare不覆盖。图像任务先读当前imagegen SKILL.md，沿用已授权AIHub https://aihub.dog/v1 与现有生成器，gpt-image-2/quality=medium/n=1/size=1536x1024，优先既有Curl传输并Preflight。运行时从AIHUB_IMAGE_API_KEY或DPAPI clixml读取密钥，只发aihub.dog、不输出明文、不跨域携带；不改系统代理或复制角色特定恢复许可。已有request/raw/result/uncertain或在途进程先检查，不能盲重发。出现传输不明准确分类，不推断未计费。既有standing_recovery授权如确实适用，读取原用户证据、核范围并按现有生成器的角色支持和计数执行；不得自动重置计数或把代理自己设的max1说成用户预算。WinterOgre旧五次不确定仍保留，已恢复Up05和首次Down两个HTTP200不意味着旧请求免费。

stage入口character_step.py stage WinterWarg。必须实际检查两方向raw、14或实际需要的分件数量、alpha/去底/描边/孔洞/切片/Atlas/Pivot/PPU/顺序和组合；原色、脸、毛、装备、真实器官和tail根连接，Up无脸/后跟正确、Down面部与脚趾正确，左右原侧面保留，四向及状态/死亡/复用无地面阴影。独立读取Wolf原Walk时长；build_runtime_media.py把0.5s写死，若原clip不同仅在角色Docs中用真实相位修正并保留旧媒体，不能谎标周期或合成动作。

安装前再核六保护和范围指纹、Unity身份与空闲。单角色现有Builder安装，installed_manifest存在就恢复而非删除；记录完整prePlay生产指纹，Directions.meta位于art_dir外可能被目录内扫描遗漏，要单列核对。两轮实际运行必须用最终生产版本，保存actual_frames.jsonl、actual_runtime_checks.txt、全部原PNG、revision/SHA和安全返回场景。覆盖四方向步态、连续转向/相位延续、纯纵向与斜向/滞回、原生状态/头事件/攻击、受击和致死白闪结束、全身死亡旋转收缩淡出、自动回收/同实例正常复用、暂停恢复1x2x3x。不能用手动Animator.Update或离线图假冒Play。C#确需最小修改时查调用/依赖，完成同批后按8088目标MCP refresh/request compile、轮询ready/compile/reload/update、error和errorCS及scriptCompilationFailed闭环；不把历史错误清空。

实际查看两轮four_directions、runtime strip、按时间的足够原PNG和所有最终GIF编码帧。若工具不能实时播放，按序抽样并如实记录范围/限制；一次1～2张清晰预览和必要原尺寸局部，原件留盘，勿累计整个队列图片。运行PASS不能代替视觉通过。把实际中文观察写record_note_utf8.txt，先核runtime_summary最终版本/168/0/帧SHA再record。最终只能completed_pending_user_art_review、user_approved=false；用户自己批准才user_approved。现有record_review.py会调用collect_gifs.py，核全部实际来源及集中副本SHA，区分当前审核/历史与否决，数量由现场manifest算，不写死每角色12。完整路径并集审计归因本角色与确证Reporter时间戳，原prefab语义/GUID/root/HP/锚点/移动战斗/原动画合同/导入/依赖/收集覆盖保持；不称旧全局失败已通过或宣称构建回读。

前任WinterOgre的最终证据在WinterOgre/final_validation_20261029.json、version_binding_final_20261029.json、scope_incremental_final_20261029.json、visual_review_art_r01_20261029/review.json、gif_archive_verification_20261029.json。281板采样位/263不同PNG、8完整原PNG、60编码帧及4整帧；未实时播放或全审。AllGIF1612，本角色12最终+6历史共18。完整增量5545→5565文件，22变化/20新增/0删除、unexpected0；原组件semantic PASS、源与其他共享资源不变。最终clean Boot非Play/failed=false/ready=true/currenterror0，早期MCP错误保留在原证据。不要运行前任prepare/stage/install/finalize，或清理旧5次uncertain。PossessedWarg阻断仍独立保留。

边界：不git pull/reset/clean/checkout覆盖、不commit/push、不构建部署、不删除资源/场景、不改保护表Luban/Config/Datas/Levels/**、EnemyData.xlsx、__tables__.xlsx，不直接写Assets/ConfigJson或Gen、不恢复声音系统；不创建子代理/fork/并行角色/计时器/定时任务，不改长期memory，不改模型或推理设置。用户长期偏好完整单次可复制prompt，后继说明交付为完整UTF8文件、不占位或分段省略。

完成WinterWarg或准确记录真实阻断后，先安全交回Unity，核实时items优先恢复可恢复已开始项，再选最低index独立未开始角色，PossessedWarg无新可恢复证据就保留。新建带时间总结，更新README/live prompt、NEXT_ENEMY_TASK完整说明和progress，chain=handoff_ready并产生唯一token；按协议现场list_projects确认E:/MyTowerGame项目，再唯一create_thread(target={type:"project",projectId:现场ID,environment:{type:"local"}},prompt:完整新提示)。不fork、不model/thinking override。先保存明确成功响应，再最后工作区写入active新owner/token和创建记录；此后父只读，用一次有界wait_threads确认启动，最终给真实::created-thread。创建结果不明先查返回/实际聊天列表，不能盲目再创建。创建失败保留完整NEXT和总结并如实报告。循环至108有效完成或只剩确实阻断，不逐角色等用户确认。
