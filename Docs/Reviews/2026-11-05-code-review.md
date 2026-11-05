# 自由人塔防：工程代码审查报告

审查日期：2026-11-05（Asia/Shanghai）  
目标工程：`E:/MyTowerGame`  
代码基线：Git `b56ed757` 加本次审查开始时的工作区内容  
Unity：`2022.3.62f3c1`；MCP 插件：`com.coplaydev.unity-mcp v10.3.0`  
审查方式：静态代码、调用链、配置及资产引用交叉核查，辅以目标编辑器的只读状态和 Console 查询。

## 1. 审查结论

**建议先修复严重问题，再安排版本验收。** 本轮形成 **37 项问题或改进建议：致命 0 项、严重 8 项、一般 24 项、建议 5 项**。其中正常游戏流程即可触发的主要风险集中在续局快照、累计计时、失败结算和界面输入；异常路径风险集中在存档后端切换、失败反馈、资源所有权与发布任务取消。S08 及 G21～G24 是辅助工具风险，只有调用相应入口或特定参数时才触发，不应理解为当前 Player 已发生的故障。

“未发现致命问题”只表示本轮未取得足以判定致命等级的证据，不表示工程不存在崩溃风险。所有缺陷均有当前代码证据；文中复现步骤为后续验收用例，**本轮没有执行游戏复现、自动化测试、APK 构建或设备性能测试**。

### 1.1 分级标准

| 等级 | 本报告采用的标准 | 处理建议 |
|---|---|---|
| 致命 | 有确定证据表明常规核心路径无法启动、普遍崩溃，或发生不可恢复的大范围数据破坏 | 阻断交付 |
| 严重 | 核心状态或持久化数据错误、玩家进度丢失/收益重复，或发布控制和代码信任边界失效 | 优先修复并专项回归 |
| 一般 | 条件性功能错误、边界处理缺失、性能和可恢复性缺陷 | 纳入近期修复 |
| 建议 | 低影响表现问题、潜伏 API 缺陷、维护及扩展风险 | 安排治理，避免继续扩散 |

### 1.2 范围与证据边界

- 盘点了 `Assets/Scripts` 的 134 个、`Assets/AOTAssembly` 的 17 个、`Assets/Editor` 的 68 个和 `Assets/Tests` 的 5 个 C# 文件。按启动、玩法、存档、配置、UI、音频、资源、构建发布分层审查；关键问题均追踪至实际调用方、状态写入及恢复入口。
- UI、本地化、相机共 41 个文件；战斗、棋盘、寻路、波次及相关数据视图约 32 个文件；数据后端全部 12 个脚本及管理器、快照模型均进行了针对性细读。启动、资源、音频和构建发布重点检查生命周期、失败路径和并发。上述数字存在模块交叉，不能相加为去重覆盖量。
- 68 个编辑器文件进行了目录及危险操作检索；构建、热更、Luban 导出和相关 prefab 构建链重点细读。另盘点 `.workbuddy/tools` 和 `Luban` 下 118 个 `.py/.bat/.ps1`，重点抽查数值 pipeline、地图导出、历史改表入口和本地热更服务。历史美术制作器、批量资产修复器及其它辅助脚本以风险抽查为主。第三方库、Luban 生成类及历史证据副本不作逐行质量背书；只在核实项目调用契约时查看相关实现。
- 审查包含现有未提交的 `TowerActionMenu.cs`、`TowerBuildMenu.cs`；没有覆盖、回滚或修改它们。已有 `Artifacts/L02_ZeroLeak_20261104_134025` 改动也予以保留。
- UI 结论来自代码、输入链和相关资产配置，不等于已经完成各屏幕尺寸、触摸设备、字体、人工听感或视觉验收。
- 问题链接指向本轮审查时的文件和单个起始行；后续代码变动可能使行号移动。每项同时给出方法名，便于重新定位。

### 1.3 编辑器现场

用户现场确认端口为 8086，并提供 MCP 窗口截图。本轮通过 `unityMCP` 读取 custom-tools、instances，明确选中现场返回的 `MyTowerGame@9e28c50b510eeb91`，再由 project/info 确认 `projectRoot=E:/MyTowerGame`、Unity `2022.3.62f3c1`、目标 Android。

只读查询结果：当前场景 `Assets/Scenes/Boot.unity`，未处于 Play Mode；`is_compiling=false`、`is_domain_reload_pending=false`、`is_updating=false`、`ready_for_tools=true`；Console 的 error 查询返回 0 条。该结果仅代表查询时的编辑器现场，**不能证明下列业务缺陷不存在，也不等于完成了重新编译或运行验收**。

`execute_code` 的只读 `scriptCompilationFailed` 补充探针被工具权限限制拒绝，返回 `MCP tool call requires approval, but approval policy is never`，因此未取得该补充值。没有绕过限制或改用其它工程。此次交付仅增加审查文档及按项目规范记录连接线索，未修改参与编译的代码，未请求强制刷新编译。

## 2. 问题清单汇总

