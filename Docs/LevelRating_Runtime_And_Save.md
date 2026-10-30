# 五星评分、计时与存档实现

> **2026-10-30 口径变更（先读这条）**：局内的塔阵 / 金币 / 生命**不再落盘**，
> "退出后继续"与"失败续局"两条链路已整体删除。本文下方描述局内快照的段落
> （尤其"局内快照采用完整波次检查点…"这一整段）属于**历史记录**，不再是当前实现。
> 当前实现：只有通关（`SaveManager.RecordClear`）写星级 / 最快用时 / 最佳剩余生命；
> 进关永远从第一波、满血、初始金币开始。详见 `Docs/SavePolicy_2026-10-30.md`。

`LevelRatingEvaluator.Evaluate(profile, metrics)` 是唯一评分入口。五档条件从高到低判定；完整波数、成功出生数、击杀与漏怪守恒、逐波统计、正数战斗用时、有效标记及完整版本键均先通过完整性检查。失败和调试预览为 0 星，且不会调用正式写档。首领集合与精英/首领集合来自 LevelRating，而不是通过扣血量或所有 Type=3 推断。

本局开始冻结 `LevelRatingProfile`，配置仅允许在退出活动关卡后重载。正式成绩版本键为 `profileId|balanceRevision|ratingRevision|planHash`，profileRevision 进入生成器的 planHash。配置加载还校验 `runtimeContentHash`：八张实际导出 JSON 原文（统一 LF，移除 BOM）与评级字段的 SHA256。任何实际配置与认证摘要不一致都会拒绝开局。此校验覆盖实际数据，不依赖说明文字。

`GameClock` 的 Tick 与 DeltaTime 共用帧幂等入口。双精度秒累加器保留小数；毫秒只在读取或结算时统一换算。整局时钟从点击第一波开始，波间等待计入；战斗时钟从每波第一只成功出生开始，到该波计划敌人全部结算停止，波间准备不计入。两者均消费同一模拟 dt，暂停和后台冻结，离线时间不加入。首次出生受到同屏上限暂缓时不会提前启动战斗计时。

WaveManager 仅在成功出生后推进游标。同屏上限暂缓保留当前待刷项并退出本帧循环；资源、配置或路径错误会终止本局正式评级。GameFlow 在出生时登记实例，在 EnemyKilled/EnemyReachedEnd 回调中于回收前采集配置身份并一次性结算。清场判定使用这份即时未结算账本，覆盖 CombatSystem 本帧计算存活数后刚出生的末只敌人，避免缓存为零时提前清场。出生与结算数不完整时先终止评级，不发放回合奖励。漏怪回调不读取尚未更新的最终 HP。正式清场发奖、最终写档和弹窗共享一次性结果，重复事件不增加通关次数。

局内快照采用完整波次检查点。开波前保存本次准备的金币、生命和塔；半波退出后，所有半波消费、收入、进度、漏怪与时钟一起回到该检查点。清场后保存下一个波游标及完整统计，含 runId、冻结评分配置和双精度时钟。快照同时保存整局时钟是否已经启动、自动开下一波的剩余等待，以及每座塔的开火冷却、索敌计时、减速光环脉冲、后坐力、朝向和炮管姿态；重建塔后恢复这些相位，避免继续游戏改变后续输出与毫秒门槛。恢复验证统计守恒、逐波序号、版本、塔槽唯一性、有限且非负的计时和有效塔相位；任何塔恢复失败会作废整个快照并重开本关。最终游标允许等于波数，恢复后直接做一次性结算，不重打末波。已提交 runId 在进度中留存，避免重复写入。

SQLite schema 由 2 增量升至 3，关卡进度及快照新增受保护 rating_payload 列；旧密文字段先由 C# 解密，再写入新归档。快照受保护 payload 与主表、塔表处于同一事务。最终通关使用 `ISaveStorage.CommitClear` 在同一事务内更新成绩并清除快照。JSON 格式由 1 显式升至 2，升级前保留 `.legacy-v1.bak`，不再因版本不同返回空档。JSON 最终通关与快照失效通过同一文件原子替换提交，另留 `.previous.bak`。

