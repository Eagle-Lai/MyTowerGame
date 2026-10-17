# 五星评分、计时与存档实现

`LevelRatingEvaluator.Evaluate(profile, metrics)` 是唯一评分入口。五档条件从高到低判定；完整波数、成功出生数、击杀与漏怪守恒、逐波统计、正数战斗用时、有效标记及完整版本键均先通过完整性检查。失败和调试预览为 0 星，且不会调用正式写档。首领集合与精英/首领集合来自 LevelRating，而不是通过扣血量或所有 Type=3 推断。

本局开始冻结 `LevelRatingProfile`，配置仅允许在退出活动关卡后重载。正式成绩版本键为 `profileId|balanceRevision|ratingRevision|planHash`，profileRevision 进入生成器的 planHash。配置加载还校验 `runtimeContentHash`：八张实际导出 JSON 原文（统一 LF，移除 BOM）与评级字段的 SHA256。任何实际配置与认证摘要不一致都会拒绝开局。此校验覆盖实际数据，不依赖说明文字。

`GameClock` 的 Tick 与 DeltaTime 共用帧幂等入口。双精度秒累加器保留小数；毫秒只在读取或结算时统一换算。整局时钟从点击第一波开始，波间等待计入；战斗时钟从每波第一只成功出生开始，到该波计划敌人全部结算停止，波间准备不计入。两者均消费同一模拟 dt，暂停和后台冻结，离线时间不加入。首次出生受到同屏上限暂缓时不会提前启动战斗计时。

WaveManager 仅在成功出生后推进游标。同屏上限暂缓保留当前待刷项并退出本帧循环；资源、配置或路径错误会终止本局正式评级。GameFlow 在出生时登记实例，在 EnemyKilled/EnemyReachedEnd 回调中于回收前采集配置身份并一次性结算。清场判定使用这份即时未结算账本，覆盖 CombatSystem 本帧计算存活数后刚出生的末只敌人，避免缓存为零时提前清场。出生与结算数不完整时先终止评级，不发放回合奖励。漏怪回调不读取尚未更新的最终 HP。正式清场发奖、最终写档和弹窗共享一次性结果，重复事件不增加通关次数。

局内快照采用完整波次检查点。开波前保存本次准备的金币、生命和塔；半波退出后，所有半波消费、收入、进度、漏怪与时钟一起回到该检查点。清场后保存下一个波游标及完整统计，含 runId、冻结评分配置和双精度时钟。快照同时保存整局时钟是否已经启动、自动开下一波的剩余等待，以及每座塔的开火冷却、索敌计时、减速光环脉冲、后坐力、朝向和炮管姿态；重建塔后恢复这些相位，避免继续游戏改变后续输出与毫秒门槛。恢复验证统计守恒、逐波序号、版本、塔槽唯一性、有限且非负的计时和有效塔相位；任何塔恢复失败会作废整个快照并重开本关。最终游标允许等于波数，恢复后直接做一次性结算，不重打末波。已提交 runId 在进度中留存，避免重复写入。

SQLite schema 由 2 增量升至 3，关卡进度及快照新增受保护 rating_payload 列；旧密文字段先由 C# 解密，再写入新归档。快照受保护 payload 与主表、塔表处于同一事务。最终通关使用 `ISaveStorage.CommitClear` 在同一事务内更新成绩并清除快照。JSON 格式由 1 显式升至 2，升级前保留 `.legacy-v1.bak`，不再因版本不同返回空档。JSON 最终通关与快照失效通过同一文件原子替换提交，另留 `.previous.bak`。

写入失败不会发布 JSON candidate 或修改后端读回结果；KV 归档备份同样仅在原子替换成功后发布。SaveManager 的 TrySetSnapshot/TryClearSnapshot 在后端保存、Flush、当次错误检查与完整回读匹配后才发布内存快照；普通写入及旧的 void 包装也遵守这一顺序。写入或清除失败保留内存原检查点，重玩、重开和跨关清除失败会中止操作并提示重试。SQLite 的 BEGIN IMMEDIATE、写入、COMMIT 和事务处置均在 CommitClear 的异常边界内；另一连接持有写锁时返回 false 及当次错误，不让异常绕过待保存结果的建立。原生 COMMIT 失败会尝试回滚并向调用者报告失败，内部事务回滚会使外层事务只能回滚。正式结算失败保留终局检查点，显示“重试保存”，暂不显示新纪录或允许进入下一关；重试使用原始同一 runId，成功后才发布成绩。未来 JSON 格式被当前客户端按只读处理，避免较旧客户端覆盖新版本档案。

内容变更时先持久化原成绩备份，再归档旧版本原星数、生命、用时及证据，重置本版评定，最后写迁移标记。归档通过版本键去重，重复迁移不会增加 clearCount。旧通关次数及旧成绩继续支持已获解锁；TotalStars 只累计本版 0—5 星。本版最快战斗用时和整局最快用时独立记录，最高星证据对应同一个 runId，不拼接不同局的数据。

编辑器测试入口：进入 Play 前设置 `UnityEditor.SessionState.SetString("FT.Balance.TestStorageContext", "唯一测试名称")`，让管理器初始化即使用 `persistentDataPath/BalanceTests/<context>/` 的独立 SQLite/JSON；退出后清除该 SessionState。已运行的测试可使用 `SaveManager.Instance.SetTestStorageContext(...)` 的 IDisposable 作用域切换并恢复。工作台候选通过 `Configs.LoadTestCandidate(directory)` 加载，要求独立测试存储与无活动关卡。固定步长 PlayMode 回放可用 `GameClock.BeginManualSimulation()`、`StepManualFrame(dt)` 和 `GameFlowManager.StepManualSimulation()`；这条路径仍使用真实波次、敌人、塔、寻路和唯一评分器，报告应明确其与普通实时帧实测的区别。半波回退的开波检查点发生在原帧 Combat 阶段之后，恢复验证通过真实 Next 请求完成原帧剩余 Flow 阶段，不额外插入一次时钟或 Combat 步进；波边界继续直接使用快照剩余自动等待，不通过反射补时。