| 编号 | 等级 | 类别 | 问题 | 主位置 |
|---|---|---|---|---|
| S01 | 严重 | 数据/状态 | 波中卖塔保存即时收益，却以波首重新续玩 | [GameFlowManager.cs:1427](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:1427) |
| S02 | 严重 | 数据/计时 | 波次快照未更新累计时间，续局丢失已耗时 | [GameFlowManager.cs:704](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:704) |
| S03 | 严重 | 异常处理 | 清档失败被吞掉，内存与 UI 仍报告成功 | [SaveManager.cs:256](E:/MyTowerGame/Assets/Scripts/Core/Manager/SaveManager.cs:256) |
| S04 | 严重 | 数据兼容 | SQLite 与 JSON 回退后端形成分叉存档 | [SaveStorageFactory.cs:68](E:/MyTowerGame/Assets/Scripts/Data/Persistence/SaveStorageFactory.cs:68) |
| S05 | 严重 | 逻辑/状态 | 失败结算后仍移动、攻击并修改数据 | [CombatSystem.cs:248](E:/MyTowerGame/Assets/Scripts/Core/Combat/CombatSystem.cs:248) |
| S06 | 严重 | 发布/并发 | 取消热更未取消后台上传，仍可能激活版本 | [HotUpdatePipeline.cs:475](E:/MyTowerGame/Assets/Editor/HotUpdate/HotUpdatePipeline.cs:475) |
| S07 | 严重 | 运行时/信任 | HTTP/UDP 选址加自报 MD5，缺少热更代码来源认证 | [BootReleaseStore.cs:129](E:/MyTowerGame/Assets/AOTAssembly/BootReleaseStore.cs:129) |
| S08 | 严重 | 工具/数据 | 历史批量入口仍可改 L02～L30，并将小数金币截整 | [_manual_scale_levels.py:129](E:/MyTowerGame/.workbuddy/tools/_manual_scale_levels.py:129) |
| G01 | 一般 | 异常处理 | 阵型落盘失败仍返回成功 | [LevelLayout.cs:529](E:/MyTowerGame/Assets/Scripts/Data/LevelLayout.cs:529) |
| G02 | 一般 | 数据兼容 | 高版本 SQLite 的“只读兼容”没有真正限制写入 | [SaveSchema.cs:166](E:/MyTowerGame/Assets/Scripts/Data/Persistence/SaveSchema.cs:166) |
| G03 | 一般 | 配置/边界 | 缺失波次组仅告警，实际缩减出怪仍可通关 | [Configs.cs:253](E:/MyTowerGame/Assets/Scripts/Data/Configs.cs:253) |
| G04 | 一般 | 数据恢复 | JSON 损坏不读已有备份，后续还可能覆盖恢复点 | [JsonSaveStorage.cs:140](E:/MyTowerGame/Assets/Scripts/Data/Persistence/JsonSaveStorage.cs:140) |
| G05 | 一般 | 异常/音频 | JSON 成功写入不清 LastError，音频设置持续误重试 | [JsonSaveStorage.cs:168](E:/MyTowerGame/Assets/Scripts/Data/Persistence/JsonSaveStorage.cs:168) |
| G06 | 一般 | 寻路/边界 | 建塔只查 S→E，已有怪被封支路后仍可能穿塔 | [BaseTower.cs:982](E:/MyTowerGame/Assets/Scripts/Tower/BaseTower.cs:982) |
| G07 | 一般 | 容量/同步 | 同帧批量出生读取旧计数，突破同屏上限 | [EnemyManager.cs:83](E:/MyTowerGame/Assets/Scripts/Enemy/EnemyManager.cs:83) |
| G08 | 一般 | 索敌/逻辑 | 改道后路径进度基准不一，最危险优先失真 | [BaseEnemy.cs:62](E:/MyTowerGame/Assets/Scripts/Enemy/BaseEnemy.cs:62) |
| G09 | 一般 | 移动/性能 | 换路径点丢步长，实际移动速度依赖帧率 | [BaseEnemy.cs:474](E:/MyTowerGame/Assets/Scripts/Enemy/BaseEnemy.cs:474) |
| G10 | 一般 | 数据/性能 | 出生延期计数写入临时克隆，统计丢失并产生分配 | [WaveManager.cs:186](E:/MyTowerGame/Assets/Scripts/Round/WaveManager.cs:186) |
| G11 | 一般 | 性能 | 空间哈希反复丢弃、重建桶列表 | [EnemyGrid.cs:60](E:/MyTowerGame/Assets/Scripts/Core/Combat/EnemyGrid.cs:60) |
| G12 | 一般 | UI/输入 | 加载遮罩缺 GraphicRaycaster，点击可穿透 | [LevelLoadingMask.cs:84](E:/MyTowerGame/Assets/Scripts/UI/LevelLoadingMask.cs:84) |
| G13 | 一般 | UI/同步 | 清档成功后主菜单统计不刷新 | [MainMenuView.cs:94](E:/MyTowerGame/Assets/Scripts/UI/MainMenuView.cs:94) |
| G14 | 一般 | UI/输入 | 右键长按启动拖拽，右键释放无法结束 | [TowerDragButton.cs:34](E:/MyTowerGame/Assets/Scripts/UI/TowerDragButton.cs:34) |
| G15 | 一般 | 相机/交互 | 震屏中缩放重复扣除偏移，取景中心漂移 | [CameraController.cs:419](E:/MyTowerGame/Assets/Scripts/Camera/CameraController.cs:419) |
| G16 | 一般 | 资源/维护 | 关卡预载包引用只增不减，旧关资源持续保留 | [YooAssetResLoader.cs:1278](E:/MyTowerGame/Assets/Scripts/Core/Res/YooAssetResLoader.cs:1278) |
| G17 | 一般 | 资源/并发 | 预载与同步加载同名资源，句柄覆盖造成泄漏 | [YooAssetResLoader.cs:1333](E:/MyTowerGame/Assets/Scripts/Core/Res/YooAssetResLoader.cs:1333) |
| G18 | 一般 | 启动/边界 | 探测仅认非空 HTTP 200，错误候选可挤掉有效服务器 | [BootLoader.cs:175](E:/MyTowerGame/Assets/AOTAssembly/BootLoader.cs:175) |
| G19 | 一般 | 编辑器/时序 | Luban 导出先查 AssetDatabase 后刷新，首次导出可能误失败 | [LubanExporter.cs:184](E:/MyTowerGame/Assets/Editor/LubanExporter.cs:184) |
| G20 | 一般 | 构建/并发 | 构建流水线互斥只有单向检查 | [BuildApk.cs:203](E:/MyTowerGame/Assets/Editor/BuildApk.cs:203) |
| G21 | 一般 | 工具/边界 | 输出目录校验晚于写入，拒绝后仍可能污染受保护目录 | [balance_pipeline.py:1163](E:/MyTowerGame/.workbuddy/tools/balance_pipeline.py:1163) |
| G22 | 一般 | 工具/维护 | 数值校验器仍要求已删除的评级表，现行合法布局误失败 | [balance_pipeline.py:1010](E:/MyTowerGame/.workbuddy/tools/balance_pipeline.py:1010) |
| G23 | 一般 | 工具/数据 | 旧同步工具直接改导出 JSON，源表缺失却正常跳过 | [sync_tower_prefabs.py:71](E:/MyTowerGame/.workbuddy/tools/sync_tower_prefabs.py:71) |
| G24 | 一般 | 工具/进程 | 停服脚本只凭端口和进程名强杀，且不支持启动时自定义端口 | [停止热更服务器.bat:10](E:/MyTowerGame/.workbuddy/tools/停止热更服务器.bat:10) |
| A01 | 建议 | 表现 | 无目标早退会冻结尚未完成的炮管后坐回位 | [BaseTower.cs:341](E:/MyTowerGame/Assets/Scripts/Tower/BaseTower.cs:341) |
| A02 | 建议 | 风格/维护 | 暂停、存档的历史注释与现行实现矛盾 | [GameFlowManager.cs:735](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:735) |
| A03 | 建议 | UI/扩展 | 两个径向菜单重复维护模态窗字符串清单 | [TowerActionMenu.cs:208](E:/MyTowerGame/Assets/Scripts/UI/TowerActionMenu.cs:208) |
| A04 | 建议 | 数据/扩展 | committedRunIds 永久增长，读取与存储成本递增 | [SaveManager.cs:446](E:/MyTowerGame/Assets/Scripts/Core/Manager/SaveManager.cs:446) |
| A05 | 建议 | 基础设施 | 暂无业务使用的定时器复用和清理逻辑存在潜伏错误 | [TimerManager.cs:159](E:/MyTowerGame/Assets/Scripts/Core/TimerManager.cs:159) |

## 3. 严重问题详解

### S01：波中卖塔使资源、统计与波次游标属于不同时间点

- **位置**：[GameFlowManager.OnTowerSold](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:1427)，关联 [SaveCurrentLevel](E:/MyTowerGame/Assets/Scripts/Data/LevelLayout.cs:319) 与 [RestoreSavedLevelState](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:432)。
- **触发条件**：当前波已击杀部分怪物、获得金币或发生漏怪后出售一座塔，再退出并重进同关。
- **成因与证据**：`OnTowerSold` 保存当前即时资源。战斗中只克隆 `_run` 并删掉末尾当前波明细，没有回滚累计 `successfulSpawned/killed/leaked`；保存的 `_roundCursor` 仍表示上一完成波。恢复资源后，未完成波从开头再次生成。
- **影响**：保留当前波已经赚到的金币，又能重打这些敌人再次获得金币；累计统计与逐波明细不一致。第一波游标为 0 时，即使不保存运行统计，保存即时资源仍可导致重复收益。漏怪后的 HP 也可能与重新生成的整波不一致。
- **修复建议**：统一捕获同一检查点的资源、塔阵、统计、游标。若仅支持波边界续局，波中售塔应按明确的检查点变更规则提交；若支持波中续局，需要完整保存剩余出生时间轴和实体状态。只删除当前波明细不能实现一致性。
- **验收用例**：完成第一波；第二波击杀部分敌人后卖塔、退出、重进；比较金币、HP、游标和累计/逐波出生击杀数，并再次击杀相同出生序列。修复后不能重复获得已经结算的收益。

### S02：每波快照缺少累计计时，正常续局会低估成绩

- **位置**：[FinishRound](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:704)，关联同文件 [EvaluateRun](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:835) 和 [恢复计时](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:446)。
- **触发条件**：完成任意非最后波，退出后按存档续局。
- **成因与证据**：`FinishRound` 只更新当前波明细的 `combatEndSeconds/levelEndSeconds`，随后保存 `_run`；运行累计字段 `combatElapsedSeconds/levelElapsedSeconds` 仅在最终 `EvaluateRun` 中更新。恢复时却用这两个尚未更新的累计字段调用 `GameClock.RestoreTimers`。
- **影响**：此前已耗费的关卡与战斗时间恢复为零或过期值，最终结算及 `bestTimeMs/bestCombatTimeMs` 偏小，最快成绩失去可信度。
- **修复建议**：将计时、资源和统计纳入统一的快照捕获方法，每个持久化入口调用同一方法，避免只有最终结算补齐字段。
- **验收用例**：记录第一波结束时计时并退出；续局后完成全关；对照保存的波明细结束时间、累计时间和最终最佳时间。续局前的时间必须保留。