写入失败不会发布 JSON candidate 或修改后端读回结果；KV 归档备份同样仅在原子替换成功后发布。SaveManager 的 TrySetSnapshot/TryClearSnapshot 在后端保存、Flush、当次错误检查与完整回读匹配后才发布内存快照；普通写入及旧的 void 包装也遵守这一顺序。写入或清除失败保留内存原检查点，重玩、重开和跨关清除失败会中止操作并提示重试。SQLite 的 BEGIN IMMEDIATE、写入、COMMIT 和事务处置均在 CommitClear 的异常边界内；另一连接持有写锁时返回 false 及当次错误，不让异常绕过待保存结果的建立。原生 COMMIT 失败会尝试回滚并向调用者报告失败，内部事务回滚会使外层事务只能回滚。正式结算失败保留终局检查点，显示“重试保存”，暂不显示新纪录或允许进入下一关；重试使用原始同一 runId，成功后才发布成绩。未来 JSON 格式被当前客户端按只读处理，避免较旧客户端覆盖新版本档案。

内容变更时先持久化原成绩备份，再归档旧版本原星数、生命、用时及证据，重置本版评定，最后写迁移标记。归档通过版本键去重，重复迁移不会增加 clearCount。旧通关次数及旧成绩继续支持已获解锁；TotalStars 只累计本版 0—5 星。本版最快战斗用时和整局最快用时独立记录，最高星证据对应同一个 runId，不拼接不同局的数据。

编辑器测试入口：进入 Play 前设置 `UnityEditor.SessionState.SetString("FT.Balance.TestStorageContext", "唯一测试名称")`，让管理器初始化即使用 `persistentDataPath/BalanceTests/<context>/` 的独立 SQLite/JSON；退出后清除该 SessionState。已运行的测试可使用 `SaveManager.Instance.SetTestStorageContext(...)` 的 IDisposable 作用域切换并恢复。工作台候选通过 `Configs.LoadTestCandidate(directory)` 加载，要求独立测试存储与无活动关卡。固定步长 PlayMode 回放可用 `GameClock.BeginManualSimulation()`、`StepManualFrame(dt)` 和 `GameFlowManager.StepManualSimulation()`；这条路径仍使用真实波次、敌人、塔、寻路和唯一评分器，报告应明确其与普通实时帧实测的区别。半波回退的开波检查点发生在原帧 Combat 阶段之后，恢复验证通过真实 Next 请求完成原帧剩余 Flow 阶段，不额外插入一次时钟或 Combat 步进；波边界继续直接使用快照剩余自动等待，不通过反射补时。

EditMode 测试位于 `Assets/Tests/BalanceRating/`，覆盖评级输入完整性、版本失效、旧成绩归档幂等、双时钟、帧幂等、存储升级、损坏快照拒绝、塔相位恢复与写入故障后的检查点保留。测试 fixture 只说明接口及数据完整性要求。

回归 `SqliteBusyBeginRetainsTerminalCheckpointAndRetriesSameClear` 使用第二个原生 SQLite 连接占写锁，要求结算返回 false、旧成绩和终局检查点保持；释放后用同一 runId 重试，避免重复通关。

`TimeScalePauseAndResumeCannotAccrueOrCatchUpEitherTimer` 检查暂停时两种计时均冻结，恢复后只累计当前步长。

`BalanceRuntimeSafetyVerifier.Run(outputPath)` 用于隔离存储中的资源失败、容量暂缓、无效波次、解锁规则和结算重试故障测试。`UseProductionUnlockRulesForTest()` 只用于编辑器测试真实解锁分支，不进入玩家构建。

资源故障注入需要穿过实际加载器路径，结束后恢复资源登记、句柄、定位地址与对象池引用；同步场景开始时应重算存活缓存，避免前一夹具状态影响后续测试。

安全验证器中的终局统计是故障测试 fixture，只验证输入拒绝、存档原子性与 UI 门禁。
