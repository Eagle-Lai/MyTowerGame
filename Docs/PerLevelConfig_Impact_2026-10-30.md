# 关卡配置「每关一组」改造 —— 影响面清单（2026-10-30）

> 本文只做盘点与方案，不含代码改动。文末有 5 个需要你拍板的点。

## 一、现状：10 张表，其中 3 张仍是"公共"的

`__tables__.xlsx` 里登记的 10 张表：

| 表 | 内容 | 形态 | 数据量 | 要不要下沉到每关 |
|---|---|---|---|---|
| `TBSceneInfo` | 关卡（初始金币/生命、回合列表、相机、难度） | **已每关** 30 文件 | 30 行 | — |
| `TBLevelMap` | 棋盘布局 | **已每关** 30 文件 | 30 行 | — |
| `TBRoundData` | 回合（波次列表、通关奖励） | **已每关** 30 文件 | 750 行 | — |
| `TBEnemyList` | 波次（出怪序列、间隔） | **已每关** 30 文件 | 750 行 | — |
| `TBLevelRating` | 评级参数 | **已每关** 30 文件 | 30 行 | — |
| `TBEnemyData` | 怪物（血量/速度/护甲/奖励/是否飞行） | **半公共**：基表 `EnemyData.xlsx` **132 行 canonical** + 30 个分层变体文件 | 12,594 行 | **要**（基表是公共信息） |
| `TBTowerInfo` | 防御塔（3 类 × 3 级） | **公共** 1 文件 | 9 行 | **要** |
| `TBBulletData` | 子弹（被塔表 `bulletId` 引用） | **公共** 1 文件 | 6 行 | **要**（塔下沉后必须跟着走） |
| `TBGlobal` | 全局常量 | **公共** 1 行 | 22 个常量 | **拆**（见 §四） |
| `TBLocalization` | 多语言词条 | 公共 | 数百条 | **不建议**（文本与关卡无关） |

一句话：**真正挡住"每关定制"的是塔表、子弹表、怪物基表、全局常量这 4 张。**

## 二、代码影响（按表列，含文件:行）

### 2.1 防御塔（`TBTowerInfo`，9 行）

| 访问点 | 位置 | 说明 |
|---|---|---|
| `Configs.GetTowerByTypeAndLevel(type, level)` | `Assets/Scripts/Data/Configs.cs:430` | **按 type+level 线性扫全表** —— 现在是"全局唯一"，下沉后必须变成 `(levelId, type, level)` |
| `Configs.GetTowerByTypeAndLevelSilent` | `Configs.cs:445` | 高频/可失败场景（按钮可用性刷新） |
| `Configs.GetTowerSilent(id)` / `GetTower(id)` | `Configs.cs:462 / 418` | 按 id 取 |
| `Configs.TowerTable.DataList` | `Assets/Scripts/UI/TowerCodexItem.cs:150` | **枚举全表**画图鉴；下沉后要按当前关过滤 |

调用点（共 7 处）：

```
Assets/Scripts/Tower/BaseTower.cs:921          TowerConfig cfg = Configs.GetTowerByTypeAndLevel(type, level);
Assets/Scripts/Tower/TowerPlacement.cs:159     同上（建造/升级预览）
Assets/Scripts/UI/HudView.cs:662               建塔按钮（type, level=1）
Assets/Editor/Balance/BalancePlayModeVerifier.cs:462/465/495
```

**关键耦合**：`TowerInfo.upgradeTo` 是"下一等级塔的 **id**"（1→2→3），`sellPrice` 是累计成本；
塔表下沉后这两列要按本关的 id 段解析，否则升级链会跳到别的关的塔。

### 2.2 子弹（`TBBulletData`，6 行）

| 访问点 | 位置 |
|---|---|
| `Configs.GetBullet(Config.BulletId)` | `Assets/Scripts/Tower/BaseTower.cs:676`（唯一调用点） |

塔表 9 行的 `bulletId` 全部指向它。**塔下沉 = 子弹必须一起下沉**，否则"某关专属弹道"无从配起。

### 2.3 怪物（`TBEnemyData`，132 行基表 + 12,462 行变体）

| 访问点 | 位置 | 说明 |
|---|---|---|
| `Configs.GetEnemy(id)` | `Assets/Scripts/Enemy/EnemyManager.cs:63`、`GameFlowManager.cs:484`、`LevelDetailView.cs:254/292`、`Assets/Editor/Balance/BalanceRuntimeSafetyVerifier.cs:181` | 5 处，全部按**全局 id** |
| `Configs.EnemyTable.DataList` | `Assets/Scripts/UI/MonsterCodexView.cs:58` | **枚举 1.2 万行**画图鉴 |

