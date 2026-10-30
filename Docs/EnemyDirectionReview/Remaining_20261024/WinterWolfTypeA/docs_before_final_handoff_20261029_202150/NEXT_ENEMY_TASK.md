# WinterWolfTypeA(index113) 阻塞恢复完整执行 Prompt

在 E:/MyTowerGame 继续敌人四方向续作，本次唯一角色仍为 WinterWolfTypeA(index113)。本文件是完整 UTF8 恢复入口，可以一次复制。任务尚未完成，不把阻塞当作验收，不重新准备或盲目生成，不创建空转后继。当前时间记录 2026-10-29T18:09:02.454154+08:00；实时进度101/108，AllGIF1642。

## 1. 先读现场与所有权

先完整读取 E:/MyTowerGame/AGENTS.md、ProjectSettings/ProjectVersion.txt，以及以下文件；下列相对路径均相对 E:/MyTowerGame：

1. Docs/EnemyDirectionReview/Remaining_20261024/REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md。
2. Docs/EnemyDirectionReview/Remaining_20261024/CONTINUATION_PROTOCOL_20261026.md 和 IMAGE_RELAY_RECOVERY_20261026.md。
3. Docs/EnemyDirectionReview/Remaining_20261024/NEXT_ENEMY_TASK.md、conversation_chain.json、progress.json。
4. Docs/EnemyDirectionReview/README.md 和 PREFAB_CHANGES_SUMMARY_20261026.md。
5. Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/20261029_180902_WinterWolfTypeA_blocked.md 与 Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/blocked_generation_recovery_20261029_180902.json。
6. Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/down_request_recheck_20261029_180355.json、Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/request_process_recheck_20261029_180355.json、Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/scope_incremental_blocked_20261029_180355.json、Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/unity_release_blocked_20261029_180355.json、Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/successor_assessment_blocked_20261029_180355.json、Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/up_art_review_blocked_20261029_180355.json、Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/docs_tooling_final_20261029_180355.json。
7. WinterWolfTypeA 目录中的 sync_start_20261029.json、production_paths_before_20261029.json、anatomy_plan.json、source_animation_contract_complete_20261029.json、standing_authorization_original_messages_20261029.json、standing_recovery_application_20261029_Down.json、proxy_transport_application_20261029.json、read_only_service_recheck_20261029T094736Z.json、unauthenticated_transport_control_20261029.json 和全部 generation 原始材料。
8. 现有 character_step.py、prepare_character.py、generate_character.ps1、generate.mjs、pack_character.py、adjust_layout.py、install_character.py、runtime_runner.py、runtime_runner_revision.py、build_runtime_media.py、record_review.py、collect_gifs.py，local_baseline.json、production_fingerprints_before.json、Batch01_10/user_approval_20261023.json 和 AllGIF/manifest.json。

当前链 state=blocked，owner_thread_id=01a18704-42a8-7f52-bc92-f8ca404a0b39，dispatch_token=winterwarg-to-winterwolftypea-20261029_173527-8e8dd053-9008-4a8f-b69a-61a589f400a4，current_character=WinterWolfTypeA。没有新后继聊天，也没有新token。blocked期间只读诊断、核对与保存Docs恢复证据；不能操作Unity或生产资源。恢复条件实证满足后，由同一合法owner记录具体恢复依据、保持owner/token并将链恢复active，再执行后续；若用户另开新聊天，先同步，只能在原owner明确转移唯一所有权后操作，不超时抢锁、不自行改owner、不重复派发。

## 2. 当前准确阻塞与费用状态

Up首次请求HTTP200，原图generation/Up/raw.png，RGB1536×1024，1403379bytes，SHA256=0ECD4F96A778688C9DD614F23B70E09AE79A397082E8C1581510F969856D4586。Down三次都结果不明：

| 请求 | 现场结果 | 当前缺失 |
|---|---|---|
| generation/Down | Curl55 Send failure: Connection was aborted | 无HTTP、raw、result、query/job ID |
| generation/Down/revision_01 | Curl55 Send failure: Connection was aborted | 无HTTP、raw、result、query/job ID |
| generation/Down/revision_02 | 经既有127.0.0.1:7897代理仍Curl52 Empty reply from server | 无HTTP、raw、result、query/job ID |

