# 关卡数值可调节项清单（L01 + 全工程）

> 核对日期：2026-11-02  
> 工程：`D:\FishTestGame`（Unity 2022.3.62f3c1）  
> 核对对象：`Luban/Config/Datas/Levels/L01/*.xlsx`、`Global.xlsx`、`Assets/Scripts/**`、`Assets/Gen/**`  
> 说明：本文件是**现状盘点**，不含任何数值改动。所有"现值"均读自磁盘上的当前表。

---

## 0. 先回答你举的 6 个例子

| 你提出的字段         | 当前是否存在  | 说明                                                                                                        |
| -------------- | ------- | --------------------------------------------------------------------------------------------------------- |
| 通关后增加的金币数值     | **不存在** | 只有"每波通关奖励"`RoundData.rewardGold`（L01 共 25 波，合计 1305 金）。没有"整关通关额外奖励"这一项                                    |
| 每五关后添加的金币数值    | **不存在** | 全工程没有跨关经济：`PlayerDataManager.Gold` 在每次 `InitFromLevel` 时被重置为 `SceneInfo.initialGold`，没有钱包/累计概念，也没有里程碑发放逻辑 |
| 每四关地面怪物 HP 比例  | **不存在** | 怪物血量在 `BaseEnemy.Init` 里直接取 `EnemyConfig.Hp`，**没有任何倍率层**。L02–L30 的难度是靠"复制一套表 + 手工把 hp 改一遍"实现的             |
| 每第五关地面怪物比例     | **不存在** | 同上                                                                                                        |
| 每四关空中怪物 HP 比例  | **不存在** | 同上。L01 有 21 条飞行怪（`Bat`），`isFlying=1` 是唯一区分口径                                                              |
| 每第五关空中怪物 HP 比例 | **不存在** | 同上                                                                                                        |

**结论**：你现在想要的是"**跨关进度缩放层**"，而工程目前是"**30 关 30 套独立静态表**"。  
证据：`L02` 272 条怪 / `L05` 354 条 / `L11`–`L30` 全部 454 条、结构近似但数值逐关不同；`EnemyList.desc` 里能看到历史调参痕迹（`ground5-20261030`、`hp2-20261030`、`w25soften-20261030`…），全部是直接改表值，而非运行时缩放。

---

## 1. 关卡主表 `SceneInfo.xlsx`（L01 仅 1 行）

文件：`Luban/Config/Datas/Levels/L01/SceneInfo.xlsx`  
代码：`Assets/Scripts/Data/LevelConfig.cs` → `LevelConfig`

| 字段                                                                                                 | L01 现值                             | 作用                                 | 状态                                                                                                             |
| -------------------------------------------------------------------------------------------------- | ---------------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `id`                                                                                               | 1                                  | 关卡 id（主键）                          | ✅                                                                                                              |
| `RoundList`                                                                                        | `1..20, 401..405`（25 个）            | 本关回合顺序 → `TBRoundData`             | ✅ 决定波数与顺序                                                                                                      |
| `mapId`                                                                                            | 1                                  | 棋盘 id → `TBLevelMap`               | ✅                                                                                                              |
| `name`                                                                                             | `关卡 1`                             | 关卡名（多语言经 `Localization.LevelName`） | ✅ 展示                                                                                                           |
| `initialGold`                                                                                      | 100                                | 进关初始金币                             | ✅                                                                                                              |
| `initialHp`                                                                                        | 10                                 | 进关初始生命（= 可漏怪数上限）                   | ✅                                                                                                              |
| `waveIntervalMs`                                                                                   | 2500                               | **注释说"回合间准备时间"**                   | ❌ **死字段**：`LevelConfig.WaveIntervalSec` 封装了它，但**全工程无调用点**；实际节奏由 `LevelRules.autoNextRoundDelayMs`（L01=10000）控制 |
| `difficulty`                                                                                       | 1                                  | 难度标签                               | ⚠️ 仅选关界面显示（`SelectView` / `LevelDetailView`），不参与任何数值计算                                                         |
| `desc`                                                                                             | 见原表                                | 备注                                 | ⚠️ 仅备注                                                                                                         |
| `nightSightMs`                                                                                     | 0                                  | 预留视野遮蔽                             | ❌ 死字段，未读取                                                                                                      |
| `CameraPosition` / `CameraRotration` / `MapName` / `EenemyPosition` / `MapPosition` / `PointScale` | 18,32,2 / 60,0.2,0 / MapModel1 / … | 3D 时代遗留                            | ❌ 全部未读取（2D 固定视角）                                                                                               |



