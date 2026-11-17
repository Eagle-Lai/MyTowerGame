# VOL_11 · 数值体系 V2（2026-11-15 落表定版）

> ⚠️ **2026-11-17 标注：本册的数值结论已被 V3 定稿（2026-11-16）整体覆盖，只作过程档案保留（原文未改）。**
> 现行口径见 `MEMORY.md`「V3 定稿」条与 `Docs/BalanceV2/07_V3_定稿L01基准换算.md`。
> 另：本册「`sellPrice`=累计投入、`sellRefundRate`=0.7」的卖塔写法**与源码实际相反**——源码是
> `sellPrice` 已按累计投入 ×0.7 预折算、`sellRefundRate`=1.0，只允许一处打折。

> 本册记录 2026-11-14~15 重做的 30 关数值体系里**长期有效**的口径。
> 设计原文在 `Docs/BalanceV2/01_设计总纲.md`、`02_全局参数.md`；**实际数值以源表与
> `06_模拟验证记录.md` 为准**（01/02 是草案，个别范围值在 V2.1→V2.3 校准中被改过）。
> 本册不重复设计推导，只固化"以后改数值必须知道的事"。

## 1. V2 与旧体系的关系

- **三型塔 30 关共用一套参数**，不再随关卡成长；`TowerInfo` 30 份同值。
- 关卡仍 30 × 25 波，每 6 关一阶段（S1–S5），每 5 波一个困难波（W5/10/15/20/25）。
- **关与关独立**，阶段只决定本关可用的压力维度（怪种/集群/高速/重甲/双峰）。
- **参照解**=零漏怪满血通过的玩家常见打法：绕路墙以单体为主、拐角放范围、U 形掉头处
  放减速；升级预算 30% 给航线单体。**取消「提前设防」要求**（V2.3 用户实测 L01 后重定）。
- **V2 作废了 11-07/11-08 的 L02 定稿口径**：`VOL_09` 里的 EHP 21,647,953、Λ 曲线 ×2.92、
  `_l02_hp_*` 系列脚本全部只作历史档案，不要再用来对账或复跑 verify。
- 星级评分仍全删除状态（通关记 5 星），`initialGold` 仍全关 100（铁律不变）。

## 2. 塔与规则常量（落表值）

| 塔 | 级 | 增量价 | 累计价 | power | CD | 射程 | 其他 |
|---|---|---|---|---|---|---|---|
| 单体 | 1/2/3 | 20/30/50 | 20/50/100 | 8/20/44 | 0.8 s | 2.00/2.25/2.50 | 可对空 ×1.0 |
| 范围 | 1/2/3 | 30/40/60 | 30/70/130 | 12/30/60 | 1.5 s | 2.00/2.10/2.20 | 爆炸半径 0.90/1.05/1.20，不可对空 |
| 减速 | 1/2/3 | 25/35/50 | 25/60/110 | 0 | 0.25 s | 2.00/2.25/2.50 | 减速 20/30/40%，可作用空中 |

- `sellPrice` = 累计投入，`LevelRules.sellRefundRate` = 0.7（只在一处打折）。
- `WaveTuning` 全部中性；困难波靠出怪构成本身体现，不加乘区。
- 设计意图：单体 DPS/金 ≈ 0.5；范围单目标 ≈ 0.27–0.31，盈亏点 k\* ≈ 1.8；
  减速只在「覆盖 ≥ 2 座输出塔的重叠区」才划算（ΔDPS/金 > 直接买输出）。

## 3. 怪物原型（相对倍率，基准值逐关校准）

| 原型 | 层 | HP | 速度 | 护甲 | 漏怪扣血 | 首现 |
|---|---|---|---|---|---|---|
| G1 步兵 | 地 | 1.00 | 1.00 | 0 | 1 | S1 |
| G2 群兵 | 地 | 0.30 | 1.05 | 0 | 1 | S2 |
| G3 疾行 | 地 | 0.60 | 1.80 | 0 | 1 | S3 |
| G4 重甲 | 地 | 2.50 | 0.70 | 0.40 | 2 | S4 |
| A1 飞行 | 空 | 1.00 | 1.00 | 0 | 2 | S1 |
| A2 重型飞行 | 空 | 2.20 | 0.80 | 0.20 | 3 | S4 |
| B 首领 | 地 | 12.0 | 0.60 | 0.25 | 5 | 仅 W25 |

