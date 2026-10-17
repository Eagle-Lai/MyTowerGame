# 20×20 关卡数据、八档配方与证据

正式应用 D04「中等」，保留 20 个关卡 ID，每关 20 个独立 Round，每 Round 恰好一个 EnemyList。关卡等级、战役阶段 I—V、八档开发调参预设和本局 1—5 星分别存储。玩家没有新增八档选择流程。

权威输入为 `Luban/BalanceDesign/balance_design.json`；唯一公式与计划编译器为 `.workbuddy/tools/balance_pipeline.py`。原始资源和非管理字段的基线在 `baseline_data.json`，不会从已经应用的倍率结果反向生成，防止切档复利。工作台直接异步调用同一 CLI。

## 公式与经济

数量 N=L+w+6；L1 为 8—27、总 350；L20 为 27—46、总 730。基础 EHP 按 prompt 的数量、关卡 3% 成长、波次线性/二次项、5/10/15 压力倍率 1.12、20 波 1.25 生成，再依 L→w 顺序执行相邻波和相邻关同波号至少 4% 的预算包络。护甲用 HP=B×q/Q×(1−armor) 一次换算，没有重复护甲或 HP 倍率。

八档使用原始倍率：EHP 为 0.50/0.65/0.82/1/1.18/1.40/1.65/1.95；速度 0.90/0.94/0.97/1/1.02/1.04/1.06/1.08；间隔 1.10/1.07/1.04/1/0.98/0.95/0.92/0.89；金币 1.40/1.25/1.10/1/0.96/0.92/0.88/0.84。正数统一 floor(v+0.5)。每档均保留完整 400 波和相同首次机制登场。

初始金 100+18×(L−1)、生命 20；清场金每五波为 6/7/8/9，总 150。击杀奖励按角色固定，所有 reward≥1。初次布防无限等待；Round/EnemyList 开始延迟都为 0，清场后默认 5 秒。波内出怪间隔按公式由 900ms 递减，D04 范围 450—900ms。

|角色|q|速度|护甲|击杀金|漏怪伤害|Type|
|---|---:|---:|---:|---:|---:|---:|
|普通|1|1.10|0|2|1|1|
|虫群|0.65|1.05|0|1|1|1|
|快速|0.85|1.60|0|2|1|2|
|飞行|1.2|1.40|0|3|1|4|
|中型|2|1.00|0.08|3|1|1|
|重型|4|0.80|0.18|5|2|3|
|精英|7|0.75|0.22|8|2|3|
|首领|18|0.65|0.25|25|4|5|

普通/火力/减速各三级。攻击、CD、半径、增量价格、累计成本及 70% 出售价按 prompt 九行落实。减速伤害为 0；25%/35%/45% 光环单独显示。普通和减速可对空，火力只打地面。AOE 仍为 1.2 格；索敌节流 100ms；Global.sellRefundRate=1。

## 确定编组与资源

所有槽位在生成时确定，运行时没有随机补数。编组先落实飞行、压轴首领/精英、重型、快速、中型和虫群，再用已解锁普通单位填满；角色按固定轮转分散到出怪列车中。第 1 关飞行只数为第 7/8 波 1，第 9/10 波 2，第 11 波 0，第 12 波 1，第 13—15 波 2，第 16 波 0，第 17 波 2，第 18—20 波 3。第 20 波 Rat 精英替换一个护卫，总数仍为 27。第 12 关起压轴才进入首领池；132 新变体明确为首领。

全部 119 个战斗 prefab 已由 Unity 身体 Sprite bounds 实测，保留根变换并乘配置 scale=0.5，排除血条、阴影及效果祖先。`monster_measurements.json` 保留测量方法；各档 `monster_catalog_119.json` 合并尺寸、原型 ID、实际选用 ID、首次登场、角色与飞行身份。当前正式编组使用 22 个唯一资源；其余资源保留目录，不制造美术副本或独立对象池。

首领变体按对应身体最大边规范为 3.2/3.3/3.4/3.5 格；原型 1—132 不改，首领 BodyRadius=0.6，其他当前变体=0.4。移动仍是已有单格路径体系，没有新增多格碰撞。大体型转弯、血条遮挡及视觉检查需以 Unity 报告为准。

稳定变体键为 `profile|level|wave|canonicalId|role`，固定 D01—D08 的 profile 序号，ID 从 100000 分区分配，持久化于 `variant_manifest.json`。D04 当前 4054 个变体；正式 EnemyData 仅追加所选档所需变体，保留 132 个原型。Round/EnemyList 的稳定 ID 为 `(L−1)×20+w`，共 1—400。

