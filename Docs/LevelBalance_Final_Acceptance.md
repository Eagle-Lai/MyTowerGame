# 关卡数值重设计：最终验收主报告

> 历史版本：本文件保留 2026-10-17 的 20×20 验收记录。当前 30×25 长路线改造见 [新版验收报告](BalanceEvidence/30x25/acceptance.md)，不要将本页结果用于认证新版。

本报告按 [执行 Prompt](LevelBalance_Redesign_Executable_Prompt.md) 汇总最终交付和实际证据，记录日期为 2026-10-17。目标工程为 `E:/MyTowerGame`，Unity `2022.3.62f3c1`，编辑器验证使用本工程 `unityMCP / 8082`。核心数据、评分、存档、工作台、要求的真实抽样和必要验证已完成，最终编译及控制台检查通过；[最终机器验收](BalanceEvidence/final-verification.json) 汇总实际结果。工作台原生窗口截图仍受 Windows 桌面捕获权限阻断，具体边界见末节。

正式预设为 D04「中等」：保留 20 个原关卡 ID，每关 20 个独立清场 Round，每 Round 一个 EnemyList，共 400 波。阶段 I—V、八档开发调参预设与本局 1—5 星分别存储，玩家没有新增八档选择流程。八档共 160 组预设/关卡、3200 波；已合并 960 条离线记录和 168 条真实运行记录，全部匹配当前完整版本与 planHash。

## 交付索引