现状是"一张表 31 个文件"：基表 `EnemyData.xlsx` 的 132 行是 30 关共用的 canonical 定义，
分层文件只放"每关变体"。要做成"每关一组"，基表这 132 行必须拆到各关（或明确保留为"模板"）。

### 2.4 回合 / 波次 / 关卡 / 棋盘 / 评级（已是每关，但要跟着改查询签名）

| 访问器 | 次数 | 代表位置 |
|---|---|---|
| `Configs.GetRound` | 8 | `GameFlowManager.cs:470/526/652/670`、`LevelDetailView.cs:179` |
| `Configs.GetWaveGroup` | 7 | `GameFlowManager.cs:477/539`、`WaveManager.cs:92`、`LevelDetailView.cs:191` |
| `Configs.GetLevel` | 7 | `GameFlowManager.cs:49/70`、`SaveManager` 间接 |
| `Configs.GetLevelRating` | 8 | `SaveManager.cs:380/401/426`、`GameFlowManager.cs:52/310`、`LevelDetailView.cs:205` |
| `Configs.GetLevelMapOfLevel` | 5 | `GameFlowManager.cs:289`、`LevelMapPreviewGraphic.cs:15`、`LevelPreviewCapture.cs:133/162`、`LevelPreviewVerifier.cs:166` |

这些表虽已是"每关一个文件"，但**代码里仍是一次性把所有关的表全部加载进静态字段**（`Configs.EnemyTable/RoundTable/...`）。
要做到"一组一关"，还得把加载改成"按当前关取子集"。

### 2.5 全局常量（`TBGlobal`，22 个字段，18 个被代码引用）

| 字段 | 次数 | 归类 | 建议 |
|---|---|---|---|
| `SellRefundRate` | 6 | 经济 | **下沉** |
| `CellSize` | 4 | 地图几何 | **下沉**（每关棋盘比例可不同） |
| `ShowDebugLog` | 3 | 引擎 | 留全局 |
| `MaxEnemyAlive` / `EnemyPoolSize` / `BulletPoolSize` | 4 | 引擎 | 留全局 |
| `DeathRecycleDelayMs` / `CheckOfflinePerFrame` / `TargetFrameRate` | 3 | 引擎 | 留全局 |
| `DefaultDamageToPlayer` / `DefaultBodyRadius` / `DefaultSearchIntervalMs` | 3 | 玩法默认 | **下沉** |
| `DefaultReward` | 0（已废） | 玩法默认 | 删除 |
| `AutoNextRoundDelayMs` / `AutoStartRoundDelayMs` | 2 | 关卡节奏 | **下沉** |
| `ShakeAmplitude` / `ShakeDurationSec` | 2 | 表现 | 可下沉 |
| `ShowDamageText` / `DamageTextThrottleSec` | 2 | 表现 | 可下沉 |
| `ArtFaceLeft` / `BoardOriginPadding` | 2 | 表现/几何 | 表现留全局，`BoardOriginPadding` 随 `CellSize` 下沉 |

## 三、会被连带打破的机制（比表本身更容易出事）

1. **运行时内容哈希**（`Configs.cs:362`）
   现在固定吃 **8 张全局表 JSON + 30 行评级**，算出一个总哈希，30 关共用。
   下沉后必须改成**按关卡**算：`hash(L01) = 本关 9 张表 + 本关评级行`。
   → 好处很大：以后改 L01 只重封 L01，**不用再 30 关全封**（你今天反复踩的就是这个）。

2. **评级校验** `Configs.ValidateRatingPlan`（`Configs.cs:380`）
   走 关卡→回合→波次→敌人，并比对 `expectedEnemyCount`、`bossVariantIds`。
   下沉后要新增：本关塔表必须覆盖 **3 类 × 3 级**、每个 `upgradeTo/bulletId` 在本关内可解析。

3. **跨表自检** `Configs.ValidateCrossReferences`（`Configs.cs:237`）
   现在遍历"全表"；下沉后要改成按关卡遍历（30 次），否则报错信息说不清是哪一关的问题。

4. **Luban 表登记与表头一致**
   `__tables__.xlsx` 每张表的 `input` 要从 1 个文件变成 30 个；`define_from_file=True` 意味着
   **表头定义只认第一个文件**（今天的 `reward int→float` 事故已经验证过这一点）。
   30 份表头必须逐字一致，否则导出报的是"第一个文件"的类型错误，定位极难。

5. **ID 空间**
   30 关各写 1..9 号塔 → 合并后主键冲突。两个解法：
   - 每关 id 段：`levelId*1000 + type*10 + level`（L01 = 1011..1033）；
   - 复合键：`(levelId, towerId)`，但 Luban map 表只支持单主键，要自己加列或用联合主键。

6. **存档/快照/续局**
   `TowerSnapshot` 存的是 `row/col/type/level`（**不存塔 id**），所以 id 段变化**不影响存档兼容**；
   但 `LevelCheckpointValidator` 的 `versionKey` 含 `planHash`，改表即作废（现有行为，符合预期）。