混编可以降低同角色单只 HP，整波 ΣEHP 始终严格增长。报告 `validation.json` 的 `individualHpDropsOver10Percent` 明确列出大于 10% 的下降，主要发生在新重型加入的 10→11 波；没有宣称单只属性全部单调。

## 地图

第 1 关由 11×5 扩为 13×7；第 2—5 关保留开阔空间；第 6—10 关加入四格稀疏交错障碍；其它大部分保留既有地形。第 14/15 关原 S/E 直线只有两格，已将两端移动到左右边缘，保留中央障碍，避免飞行单位因极短射击窗口造成无解对空。

每张图均检查尺寸、合法字符、唯一 S/E 和四向 BFS。各档 `maps.json` 列空场最短路、障碍/禁建/可建格数、四座示例合法塔位、布塔后路径和半径 3 的覆盖格。该示例只证明合法性；策略报告的实时消费、完整操作轨迹才用于通关预测。

## 评分配置、Hash 与校准边界

新增 LevelRating.xlsx，登记于 __tables__.xlsx，Luban 自动生成 cfg.LevelRating/TBLevelRating，并导出 20 行 tblevelrating.json。完整评级键为 profileId|balanceRevision|ratingRevision|planHash；profileRevision 进入 hash。bossVariantIds 与 criticalVariantIds 从角色元数据生成，不用扣血量猜身份，不把普通重型误算精英。

Par0 使用各波最后出生跨度加阶段清尾预算后向上取整到 5 秒。D04 L1=440000ms，L20=825000ms。这是初始战斗时间门槛，排除开场、波间准备和暂停。校准状态最初为 `pending_unity_reference`；数学通过不认证五星可达，最终状态仅由下述同版本真实证据绑定。

planHash 是最终 profile、怪物实际数值/名单/间隔、地图、塔、经济及评级参数确定性 JSON 的 SHA256。runtimeContentHash 另验证实际八张战斗 JSON 原文与 20 行评分关键字段，换行统一 LF、排除 BOM。该摘要不循环包含自身，加载缺失或不符不得认证正式成绩。跨局版本迁移与时钟/评分/快照实现见 `LevelRating_Runtime_And_Save.md`。

校准状态由真实证据派生。配方的 `calibrationEvidence` 路径清单绑定 Unity 唯一 C# 评分器输出；编译器核对 profile、完整版本/hash、有效五星、20 波完整出生与击杀和非调试标记后，才将对应评分行、关卡报告和 20 条波次报告设为 `verified_unity_reference`。状态在 planHash 生成后回填，补充证据不会改变战斗内容的 hash；过期 hash、离线预测、不完整波和无效评分均保持待验证。证据文件本身纳入候选源 Hash 检查。

`balance_merge_evidence.py` 按相同 profile/关卡/planHash 合并离线与真实逐波结果，生成 JSON/CSV/完整可读 Markdown、覆盖索引、五星参考和较低星对照。真实参考的实际操作另导出为独立 operations.json，按 profile、关卡和完整 hash 归档；来源 sidecar 保留 runId、原记录文件和索引，不依赖人工从大 JSON 提取。

## 生成、覆盖与事务

覆盖顺序是基准→预设→global→level→range→wave。格式 `{id,profileId,target,scope,levelId,waveStart,waveEnd,waveOrdinal,field,mode,value}`；mode 为 replace 或 multiply。塔另带 targetId；明确的组成使用 `{canonicalEnemyId,role,count}`。相同优先级同字段重叠直接失败，数量/CD/价格等整数不接受小数。单体 HP 覆盖若与整波 EHP 目标冲突直接失败，不在后台重分配抹掉用户输入。

预览只写 Library。应用先检测管理单元格与全部源文件 Hash、Excel 可写性，在暂存区保留表头/类型/样式落表，运行两次 Luban（第二次绑定 runtimeContentHash），从真实 JSON 回读，再检查源文件未变才提交。事务日志先备份全部受影响源表、配方、manifest、Gen 和 JSON；保留既有 .meta 与 FTProject.Gen.asmdef。取消在安全阶段响应，提交中不强行杀进程。中断任务的退出 PID 可被识别，下次应用恢复 prepared/committing 日志；外部新改动会阻止无提示回滚。

