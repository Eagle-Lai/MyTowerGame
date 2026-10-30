# MyTowerGame 敌人四方向资源与动画续作执行 Prompt

请在 E:/MyTowerGame 中，承接已经开展的敌人预制体四方向美术补全、方向接入、角色专属动画和审阅归档任务，继续完成 Remaining_20261024/progress.json 中尚未完成的角色。直接开展实际工作，持续推进至队列全部完成，或遇到确实无法自主解决的阻断；不要只分析、重写计划或重复已完成角色。

本文建立于 2026-10-26 的磁盘快照。执行时先读取实时状态，所有数量、角色阶段、资源选择和运行 revision 均以当前文件及有效证据为准。本文取代旧 20261024 prompt 中“只完成 6 个、从 Butcher 开始、GIF 为 105 个”的过时起点，不替换或改写历史证据。

## 0. 长任务串行续接与图片中转限制

用户于 2026-10-26 进一步要求按“一个角色完成 → 自动总结 → 更新 prompt → 自行开启全新对话 → 下一个角色”的方式循环。各对话遵循 `CONTINUATION_PROTOCOL_20261026.md`、`conversation_chain.json` 与 `NEXT_ENEMY_TASK.md`，完成当前唯一角色后主动创建唯一后继，不等待逐角色授权。不得以原文“持续处理”理解为在同一聊天内连续积累全部角色图片；不得并行创建多个生产修改任务。

<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->
2026-10-29 WinterOgre111续作后仍blocked，99/108，AllGIF1594、无新增媒体。原3次unknown保留，本轮新增Up revision_03 Curl55和修复传输后的revision_04 Curl52空回复，共5次均无HTTP/raw/result/查询ID，费用仍未知。原自动2/2与本轮两个独立max1决定均已用尽，不重置，不再付费，不拿Down/其他角色探针；Down从未请求。非计费对照定位直连上传71446字节后中断；经系统现有代理完整上传660604字节得到401、证书校验0，但正式请求仍无回复，不能宣称图像服务恢复。鉴权models/usage200、余额有效；汇总图像请求15/$1.05未变不能证明单次未收费。未stage/install/Verify/Play/record、未改角色生产资源/共享C#；5545路径并集仅Reporter旧自动时间戳，六保护/其他角色/配置无漂移，历史global291unexpected/6语义失败未重审。Unity8088现场身份正确，单一clean Boot、非Play、全空闲、failed=false/ready=true，保留2条MCP连接Error，error0未满足，不清日志。7个not_started只有reference8文件，PossessedWarg旧Downunknown保留；无独立可恢复项，chain=blocked保留owner/token，未建后继。证据WinterOgre/blocked_generation_recovery_20261029_143535.json，交接Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/20261029_143535_WinterOgre_blocked.md；完整入口NEXT_ENEMY_TASK.md。
<!-- ENEMY_SERIAL_LIVE_STATE_END -->

如果当前对话出现 `image relay inline images exceed the configured 32 MiB request limit`，先保留磁盘现场，不重复发送同一图片请求，不重复付费生成已有结果。使用 `IMAGE_RELAY_RECOVERY_20261026.md` 和 `CONTINUATION_PROTOCOL_20261026.md` 交接；需要时从不携带旧图片历史的新对话继续。

每个对话只负责一个敌人预制体角色：完成该角色当前阶段、安装、两轮真实运行、视觉审阅、record 和 GIF 归档，或记录真实阻断并安全交回 Unity，才能开始下一个角色。对 `Assets/Prefabs/Enemy` 的修改必须严格按角色逐个批次执行，禁止并行修改多个预制体。每个阶段都要将角色、状态、revision、运行计数、视觉审阅范围、证据路径和阻断原因落盘，再由下一对话读取实时 `progress.json` 续接。

