# 第一关数值重平衡 —— 可执行 Prompt

> **使用方法**：把下方「PROMPT 正文」整段投喂给 AI 执行（WorkBuddy / CodeBuddy 均可）。
> **适用版本**：家用 D 版 `D:\FreedomTower_1`（Unity 2022.3.62f3c1）。同步公司 E 版 `E:\MyTowerGame` 时，需将 `balance_design.json` 的同批参数改动复刻过去后重新 apply。
> **生成依据**：2026-10-20 对运行时配置 `Assets/ConfigJson/*.json` 与配方 `Luban/BalanceDesign/balance_design.json`（revision: balance-30x25-tight-v5, profile D04）的实测数据。

---

## PROMPT 正文

### 1. 角色与目标

你是本 Unity 塔防项目（FTProject，30 关 × 25 波）的数值策划兼程序。玩家实测第一关（D04「中等」预设）通关后 20/20 满血、353 金币剩余、防线铺满整条路径、怪物走不到一半路就被消灭，判定当前节奏「过于轻松」。你的任务是**通过数值配方重调第一关及全关卡压力曲线**，达成以下体验目标：

1. 开局金币紧张：无法一开局就铺满防线，前 5 波必须做取舍；
2. 每波怪物数量充足：怪流有持续压力，需要关注漏怪；
3. 怪物血量随波次/关卡有明显增益：后期不升级塔就守不住；
4. 飞行怪成为常规威胁：早期出现、多波覆盖、数量占比显著，逼出对空配置（普通塔/冰塔可对空，火力塔不能对空）；
5. 全 30 关同向增压，D01~D08 难度梯度单调不倒挂。

### 2. 项目事实（先读，不要重新考古）

- **数值来源是编译管线，不是手改表**：`.workbuddy/tools/balance_pipeline.py` 是唯一权威数值编译器，`Luban/BalanceDesign/balance_design.json` 是配方文件。`Luban/Config/Datas/*.xlsx` 与 `Assets/ConfigJson/tb*.json` 都是管线生成物，**禁止手改**。
- 当前已应用状态：profileId=D04，jobId=apply-v5-20261020，balanceRevision=balance-30x25-tight-v5（见 `Luban/BalanceDesign/applied_state.json`）。
- 第一关专属敌人是独立变体 id（`tbenemydata` 中 desc 含 `profile=D04; level=1; wave=N`），改第一关数值不影响其他关引用。
- 经济与属性全部数据驱动，运行时代码无波次缩放乘区，**本次不需要改 C#**。
- 出怪/经济关键读取点（仅供验证参考，不改）：`PlayerDataManager.cs`（`Gold = level.InitialGold`）、`WaveManager.cs`（按 `SceneInfo.RoundList` 逐波取 `EnemyList`）。

**第一关实测现状（25 波）**：

| 指标 | 现状值 |
|---|---|
| 开局金币 initialGold | **620**（生命 20，波间隔 5000ms） |
| W1 | 11 只，单体 hp 12，EHP 131，450ms/只 |
| W10 | 38 只，hp 15~76，EHP 1742 |
| W15 | 53 只，hp 24~148，EHP 4342 |
| W25 | 83 只，hp 57~705，EHP 16567，240ms/只，仅 1 只 elite，无 boss |
| 全关总怪量 / 飞行怪 | 1175 只；飞行 42 只 = **3.6%**；W1~W6 无飞行怪，W7 首现 1 只 |
| 飞行怪种类 | 仅 Bat / EvilEye / MohawkBat 三种 |
| 波奖励 rewardGold | 22 → 30 |
| 塔价（TowerInfo） | 普 32/90/180，火 44/110/210，冰 30/85/170；普塔 L1 DPS≈13.3 |

**根因在配方 `balance_design.json` 的这些参数（当前值）**：