### S03：清档失败被后端吞掉，上层仍清空内存并提示成功

- **位置**：[SaveManager.TryResetAll](E:/MyTowerGame/Assets/Scripts/Core/Manager/SaveManager.cs:256)，关联 [SQLite ResetAll](E:/MyTowerGame/Assets/Scripts/Data/Persistence/SqliteSaveStorage.cs:431)、[JSON ResetAll](E:/MyTowerGame/Assets/Scripts/Data/Persistence/JsonSaveStorage.cs:406) 和 [设置界面反馈](E:/MyTowerGame/Assets/Scripts/UI/SettingView.cs:196)。
- **触发条件**：数据库写锁、删除权限不足、文件只读或磁盘异常。
- **成因与证据**：两个后端的 `ResetAll()` 均捕获错误后正常返回；`TryResetAll()` 把“没有异常传播出来”当作成功，直接替换 `_data` 并返回 true。JSON 后端更是在删除文件前就清空后端内存。
- **影响**：界面提示已重置，当前内存也像新档，但磁盘仍存旧记录，重启后旧进度复活；部分失败时可能混合新旧数据。
- **修复建议**：重置接口返回明确提交结果；持久层成功后再替换内存和发通知。JSON 多文件清档须定义部分删除失败时的恢复策略。
- **验收用例**：在隔离存档上持有写锁或拒绝删除，再执行清档。应返回失败、保留一致的内存状态，并提供明确重试反馈；恢复权限后重试应真正清空。

### S04：SQLite 与 JSON 后端切换没有迁移/权威来源协议

- **位置**：[SaveStorageFactory.Create](E:/MyTowerGame/Assets/Scripts/Data/Persistence/SaveStorageFactory.cs:68)。
- **触发条件**：历史 JSON 存档升级到可用 SQLite；或某次 SQLite 无法打开而退到 JSON，之后 SQLite 又恢复。
- **成因与证据**：工厂一旦打开并初始化 SQLite 就直接返回，没有检查、导入 JSON 进度，也没有记录回退期间哪份数据为权威。SQLite 失败才会读取另一套 JSON 文件。
- **影响**：升级后表现为进度清零；回退期间的新通关、阵型、语言等在下一次 SQLite 恢复时“消失”，原 SQLite 旧数据重新出现。两份文件可能仍在，但游戏不可见，属于可见进度丢失。
- **修复建议**：实现有备份、幂等标记和冲突策略的一次性导入及后端恢复协议；临时回退也必须明确权威来源，不能简单按“哪个能打开”选择。
- **验收用例**：在隔离目录准备有进度的 JSON，启用 SQLite 后启动；再模拟 SQLite 失败→JSON 游玩→SQLite 恢复，确认进度不会倒退且不会重复合并通关次数。

### S05：结算只停出生和计时，没有冻结战斗模拟

- **位置**：[GameFlowManager.OnGameOver](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:804)、[InvalidateRun](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:883)、[CombatSystem.OnUpdate](E:/MyTowerGame/Assets/Scripts/Core/Combat/CombatSystem.cs:248)、[BaseEnemy.Die](E:/MyTowerGame/Assets/Scripts/Enemy/BaseEnemy.cs:800)。
- **触发条件**：生命归零时场上仍有多个敌人和可以攻击的塔；或出生失败触发异常中止。
- **成因与证据**：流程进入 `GameOver` 后只停止计时和 `_wave`；`CombatSystem` 不检查流程终态，继续 `TickEnemies/TickTowers`。[GameClock.StopLevelTimer](E:/MyTowerGame/Assets/Scripts/Core/GameClock.cs:157) 只停止累计计时，[RefreshFrame](E:/MyTowerGame/Assets/Scripts/Core/GameClock.cs:176) 仍生成模拟 dt。结算窗也不暂停模拟；敌人死亡仍会发金币、记击杀。异常中止的结束事件同步也不完整。
- **影响**：结算窗口显示先前构造的数据，背景实体、HUD 金币、击杀数和 `_run` 账本继续变化，产生互相矛盾的结果。普通失败后 `LoseHp` 有终态守卫，因此不能声称玩家 HP 和 TotalLeaked 仍变化；漏怪事件写入的运行账本与震屏则仍可变化。若中途出生失败触发 InvalidateRun 且场上仍有残敌，该入口未设置 PlayerData.IsGameOver，后续还可能扣血并再次触发失败事件；波末检查触发的作废通常已无残敌，不混同处理。
- **修复建议**：统一正常失败、胜利与异常中止的终态入口，冻结逻辑模拟和业务输入。需要继续播放的死亡/结算动画应单独更新，不依赖继续攻击或移动。
- **验收用例**：在多敌、多塔场景使生命归零，停留结算窗数秒；金币、击杀、漏怪和实体逻辑应保持终态。另覆盖资源出生失败的 HUD、声音和交互终态。

### S06：取消热更没有停止上传，取消后仍可能真正发布

- **位置**：[HotUpdatePipeline.Cancel](E:/MyTowerGame/Assets/Editor/HotUpdate/HotUpdatePipeline.cs:475)、[后台上传](E:/MyTowerGame/Assets/Editor/HotUpdate/HotUpdatePipeline.cs:796)、[Fail](E:/MyTowerGame/Assets/Editor/HotUpdate/HotUpdatePipeline.cs:1128)、[UploadAll](E:/MyTowerGame/Assets/Editor/HotUpdate/HotUpdateDeployer.cs:326)。
- **触发条件**：启用远端上传，在上传过程中点击取消；取消后立即启动另一轮发布。
- **成因与证据**：`Cancel` 仅进入 `Fail` 并清除 `_uploadTask` 引用，没有取消令牌、请求中止或等待退出。已经执行的 `Task.Run` 仍继续上传，循环最后仍会 PUT `release.json`；旧任务完成时还会写共享 `_uploadOk/_uploadError`。
- **影响**：用户认为取消的版本仍可能上线；旧任务和新任务可能并发激活不同版本、污染状态，使界面结论与远端实际版本不一致。
- **修复建议**：每轮任务持有独立 runId、结果对象及协作取消令牌；每个文件及最终激活前检查取消/所有权。取消中保持 busy，直到 worker 确认退出；已发出的激活请求还需处理结果不确定性。
- **验收用例**：仅用隔离上传端点与限速网络，在上传中取消，检查后续 PUT 和最终激活指针；再开启第二轮，确认没有旧任务继续写入。不得以正式远端作为此故障用例的环境。

### S07：热更完整性校验没有认证代码来源

- **位置**：[BootServerSelection.ParseBroadcast](E:/MyTowerGame/Assets/AOTAssembly/BootServerSelection.cs:235)、[BootReleaseStore.Valid](E:/MyTowerGame/Assets/AOTAssembly/BootReleaseStore.cs:54)、[SelectRemote](E:/MyTowerGame/Assets/AOTAssembly/BootReleaseStore.cs:129)、[下载校验来源](E:/MyTowerGame/Assets/AOTAssembly/HotUpdateDllDownloader.cs:121)、[Assembly.Load](E:/MyTowerGame/Assets/AOTAssembly/HotUpdateAssembler.cs:169)。
- **触发条件**：启用当前 Android 的 `FT_HOTUPDATE` 路径，并连接不可信局域网、遭遇 HTTP 内容篡改或伪造发现服务。这里报告的是可达的信任边界缺陷，未执行攻击复现。
- **成因与证据**：UDP 魔数不是身份认证，候选地址使用 HTTP；`release.json` 与 DLL 校验值来自同一未认证来源。`Valid` 校验格式、文件集合、API 与 `aotSignature` 相等，但签名字段实际是兼容性摘要，未做可信公钥的数字签名验证。攻击者同时更改 DLL 与自报 MD5 时，现有完整性检查不能区分合法发布者。
- **影响**：可将本应仅用于发现/下载的网络输入提升为客户端执行代码，或造成启动拒绝服务。MD5 换成另一种无密钥摘要也不能单独解决来源认证问题。
- **修复建议**：发布描述符及载荷哈希采用可信公钥验证的数字签名；正式包限制可信 HTTPS 来源，并将开放式 UDP 开发发现明确限制在开发环境。兼容性摘要继续用于 AOT 匹配，不能充当发布者身份。
- **验收用例**：在隔离环境分别验证合法签名、篡改 DLL、篡改摘要、未知签名者及伪造发现地址。后四者应在加载程序集前被拒绝，同时保留已验证本地版本的明确恢复路径。