---

## 2. 本关玩法规则 `LevelRules.xlsx`（每关 1 行，2026-10-30 从 Global 拆出）

文件：`Luban/Config/Datas/Levels/L01/LevelRules.xlsx`  
代码：`Assets/Scripts/Data/GlobalConfig.cs` → `GlobalConfig`（属性名不变，数据源换成"本关行"）

| 字段                        | L01 现值 | 作用                          | 状态                                                                                               |
| ------------------------- | ------ | --------------------------- | ------------------------------------------------------------------------------------------------ |
| `cellSize`                | 1      | 棋盘格子边长（世界单位）                | ✅ 直接影响棋盘/射程/怪物尺寸观感                                                                               |
| `boardOriginPadding`      | 1      | 棋盘相对相机中心留白                  | ❌ **死字段**：`GlobalConfig` 暴露了，但 `GameFlowManager.InitLevel` 的 origin 直接用 `-Cols*cellSize/2`，未使用本值 |
| `defaultReward`           | 5      | 未配 reward 时的击杀奖励            | ❌ **死字段**：2026-10-29 改小数掉落时已取消回退（`EnemyConfig.Reward` 直接返回表值）                                    |
| `defaultDamageToPlayer`   | 1      | 未配漏怪伤害时的兜底                  | ✅ 兜底（L01 表里都有值，实际不触发）                                                                            |
| `defaultBodyRadius`       | 0.4    | 未配受击半径时的兜底                  | ✅ 兜底                                                                                             |
| `defaultSearchIntervalMs` | 100    | 未配索敌间隔时的兜底                  | ✅ 兜底                                                                                             |
| `autoNextRoundDelayMs`    | 10000  | 一波结束后自动开下一波的延迟；0=手动         | ✅ **这是真正的波间节奏开关**                                                                                |
| `autoStartRoundDelayMs`   | 0      | 进关后自动开第一波延迟                 | ✅                                                                                                |
| `sellRefundRate`          | 1      | 卖塔返还比例（乘在 `min(售价,累计投入)` 上） | ✅                                                                                                |
| `artFaceLeft`             | 1      | 怪物美术默认朝左                    | ✅ 仅影响翻转方向                                                                                        |
| `showDamageText`          | 1      | 伤害飘字总开关                     | ✅                                                                                                |
| `damageTextThrottleMs`    | 120    | 同一怪两次飘字最小间隔                 | ✅                                                                                                |
| `shakeAmplitude`          | 0.12   | 震屏幅度（**仅漏怪允许震**）            | ✅                                                                                                |
| `shakeDurationMs`         | 180    | 震屏时长                        | ✅                                                                                                |

---

## 3. 波次与出怪

### 3.1 `RoundData.xlsx`（一关 25 行 ≈ 25 波）

文件：`Luban/Config/Datas/Levels/L01/RoundData.xlsx`  
代码：`Assets/Scripts/Data/WaveConfig.cs` → `RoundConfig`

