# L01 示意图迷宫重设计 —— 数值方案与验证证据（2026-10-28）

## 任务背景

用户提供 30 张关卡路径示意图（`C:\Users\Administrator\Pictures\路径布局图\`），要求按 7 条约束重设计 30 关数值，
本轮只交付第一关。约束：① W25 最后一怪距终点≥2 格被消灭；② 初始金钱 100；③ 空军从 W5 起且逐波递增、
关卡越靠后种类越丰富；④ 允许重设计三塔三级数值；⑤ 末波最后一怪消灭前示意图全部可建造格建满三级塔；
⑥ 难度循序渐进；⑦ 零漏怪通关。

## 第一关基元（像素级提取自示意图）

- 网格 13×7（与 `Levels/L01/LevelMap.xlsx` 一致），S(1,4) → E(13,4)。
- **示意图终局蛇形路线 = 49 格（48 步）**：col1↓ → r7→ → col3↑ → r1→ → col5↓ → r7→ → col7↑ → r1→ → col9↓ → r7→ → col11↑ → r1→ → col13↓。
- **可建造格 = 42 个**（全部偶数列墙体 + col1 顶部 3 格 + col13 底部 3 格），终局满三级。

### 蓝图 42 格塔型分配（意图布局）

| 塔型 | 数量 | 格位（列,行 1 起） |
|---|---|---|
| 冰霜 Frost | 7 | (2,4)(4,4)(6,4)(8,4)(10,4)(12,4)(13,6) —— 全部压在空军直航线（第 4 行）上 |
| 普通 Normal | 22 | 六面墙第 3/5 行 ×12、(1,2)(1,3)(13,5)(13,7)(2,1)(6,1)(10,1)(4,7)(8,7)(12,7) |
| 火力 Blast | 13 | (1,1) + 六面墙第 2/6 行 ×12 |

三塔满级总造价 = 22×100 + 13×139 + 7×130 = **4917 金**；最省全普通 = 4200 金。

## 数值方案（相对现行的改动点）

| 项 | 现行 | 新方案 |
|---|---|---|
| 初始金币 | 100 | 100（不变，满足约束②） |
| 初始生命 | 12 | **1**（约束⑦零漏怪的数值化：任一漏怪即败） |
| 波数 | 25 | 25（不变） |
| 空军起始 | W5（但 W5=W6=14 有平台期，且用满 4 种空军） | **W5 起逐波严格递增 2,3,4,…,22（共 242），全关仅 1 种空军 Bat（canonical 11）**，为后续关卡留出"种类不断丰富"的阶梯 |
| 每波总数 N | 25+6W（31→175，总 2575） | 不变 |
| 每波 EHP 目标 | 256→51579（W5/10/15/20 压力波、W25 ×2 节奏） | **逐波保持不变** |
| 敌人构成 | 混排 | 轮转混排：normal(Chick/Chicken)→swarm(Larva)→medium(Crawler)→heavy(Scarab)→elite(Rat, 仅 W25×3)→air(Bat)，均匀铺开避免空军扎堆 |
| 地面配比 | — | W1-2 全普通；W3+ 虫群 30%；W5+ 中型 20%；W11+ 重型 12%；W25 加精英 2% |
| 出怪间隔 | 280ms 递减至 128ms | 不变 |
| 击杀奖励 | n2/s1/m2/h3/elite5/air1 | 不变（击杀金 4506 + 波奖 825 + 初始 100 = 总收入 **5431**，覆盖意图布局 4917，余量 10.5%；全普通仅 4200，余量 29%） |
| 三塔三级数值 | 现行（普通 32/28/40、火力 44/40/55、冰霜 30/40/60；普通/冰霜可打空军，火力不可） | **复核后保持不变**（避免扰动 L02-L30 既有平衡；约束④为"允许"而非"必须"） |

变体 ID 新区间 `5000000..5000245`（106 个变体，与 30 关现存 ID 无冲突，写入前已断言校验）。

## 验证结果

### 1) 离线空间仿真（`tools/l01_verify.py`，改编自 balance_simulator spatial-fixed-step-30x25-maze-v6）

按蓝图 42 建造 + 84 升级的脚本化顺序（先建满、后按 Frost→Normal 核心全员→其余的优先级升级）：
**100ms 与 50ms 两种步长下 7 项约束全部通过**：

- C1 末怪距终点：W25 最后一杀距 E **38.4 格**（heavy，路径 48 步）；**全波最小击杀距离 4.8 格（100ms）/6.2 格（50ms）**，远超 ≥2 格要求；
- C2 初始金钱 100 ✓；
- C3 空军 W1-4=0、W5 起严格递增 ✓；全关仅 `Enemy_Bat` 一种空军 ✓；
- C5 末波开打前（波边界操作先于任何 W25 击杀）42 格全部三级塔 ✓；
- C7 零漏怪：2575 全歼 / 0 漏 / hp=1 通关 ✓；
- C6 难度曲线：波战斗时长 13.9s→39.2s、塔数 3→42、路径 12→48 步、同屏峰值 19→113，单调爬升无断崖；
- 收支：总收入 5431，终局余 514 金，全部升级在 W24/W25 边界前完成。

### 2) 标准链路与 Unity 运行时

- `balance_pipeline.py verify-layout`：passed=true（L01 106 变体闭合引用、无孤儿行、30 关无 ID 冲突）。
- Luban 导出 ×2（第二次为重封哈希后让 `tblevelrating.json` 携带哈希）→ `Assets/ConfigJson`。
- `runtimeContentHash` 重算（严格复刻 `Configs.CalculateRuntimeContentHash`）= `00bdece0a5d81b3f0d2e1108ba65433311b49ca22496026bc04d9e1bd7d2a370`，写入全部 30 关 LevelRating 行（全局哈希，含 17 字段评级行文本）。
- Unity MCP（**端口 8084**，实例 FishTestGame@0c9048e2c2ec99ee）：refresh+编译 `scriptCompilationFailed=False`；
  **Play Mode 原生启动，控制台输出 `[Rating] Runtime configuration SHA256 verified: 00bdece0…`，运行时 0 错误**。

### 3) 过程中发现并修复的问题

- 直接跑 Luban 客户端未带 `--` 分隔符参数不生效；
- 导出清空了手工添加的 `Assets/Gen/FTProject.Gen.asmdef`（引用 FTProject.LubanLib）导致 CS0246 'Bright'，已从 git 恢复并复验编译通过；
- 域重载后编辑器态直连 ResLoader 预载不可用（资源包未初始化，10 表全 null），改走 Play Mode 原生流程完成运行时验证。

## 变更清单（git 工作区）

- `Luban/Config/Datas/Levels/L01/{EnemyData,EnemyList,SceneInfo,LevelRating}.xlsx` — 重设计数据
- `Luban/Config/Datas/Levels/L02..L30/LevelRating.xlsx` — 仅 runtimeContentHash 重封（标准链路要求）
- `Assets/ConfigJson/{tbenemydata,tbenemylist,tbsceneinfo,tblevelrating}.json` — Luban 导出产物
- `.gitignore` — 追加 `.cache.meta`（Luban 根目录增量缓存）
- 本目录 `tools/`：`l01_design.py`（设计+写表）、`l01_verify.py`（验证器）、`reseal_hash.py`（哈希重封）；`reports/verify_result.json`

## 复跑方式

```
PY=C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe
$PY Docs/BalanceEvidence/L01-DiagramRedesign-20261028/tools/l01_verify.py 50   # 离线约束验证（读盘上表）
$PY Docs/BalanceEvidence/L01-DiagramRedesign-20261028/tools/reseal_hash.py    # 导出后重封哈希
```

## 后续（待用户体验 L01 后）

逐关推进 L02-L30：空军种类阶梯（L02:+EvilEye → L03:+MohawkBat → L04:+DreadEye → L05:+QuickBat）、
EHP 曲线与经济按同法重设计并逐关仿真+Play Mode 验证。**注意：改动任一关表后必须重跑 `reseal_hash.py` 并重新导出（全局哈希）。**
