# WolfMounfed117 唯一接棒执行 Prompt

在E:/MyTowerGame继续敌人四方向续作。本聊天只完成WolfMounfed(index117)，完成后按串行协议创建唯一后继。当前105/108，所有completed_pending_user_art_review仅内部完成，用户尚未美术批准。本文为完整UTF8执行说明，不依赖旧聊天图片。

## 1. 唯一所有权和现场同步

dispatch_token=wolfhound-to-wolfmounfed-20261029_222452-68c070b7-1479-493d-aae5-005029aba3d5
父线程=01a187ef-5f47-7760-b7fe-97a5e2d35e37
先读E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt、Docs/EnemyDirectionReview/Remaining_20261024/conversation_chain.json、progress.json、CONTINUATION_PROTOCOL_20261026.md、IMAGE_RELAY_RECOVERY_20261026.md、REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md、NEXT_ENEMY_TASK.md、Docs/EnemyDirectionReview/README.md及Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/20261029_222452_WolfHound_completed.md。读本角色已有证据、git status、相关差异、实现、直接依赖/生命周期；保留全部既有未提交改动。同步不授权git pull/reset/clean/checkout、commit/push。

只有chain.state=active、owner_thread_id等于本聊天真实ID、current_character=WolfMounfed且token完全匹配，才能改生产或操作Unity。若handoff_ready，仅只读限次等待父登记，不因超时抢占。max_active_production_tasks=1；一聊天一角色，禁止子代理、并行角色、fork、定时器和自动化。父先保存明确创建响应，再以最后一次工作区写入登记新owner active，随后停止全部工作区写入。

剩余3项：PossessedWarg79 blocked、WolfMounfed117、Zombie118。108为授权数量，末项index118，WolfMounfed保持原拼写。PossessedWarg旧Down无raw/result/服务查询ID、结果及费用unknown，不推定未发送/未收费，不重发。交接时WolfMounfed仅8个reference文件，父额外写此prompt，没有generation/staged_art/install/runtime。开工重新递归核实，恢复已出现阶段，不盲目prepare、生成或安装。

## 2. 工程身份与Unity8088

目标E:/MyTowerGame，Unity2022.3.62f3c1，以ProjectVersion.txt为准。unityMCP HTTP Local http://127.0.0.1:8088/mcp。根AGENTS的FreedomTower_1/D:/8082为旧信息，8082属于FishTestGame、8080属于CatchFish；不操作其他工程，也不为此改根AGENTS。用户要求桌面/电脑控制先弹确认，本任务优先文件/命令行与Unity MCP，不擅控桌面。

首次/重连/域重载后读mcpforunity://custom-tools和mcpforunity://instances，动态选MyTowerGame完整ID，set_active_instance，再project/info核路径/版本。可复用Remaining_20261024/mcp_call.py Client.identity()，loopback禁代理、不硬编码实例hash。服务离线按既有授权恢复目标已有服务/桥接，复用在线服务、不抢端口、不杀其他工程；确需桌面操作仍须用户确认。失败及时说明E:/MyTowerGame、版本、8088故障环节和具体开启/连接步骤。

操作前先读error/errorCS，再state及实际probe，确认无他人Play、脏场景、测试、review/balance/manual/recording、编译/更新。前任交回单一clean Boot不能替代现场核对，不能强停后来任务。本角色两轮真实Play已有授权，不逐角色再问；结束恢复原干净场景。无Unity C#改动不为形式额外编译。如改C#，同批完成后8088 MCP refresh_unity(mode=force,scope=all,compile=request,wait_for_ready=true)，每1–2秒读state直到compile/reload/update=false且ready=true，error/errorCS0、scriptCompilationFailed=false；期间不改代码，断线约5秒重连重核，不清控制台。

## 3. WolfMounfed自身源参考和原动画合同

battle=Assets/Prefabs/Enemy/Enemy_WolfMounfed.prefab
source=Assets/_UIAssets/Monsters/Mounts/WolfMount/WolfMounfed.prefab
atlas=Assets/_UIAssets/Monsters/Mounts/WolfMount/WolfMounted.png
controller=Assets/_UIAssets/Monsters/_Common/Animations/Wolf/Controller.controller
Directions=Assets/_UIAssets/Monsters/Mounts/WolfMount/Directions

WolfMounfed保持实际拼写，atlas文件名WolfMounted.png、目录Mounts/WolfMount。父未审本角色实际源图。按真实源层级核对是否有骑手/鞍具/武器及其归属；只保留源确有的器官装备，不按名称推定，也不继承WolfHound项圈。