三个请求的prompt/request/console/uncertain均保留；完整SHA见阻塞报告和down_request_recheck。站立授权原用户原文是“继续任务。后续同样的情况，不再需要我确认，可以继续静默执行”，来源聊天01a18093-7687-7313-aaba-7419090cc829、用户消息01a180aa-7768-7222-bc85-7aa51e801cdd，本聊天已read_thread现场核对。两个额外恢复机会2/2均已消耗，数字是代理保守执行上限，并非用户金额预算；不重置前任任何角色计数。本文件没有新增付费机会，不再发送Down或用下一角色付费探测。

认证GET/models与GET/usage曾返回200、余额有效，但不能证明图像POST可用、旧请求未收费或已完成。无密钥诊断中直连上传65331bytes后Curl55，既有代理完整上传434497bytes返回401/TLSverify0；真实代理Down02仍Curl52。系统代理未更改。本轮收尾没有新付费调用，进程复查无在运行的图像生成器；本地进程结束不证明远端未处理。

先查现存结果、文件、服务响应及可用provider查询路径。需要恢复旧Down结果及其版本关联，或获得具体请求处置；确需新请求时，必须先诊断并解决真实认证POST故障，再记录在已有授权内的新有限执行决策。重复GET200、无密钥401、时间经过或换聊天均不是恢复证据。三次费用始终unknown，不推断免费。不要盲查未文档化付费端点，不再重复诊断计费请求。

## 3. 参考、解剖与现有Up局部稿

battle=Assets/Prefabs/Enemy/Enemy_WinterWolfTypeA.prefab；source=Assets/_UIAssets/Monsters/Dogs/WinterWolfTypeA/WinterWolfTypeA.prefab；atlas=Assets/_UIAssets/Monsters/Dogs/WinterWolfTypeA/WinterWolfTypeA.png；controller=Assets/_UIAssets/Monsters/_Common/Animations/Wolf/Controller.controller；Directions=Assets/_UIAssets/Monsters/Dogs/WinterWolfTypeA/Directions。

已实际看完整原atlas与完整序列化源参考，读战斗/源层级与锚点。真实特征是棕橄榄背、赭圆斑、高尖棕耳、象牙白眉和白眼底/深瞳、白长口鼻、宽白尖胸毛、四条短棕上腿/白爪、整条象牙白加taupe阴影的蓬尾。不是琥珀发光眼，不是只有尾尖白，不沿用WinterWarg的刺或造型。无项圈、鞍、背刺。

原Up躯干出现额外耳状突起，后脚带前趾线。local_revision_01移除躯干重复耳并闭合白肩毛，local_revision_02继续去后趾但填色有斑驳；最新generation/Up/local_revision_03/raw.png将后跟下部内侧平涂为原风格象牙白，保留四像素外描边。最新SHA256=B7FFAC6DE6A7250C481AC1E6D0E78B1E03390CB9FED2EE068B7945080ABFA32D。全部原件、三份本地修订、processing.json、前后放大对照与retouch脚本保留。本地修订不是新的AI结果，原Up与最新全图及局部对照已实看。最新仍是候选，不是透明分件或最终绑定通过；未建art_selection，未stage。

anatomy_plan和Up/Down提示已按真实源图改好，初始generic副本保留。character_step.py prepare已经执行，不重跑；prepare_reviewed_20261029.py完成计划/提示但首次合同对象序列化错误和末尾打印失败，随后capture_contract_20261029.py保存有效source_animation_contract_complete_20261029.json。早期source_animation_contract_20261029.json仅历史，不把它当结构化合同，也不重跑会覆盖备份的prepare脚本。

原合同：Ready0.5s/loop/24float，Walk0.5s/loop/33float，Attack0.5s/nonloop/48float，Death0.416666657s/nonloop/39float；四clip均0PPtr。Attack SetHead0@0、SetHead1@0.166666672、Event("Attack")和SetHead0@0.333333343；Death SetHead2@0。参数Attack trigger、Action bool、State int、Speed float。完整keys与层级以complete文件为准。保留原侧向所有曲线、时长、loop、事件、状态机及回收复用合同，只追加纵向适配。

