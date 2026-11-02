# 执行提示词：关卡波次数值调节（WaveTuning）

> 生成日期：2026-11-02
> 适用工程：`D:\FishTestGame`（Unity 2022.3.62f3c1）
> 前置阅读：`AGENTS.md`、`Docs/LevelTuningInventory_2026-11-02.md`
> **口径作废声明**：`Docs/LevelTuningConfig_Plan_2026-11-02.md` 是按"每 4 关 / 每 5 关"的关卡进度写的，已被本文件取代，**不要按它执行**。
> 本提示词**只增加机制，不调整任何现有数值**。执行完成后，30 关的战斗数值必须与执行前逐项一致。

---

## 0. 一句话任务

新增一张 `WaveTuning` 配置表，按「关卡 × 波次类型（普通 / 困难）」提供怪物属性倍率与金币加成；把 `RoundData` 的 `waveType` 显式写死为 1/2；在怪物生成链路注入倍率。

**覆盖范围：`L01`–`L30` 全部 30 关，一关都不能少。**

---

## 1. 背景与现状

### 1.1 需求来源

用户要求："给关卡配置增加一组调节字段，用来分别控制**普通波次**和**困难波次**的地面/空中怪物 HP 比例，以及每波通关金币。"

### 1.2 概念定义（必须严格遵守）

- **每 5 波为一组**，前 4 波是**普通波**，第 5 波是**困难波**（坎）。
- 以 25 波为例：

| 波次序号 | 类型 |
|---|---|
| 1、2、3、4 | 普通 |
| **5** | **困难** |
| 6、7、8、9 | 普通 |
| **10** | **困难** |
| 11、12、13、14 | 普通 |
| **15、20、25** | **困难** |

- 波次类型**写死在配置数据里**（`RoundData.waveType`），不在代码里取模推断。
- `waveType` 只允许两个值：`1 = 普通`、`2 = 困难`。**不允许 0，不允许空**。

### 1.3 关键陷阱：波次序号 ≠ 表行顺序

实测 30 关：

- **L01、L02** 的 `RoundData.xlsx` 表内行顺序与 `SceneInfo.RoundList` 顺序**不一致**（例：L01 的 `RoundList` 是 `1..20, 401..405`，而表里 401 排在 13..20 之前）。
- L03–L30 两者一致。
- `RoundData.name` 字段格式统一为 `第 N/25 波`，且与 `RoundList` 位置**100% 吻合**（30 关、0 行偏差）。

**因此填写 `waveType` 必须依据 `name` 里的 N（或 `RoundList` 的位置），绝对不能按表行号。**

### 1.4 覆盖范围（硬要求，先看这条）

- 本改动必须覆盖 **`L01`–`L30` 全部 30 关**。
- 需求最初以"第一个关卡"举例，只是说明调节字段的用途，**不代表只改 L01**。
- "覆盖完整"的硬指标，缺一条都算没做完：

| # | 指标 | 精确值 |
|---|---|---|
| 1 | `WaveTuning.xlsx` 数据行 | **恰好 60 行** = 30 关 × (普通 + 困难)；`levelId` 1..30 每关 2 行，不缺不重 |
| 2 | `RoundData.xlsx` 已加列 | **恰好 30 个文件**，每个都有 `waveType` 列 |
| 3 | `waveType` 取值 | 30 关共 **750 行**（30 × 25）全部 ∈ {1, 2}，**不允许出现 0 / 空 / 其他值** |
| 4 | 困难波数量 | 每关 **5 行** `waveType=2`（第 5/10/15/20/25 波），共 150 行；其余 600 行为 1 |
| 5 | 导出的 `tbrounddata.json` | **恰好 750 条**记录，每条都带 `waveType` |

> 只做 L01、或只做"能跑通的两三关"，都按**未完成**处理。

### 1.5 现状事实

| 项 | 现状 |
|---|---|
| 关卡数 × 波数 | 30 × 25 = 750 波 |
| 怪物 HP | 直接在 `EnemyData.hp`，**无任何倍率层**（`BaseEnemy.Init` 里 `CurrentHp = cfg.Hp`） |
| 波次金币 | `RoundData.rewardGold`，逐波配置 |
| 波次类型 | 概念不存在 |
| 地空判定 | 唯一口径是 `EnemyData.isFlying`（0 地面 / 1 空中） |

---

## 2. 改动范围总览

### 2.1 配置表