### S08：历史跨关改表入口仍可执行，且不支持当前小数金币口径

- **位置**：[_manual_scale_levels.main](E:/MyTowerGame/.workbuddy/tools/_manual_scale_levels.py:115)、[reward 读取](E:/MyTowerGame/.workbuddy/tools/_manual_scale_levels.py:60)、[批量写回](E:/MyTowerGame/.workbuddy/tools/_manual_scale_levels.py:129)。
- **触发条件**：开发或数值维护人员误用该历史脚本。没有证据表明它在本轮被执行，本轮也没有运行它。
- **成因与证据**：入口只有 `--slope`，直接遍历 L02～L30，分别保存 EnemyData、EnemyList 和 RoundData；没有预览、明确关卡范围或提交门禁。读取 reward 强转 int，计算后又 `max(1, round(...))`。当前导出数据存在 0.1903、0.1522 等小数奖励，已不符合该假设；`kill_now` 为零时缩放计算还会除零。
- **影响**：误用可大范围改变受保护源表，将小数奖励截断并重新放大到至少 1，破坏现行经济；若处理到中途异常，已完成关卡不会自动回滚。它同时与当前禁止脚本批量改表、默认最小改动范围的规范冲突。严重等级针对可写入的维护入口，不代表常规游戏启动会调用它。
- **修复建议**：禁用或隔离这个历史写表入口，保留历史用途说明，并引导当前手工改表→标准 Luban 导出流程；不要为修复此问题恢复批量 apply/rollback。确需后续工具设计时，先另行确认授权与范围。
- **验收用例**：通过入口检查确认历史脚本无法改写正式源表；小数精度与零分母用隔离数据或纯计算用例覆盖。不得直接在 L01～L30 源表上执行旧脚本验证风险。

## 4. 一般问题详解

### G01：阵型写入错误无法传给调用方

- **位置**：[LevelLayoutStore.WriteBook](E:/MyTowerGame/Assets/Scripts/Data/LevelLayout.cs:529) → [SetUserValue](E:/MyTowerGame/Assets/Scripts/Core/Manager/SaveManager.cs:603) → [SQLite SetValue](E:/MyTowerGame/Assets/Scripts/Data/Persistence/SqliteSaveStorage.cs:401) / [JSON WriteKvFile](E:/MyTowerGame/Assets/Scripts/Data/Persistence/JsonSaveStorage.cs:228)。
- **条件与成因**：KV 写失败时后端只记错误；中间接口为 void，`WriteBook` 调用后直接返回 true。上层 catch 无法捕获已被后端处理的失败。
- **影响**：波次、阵型或售塔结果未落盘，调用方仍打印成功，不能触发补救或重试；退出后恢复旧记录。这与 S03 的“清档”是不同操作，但具有相同错误契约缺陷。
- **修复建议**：返回操作级提交结果或传播明确异常，只有实际提交后才能声称落盘。
- **验收用例**：隔离库加写锁，完成一波或售塔；失败时不得出现“已落盘”成功结论，解除锁后可重试。

### G02：高版本 SQLite “只读兼容”只有日志

- **位置**：[SaveSchema.Ensure](E:/MyTowerGame/Assets/Scripts/Data/Persistence/SaveSchema.cs:166)，关联 [写设置](E:/MyTowerGame/Assets/Scripts/Data/Persistence/SqliteSaveStorage.cs:124)、[WriteLevel](E:/MyTowerGame/Assets/Scripts/Data/Persistence/SqliteSaveStorage.cs:203)。
- **条件与成因**：检测到数据库版本高于客户端时只输出只读兼容提示，没有建立只读连接或禁止写入；旧代码仍执行 `INSERT OR REPLACE`。
- **影响**：客户端降级后可能把新版本增加的列重置为默认值/NULL，或触发新约束失败，破坏应保留的数据。是否命中取决于未来 schema 的扩展方式，当前保护本身没有实现。
- **修复建议**：把 schema 兼容状态传到连接和存储层，真实禁止高版本库写入，或阻止用旧客户端打开。
- **验收用例**：副本库提升版本并增加带数据的扩展列，旧客户端保存时必须明确拒绝且原记录逐字段保持。

### G03：缺失波次组不阻断启动，账本按缩减计划照常通过

- **位置**：[Configs 加载结果](E:/MyTowerGame/Assets/Scripts/Data/Configs.cs:253)、[交叉引用检查](E:/MyTowerGame/Assets/Scripts/Data/Configs.cs:385)、[告警策略](E:/MyTowerGame/Assets/Scripts/Data/Configs.cs:452)，关联 [开波计划量](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:571) 与 [时间轴构造](E:/MyTowerGame/Assets/Scripts/Round/WaveManager.cs:100)。
- **条件与成因**：RoundData 引用了不存在或空的波次组。配置先置 `IsLoaded=true`，交叉引用错误仅告警；计划量和实际时间轴又同时跳过缺组，后续二者数量相等也不能发现“本应存在的组”。
- **影响**：少打怪甚至空波仍可能领取回合奖励、记录通关。此问题限定为缺组/空组；缺少单个 enemy 的出生失败有单独中止逻辑，不能混为一谈。
- **修复建议**：将必要引用缺失列为阻断性错误，影响 `ok/IsLoaded`；开波也校验完整计划，不能静默缩减。
- **验收用例**：仅在独立候选配置中构造无效组引用，应明确拒绝启动该关/波，不发奖励。源表仍应手工维护并经 Luban 导出。

### G04：JSON 主档损坏时不尝试已有恢复备份

- **位置**：[主档读取失败](E:/MyTowerGame/Assets/Scripts/Data/Persistence/JsonSaveStorage.cs:140)、[备份写入](E:/MyTowerGame/Assets/Scripts/Data/Persistence/JsonSaveStorage.cs:178)、[KV 读取失败](E:/MyTowerGame/Assets/Scripts/Data/Persistence/JsonSaveStorage.cs:220)、[KV 替换](E:/MyTowerGame/Assets/Scripts/Data/Persistence/JsonSaveStorage.cs:235)。
- **条件与成因**：主 JSON/KV 被截断、无法解密或解析失败。写入维护了 `.previous.bak`，读取却直接返回新档/空册，没有校验备份或隔离损坏文件。
- **影响**：原可恢复进度被当作全新档；继续操作后，下一次替换可能把损坏主档写进 `.previous.bak`，覆盖上一有效恢复点。
- **修复建议**：主档→已校验备份恢复；损坏文件另存，恢复确认前不得覆盖最后有效备份。
- **验收用例**：准备有效备份并损坏副本主档，启动应恢复备份；之后保存仍保留可用恢复链。

### G05：JSON 错误状态在成功后不复位，音频保存持续重试

- **位置**：[WriteSaveFile](E:/MyTowerGame/Assets/Scripts/Data/Persistence/JsonSaveStorage.cs:168)、[WriteKvFile](E:/MyTowerGame/Assets/Scripts/Data/Persistence/JsonSaveStorage.cs:228)、[SaveAudioSettings](E:/MyTowerGame/Assets/Scripts/Core/Manager/SaveManager.cs:560)、[FlushSettings](E:/MyTowerGame/Assets/Scripts/Audio/AudioRuntime.cs:575)。
- **条件与成因**：JSON 后端发生一次暂时写入错误，之后磁盘恢复。失败写 `LastError`，成功路径不清除；音频保存以该共享历史值判断本次是否成功。
- **影响**：实际已保存仍返回 false，`_settingsDirty` 保持，每 5 秒继续序列化、加密和刷盘，带来误报及额外 IO。
- **修复建议**：返回独立操作结果；成功提交清除对应错误，不能用历史 `LastError` 代替本次结果。
- **验收用例**：一次写失败后恢复权限，后续成功应清错误及 dirty 标记，不再周期性重写。