```
formula.initialGold: 620            ← 开局经济过剩的直接来源
formula.countOffset: 6              ← W1 N = 6+2+3×1 = 11
formula.countLevelCoefficient: 2
formula.countWaveCoefficient: 3     ← W25 N = 6+2+3×25 = 83
formula.spawnBaseMs: 450, minSpawnMs: 240
formula.baseEhpPerUnit: 10          ← W1 单怪 12 hp 的来源
formula.waveLinear: 0.08, waveQuadratic: 0.022
formula.levelEhpGrowth: 0.02        ← 每关仅 +2%，增益无感
formula.minBudgetGrowth: 1.02, finalMultiplier: 1.14
formula.rewardBase: 22, goldPerEhp: 0
roles.air.weight: 0.3               ← 全角色最低（normal 1.0 / swarm 0.65 / medium 1.7 / heavy 2.2）
unlockSchedule: air 在 L1 的 W7/W8/W10 才解锁
```

### 3. 数值改动方向（参数级白名单）

**只允许改 `Luban/BalanceDesign/balance_design.json` 的以下字段**，其余字段（maps、towerValues、bulletValues、表结构、命名）一律不动。给出的建议值是起点，最终以第 5 节验收标准经仿真收敛为准：

| 参数 | 当前 | 建议 | 目的 |
|---|---|---|---|
| formula.initialGold | 620 | **180~230** | 开局只够 2~4 座一级塔，前 5 波做取舍 |
| formula.rewardBase | 22 | 24~28 | 数量上升后波奖励略提，但不改变紧张感 |
| formula.countOffset | 6 | 8 | W1 起步怪量 ↑ |
| formula.countLevelCoefficient | 2 | 3 | 关卡维度数量成长 ↑ |
| formula.countWaveCoefficient | 3 | **5~6** | 波次维度数量成长 ↑（W25 目标 140~170 只） |
| formula.minSpawnMs | 240 | 190~200 | 出怪更密（同屏峰值受第 6 节上限约束） |
| formula.baseEhpPerUnit | 10 | **20~26** | W1 单怪 12 → 25~35 hp（普塔 L1 两三发击杀） |
| formula.waveLinear | 0.08 | 0.12~0.15 | 波内血量成长 ↑ |
| formula.waveQuadratic | 0.022 | 0.028~0.034 | 后期波血量加速成长 |
| formula.levelEhpGrowth | 0.02 | **0.06~0.08** | 「随关卡明显增益」的核心参数 |
| formula.minBudgetGrowth | 1.02 | 1.04~1.06 | 预算下限复利 ↑ |
| formula.finalMultiplier | 1.14 | 1.20~1.30 | 收官波加压 |
| roles.air.weight | 0.3 | **0.9~1.2** | 飞行怪从 3.6% 提到 12%~20% |
| unlockSchedule（L1 air 三条） | W7/W8/W10 | **W3/W5/W8** | 飞行怪第 3 波即登场 |

可选加分项（默认执行，若仿真不达标可回退）：在 unlockSchedule 为 L1 的 W20 增加一条 elite 解锁、W25 增加 1 只 boss（type=5），让收官波有「必打大怪」的记忆点。

### 4. 执行步骤

1. **开工前置（强制约定）**：确认 Unity MCP 可用（ping/telemetry），选定 MyTowerGame 实例并核对 `projectRoot`；若 MCP 不可用，停下来向用户说明并等确认，不得绕过。
2. `python .workbuddy/tools/balance_pipeline.py inspect` 核对当前 applied 状态与本文第 2 节一致；确认 git 工作区干净（或先提交存量改动）。
3. 按第 3 节修改 `Luban/BalanceDesign/balance_design.json`，并把 balanceRevision 升一位（如 `-v6`）。
4. `python .workbuddy/tools/balance_pipeline.py preview --profile D04`（preview 不写盘），导出 W1/W10/W15/W25 关键波对照，确认方向正确。
5. `python .workbuddy/tools/balance_pipeline.py validate` → `simulate --profile D04`：离线仿真全 30 关通过率、漏怪分布、评级阈值。不达标 → 回第 3 步调参重仿，**禁止直接 apply 赌结果**。
6. `python .workbuddy/tools/balance_pipeline.py apply --profile D04` 正式写入（xlsx + 评级表 + applied_state）。
7. Unity 菜单 3 重导 Luban（改 xlsx 必重导），刷新 `Assets/ConfigJson/tb*.json`；注意 `gen_code_json.bat` 会删 `FTProject.Gen.asmdef` 的既有坑，跑完要还原。
8. MCP 编译验证：`refresh_unity(force)` → 轮询 editor/state 直到编译空闲 → `read_console` 查 `error CS`，本次错误修复后复验。
9. PlayMode 实测第一关（可用 `Assets/Editor/Balance/` 下的 LevelBalanceWorkbench / BalancePlayModeVerifier / BalanceGameplayCapture 工具链），记录：开局可建塔数、各波漏怪数、怪物死亡位置分布、飞行怪压力体感。
10. 若需真机生效：配置属 AB 资源 → 重打 AB（菜单 9）→ deploy → `启动热更服务器.bat`（热更三件套铁律，顺序不可乱）。
11. 按提交约定收尾：先写记忆（日档 + MEMORY 分册），然后**全部改动一笔提交**（含 xlsx、ConfigJson、BalanceDesign 状态文件、BalanceWorkbench 产物，不拆不挑）。