图片原件和完整运行帧保存在磁盘。模型审阅时优先分次读取 1～2 张清晰预览及必要细节，不一次内嵌所有历史图片、所有 GIF 或全部角色证据；预览大小只是降低请求载荷的建议，不得代替原始证据检查，也不改变真实运行和视觉验收标准。新对话不得继承旧聊天中的图片历史作为继续执行的前提。

## 1. 目标、授权和完成标准

1. 原续作授权队列共 108 个角色。AdvancedHen 是此前示例；首批 10 个已获用户美术批准，不属于这 108 个续作角色。
2. 继续采用现有方向系统、单角色流水线及原角色风格，完成真正的 Up 背面和 Down 正面，不重新设计整套系统。
3. 对本轮剩余角色逐个完成：参考与解剖计划、原图审阅、分件与布局、单角色安装、两轮真实 Unity Play 检查、实际媒体视觉审阅、记录和 GIF 集中归档。
4. 已有授权允许继续全部剩余角色，不需要每完成一个就重新请求批量授权。用户美术待验收不阻止处理下一个角色。
5. 技术检查通过和内部视觉检查完成后，只能标为 completed_pending_user_art_review。只有用户明确批准，才能标为 user_approved；不能将本次“继续执行”的授权解释成美术批准。
6. 本任务要求逐角色验证。不能为了速度取消实际运行检查，不能只生成图片、只写文档或批量勾选完成。
7. 本任务不包含发布、构建 APK、设备部署、数值调优、自动 Git 提交或推送；不借用其他工程的平台或测试结果。

## 2. 开工先读取并同步现场

工作目录必须是 E:/MyTowerGame。先读取以下文件，并只针对即将处理的角色扩展检查：

- 根目录及目标目录链上的 AGENTS.md。
- ProjectSettings/ProjectVersion.txt。
- Docs/EnemyDirectionReview/PREFAB_CHANGES_SUMMARY_20261026.md。
- Docs/EnemyDirectionReview/README.md。
- Docs/EnemyDirectionReview/Remaining_20261024/progress.json。
- Docs/EnemyDirectionReview/Remaining_20261024/character_step.py。
- Docs/EnemyDirectionReview/Remaining_20261024/generate_character.ps1 和 generate.mjs。
- Docs/EnemyDirectionReview/Remaining_20261024/prepare_character.py、pack_character.py、install_character.py、record_review.py。
- Docs/EnemyDirectionReview/Remaining_20261024/runtime_runner.py、runtime_runner_revision.py、collect_gifs.py。
- Docs/EnemyDirectionReview/Remaining_20261024/local_baseline.json、production_fingerprints_before.json。
- Docs/EnemyDirectionReview/Batch01_10/user_approval_20261023.json。
- Docs/EnemyDirectionReview/AllGIF/manifest.json。
- 当前角色的 anatomy_plan.json、reference、generation、art_selection.json、layout_adjustments.json、安装清单、返修记录及已有运行证据。

按需要读取共享实现及直接依赖：Assets/Scripts/Enemy/BaseEnemy.cs、EnemyDirectionalVisual.cs、EnemyDirectionalProfile.cs、MonsterAnimEventReceiver.cs，以及 Assets/Editor/EnemyDirectionalRigBuilder.cs、EnemyDirectionPrefabBuilder.cs、EnemyDirectionBatchReview.cs、EnemyDirectionRemainingCatalog.cs、EnemyDirectionRemainingMotion.cs。

先检查 git status、当前差异及相关调用关系，建立本轮增量基线和指纹。同步是读取现场，不是从远端拉取。不得 git pull、reset、clean、checkout 覆盖用户改动；不得重置既有进度、历史基线或指纹来消除冲突。

特别注意：目前 E:/MyTowerGame/AGENTS.md 的项目标题和路径仍写着 FreedomTower_1 / D:/FreedomTower_1。记录这项规则文件差异，遵循本任务明确指定的 E:/MyTowerGame 和用户提供的 MyTowerGame 路由要求；不能因此转到 D:/FreedomTower_1，也不要未经任务需要改写 AGENTS.md。

## 3. 已知进度快照与剩余队列