## 4. 工程身份、范围和现有生产保护

实际目标E:/MyTowerGame / Unity2022.3.62f3c1 / unityMCP / http://127.0.0.1:8088/mcp。AGENTS里的FreedomTower_1/D:/8082是旧信息，8082现在属于FishTestGame，8080属于CatchFish；不改根规则、不操作其他工程。版本以ProjectVersion文件现场为准。桌面控制必须先询问用户，本轮未使用。

需要Unity操作时，先读mcpforunity://custom-tools及instances，动态选择完整MyTowerGame ID并set_active_instance，再读project/info核路径和版本；新会话/重连/域重载重核。桌面MCP握手失败可审阅复用mcp_call.py Client.identity()直连HTTP8088，loopback禁代理。离线按项目规则自主恢复已有服务/桥接，不抢端口、不杀进程、不依赖离线服务启动自身。

开工时已保存Assets/Packages/ProjectSettings/Luban共5585文件完整路径SHA基线和battle/source/atlas及各meta六保护，六项匹配最初production_fingerprints。收尾全路径并集审计5585→5585，changed/added/deleted全部空，无Reporter时间戳例外，源文件、共享C#、原Wolf合同、其他角色和配置均无本轮漂移；原基线/首批批准/AllGIF清单SHA不变。历史全局scope失败未重审，不宣称全局PASS。原git改动保留，不能以HEAD回滚消除差异。

最新Docs/EnemyDirectionReview/Remaining_20261024/WinterWolfTypeA/unity_release_blocked_20261029_180355.json通过动态身份确认，clean Boot、非Play、非dirty、review/balance/manual=false，compile/reload/update/tests=false、ready=true、scriptCompilationFailed=false，error与errorCS返回0。没有生产改动、C#改动、stage/install/Verify/Play/runtime/record，没有新GIF，没有构建部署。Unity已空闲安全交还；没有请求刷新或编译。

Docs共享generate.mjs仅增加当前WinterWolfTypeA Down Curl55的standing恢复01/02，以及仅Down02使用SHA绑定无密钥完整上传401证据的既有代理传输。原owner/token/原授权/证据SHA/无成功/计数保护保留。原文件备份和完整patch见docs_tooling证据，不擅自移除防重保护或扩张为通用无限重试。

## 5. 恢复后逐阶段继续，不跨阶段宣称完成

所有流水线Python用 C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe -X utf8，子进程用sys.executable；不使用PATH Python3.13 isolated。图片任务遵循已读imagegen与full-output-enforcement技能，用户授权AIHub优先于工具默认路由。AIHub https://aihub.dog/v1，既有生成器gpt-image-2/medium/n1/1536x1024；密钥仅运行时从环境或C:/Users/Administrator/.codex/secrets/aihub-image-key.clixml DPAPI读取，仅发送aihub.dog，不明文输出/落盘/跨域重定向。保存每个request/raw/result/uncertain/error，任何请求前核在途与已成功结果，不删旧请求或安装清单绕过防重。

恢复出有效Down后先实看完整Down及Up候选，审正确正脸/前趾与纯后脑/后跟、原色/胸毛/尾根、无影、清晰描边及完整连接。确认后再选art_selection；character_step.py stage WinterWolfTypeA前核暂存不存在，不无条件重跑full stage。按实际分件清品红透明背景，检查边缘污染、描边、孔洞、透明连接根、Atlas切片、PPU、pivot、render order与完整四向离线组合。名义格界不是裁掉耳足尾的理由，必要局部修补必须留原始来源/范围/SHA与修前版本。保留原左右侧图，原有四腿按对角配对、短步幅、轻躯干摆及克制尾摆；Up头在远端上方、肩毛连接，下方棕臀与尾根；Down远臀上方、白胸与头朝下覆盖，尾在臀后。

