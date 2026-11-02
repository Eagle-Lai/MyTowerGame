# 关卡数值调节字段 —— 设计与实施计划

> 日期：2026-11-02
> 目标：在**每关一份**的关卡配置里增加一组"数值调节旋钮"，让策划改一关的强度时不必逐条改 `EnemyData`（L01 106 条、L30 454 条）
> 状态：**设计稿，未动表、未改代码**

---

## 1. 一句话方案

在 `Levels/Lxx/LevelRules.xlsx` 末尾追加一组字段（默认值全部 = 不改变现状），
由 `Configs.GetEnemy()` 在生成怪物配置时按当前关的规则做缩放；
`LevelRules` 已经是"每关一份"的表，天然满足"跟着关卡配置走"。

**为什么不是 `Global.xlsx`**：那是全工程单行表，30 关共用一份，改一处影响所有关。
你要的是"调节每个关卡的数值"，落点必须是每关一份的表。

---

## 2. 关键设计决策（先对齐，再动手）

### D1. "每四关 / 每第五关"怎么表达 —— 推荐"每关一个总倍率"

表里**只放一个** `groundHpScale` / `airHpScale`，不写 `groundHpScalePer4` 这种字段。

节奏由你在 30 行里填值决定：

| 关卡 | groundHpScale | airHpScale | 你的叫法 |
|---|---|---|---|
| L01 | 1.00 | 1.00 | 基准 |
| L02 | 1.05 | 1.00 | |
| L03 | 1.08 | 1.00 | |
| L04 | 1.10 | 1.02 | ← "每四关"的地面比例 |
| L05 | 1.20 | 1.05 | ← "每第五关"的地面/空中比例 |
| L08 | 1.32 | 1.08 | ← 又是"每四关" |
| L10 | 1.45 | 1.12 | ← 又是"每第五关" |

**理由**：
- 代码不需要知道"4"或"5"，规则全在表里，改节奏不用改代码
- 每关的最终倍率是绝对值，可预测、可单独回滚
- 现有 L02–L30 的 `hp` 已经是手调结果；如果让代码按"每 4 关累积乘一次"，会**在手调值上再叠一层**，最终值不可控

**不推荐的做法**：在表里放 `hpScalePer4` + `hpScalePer5` 两个字段，由代码算 `floor((levelId-1)/4)` 次幂。
问题：① 需要额外定义"基准关"；② 第 20 关同时命中 4 和 5，叠加方式还得再定；③ 与现有手调值双重放大。

### D2. 缩放作用在"读取时"，不写回表

`EnemyData.hp` 保持原值不动，缩放发生在 `EnemyConfig` 包装层：

```
EnemyData.hp (表值)  ×  LevelRules.groundHpScale/airHpScale  =  实际血量
```

好处：随时把倍率改回 1.0 就完全复原；不会污染原表；`git diff` 只看到 LevelRules 一列。

### D3. 地面/空中只认 `isFlying`

`EnemyData.isFlying`（0/1）是工程里唯一的地空判定口径（塔的 `canAttackAir`、`airDamageScale` 都认它）。缩放沿用同一口径，不新增判断。

### D4. 图鉴不受缩放影响

`MonsterCodexView` 里 `new EnemyConfig(raw)` 用的是原始构造函数，显示表值。
战斗路径 `Configs.GetEnemy(id)` 返回带缩放的实例。两者互不干扰。

### D5. 金币字段的落点（**需要你选**）

当前架构：`PlayerDataManager.Gold` 是**局内**金币，`InitFromLevel` 时被重置，结算后不保留，也没有跨关钱包。

所以"通关后增加的金币"必须选一个去处：