2026-10-26 读取到的快照：

- Enemy 目录共 119 个 prefab。
- 相对 Git HEAD 55cdec16 有 67 个 prefab 未提交修改，均为已有文件修改，已暂存 0 个。
- 78 个 prefab 已序列化绑定方向 Profile：AdvancedHen + 首批 10 个 + 续作 67 个。
- 续作 completed_count=67，authorized_count=108，尚未完成 41 个。
- progress.current=PossessedWarg；该角色状态为 reference_prepared。
- PirateBoar 尚未完成安装，progress 为 staged_pending_visual_check，并保存了历史阻断记录及更新的返修材料。
- 其余 39 个角色为 not_started。
- AllGIF/manifest.json 记录 1005 个 GIF，包含历史、返修和不同版本，不能等同当前完成或用户批准数量。
- 已完成 67 项保存的最终运行记录各为 168 PASS / 0 FAIL；这是历史结果，不代表本轮重新执行。

剩余 41 个角色完整清单如下，名称大小写及原有拼写必须保持：

1. PirateBoar
2. PossessedWarg
3. PossessedWatchdog
4. PossessedWolf
5. Pug
6. Punisher
7. PurpleScarab
8. Ram
9. Rat
10. RatKing
11. RedScorpion
12. Rooster
13. RoyalBoar
14. SabretoothTiger
15. Scarab
16. ScarabMounted
17. ShardLizard
18. Sheep
19. SlugQueen
20. Swine
21. Tiger
22. TreasureChest
23. Troll
24. Turkey
25. VolcanoParasite
26. Warg
27. Wasp
28. Watchdog
29. WhiteWolf
30. WildGoat
31. WildRooster
32. WinterBear
33. WinterBoar
34. WinterOgre
35. WinterWarg
36. WinterWolfTypeA
37. WinterWolfTypeB
38. Wolf
39. WolfHound
40. WolfMounfed
41. Zombie

不要将 WolfMounfed 擅自改名为 WolfMounted；按当前角色登记找到实际资源。执行时若进度已有推进，跳过具有有效完成证据的项目，并报告快照差异，不退回本文的旧数量。

## 4. 当前应如何继续

### 4.1 先恢复 PossessedWarg 的中断现场

不要直接重新运行 prepare 或两方向生成。当前已存在：

- PossessedWarg/anatomy_plan.json。
- PossessedWarg/reference/。
- PossessedWarg/generation/Up/prompt.txt、request.json、raw.png、result.json。
- PossessedWarg/generation/Down/prompt.txt、request.json；本次清点未见 raw.png 或 result.json。

正确处理顺序：

1. 读取 anatomy_plan、原始图集、源 prefab 的完整参考、上下 prompt 与 request/result，并确认源文件指纹。
2. 查看已经生成的 Up/raw.png，判断是否合格；不要重复发送 Up 请求。
3. 调查 Down 请求：核对请求时间、错误或 uncertain_result 记录、相关仍在运行的生成进程及可查询的服务结果。存在 request.json 不能直接解释为“没有收费”或“可以重试”。
4. 如果原请求仍在执行，等待并观察结果，不并发发起相同请求；如果已有返回结果，恢复使用已有输出。
5. 如果已确定失败，保存失败记录和原请求，以新的、未使用 revision 编写恢复说明和提示词，再执行必要的新请求。不要删除 request.json 绕过防重保护。
6. 若服务不提供查询方式且无法确认请求结果，明确记录不确定性；在恢复条件清楚之前不盲目重复付费请求。可继续不依赖该结果的参考整理或其他安全工作，但不能伪报该角色完成。
7. 注意 generate.mjs 的 revision 分支会引用该方向的旧 generation/方向/raw.png。Down 原图缺失时，先检查这项前提；不能直接调用一个必定失败的 revision，也不能复制 Up 图充作 Down。必要时仅补充有明确失败记录、全新输出路径和指纹保护的恢复入口，保留原有防重机制。
8. 两方向原图及分件均通过视觉检查后，再 stage、安装、运行、审阅和 record。