最终应用记录：`Library/BalanceWorkbench/apply-D04-final-certified-20261017/transaction.json`，状态 `committed`；50 个候选文件中 40 个实际内容变化，所有提交后 Hash 与 journal 一致，既有文件的备份全部保留。最终正式回读检查通过、错误和警告均为 0，20 行 D04 评分状态均为 `verified_unity_reference`。`Docs/BalanceEvidence/final-application.json` 和 `Reports/application.json` 保存完整 20 个 planHash、事务及回读位置；D04 runtimeContentHash 为 `f7d9caf8af2ee6de5f8b58bece6af8b829b7efaa265eb3442f0fed9f5b2b87ea`。事务目录是本机恢复材料，不应被当成版本库唯一备份。可重复命令和窗口操作见 `LevelBalance_Workbench_Quickstart.md`。

## 当前静态及离线证据

`Reports/validation.json`：八档共 160 关/3200 波静态与数学检查通过；各档 waves.json/csv 给出每波真实名单、数量、实际 EHP、间隔、击杀和清场收入、飞行/重型/精英/首领标记；maps.json 和 monster_catalog_119.json 为地图及资源清单。D04 完整 400 波报告在 `Reports/D04/`。

`Simulation/matrix_480.json`：8 档×20 关×普通/火力/减速混合三种可复现空间策略。`reference/` 另给 160 套逐关优化参考，`lower-star/` 给 160 套合法完成且有效 1—4 星的失误对照，`mistake/` 保留 160 套明显失误导致失败的对照，共 960 条完整结果，聚合入口为 `matrix_all_960.json`。各 result.json 逐波记录出生、击杀、漏怪、现金、支出、塔组合、两种时间、峰值、AOE 真实平均命中、有效射击窗口、过量伤害和减速覆盖；聚合矩阵提供路径索引。使用实际地图四向 BFS、合法塔阻挡、飞行直线、持续锁定、CD、最强减速及地面 AOE；操作不会预支击杀收入。BFS 平局顺序、固定步长、float64 和 Unity 帧调度差异都明确标注为近似。

模拟器只输出 LevelRunMetrics 与 LevelRatingProfile，星数由 C# 唯一 LevelRatingEvaluator 回填，Python 不维护第二套评分公式。`D04_reference_index.json` 给出每关最优已发现候选及 operations.json 路径，可直接用于真实回放。

全部 960 条输出均有 Unity 唯一 C# `LevelRatingEvaluator` 的实际评分：160 套参考全部为有效预测五星；160 套低星对照均完成 20 波并合法通关，1/2/3/4 星分别 71/42/14/33 套。低星样本先复用已有弱策略，缺口再限制首波布塔数量或采用较差塔位，第二波起恢复参考消费策略；没有补金币或篡改指标。最终 160 套对照的 3200 波、5046 笔购买已核对实际塔价、逐波收支与非负余额，结果在 `lower_star_economy_audit.json`。另保留的 160 套失败对照显示 0 星/无效通关证据是预期行为，不认证为正式一星。`reference_index_160.json` 同时链接参考、有效低星和失败轨迹，`lower_star_index_160.json` 提供低星完整索引，`final_matrix_coverage.json` 汇总实际 C# 结果。每档仍为 20 个玩家关卡，所有自动策略使用测试数据。

三种统一基线策略的 C# 预测五星次数（每档 60 局）依次为 D01=58、D02=56、D03=50、D04=40、D05=37、D06=29、D07=16、D08=11。优化参考各档 20/20 达到预测五星，说明高档依赖布防和升级改进；并未把统一弱策略的失败隐藏成“全通过”。离线预测仍不认证真实可达性，真实覆盖由 Reports 的逐关 hash 匹配索引单列。

`Reports/README.md` 是最终报告入口，`reference_index.json` 优先给出同版本、操作完成的真实五星参考，独立操作文件位于 `Reports/References/<profile>/L<关卡>-<完整 hash>/`，来源 sidecar 保留原文件、记录索引、runId 与实际资金等待策略。最终合并覆盖 168 条真实运行与 960 条离线结果，所有记录均匹配当前完整版本和 planHash。D04 的 20 关全部达到真实有效五星，八档各第 1/10/20 关也均有真实五星；合计严格认证 41/160 关，余下 119 关的五星可达性保留待验证，并明确使用离线参考。真实有效低星对照覆盖 21 关，离线有效低星对照覆盖全部 160 关，逐条状态见 `Reports/coverage.json`。

## 高档后期增长校准

初版统一倍率下，固定击杀收益与塔价格没有同步扩大，高档后段 EHP 增长快于可购火力；初版 D05/D06/D07/D08 三模板仅 16/4/2/2 关有零漏怪且 T≤Par 的候选。原始高档失败摘要在 `Simulation/initial_high_profiles_superseded.json`，完整原结果保存在本机 `Library/BalanceWorkbench/pre-gradient-simulation`；早期真实初测仅用于定位，修复波次清场时序前的报告不作为校准通过证据。

