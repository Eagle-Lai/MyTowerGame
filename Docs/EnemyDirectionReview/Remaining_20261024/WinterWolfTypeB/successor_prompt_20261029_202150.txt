# WinterWolfTypeB114 唯一接棒执行 Prompt

在E:/MyTowerGame继续敌人四方向续作。当前唯一目标WinterWolfTypeB(index114)，先读文件并核对链所有权，再实际完成一个角色，最后按协议创建唯一后继。总进度102/108，状态completed_pending_user_art_review仅表示内部完成，用户未美术批准。本文件是完整UTF8接棒说明，不依赖旧聊天图片。

## 1. 唯一所有权和开工同步

dispatch_token=winterwolftypea-to-winterwolftypeb-20261029_202150-95ef4a42-ad29-4647-9b2c-ffe57580e7b0
父线程=01a18704-42a8-7f52-bc92-f8ca404a0b39
先读E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/Remaining_20261024/conversation_chain.json、progress.json、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、NEXT_ENEMY_TASK.md、Docs/EnemyDirectionReview/README.md和Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/20261029_202150_WinterWolfTypeA_completed.md。先读本角色已有reference及实际材料、git status和相关差异。全工程既有未提交工作必须保留；同步不授权git pull/reset/clean/checkout、commit/push。

只有chain.state=active、owner_thread_id等于本新聊天实际ID、current_character=WinterWolfTypeB且token完全匹配后才能改生产或操作Unity。若handoff_ready，限次只读等父登记，不能超时抢占；token或owner不匹配则不动生产。max_active_production_tasks=1，一次只做一个角色，不启动子代理、并行角色、fork、自动化或定时器。父会先记录create_thread明确成功响应，再最后写入active新owner并停止工作区写入。

实时队列剩余6项：PossessedWarg79 blocked、WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118。108是授权项数，末项index118，WolfMounfed原拼写保留。PossessedWarg Down旧请求结果未知，不把request存在解释为未发送/未收费，不重发。当前已递归核实B只有8个reference文件，无generation/staged_art/install/runtime；在你开工时再核实，恢复新增阶段而不盲目从prepare开始。

## 2. 正确Unity路由与用户边界

目标E:/MyTowerGame、Unity2022.3.62f3c1，现场版本文件为准；unityMCP HTTP http://127.0.0.1:8088/mcp。根AGENTS的FreedomTower_1/D:/8082是旧信息；8082当前属于FishTestGame、8080属于CatchFish，不改根AGENTS、不操作其他工程。用户要求控制电脑前弹确认；本任务用文件/命令行和Unity MCP，不得擅自控制桌面。

首次/重连/域重载动态读mcpforunity://custom-tools及instances，选MyTowerGame完整ID，set_active_instance，再读project/info核路径版本。可复用已审mcp_call.py Client.identity()直连8088，loopback禁代理，不硬编码实例hash。离线按项目规则自主恢复已有服务桥接、不抢端口、不杀其他工程；桌面控制确需时遵守用户确认要求。无法恢复须说明工程/版本/服务8088和具体启动连接动作。

操作前先读取error/errorCS日志，再读editor/state和实际probe，确保无他人Play、录像、测试、review、balance/manual、编译或脏场景。前任已交回clean Boot，不能据旧快照强停后来任务。当前角色两轮真实Play已有授权，不逐角色再问。测试完成安全交回原干净场景。

## 3. 源参考、身份与原动画合同

battle=Assets/Prefabs/Enemy/Enemy_WinterWolfTypeB.prefab
source=Assets/_UIAssets/Monsters/Dogs/WinterWolfTypeB/WinterWolfTypeB.prefab
atlas=Assets/_UIAssets/Monsters/Dogs/WinterWolfTypeB/WinterWolfTypeB.png
controller=Assets/_UIAssets/Monsters/_Common/Animations/Wolf/Controller.controller
Directions=Assets/_UIAssets/Monsters/Dogs/WinterWolfTypeB/Directions

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

写conversation_handoffs带时间B总结，含真实修改、revision/指纹、运行计数、所审画面、范围、Unity状态、请求消耗和后继。更新README及主执行prompt的live块，保历史；写一个完整UTF8 NEXT和后继prompt，不分段不省略不放占位符。先确认Unity释放，再chain=handoff_ready、新唯一token、parentID、下一角色。现场list_projects确认E:/MyTowerGame，唯一create_thread(target={type:project,projectId:现场ID,environment:{type:local}},prompt:完整文本)，不fork/子代理/模型推理覆盖。创建结果不明先查真实响应/聊天不重试。明确成功响应落盘，父最后工作区写chain=active新owner/token并停止所有写入；一次有界wait_threads确认启动，最后给真实created-thread directive。创建失败保留完整prompt与总结，准确报告。

禁止配置表自动改写、Assets/ConfigJson或Assets/Gen直接写入、恢复声音、构建部署、生产删除、Git提交推送、memory修改、桌面擅控。所有已有失败/否决/unknown/计数与安装清单保留。现在从身份、所有权、现场和自身完整源图开始，完成实际工作。