| 字段            | L01 现值                            | 作用                       | 状态                                  |
| ------------- | --------------------------------- | ------------------------ | ----------------------------------- |
| `id`          | 1..20, 401..405                   | 回合 id（主键）                | ✅                                   |
| `EnemyIndexs` | 每行 1 个波次 id                       | 本回合包含的波次 → `TBEnemyList` | ✅ 当前**每回合只放 1 组**；放多个可实现"同回合多路同时出怪" |
| `interval`    | 全 0                               | 本回合相对上一回合的准备延迟（ms）       | ✅ 进 `WaveManager` 时间轴起点             |
| `name`        | `第 N/25 波`                        | 展示名                      | ⚠️ 仅展示                              |
| `rewardGold`  | `36,36,36,36,84,43,…,93`（合计 1305） | **每波通关奖励金币**             | ✅ 唯一的"波次金币"入口                       |

> 规律观察：每 5 波一个高点（84/87/90/93），其余 36→49 递增；这是当前唯一的"节奏感"来源。

### 3.2 `EnemyList.xlsx`（一波敌人的编组，25 行）

文件：`Luban/Config/Datas/Levels/L01/EnemyList.xlsx`  
代码：`WaveManager.BeginRound` / `WaveGroupConfig`

| 字段              | L01 现值           | 作用                   | 状态                       |
| --------------- | ---------------- | -------------------- | ------------------------ |
| `id`            | 1..20, 401..405  | 波次 id                | ✅                        |
| `EnemyIndexs`   | 31 → 726 只（逐波递增） | 本波怪 id 列表（按顺序生成）     | ✅ **改出怪数量/顺序/配比就改这里**    |
| `interval`      | 全 0              | 本组相对回合开始的延迟（ms）      | ✅                        |
| `enemyInterval` | 280 → 126（逐波递减）  | **波内相邻两只怪的生成间隔（ms）** | ✅ 这是"出怪密度"的总开关           |
| `desc`          | 见原表              | 备注（含 EHP / 历史调参记录）   | ⚠️ 仅备注，但**是排查数值来源的最佳线索** |

---

## 4. 怪物 `EnemyData.xlsx`（L01 共 106 条）

文件：`Luban/Config/Datas/Levels/L01/EnemyData.xlsx`  
代码：`Assets/Scripts/Data/EnemyConfig.cs`；`BaseEnemy.Init` 里 `TotalHp = CurrentHp = cfg.Hp`

| 字段                           | L01 范围 / 现值            | 作用                         | 状态                                               |
| ---------------------------- | ---------------------- | -------------------------- | ------------------------------------------------ |
| `id`                         | 5000000 起，按波次变体编号      | 怪物变体 id（每波一套）              | ✅                                                |
| `hp`                         | 7.40 ~ 2379.27（均值 361） | 血量                         | ✅ **无任何倍率层，改多少就是多少**                             |
| `speed`                      | 0.777 ~ 1.140（格/秒）     | 移动速度                       | ✅                                                |
| `armor`                      | 0 ~ 0.22               | 护甲减伤（最终伤害 = 伤害 ×(1-armor)） | ✅                                                |
| `reward`                     | 0.152 ~ 2.000（小数）      | 击杀金币（小数累加，满 1 入账）          | ✅                                                |
| `damageToPlayer`             | 1 或 2                  | 漏怪扣血                       | ✅                                                |
| `bodyRadius`                 | 全 0.4                  | 受击半径（索敌/命中）                | ✅                                                |
| `scale`                      | 全 0.5                  | 显示缩放                       | ✅ 观感                                             |
| `isFlying`                   | 0=85 条 / 1=21 条        | **地面/空中唯一判定**              | ✅ 塔的 `canAttackAir` 与 `airDamageScale` 都认这一列     |
| `type`                       | 1=69 / 3=16 / 4=21     | 1 普通 / 3 精英 / 4 飞行         | ✅                                                |
| `resName` / `animController` | 见原表                    | 预支体 / 动画家族                 | ✅ 资源绑定                                           |
| `interval`                   | 全 100                  | 注释写"出现间隔"                  | ❌ **死字段**：实际间隔取 `EnemyList.enemyInterval`，本列无调用点 |
| `levelId`                    | 全 1                    | 所属关卡                       | ✅ 交叉引用自检用（跨关引用会被拦）                               |
| `name` / `desc`              | 见原表                    | 名字 / 备注                    | ⚠️ 备注                                            |