### G06：建塔可封闭场上怪物支路，失败改道保留旧路径

- **位置**：[TryBuildInternal](E:/MyTowerGame/Assets/Scripts/Tower/BaseTower.cs:982)、[改道分发](E:/MyTowerGame/Assets/Scripts/Core/Combat/CombatSystem.cs:162)、[BaseEnemy.RefreshPath](E:/MyTowerGame/Assets/Scripts/Enemy/BaseEnemy.cs:741)、[MoveAlongPath](E:/MyTowerGame/Assets/Scripts/Enemy/BaseEnemy.cs:474)。
- **条件与成因**：怪已进入某支路，随后建塔封住其出口，但另一条出生点→终点路线仍存在。建造只校验 S→E；该怪重算为空时保留旧路线，移动又不检查后续点是否已成墙。
- **影响**：建造通过，已有怪继续按旧路线穿过封口塔，破坏寻路与碰撞表现的一致性。
- **修复建议**：临时置墙阶段校验受影响地面怪可达性，或建立明确不可达策略；应继续保留现有“怪脚下允许建塔”的业务规则。
- **验收用例**：使用存在旁路及支路的测试地图，在怪进入后封口，S→E 保持通畅；已有怪不得穿过新塔。

### G07：出生容量检查使用上一更新阶段的存活数

- **位置**：[EnemyManager.Spawn](E:/MyTowerGame/Assets/Scripts/Enemy/EnemyManager.cs:83)、[批量出生循环](E:/MyTowerGame/Assets/Scripts/Round/WaveManager.cs:171)、[存活数重算](E:/MyTowerGame/Assets/Scripts/Core/Combat/CombatSystem.cs:289)。
- **条件与成因**：临近容量上限且同帧有多个到期出生项。出生循环读取的 `AliveEnemyCount` 只在战斗更新重算，注册新怪不立即增加它。
- **影响**：例如上限 200、旧计数 199，同帧 4 次出生均可能通过，实际达到 203。当前全局配置确实包含上限 200。低帧率/密集出生时保护失效。
- **修复建议**：注册、死亡、回收维护即时存活数，或在出生批次预留名额，保持计数单一来源。
- **验收用例**：接近上限时制造跨多个出生间隔的长帧，实际已注册存活数始终不得超过上限。

### G08：“最危险优先”比较了不同路径起点的进度

- **位置**：[BaseEnemy.PathProgress](E:/MyTowerGame/Assets/Scripts/Enemy/BaseEnemy.cs:62)、[SetPath](E:/MyTowerGame/Assets/Scripts/Enemy/BaseEnemy.cs:627)、[RefreshPath](E:/MyTowerGame/Assets/Scripts/Enemy/BaseEnemy.cs:741)、[ScoreCandidate](E:/MyTowerGame/Assets/Scripts/Tower/BaseTower.cs:643)。
- **条件与成因**：只有一部分怪因建塔被改道。进度为当前路径索引除以当前路径长度；新路线从当前位置起算并重置索引，无法和仍使用完整原路线的怪比较。
- **影响**：已靠近终点的改道怪被当作低进度，塔可能转打更远目标，造成不合理漏怪。当前存在使用该目标模式的塔配置。
- **修复建议**：比较剩余路径世界距离或抵达时间，定义地面/飞行目标的可比口径；若有对空优先，保留现有优先层次。
- **验收用例**：两怪同在射程，仅让靠前者局部改道；下一次索敌应按实际危险程度选择，不能因路线重置而倒序。

### G09：移动截断剩余步长，并额外消耗换点空帧

- **位置**：[MoveAlongPath](E:/MyTowerGame/Assets/Scripts/Enemy/BaseEnemy.cs:474)，特别是索引变化早退和步长截断。
- **条件与成因**：走到路径拐点/格心，尤其低帧率或高倍速。一帧最多走到一个点，剩余位移丢弃；下一帧推进索引后又直接 return，不消费该帧 dt。
- **影响**：怪物有效速度随帧率和倍速改变，塔的攻击窗口及关卡难度也被改变。攻击周期已有补射，但移动没有等价补偿。
- **修复建议**：按距离预算循环消费路径段、保留剩余步长，并设置安全迭代上限处理重复点。
- **验收用例**：固定速度、路径和随机条件，在不同帧率以及 1×/3× 下比较模拟抵达时间。静态示例：格长 1、速度 1、dt=0.25，4 次移动后仍多一次换点空帧；这不是实测值。

### G10：延期计数改的是公开快照，真实统计没有更新

- **位置**：[WaveManager.Tick](E:/MyTowerGame/Assets/Scripts/Round/WaveManager.cs:186)、[RunMetrics getter](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:90)、[JSON Clone](E:/MyTowerGame/Assets/Scripts/Data/LevelRunMetrics.cs:46)。
- **条件与成因**：同屏容量满。`RunMetrics` 返回 JSON 深克隆，调用方只在克隆上 `spawnDeferredCount++`，未写回内部 `_run`。
- **影响**：存档/审计中的延期次数失真；容量持续满时每帧复制整局历史，额外产生序列化分配。
- **修复建议**：增加受控的内部统计接口，如 `NotifySpawnDeferred`；公开 getter 继续保留只读快照语义。
- **验收用例**：维持满容量数秒，比较真实运行记录和持久化延期次数，并测量此路径是否仍分配整局 JSON。

### G11：空间哈希桶没有复用，稳态移动仍产生列表分配

- **位置**：[EnemyGrid.Update](E:/MyTowerGame/Assets/Scripts/Core/Combat/EnemyGrid.cs:60)、[Remove](E:/MyTowerGame/Assets/Scripts/Core/Combat/EnemyGrid.cs:81)。
- **条件与成因**：最后一只怪离开某桶后移除整个字典条目；下次进入又 `new List<BaseEnemy>(8)`。
- **影响**：地图和数量已稳定时，分散怪跨桶仍不断分配，不能达到注释期望的更新阶段零分配。具体 GC 峰值和掉帧幅度尚无本轮 Profiler 数据。
- **修复建议**：有限棋盘中保留空桶，或使用列表池；避免无界保留任意坐标桶。
- **验收用例**：预热后持续跨桶移动，用 Profiler 检查该方法的 GC.Alloc；同时验证大地图/越界坐标不会使缓存无界增长。

### G12：独立加载 Canvas 缺少 UI 射线器

- **位置**：[LevelLoadingMask.Ensure](E:/MyTowerGame/Assets/Scripts/UI/LevelLoadingMask.cs:84)。
- **条件与成因**：新建的 Overlay Canvas 只有 CanvasScaler、背景 Image 和 CanvasGroup；虽然 Image 设置 `raycastTarget=true`，整个 Ensure 未添加 `GraphicRaycaster`。
- **影响**：遮罩显示或约 0.18 秒淡出时，底层已创建的 HUD 仍可能接受开始、倍速、建塔点击；视觉遮挡与交互阻挡不一致。
- **修复建议**：独立 Canvas 添加 GraphicRaycaster；键盘和棋盘原生输入需要流程层明确的加载输入门禁，不能仅靠 UI 射线。
- **验收用例**：在切关淡出期间连续点击新 HUD 各按钮区域，遮罩隐藏前不得触发业务事件。

### G13：成功清档没有通知仍激活的主菜单