| # | 文件 | 动作 |
|---|---|---|
| T1 | `Luban/Config/Datas/WaveTuning.xlsx` | **新建**，13 个字段 × 60 行数据（表头首格为 `##` 标记列） |
| T2 | `Luban/Config/Datas/__tables__.xlsx` | **加 1 行**表登记 |
| T3 | `Luban/Config/Datas/Levels/L01..L30/RoundData.xlsx` | **30 张全部**追加 1 列 `waveType`，数据填 1/2（缺一关都算未完成） |
| T4 | `Tools/fill_round_wavetype.py` | **新建**一次性填表工具 |

### 2.2 代码（11 个文件）

| # | 文件 | 动作 |
|---|---|---|
| C1 | `Assets/Scripts/Core/Res/ResTable.cs` | 登记 `tbwavetuning` |
| C2 | `Assets/Scripts/Data/Configs.cs` | 加载新表、建索引、`GetWaveTuning`、`GetEnemy` 加重载 |
| C3 | `Assets/Scripts/Data/WaveConfig.cs` | `RoundConfig` 加 `WaveType` |
| C4 | `Assets/Scripts/Data/EnemyConfig.cs` | 加 `WaveTuning` 构造，5 个 getter 缩放 |
| C5 | `Assets/Scripts/Enemy/EnemyManager.cs` | `Spawn` 加 `isHardWave` 参数 |
| C6 | `Assets/Scripts/Round/WaveManager.cs` | `BeginRound` 加 `isHardWave`，`Tick` 透传 |
| C7 | `Assets/Scripts/Game/GameFlowManager.cs` | 判定困难波、波次金币加成 |
| C8 | `Assets/Scripts/Enemy/BaseEnemy.cs` | 漏怪震幅改用基础伤害 |
| C9 | `Assets/Editor/LubanExporter.cs` | 必备表列表加 `tbwavetuning` |
| C10 | `Assets/Editor/M0SetupWizard.cs` | 同上 |
| C11 | `Assets/Scripts/Data/Configs.EditorCandidates.cs` | 候选表加载/回滚/索引重建补 `tbwavetuning`（**不改会断平衡测试**） |

### 2.3 生成物（禁止手改）

`Assets/Gen/WaveTuning.cs`、`Assets/Gen/TBWaveTuning.cs`、`Assets/Gen/RoundData.cs`、`Assets/Gen/Tables.cs`、`Assets/ConfigJson/tbwavetuning.json`、`Assets/ConfigJson/tbrounddata.json`

### 2.4 明确不改

- `LevelRules.xlsx` 及其 15 个字段（**一个都不加**）
- `EnemyData` / `EnemyList` / `SceneInfo` / `LevelMap` / `TowerInfo` / `BulletData` 的任何现有值
- 存档结构、`SaveData.CurrentVersion`、SQLite schema
- UI 预制体、图鉴显示逻辑
- 震屏规则（只有漏怪震，震幅口径不变）

---

## 3. 配置表改动

### 3.1 新建 `Luban/Config/Datas/WaveTuning.xlsx`

单 Sheet，三层表头 + 60 行数据。

**第 1 行（字段名）**

```
## | id | levelId | waveType | groundHpScale | airHpScale | groundSpeedScale | airSpeedScale | groundArmorBonus | airArmorBonus | killGoldScale | leakDamageBonus | waveGoldBonus | desc
```

**第 2 行（类型）**

```
##type | int | int | int | float | float | float | float | float | float | float | int | int | string
```

**第 3 行（注释）**

```
## | 主键 1..60 | 关卡 id → TBSceneInfo | 波型 1=普通 2=困难 | 普通/困难：地面怪HP倍率 | 空中怪HP倍率 | 地面怪速度倍率 | 空中怪速度倍率 | 地面怪护甲加成（减伤比例，加法） | 空中怪护甲加成 | 击杀金币倍率 | 漏怪额外扣血 | 波次通关额外金币 | 备注
```

**第 4–63 行（数据）**

> **必须填满 60 行：`levelId` 1..30 每关两行，不允许只填 L01、也不允许跳关。** 每行都要有完整字段，不能留空。

- `id`：1..60
- `levelId`：1..30，每关两行
- `waveType`：每关第 1 行 = 1，第 2 行 = 2
- `groundHpScale` / `airHpScale` / `groundSpeedScale` / `airSpeedScale` / `killGoldScale`：全部填 `1`
- `groundArmorBonus` / `airArmorBonus`：全部填 `0`
- `leakDamageBonus` / `waveGoldBonus`：全部填 `0`
- `desc`：`L01 普通` / `L01 困难` … `L30 困难`
- 第 64 行（数据行之后的第一个空行）：可留空