**L01 怪种构成**：Chicken 25、Larva 23、Crawler 21、Bat 21（飞行）、Scarab 15、Rat 1。

---

## 5. 防御塔 `TowerInfo.xlsx`（3 型 × 3 级 = 9 行）

文件：`Luban/Config/Datas/Levels/L01/TowerInfo.xlsx`  
代码：`Assets/Scripts/Data/TowerConfig.cs`

| 字段                           | L01 现值（三型三级）                                  | 作用                             |
| ---------------------------- | --------------------------------------------- | ------------------------------ |
| `type`                       | 1 普通 / 2 火力 / 3 减速                            | 塔型（决定行为分支）                     |
| `level`                      | 1 / 2 / 3                                     | 等级                             |
| `radius`                     | 普通 2/2.15/2.3；火力 2/2.1/2.2；减速 2.2/2.35/2.5    | 攻击半径（格）                        |
| `power`                      | 普通 6/9/13；火力 16/24/33；减速 0                    | 单次伤害                           |
| `CD`                         | 普通 450/430/410；火力 1000/950/900；减速 250/240/230 | 攻击间隔（ms）；减速塔=光环节拍              |
| `prices`                     | 普通 32/28/40；火力 44/40/55；减速 30/40/60           | **增量价**（建造价 / 升级价 / 升级价）       |
| `sellPrice`                  | 普通 22/42/70；火力 30/58/97；减速 21/49/91           | 出售上限（实际 = `min(售价,累计投入)×返还比例`） |
| `upgradeTo`                  | 1002/1003/0 等                                 | 升级链（0=满级）                      |
| `targetMode`                 | 全 0                                           | 0 路径最前 / 1 最近 / 2 最高血          |
| `searchIntervalMs`           | 全 100                                         | 索敌节流                           |
| `rotateSpeed`                | 全 360                                         | 炮管转向（度/秒）                      |
| `canAttackAir`               | 普通 1 / 火力 0 / 减速 1                            | 能否打飞行                          |
| `airDamageScale`             | 普通 1/1/**1.1**；其余 1                           | 仅对飞行单位的伤害倍率                    |
| `effectType` / `effectValue` | 火力 3（AOE）；减速 1 + 0.3/0.4/0.5                  | AOE / 减速比例                     |
| `bulletId`                   | 普通 101；火力 102/106/107；减速 0                    | 关联子弹表                          |

---

## 6. 子弹 `BulletData.xlsx`（6 行）

文件：`Luban/Config/Datas/Levels/L01/BulletData.xlsx`

> **重要前提**：2026-10-31 真实弹体系统已整体删除，塔改为"即时命中/落点结算"。  
> 因此这张表**只剩 3 个字段真正生效**。

| 字段                                    | 现值                         | 状态               |
| ------------------------------------- | -------------------------- | ---------------- |
| `aoeRadius`                           | 0 / 0.75 / 0.9 / 1.05      | ✅ 火力塔范围结算的唯一来源   |
| `effectType`                          | 0 / 1 减速 / 2 持续伤害 / 3 范围伤害 | ✅                |
| `effectValue`                         | 0 / 0.5 / 6                | ✅（减速比例；DOT 每秒伤害） |
| `speed`                               | 全 12                       | ❌ 弹体已删，无调用       |
| `hitRadius`                           | 全 0.25                     | ❌ 同上             |
| `lifeTimeMs`                          | 全 3000                     | ❌ 同上             |
| `scale` / `name` / `resName` / `desc` | —                          | ❌ 展示/资源，已无弹体     |

---

## 7. 棋盘 `LevelMap.xlsx`（L01 1 行）

| 字段              | 现值                                                        | 作用                                                        |
| --------------- | --------------------------------------------------------- | --------------------------------------------------------- |
| `cols` × `rows` | 13 × 7                                                    | 棋盘尺寸（**改这里会改变整关走位与塔位容量**）                                 |
| `cells`         | `.............` ×3 + `S...........E` + `.............` ×3 | 地形字符：`S` 起点 / `E` 终点 / `.` 可建造 / `#` 障碍 / `X` 空洞 / `P` 装饰 |

---

## 8. 全局常数 `Global.xlsx`（单行，id=1）

> 表头注释原文：**"本表是全工程【唯一的常数配置表】（单行，id 固定 1）—— 所有新增的全局常数都加在这里，不要再新建第二张常数表"**。  
> 这句话是你后续加"每 N 关"类字段最权威的落点依据。

| 字段                     | 现值  | 作用           | 状态                                                                       |
| ---------------------- | --- | ------------ | ------------------------------------------------------------------------ |
| `enemyPoolSize`        | 256 | 怪物对象池初始容量    | ✅                                                                        |
| `bulletPoolSize`       | 128 | 子弹对象池容量      | ✅ 弹体已删，实际无用                                                              |
| `maxEnemyAlive`        | 200 | 同屏怪物上限（性能保护） | ✅                                                                        |
| `targetFrameRate`      | 60  | 目标帧率         | ❌ **失效**：`GlobalConfig.TargetFrameRate` 已改为读 `FrameRatePolicy`，表值不覆盖运行策略 |
| `deathRecycleDelayMs`  | 600 | 死亡动画后回收延迟    | ✅                                                                        |
| `checkOfflinePerFrame` | 1   | 每帧最多重算路径次数   | ✅                                                                        |
| `showDebugLog`         | 1   | 战斗自检日志       | ✅                                                                        |

---

## 9. 代码里写死、目前**不能**配置的数值（可考虑提为字段）

| 位置                          | 常量                                     | 值               | 影响              |
| --------------------------- | -------------------------------------- | --------------- | --------------- |
| `BaseTower.cs:142`          | `SlowDurationSec`                      | 2s              | 减速持续时间          |
| `BaseTower.cs:143`          | `DotDurationSec`                       | 3s              | 持续伤害总时长         |
| `BaseTower.cs:132`          | `AuraPulseSec`                         | 0.15s           | 减速光环施加节拍        |
| `BaseTower.cs:129`          | `SlowAuraLingerSec`                    | 0.1s            | 离开光环后的残留        |
| `BaseTower.cs:121`          | `MinRotateStep`                        | 0.5°            | 炮管最小转向步长        |
| `BaseTower.cs:149/151`      | `RecoilDistance` / `RecoilDurationSec` | 0.07 / 0.09s    | 后坐力表现           |
| `BaseEnemy.cs:156`          | `ArriveThreshold`                      | 0.08 格          | 判定"到达终点"的距离     |
| `BaseEnemy.cs:102`          | `FlashDurationSec`                     | 0.08s           | 受击闪白            |
| `PlayerDataManager.AddGold` | 取整规则                                   | 满 1 才入账         | 小数金币的累计口径       |
| `GameClock.cs:39`           | `Tiers`                                | `{1,2,3}`       | 倍速档位（写死数组）      |
| `SaveManager.cs:58`         | `MaxStars`                             | 5               | 通关星级（评级下线后固定 5） |
| `SaveManager.IsUnlocked`    | 解锁规则                                   | 前一关通关           | 无金币/星级门槛        |
| `CameraController.cs:22`    | `DefaultZ`                             | -10             | 相机 Z            |
| `BoardView.cs:19`           | `CellFillRatio`                        | 0.94            | 格子视觉填充比         |
| `WaveManager`               | 默认波内间隔                                 | 200ms（表为 0 时兜底） | 出怪间隔兜底          |

---

## 10. "调了没反应"的字段汇总（重点避坑）

以下字段在表里存在、Excel 也能改，但**代码根本不读**：

1. `SceneInfo.waveIntervalMs`（L01=2500）→ 真正的波间节奏是 `LevelRules.autoNextRoundDelayMs`
2. `SceneInfo.nightSightMs`
3. `SceneInfo.CameraPosition` / `CameraRotration` / `MapName` / `EenemyPosition` / `MapPosition` / `PointScale`
4. `LevelRules.boardOriginPadding`
5. `LevelRules.defaultReward`
6. `EnemyData.interval`（实际用 `EnemyList.enemyInterval`）
7. `BulletData.speed` / `hitRadius` / `lifeTimeMs` / `scale`
8. `Global.targetFrameRate`（被 `FrameRatePolicy` 覆盖）
9. `Global.bulletPoolSize`（弹体已删）

---

## 11. 如果要加"每 N 关"类字段：推荐落点与改动面

### 11.1 落点选择

| 方案        | 位置                    | 适合什么                           | 代价                                       |
| --------- | --------------------- | ------------------------------ | ---------------------------------------- |
| **A（推荐）** | `Global.xlsx` 新增列     | 跨关统一规则（每 4/5 关的金币、地面/空中 HP 比例） | 需重跑 Luban；`GlobalConfig` 加属性；在进关/生成怪时应用  |
| B         | `LevelRules.xlsx` 新增列 | 只对某一关生效的特殊规则                   | 30 张表都要补列（Luban 要求列一致），维护成本高             |
| C         | 新建 `Progression.xlsx` | 未来要做"章节/赛季"多套曲线                | 与 `Global.xlsx` 表头注释"不要再新建第二张常数表"冲突，需你点头 |

### 11.2 必须一起改的链路

1. **Luban**：改 `Global.xlsx` 表头三行（`##` / `##type` / `##` 注释）→ 跑 `Luban/Config/gen.bat` → 重新生成 `Assets/Gen/Global.cs` 与 `Assets/ConfigJson/tbglobal.json`
2. **代码读取**：`GlobalConfig` 新增属性（保持"缺表不崩"的默认值风格）
3. **应用点**：
   - HP 比例 → 只能落在 `EnemyManager` 生成怪 / `BaseEnemy.Init`（当前是 `CurrentHp = cfg.Hp`，没有中间层）
   - 金币 → 落在 `PlayerDataManager.InitFromLevel`（初始金币）或 `GameFlowManager.FinishRound/CompleteVictory`（奖励）
4. **口径风险**：
   - 局内续玩快照存的是"绝对金币/生命"，若中途改了倍率，老快照会和新规则混在一起
   - `EnemyList.desc` 里的 EHP 是手工算的历史值，加运行时倍率后**全部对不上**，需要重新标定基准
   - 现有 L02–L30 的 hp 已经是手调结果；再加一层倍率 = **在现值上再乘一遍**，不是"从基准放大"

---

## 12. 需要你先确认的 4 件事


1. **语义**："每四关/每第五关"是指"第 4、8、12…关各乘一次"，还是"每过 4 关累积乘一次"（第 8 关乘两次）？
2. **叠加方式**：第 20 关同时命中"每 4 关"和"每 5 关"时，是**两个比例相乘**、**相加**，还是**取较大值**？
3. **基准**：比例乘在"当前表里的 hp"上，还是"先回退到一个基准 hp 再乘"？（后者要先把 L02–L30 的手调结果还原，工作量大）
4. **金币口径**：当前没有跨关钱包，"通关后加金币""每 5 关加金币"最终加到哪——**下一关的初始金币**？还是仅结算界面展示？

---

## 附：L01 量化基线（便于后续调参对照）

| 指标 | 值 |
|---|---|
| 波数 | 25 |
| 波次奖励合计 | 1305 金 |
| 初始金币 / 生命 | 100 / 10 |
| 怪物变体数 | 106（地面 85 / 空中 21） |
| 怪物 HP 区间 | 7.40 ~ 2379.27（均值 361） |
| 单只击杀金区间 | 0.152 ~ 2.000 |
| 出怪间隔 | 280ms（W1）→ 126ms（W23） |
| 每波怪数 | 31（W1）→ 726（W25） |
| 塔配置 | 3 型 × 3 级 = 9 行 |
| 棋盘 | 13 × 7 |