读local_baseline.json、production_fingerprints_before.json、Batch01_10/user_approval_20261023.json与AllGIF/manifest.json。建立Assets/Packages/ProjectSettings/Luban全路径SHA基线，以及battle/source/atlas和三meta六保护；Directions根.meta单列，新增删除都计入。定向读BaseEnemy、EnemyDirectionalVisual/Profile、MonsterAnimEventReceiver、EnemyDirectionalRigBuilder、EnemyDirectionPrefabBuilder、EnemyDirectionBatchReview、RemainingCatalog/Motion及直接调用/缓存/回收复用。

必须实看完整原atlas与source_prefab_offline，读层级、各器官、锚点、渲染顺序、左右原图。不能按WolfMounfed名字或复制WolfHound/Wolf/WinterWolfTypeB的颜色、器官、比例、布局。捕获自身Ready/Walk/Attack/Death和controller完整结构化合同：状态/参数/过渡、所有float和PPtr绑定、完整key/tangent/weight、事件、loop/时长/rate；不以ToString对象冒充合同。Up为真后脑无五官/前向耳垫，后跟平滑；Down真正面/前趾。不加原型没有的装备，不留重复头耳、断颈或浮动器官。保护首批10项用户批准、BlueScorpion最终尾及否决历史。

## 4. Image API正式入口、防重复与网络恢复

已有用户AIHub授权，https://aihub.dog/v1/images/edits，gpt-image-2、medium、n=1、1536x1024。密钥仅运行时从AIHUB_IMAGE_API_KEY或C:/Users/Administrator/.codex/secrets/aihub-image-key.clixml DPAPI读取，仅送https://aihub.dog，不输出、不落盘、不进命令行参数、不跨域转发，结束清临时环境。使用现有generate_character.ps1/generate.mjs，先读入口及保护，逐方向审阅。

用户固定Curl参数--resolve aihub.dog:443:191.101.132.254必须保留。WolfHound本次Up/Down初次均HTTP200，raw1529005/1413412bytes，实际PNG RGBA1536×1024，共2请求0unknown0恢复。读image_transport_edge_map_20261029_1830.md、docs_tooling_edge_resolve_20261029_182840.json、WolfHound/generate_initial_direct_20261029.ps1与generation_final_accounting_20261029.json；必要再读WinterWolfTypeB/docs_generator_recovery_20261029.json及patch。包装脚本含角色专用owner/token，须独立适配WolfMounfed，不直接执行WolfHound/Wolf/B脚本。

普通入口verifiedDirectTransport可能false。调用进程内临时NO_PROXY=aihub.dog，暂清HTTP_PROXY/HTTPS_PROXY/ALL_PROXY，finally恢复；确保Curl直连固定域名边缘，不用--system-local-proxy、不改hosts/系统代理、不禁TLS。Preflight只核输入/路由，不发图请求。若改Docs工具，先留SHA/backup/patch，仅定点改合法入口，不弱化owner/token、源指纹、已成功图、请求结果或计数保护。

任何request/raw/result/uncertain/revision先查材料和在途进程。成功不重生；unknown不当成失败或未收费，超时不盲重发。B初次Up Curl55仍unknown、standing额外1/2；A旧三Down unknown、standing2/2及A Down03专用max1不得借给WolfMounfed或重置。若同类网络故障，先核WinterWolfTypeA/standing_authorization_original_messages_20261029.json中的原人类回复“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”、范围、已用计数和合法入口，再按现有授权推进。代理执行界限不是用户金额预算，不删日志/改名绕防重，不以非鉴权401或外部WorkBuddy推理倒推未计费。没有合法恢复路径则准确阻断，不借其他角色付费探测。

## 5. 制作、安装与两轮真实Play

Python统一C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8；子Python用sys.executable。先读character_step.py、prepare_character.py、pack_character.py、adjust_layout.py、render_staged_rig.py、install_character.py、runtime_runner.py、runtime_runner_revision.py、build_runtime_media.py、record_review.py、collect_gifs.py。仅未准备时character_step.py prepare WolfMounfed。按自身源完善anatomy_plan及prompt，实看每张raw后再art_selection。局部像素修订保父图、区域、方法和SHA，明确是本地衍生，不冒充新AI返回。

按实际测量矩形分件，不假定格界；去品红、查透明微洞/尘点/描边污染、切片、PPU/pivot/render order和根部遮挡。前任14分件/2048只是前任事实，按本角色实际和工具合同处理。平涂不得留矩形缝/碎斑/重复器官；全身离线四向与细节均须实际看，耳脚尾不裁。足尾根连接，四足对角短步、躯干/尾错相，攻击蓄力发力、死亡连接，无地面影。保原左右曲线/事件/loop/时长。full-stage/pack会覆盖后续alpha修订，先保父版本再执行。