7. **UI 全表枚举**
   `TowerCodexItem`（塔图鉴）、`MonsterCodexView`（怪物图鉴，1.2 万行）现在枚举全表。
   下沉后要么按当前关过滤，要么明确保留一个"合并视图"给图鉴用 —— 这是产品决策，不是纯技术。

8. **配置加载与预载**
   `Configs.ConfigKeys`（`Configs.cs:54`）现在固定 10 个 key，`ResLoader.Preload` 一次性全拉。
   下沉后 key 数量 ≈ 10 + 30×3 = 100 项，要么全拉（内存↑），要么改成"进关时拉本关的"（启动更快，但要接异步）。

9. **工具链（容易被低估）**
   `.workbuddy/tools` 里 **12+ 个脚本**直接读 `TowerInfo.xlsx` / `Global.xlsx` / 全局 id
   （`balance_pipeline.py`、`balance_capacity.mjs`、`append_tower_rows.py`、`apply_m2_balance.py`…），
   加上 `Assets/Editor/Balance/*` 的验证器与工作台。这部分改动量不小，而且不显眼。

## 四、目标形态（推荐方案 C：物理下沉 + 引擎常量留全局）

```
Luban/Config/Datas/
  Levels/L01/
    SceneInfo.xlsx    LevelMap.xlsx   RoundData.xlsx
    EnemyList.xlsx    EnemyData.xlsx  LevelRating.xlsx
    TowerInfo.xlsx    ← 新增：本关 9 行（3 类 × 3 级）
    BulletData.xlsx   ← 新增：本关 6 行
    LevelRules.xlsx   ← 新增：原 Global 的玩法常量（cellSize/节奏/退款/默认值/表现）
  Levels/L02/ … L30/  同上
  Global.xlsx         ← 只留 7 个引擎常量（池大小/帧率/回收/日志/离线检查）
  Localization.xlsx   ← 保持公共（文本与关卡无关）
  __tables__.xlsx     ← 9 张表各登记 30 个文件 + 2 张公共表
```

ID 规则建议：塔 `levelId*1000 + type*10 + level`，子弹 `levelId*100 + bulletId`；
代码对外不暴露塔 id（一律走 `(levelId, type, level)`），`upgradeTo` 只在本关内跳。

## 五、分阶段落地（每阶段可独立验证，不必一次做完）

| 阶段 | 内容 | 验证点 |
|---|---|---|
| P0 | 定 ID 规则、`__tables__.xlsx` 加 30 文件、生成 30 份塔/子弹/规则表初值（从现值复制） | Luban 导出成功；30 关数据与现值逐字段一致 |
| P1 | 代码加关卡作用域：`Configs.GetTower(levelId, type, level)`、`GetBullet(levelId, id)`；`Config` 在 `InitLevel` 时绑定 levelId | 编译 0 错；Play Mode 三塔建造/升级/出售正常 |
| P2 | 塔/子弹/图鉴/建造 UI 改按当前关取；自检按关遍历 | 图鉴只显示本关塔；跨关数据不串 |
| P3 | `Global` 拆成"引擎常量 + 每关 LevelRules" | 每关 `cellSize`/退款/节奏独立可改 |
| P4 | 哈希/评级改**按关卡**重封（每关独立 runtimeContentHash） | 改 L01 只重封 L01；Play Mode `[Rating] verified` 通过 |
| P5 | 敌人基表 132 行 canonical 拆分/去重 | 12,594 行变体仍可解析；图鉴不重复 |
| P6 | 工具链与 Editor 验证器对齐 | `.workbuddy/tools` 只读命令跑通 |

## 六、需要你拍板的 5 个点

1. **形态**：物理下沉（每关一个文件，符合"一组一关"，但改公共值要动 30 次）还是
   逻辑下沉（一张表加 `levelId` 列，改动小但仍是"一张大表"）？我推荐**物理下沉 + 保留 Global 引擎常量**。
2. **引擎常量**：`enemyPoolSize / bulletPoolSize / maxEnemyAlive / targetFrameRate / deathRecycleDelayMs / checkOfflinePerFrame / showDebugLog` 这 7 个允许留在 Global 吗？（下沉到 30 份没有意义，且极易漂移）
3. **本地化**：`Localization.xlsx` 保持公共？
4. **塔 id**：按 `levelId*1000+...` 重新编号（代码对外不暴露 id）可以吗？现有存档不存塔 id，无兼容问题。
5. **工具链**：`.workbuddy/tools` 那 12 个脚本要不要一起改？不改的话，P6 之后它们读的表路径会全部失效。

确认后我按 P0→P1 先做骨架与塔/子弹下沉，每阶段给验证结果再往下走。