角色身份以原始资源为准；当前解剖计划描述为深橄榄色四足狼兽、琥珀眼、金色背刺、蓬松长尾和四个爪足。背面不画脸，足部方向和尾根连接要正确，不照搬 BlackWolf 的具体造型。

### 4.2 优先补齐 PirateBoar，不退回旧 revision

完成当前 PossessedWarg 的安全恢复后，优先回收 PirateBoar 的未完成项，再继续后续队列。也可在不占用 Unity、不改生产资源的前提下，先检查它的离线材料。

必须同时读取：

- PirateBoar/blocked_review.json。
- PirateBoar/art_selection.json。
- PirateBoar/layout_adjustments.json。
- PirateBoar/revision_04_processing.json。
- PirateBoar/generation/Up/revision_04/raw.png。
- PirateBoar/generation/Down/revision_04/raw.png。
- PirateBoar/offline_Up.png、offline_Down.png、offline_rig_proof.png。
- 原始图集、完整源参考、已有 revision_01 至 revision_03 的审阅与修正说明。

blocked_review.json 描述的是 revision_01 旧问题：帽子/耳环在头身重复、后向蹄仍画正面分趾、炮管错误并入头片。当前 art_selection 已选择上下 revision_04；revision_04 是保留旧结果的局部像素修补，仍标记 pending_visual_check。不能据旧阻断记录断言 revision_04 已失败，也不能因存在 revision_04 就断言已经通过。

先实际查看最新原图，核对头身装备分配、耳环唯一性、帽子和炮车结构、后足方向及角色原设，再确认离线图是否确实来自最新选图；必要时重建 Docs 下的暂存和离线图后审阅。不要重复运行 revision_04_retouch.py，它包含拒绝覆盖已有输出的保护。

原始资源没有 Tail sprite/renderer，当前 art_selection 将兼容尾部切片设为透明；保留该角色事实，不为满足模板凭空增加尾巴。

最新 revision 合格后沿用单角色安装流程。仍不合格则建立下一个未占用 revision，说明具体问题，保留此前版本；不要退回 revision_02，不覆盖旧请求或付费结果。只有真实安装、两轮运行及实际画面都通过，才能清除当前阻断并记为完成；清除的是当前状态，历史 blocked_review 仍保留。

### 4.3 后续调度不能只盲用 progress.current

record_review.py 会把 current 指向队列中第一个未完成项，因此已越过的 PirateBoar 可能重新成为 current。这是正常的历史未完成回流，不要因此重复 prepare、生成或安装已完成角色。

每次记录后重新读取 items，结合角色实际材料和阻断记录选取下一项：先恢复已开始角色，补齐 PirateBoar，然后按 index 处理其余未完成项。若某项存在真实阻断，记录原因、恢复动作及当前调度决定；可安全推进独立角色时继续推进，不静默跳过，也不把它从 108 项里删掉。

## 5. 单角色操作流程与已核对的入口

以下命令从 E:/MyTowerGame 执行。命令要分阶段运行，每个视觉检查点实际查看材料后再继续，不能整段无条件连跑。

初始化本轮变量和实时检查：

    Set-Location -LiteralPath 'E:/MyTowerGame'
    $env:PYTHONUTF8 = '1'
    $OutputEncoding = [System.Text.UTF8Encoding]::new()
    $taskPython = 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    $taskRun = 'Docs/EnemyDirectionReview/Remaining_20261024'
    $taskStep = Join-Path $taskRun 'character_step.py'
    $taskProgressPath = Join-Path $taskRun 'progress.json'
    $taskProgress = Get-Content -LiteralPath $taskProgressPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $taskProgress | Select-Object status, authorized_count, completed_count, current, updated_at
    $taskProgress.items | Where-Object { $_.status -notin @('completed_pending_user_art_review', 'user_approved') } | Select-Object index, name, status