安装前复核生产全指纹、六保护、正确Unity身份和空闲；Directions.meta位于目录外必须单列。若已有installed_manifest走实际恢复/返修路径，不删除清单。只安装当前角色Builder并Verify，记录最终生产全指纹后才运行。本任务两轮真实Play已有授权，先日志再状态/占用，不覆盖脏场景、不强停他人测试。原生普通死亡与指定Up死亡每轮84PASS0FAIL，保存全部actual_frames.jsonl/actual_runtime_checks.txt/真实PNG及Unityframe、normalizedTime、realtime和SHA，最终runtime_summary绑定实际最终版本，总168PASS0FAIL。恢复原干净场景并确认无录像/测试/编译占用。

覆盖四向步态、纯纵向/斜向滞回、近零保持、连续转向相位、原生状态和头事件、攻击/受击/致死白闪结束、完整死亡旋转收缩淡出、自动回收/同实例复用、暂停恢复及1x2x3x和适用飞行。不得用Animator.Update或离线合成冒充真实Play；程序PASS而画面不对仍须保留旧版本返修并重跑最终两轮。

C#若确需修改，先读实现/调用/生命周期，同批改完再8088 MCP refresh_unity(mode=force,scope=all,compile=request,wait_for_ready=true)，1–2秒轮询compile/reload/update=false且ready=true，再read_console(error/errorCS)及scriptCompilationFailed=false；编译期间不写代码，断线先等约5秒、重连重核，保留历史错误不清控制台。无UnityC#改动不为收尾额外改脚本或编译。

build_runtime_media.py可能写死0.5s；本角色原Walk正好0.5s，但仍需解码GIF累计时长及真实相位，避免非10ms帧间隔截短。必要时仅当前角色Docs保留修前GIF并做累计10ms量化，记录量化误差，不合成姿态、不改共享脚本；不照抄WinterOgre670ms或前任修订计数。

实际审最终两轮four_directions/runtime strip、足够真实时序PNG和最终GIF编码帧，1–2图/次，原件留盘。审图crop不能裁完整耳/足/尾；必要另看未裁nativePNG和GIF整帧。不能播放就准确记录抽样范围，不能声称实时播放或全帧通过。最后使用现有record_review流程，UTF8视觉备注先写文件再传参；最终只能completed_pending_user_art_review、user_approved=false，用户明确批准才可批准。record调用collect_gifs集中归档所有实际GIF，核源与集中副本SHA，区分最终/否决/历史，不固定每角色12或固定总数。现在1642保持，本轮无新GIF无需为阻塞重跑record或collect。

## 6. 队列、恢复后的唯一后继和禁止事项

剩余7项已递归核查：PossessedWarg79旧Down结果不明，只有Up且无stage/install/runtime；WinterWolfTypeA113为当前Down三不明；WinterWolfTypeB114、Wolf115、WolfHound116、WolfMounfed117、Zombie118均not_started且各只有8个嵌套reference文件，无生成、暂存、安装或运行阶段。没有能独立交付的恢复阶段。正常下一个未开始角色是WinterWolfTypeB114，但当前需要同一失败图像POST，不能把它当付费探针或创建空转后继。因此链已blocked，保留当前owner/token，无新聊天，不宣称后台继续。

当前角色真正完成或新现场出现可独立恢复的阶段后，安全交还Unity，重读实时items，优先可恢复已开始项，再选最低index未开始项。保留PossessedWarg未知请求及任何前任消耗。写带时间总结，更新README、主执行prompt实时块、完整UTF8 NEXT和progress；仅确有可执行唯一后继时chain=handoff_ready并生成新token。现场list_projects核E:/MyTowerGame，唯一create_thread(target={type:"project",projectId:现场ID,environment:{type:"local"}},prompt:完整新提示)，不fork、不覆盖model/thinking。明确成功响应落盘后父最后写链转active新owner/token并停止工程写入，一次有界wait_threads确认启动，最终只用真实created-thread；创建结果不明先查实际响应/聊天，不重复创建。全部108有效完成或只剩真实阻断时停止。

禁止git pull/reset/clean/checkout覆盖、commit/push、构建/部署、删除资源/场景、自动改关卡/敌人/登记数值表、直接写Assets/ConfigJson或Assets/Gen、恢复声音、子代理/并行角色/fork/定时器/自动化、长期memory修改、模型/推理设置覆盖。保留首批10项用户批准及所有历史失败、否决和冻结证据。完整prompt交付一个UTF8文件，不分段、不省略、不使用占位符。