### 5. 验收标准（全部量化，仿真 + PlayMode 双重核对）

对第一关：

1. **经济**：initialGold ≤ 230；玩家在 W1 结束前最多建成 4 座一级等效塔；W5 结束前金币不足以同时拉满「普+火+冰」三条线的一级塔。
2. **数量**：W1 N ∈ [16, 20]；W10 N ≥ 55；W25 N ∈ [140, 170]；全关总怪量 ≥ 2400（现 1175）。
3. **血量**：W1 EHP ∈ [400, 650]（现 131）；W15 EHP ≥ 12000（现 4342）；W25 EHP ∈ [80000, 150000]（现 16567）；W25 普通怪单体 hp ∈ [300, 500]（现 57）。
4. **飞行**：首个飞行怪出现在 W3~W4；含飞行怪的波 ≥ 15/25；全关飞行占比 ∈ [12%, 20%]；飞行种类 ≥ 3（现三种已够，靠权重提升出场）。
5. **压力体感**：用 D04 现有五星 reference 操作重放后不再是满血五星；理想操作漏怪 0~3，普通操作漏怪 3~10；普通操作下怪物死亡位置中位数 ≥ 路径长度的 55%（对应「走不完一半就被消灭」的反向验收）。
6. **不倒挂**：其余 29 关同向增压，D01~D08 预设梯度单调保持；离线仿真 30 关全部可通关（不存在仿真无法通关的关卡）；LevelRating 的 2/4 星阈值体系仍然成立（apply 会同步重算评级表，确认无报错）。

### 6. 红线约束

- 禁止手改 `Luban/Config/Datas/*.xlsx` 与 `Assets/ConfigJson/tb*.json`（管线拥有，手改会被覆盖并破坏 header 契约）。
- 不改 TowerInfo 塔价/塔属性、BulletData、Global 的池子上限语义；若仿真确需放开 `maxEnemyAlive=200` / `enemyPoolSize=256`（单波同屏峰值须 < 180，否则必须先调 Global 并单独说明）。
- 不复活已删除的 Pierce4 / Laser5 编号；不改 FreeTower 包裹名、FTProject 命名空间、任何命名规范。
- 本次不改 C# 运行时代码；若仿真达标但实测体感仍不对，先回到配方参数迭代，确实需要新机制（如运行时波次乘区）再单独向用户提案。
- 编辑器脚本不弹 DisplayDialog，结果走 Debug.Log；每一步等编译完成（isCompiling=false）再进行下一步。
- 每轮改参数只动白名单字段；改前把修改前后的 diff 输出到日志，改后用 git diff 自查没有碰白名单外的内容。

### 7. 交付物

1. 修改后的 `Luban/BalanceDesign/balance_design.json`（唯一人工改动点）。
2. apply 后重新生成的全部表文件与评级/状态文件（管线产物，随提交入库）。
3. 一份简报（写入对话即可，不新建文档）：改动参数前后对照表 + 第一关 25 波 W1/W10/W15/W25 前后对照 + 仿真与 PlayMode 验收结果逐条打勾。
4. 若第 5 节任何一条无法达标：明确说明卡在哪个指标、当前达到的值、下一步调参建议，不得静默降级。

--- PROMPT 结束 ---