- 空中占等效血量：W5 起 轻 25% / 中 35% / 困难 30%；**W1–W4 无空中**。
- 地速按阶段：S1 1.0 / S2 1.08 / S3 1.15 / S4 1.22 / S5 1.3 格/s。
- 怪数规模：W1 ≈ 15 只 → W25 ≈ 52–87 只（V2.3 怪数约为旧版的 ×2.5）。

## 4. 落表与验收链路（下次改数值照这个走）

```bash
# 1) 改设计/参数 → 重跑模拟器生成计划（.NET 10）
dotnet run -c Release --project .workbuddy/tools/balance_v2/MapMetrics   # 地图指标
dotnet run -c Release --project .workbuddy/tools/balance_v2/RefSim       # → Docs/BalanceV2/sim/table_plan.json

# 2) 演练（只读）→ 看 Docs/BalanceV2/sim/dryrun_report.json
python .workbuddy/tools/balance_v2/apply_v2_tables.py --dry-run
#    ⚠️ dry-run 会覆盖 dryrun_report.json；只想比对就先备份再还原

# 3) 落表（先备份到 Docs/BalanceV2/backup_<日期>_before_vX.Y，写完自动白名单回读校验）
python .workbuddy/tools/balance_v2/apply_v2_tables.py --apply
#    上一轮被文件占用中断时用 --resume 沿用已有备份

# 4) Luban 导出 → Unity 看 [Config] 汇总（走编辑器菜单，别直跑 exe）

# 5) 空中顺序复核（落表后必跑，铁律）
python .workbuddy/tools/check_air_spawn_order.py   # 期望 PASS，adjacent_air_pairs=0
```

- 脚本只改：`TowerInfo` / `BulletData`(aoeRadius) / `LevelRules`(sellRefundRate) /
  `LevelMap`(airSpawn 两列) / `RoundData` / `EnemyList` / `EnemyData`。
- **绝不改**：`SceneInfo`（initialGold=100、initialHp、RoundList）、地图 `cells`、
  `WaveTuning`、`TBGlobal`。脚本里 `SceneInfo` 是只读加载，跑完 `wb.pop("SceneInfo")`。
- `EnemyData.levelId` 由脚本写当前关，顺带修掉了历史遗留的 `levelId=1`。

## 5. 空中出生格（同批上线的玩法契约）

- `LevelMap` 新增 `airSpawnRow` / `airSpawnCol`（-1 = 沿用起点 S）；`LevelMapConfig`
  暴露 `HasAirSpawn`，`EnemyManager` 在 `enemy.Init` **之前**摆位（飞行直线取当前位置为起点）。
- 已指定：L18/L20/L21/L22/L23/L29 = (0,0)，L28 = (0,16)，其余 23 关沿用 S。
- 与「空中不得相邻」并存：生成器断言 + 跨波首尾不放空中，落表后必须跑检查脚本。

## 6. V2.3 验收证据（750 波）

- 参照解满血通过、总漏怪 0；再低 10 个百分点则 708/750 波漏怪（94.4%）→ 余量不虚高。
- W1–W4 共 120 波无空中，W5 起 630 波均有空中；空中占等效血量 25.0%–35.2%。
- 单波 30–59 s；战斗时间 834–1216 s；开局金币 30 关 = 100。
- 位置容错：开局 5 塔换次优格，W1–W3 零漏（L28/L29 不适用）。
- 已知偏差：42 波「再低 10% 也不漏」（W1–W3 为主，迷宫未成形、塔少，属预期）；
  最长绕路仅 L01 证明最优，其余关是 60 s 搜索最好解；模拟按理想出怪时刻，
  运行时组间衔接有约半个间隔误差。

## 7. 工具与产物位置

| 内容 | 位置 |
|---|---|
| 设计总纲 / 全局参数 / 地图指标 | `Docs/BalanceV2/01~03_*.md` |
| 难度曲线页（自包含 HTML） | `Docs/BalanceV2/05_难度曲线.html`，`StaticServe` 8765 端口托管 |
| 验收记录（逐关表） | `Docs/BalanceV2/06_模拟验证记录.md` |
| 落表计划 / 逐关明细 / 汇总 | `Docs/BalanceV2/sim/{table_plan,levels,summary}.json` |
| 逐关可读档案 | `Docs/BalanceV2/levels/L01–L30.md` |
| 旧版归档（V2.0/V2.2） | `Docs/BalanceV2/v2.0_archive/`（含两份已写入过的 plan） |
| 模拟器 / 落表脚本 | `.workbuddy/tools/balance_v2/`（bin/ 不入库，csproj 已反忽略） |
| 落表前快照 | `Docs/BalanceV2/backup_*`（**不入库**，需要历史用 git） |