安装前重核owner、8088身份、error→state→严格空闲和全路径保护。未安装前语义工具可能因缺Directions返回false，只作诊断；以六保护+完整路径精确SHA作门。只装WolfMounfed并Builder/Verify，不全目录重建、不删installed_manifest。安装后绑定battle/meta、Directions所有文件及根.meta、全部暂存文件、安装manifest和Verify的SHA，绑定后才运行。

普通死亡与Up死亡两轮真实Play，每轮84检查，共168PASS0FAIL；初次runtime_r01/runtime_updeath_r01，返修用未占用revision并保旧轮。保actual_frames.jsonl/checks/原始PNG/Unity frame/realtime/normalizedTime/SHA，覆盖四向及斜向滞回/近零、原生状态/头事件、连续转向保相位、受击/致死闪白结束、死亡旋转收缩淡出、自动回收同实例复用、暂停恢复、1x2x3x及适用Flying探针。禁止Animator.Update或离线合成冒充实际Play。断言PASS仍须审画，有视觉错误就保旧返修、重绑定并重跑最终两轮。

## 6. 审阅、时长、范围与记录归档

实际查看最终两轮four_directions、runtime strip、足量时序真实PNG、原生循环和每个最终GIF的解码帧，覆盖动作。一次1–2图，原始完整证据留盘；先看未裁原图，再看保耳脚尾crop。记录实际采样位/不同PNG/GIF编码帧数、路径/SHA和观察。不能播放就如实写逐序抽样，不声称实时播放或全帧看完。WolfHound本轮605PNG、305采样位/293不同PNG只是历史，不能抄成新角色计数。

解码GIF实际总时长并比WolfMounfed自己的Walk合同，不从前任推定.5s。Pillow逐帧10ms截断可能缩短；需要时仅Docs保修前GIF/manifest，按真实normalized phase累计边界量化到10ms并保持合同总时长，不合成姿态。可读WolfHound/prepare_visual_closeout_20261029.py；WolfHound只修4个460–470ms Up/Down至500ms，原500ms双向GIF未重写。数量必须现场计算。

最终全路径并集含新增/删除/Directions根.meta；源/meta、原动画、共享C#、其他角色及配置保护。Reporter build_info仅在ReporterEditor不变、精确设备/本地时间格式符合且在实际Play时间窗时单列。历史global scope失败不重标PASS。最终生产/暂存/manifest/Verify须匹配prePlay，同版绑定runtime记录/PNG/媒体。再现场核import/rect/pivot/PPU/alpha/依赖/Verify收集器、errors0/failedfalse、单一clean Boot非Play全空闲；不构建发布包。

UTF8真实visual_note先写WolfMounfed/record_note_utf8.txt，再文件读取传character_step.py record WolfMounfed，避免PowerShell中文参数损坏。只能completed_pending_user_art_review、user_approved=false。record会collect_gifs；逐个核本角色全部GIF源/集中副本SHA、最终/修前/否决分类，保所有旧来源哈希。起点AllGIF1710只是此刻，不假定每角色12。保存final_validation/version_binding/scope/review/archive和Unity release，进度递增，首批批准不变。

## 7. 串行后继与父停止写入

完成WolfMounfed或准确记录真实阻断后安全交回Unity。重读progress并递归未完成材料，优先独立可恢复已开始项，再按index正常下一Zombie118；PossessedWarg旧unknown保留，不机械用progress.current。全部108有效完成或只剩真实阻断才停止，待用户美术审核不暂停链。

新建带时间WolfMounfed handoff，写实际修改/revision/指纹、两轮计数、所审范围/限制、Unity状态、网络尝试/unknown/计数及后继。更新README和主prompt live块，保留历史；写完整UTF8 NEXT与后继prompt，不省略、不占位、不分段。先确认Unity释放，再chain=handoff_ready、新唯一token、parentID/下一角色；现场list_projects核E:/MyTowerGame，唯一create_thread(target={type:project,projectId:现场ID,environment:{type:local}},prompt:完整文本)，不fork、不子代理、不模型/推理覆盖。创建结果不明先查真实响应/聊天，不重复派发。明确成功响应先落盘，再父最后工作区写chain active新owner/token，随后停止全部工作区写入；一次有界wait_threads确认启动，最终输出真实created-thread directive。失败保完整文件并准确报告。

禁止配置表自动改写、Assets/ConfigJson或Assets/Gen直接写、恢复声音、构建部署、生产删除、Git提交推送、memory修改或擅控桌面。保留历史失败/否决/unknown/计数/安装清单。现在先核所有权、工程和实际源参考，完成WolfMounfed的实际工作。