必要 EditMode 测试位于 `Assets/Tests/BalanceRating/`，覆盖生命/毫秒边界、精英及首领上限、缺失/调试/版本无效证据、旧成绩归档幂等、双时钟与帧幂等、SQLite/JSON 4/5 星重启回读、计时小数反复存取、旧后端升级、完整终局游标及损坏快照拒绝。末只出生且战斗存活缓存为零的回归验证不得提前奖励或胜利；SQLite 只读连接与 JSON 临时路径被目录占用的实际故障验证快照写入/清除失败保持原边界、重启可读、解除故障后可重试。塔相位测试经过 30 次 JSON 往返，验证冷却/索敌/炮管恢复与非有限数据拒绝；时钟恢复测试覆盖 0.0625 秒小数边界、启动标记、暂停与后台冻结。2026-10-17 的统一 Unity MCP 编译成功，`scriptCompilationFailed=false`；EditMode 运行 54 项全通过，失败及跳过均为 0，原始结果见 [editmode-final-54.json](BalanceEvidence/editmode-final-54.json)。最新 HUD、怪物构建及安全夹具修改统一编译后再次运行，仍为 54/54 通过，见 [editmode-final-54-recheck.json](BalanceEvidence/editmode-final-54-recheck.json)。

最终正式数据应用后再次完成 EditMode 验证，54/54 通过、失败与跳过均为 0，见 [editmode-final-postapply-54.json](BalanceEvidence/editmode-final-postapply-54.json)。此报告与下述运行安全报告为分别执行的检查，不能将构造夹具混入玩法回放证据。

真实 Unity 固定步长检查点回放见 [unity-results.json](BalanceEvidence/PlayMode-checkpoints/unity-results.json) 与 [speed-comparison.json](BalanceEvidence/PlayMode-checkpoints/speed-comparison.json)。D04 第 1 关同一份余额驱动操作在 1×/2×/3×、波边界退出继续、实际半波消费后回退、终局重复事件共六局均为 5 星、350 只出生和击杀、零漏怪、余额 78，原始战斗时钟 379 秒、整局时钟 474.0625 秒完全相同。比较器仅规范化 runId，逐波统计、现金流、原始 double、塔布局及最终塔相位均严格一致；这组证据证明该回放的继续等价与倍速口径，不替代全部关卡或普通实时帧的平衡验证。

回归 `SqliteBusyBeginRetainsTerminalCheckpointAndRetriesSameClear` 使用第二个原生 SQLite 连接的真实写事务占锁，要求结算返回 false 而不抛出、旧成绩和终局检查点完整保留；释放写锁后用同一 runId 及证据重试，重启读回只观察到一次通关和原子清除的快照。该项已在上述 54 项统一运行中通过。

三档 `TimeScalePauseAndResumeCannotAccrueOrCatchUpEitherTimer` 直接设置 `Time.timeScale=0`，验证两种计时均冻结，恢复后只累计当前步长，不追赶暂停期间时间；三个档位均已在上述 54 项统一运行中通过。

独立 `BalanceRuntimeSafetyVerifier.Run(outputPath)` 已在隔离 main 场景 PlayMode 实际执行，八个场景全部通过，见 [runtime-safety.json](BalanceEvidence/runtime-safety.json)，顶层 `passed=true`、`resourceLoader=YooAssetResLoader`。通过场景覆盖实际同屏容量暂缓及首只成功出生计时、实际资源加载失败、F2 的 Win/GameOver 弹窗链、未完成波统计和跳到末波的拒绝、旧档迁移后的正常解锁及版本总星数隔离，以及 SQLite 只读连接和 JSON 临时文件受阻下的 CompleteVictory→待保存弹窗→Next 门禁→同一 runId 重试→重复回调及重开回读。只在独立存储作用域内使用 `UseProductionUnlockRulesForTest()` 绕过编辑器全解锁例外，从而运行真实玩家解锁分支；该接口不存在于玩家构建。

资源故障场景实际目标为 `Enemy_Chick`：临时移除目标对象池与 YooAsset 已缓存句柄入口，保留原句柄且不 Release，将定位缓存改为唯一不存在地址，穿过真实 YooAsset 加载路径。场景确认生成计数及战斗时间仍为 0、正式评级失效且无奖励，最后恢复原资源登记、句柄、定位地址和对象池引用；机器结果 `resourceStateRestored=true`。每个同步场景开始时通过真实 `TickEnemies(0)` 重算存活缓存，避免上一夹具的同屏上限缓存阻止本场景触及资源故障。实际加载失败、无效波次与两后端写入故障产生的 12 条 Warning/Error 全部保留，按场景、UTC 和 `expectedFault=true` 写入结果；底层 YooAsset 日志仅在含本次唯一故障地址时归为该预期注入。

安全验证器中的完整终局统计是明确构造的故障测试 fixture，只用于验证评分拒绝、存档原子性和 UI 门禁；八场景通过不认证实战通关、平衡校准或五星可达性。前两次夹具未能触发预期资源故障的 7/8 结果保留在 [runtime-safety-initial-failed.json](BalanceEvidence/runtime-safety-initial-failed.json) 与 [runtime-safety-second-failed.json](BalanceEvidence/runtime-safety-second-failed.json)；修正同帧存活缓存同步及实际加载器缓存注入后，以上最新报告才达到 8/8。