| 方案 | 做法 | 改动 | 玩家感知 |
|---|---|---|---|
| **A（推荐）纯配置** | 不改代码。想让"第 5 关通关后多给 50"，就直接在 **L06 的 `initialGoldBonus` 填 50** | 仅表 | 进第 6 关时初始金币多 50 |
| B 通关结算奖励 | `LevelRules.clearGoldBonus`，通关时累加到 `kv_store` 的 `carry/gold`，下次进关叠加并清零 | 表 + 代码 + 存档键 + 结算 UI | 结算界面显示"+50 金币已存入下一关" |
| C 跨关钱包 | 新增持久金币账户，局内金币与账户打通 | 大改经济模型 | 需要重新设计所有金币入口 |

A 零风险、零存档改动；B 有反馈但多一条持久化链路（要考虑重复领取、退出未落盘）；C 不建议在本轮做。

**默认按 A 规划**，`clearGoldBonus` 先不加。

---

## 3. 字段定义（第一版，7 个）

追加到 `LevelRules.xlsx` 末尾（`shakeDurationMs` 之后），三行表头都要填。

| # | 字段名 | 类型 | 默认 | 语义 | 空值行为 |
|---|---|---|---|---|---|
| 1 | `groundHpScale` | float | 1 | 地面怪 HP 乘数 | ≤0 视为 1 |
| 2 | `airHpScale` | float | 1 | 空中怪 HP 乘数 | ≤0 视为 1 |
| 3 | `groundSpeedScale` | float | 1 | 地面怪速度乘数 | ≤0 视为 1 |
| 4 | `airSpeedScale` | float | 1 | 空中怪速度乘数 | ≤0 视为 1 |
| 5 | `killGoldScale` | float | 1 | 击杀金币乘数（不分地空） | ≤0 视为 1 |
| 6 | `initialGoldBonus` | int | 0 | 本关初始金币加成（加在 `SceneInfo.initialGold` 上） | 任意 |
| 7 | `waveGoldScale` | float | 1 | 每波奖励金币乘数（乘在 `RoundData.rewardGold` 上） | ≤0 视为 1 |

> 全部默认 1 / 0 → **加字段本身不会改变现有 30 关的任何数值**，这一点是硬要求。

### 可选扩展（第二版，先不做）

| 字段 | 语义 | 风险 |
|---|---|---|
| `groundArmorBonus` | 地面怪护甲加成（加法，clamp 0~1） | 低 |
| `airArmorBonus` | 空中怪护甲加成 | 低 |
| `spawnIntervalScale` | 出怪间隔乘数（>1 更慢） | 中：影响波次时长统计 |
| `enemyCountScale` | 每波怪数乘数 | 高：会破坏"预期出怪数"账本与结算统计，不建议 |

---

## 4. 生效链路（逐字段）

| 字段 | 读取位置 | 应用位置 | 现有代码 |
|---|---|---|---|
| `groundHpScale` / `airHpScale` | `Configs.Global.RawRules` | `EnemyConfig.Hp` | 现为 `return _d.Hp`；`BaseEnemy.Init` 里 `CurrentHp = cfg.Hp` |
| `groundSpeedScale` / `airSpeedScale` | 同上 | `EnemyConfig.Speed` | 现为 `return _d.Speed`；`BaseEnemy.Init` 里 `_speed = cfg.Speed` |
| `killGoldScale` | 同上 | `EnemyConfig.Reward` | 现为 `return _d.Reward`；`BaseEnemy.Die` 里 `AddGold(reward)` |
| `initialGoldBonus` | 同上 | `PlayerDataManager.InitFromLevel` | 现为 `Gold = level.InitialGold` |
| `waveGoldScale` | 同上 | `GameFlowManager.FinishRound` | 现为 `AddGold(rc.RewardGold)` |

### 4.1 `EnemyConfig` 改造（不改图鉴）

