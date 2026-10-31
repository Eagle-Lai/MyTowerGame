# 每波落盘 + 续局还原（布阵 / 金币 / 生命 / 波次游标）（2026-10-31）

## 需求演进与最终口径

需求原文：

> 「修改代码，每个关卡在关卡完成后，都保存当前关卡的防御塔摆放数据，进行落盘，游戏通关后再清除数据」

四轮澄清后的最终口径（用户逐条确认，均以此为准）：

| 问题 | 用户选择 | 落地含义 |
|---|---|---|
| 落盘的阵型之后怎么用 | **重进时免费还原** | 再进该关时把上次阵型直接摆回棋盘，不扣金币 |
| 已保存的记录什么时候删 | **每次写入清旧写新** | 整条替换该关旧记录；长期保留，不做"全游戏通关后统一清空" |
| 什么时候写盘 | **每通过一波就写** | `FinishRound` 回合结算后立即落盘；整关通关再写一次 |
| 除了塔阵还存什么 | **金币 + 生命** | 记录带 `gold/hp/maxHp`，进关时覆盖 `PlayerDataManager` |
| 要不要存进度 | **存波次游标**（第二轮追加） | 连 `roundCursor` + 整份 `LevelRunMetrics` 一起存，重进**接着上一波打** |

> 原始那句「游戏通关后再清除数据」收敛为「每次写入时清旧写新」——
> 因为"关卡完成后保存"与"最后一波完成后清除"是同一时刻（`CompleteVictory`），
> 照字面执行等于存了立刻删。这一点已在实施前与用户确认。

## 与 2026-10-30 存档口径的关系（重要，必须如实记录）

`Docs/SavePolicy_2026-10-30.md` 当时定的是"局内一律不落盘"，理由是：
在波次边界写快照 = 玩家可以从任意波次重来 = 漏洞。

**本次（2026-10-31 第二轮）等于把这套"续玩快照"恢复回来了**，用户明确要求并接受其代价。
差别只在实现形态，不在语义：

| 维度 | 2026-10-30 废止的旧快照 | 现在（2026-10-31） |
|---|---|---|
| 内容 | 塔阵 + 金币 + 生命 + 波次游标 + `LevelRunMetrics` | **完全一样**（另加"重玩起点"语义） |
| 写入时机 | 每波开始前 / 每波结束 / 退出 / 失败 | **每波结束（通过）** + 整关通关（写重玩起点） |
| 存储位置 | SQLite `level_snapshot` / `snapshot_tower` 表 | kv_store 单键 `layout/campaign`（密文 json） |
| 表结构 | 占用两张表 | **不建表、schema 仍是 4**，旧表继续空置 |
| 恢复后果 | 从第 N 波继续 | 从第 N 波继续（同一行为） |

也就是说：

- ✅ **"续玩 / 失败后从当前波重来"重新成立**——这是用户要的（不用一遍遍重打前面的波）。
- ⚠️ 旧的 `level_snapshot` 表**仍然不写**，本次记录只走 kv；`PurgeLegacyRunState` 照旧清旧表残留。
- ⚠️ 评级证据不完整的问题必须一起解决，否则续玩通关拿不到星、下一关也解不开（见"为什么连统计一起存"）。

## 数据模型

`Assets/Scripts/Data/LevelLayout.cs`

```
LevelLayoutBook            // 整本记录册，一个 kv 键
  formatVersion            // 1；不符按"没有记录"处理（新增字段全部走显式开关，不需升版）
  levels[]  LevelLayout
      levelId, savedAtUnix, runId, towerCount
      towers[]  TowerLayoutEntry { row, col, type, level }
      resourcesSaved, gold, hp, maxHp          // 金币/生命（老记录为 false → 不动资源）
      runSaved, roundCursor, levelTimerStarted // 进度（老记录为 false → 从第 1 波开始）
      runMetrics                              // 整份 LevelRunMetrics（含 waves[] 每波明细）
```

设计取舍：

- **`resourcesSaved` / `runSaved` 两个开关必须有**：老记录没有这些字段，JsonUtility 读成 0/false，
  不区分就会"0 血 0 金开局"或"游标 0 误判"。游标 0 本身是合法值（第 1 波还没过），不能当哨兵。
- **为什么连整份 `LevelRunMetrics` 一起存**：评级要核对
  `completedWaveCount == expectedWaveCount`、`successfulSpawned == expectedEnemyCount`、每波明细与计时。
  只存游标会让续玩局在结算时被判 `Incomplete waves / Spawn count mismatch` → 星级不落库 → 下一关锁死。
- **存 `type + level` 而不是配置 id**：塔表已按关拆分，id 会随关卡漂移。
- **不存坐标/朝向/冷却**：位置由格子决定（`SnapToCell`），冷却与炮管相位属战斗瞬时状态。
- **整本存一个键**：读取全有/全无，覆盖写入天然原子；30 关规模只有几十 KB（含统计后仍远小于 1MB）。
- **加密存放**（`sensitive=true`）：记录能换来免费塔与资源，属"改了能占便宜"的数据。

