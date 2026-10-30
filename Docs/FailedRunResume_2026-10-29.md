# 失败续局：改完数值后从失败的那一波接着打（2026-10-29）

## 需求

> 「当我失败后，修改了配置后，下次运行能够在失败的关卡继续玩，也就是说，需要记录失败前的
> 那个关卡的防御塔布阵信息和金币等等的其他相关内容，缓存下来。」

## 结论先说：这套链路原本 90% 都在，只差一个"改表后不作废"

工程里已有完整的局内快照（`LevelSnapshot` + `snapshot_tower` 表 + `LevelCheckpointValidator`），
回合开始时 `OnStartRequest → SaveSnapshotNow()`，退出/重开后从快照恢复。但它的兼容性校验是
**严格的版本比对**：

```csharp
// LevelCheckpointValidator.IsCompatible
snapshot.ratingProfile.versionKey != profile.versionKey  → 判定不兼容
// versionKey = profileId|balanceRevision|ratingRevision|planHash
```

而 `SaveManager.EnsureRatingVersion()` 在配置版本变化时还会直接 `_data.snapshot = new LevelSnapshot()`。
也就是说：**改完配置表，旧快照必然被清空** —— 这正好是用户要的场景，所以必须另开一份
"不校验配置版本"的续局点。

## 设计

| 项 | 做法 |
|---|---|
| 存哪 | SQLite `kv_store`，key = `checkpoint/failed-run`（明文，与快照同级） |
| 为什么不复用快照表 | 快照会被评级版本迁移整份清空；kv 键不参与版本校验，改表与重启都不丢 |
| 存什么 | `FailedRunCheckpoint`：levelId / completedWaves / failedWave / gold / hp / maxHp / 战斗与关卡计时 / 塔列表（row,col,type,level）/ configVersionKey（只做日志）/ 时间戳 |
| 什么时候写 | **失败判定时**（`OnGameOver(false)` → `CaptureFailedRunCheckpoint()`） |
| 数据从哪来 | 本波开始前 `OnStartRequest` 刚存的 `LevelSnapshot` —— 它恰好就是"失败这一波的开头"：金币/生命/塔阵都停在开波前 |
| 恢复粒度 | **只到波次边界**：不记录怪的半途位置/血量（收益极低、失配风险极高） |
| 恢复时机 | `InitLevel` 里先走原快照 `TryRestoreSnapshot`，失败才 `TryRestoreFailedRun` |
| 清理时机 | 通关（`OnGameOver(true)`）、显式"重玩"（`RestartLevel` / 关卡详情重玩）、切到别的关 |
| 评分影响 | 续局把 `LevelRunMetrics.statisticsValid/timingValid=false`、`debugOverride=true` → **本局不计星**，也不会改写通关记录；续局时会 Tips 明确提示 |

### 关键取舍：为什么续局不计星

跨配置（甚至跨尝试）的击杀/漏怪统计不可能满足评级口径（`Evaluate` 要求
`successfulSpawned == expectedEnemyCount`、逐波账目闭合、`versionKey` 一致）。
硬凑只会污染通关记录，所以这类局明确标成"不入档"，只用于验证数值。

配套改动：`SaveSnapshotNow()` 对这类局直接早退 —— 否则退出时会写一份过不了校验的快照，
下次进关先弹"快照不兼容"再弹"已从失败续局继续"，两条自相矛盾的提示。

## 改动文件

| 文件 | 内容 |
|---|---|
| `Assets/Scripts/Data/Persistence/FailedRunCheckpoint.cs` | **新增**：续局点数据结构 + 自检 + JSON 序列化（含设计说明） |
| `Assets/Scripts/Core/Manager/SaveManager.cs` | 新增 `SaveFailedRunCheckpoint` / `TryGetFailedRunCheckpoint` / `ClearFailedRunCheckpoint`（kv_store 明文，带内存缓存） |
| `Assets/Scripts/Game/GameFlowManager.cs` | ① `TryGetResumableCheckpoint` 增加失败续局兜底；② `TryRestoreSnapshot` 改返回 bool；③ 新增 `TryRestoreFailedRun` / `BuildResumedRunMetrics` / `CaptureFailedRunCheckpoint`；④ `OnGameOver` 失败时记录、胜利时清除；⑤ `StartLevel` 换关时丢弃；⑥ `RestartLevel` 显式重玩时清除；⑦ `SaveSnapshotNow` 对续局早退 |
| `Assets/Scripts/UI/LevelDetailView.cs` | 关卡详情的"重玩"确认后一并清除失败续局 |

**UI 零改动**：主菜单"继续游戏"、选关提示、关卡详情按钮文案都走
`GameFlowManager.TryGetResumableCheckpoint`，兜底接上后自动显示"继续"。

## 端到端验证（Unity 2022.3.62f3c1，Play Mode）

| 步骤 | 结果 |
|---|---|
| 编译 | `scriptCompilationFailed = false`，无 `error CS` |
| 进 L01 → 建 2 座塔（T1L1@[0,0]、T2L1@[0,2]）→ 开第 1 波 → `LoseHp(99)` 强制失败 | `[Flow] 已记录失败续局点：关卡 1｜死于第 1 波｜已完成 0 波｜金币 100｜生命 10/10｜塔 2 座` |
| 退出 Play → 重新进入（模拟"下次运行"） | `快照=True 失败续局=True`，续局点内容不变（已落盘） |
| 模拟改表（`ClearSnapshot(true)`，等价于评级迁移清空快照） | `快照=False 可续玩=True 关卡=1 下一波=1` → 主菜单/选关会显示"继续" |
| `StartLevel(1)` 走续局 | `state=Preparing towers=2 [0,0 T1L1] [0,2 T2L1] gold=100 hp=10/10 statsValid=False debugOverride=True` |
| 运行期错误 | 0 条 |

## 已知边界

- **不保存半波状态**：恢复点是"失败那一波的开头"，不是"漏第 10 只怪那一刻"。
- **不计星**：用于验证数值，不能用来刷星级。
- 切到别的关会丢弃该关的续局点（避免进关被上一关的残局劫持）。
- 真机（Android）未验，只在编辑器 Play Mode 验证。
- 存档键是明文（与 `level_snapshot` 一致）—— 属于本地试玩缓存，改它没有收益。