```csharp
// 原构造函数保留：图鉴等"看表值"的场景继续用
public EnemyConfig(EnemyData d) : this(d, 1f, 1f, 1f) { }

public EnemyConfig(EnemyData d, float hpScale, float speedScale, float rewardScale)
{
    _d = d;
    _hpScale = hpScale > 0f ? hpScale : 1f;
    _speedScale = speedScale > 0f ? speedScale : 1f;
    _rewardScale = rewardScale > 0f ? rewardScale : 1f;
}

public float Hp { get { return _d.Hp * _hpScale; } }
public float Speed { get { return _d.Speed * _speedScale; } }
public float Reward { get { return _d.Reward * _rewardScale; } }
```

### 4.2 `Configs.GetEnemy` 注入

```csharp
public static EnemyConfig GetEnemy(int id)
{
    EnemyData d = EnemyTable != null ? EnemyTable.GetOrDefault(id) : null;
    if (d == null) { /* 原错误日志 */ return null; }
    LevelRules r = Global != null ? Global.RawRules : null;
    if (r == null) return new EnemyConfig(d);

    bool air = d.IsFlying != 0;
    float hp = air ? r.AirHpScale : r.GroundHpScale;
    float spd = air ? r.AirSpeedScale : r.GroundSpeedScale;
    return new EnemyConfig(d, hp, spd, r.KillGoldScale);
}
```

### 4.3 金币

```csharp
// PlayerDataManager.InitFromLevel
int bonus = Configs.Global != null ? Configs.Global.InitialGoldBonus : 0;
Gold = Mathf.Max(0, level.InitialGold + bonus);

// GameFlowManager.FinishRound
float scale = Configs.Global != null ? Configs.Global.WaveGoldScale : 1f;
int reward = Mathf.RoundToInt(rc.RewardGold * scale);
if (reward > 0) { AddGold(reward); Tips(...); }
```

---

## 5. 表结构改动（30 张表）

### 5.1 手工步骤（单表）

1. 打开 `Levels/L01/LevelRules.xlsx`
2. 在 `shakeDurationMs` 右侧追加 7 列
3. 第 1 行（`##`）填字段名、第 2 行（`##type`）填类型、第 3 行（`##`）填中文注释
4. 第 4 行填默认值：`1,1,1,1,1,0,1`
5. 其余 29 张表重复

### 5.2 现实问题：30 张表 × 7 列 × 3 行 = 630 个单元格

Luban 对同一张表的多个输入文件要求**列结构完全一致**，不能先只改 L01。

但 `AGENTS.md` 明令："禁止任何脚本批量改写关卡配置表 `Levels/L01..L30/**`"。

**两个选项，需要你定**：

| 选项 | 做法 | 风险 |
|---|---|---|
| **甲（推荐）** | 授权一次性"只追加列、不碰任何现有单元格"的脚本；改完用 `git diff` 逐表核对，diff 里应当**只有新增列** | 需你明确授权这一次；脚本不写任何数值 |
| 乙 | 你手工改 30 张表 | 慢，但完全符合现行规则 |

### 5.3 导表

```
双击 Luban/gen_code_json.bat
```

产物：
- `Assets/Gen/LevelRules.cs`（新增属性）
- `Assets/ConfigJson/tblevelrules.json`（新增键，30 条）

> 注意：`gen_code_json.bat` 的产物自检列表里没有 `tblevelrules`，只看得到 8 张表。导完请手动确认 `tblevelrules.json` 时间戳已更新。

---

## 6. 代码改动清单

| 文件 | 改动 | 量级 |
|---|---|---|
| `Assets/Gen/LevelRules.cs` | 由 Luban 生成，不手改 | 自动 |
| `Assets/Scripts/Data/GlobalConfig.cs` | 新增 7 个属性（带默认值兜底） | +30 行 |
| `Assets/Scripts/Data/EnemyConfig.cs` | 加缩放构造 + 三个 getter 乘系数 | +15 行 |
| `Assets/Scripts/Data/Configs.cs` | `GetEnemy` 注入缩放 | +12 行 |
| `Assets/Scripts/Core/Manager/PlayerDataManager.cs` | `InitFromLevel` 加 `initialGoldBonus` | +3 行 |
| `Assets/Scripts/Game/GameFlowManager.cs` | `FinishRound` 波次奖励乘 `waveGoldScale` | +4 行 |