**行号对照**

| 数据行 | id | levelId | waveType |
|---|---|---|---|
| r4 | 1 | 1 | 1 |
| r5 | 2 | 1 | 2 |
| r6 | 3 | 2 | 1 |
| r7 | 4 | 2 | 2 |
| … | … | … | … |
| r62 | 59 | 30 | 1 |
| r63 | 60 | 30 | 2 |

### 3.2 `__tables__.xlsx` 追加一行

在现有表登记的最后一行（`TBLevelRules` 那行之后）追加：

| 列 | 值 |
|---|---|
| `##var` | `每关每波型数值调节（2026-11-02）` |
| `full_name` | `TBWaveTuning` |
| `value_type` | `WaveTuning` |
| `define_from_file` | `True` |
| `input` | `WaveTuning.xlsx` |
| `index` | `id` |
| `mode` | 留空 |
| `group` | 留空 |
| `comment` | `普通/困难波次的属性倍率与金币加成；主键 id，代码按 levelId+waveType 建索引` |
| 其余列 | 留空 |

> **不要用联合主键**（`levelId+waveType`），避免依赖 Luban 多主键 API 的版本差异。用自增 `id` + 代码内索引。

### 3.3 30 张 `RoundData.xlsx` 追加 `waveType` 列

- 位置：现有最后一列 `rewardGold` 的右侧
- 第 1 行：`waveType`
- 第 2 行：`int`
- 第 3 行：`波型 1=普通 2=困难（工具统一填写，禁止留空/填0）`
- 第 4 行起：按 **`name` 里的 N** 填 `2 if N % 5 == 0 else 1`

**不允许用表格行号推断**（L01/L02 会错）。

### 3.4 工具 `Tools/fill_round_wavetype.py`

**职责**：一次性、幂等地给 30 张 `RoundData.xlsx` 补 `waveType` 列并填值。

**命令行**

```
python Tools/fill_round_wavetype.py --dry-run              # 只打印报告，不写盘
python Tools/fill_round_wavetype.py --apply                # 写入（自动备份）
python Tools/fill_round_wavetype.py --verify               # 逐格对比 .bak，确认只改了 waveType
python Tools/fill_round_wavetype.py --apply --every 5      # 默认就是 5，可改
```

**实现要求**

0. **必须遍历 30 个关卡目录（`L01`–`L30`），一个都不能漏。** 任何一个目录缺失、文件打不开、交叉校验失败，**整批 abort、不写盘**，不允许"跳过继续"或"只处理前几关"。
1. 解析 `D:/FishTestGame/Luban/Config/Datas/Levels/L01..L30/RoundData.xlsx`。
2. 对每张表：
   - 读 `SceneInfo.xlsx` 的 `RoundList` 作为**权威波次顺序**；
   - 读 `RoundData` 每行 `name`，正则 `第\s*(\d+)\s*/` 取 N；
   - **交叉校验**：`name` 里的 N 必须与该 `id` 在 `RoundList` 中的位置一致；不一致直接 abort 并报错；
   - `waveType = 2 if N % every == 0 else 1`。
3. 若表里没有 `waveType` 列：在最后一列右侧追加 3 行表头（字段名 / `int` / 注释）。
4. 若已有 `waveType` 列：只覆盖该列的值，**不触碰任何其他列**。
5. `--apply` 前把原文件复制为 `RoundData.xlsx.bak_20261102_wavetype`。
6. `--verify`：逐单元格比较 `.bak` 与当前文件，**除 `waveType` 列外任何一格不同就报错退出 1**。
7. 输出报告（每关一行）：`L01 数据行=25 困难波=[第5/10/15/20/25波] 普通=20 困难=5`；**末尾必须打印汇总**：`处理关卡=30/30 总行数=750 困难波=150`。少一关或行数不对就退出 1。
8. 脚本头部注释写明：
   - 本次批量写表是用户 2026-11-02 明确授权的**单次、单列**操作；
   - 只写 `waveType` 一列，不改任何现有数值；
   - 与 `AGENTS.md` 的"禁止脚本批量改写关卡表"的关系：授权仅限本次、仅限该列。

**伪代码**

```python
EVERY = 5
LEVELS = [f"L{i:02d}" for i in range(1, 31)]

for level in LEVELS:
    order = read_sceneinfo_roundlist(level)          # [1,2,...,20,401,...,405]
    rows  = read_rounddata(level)                    # 按表行顺序
    pos   = {rid: i + 1 for i, rid in enumerate(order)}
    for r in rows:
        n = parse_name(r["name"])                    # "第 21/25 波" -> 21
        assert pos[r["id"]] == n, f"{level} id={r['id']} name/顺序不一致"
        r["waveType"] = 2 if n % EVERY == 0 else 1
    write_column(rows, "waveType")
```