## 写入链路

| 位置 | 传参 | 效果 |
|---|---|---|
| `GameFlowManager.FinishRound` | `(levelId, _roundCursor, _run, null)` | **每通过一波**：塔阵 + 金币/生命 + 游标 + 运行统计 |
| `GameFlowManager.CompleteVictory` | `(levelId, 0, null, runId)` | 通关：写"重玩起点"——游标 0、不带统计，重进从第 1 波、全新评级 |
| `GameFlowManager.RetryPendingClearSave` | 同上 | 补写成绩成功时补记一次 |
| `LevelLayoutStore.SaveCurrentLevel` | — | 遍历 `TowerManager.Towers` 排序 → 读 `PlayerDataManager` 三值 → `runMetrics.Clone()` → `book.Upsert` → `JsonUtility.ToJson` → `SaveManager.SetUserValue("layout/campaign", json, sensitive:true)` |

日志：

```
[Layout] 第 1 关已落盘：5 座塔，金币 118，生命 8/10，波次 3（累计 1 关有记录）
[Layout] 第 1 关已落盘：5 座塔，金币 640，生命 10/10，波次 从头（累计 1 关有记录）   ← 通关那一笔
```

**为什么要区分"波次存档"和"通关后的重玩起点"**：通关时 `_roundCursor == _roundIds.Count`，
如果照原样存游标，下次进关会立刻满足 `_roundCursor >= _roundIds.Count` → 一进门又判一次通关。
所以通关这一笔写 `0 + 无统计`，语义是"这一关已通关，再进就是重玩"。

不写的情况：失败（生命归零那一刻）、中途退出、杀进程。但**之前通过的波次已经存过**，
所以"打一波就退"的进度仍然在。

## 还原链路

`GameFlowManager.InitLevel(levelId, restoreSavedState = true)` 第 ⑨.5 步（回合队列建好之后、HUD 刷新之前）：

> `restoreSavedState=false` 只由"重新开始"传入，整段还原直接跳过。

```
RestoreSavedLevelState(levelId)
  ① 校验能否接管进度：评级版本一致 / runId 未入档 / 0 < roundCursor < 波数
       └ 任一不满足 → 只还原塔与资源，波次从第 1 波开始（并打 Warning）
  ② LevelLayoutStore.RestoreResources(saved, killed, leaked)   // 走 PlayerDataManager.RestoreState
  ③ LevelLayoutStore.RestoreTowers(saved)                      // 批量静默、不扣钱
  ④ _run = metrics.Clone(); _roundCursor = saved.roundCursor;
     GameClock.RestoreTimers(combat, level, levelTimerStarted)
```

关键约束：

- **顺序固定**：先定"能否接管统计"（金币恢复要写回击杀/漏怪数）→ 覆盖资源 → 摆塔 → 赋游标与计时。
  游标必须在 `_roundIds` 建好之后赋值，否则 `Mathf.Clamp` 没有上界。
- **资源必须走 `RestoreState`**：金币/生命是私有 set，必须广播
  `GoldChangeEvent` / `PlayerHpChangeEvent` / `PlayerStateInitEvent`，否则 HUD 还显示初始值。
- **统计接着累加**：`_run` 用 `Clone()` 接管，`runId` 保持原值 —— 结算时 `RecordClear` 认的是同一局，
  不会因为"换了会话"而判成两次通关；`_run.waves` 是 `Add` 追加（不是重建），所以续玩后波次明细连续。
- **静默摆塔**：`TryBuildInternal(..., quiet)` 不弹 Tips、不刷红格；`_restoreBatchDepth > 0` 时
  不发 `BuildTowerSuccess`、不逐座重算路径，批量结束 `RequestRefresh()` 一次。
- **失败容忍**：某座塔摆不下就跳过计数，日志
  `[Layout] 第 N 关阵型已免费还原：X 座（跳过 Y 座）`；绝不因一条脏记录让整关进不去。
- **不接管的四种情况**（都只影响进度，不影响塔/资源）：统计缺失、评级版本变了、runId 已入档、游标越界。
  尤其"改过数值表"时丢弃进度是对的 —— 否则两套数值混进同一份评级证据，星级不可信。

## 经济防线（必须保留）

免费还原天然带一个漏洞：**还原塔按配置售价卖出 = 白拿金币**。堵法：

`BaseTower.InvestedGold`（实际投入）+ `TowerManager.RefundOf(tower)`：

```
返还 = min(配置售价, 实际投入) × Global.SellRefundRate
```

- 正常建的塔：投入 ≥ 售价（售价本就是累计投入的约七成）→ 返还额与改造前完全一致；
- 还原塔：投入 0 → 返还 0；
- 还原后升级的塔：`InvestedGold = 旧投入 + 升级费` → 只返还升级花掉的部分，永不超过投入。

公式只允许存在 `RefundOf` 一处；UI 三处（`TowerActionMenu` / `TowerInfoView` / `SellConfirmView`）
与执行层 `TowerManager.Sell` 全部调用它。`SellConfirmView` 的"退回 N% 的累计投入"
改为按**这一座塔**实算（`refund / invested`）。