- **位置**：[MainMenuView.Subscribe](E:/MyTowerGame/Assets/Scripts/UI/MainMenuView.cs:94)、[RefreshStats](E:/MyTowerGame/Assets/Scripts/UI/MainMenuView.cs:123)、[SettingView.ResetRoutine](E:/MyTowerGame/Assets/Scripts/UI/SettingView.cs:196)、[设置打开/关闭流程](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:1344)。
- **条件与成因**：从主菜单打开设置并成功重置。主菜单仍激活，只监听语言变化；设置只刷新自身并发提示，没有进度变化事件。
- **影响**：关闭设置后累计星数、通关数仍为旧值，玩家无法判断清档是否成功；重新启用主菜单或切语言才刷新。
- **修复建议**：成功提交清档后发布明确的进度/存档变化通知，所有展示进度的界面订阅。
- **验收用例**：有通关记录时从主菜单清档，关闭设置后主菜单应立即显示清零，且与选关一致。此项与 S03 的磁盘失败反馈独立。

### G14：按键入口和拖拽结束条件不一致

- **位置**：[TowerDragButton.OnPointerDown/Up](E:/MyTowerGame/Assets/Scripts/UI/TowerDragButton.cs:34)、[HUD 长按判定](E:/MyTowerGame/Assets/Scripts/UI/HudView.cs:395)、[拖拽释放检测](E:/MyTowerGame/Assets/Scripts/Tower/TowerPlacement.cs:704)。
- **条件与成因**：鼠标右键在塔按钮按住超过长按阈值。中继忽略 `eventData.button`，任意键均启动手势；下游只用 `GetMouseButtonUp(0)` 结束拖拽。
- **影响**：右键释放后 ghost 继续跟随，建造态残留，随后操作可能非预期落子；需要再次取消。此为编辑器/鼠标输入缺陷，不能直接当作 Android 触摸已复现。
- **修复建议**：明确只接收主按键/触摸主指针，并传递 pointerId，让开始、移动、结束属于同一手势。
- **验收用例**：金币充足时右键长按、松开再移动，ghost 不应残留；同时覆盖触摸取消、拖出按钮及多指输入。

### G15：震屏和缩放对相机位置采用了冲突的偏移口径

- **位置**：[HandleZoom](E:/MyTowerGame/Assets/Scripts/Camera/CameraController.cs:419)、[LateUpdate](E:/MyTowerGame/Assets/Scripts/Camera/CameraController.cs:137)。
- **条件与成因**：漏怪震屏尚未结束时滚轮缩放。缩放先从 Transform 减去 `_shakeOffset`，但保留该字段；同帧 LateUpdate 再减一次。
- **影响**：抖动结束后真实取景中心发生偏移，连续操作可积累漂移；Clamp 可能掩盖部分情况。
- **修复建议**：独立保存不含震动的相机位置，最后叠加表现偏移；或剥离后同步清零偏移。
- **验收用例**：在允许平移的缩放范围，比较震屏中和非震屏中同样缩放操作后的棋盘中心位置。

### G16：关卡预载引用没有退出时的对应释放

- **位置**：[PreloadLevelResources](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:471)、[AcquireRef](E:/MyTowerGame/Assets/Scripts/Core/Res/YooAssetResLoader.cs:1278)、[TeardownLevel](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:1062)、[EnemyManager.ClearAll](E:/MyTowerGame/Assets/Scripts/Enemy/EnemyManager.cs:195)。
- **条件与成因**：正常反复切关、访问不同怪物家族。每次 Preload 为相关包增加引用，但业务层搜索不到 `ReleaseBundle` 调用；ClearAll 只把怪回池，池和非激活实例继续保留，预载句柄也保存在 `_handles`。
- **影响**：非 Persistent 的旧关怪物、塔及 HUD 资源仍被持有，内存随访问过的新资源集合和各 prefab 的实例高水位累积。同关反复进入主要增加引用整数，**不能据此声称每次都复制纹理、必定线性无限增长或已经 OOM**。
- **修复建议**：明确每关租约、共享常驻资源及池所有者；退出时取消该关未完成预载，清理不再使用的池实例，再成对释放包。仅调用卸载而保留池中依赖实例也不安全。
- **验收用例**：跨多种怪物家族切关，比较非持久包引用与内存持有；退出后应按既定缓存预算回落，公共资源不能被误卸载。

### G17：冷预载和同步恢复同名资源会遗失一个 YooAsset 句柄

- **位置**：[异步加载完成登记](E:/MyTowerGame/Assets/Scripts/Core/Res/YooAssetResLoader.cs:994)、[同步登记](E:/MyTowerGame/Assets/Scripts/Core/Res/YooAssetResLoader.cs:952)、[预载完成登记](E:/MyTowerGame/Assets/Scripts/Core/Res/YooAssetResLoader.cs:1333)。
- **条件与成因**：预载尚未完成时，同一逻辑名又被加载。实际调用链：InitLevel 先预载首项 `Tower_Normal0`，句柄 A 等待时未登记；同帧恢复已有塔阵，同步 Instantiate 创建并登记句柄 B；A 完成后直接覆盖 B，没有释放 B。
- **影响**：字典只剩一个句柄，另一个 provider 引用计数仍在；即便 provider 被共享，也不是 GC 可以自动修复的托管引用问题。包内 ProviderBase 的 CreateHandle/ReleaseHandle 已交叉核实其独立加减引用语义。
- **修复建议**：登记进行中的请求并去重，统一一个逻辑名的所有权；完成阶段不可无释放地覆盖已有句柄，并处理取消/晚到回调。
- **验收用例**：冷加载且有 Normal0 塔阵的存档进关，追踪创建/释放句柄数量；完成和退出后 provider 引用应与所有者数一致。本条是句柄覆盖泄漏，与 G16 的关卡租约缺失不同。

### G18：错误的 HTTP 200 候选可以阻止使用有效热更服务器

- **位置**：[ProbeCandidatesCo](E:/MyTowerGame/Assets/AOTAssembly/BootLoader.cs:175)、[候选胜出后处理](E:/MyTowerGame/Assets/AOTAssembly/BootLoader.cs:84)。
- **条件与成因**：存在多个发现候选，其中一个错误站点/不兼容版本更快返回非空 HTTP 200。探测不解析、校验 BootRelease，直接停止其它候选；后续 SelectRemote 才发现无效，但会退本地候选或等待重试，不再尝试已丢弃的有效候选。
- **影响**：明明有可用服务器，客户端却离线启动旧版或反复失败，定位困难。
- **修复建议**：以可解析且兼容的 release 描述符作为候选成功条件，或失败后继续其余候选。可达性探测仍须保持有界。
- **验收用例**：隔离环境提供“更快的非 release 200”和“稍慢的有效 release”两个候选，应选择后者，而非直接回退。

### G19：Luban 外部产物在导入前按 Unity 资产判缺失

- **位置**：[LubanExporter.ExportInternal](E:/MyTowerGame/Assets/Editor/LubanExporter.cs:184)，关联 [M0SetupWizard](E:/MyTowerGame/Assets/Editor/M0SetupWizard.cs:71)、[FT_FeatureBuild](E:/MyTowerGame/Assets/Editor/FT_FeatureBuild.cs:107)。
- **条件与成因**：首次导出、产物被清理或新增表尚未导入。外部进程完成后先 `AssetDatabase.LoadAssetAtPath` 检查；只有检查通过才 Refresh，失败会提前 return。
- **影响**：磁盘 JSON 已存在仍报产物缺失，搭建/功能构建流程中止；菜单 wrapper 之后刷新也不能改变已返回的失败结果。
- **修复建议**：先用 File.Exists 检查外部产物，再显式导入/刷新，之后做 TextAsset 和解析校验。
- **验收用例**：在隔离 checkout 准备尚未导入的新产物，核对磁盘文件与 ExportInternal 结果。不得删除正式工程产物来制造该场景。

### G20：完整构建与热更的互斥门禁不对称