### 3.5 导表

```
双击 Luban/gen_code_json.bat
```

导完必须确认：

- `Assets/ConfigJson/tbwavetuning.json` 存在、数组长度 **60**
- `Assets/ConfigJson/tbrounddata.json` 每条记录都有 `waveType`，值 ∈ {1,2}
- `Assets/Gen/WaveTuning.cs`、`TBWaveTuning.cs` 已生成
- `Assets/Gen/RoundData.cs` 多了 `WaveType` 属性

> 注意：`gen_code_json.bat` 的产物自检列表只覆盖 10 张表，**不含 `tbwavetuning`**。必须手动确认该 json 已更新（看时间戳）。

---

## 4. 代码改动

### C1. `Assets/Scripts/Core/Res/ResTable.cs`

在 `tblocalization` 那一行（第 40 行）之后追加：

```csharp
{ "tbwavetuning", new ResAddress(ResBundle.Config, "tbwavetuning", "Assets/ConfigJson/tbwavetuning.json") },
```

### C2. `Assets/Scripts/Data/Configs.cs`

**(a) 表实例**（第 40 行 `LocalizationTable` 之后）

```csharp
public static TBWaveTuning WaveTuningTable { get; private set; }
```

**(b) `ConfigKeys`**（第 127-132 行）

```csharp
private static readonly string[] ConfigKeys =
{
    "tbenemydata", "tbtowerinfo", "tbbulletdata", "tbenemylist",
    "tbrounddata", "tbsceneinfo", "tblevelmap", "tbglobal",
    "tblevelrules", "tblocalization", "tbwavetuning"
};
```

**(c) `LoadAsync` 内加载**（`RulesTable = LoadTable(...)` 之后）

```csharp
WaveTuningTable = LoadTable("tbwavetuning", n => new TBWaveTuning(n));
```

**(d) 索引**（`RulesByLevel` 构建之后）

```csharp
private static readonly Dictionary<int, WaveTuning> WaveTuningByKey = new Dictionary<int, WaveTuning>();
// key = levelId * 10 + waveType
```

```csharp
RebuildWaveTuningIndex();
```

方法定义：

```csharp
private static void RebuildWaveTuningIndex()
{
    WaveTuningByKey.Clear();
    if (WaveTuningTable == null || WaveTuningTable.DataList == null) return;
    foreach (WaveTuning t in WaveTuningTable.DataList)
    {
        WaveTuningByKey[t.LevelId * 10 + t.WaveType] = t;
    }
}
```

**(e) 访问器**（`GetEnemy` 附近）

```csharp
/// <summary>取某关某波型的调节参数；缺表/缺行返回 null（调用方按默认值 1/0 处理）。</summary>
public static WaveTuning GetWaveTuning(int levelId, bool isHardWave)
{
    WaveTuning t;
    return WaveTuningByKey.TryGetValue(levelId * 10 + (isHardWave ? 2 : 1), out t) ? t : null;
}
```

**(f) `GetEnemy` 加重载**（原第 427 行）

```csharp
public static EnemyConfig GetEnemy(int id, bool isHardWave = false)
{
    EnemyData d = EnemyTable != null ? EnemyTable.GetOrDefault(id) : null;
    if (d == null)
    {
        Debug.LogError(string.Format("[Config] TBEnemyData 中找不到 id={0}", id));
        return null;
    }
    return new EnemyConfig(d, GetWaveTuning(ActiveLevelId, isHardWave));
}
```

**(g) `LogSummary`（必须）**

在汇总字符串末尾加一行 `TBWaveTuning : {n} 条`，并补一个 `Count(TBWaveTuning t)` 重载。

**(h) `ValidateCrossReferences`（必须）**

追加一段：每关必须存在 `waveType=1` 与 `waveType=2` 两行，缺失记 warning：

```csharp
if (LevelTable != null && LevelTable.DataList != null)
{
    foreach (SceneInfo lv in LevelTable.DataList)
    {
        for (int wt = 1; wt <= 2; wt++)
        {
            if (!WaveTuningByKey.ContainsKey(lv.Id * 10 + wt))
            {
                sb.AppendLine(string.Format("  · 关卡 {0} 缺少 waveType={1} 的 WaveTuning 行（将按默认值 1/0 运行）", lv.Id, wt));
                problems++;
            }
        }
    }
}
```