最终高档候选保留八档全部首波 EHP/金币基准、20×20 数量、首次机制、速度、间隔、击杀/清场奖励、塔属性与价格。D04 全部基准保持精确。D05/D06/D07/D08 在 w>1 的预算改为逐渐接近 D04 的 1.04/1.08/1.12/1.16 倍，并依次取不低于前一档同波预算、前一波×1.04 向上取整、前一关同波×1.04 向上取整。最终值全部写成显式 wave override，报告逐项列明来源，没有后台再乘 HP 或悄悄修复用户覆盖。

因此高档仍有更难的首阵、更少的起始金、更快的敌人和更紧的出生间隔，后期也保留 EHP 梯度；通过路线、AOE、对空覆盖及中波真实收益升级获得合法五星，不放宽 Par，也未把八档变成相同内容。梯度与全部 3200 波在最终正式应用后再次验证通过；正式配方已包含 1520 条高档显式覆盖和四份 hash 匹配的真实证据路径。D04 战斗数值和全部 planHash 保持不变，正式评分配置回填了 20 关认证状态。当前应用状态以事务记录和 `applied_state.json` 为准。

旧 5 波追加脚本、M2 balance/config 和旧 challenge 生成脚本已增加退出护栏；balance_sim.py 已改为本轮空间模拟的兼容入口，移除旧写死 D:/FreedomTower_1 的 DPS 估算。

## 本机性能与故障恢复验证

实测环境为 Intel i7-13700F（16 核/24 线程）、31.84 GiB 内存、Windows、Python 3.12.14、openpyxl 3.1.5。最终正式应用及 168 条真实证据绑定后连续测量三次：单波视图 preview 平均 0.398 秒（0.386—0.418 秒，仍完整生成和校验 400 波）；正式导出 JSON 的 400 波生成、validate/runtimeContentHash 回读平均 0.189 秒（0.187—0.193 秒）。逐次值和实际 Python 路径在 `Docs/BalanceEvidence/data-pipeline-performance.json`。

独立临时工程事务故障测试 15/15 通过，涵盖提交中断、最终回读失败整批回滚、真实 Windows Excel 文件共享锁阻止替换、活动/过期锁、取消、源文件变更、依赖与 Luban 失败。恢复会跳过已经是原 Hash 的文件，清理 `.balance-tmp`；无法恢复的 journal 标为 `rollback_blocked`，后续任务仍会阻断，不能因锁文件被删除而绕过。结果在 `Docs/BalanceEvidence/pipeline-transaction-tests.json`，测试确认正式工程文件 Hash 未变。

正式应用后重跑真实工作簿和 CLI 进程测试 5/5 通过，连同公式与差异预览 13 项、证据完整性 10 项和事务 15 项共 43 项全部再次通过。预览按 Luban 字段的 float32 运行精度比较，避免把等价序列化值列成几千条假差异；最终应用前的 D04 预览仅有 20 条校准状态回填，实测 0.420 秒。4186 个数据行的 EnemyData 在 D08→减少 64 个变体→D04 的三次临时切档中，暂存耗时分别为 1.012/0.886/1.007 秒；工作簿始终为 4189 行，复用移除及既有空白行，132 个原型的单元格值、样式和人工附加列保持一致。两次真实 Luban 导出及评分摘要绑定合计 1.464 秒，导出 JSON 回读通过；生成代码统一 LF 且无行尾空白。取消检查覆盖表边界和每 128 个数据行。完整逐表耗时在 `Docs/BalanceEvidence/pipeline-io-tests.json`。

编辑器通过 `FT_BALANCE_EDITOR_LOG` 指定绝对 `pipeline.log`；Python 全程将标准输出、标准错误和异常堆栈写入 UTF-8 行缓冲文件，工作台定时读取，因此进程输出不依赖可能被 Unity 域重载卸载的管道读取器。普通 CLI 保留控制台输出。显式 `--out` 的任务在结束时原子写入 `cli-exit.json`，包含 jobId、command、exitCode 和 UTC 完成时间；启动先删除同目录旧收据，避免误认旧成功结果。真实子进程验证成功、异常及参数错误的退出码分别为 0/1/2，编辑器日志模式下管道输出为空，异常文件保留堆栈。域重载后的实际工作台恢复结果另以编辑器验收报告为准。