$taskName 必须从实时未完成队列中明确选定，且已检查该角色实际阶段。恢复当前角色时可设置：

    $taskName = 'PossessedWarg'

仅对确实未准备过的角色执行准备，不对已有材料角色无条件重跑：

    & $taskPython -X utf8 $taskStep prepare $taskName

检查源参考、解剖计划和方向 prompt。仅当该方向没有已存在、仍在运行或结果不明的请求，并且确实需要新生成时，执行相应方向：

    & (Join-Path $taskRun 'generate_character.ps1') -Character $taskName -Direction Up
    & (Join-Path $taskRun 'generate_character.ps1') -Character $taskName -Direction Down

上面两条是首次生成入口，不能直接用于当前 PossessedWarg。返修的 -Revision 参数必须使用检查过的新目录及对应 prompt，并满足生成器的输入前提。

两方向原图审阅通过后暂存，检查实际透明度、切片、布局和离线四方向图：

    & $taskPython -X utf8 $taskStep stage $taskName

确认生产指纹没有漂移、Unity 身份与使用状态正确、原 prefab 尚未安装本轮方案，再执行：

    & $taskPython -X utf8 $taskStep install-and-review $taskName

该入口会安装当前角色、运行两轮真实检查并生成范围审计。若 installed_manifest.json 已存在，不删除它绕过保护；从对应返修路径恢复，并使用新的运行 revision。范围审计失败要区分本轮修改、其他已存在改动和编辑器自动副作用，不擅自扩大允许列表。

运行后查看最终 four_directions.png、runtime_visual_strip.png、真实帧及 GIF；发现问题先修复。将真实观察以 UTF-8 写到当前角色的 record_note_utf8.txt，再读取文件传入 record，避免长中文命令行损坏：

    $taskNotePath = Join-Path (Join-Path $taskRun $taskName) 'record_note_utf8.txt'
    & $taskPython -X utf8 -c 'from pathlib import Path; import subprocess,sys; base=Path(sys.argv[1]); name=sys.argv[2]; note=Path(sys.argv[3]).read_text(encoding="utf-8-sig").strip(); assert note, "Review note is empty"; subprocess.run([sys.executable, str(base/"character_step.py"), "record", name, note], check=True)' $taskRun $taskName $taskNotePath

record 前必须确认 runtime_summary.json 指向本次最终安装版本，passes=168、failures=0，且已完成真实媒体审阅。脚本只检查这些数值并不能代替人工视觉判断；不得复制旧 summary、expected 文案或其他角色备注冒充。

## 6. 美术与动画硬性要求

1. 颜色、描边、材质、比例、表情、装备和角色身份以当前原始图集及完整源 prefab 为准。原始图集可能只有分件，不能凭单张侧图猜器官。
2. Up 为背向屏幕上方移动的背面；Down 为面向屏幕下方移动的正面。不能用侧图旋转、拉伸或镜像伪造正背图；左右沿用原有侧图及镜像规则。
3. 按自身解剖安排肢体数量、关节、足尖、尾根、武器和遮挡。不得有背面脸、反向脚趾、漂浮肢体、断开的颈部、重复装备、复制出的头或原角色没有的器官。
4. 行走有角色专属步态及连续循环；四足、六足、鸟类、飞行、漂浮、无足爬行、宝箱分别处理。头、身体和附肢允许错相，但根部固定连接，转向不能重播相位或抖动。
5. 攻击要有合理蓄力和发力，死亡要保持部件连接并完成淡出/收缩；不能只调速度充当动画返修。
6. 保留原侧面 float/PPtr 曲线、事件、时长和 loop 契约；沿用实际 Controller 的 Idle/Ready/Walk/Run/Attack/Death、State、Speed、Attack 和兼容 Action。头部正常/愤怒/死亡事件必须匹配方向。
7. Left、Right、Up、Down 及攻击、受击、死亡、对象池复用后均无角色地面阴影。仅处理当前角色战斗呈现中的阴影，保留原共享资源；新增图像不能画入地面阴影。
8. 检查真实透明背景、去底色污染、边缘、孔洞、切片边界、Pivot、PPU、导入设置和渲染顺序。不能用颜色掩码误删深色器官后仍声称合格。
9. 保持受击闪白、致死闪白结束、死亡淡出及对象池同实例复用；不要新增逐帧材质实例、重复组件、额外每帧层级查找或第二套方向系统。
10. 保持 prefab 根节点及 GUID、原 Sprite GUID/ID、逻辑路径、碰撞器、HP、血条、锚点、移动及战斗参数，不用本美术任务改业务或数值。
11. 使用已有单角色 Builder 与专用 Directions 资源；不得全目录重建、批量删除阴影或修改共享动画牵连其他角色。发现确需共享 C# 修复时，先查依赖、最小修改，再完成正确工程编译及受影响回归。