### C3. `Assets/Scripts/Data/WaveConfig.cs`

`RoundConfig` 类内加：

```csharp
/// <summary>波型：1=普通 / 2=困难（数据显式填写；0 视为普通，仅作防御）</summary>
public int WaveType { get { return _r.WaveType; } }
```

### C4. `Assets/Scripts/Data/EnemyConfig.cs`

**整体替换为下面的结构**（保留原有注释与 `Raw` / `Id` / `Name` / `ResName` / `Type` / `Scale` / `BodyRadius` / `IsFlying` / `AnimController` / `Desc` 等成员）：

```csharp
private readonly EnemyData _d;
private readonly float _hpScale;
private readonly float _speedScale;
private readonly float _armorBonus;
private readonly float _rewardScale;
private readonly int _leakBonus;

/// <summary>看表值（图鉴等）：不缩放</summary>
public EnemyConfig(EnemyData d) : this(d, null) { }

/// <summary>战斗用：按当前关 + 当前波型缩放</summary>
public EnemyConfig(EnemyData d, WaveTuning t)
{
    _d = d;
    bool air = d.IsFlying != 0;
    _hpScale    = Positive(air ? t?.AirHpScale    : t?.GroundHpScale);
    _speedScale = Positive(air ? t?.AirSpeedScale : t?.GroundSpeedScale);
    _armorBonus = air ? (t != null ? t.AirArmorBonus    : 0f)
                      : (t != null ? t.GroundArmorBonus : 0f);
    _rewardScale = Positive(t?.KillGoldScale);
    _leakBonus   = t != null ? t.LeakDamageBonus : 0;
}

private static float Positive(float? v) { return v.HasValue && v.Value > 0f ? v.Value : 1f; }

public float Hp     { get { return _d.Hp * _hpScale; } }
public float Speed  { get { return _d.Speed * _speedScale; } }
public float Armor  { get { return Mathf.Clamp01(_d.Armor + _armorBonus); } }
public float Reward { get { return _d.Reward * _rewardScale; } }

/// <summary>不含波型加成的漏怪伤害（震屏分级用它，避免数值调节放大震动）</summary>
public int BaseDamageToPlayer
{
    get { return _d.DamageToPlayer > 0 ? _d.DamageToPlayer : Configs.Global.DefaultDamageToPlayer; }
}

public int DamageToPlayer { get { return BaseDamageToPlayer + _leakBonus; } }
```

> 不要把 `WaveTuning t` 存成字段：构造里已把 5 个值摊平成倍率，留着只会触发"未使用字段"告警。

### C5. `Assets/Scripts/Enemy/EnemyManager.cs`

第 60 行签名与第 63 行取值：

```csharp
public BaseEnemy Spawn(int enemyId, bool isHardWave = false)
{
    LastSpawnFailure = SpawnFailure.None;
    EnemyConfig cfg = Configs.GetEnemy(enemyId, isHardWave);
    // 其余不变
```

> 默认参数保证 `Assets/Editor/Balance/BalanceRuntimeSafetyVerifier.cs:136` 的 `Spawn(enemyId)` 不用改。

### C6. `Assets/Scripts/Round/WaveManager.cs`

字段区加：

```csharp
private bool _isHardWave;
```

`BeginRound`（第 66 行）：

```csharp
public void BeginRound(RoundConfig round, bool isHardWave = false)
{
    _isHardWave = isHardWave;
    // 其余不变
```

`Tick`（第 174 行）：

```csharp
BaseEnemy spawned = EnemyManager.Instance.Spawn(e.EnemyId, _isHardWave);
```

### C7. `Assets/Scripts/Game/GameFlowManager.cs`

**(a) 判定方法**（放在 `OnStartRequest` 之前）

```csharp
/// <summary>困难波判定：只认数据里的 waveType=2；0/1 一律按普通波。</summary>
private static bool IsHardWave(RoundConfig round)
{
    return round != null && round.WaveType == 2;
}
```

**(b) `OnStartRequest`（第 568 行）**

```csharp
_wave.BeginRound(round, IsHardWave(round));
```

**(c) `FinishRound` 金币结算（第 676-686 行）**

