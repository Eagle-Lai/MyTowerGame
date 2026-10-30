# 存档口径变更：局内不落盘，只有通关写成绩（2026-10-30）

## 需求原文

> 「本地存储防御塔布阵信息存在错误，应该是通关后才能落盘，不是每次放下就落盘的，
> 不然会存在漏洞，还有金币和 HP 的保存逻辑也是一样的。」

确认口径时选择了**「局内一律不落盘」**：塔阵 / 金币 / 生命只存在于本局内存，
退出或杀进程＝本局作废，从第一波重打。代价是"退出后继续"和"失败续局"两个功能一起下线。

## 改造前的事实（为什么说它像"放下就落盘"）

代码里没有"放一座塔写一次盘"的调用点，但塔阵 / 金币 / 生命被写进同一份**局内快照**，
落盘时机有 4 处，任意一处都能把当前布阵与金币血量持久化：

| 时机 | 位置（改造前） |
|---|---|
| 每波开始前 | `GameFlowManager.OnStartRequest` → `SaveSnapshotNow()` |
| 每波结束 | `GameFlowManager.FinishRound` → `SaveSnapshotNow()` |
| 退出到选关 | `GameFlowManager.QuitToSelect` → `SaveSnapshotNow()` |
| 失败 | `OnGameOver` → `CaptureFailedRunCheckpoint()` → kv `checkpoint/failed-run` |

存储落点：SQLite `level_snapshot`（金币 / 生命 / 波次游标 / 评级证据）＋ `snapshot_tower`
（每座塔的格位 / 类型 / 等级 / 冷却与炮管相位），旧版本还有 JSON 里的 `snapshot` 字段。

**漏洞形态**：玩家在任何波次边界退出重进，就能拿回当时的布阵与金币血量；
失败时还会额外留一份"本波开头"的续局点，可以无限重打同一波。

## 现行口径

- 局内（`GameFlowState.Preparing / RoundRunning / RoundComplete`）：**不写任何盘**。
- 通关（`SaveManager.RecordClear`）：只写星级、最快用时、最佳战斗用时、最佳剩余生命、runId。
- 进关：`PlayerDataManager.InitFromLevel(Level)` 给初始金币与满血，棋盘无塔，`_roundCursor = 0`。
- 退出 / 失败 / 重开：`TeardownLevel` 拆实体，内存状态直接丢弃；重开＝重新 `InitLevel`。

## 代码改动

| 文件 | 改动 |
|---|---|
| `Assets/Scripts/Game/GameFlowManager.cs` | 删除 `TryGetResumableCheckpoint`、`SaveSnapshotNow`、`TryRestoreSnapshot`、`TryRestoreFailedRun`、`BuildResumedRunMetrics`、`CaptureFailedRunCheckpoint` 及 4 处落盘调用；`InitLevel` 不再恢复；`StartLevel`/`RestartLevel`/`QuitToSelect` 去掉清快照与续局点 |
| `Assets/Scripts/Core/Manager/SaveManager.cs` | 删除 `Snapshot`/`HasSnapshot`/`SetSnapshot`/`TrySetSnapshot`/`TryClearSnapshot`/`ClearSnapshot` 与失败续局三方法；新增 `PurgeLegacyRunState()`（启动时按"存在才清"删掉旧快照与 kv 续局点） |
| `Assets/Scripts/Data/Persistence/FailedRunCheckpoint.cs` | **删除**（含 meta） |
| `Assets/Scripts/Data/LevelCheckpointValidator.cs` | **删除**（含 meta）：它只服务于续局兼容性判定 |
| `Assets/Scripts/UI/MainMenuView.cs` | 主菜单 `ContinueBtn` 恒隐藏，开始按钮恢复单一主色 |
| `Assets/Scripts/UI/SelectView.cs` | 去掉"可续玩关优先选中"与格子上的 `Continue` 状态 |
| `Assets/Scripts/UI/LevelDetailView.cs` | 开始按钮不再显示 `Continue`；"重玩"不再先清快照 |
| `Assets/Scripts/UI/PauseView.cs` | 退出确认的**兜底文案**改为"本局作废"（见待办：本地化词条仍是旧说法） |
| `Assets/Editor/Balance/BalanceCheckpointVerifier.cs` | 重命名为 `BalanceSpeedComparison.cs`，只保留 ×1/×2/×3 倍速一致性与终局塔阵比对 |
| `Assets/Editor/Balance/BalancePlayModeVerifier.cs` | 去掉续局场景的 Begin/BeforeStep/AfterStep/Complete 与半波回滚；结果条目新增 `finalTowerSignature` |
| `Assets/Editor/Balance/BalanceRuntimeSafetyVerifier.cs` | 待保存重试的安全性验证保留，删掉"终局检查点"相关断言 |
| `Assets/Tests/BalanceRating/LevelRatingTests.cs` | 删除 2 个只测快照门面/校验器的用例，`NewCampaignRequiresAll25Waves` 去掉快照断言；新增 `GameplayMustNotExposeRunStatePersistenceApi` 防回归（谁把 `SaveSnapshotNow` / `SetSnapshot` / 续局点加回来就红） |
| `.workbuddy/tools/final_campaign_request.py` | `--kind checkpoints` 改为 `--kind controls`，只发倍速基线与高占用/低星对照，不再发续局场景 |

