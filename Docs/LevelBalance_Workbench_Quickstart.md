# 关卡数值工作台：操作与恢复

本轮正式内容为 D04「中等」，20 个原关卡 ID、每关 20 个独立清场波次。阶段 I—V、八档调参预设、单局 1—5 星分别存储。数据公式只在 `.workbuddy/tools/balance_pipeline.py` 与权威配方 `Luban/BalanceDesign/balance_design.json` 定义；窗口不复制成长公式。

## 从改动到回放

1. 打开 Unity 菜单 **Tools → 塔防 → 关卡数值工作台**。选择 D01—D08 或自定义预设、关卡和波次。
2. 「波次与覆盖」选择单波、连续波段、整关或全战役，填写字段与最终值/增量倍率。例如波次 `targetEhp` 的单位为有效生命、`spawnIntervalMs` 为毫秒、`count` 必须是整数；塔的 `CD/radius/power/prices` 均保留原表整数类型。配方页可直接修改九级塔、角色、公式和评分参数。
3. 点「候选 / 差异」。草稿及候选位于 `Library/BalanceWorkbench/`；查看完整编组、原型/变体 ID、HP、速度、间隔、收益及字段修改前后值。数量、预算及版本冲突会阻止正式应用。
4. 点「快速校验」。地图页刷格写入同一候选覆盖，S/E 唯一性和四方向连通由核心检查。图表节点可定位波次；计划出生跨度不是实测清场用时。
5. 点「验证并正式应用」。管线检查文件锁和外部变化，在暂存区写 Excel、运行 Luban、从 JSON 回读验证，再提交源表、配方、manifest、Gen 和 ConfigJson。任务日志显示阶段、耗时和输出目录。
6. 用新局实测。草稿试验可在「策略与报告」选择关卡/策略并登记隔离实测，然后执行 **Tools → 塔防 → 数值验证 → 运行隔离回放**。该入口进入 PlayMode；测试存档位于独立 `BalanceTests` 命名空间，正式成绩不受影响。
7. 导出 JSON/CSV/Markdown。实际 PlayMode 结果包括每波出生、击杀、漏怪、现金流、塔操作和唯一评分器结果。离线报告必须保持“预测”标签。
8. 回滚时选择应用目录中的 `transaction.json`。核心检查当前文件是否仍对应本批应用，再整批恢复；外部新改动会阻止无提示回滚。

## 草稿和覆盖

输入后 200ms 防抖启动异步候选进程。单次预览实际耗时显示在任务日志中；切档不运行 Luban。撤销/重做使用 Unity Undo；草稿在 `Library/BalanceWorkbench/draft.json` 恢复，关闭重开窗口继续使用该文件。可导出草稿或另存稳定 ID 自定义预设。

覆盖顺序为：原始基准 → 预设倍率 → 全局 → 单关 → 波段 → 单波。同级重叠写同字段报错。`composition` 与 `roleRatios` 可在配方结构编辑器修改；最终名单由核心确定生成，游戏中不随机补槽。地图、塔、经济、怪物或评分参数变化会改变 planHash，并使既有 Par 校准证据失效。

直接手改受管理 Excel 或 JSON 后，正式应用会报冲突。请将变动显式录入配方覆盖，或保留源文件、放弃当前候选；不要绕过冲突检查。未管理字段保留既有内容。

## 命令行

以下命令在 PowerShell、`E:\MyTowerGame` 执行。Python 可在窗口修改；当前环境已验证 bundled Python 包含 openpyxl。

```powershell
$balancePython = 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $balancePython .workbuddy/tools/balance_pipeline.py preview --profile D04 --out Library/BalanceWorkbench/cli-preview --dry-run
& $balancePython .workbuddy/tools/balance_pipeline.py validate --profile D04 --export-dir Assets/ConfigJson --out Library/BalanceWorkbench/cli-validate
& $balancePython .workbuddy/tools/balance_pipeline.py all-profiles --out Library/BalanceWorkbench/cli-eight
& $balancePython .workbuddy/tools/balance_pipeline.py simulate --profile D04 --strategy mixed --level-min 1 --level-max 20 --step-ms 100 --out Library/BalanceWorkbench/cli-simulation
& $balancePython .workbuddy/tools/test_balance_pipeline.py
& $balancePython .workbuddy/tools/check_ui_contract.py
```

正式应用与回滚：

```powershell
& $balancePython .workbuddy/tools/balance_pipeline.py apply --profile D04 --recipe Luban/BalanceDesign/balance_design.json --out Library/BalanceWorkbench/cli-apply
& $balancePython .workbuddy/tools/balance_pipeline.py rollback --transaction Library/BalanceWorkbench/cli-apply/transaction.json
```

Unity Test Runner 运行 `FTProject.BalanceRating.EditModeTests` 和 `FTProject.BalanceCombat.EditModeTests`。编译验证必须按根目录 AGENTS.md 的 unityMCP / 8082 流程执行。完整 PlayMode 批次入口为 `FTProject.EditorTools.BalancePlayModeVerifier.StartBatch(requestPath)`，请求含 `output/stepSeconds/stepsPerUpdate/runs`，每条 run 含 `profileId/levelId/strategy/speed/candidateDirectory`；可选 `operationsPath` 重放合法操作轨迹。