```csharp
if (_roundCursor < _roundIds.Count)
{
    RoundConfig rc = Configs.GetRound(_roundIds[_roundCursor]);
    if (rc != null)
    {
        bool isHard = IsHardWave(rc);
        WaveTuning tuning = Configs.GetWaveTuning(Level.Id, isHard);
        int bonus = tuning != null ? tuning.WaveGoldBonus : 0;
        int reward = rc.RewardGold + bonus;
        if (reward > 0)
        {
            PlayerDataManager.Instance.AddGold(reward);
            Tips(Localization.Get("Wave reward +{0} gold", reward)
                ?? string.Format("波次奖励 +{0} 金币", reward));
        }
    }
}
```

**(d) 统计口径（第 697-698 行）**

`completed.clearGold` 要记录**实际到账**：

```csharp
RoundConfig finishedRound = Configs.GetRound(_roundIds[_roundCursor - 1]);
int finishedBonus = finishedRound != null
    ? (Configs.GetWaveTuning(Level.Id, IsHardWave(finishedRound))?.WaveGoldBonus ?? 0)
    : 0;
completed.clearGold = finishedRound != null ? finishedRound.RewardGold + finishedBonus : 0;
```

### C8. `Assets/Scripts/Enemy/BaseEnemy.cs`

`OnReachEnd`（第 832、842 行）：扣血用加成后的值，**震幅用基础值**。

```csharp
int dmg = Config.DamageToPlayer;
int baseDmg = Config.BaseDamageToPlayer;
...
float amp = Configs.Global.ShakeAmplitude * (1f + 0.35f * Mathf.Max(0, baseDmg - 1));
```

> 理由：`leakDamageBonus` 是经济/难度旋钮，不应连带改变震屏强度；震屏规则仍受"只有漏怪震"约束。

### C9. `Assets/Editor/LubanExporter.cs`

第 186-187 行的 `tables` 数组末尾加 `"tbwavetuning"`。

### C10. `Assets/Editor/M0SetupWizard.cs`

第 199-203 行的 `expected` 数组末尾加 `"tbwavetuning"`。

### C11. `Assets/Scripts/Data/Configs.EditorCandidates.cs`（**容易漏，漏了会断平衡测试**）

`LoadTestCandidate` 会遍历 `ConfigKeys` 并要求每个 key 都有对应 json，缺一个就抛 `FileNotFoundException`。加了新表后，**所有历史候选目录都会缺 `tbwavetuning.json`**，导致 `BalancePlayModeVerifier` 直接抛异常。

三处必须改：

**(a) 缺文件时回退到当前已加载表**（第 22-25 行的判断）

```csharp
else if ((key == "tblocalization" || key == "tbwavetuning") && LoadedJson.ContainsKey(key))
    json[key] = LoadedJson[key];
```

**(b) 构造 + 接管 + 回滚**

```csharp
var waveTunings = new TBWaveTuning(JSONNode.Parse(json["tbwavetuning"]));
...
var oldWaveTunings = WaveTuningTable;
...
WaveTuningTable = waveTunings;
RebuildWaveTuningIndex();
...
catch
{
    WaveTuningTable = oldWaveTunings;
    RebuildWaveTuningIndex();
    ...
}
```

**(c) 把索引构建抽成方法**

在 `Configs.cs` 里新增：

```csharp
private static void RebuildWaveTuningIndex()
{
    WaveTuningByKey.Clear();
    if (WaveTuningTable == null || WaveTuningTable.DataList == null) return;
    foreach (WaveTuning t in WaveTuningTable.DataList)
    {
        WaveTuningByKey[t.LevelId * 10 + t.WaveType] = t;
    }
}
```

`LoadAsync` 与 `LoadTestCandidate` 都调它，避免两处各写一遍。

---

## 5. 逻辑口径（必须逐条遵守）

| # | 口径 | 说明 |
|---|---|---|
| L1 | 倍率选择依据 `isFlying` | `isFlying != 0` → `air*`，否则 `ground*` |
| L2 | 倍率缺省 = 1 | 值为 null / ≤0 一律按 1 处理（0 倍速/0 血没有意义） |
| L3 | 护甲是加法 + clamp | `Clamp01(base + bonus)`；超过 1 会变负伤害（回血），必须夹住 |
| L4 | 金币是加法 | `RoundData.rewardGold + waveGoldBonus`，不覆盖原值 |
| L5 | 击杀金币是乘法 | `EnemyData.reward × killGoldScale`，仍走 `AddGold(float)` 的小数累加 |
| L6 | `waveType` 只认 2 为困难 | 0/1 都是普通，防止脏数据把某波误判为困难 |
| L7 | 困难波不影响出怪数量/顺序 | 只改属性，`EnemyList.EnemyIndexs` 一概不碰 |
| L8 | 图鉴不缩放 | `MonsterCodexView` 继续用 `new EnemyConfig(raw)` |
| L9 | 震幅不随 `leakDamageBonus` 变化 | 见 C8 |