保留但当前**没有运行时调用点**的遗留件（有意为之，见"待办"）：
`LevelSnapshot` / `TowerSnapshot` DTO、`ISaveStorage.LoadSnapshot/SaveSnapshot`、
`BaseTower.CaptureCheckpointState/RestoreCheckpointState`。保留理由：旧库的
`level_snapshot` / `snapshot_tower` 表仍在，清理与结构兼容还需要这些 DTO；
删除它们要连带做表结构迁移，风险大于收益。

## 数据兼容

- **表结构不变**（SQLite schema 仍是 4），只是这两张表不再被写入。
- 启动时 `PurgeLegacyRunState()`：若 `LoadSnapshot().valid == true` 就写回一份空快照；
  若 kv 里还有 `checkpoint/failed-run` 就删掉。没有残留时不写盘。
- 老玩家的星级 / 通关次数 / 最快用时全部保留（那是 `level_progress`，与快照无关）。

## 验证

- **编译**：`dotnet build` 三个相关工程各 0 error
  （`FTProject.Runtime` / `FTProject.Editor` / `FTProject.BalanceRating.EditModeTests`）。
  注：工程文件由 Unity 生成且未入库，验证时临时补了 `BalanceSpeedComparison.cs` 的条目，
  验证后已还原；Unity 下次打开工程会自己重新生成。
  整解决方案里的 `Assembly-CSharp.csproj` 用 dotnet 直接编会报 CS0518（缺 mscorlib 引用），
  属 Unity 生成工程的既有限制，与本次改动无关。
- **运行时**：本次未连上 Unity MCP（编辑器未运行），**Play Mode 验证未做**，需要按下面步骤人工过一遍。

### 手工验收步骤（建议顺序）

1. 进第 1 关，放 2 座塔、升 1 级、卖 1 座，确认金币变化正常。
2. 直接退出到选关 → 再次进入同一关：应当是**初始金币、满血、0 塔、第 1 波**。
3. 打一波并失败（或中途退出）→ 重进：同样是全新一局，**不应**出现"从第 N 波继续"的提示。
4. 完整通关一关 → 回选关：星级、最快用时、最佳剩余生命正常写入；杀进程重开仍在。
5. 主菜单不应出现"继续游戏"；选关格子不再出现 `Continue`；关卡详情按钮是"开始挑战/再次挑战"。
6. 老存档目录（有旧快照的库）启动一次后，`level_snapshot.valid` 应为 0、kv 不再有 `checkpoint/failed-run`。

## 待办 / 已知未收口

1. **本地化词条没改**（配置表只能人工维护，本次未获授权）：`tblocalization` 里
   `Leave this battle?` 的 zhHans 仍是「返回选关？只保留最后成功保存的波次检查点。」，
   zhHant 同理。要改成"本局进度将不保留"，需人工改 `Localization.xlsx` → Luban 导出 → 重封 `runtimeContentHash`。
   代码侧只改了**词条缺失时**的英文兜底。
2. `BaseTower.CaptureCheckpointState/RestoreCheckpointState` 与 `TowerSnapshot` 的相位字段
   已无运行时调用点（仅单测在用）。若确认不再需要"塔相位可序列化"，可连同
   `TowerSnapshot.HasValidRuntimeState` 与对应单测一起删掉。
3. 平衡工具若还有脚本传 `checkpointScenario` / `checkpointWave`，现在会被忽略；
   旧的 `--kind checkpoints` 已改名 `controls`，历史命令行需要跟着改。