**不改**：存档结构、`SaveData` 版本、SQLite schema、星级/统计口径、UI 预制体。

---

## 7. 兼容性与副作用

| 项 | 结论 |
|---|---|
| 老存档 | 不受影响（倍率不进存档） |
| 局内续玩 | 快照只存塔阵/金币/生命，不存怪物血量；同一局内重新加载表才会变，正常流程不会 |
| 出怪账本 | 不受影响（只改属性，不改数量/顺序） |
| 结算统计 | 击杀数、漏怪数不变；`killGold` 统计会随倍率变化，属预期 |
| `EnemyList.desc` 的 EHP | **会失真**。建议在每个 `desc` 末尾追加一行 `tuning-20261102: groundHp x1.10, airHp x1.05`，便于回溯 |
| 图鉴 | 显示表值，不受影响 |
| 性能 | `GetEnemy` 每只怪调一次，只多 3 次乘法和 1 次字典查找，可忽略 |

---

## 8. 验证清单

1. **导表**：`tblevelrules.json` 的 30 条记录都含 7 个新键，值分别为 `1,1,1,1,1,0,1`
2. **编译**：Unity 无 `error CS`（`refresh_unity` → 读 `editor/state` → 读 console）
3. **默认值回归**：进 L01，任选一只怪，Console 打印 `Hp` 应与表值完全一致（倍率 1 生效）
4. **单关生效**：只把 L01 的 `groundHpScale` 改成 1.5，重进 L01，地面怪血量应 ×1.5、空中怪不变
5. **隔离性**：同一次改动下进 L02，血量应无变化（证明"跟着关卡走"）
6. **金币**：`initialGoldBonus=50` 时 L01 开局金币 = 150；`waveGoldScale=2` 时第 1 波奖励 72
7. **图鉴**：怪物图鉴数值不随倍率变化
8. **回滚**：把倍率改回 1，数值完全复原（表值未被写坏）

---

## 9. 分期

| 阶段 | 内容 | 产出 |
|---|---|---|
| P0 | 本设计确认（3 个待定项） | 你拍板 |
| P1 | 30 张表加列 + 导表 | `LevelRules.cs` / `tblevelrules.json` |
| P2 | 代码接入（6 个文件） | 编译通过 |
| P3 | L01 单关验证 + 隔离性验证 | Console 数值对照 |
| P4 | 文档与记忆更新 | 本文件补"实施结果"段 |

---

## 10. 待你拍板的 3 件事

1. **金币口径**：按 D5 的 **A（纯配置：在下一关 `initialGoldBonus` 填值）**，还是要 **B（通关结算奖励 + 跨关携带）**？
2. **字段范围**：只做第 3 节的 **7 个**，还是一并加入可选扩展（护甲加成 / 出怪间隔）？
3. **加列方式**：授权一次性"只追加列"的脚本（选项甲），还是你手工改 30 张表（选项乙）？

---

## 附：与你原始举例的对照

| 你的说法 | 本方案里的字段 | 填在哪 |
|---|---|---|
| 通关后增加的金币数值 | `initialGoldBonus`（方案 A）或 `clearGoldBonus`（方案 B） | 想让第 5 关通关后多给 → 填 L06（方案 A）/ L05（方案 B） |
| 每五关后添加的金币数值 | 同上 | L06、L11、L16…（方案 A） |
| 每四关地面怪 HP 比例 | `groundHpScale` | L04、L08、L12… |
| 每第五关地面怪比例 | `groundHpScale` | L05、L10、L15… |
| 每四关空中怪 HP 比例 | `airHpScale` | L04、L08、L12… |
| 每第五关空中怪 HP 比例 | `airHpScale` | L05、L10、L15… |