---

## 6. 执行顺序（每步验证后再进下一步）

| 步 | 动作 | 验证 |
|---|---|---|
| 1 | 新建 `WaveTuning.xlsx`（60 行全默认） | 60 行、id 1..60、每关两行 1/2 |
| 2 | `__tables__.xlsx` 加登记 | 行数 +1，`full_name=TBWaveTuning` |
| 3 | 写 `Tools/fill_round_wavetype.py` | `--dry-run` 输出 30 关报告，困难波序号都是 5/10/15/20/25 |
| 4 | `--apply` → `--verify` | verify 退出码 0；`git status` **恰好 30 个** `RoundData.xlsx`；报告末尾为 `处理关卡=30/30 总行数=750 困难波=150` |
| 5 | 跑 `Luban/gen_code_json.bat` | `tbwavetuning.json` **60 条**；`tbrounddata.json` **750 条**且每行有 `waveType` |
| 6 | 改 C1–C11 | Unity 编译无 `error CS` |
| 7 | 数值回归 | 第 7 节第 1–3、9、11 条 |
| 8 | 生效验证 | 第 7 节第 4–8、10、12 条 |

> 第 6 步完成后必须按 `AGENTS.md` 的强制验证：`refresh_unity(mode="force", scope="all", compile="request", wait_for_ready=true)` → 等 `is_compiling=false` → `read_console(types=["error"])` 确认无编译错误。

---

## 7. 验收标准（逐条可测）

### 7.0 覆盖完整性（先验这条，不通过直接退回）

| # | 检查 | 期望值 | 怎么查 |
|---|---|---|---|
| 0-1 | `WaveTuning.xlsx` 数据行 | **60** | 打开表数行，或 `tbwavetuning.json` 长度 |
| 0-2 | `levelId` 覆盖 | **1..30 每关 2 行**，无缺无重 | 脚本按 levelId 分组计数 |
| 0-3 | `RoundData` 已改文件数 | **30** | `git status --porcelain \| grep RoundData \| wc -l` |
| 0-4 | `waveType` 行数 | **750**（30 × 25），全部 ∈ {1,2} | 遍历 30 张表统计 |
| 0-5 | 困难波行数 | **150**（每关 5 行），普通 **600** | 按 `waveType` 计数 |
| 0-6 | `tbrounddata.json` | **750 条**，每条带 `waveType` | JSON 解析计数 |
| 0-7 | `tbwavetuning.json` | **60 条** | JSON 解析计数 |

> 任何一项对不上，说明没有覆盖 30 关，**不许进入后面的功能验收**。

### 7.1 数据正确性

1. **默认值回归**：60 行全为默认（1/1/1/1/0/0/1/0/0）时，进 L01，任取一只地面怪与一只空中怪，`Hp` / `Speed` / `Armor` / `Reward` 与 `EnemyData` 表值**完全一致**。
2. **波型标记**：`tbrounddata.json` 里 L01 的 25 条记录，`waveType=2` 的恰好是 `name` 为"第 5/10/15/20/25 波"的 5 条。
3. **L01/L02 顺序**：L01 的 id=401 那条 `waveType` 必须是 **1**（它是第 21 波），不能因为排在表第 13 行就填 2。

### 7.2 隔离性

4. **单波型生效**：只把 L01 `waveType=2` 行的 `groundHpScale` 改成 2.0，重进 L01：
   - 第 5/10/15/20/25 波的地面怪血量 ×2
   - 其余 20 波地面怪不变
   - 所有空中怪不变
5. **单关生效**：同一改动下进 L02，血量不变。
6. **地空分离**：只把 `airHpScale` 改 1.5，空中怪（Bat）血量 ×1.5，地面怪不变。

### 7.3 经济

7. **波次金币**：L01 普通行 `waveGoldBonus=10`、困难行 `waveGoldBonus=50`：
   - 第 1 波到账 = 原 36 + 10 = 46
   - 第 5 波到账 = 原 84 + 50 = 134
8. **击杀金币**：`killGoldScale=2`，单只击杀金翻倍，小数累加仍正常（不会出现每只都 +0）。

### 7.4 边界