## 7. 已有成果与历史经验保护

不要重生成或覆盖 AdvancedHen、首批已批准 10 个角色，以及当前已完成的 67 个续作角色。必须改共享代码并影响它们时，先保留现场基线，只做必要兼容修复与相关回归。

首批已批准角色为 Bat、BattlePanther、Bear、BearMounted、BlackBear、BlackBoar、BlackWolf、BlueScorpion、Boar、BoarMounted。以 user_approval_20261023.json 为批准来源；旧冻结记录的“待审核”不推翻后续批准。

BlueScorpion 最终尾巴为 rear_reference_r02_centered_hook：尾根固定、静态角 20°、背面高拱弯钩适度靠近中线；TailOut 的被否决记录继续有效。此经验不能自动套用 PurpleScarab、RedScorpion 或其他角色。

已完成角色的返修经验仅供排错：MeatBug 的原侧面头部引用有过修复，MimicChest 有头部事件兼容问题，Monkey 使用 SeparateViewRigs 独立正背结构。先读当前接收器及控制器，不因旧 Wing/Leg 槽位为空就擅自补错引用，也不能把某次旧失败说成当前仍失败。

## 8. Unity 工程身份、占用与验证

2026-10-28 用户已将MyTowerGame端口调整为8088并现场核对成功；8082当前属于D:/FishTestGame，不得误操作。此当前路由优先于根规则和历史章节中的旧端口。

当前目标仅为 E:/MyTowerGame；版本以 ProjectSettings/ProjectVersion.txt 为准，快照是 Unity 2022.3.62f3c1。使用 unityMCP / http://127.0.0.1:8088/mcp；不能使用 CatchFish_Android 的 unity / 8080。

首次连接、重连、域重载或切换实例后：

1. 用 server=unityMCP 读取完整 URI mcpforunity://custom-tools 与 mcpforunity://instances。
2. 从现场列表选 MyTowerGame 的完整 Name@hash，调用 set_active_instance；不硬编码历史实例。
3. 读取 mcpforunity://project/info，确认 data.projectRoot 规范化后为 E:/MyTowerGame，且 data.unityVersion 与版本文件一致。
4. 读取 mcpforunity://editor/state。操作运行时问题时先读取该工程错误日志，再检查状态、复现和修改。

桌面 MCP 握手有问题而 8088 服务在线时，可先审阅并复用已有 Remaining_20261024/mcp_call.py；其动态实例检查必须保持。服务离线时按当前 AGENTS 的恢复流程复用并启动/连接已有 HTTP Local 服务，不能依赖离线 MCP 自启，也不能抢端口或杀共享进程。

每次安装、编译或进入 Play 前检查是否有其他验证、录像、手动模拟、未保存场景或并行任务占用。已有任务曾授权交回 Unity，不代表当前其他任务也已交回；不得以无响应或时间经过代替交接，不强停别人 Play、不覆盖场景。

本任务自己的逐角色 Play 已有授权，确认现场可用后沿用原测试器，无需逐角色重新询问。等待测试器安全结束并交回原场景。