- **位置**：[BuildApkFull.StartMenu](E:/MyTowerGame/Assets/Editor/BuildApk.cs:203)、[HotUpdatePipeline.CanStart](E:/MyTowerGame/Assets/Editor/HotUpdate/HotUpdatePipeline.cs:374)。
- **条件与成因**：先启动热更，在可交互等待/上传阶段反向启动完整构建。热更会检查 Full/Reporter 是否忙；完整构建只检查自己阶段和编辑器状态，没有检查热更任务。
- **影响**：两个 EditorApplication.update 状态机可以同时推进，在共享 HybridCLR 生成、StreamingAssets DLL/AOT 拷贝、编译和重载等阶段相互干扰，造成多余重构建、阶段中断或作业失败。影响取决于两者所处阶段。热更计划已从 Library/FTBootReleaseStage/{version} 的发布目录读取，而完整构建使用不同的 apk-baseline 目录；**没有证据证明完整构建会覆盖已冻结的上传载荷，不将其作为本条影响**。
- **修复建议**：所有入口使用同一个工程级构建互斥状态，并在编译/重载前后保持作业所有权。保留已有的载荷冻结和哈希核对机制。
- **验收用例**：隔离发布环境让热更停留上传阶段，再启动完整构建，必须明确拒绝；反向顺序也同样拒绝。

### G21：输出目录保护执行得太晚，报拒绝前后都可能已写入

- **位置**：[stage_export 保护](E:/MyTowerGame/.workbuddy/tools/balance_pipeline.py:963)、[前置报告写入](E:/MyTowerGame/.workbuddy/tools/balance_pipeline.py:1147)、[CLI 前置操作](E:/MyTowerGame/.workbuddy/tools/balance_pipeline.py:1163)、[finally 状态写入](E:/MyTowerGame/.workbuddy/tools/balance_pipeline.py:1183)。
- **条件与成因**：传入 `--out` 指向 Assets、Luban 或其它不允许的目录。只有 stage_export 内调用 `assert_safe_out`；在它之前，CLI 已 mkdir、删除旧 cli-exit，主流程还可写 resolved-plan、preview、report 和 selection。finally 仍会写退出状态。其它输出命令也未统一使用该保护。
- **影响**：即使 stage 最后拒绝，受保护目录仍可能被创建或混入非导出文件；“只写安全输出目录”的工具契约不成立。这里未声称这些报告会直接改写现有关卡表。
- **修复建议**：在任何 mkdir、unlink、日志和结果写入之前统一规范化并校验全部输出路径；拒绝路径不得在 finally 再写状态。覆盖 `--out` 两种参数形式和编辑器日志路径。
- **验收用例**：用临时模拟工程和文件操作拦截验证非法目录始终零写入，包括参数错误、stage 拒绝、异常和 finally；合法独立输出目录保持可用。

### G22：只读数值工具仍依赖已删除的评级体系

- **位置**：[LEVEL_TABLES](E:/MyTowerGame/.workbuddy/tools/balance_pipeline.py:45)、[verify_layout](E:/MyTowerGame/.workbuddy/tools/balance_pipeline.py:1005)、[旧评级重封流程](E:/MyTowerGame/.workbuddy/tools/balance_pipeline.py:971)。
- **条件与成因**：对当前合法关卡目录执行 verify-layout，或使用仍关联旧评级模型的生成/验证/stage。代码要求每关存在 LevelRating.xlsx，且预期文件集合遗漏现行逐关 TowerInfo、BulletData；现场目录已经没有 LevelRating，而有 30 张 TowerInfo 和 30 张 BulletData。stage 仍访问 tblevelrating 并计算 runtimeContentHash。
- **影响**：当前合法布局会被判缺表/文件集合不符，工具报告无法作为现行配置的可靠验收；后续维护人员可能被误导去恢复已废弃的评级表。生成与验证模型也存在同源过期风险。
- **修复建议**：按现行表登记同步只读模型、布局检查和输出，移除废弃评级/hash 假设；保留通关固定 5 星规则，不借此自动改任何源表或生成产物。
- **验收用例**：使用当前布局的隔离副本校验应通过结构检查；再删除一张真实必需表，应明确定位缺失。不得以创建评级表来“修复”校验失败。

### G23：塔资源同步工具先改导出物，再忽略缺失的旧源表

- **位置**：[目标路径](E:/MyTowerGame/.workbuddy/tools/sync_tower_prefabs.py:38)、[直接写 JSON](E:/MyTowerGame/.workbuddy/tools/sync_tower_prefabs.py:71)、[源表缺失处理](E:/MyTowerGame/.workbuddy/tools/sync_tower_prefabs.py:87)、[执行顺序](E:/MyTowerGame/.workbuddy/tools/sync_tower_prefabs.py:170)。
- **条件与成因**：带 `--apply` 且硬编码资源名映射与当前 JSON 存在差异。先直接覆盖 Assets/ConfigJson/tbtowerinfo.json，然后查找已不存在的共享 Datas/TowerInfo.xlsx；缺失只打印跳过，不能回滚前面的修改。当前源表已拆为 30 张逐关文件。
- **影响**：有差异时只改运行导出物，手工源表与 Player 数据分叉，下一次标准导出又丢失这次修改，并违反源表→Luban 导出的维护链。当前映射已匹配，不能声称此脚本本轮实际造成了漂移。
- **修复建议**：退役直接写生成 JSON 的 apply 路径；只保留只读差异提示，按项目规范手工维护对应源表并标准导出。
- **验收用例**：在隔离文件上制造映射差异，工具应只输出提示，缺源表时明确失败，不产生任何 JSON 或 xlsx 写入。

### G24：停服脚本缺少进程身份核对，可能误杀其它 Python 服务

- **位置**：[停止热更服务器.bat](E:/MyTowerGame/.workbuddy/tools/停止热更服务器.bat:10)，关联 [启动参数说明](E:/MyTowerGame/.workbuddy/tools/启动热更服务器.bat:11) 和 [HTTP 端口参数](E:/MyTowerGame/.workbuddy/tools/hotupdate_server.py:232)。
- **条件与成因**：8000 被其它 Python 服务监听，或本工程通过 `--http-port` 启动在其它端口。停止脚本只按监听端口 8000 和 python.exe 过滤，随后 taskkill /F，不检查脚本路径、项目根目录、命令行或本轮 PID。
- **影响**：可能强制结束无关服务及其未完成工作；真正的自定义端口热更服务却仍存活，界面提示也不能准确代表服务状态。
- **修复建议**：启动时记录经验证的项目根目录、PID、启动时间及参数；停止时再次核对进程身份，并先请求正常退出。端口参数由同一配置来源提供。
- **验收用例**：仅在隔离环境以无业务测试进程验证：无关服务占用 8000 不得被终止；本工程自定义端口实例应能被准确停止。不要用当前工作中的其它服务验证强杀行为。

## 5. 表现、风格与可维护性建议

### A01：炮管回位应与是否存在目标解耦

**位置**：[BaseTower.TickAttack](E:/MyTowerGame/Assets/Scripts/Tower/BaseTower.cs:341)。无目标 return 发生在 `TickRecoil(dt)` 之前，最后目标死亡/离开时，未结束的后坐可能停在缩回状态，直到下次找到目标。建议把纯视觉回位放在持续执行的视觉更新中；验收时在开火后立即移除最后目标，炮管仍应自然回位。

### A02：代码注释应描述现行契约

**位置**：[GameFlowManager:735](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:735)、[失败注释:815](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:815)、[暂停说明:1241](E:/MyTowerGame/Assets/Scripts/Game/GameFlowManager.cs:1241)，以及 PauseView、HudView 的相关说明。

当前实际实现包含每波落盘、续局恢复和打开暂停菜单时暂停；部分历史注释仍写“不落盘”“退出从第一波重来”“菜单不暂停”。这些矛盾已经足以误导维护和测试用例设计。建议将历史方案迁入变更文档，代码只保留现行规则、必要原因及约束。**本报告不把旧注释描述的行为当成当前事实，也不把既定的通关固定 5 星当作缺陷。**

### A03：模态状态查询不宜由两个菜单各自硬编码

**位置**：[TowerActionMenu.HasModal](E:/MyTowerGame/Assets/Scripts/UI/TowerActionMenu.cs:208)、[TowerBuildMenu.HasModal](E:/MyTowerGame/Assets/Scripts/UI/TowerBuildMenu.cs:503)。两处重复相同 7 个模态名，且 `"ConfirmView"` 仍是裸字符串。新增或改名弹窗时容易只更新一处，出现输入/显示不一致。建议由 UIManager 暴露统一模态状态或界面元数据，两菜单共享查询。验收应覆盖所有模态窗与两个径向菜单的组合。