| Prompt 交付项 | 实现与说明 | 主要证据 |
|---|---|---|
| 20 关经济、塔、角色、体型、地图、阶段、八档和校准理由 | [数据设计与证据说明](LevelBalance_Data_Design_And_Evidence.md) | [3200 波验证](../Luban/BalanceDesign/Reports/validation.json)；[D04 地图](../Luban/BalanceDesign/Reports/D04/maps.json) |
| 正式 400 波、八档 3200 波及逐波合并报告 | [最终报告入口](../Luban/BalanceDesign/Reports/README.md)；[D04 JSON](../Luban/BalanceDesign/Reports/D04/waves.json) / [CSV](../Luban/BalanceDesign/Reports/D04/waves.csv) | [全部波次](../Luban/BalanceDesign/Reports/all_waves_3200.json)；[证据索引](../Luban/BalanceDesign/Reports/evidence_index.json) |
| 全 119 种资源目录、实际选用及首次出场 | [资源清单](../Luban/BalanceDesign/Reports/D04/monster_catalog_119.json)；[实测尺寸](../Luban/BalanceDesign/monster_measurements.json) | [稳定变体 manifest](../Luban/BalanceDesign/variant_manifest.json)；[视觉复核](BalanceEvidence/visual-qa.md) |
| 可重复生成器、权威配方、覆盖、稳定 ID 和 CLI | [共享管线](../.workbuddy/tools/balance_pipeline.py)；[权威配方](../Luban/BalanceDesign/balance_design.json)；[工作台快速开始](LevelBalance_Workbench_Quickstart.md) | 43 项 Python 测试、真实 Excel/Luban 和事务证据见下表 |
| 逐关五星参考、有效低星对照、Par 和覆盖边界 | [160 组离线索引](../Luban/BalanceDesign/Simulation/reference_index_160.json)；[优先真实参考索引](../Luban/BalanceDesign/Reports/reference_index.json) | [逐关覆盖](../Luban/BalanceDesign/Reports/coverage.json)；[离线 C# 评分汇总](../Luban/BalanceDesign/Simulation/final_matrix_coverage.json) |
| 五星 UI、双时钟、快照、旧成绩归档和双后端迁移 | [运行与存档说明](LevelRating_Runtime_And_Save.md) | [正式应用后 54 项 EditMode](BalanceEvidence/editmode-final-postapply-54.json)；[继续与倍速](BalanceEvidence/PlayMode-checkpoints/unity-results.json)；[八项安全场景](BalanceEvidence/runtime-safety.json) |
| 可运行工作台、异步进程、域重载和完整操作路径 | [工作台源码](../Assets/Editor/Balance/LevelBalanceWorkbench.cs)；[快速开始](LevelBalance_Workbench_Quickstart.md) | [完整操作](BalanceEvidence/workbench-acceptance-20261017-105107/result.json)；[进程专项](BalanceEvidence/workbench-integration-20261017-105141-800/result.json)；[已完成任务域重载](BalanceEvidence/workbench-terminal-reload.json) |
| 正式应用、配置包和最终编辑器检查 | [正式应用记录](BalanceEvidence/final-application.json)；[当前应用状态](../Luban/BalanceDesign/applied_state.json) | [配置 AssetBundle](BalanceEvidence/config-bundle.json)；[最终验收](BalanceEvidence/final-verification.json)；[MCP 原始响应](BalanceEvidence/editor-final-mcp.json) |

源 Excel 位于 [Luban/Config/Datas](../Luban/Config/Datas/)，正式 JSON 位于 [Assets/ConfigJson](../Assets/ConfigJson/)，生成类型位于 [Assets/Gen](../Assets/Gen/)。上述源表、配方、manifest、生成类型与 JSON 一起回读验证，不能只以 JSON 差异代表完整应用。

## 正式应用与内容身份

最终 D04 应用任务为 `apply-D04-final-certified-20261017`，事务状态 `committed`、CLI 退出码 0；50 个候选文件中 40 个实际内容变化，提交后 Hash 全部匹配 journal，既有文件备份齐全。这里的 `committed` 是文件应用事务状态，不代表 Git 提交。正式回读错误和警告均为 0，20 行 D04 评分配置均为 `verified_unity_reference`。

最终 `runtimeContentHash` 为：

```text
f7d9caf8af2ee6de5f8b58bece6af8b829b7efaa265eb3442f0fed9f5b2b87ea
```

[final-application.json](BalanceEvidence/final-application.json) 保存全部 20 个 planHash、事务和正式回读位置。校准状态来自同版本真实完整五星记录，状态回填不改变战斗 planHash。高档增长调整为配方中的 1520 条显式 wave override，保留首波基准、数量、首次机制、速度、间隔、经济、塔属性及 D04 基准；差异、原因和初版失败记录见数据设计说明。

[配置包实测](BalanceEvidence/config-bundle.json) 已在当前 Android 构建目标真实生成配置 AssetBundle，通过运行地址查找读取 11 张 TextAsset，逐张与正式 JSON 一致；20 行评分配置及生产 `Configs` 计算出的 runtimeContentHash 均匹配上述值。这认证配置包内容及寻址，没有认证完整 Android Player 或真机运行。

## 玩法覆盖与真实参考

[合并索引](../Luban/BalanceDesign/Reports/evidence_index.json) 记录真实 168/168、离线 960/960 均完整匹配，未匹配记录为 0。168 条包含三种策略、失败、有效低星和优化五星记录，不能解读为 168 局全部五星。严格五星认证要求完整版本/hash 一致、有效评分、20 波完整出生与结算、操作完成且无调试标记。

| 预设 | 严格真实五星预设/关卡 | 真实有效低星预设/关卡 | 合并真实记录 | 合并离线记录 |
|---|---:|---:|---:|---:|
| D01 非常容易 | 3/20 | 1/20 | 9 | 120 |
| D02 容易 | 3/20 | 1/20 | 10 | 120 |
| D03 中等偏下 | 3/20 | 1/20 | 10 | 120 |
| D04 中等 | 20/20 | 9/20 | 89 | 120 |
| D05 中等偏上 | 3/20 | 2/20 | 12 | 120 |
| D06 困难 | 3/20 | 2/20 | 12 | 120 |
| D07 非常困难 | 3/20 | 3/20 | 12 | 120 |
| D08 极度困难 | 3/20 | 2/20 | 14 | 120 |
| 合计 | **41/160** | **21/160** | **168** | **960** |

D04 20 关均有真实有效五星；八档各第 1/10/20 关均有真实有效五星，已满足并超过 Prompt 指定的 Unity 抽样范围。另 119 组保留 `pending_unity_reference` 和离线参考，未认证全量实战五星可达；这不影响已完成的规定抽样。每组状态和 Par 比值见 [coverage.json](../Luban/BalanceDesign/Reports/coverage.json) 与 [README](../Luban/BalanceDesign/Reports/README.md)。

每份优先真实五星参考均附独立 [操作轨迹目录](../Luban/BalanceDesign/Reports/References/)，按预设、关卡和完整 hash 归档；来源 sidecar 保留原文件、索引、runId 与资金等待策略。旧的 L6/L9 失败、四星及未完成轨迹保留，用后续合法优化回放补齐认证，没有将旧失败改写为成功。

最终正式应用后另执行了 [D04 L1 烟雾回放](BalanceEvidence/PlayMode-final-formal-smoke/unity-results.json)：有效五星、350 出生/击杀、零漏怪、余额 98，战斗 373.050005558878 秒，整局 468.100006975234 秒，读取最终 runtimeContentHash。它是正式数据重新加载的额外证据，**没有计入上述 168 条合并记录**。

## 已完成的验证

| 项目 | 实际结果与范围 | 证据 |
|---|---|---|
| 八档静态及数学 | 8 档、160 组、3200 波通过；全部 119 个战斗 prefab 身体实测，正式选用 22 种资源 | [validation.json](../Luban/BalanceDesign/Reports/validation.json)；[测量](../Luban/BalanceDesign/monster_measurements.json) |
| 离线空间策略 | 三策略基线 480、优化参考 160、有效低星 160、明显失误失败对照 160，共 **960**；星级均由唯一 C# 评分器实际回填 | [完整矩阵](../Luban/BalanceDesign/Simulation/matrix_all_960.json)；[覆盖汇总](../Luban/BalanceDesign/Simulation/final_matrix_coverage.json) |
| 离线参考及低星合法性 | 160 套参考预测五星；160 套合法完成的 1/2/3/4 星对照分别为 71/42/14/33；3200 波、5046 笔购买价格及非负余额审计通过 | [低星索引](../Luban/BalanceDesign/Simulation/lower_star_index_160.json)；[经济审计](../Luban/BalanceDesign/Simulation/lower_star_economy_audit.json)；160 套失败对照保留 0 星/无效状态 |
| EditMode | 正式应用后 **54/54** 通过，失败及跳过均 0；覆盖评分边界、版本、迁移、浮点、塔相位、JSON/SQLite、真实写锁重试和真实暂停 | [postapply 原始结果](BalanceEvidence/editmode-final-postapply-54.json) |
| Python | 正式应用后重跑 **43/43**：公式及差异预览 13、校准证据 10、事务 15、真实工作簿与 CLI 5；失败、错误和跳过均 0，2795 个正式文件 Hash 不变 | [43 项统一结果](BalanceEvidence/pipeline-final-43-tests.json)；[事务结果](BalanceEvidence/pipeline-transaction-tests.json)；[I/O 结果](BalanceEvidence/pipeline-io-tests.json) |
| 故障及事务恢复 | 真实 Excel 共享锁、提交中断、回读失败、源变更、取消、Luban 失败、跨进程日志与退出收据等通过；正式工程 Hash 不变 | [事务](BalanceEvidence/pipeline-transaction-tests.json)；[真实 I/O](BalanceEvidence/pipeline-io-tests.json) |
| 预览及回读性能 | 单波视图平均 0.398 秒，仍完整生成/验证 400 波；运行数据生成及回读平均 0.189 秒，均不写正式文件 | [环境与逐次数据](BalanceEvidence/data-pipeline-performance.json) |
| 倍速与继续等价 | 1×/2×/3×、波边界继续、半波回退及终局重复六局，只排除 runId，逐波原始 double、现金和塔相位严格一致；350 出生/击杀、余额 78、五星，战斗 379 秒、整局 474.0625 秒 | [实际回放](BalanceEvidence/PlayMode-checkpoints/unity-results.json)；[比较器](BalanceEvidence/PlayMode-checkpoints/speed-comparison.json) |
| 运行安全 | **8/8**：同屏上限暂缓与首只成功出生计时、缺失资源无奖励且作废、F2 无正式成绩、未完成波无奖励/成绩、跳波拒绝、旧解锁与版本总星数隔离、SQLite 和 JSON 的 CompleteVictory→待保存→Next 门禁→同 runId 重试/重复回调 | [安全结果](BalanceEvidence/runtime-safety.json)；真实 YooAsset 缺失资源状态已恢复，12 条预期故障日志保留 |
| 工作台完整操作链 | **通过，22.942 秒**：窗口同处理入口改波/波段/关卡/塔、Undo/Redo、切档、另存、关闭恢复、差异、验证、真实 Excel/Luban 应用、新隔离局读取新 hash、导出和回滚；正式数据、存档及 KeyShard Hash 恢复/不变 | [实际结果](BalanceEvidence/workbench-acceptance-20261017-105107/result.json) |
| 工作台进程专项 | **通过，4.849 秒、32 个事件记录**：缺失 Python、独占日志锁、窗口重入、取消、超时分支与实际 RequestScriptReload；子进程在重载期间结束，首个恢复观察点已退出，以 CLI 收据认证结果 | [进程及重载](BalanceEvidence/workbench-integration-20261017-105141-800/result.json)；没有声称观察到重载后仍存活的子进程 |
| 已结束任务跨域重载 | 实际 Python 已 exit 0/Running=false 后 RequestScriptReload，域 token 改变，jobId、command、directory、exitCode 精确恢复，保持非运行且不控制旧 PID | [terminal reload](BalanceEvidence/workbench-terminal-reload.json) |
| UI、怪物与 M1 视觉 | **最终 64 图已逐张复核通过**：24 张真实 prefab/View（三语言×两尺寸×四状态）机器 issue=0；38 张怪物（22 种身体、四首领四方向半血）无洋红；2 张 M1 最终 HUD 均 89 个可建格、五个底部按钮无遮挡/越界、各自射线命中、文字 overflow=0 | [UI 结果](BalanceEvidence/UI/ui-visual-results.json)；[视觉 JSON](BalanceEvidence/visual-qa.json)；[人工复核](BalanceEvidence/visual-qa.md) |

固定步长 PlayMode 使用真实场景、WaveManager、敌人、塔、寻路、经济、GameClock 和唯一评分器，操作遵守实际余额。离线模型仍是近似，Python 没有第二套星级公式；离线预测不替代真实五星认证。安全场景的终局统计是明确构造的故障 fixture，只认证门禁与保存链路；UI 结算 fixture 只认证显示；怪物隔离半血渲染只认证外观；M1 摄像机投影及 EventSystem 射线检查没有模拟实际建塔输入。

## 最终编辑器检查及边界

全部代码和资源冻结后的 [最终编辑器验收](BalanceEvidence/final-verification.json) 已完成，[MCP 原始响应](BalanceEvidence/editor-final-mcp.json) 保留完整调用结果：明确选定本工程实例、核对路径和版本，执行 `force/all/compile=request`，域重载后重新选实例核对身份。最终新鲜状态为 idle，`is_compiling=false`、`is_domain_reload_pending=false`、`is_updating=false`、`ready_for_tools=true`，`scriptCompilationFailed=false`。控制台 `error CS` 为 0；保留的 5 条 Error 均逐条匹配安全测试的注入场景、消息和 UTC，意外错误为 0、结果未截断且无后续分页，没有清空控制台。

[最终数据审计](BalanceEvidence/final-data-audit.json) 通过：正式数据 65,533 个字段零差异、4052 个引用路径零失效，40 个事务提交文件及既有备份 Hash 均一致。正式配置包、54 项 EditMode、43 项 Python 和 64 张源图 SHA 核对均通过，实际范围与剩余限制由最终机器验收一并记录。

工作台原生窗口截图仍未取得。[捕获状态](BalanceEvidence/workbench-capture-status.json) 记录受支持的 Computer Use API 观察到 Unity 最小化；恢复/捕获实际遇到 `GetCursorPos` 拒绝访问 `0x80070005`、FrameArrived 及窗口捕获超时。早先白屏文件已拒绝作为证据。工作台处理入口、实际进程和域重载已独立验收通过，运行 UI 截图不能替代原生编辑器窗口截图。后续动作是在可访问的交互式 Windows 桌面恢复本工程 Unity 2022，打开 `Tools/塔防/关卡数值工作台` 并捕获实际窗口；未修改安全或隐私设置。

当前视觉认证限于桌面 GameView；真机触摸、安全区及性能没有获得设备证据。Dreadnought 动画武器姿势最大边 3.629 格，人工复核接受约 3.2—3.5 格规范体型的动画变化，不宣称所有动画帧刚性满足该区间。

旧失败证据继续保留，包括 [初次安全失败](BalanceEvidence/runtime-safety-initial-failed.json)、[第二次安全失败](BalanceEvidence/runtime-safety-second-failed.json)、[初版高档失败](../Luban/BalanceDesign/Simulation/initial_high_profiles_superseded.json)、[旧视觉结果](BalanceEvidence/VisualBefore/) 及较早工作台失败报告。最终通过项均指向新的实际结果，未清空日志或以文字覆盖失败历史。

## 重复操作与交付使用

按 [快速开始](LevelBalance_Workbench_Quickstart.md) 执行“选档 → 调一波/一座塔 → 差异预览 → 快速验证 → 正式应用 → 隔离新局实测 → 报告 → 回滚”；该文档包含真实 PowerShell 命令、独立测试存储、取消、日志、域重载与失败恢复说明。正式存档迁移和波边界继续口径见 [运行与存档说明](LevelRating_Runtime_And_Save.md)。

机器证据、操作轨迹和设计文档是可审查交付；`Library/BalanceWorkbench` 的事务备份属于本机恢复材料，不能充当版本库中唯一证据。用户既有未提交工作与正式存档保留，测试使用独立命名空间。