C# 修改完成后按工程规则：

- 先完成同批改动，再调用 refresh_unity(mode="force", scope="all", compile="request", wait_for_ready=true)。
- 每 1～2 秒检查 editor/state，直到 is_compiling=false、is_domain_reload_pending=false、is_updating=false、ready_for_tools=true；编译期间不继续写代码。
- read_console(action="get", types=["error"], count="50", format="json")，必要时按实际分页并用 filter_text="error CS" 定位。
- execute_code 可用时探测 return UnityEditor.EditorUtility.scriptCompilationFailed;，应为 false。
- 短暂断线先等约 5 秒、重新选实例并核对身份；不能把超时或断线当成功，不清空日志掩盖旧错误。

MCP 无法自主恢复时，记录具体失败环节并明确提示：打开 E:/MyTowerGame 的匹配 Unity 版本，在 MCP 窗口启动/连接 HTTP Local 8088，并在 Codex 启用或重连 unityMCP；当前角色的编辑器验证必须标未完成。

## 9. 每个角色的真实验收标准

1. 安装前检查当前角色生产 prefab、meta、源 prefab、原图集及目标 Directions 的指纹。发现并行漂移先查明，不能覆盖或重置基线。
2. Builder/Verify 检查通过；无 Missing、断引用、错切片或缺失部件；保留非美术组件语义。依赖及现 YooAsset/AssetBundle 收集覆盖需实际检查，不将其说成已构建发布包回读。
3. 每个角色两轮真实 Play：普通死亡轮和指定 Up 死亡轮，每轮 84 项，共 168 PASS / 0 FAIL。首次通常为 runtime_r01 与 runtime_updeath_r01；返修使用未占用的新 revision，保留失败轮。
4. 覆盖四方向移动、真实行走相位、连续转向、纯纵向出生/路径变化、斜向主轴与滞回、近零位移方向保持、原生状态和头部事件、受击及致死闪白、全身死亡淡出/收缩、自动回收和同实例再生、跨真实帧暂停恢复、1x/2x/3x 速度，以及适用的飞行行为。
5. 保留实际 Unity 帧号、原始 PNG、normalizedTime、检查日志、revision、SHA256；不能用手动 Animator.Update、离线拼图或合成姿态冒充实际 Play 帧。
6. 查看最终四方向图及动态 strip，并播放上下行走、连续转向、攻击/受击/死亡/复用、暂停倍速 GIF。若工具无法播放，按帧序实际检查足够的原始帧并明确记录查看方式及限制，不能谎称已播放或已审完整段。
7. 视觉问题即使程序 PASS 也要修复后重测。没有看过的画面不写结论；visual_note 必须是实际观察，不能使用预期文案。
8. 旧版本 runtime 检查通过不能替代新安装版本。确认 runtime_summary 与生产版本、指纹及最终 revision 一致后才 record。

## 10. Image API、编码与资源边界