## 取消和失败恢复

窗口不阻塞等待外部进程。取消预览/模拟只终止本任务进程；正式应用/回滚通过 `cancel.request` 在安全边界退出，不中断一半提交。域重载恢复只跟踪已有任务，不重复提交。

活跃任务与最后已完成任务分开保存于 Unity `SessionState`：活跃任务为 `FT.Balance.Job`，保存 PID、操作系统创建时间、jobId、命令、输出目录和可执行文件；已经由监控观察到退出的任务为 `FT.Balance.LastCompletedJob`，另保存实际观察到的退出码。导入生成 C# 可能在子进程结束后才触发域重载，因此恢复既覆盖仍活跃的任务，也覆盖刚结束的任务。恢复活跃任务时核对 `editor-job.json`、PID 与操作系统创建时间，避免控制重用该 PID 的其它进程；恢复已完成任务直接使用终局记录，不重新打开旧 PID。这里的 `SessionState` 用于同一 Unity 编辑器会话的域重载恢复。

正常监控使用操作系统提供的真实进程退出码。Python 每次结束还原子写入 `cli-exit.json`，记录 jobId、命令、整数退出码和 UTC 完成时间；重载后核对收据与原任务身份，已有操作系统退出码时还要求两者相同。新任务先移除同目录旧收据，防止将上一次成功误当成本次结果。没有观察到退出、也没有有效终局收据时显示未知/失败并提示检查事务记录，不能默认退出码为 0。恢复结果通过完成通知交给窗口，窗口再读取候选或事务产物。

完整进度由 Python 自己在其生命周期内写入 UTF-8 行缓冲的 `pipeline.log`，编辑器通过 `FT_BALANCE_EDITOR_LOG` 指定该文件并定时读取；日志不依赖已卸载脚本域中的 stdout/stderr 读取器。`editor.log` 保存编辑器侧诊断。诊断文件暂时被占用不会放弃活跃进程的所有权，下一次轮询继续监控；检查故障时同时查看这两个文件。

Excel 被占用、Python/openpyxl 缺失、Luban 失败、源哈希变化或校验失败时查看 `editor.log`、`validation.json`、`export_validation.json` 与事务记录。依赖可用窗口配置的 Python 执行 `-m pip install openpyxl` 修复。暂存失败不进入正式目录；提交异常按备份回滚。

当前活动局冻结配置、评分参数和 hash。正式应用只影响后续新局；编辑器候选重载要求先拆卸当前局且处于隔离测试存储。资源包运行还需重建实际 config 包，不能把磁盘 JSON 更新当作设备端已更新。

## 实际操作验收

2026-10-17 的 [工作台完整操作验收](BalanceEvidence/workbench-acceptance-20261017-105107/result.json) 已通过，总耗时 **22.942 秒**。执行窗口的同一处理入口，覆盖单波、波段、单关及塔修改、Undo/Redo、D01→D04 切档、预设另存、关闭重开草稿、差异与快速校验、暂存 Excel 和真实 Luban、正式应用、隔离新 PlayMode 局加载应用后的 planHash/runtimeContentHash、JSON/CSV/Markdown 报告导出与整批回滚。最终 `formalHashesRestored=true`、`officialSaveHashesUnchanged=true`、`keyShardUnchanged=true`。

[进程与域重载专项](BalanceEvidence/workbench-integration-20261017-105141-800/result.json) 已通过，**4.849 秒、32 项检查全部通过**，实际执行缺失 Python、诊断日志独占锁、运行中关闭重开及第二窗口重入、取消、超时分支和脚本域重载。重载前启动真实活跃预览；首个恢复观察时子进程已经结束，验证器通过真实 CLI 收据、原任务身份及恢复结果完成验收。因此这份报告验证“任务运行期间请求重载、重载期间退出”的路径，不能表述为观察到恢复后仍存活的子进程。正式文件与正式存档 Hash 均保持不变。

[任务完成后重载专项](BalanceEvidence/workbench-terminal-reload.json) 也已通过：先确认真实 Python 预览已经结束、退出码为 0 且 `Running=false`，再实际调用 `RequestScriptReload`；前后域 token 确实不同，恢复后的 jobId、命令、输出目录、退出码逐项精确一致，仍为 `Running=false`。这两份专项分别证明“运行中请求重载”与“任务已完成后请求重载”的恢复时序；已完成任务恢复没有重开或控制旧 PID。

## 时间和验证边界

战斗时间从每波第一只成功出生计至最后一个计划个体结算；不含开场和波间布防等待。整局时间从开第一波计至结算，含波间等待。两者均随 1×/2×/3×模拟速度推进，暂停/后台/离线冻结。

固定步长 PlayMode 回放使用真实场景、对象池、WaveManager、塔、敌人、A*、经济、GameClock 和唯一评分器；表现动画使用渲染帧，不能替代手工触摸、相机遮挡和操作手感验收。Par0、离线预测和真实证据分别记录，未覆盖关卡保持待验证状态。