9. **护甲 clamp**：把 `groundArmorBonus` 设 0.9，地面怪的 `Armor` 被夹到 1，塔的伤害为 0 而不是负数（不会回血）。
10. **缺行防御**：从 `WaveTuning.xlsx` 里删掉 L01 的 `waveType=2` 那一行，重进游戏不崩，按默认 1/0 运行，Console 有缺行 warning。
11. **图鉴**：怪物图鉴数值与改动前一致。
12. **震屏**：把 `leakDamageBonus` 设 5，漏一只怪扣 6 血，但震幅与 `leakDamageBonus=0` 时**一致**。

---

## 8. 回滚方案

**只回滚数值（最常见，不需要改代码）**：

把 `WaveTuning.xlsx` 60 行的所有倍率改回 1、加成改回 0，重新导表即可，30 关数值立即复原。

**彻底移除（需要改代码）**：

1. 删 `WaveTuning.xlsx`、删 `__tables__.xlsx` 登记行、删 `tbwavetuning.json`
2. 代码回退 C1–C11 的提交
3. `RoundData.waveType` 列可保留（不影响行为，代码只认 2）

---

## 9. 已知副作用与风险

| 风险 | 说明 | 处置 |
|---|---|---|
| `EnemyList.desc` 里的 EHP 失真 | 那些是手工算的历史值，倍率生效后对不上 | 在每个 `desc` 末尾追加 `tuning-20261102: groundHp xN, airHp xN`，便于回溯 |
| 护甲过高导致"打不动" | `armor` 是减伤比例，0.6 时只剩 40% 伤害 | 配置上限建议 ≤0.6；本次不设代码上限，只 clamp 到 1 |
| 续局快照 | 快照存塔阵/金币/生命，不存怪物血量 | 无影响；改表后需重新进关 |
| 出怪账本 | `expectedWaveCount` / `wave.killed` 只认数量 | 本方案不改数量，无影响 |
| 编辑器平衡验证工具 | `BalanceRuntimeSafetyVerifier` 调 `Spawn(enemyId)` 不传波型；历史候选目录缺 `tbwavetuning.json` | 前者默认 `false` → 普通波；后者由 C11 的"缺文件回退当前表"兜住 |
| `waveType` 漏填 | 老数据若为 0 | 代码按普通处理 + 启动自检 warning |

---

## 10. 交付物清单

**新增**

- `Luban/Config/Datas/WaveTuning.xlsx`
- `Tools/fill_round_wavetype.py`
- `Assets/Gen/WaveTuning.cs`（Luban 生成）
- `Assets/Gen/TBWaveTuning.cs`（Luban 生成）
- `Assets/ConfigJson/tbwavetuning.json`（Luban 生成）

**修改**

- `Luban/Config/Datas/__tables__.xlsx`
- `Luban/Config/Datas/Levels/L01..L30/RoundData.xlsx`（30 个）
- `Assets/Gen/RoundData.cs`、`Assets/Gen/Tables.cs`（Luban 生成）
- `Assets/ConfigJson/tbrounddata.json`（Luban 生成）
- `Assets/Scripts/Core/Res/ResTable.cs`
- `Assets/Scripts/Data/Configs.cs`
- `Assets/Scripts/Data/Configs.EditorCandidates.cs`
- `Assets/Scripts/Data/WaveConfig.cs`
- `Assets/Scripts/Data/EnemyConfig.cs`
- `Assets/Scripts/Enemy/EnemyManager.cs`
- `Assets/Scripts/Round/WaveManager.cs`
- `Assets/Scripts/Game/GameFlowManager.cs`
- `Assets/Scripts/Enemy/BaseEnemy.cs`
- `Assets/Editor/LubanExporter.cs`
- `Assets/Editor/M0SetupWizard.cs`

**报告**

- 提交前给出：`fill_round_wavetype.py --verify` 结果、`tbwavetuning.json` 条数、30 关 `waveType` 分布、Unity 编译检查结果

---

## 11. 执行者检查清单（开工前逐条确认）

- [ ] 已读 `AGENTS.md`，知道配置表保护条款与"改动前先确认范围"的规则
- [ ] **明白必须覆盖 `L01`–`L30` 全部 30 关**：60 行 WaveTuning、30 张 RoundData、750 行 waveType，一个都不能少
- [ ] 明白本次批量写表是**用户单次授权**，只允许写 `waveType` 一列
- [ ] 明白波次序号必须取 `name`/`RoundList`，不能按表行号
- [ ] 明白 `LevelRules` 一个字段都不加
- [ ] 明白护甲是加法且必须 clamp
- [ ] 明白震幅不随 `leakDamageBonus` 变化
- [ ] 已确认 Unity 编辑器版本与 MCP 端口（8084）
- [ ] 已确认改前 `git status` 干净，便于事后 diff 审计