### A04：通关幂等账本需要明确增长边界

**位置**：[SaveManager.RecordClear](E:/MyTowerGame/Assets/Scripts/Core/Manager/SaveManager.cs:446)、[序列化写入](E:/MyTowerGame/Assets/Scripts/Data/Persistence/SqliteSaveStorage.cs:206)。每次通关永久追加 runId，随后 Contains、整项深克隆和 JSON 保存的成本持续增长；这是长期重复游玩的扩展风险，不能据此声称当前存档已过大。建议在不破坏幂等语义的前提下，采用独立提交账本或有明确生命周期的去重方案。用大量重复通关的隔离存档测量体积和耗时。

### A05：重新使用旧定时器前，应修正潜伏的复用与清理错误

**位置**：[TimerManager.GetTimerItem](E:/MyTowerGame/Assets/Scripts/Core/TimerManager.cs:159)、[CheckTimerItem](E:/MyTowerGame/Assets/Scripts/Core/TimerManager.cs:195)。

复用 TimerItem 时没有重写 `callbackObject` 和 `isNotLimtied`：有限次数对象复用于 `loopTimes=-1` 时可能不执行，原无限对象复用于有限次数时仍可无限执行，目标对象也可能沿用旧值。清理循环从末尾开始却使用 `i++`，保留超过 5 项时存在越界，而不是正确倒序清理。

当前业务检索未发现实际 AddTimer 调用，Update 内的 CheckTimerItem 也被注释，因此列为潜伏 API 风险，**没有将其冒充当前游戏中已触发的定时器故障**。若继续保留，应在重新接入前完整复位所有复用字段、修正清理方向；否则明确弃用并减少维护入口。

## 6. 七个审查维度的归纳

| 用户要求的维度 | 本轮主要发现 | 评估 |
|---|---|---|
| 逻辑缺陷 | S01、S02、S05、G06、G08、G09 | 检查点、终态和路径度量存在具体不变量缺口 |
| 边界条件与异常处理 | S03、S04、G01～G05、G07、G18、G19 | 多层“记录错误但正常返回”使成功语义失真；异常/兼容用例不足 |
| 潜在运行时风险 | S07、G09～G11、G16、G17 | 网络代码信任、帧率相关移动、资源持有与 GC 需分别处理 |
| 规范与风格一致性 | S08、G21～G23、A02、A03、A05 | 写表/导出链与工具契约脱节，另有过期注释和重复状态定义；局部格式差异不是交付阻断项 |
| UI 界面与交互规范 | G12～G15、A01、A03 | 输入阻挡、手势配对、界面数据刷新和表现更新存在确定缺陷 |
| 数据交互与状态同步 | S01～S05、G01、G05、G07、G10、G13 | 多份状态缺少统一提交/通知边界，是主要系统性问题 |
| 可维护性与扩展性 | S06、S08、G16、G17、G20～G24、A02～A05 | 快照、资源租约、模态与构建任务应收敛为明确的单一所有者；历史维护工具应同步现行数据模型 |

代码中已有一些值得保留的机制：通关提交先由后端确认再更新内存；SQLite 操作大多使用参数绑定；音频入口和偏好集中管理；部分事件采用成对订阅/解绑；发布载荷具有不可变目录、字节校验和激活指针最后切换的设计。修复应沿这些机制收敛，避免建立第二套存档、暂停或音频入口。

`GameFlowManager` 约 1506 行、`BaseTower` 约 1369 行、`YooAssetResLoader` 约 1724 行、`UIPrefabBuilder` 约 3137 行，多个文件同时承担策略、生命周期和表现。文件长度本身没有作为独立缺陷计数，但上述具体问题说明应优先提取“快照捕获/提交”“终态控制”“资源租约”“发布作业”这些已有明确职责的边界，避免先做大规模格式化或无目标拆类。

## 7. 修复顺序与回归建议

### 7.1 建议分批

1. **先保护数据和发布控制**：S01～S04、S06，并隔离 S08 的历史写表入口，同步修复 G01/G05 的结果契约。为快照、清档、后端迁移定义可验证的提交结果。
2. **再收敛运行终态及信任边界**：S05、S07；同时覆盖 G03 的无效配置拒绝和 G18 的候选选择。
3. **修复战斗确定性与输入边界**：G06～G15。分别验证帧率/倍速、改道、容量和遮罩输入，避免以某一关一次通关替代回归。
4. **处理长会话资源及工具链**：G16/G17/G19～G24，之后治理 A01～A05。

每批只修改授权范围内的代码；涉及源表的修复继续按项目规则手工维护并标准导出，不能直接改生成 JSON。参与编译的 C# 修改完成后，必须按当次工程身份和端口完成 MCP 刷新、等待编译就绪及 Console 检查。

### 7.2 现有自动化覆盖的实际边界

本轮仅审读了以下 5 个测试文件，未执行；两个测试程序集均为 Editor-only。

| 测试文件 | 已有用例关注点 | 本轮缺陷中尚缺的关键回归 |
|---|---|---|
| [TowerCadenceTests.cs](E:/MyTowerGame/Assets/Tests/BalanceCombat/TowerCadenceTests.cs) | 攻击周期的帧率/倍速、长帧补射、暂停 | 敌人位移、整局抵达时间等价、失败终态 |
| [PlacementPathPreviewTests.cs](E:/MyTowerGame/Assets/Tests/BalanceCombat/PlacementPathPreviewTests.cs) | 主路径预览隔离、路径一致、堵主路回滚、剩余路径谓词 | 完整建塔链及已有怪被隔绝但 S→E 仍通 |
| [CombatTargetingAndSlowTests.cs](E:/MyTowerGame/Assets/Tests/BalanceCombat/CombatTargetingAndSlowTests.cs) | 地空过滤、减速、池化效果重置、对空优先等 | 改道后危险排序、出生容量和延期统计 |
| [AudioPreferencesPersistenceTests.cs](E:/MyTowerGame/Assets/Tests/BalanceRating/AudioPreferencesPersistenceTests.cs) | 音量归一化、JSON 兼容、SQLite 格式及失败回滚 | 波次快照、卖塔续局、JSON 错误恢复 |
| [SoundRemovalPersistenceTests.cs](E:/MyTowerGame/Assets/Tests/BalanceRating/SoundRemovalPersistenceTests.cs) | 历史音频字段兼容及 schema 迁移保留进度 | 当前后端切换、逐波恢复及资源生命周期 |

### 7.3 人工与设备验收清单

| 场景 | 最低应记录的证据 | 对应问题 |
|---|---|---|
| 波中卖塔→退出→续局 | 前后金币/HP、游标、累计和逐波账本 | S01 |
| 完成一波→退出→续局→通关 | 快照计时、最终计时、最佳成绩 | S02 |
| 文件/数据库失败与后端恢复 | 操作返回值、磁盘状态、重启后的进度 | S03、S04、G01、G04、G05 |
| 生命归零后停留结算窗 | 实体状态、金币和战绩不再变化 | S05 |
| 取消隔离发布并立即尝试新作业 | 作业 ID、worker 退出、服务端请求和激活指针 | S06、G20 |
| 长帧/不同帧率与倍速 | 实际出生上限、模拟抵达时间、索敌结果 | G07～G10 |
| 加载淡出与手势取消 | 业务事件、ghost 状态、pointer 配对 | G12、G14 |
| 刘海/不同宽高比/语言/触摸 | 界面截图、文本可读性、遮挡与点击范围 | UI 视觉覆盖边界；不冒充本轮已通过 |
| 多关卡长会话 | Profiler GC、资源句柄/包引用、池实例高水位 | G11、G16、G17 |

## 8. 交付说明

本报告提供定位、根因、影响、修复方向和可执行的验收场景，没有实施代码修复、源表修改、发布、清档或运行态操作。报告中所有“建议修复”“验收用例”都属于后续工作，不表示已修复或已验证通过。已有业务规则（固定 5 星、允许怪脚下建塔、标准 Luban 导出及多实体 MCP 身份核对）继续作为审查约束。