- 生成或编辑图片时遵循当前可用的 imagegen 技能和项目已授权的 AIHub 方式，优先复用经核对的 generate_character.ps1 / generate.mjs。模型和参数沿用当前有效流程，快照为 gpt-image-2、quality=medium、n=1、size=1536x1024；不擅自增加候选数量或付费重试。
- 服务为 https://aihub.dog/v1，密钥仅发送到 https://aihub.dog，不随跨域重定向转发。运行时从已配置环境或 C:/Users/Administrator/.codex/secrets/aihub-image-key.clixml 解密读取，结束清理；不得打印、写入仓库、请求记录、文档或交付物。
- 已有 request、raw、result、uncertain_result、仍在执行的进程或 revision 时，先检查结果再决定后续；不能绕过输出存在保护，不能自动重发超时请求。按鉴权、余额/配额、上游、网络和结果不确定分类记录失败。
- 保存真实返回的格式和尺寸，不假定与请求一致。局部修补记录父版本、范围、方法和哈希；不得借修补修改角色身份或假造 AI 返回。
- 中文说明、进度和审阅文件统一 UTF-8。已有乱码不凭猜测“修复”为通过；保留原文，必要时基于重新查看的证据追加新记录。
- 不修改 Luban/Config/Datas/Levels/L01..L30/**、EnemyData.xlsx、__tables__.xlsx；不直接写 Assets/ConfigJson/** 或 Assets/Gen/**，不恢复被删除的批量写表事务层。
- 维持无声版本，不恢复声音表、声音生成入口或声音系统。

## 11. 进度、GIF 和历史证据归档

每完成一个阶段，更新该角色实际状态和可恢复记录；必要时更新 current，但不能重置 completed_count、覆盖他人新进度或删除已完成项。进度状态至少区分未开始、参考准备、暂存待审、运行后待视觉审阅、实现完成待用户美术审阅、用户批准和阻断；沿用现有 schema，不随意发明不兼容字段。

record_review.py 会读取已有 runtime_summary 并写入完成状态，然后调用 collect_gifs.py。必须确认它没有引用旧 summary，写入后的中文内容和计数未损坏。

所有 GIF 保留原件，集中复制到 Docs/EnemyDirectionReview/AllGIF/，入口 index.html、清单 manifest.json。保留历史、返修和被否决版本；命名包含来源角色/路径/版本，记录 SHA256，发生同名不同内容时不覆盖。当前是否已批准须与有效批准记录一致。

每个角色保存参考、解剖计划、prompt/request/result、原始返回、revision 选择、透明处理/切片/布局、离线审阅、安装前后指纹、Verify、两轮原始帧及日志、媒体、实际视觉备注和失败记录。新增媒体未通过 record 流程时，也要主动归档：

    & $taskPython -X utf8 (Join-Path $taskRun 'collect_gifs.py')

后续数量从 manifest 实时读取，不写死“每个角色必增加 12 个”或沿用 1005。不要为修订此 prompt 修改冻结的批准、失败和历史进度证据。

## 12. 持续执行和最终交付

立即开工顺序：读取现场及基线 → 核对 Unity 身份和占用 → 恢复 PossessedWarg 已存在的 Up 和 Down 请求状态 → 审阅并恢复 PirateBoar 最新 revision_04 → 逐项完成其余未完成队列。每一角色均遵守前述视觉与真实运行关卡，不用批量循环无条件跳过检查。

持续处理至全部 108 个续作角色达到有效完成状态，或出现无法自主解决的真实阻断。图片、布局、动画或兼容性问题优先自行排查修复；不要仅因需要返修、旧记录有 blocked 或待用户美术验收就把整批任务交回。

阻断时明确记录角色、阶段、最新 revision、错误/不确定结果、已完成部分、Unity 状态、指纹及下一步；只暂停受影响操作。能够继续的独立工作继续推进。不得将未安装、未运行、视觉未审或失败项记为完成。

最终交付：

1. 实时总进度、108 项逐角色状态、新完成名单、未完成或阻断名单；不混淆目录 119 个与续作 108 个。
2. 可浏览的 AllGIF/index.html 和真实清单数量，逐角色四方向图、最终动作 GIF、revision 和证据来源。
3. 每个新完成项的两轮检查结果、实际视觉备注和哈希；明确历史结果、本轮结果、未执行检查及查看限制。
4. 本轮修改文件和范围审计、生产语义保护、编译/错误日志、依赖收集结果及必要的共享代码回归说明。
5. 更新 Docs/EnemyDirectionReview/README.md 的当前入口与进度说明，保留 PREFAB_CHANGES_SUMMARY_20261026.md 原快照，需要新的汇总时新增带日期/时间的版本。
6. 保持所有新完成角色为待用户美术验收，汇报可供用户审核的结果；不替用户批准，也不声称未执行的发布包、设备或长期战斗测试已通过。

开始执行，不要仅回复“可以继续”或再次交付一份计划。先给出简短现场进度更新，并完成第一个正确且可复核的角色恢复动作。