## 改动文件

| 文件 | 改动 |
|---|---|
| `Assets/Scripts/Data/LevelLayout.cs` | **新增**：DTO（towers + gold/hp + roundCursor/runMetrics + 两个开关）+ `LevelLayoutStore`（读/写/资源还原/塔阵还原） |
| `Assets/Scripts/Data/LevelLayout.cs.meta` | **新增**：GUID `545780aa6ce449af90f6ddd5f2bd1608` |
| `Assets/Scripts/Tower/BaseTower.cs` | `InvestedGold`；`TryBuildInternal(..., bool quiet)`；`RestoreTower` 静默；`BeginRestoreBatch/EndRestoreBatch`；`RefundOf`；`Sell` 统一口径；`TryUpgrade` 记账；`ClearAll` 复位批量计数 |
| `Assets/Scripts/Game/GameFlowManager.cs` | `InitLevel(levelId, restoreSavedState)` + 第 ⑨.5 步 `RestoreSavedLevelState`；`StartLevel` 增加"是否续局"开关（"重新开始"传 false）；`FinishRound` / `CompleteVictory` / `RetryPendingClearSave` 落盘；头注释同步 |
| `Assets/Scripts/Core/Manager/SaveManager.cs` | 头注释同步（2026-10-30 的"局内不落盘"已被本轮取代，旧表仍不写） |
| `Assets/Scripts/UI/TowerActionMenu.cs` | 出售返还改用 `TowerManager.RefundOf` |
| `Assets/Scripts/UI/TowerInfoView.cs` | 同上 |
| `Assets/Scripts/UI/SellConfirmView.cs` | 同上；警告文案比例改为按实际投入实算 |

## 验证

**已做（编译）**：`dotnet build` 四个工程各 **0 error**
（`FTProject.Runtime` / `FTProject.BalanceRating.EditModeTests` / `FTProject.BalanceCombat.EditModeTests` / `FTProject.Editor`）。

**未做（编辑器内）**：本会话建立时 WorkBuddy 的 `unityMCP` 连接器尚未启用，
`mcp__unityMCP__*` 工具未加载，因此**没有执行 `refresh_unity` / Console 检查 / Play Mode 验收**。

### 手工验收步骤

1. 进第 1 关，布 5 座塔，打完第 1、2 波 → Console 每次一条
   `[Layout] 第 1 关已落盘：5 座塔，金币 X，生命 Y/Z，波次 1/2`。
2. 回选关 → 再进第 1 关：应看到 5 座塔、金币与生命等于落盘值，
   日志 `[Layout] 第 1 关已续局：下一波 3/25…`，HUD 回合显示第 3 波。
3. 点开始 → 应从**第 3 波**出怪（不是第 1 波）。
4. 打完全部波次 → 星级与最快用时正常写入（续玩局必须能评星，这是本次的关键验收点）。
5. 通关后再进该关：应回到**第 1 波**（重玩），塔与资源是通关时的状态。
6. 卖一座还原塔：返还额 **0**，警告百分比 **0%**；把还原塔升到 Lv2 再卖：返还 = 升级费，不是售价。
7. 失败一局后再进：从**最后一次通过的那一波**继续（失败当波不写）。
8. 杀进程重开：进度仍在（真的落盘）。
9. 设置里"重置存档" → 再进：空棋盘 + 关卡初始金币/满血 + 第 1 波。
10. 改过 `LevelAssets`/数值表后再进：若评级版本变化，日志应出现
    `[Layout] 第 N 关不接管局内进度（评级版本已变…）`，波次回第 1 波但塔/资源照常还原。

## 已知取舍 / 待办

1. **等于恢复了 10-30 废止的续玩快照**：失败后可以无限重打同一波（因为每波通过就存、失败不写）。
   用户 2026-10-31 明确要求"接着上一波继续"，此代价已知。
2. **没有新增本地化词条**：续局/还原只有 Console 日志，没有界面提示。
   要加提示需人工改 `Localization.xlsx` 三语言 → Luban 导出 → 重封 `runtimeContentHash`。
3. **"重新开始"不续局、"从选关进"续局**：`RestartLevel()` 走 `StartLevel(Level.Id, false)`，
   空盘 + 初始金币 + 第 1 波；但它**不删除已落盘的记录**，所以退出到选关再进仍会续到那条记录上。
   如果希望"重新开始"顺带清掉记录，需要再加一句 `LevelLayoutStore` 的清除调用（当前没加，
   避免误触把玩家进度清空）。
4. **`GameClock` 计时跨会话累加**：续局后"最快用时"包含上一次会话的时间；这是"续玩"的必然结果，
   如果要求时间榜只统计一口气打完的局，需要在续局时把 `timingValid` 置 false（当前保持 true）。
5. **地图改小/改格局后**，旧记录里可能有若干格摆不下：跳过并记日志，不自动清理旧记录。
6. 记录**不参与平衡校验**，`BalanceSpeedComparison` 的 `finalTowerSignature` 也不读它。
