# 塔防节奏重构 + 关卡配置表按关拆分 —— 可执行 Prompt

> **使用方法**：把下方「PROMPT 正文」整段投喂给 AI 执行（WorkBuddy / CodeBuddy 均可）。
> **适用版本**：公司 E 版 `E:\MyTowerGame`（Unity 2022.3.62f3c1）。家用 D 版 `D:\FreedomTower_1` 需另行同步配方与表结构。
> **生成依据**：2026-10-21 对本工程的实测（配置表行数/结构、`balance_pipeline.py` 函数级实现、Luban 多文件输入三项实验）+ 《坚守阵地》公开可信资料。
> **本文件只定义"要做什么、怎么验"，不含任何已改动的工程文件**。执行前工程处于 `balance-30x25-tight-v6` / profile D04。

---

## PROMPT 正文

### 0. 一句话任务

把「30 关 × 25 波全部堆在 6 张聚合表里」改成「每关一个独立目录、目录内每张表一个文件」，并在此基础上把数值节奏从「平滑爬坡」重构为「五个陡坎 + 呼吸段」的紧张节奏，全部改动必须经离线仿真与 PlayMode 回放验证。

**两个阶段必须按顺序做，且阶段 A 单独可交付**：

| 阶段 | 内容 | 完成标志 |
|---|---|---|
| A | 纯物理拆表，**一个数值都不改** | 拆分前后 `Assets/ConfigJson/tb*.json` 语义等价（按 id 排序逐字段一致） |
| B | 在新结构上重构节奏数值 | 30 关仿真 + PlayMode 验收全过 |

如果只想先解决"表太乱"，做完阶段 A 就停，不要顺手改数值——否则等价性校验失效，出问题无法二分定位。

---

### 1. 角色与目标

你是本项目的数值策划兼工具链工程师。当前玩家体感是「前期太松、后期太挤、整关太平」：第 1 关开局 230 金币可铺 7 座塔，25 波里没有任何一个必须做决策的时刻。

#### 1.1 体验目标（每条都要能被第 7 节量化验收）

1. **开局必须取舍**：任意关卡开局金币只够 2.5~3.5 座最便宜塔（当前是 7 座），前 3 波就要决定"铺数量"还是"攒高级塔"。
2. **五个陡坎**：每关第 5/10/15/20/25 波是明确的压力峰，环比强度 ≥ 普通波的 1.4 倍；扛过之后有 2~3 波明显喘息，形成"冲刺—呼吸"交替。
3. **波与波几乎无缝**：波间空档从 5000ms 压到 2500ms（前 3 关 3000ms），单波节拍 14~22 秒，单关 25 波 7~9 分钟——对齐《坚守阵地》100 波 30 分钟（1x）的节拍密度。
4. **漏怪有痛感**：初始生命 20 → 12，四星容错 2 漏不变，但血量占比语义随之下调，玩家不能再"送几只无所谓"。
5. **空军是常规威胁**：第 3 波首现（已实现），每 5 波必有一段，占比 12%~18%，逼出对空配置。
6. **收入不能脱钩**：击杀金币仍是主要来源，坎波给 1.5 倍波奖励作为"过坎回血"，形成"过坎→变强→下一个坎"的正反馈，而不是"存钱躺过"。

#### 1.2 不允许改变的东西

关卡总数 30、每关波数 25、地图布局 `LevelMap` 的格子内容、塔的种类与数量、难度预设 D01~D08 的档数与命名、五星评级体系、`FreeTower` 包裹名与 `FTProject` 命名空间。

---

### 2. 工程事实（先读，不要重新考古）

#### 2.1 唯一权威链路

- 数值编译器：`.workbuddy/tools/balance_pipeline.py`（唯一权威，1145 行）
- 配方：`Luban/BalanceDesign/balance_design.json`（`balanceRevision = balance-30x25-tight-v6`）
- 状态：`Luban/BalanceDesign/applied_state.json`（profileId=D04，jobId=apply-v6-20261020）
- 一切 `Luban/Config/Datas/*.xlsx`、`Assets/ConfigJson/tb*.json`、`Assets/Gen/*.cs` 都是**生成物，禁止手改**。
- Python 必须用带 openpyxl 的 venv：`C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe`（本机实测 `openpyxlAvailable: true`；系统 3.13 无 openpyxl，`apply` 会挂）。
- 命令：`inspect` → `preview --profile D04` → `validate` → `simulate` → `apply --profile D04`；输出在 `Library/BalanceWorkbench/<job>`。

#### 2.2 六张关卡表的现状（实测行数）

| 表 | 文件 | 数据行 | 结构 |
|---|---|---|---|
| TBSceneInfo | `SceneInfo.xlsx` | 30 | 每行一关；`RoundList` 用逗号串引用本关 25 个 round id |
| TBRoundData | `RoundData.xlsx` | 750 | 每行一波；`EnemyIndexs` 是本波 enemyList id |
| TBEnemyList | `EnemyList.xlsx` | 750 | 每行一波；`EnemyIndexs` 是 18~162 个怪物 id 的长串 |
| TBLevelMap | `LevelMap.xlsx` | 30 | 每行一关；`cells` 用 `|` 分隔行 |
| TBLevelRating | `LevelRating.xlsx` | 30 | 每行一关 |
| TBEnemyData | `EnemyData.xlsx` | **10905** | 132 行原型（id<100000）+ **10773 行关卡变体**（id≥100000，desc 含 `level=N; wave=M`） |

id 是全局连续的 1..750（round/list 各自一套），**没有任何"关卡号"字段**——这是"聚合"的根源。

#### 2.3 运行时读取链路（为什么拆表可以 0 改 C#）

```
SceneInfo.RoundList[]  →  TBRoundData[id]  →  EnemyIndexs[]  →  TBEnemyList[id]  →  EnemyIndexs[]  →  TBEnemyData[id]
```

- `LevelConfig.cs` 只暴露 `RoundIds`（= SceneInfo.RoundList），`WaveConfig.cs` 只按 id 查表。
- 全工程 `Assets/Scripts` **没有** 30/25 的硬编码常量（已 grep 确认），关卡完全由配置驱动。
- 因此：只要 Luban 导出的 `tb*.json` 内容不变，拆表对运行时**零影响**。

#### 2.4 三个已实测的 Luban 事实（本轮实验结论，直接决定方案）

用本工程 `Luban/Tools/Luban.ClientServer/Luban.ClientServer.exe` 做了三组隔离实验：

| 实验 | 结论 | 影响 |
|---|---|---|
| 一张表 `input` 写多个 xlsx（逗号分隔） | **合并成功**，导出单一 json，行序 = 文件声明顺序 | ✅ 拆表可行 |
| 一个 xlsx 内放多个 sheet | **所有 sheet 被同一张表吞掉**（实验里 `OtherData` 的 id=91 被并入 TBRoundData） | ❌ **不能**"每关一个工作簿装多张表" |
| 两个文件出现重复主键 | **明确报错**：`主键字段:'id' 主键值:'1' 重复` | ✅ 拆错能被抓住 |

另：`input` 支持子目录相对路径（`Levels/L01/RoundData.xlsx` 实测通过）。

> 结论：**「每关一个目录、每张表一个文件」是唯一可行结构**。想做成"一个关卡一个 xlsx"必须改 Luban 读表逻辑，不在本次范围。

#### 2.5 现有硬校验及其约束

`validate()` 的硬校验里有一条与"节奏"直接冲突：

- **逐关逐波 EHP/数量严格递增**：对 `(L, w-1)` 和 `(L-1, w)` 都必须严格 `>`。
- 这意味着**不能做真正的锯齿波**（W6 不能比 W5 低）。

因此节奏设计只能走"**单调但坡度突变**"：整体仍递增，但 W5/10/15/20/25 的环比显著高于相邻波。这也是下面 5.1 的写法。**不要为了做锯齿去改这条校验**——它同时保证了 30 关不塌陷，v6 已经为它付出过代价（见 `VOL_08` 的 K=1.61 由来）。

其它硬校验：跨表 hash、EHP ±0.5%、prefab/注册存在性、塔价链、rating 字段、Par > spawn span。全部保留。

---

### 3. 参考基准：《坚守阵地》

#### 3.1 确证数值（可信来源）

| 项目 | 数据 | 来源 |
|---|---|---|
| 波数 | 100 波（classic / extended） | Giant Bomb wiki |
| 起始金币 | **$15** | Ars Technica 2008 评测 |
| 生命 | **20**（20 个单位到达出口即失败） | Ars Technica |
| 塔价 | Gatling $5 / Goo $10 / Missile $20 / Ice $20 / Laser $40 / Flame $50 / Tesla $70 / Mortar $120 | Giant Bomb wiki |
| 升级 | 每塔 2 次，费用为原价的 30%~80% | Ars Technica |
| 击杀赏金 | 普通 $1~$2，硬的 $10~$20 | Ars Technica |
| 单局时长 | 100 波 ≈ 15 分钟（2 倍速）→ **1x 约 30 分钟，即 18 秒/波** | Steam 全成就指南 |
| 空军 | 直线飞越迷宫，无视地面路径 | Giant Bomb |
| 地面路径 | 走最短路径，玩家自建但必须连通 | Giant Bomb |
| 地图 | 1~3 个入口/出口，5 张图 | Giant Bomb |

补充（二手来源，仅作方向参考、不作验收依据）：Gatling 伤害 43/86/129、Tesla 525/1050/1575、Mortar 1300/2600/3900；Goo 减速 35%/50%/65%。

#### 3.2 从数据里提炼的 6 条节奏法则

1. **开局预算 = 3 座最便宜塔**（$15 / $5）。第一波就必须选"铺满"还是"留钱"。
2. **塔价梯度 24 倍**（$5 → $120）。购买力是分期解锁的，每 10 波左右才够买下一档。
3. **单波 18 秒、波间几乎无缝**。紧张感来自"没时间想"，不是"怪血厚"。
4. **容错 0.2 命/波**（20 命 / 100 波）。允许失误，但完美通关是独立成就。
5. **收入靠击杀，不靠波奖励**。杀不动 → 没钱 → 更杀不动，形成负反馈压力。
6. **空军绕过地面防线**。强制维持两套火力，不能一招通吃。

#### 3.3 换算到本工程（25 波 × 30 关）

| 维度 | 《坚守阵地》 | 本工程目标 | 现状（v6, L1/D04） |
|---|---|---|---|
| 开局预算 / 最便宜塔价 | 3.0× | **2.5~3.5×** | 7.2×（230/32） |
| 单波节拍 | 18s | **14~22s** | W1 7.7s、W25 34s，且波间 5s |
| 单关时长 | 30 min / 100 波 | **7~9 min / 25 波** | 约 12 min |
| 生命 / 波数 | 0.20 命/波（20 命 / 100 波） | **0.48 命/波（12 命 / 25 波）** | 0.80 命/波（20 命） |
| 压力峰间隔 | 约每 10 波 | **每 5 波** | 每 5 波但仅 ×1.12 |
| 塔价梯度 | 24× | 保持 6.6×（本次不动塔价） | 32→210 |

> **关键判断**：本工程的差距**不在"总量不够大"**（W1→W25 已经是 160 倍），而在"开局太富、波间太长、坎不够尖"。所以阶段 B 的主战场是**预算、节拍、坡度**，不是继续堆血量。
>
> 生命取 12（0.48 命/波）而不是照抄 FR 的 0.2 命/波：本工程棋盘只有 13×7~16×9、路径短、单体通过窗口小，容错给到 FR 的 2.4 倍才不至于"一只快怪漏过去就掉一颗星"。

---

### 4. 阶段 A：按关拆分（数值零变化）

#### 4.1 目标结构

```
Luban/Config/Datas/
├─ Levels/
│  ├─ L01/
│  │   ├─ SceneInfo.xlsx      # 1 行：该关元信息（RoundList 引用本关 25 个 round id）
│  │   ├─ RoundData.xlsx      # 25 行
│  │   ├─ EnemyList.xlsx      # 25 行
│  │   ├─ LevelMap.xlsx       # 1 行
│  │   ├─ LevelRating.xlsx    # 1 行
│  │   └─ EnemyData.xlsx      # 该关全部怪物变体（约 360 行）
│  ├─ L02/ ... L30/           # 同上
├─ EnemyData.xlsx             # 只留 132 行原型（id < 100000）
├─ TowerInfo.xlsx  BulletData.xlsx  Global.xlsx  AudioData.xlsx  Localization.xlsx   # 不动
└─ __tables__.xlsx            # input 改成 30 个路径
```

每关 6 个文件 × 30 关 = 180 个文件；加上主表 6 个，`Datas` 共约 186 个 xlsx。

#### 4.2 `__tables__.xlsx` 的 input 写法

每张关卡表的 `input` 列写成 30 个相对路径、逗号分隔（**不要有空格**）：

```
TBRoundData  → Levels/L01/RoundData.xlsx,Levels/L02/RoundData.xlsx,...,Levels/L30/RoundData.xlsx
TBEnemyData  → EnemyData.xlsx,Levels/L01/EnemyData.xlsx,...,Levels/L30/EnemyData.xlsx
```

- 必须由脚本生成，禁止手写（30×6 段路径，手写必错）。
- 路径用 `/`；实测可解析。
- 主表 `EnemyData.xlsx` **必须排在第一位**，原型行先入表；变体行随后。

#### 4.3 表归属规则（哪些行进哪个文件）

| 表 | 归属判据 | 每文件行数 |
|---|---|---|
| SceneInfo | `id == L` | 1 |
| RoundData | `id ∈ SceneInfo[L].RoundList` | 25 |
| EnemyList | `id ∈ RoundData[r].EnemyIndexs`（r 属于本关） | 25 |
| LevelMap | `levelId == L` | 1 |
| LevelRating | `id == L` | 1 |
| EnemyData | `id >= 100000` 且 `desc` 中 `level=L` | 约 360 |

> 不要用 id 数值范围去猜关卡（变体 id 里 `(L-1)*40000` 只是编码巧合，含 profile 位）。**一律以 desc 里的 `level=` 为准**，并在迁移脚本里断言 id 唯一。

#### 4.4 管线改造清单（函数级，按此顺序改）

| # | 位置 | 改什么 |
|---|---|---|
| 1 | `TABLE_FILES` 附近 | 新增 `LEVEL_TABLES = ['tbsceneinfo','tbrounddata','tbenemylist','tblevelmap','tblevelrating','tbenemydata']` 与 `level_path(L, table) -> 'Levels/L%02d/<Name>.xlsx'` |
| 2 | `source_hashes()` | 把 30×6 新路径纳入 hash 集合，否则 `assert_sources()` 会误报"源表被外部修改" |
| 3 | `excel_write(stage, plan)` | 拆成两段：全局表照旧；关卡表按 L 分组写独立文件（表头 3 行 + 数据行，样式从模板复制）。`tbenemydata` 要再分流一次：`id < 100000` 的原型写回 `Datas/EnemyData.xlsx`，变体写 `Levels/Lxx/EnemyData.xlsx` |
| 4 | `write_rating_excel()` | 按关写 `Levels/Lxx/LevelRating.xlsx`，只写该关 1 行 |
| 5 | `excel_write()` 里 `__tables__.xlsx` 段 | 自动重写 6 张表的 input 清单（幂等：每次先清空再按 L01..L30 顺序填） |
| 6 | `check_managed_conflicts()` | 扫描新路径集合 |
| 7 | `apply_plan()` 的 `files` 列表 | 动态枚举 `Levels/*/*.xlsx`，并**加入旧聚合文件的删除项** |
| 8 | `commit_files()` / journal | 支持"删除文件"事务项（拆表后 `Datas/RoundData.xlsx` 等 5 个必须消失；回滚要能恢复） |
| 9 | `validate()` | 新增"归属一致性"检查：`Levels/Lxx` 下的行必须只属于 Lxx（见 4.6 第 4 条） |
| 10 | 新增 `verify-layout` 子命令 | 检查 30 目录 × 6 表齐全、行数符合 4.3、input 清单与磁盘一致、无重复 id |

**不要动**：`generate()` 的数值逻辑、`validate()` 的既有硬校验、`luban_export()` 的调用方式、`runtime_content_hash()` 的字段集合。

#### 4.5 地图编辑器链路（最容易漏）

`Assets/Editor/LevelMapEditorWindow.cs` 的一键写入走 `.workbuddy/tools/apply_levelmap_export.py`，脚本里硬编码了 `Datas/LevelMap.xlsx` 和 `Datas/SceneInfo.xlsx`。

必须同步改：

- `apply_levelmap_export.py`：按 `level_id` 定位 `Levels/L{level_id:02d}/LevelMap.xlsx`；关卡存在性检查改读 `Levels/Lxx/SceneInfo.xlsx`（或直接读合并后的 `Assets/ConfigJson/tbsceneinfo.json`，更稳）。
- 备份文件命名带上关卡号，避免 30 个 `LevelMap.xlsx.bak` 互相覆盖。
- 改完在编辑器里实点一次「一键写入 xlsx」，确认 ⑤ 回读比对仍通过。

#### 4.6 一次性迁移脚本

新建 `.workbuddy/tools/migrate_split_level_tables.py`，只做迁移，不做数值：

1. 备份整个 `Datas` 到 `Luban/BalanceDesign/Versions/split-<date>/`。
2. 按 4.3 规则把 6 张关卡表拆成 180 个文件；`Datas/EnemyData.xlsx` 只保留 132 行原型。
3. 重写 `__tables__.xlsx` 的 6 条 input。
4. **逐文件断言**：行数符合 4.3；id 唯一；`desc` 的 `level=` 与目录号一致；`RoundList` 长度 25。
5. 跑一次 Luban（`DOTNET_ROLL_FORWARD=LatestMajor`），比对导出 json 与迁移前：
   - 8 个 `tb*.json` 的**行集合**必须完全一致（按 id 排序后逐字段比对，忽略键顺序）
   - 行数必须一致（`tbrounddata` 750、`tbenemylist` 750、`tbenemydata` 10905、`tbsceneinfo` 30…）
6. 输出 `Docs/BalanceEvidence/split-migration.json`：每表行数、hash 前后对照、不一致项列表。

> **阶段 A 的验收只要一条：拆分前后 `Assets/ConfigJson/tb*.json` 语义等价。** 任何数值差异都说明脚本写错了，不要"顺便修一下"。

---

### 5. 阶段 B：数值体系（节奏紧张）

#### 5.1 节奏波形规格

保持单调递增（2.5 的硬校验），用"坡度突变"制造坎。下表是**目标形态**，不是逐波要对的死表——真实波形由 `waveLinear / waveQuadratic / pressureMultiplier` 三者共同决定，验收以 7.2 的区间为准：

| 波次 | 相对上一波 EHP 环比 | 说明 |
|---|---|---|
| W1~W4 | 1.25 ~ 1.35 | 教学段；数量增长占比大，所以环比天然偏高 |
| **W5** | **1.70 ~ 1.92** | 第一个坎：重甲 + 空军混编 |
| **W6** | **1.02 ~ 1.06** | 呼吸起点：靠 `minBudgetGrowth` 兜底，坡度骤降 |
| W7~W9 | 1.15 ~ 1.27 | 呼吸段（绝对值仍高于 W5，但体感轻松） |
| **W10** | **1.55 ~ 1.80** | 第二个坎：空军占比拉到 18% |
| **W11** | **1.02 ~ 1.06** | 呼吸起点（多为兜底平台波） |
| W12~W14 | 1.03 ~ 1.22 | 呼吸（前段在兜底平台上，后段重新爬升） |
| **W15** | **1.55 ~ 1.80** | 第三个坎：首次大量 fast + 空军 |
| **W16** | **1.02 ~ 1.06** | 呼吸起点 |
| W17~W19 | 1.10 ~ 1.25 | 呼吸 |
| **W20** | **1.55 ~ 1.80** | 第四个坎：elite 潮 |
| **W21** | **1.02 ~ 1.06** | 呼吸起点 |
| W22~W24 | 1.05 ~ 1.22 | 呼吸 |
| **W25** | **1.70 ~ 2.10** | 收官：boss（L≥12）+ 最大数量 |

> **坎后第一波为什么只有 +2%**：`generate()` 里有一条既有兜底 `budget = max(raw, 前波 × minBudgetGrowth)`，`minBudgetGrowth = 1.02`。`pressureMultiplier` 只乘在 W5/10/15/20/25，所以坎后一波的 `raw` 反而**低于**坎波，被兜底成 `坎波 × 1.02`。**这就是免费的"呼吸机制"，不需要新代码**——不要为了提高 W6 环比去改 `minBudgetGrowth`，那会把五个坎一起抹平。
>
> **W25 不叠乘（易踩坑）**：源码是三元表达式 `finalMultiplier if w == wave_count else pressureMultiplier if w % 5 == 0 else 1`——**W25 用的是 `finalMultiplier`，不是 `pressureMultiplier`，两者不相乘**。所以 N25 的收官强度完全由 `finalMultiplier` 决定；按 `waveLinear/waveQuadratic` 新起点值手算，`finalMultiplier = 1.30` 时 W25 环比只有约 1.45，达不到 1.70 下限，**必须给到 1.55 左右**。不要误以为"W25 既吃 pressure 又吃 final"而把 `finalMultiplier` 压得过低。

派生约束：

- **坎/普比 ≥ 1.40**（这是"紧张感"的核心指标，必须逐关校验）
- 全关 `W25.EHP / W1.EHP ∈ [120, 200]`（现状 160，保持同量级）
- 任意相邻两波的数量环比 ≤ 1.20（数量不能跳变，只有强度跳变）

实现路径（只调这三个参数，不新增公式）：

```
formula.pressureMultiplier  1.12 → 1.40 ~ 1.44     # 坎波额外乘区（起点 1.42）
formula.waveLinear          0.08 → 0.045 ~ 0.055   # 压低平滑斜率
formula.waveQuadratic       0.022 → 0.014 ~ 0.018
```

降斜率会让总量下降，用 `formula.levelEhpGrowth` 或 L 级 override 补回；**优先用 override，不要一刀切改全局 base**（v6 的教训：全局 base 一动，L20 W1 直接全灭）。

#### 5.2 开局预算曲线

现状最刺眼的问题是**没有关卡成长曲线**：L1=230（override）、L2=624、L30=736 —— 第 2 关直接跳到 19 座塔，之后 29 关几乎持平。

目标：

```
initialGold(L) = 100 + 20 × (L - 1)      # L1=100, L10=280, L20=480, L30=680
```

- 对应可建塔数（塔价 32）：L1 **3.1** / L10 8.8 / L20 15 / L30 21.3
- **必须删除 `L1-gold-v6` 这个 override**（它把 L1 拉到 230，是新曲线的反面）
- `formula.goldPerLevel` 4 → 20

验收时要检查"开局可建塔数"这条曲线是否单调且不出现断层（相邻关比值 ≤ 1.25）。

#### 5.3 参数白名单（只允许改这些）

| 参数 | 当前 | 起点值 | 目的 |
|---|---|---|---|
| `formula.initialGold` | 620 | **100** | 开局只够 3 塔 |
| `formula.goldPerLevel` | 4 | **20** | 关卡维度成长 |
| `formula.initialHp` | 20 | **12** | 漏怪有痛感 |
| `formula.autoNextRoundDelayMs` | 5000 | **2500** | 波间几乎无缝 |
| `formula.spawnBaseMs` | 450 | **380** | 前期出怪更密 |
| `formula.spawnWaveReductionMs` | 10 | **6** | 后期压缩更平缓（避免同屏爆炸） |
| `formula.minSpawnMs` | 200 | **150** | 后期下限 |
| `formula.maxSpawnMs` | 450 | **380** | 上限同步 |
| `formula.pressureMultiplier` | 1.12 | **1.42**（1.40~1.44） | 坎更尖；1.40 时中段坎/普比只有 1.38，1.44 会把 W5 顶到 1.89 |
| `formula.waveLinear` | 0.08 | **0.050** | 压低平滑斜率 |
| `formula.waveQuadratic` | 0.022 | **0.016** | 同上 |
| `formula.finalMultiplier` | 1.14 | **1.55**（1.50~1.62） | 收官更重；见下方"W25 不叠乘"说明 |
| `formula.tailBaseMs` | 11500 | **按新节拍重算** | Par 时长基准，随节拍变快下调 |
| `formula.rewardBase` | 26 | 26（不动） | 收入端不主动加码 |
| `formula.rewardPeakMultiplier` | **新增** | **1.5** | 坎波（W5/10/15/20/25）波奖励 ×1.5 |
| `roles.air.weight` | 1.0 | 1.0（不动，L1 已 1.0） | — |
| `overrides` 中 `L1-gold-v6` | 230 | **删除** | 交给新曲线 |
| `overrides` 中 `L*-tighten` | 1.19~2.06 | **重算** | 见下 |

`L*-tighten` 是 30 条逐关乘区，原本用来补偿"单调性硬校验 + L1 抬高"。新曲线下必须重算：

- 先删掉全部 `L*-tighten` 与 `L1-gold-v6`；其余 level 级 override（如 `L3-gold` 这类历史金币覆盖）先留着，它们不影响 EHP 预算
- 让 `generate()` 产出原始预算
- 若 `validate` 报单调性失败，再用 `T_{L+1} = max(raw, T_L×1.003)` 做**前向最小修复**，重新生成等价的 tighten 值写回配方

**不要保留旧 tighten 值再叠加新参数**——两套补偿叠乘会把 L20 打到不可通关。

#### 5.4 出怪与构成

- `unlockSchedule`：空军保持 L1 W3 首现；每关再补 W8/W13/W18/W23 四个**解锁点**（它只决定"该波起角色可用"，实际是否出、出多少由 `composition()` 与 `roles.air.weight` 决定）。
- 重甲：L1 从 W8 起，L≥6 从 W5 起。
- 精英：L≥5 的 W15/W20；boss：L≥12 的 W25（现有规则不变）。
- `composition()` 里 L1 空中的硬编码分支（`0 if w<3 else max(1,floor(n*.13))`）改为数据驱动：读 `unlockSchedule` 决定首现波，比例用 `roles.air.weight` 反推。**这是脚本改动，属于本次授权范围**。

#### 5.5 星级与 Par

- `rating` 的三个血量 permille（500/750/900）与 `maxFourStarLeaks = 2` 不动——它们相对 `initialHp` 计算，生命改 12 后语义自动收紧。
- `fourStarTimePermille` 1250 → **1150**（限时收紧，逼玩家别磨）。
- Par 由 `tailBaseMs + tailTierGrowthMs × (stage-1)` 决定，节奏变快后需重算：保持"理想操作剩余时间 15%~30%"即可（`tailTierGrowthMs` 1500 可同批下调）。

---

### 6. 执行步骤

#### 阶段 A

1. **前置**：`git status` 干净（不干净先按项目规范一笔提交）；确认 Unity 未在编译/Play。
2. 备份 `Luban/Config/Datas` 与 `Luban/BalanceDesign` 到 `Versions/`。
3. 写 `migrate_split_level_tables.py`，先 `--dry-run` 打印将生成的 180 个文件与行数，人工核对 L01/L15/L30 三关。
4. 正式迁移 → 跑 Luban → 生成 `split-migration.json`，逐表核对行数与 hash。
5. 改造 `balance_pipeline.py`（4.4 的 10 条），跑 `inspect` 确认 `sourceHashes` 已覆盖新路径。
6. `preview --profile D04`（不写盘）→ 应报"无变化"或 plan 与当前 applied 一致；若报大量 diff 说明拆表改变了数据。
7. 改 `apply_levelmap_export.py`，编辑器实点一次地图「一键写入」验证回读。
8. **阶段 A 收尾验证**：`refresh_unity(force)` → 等 `isCompiling=false` → `read_console` 查 `error CS` 为 0 → PlayMode 跑第 1 关 3 波，确认出怪/地图正常。

#### 阶段 B

9. `inspect` 确认状态；把 `balanceRevision` 升到 `-v7`。
10. **先删 override**：删掉 `L1-gold-v6` 与全部 `L*-tighten`。不先删，旧值会把新 formula 覆盖掉（`L1-gold-v6` 的 230 会盖住 `initialGold` 的新曲线）。
11. 再按 5.3 改 formula → `preview --profile D04`（不写盘），导出 W1/W5/W6/W10/W25 对照表，检查坎/普比是否 ≥ 1.40。**不达标就继续调 `pressureMultiplier` / `waveLinear` / `waveQuadratic`，不要往下走。**
12. 若 `validate` 报单调性失败，按 5.3 的前向最小修复重算 `L*-tighten` 并写回；再次 `preview` 确认坎/普比未被修复动作抹平。
13. 实现 `rewardPeakMultiplier`（`generate()` 里 `rewardGold` 计算处，`w % 5 == 0` 时乘）。
14. `validate` → `simulate --level-min 1 --level-max 30 --profile D04 --strategy mixed`：**只做下界观察**（记录每关完成波次与漏怪）。**任何关卡 W1 全灭 = 参数过激，回第 11 步**；其余情况不因漏怪回调。
15. 用 `balance_fill_gate.py` 跑 30 关 reference：这是**通关判据**（7.2 第 10~12 条），具体参数以该脚本 `--help` 为准。不过关先看 `L*-tighten` 是否残留，再降 `pressureMultiplier` 0.02 重跑。
16. `simulate` 分别跑 D01 / D04 / D08，确认难度梯度单调。
17. `apply --profile D04` 正式写入。
18. Unity 菜单 `Tools/塔防/3. 导出配置表（Luban）`（`LubanExporter.cs` 直调 exe，自带 asmdef 备份还原；日志里 `[remove] FTProject.Gen.asmdef` 是中途行为，导出后用 `ls` 复核已还原）。
19. `refresh_unity(force)` → 域重载会断线，等 5~8 秒重连 → 核对实例与 `projectRoot` → `scriptCompilationFailed == false` → `read_console(types=["error"])` 无 `error CS`。
20. PlayMode 回放：SessionState 设 `FT.Balance.TestLevel/Profile/Strategy` → 菜单 `Tools/塔防/数值验证/运行隔离回放`（要求空闲 EditMode，自动切 main.unity，跑完自动退出）→ 读 `Library/BalanceWorkbench/PlayMode-*/status.json` 与 `unity-results.json`。至少跑 L1 / L10 / L20 / L30。
21. 真机（若需要）：重打 AB（菜单 9）→ deploy → 先跑 `启动热更服务器.bat`（三件套顺序不可乱）。
22. 收尾：先写记忆（日档 + `VOL_03`/`VOL_08` 分册），**全部改动一笔提交**（180 个 xlsx + pipeline + 文档 + 产物，不拆不挑）；提交后不再写盘。

---

### 7. 验收标准（逐条量化，仿真 + 编辑器双证）

#### 7.1 阶段 A（拆表正确性）

1. `Levels/L01..L30/` 六张表齐全，共 180 个文件；每个文件表头 3 行结构与主表一致。
2. 行数：Round 25 / EnemyList 25 / SceneInfo 1 / LevelMap 1 / LevelRating 1 / EnemyData ≥ 1（合计 10773）。
3. `tb*.json` 拆分前后按 id 排序逐字段一致；行数与 2.2 表格所列数字逐一相符。
4. Luban 导出 0 报错；无重复主键。
5. 运行时 PlayMode 进第 1 关，出怪序列与拆分前一致（对比 `EnemyList` 前 3 波 id 列表）。
6. 地图编辑器「一键写入」往返一致（⑤ 步通过）。

#### 7.2 阶段 B（节奏与数值）

对 D04，逐关检查：

| # | 指标 | 通过线 |
|---|---|---|
| 1 | 坎/普比 | 每关 W5/10/15/20/25 的环比 ÷ 相邻普通波环比 **≥ 1.40** |
| 2 | 普通波环比 | 非坎波 ∈ [1.01, 1.30]，且**不得出现 < 1.00**（单调性硬校验会拦）；坎后首波允许落在 1.02 的兜底平台 |
| 3 | 数量环比 | 相邻波 ≤ 1.20 |
| 4 | 开局可建塔数 | L1 ∈ [2.5, 3.5]；相邻关比值 ≤ 1.25 |
| 5 | 单关节拍 | Σ(spawn span) + 24×波间空档 ∈ [420s, 540s]（7~9 分钟） |
| 6 | 单波 span | W1 ∈ [5s, 9s]；W25 ∈ [18s, 28s] |
| 7 | 同屏峰值 | ≤ 160（Global `maxEnemyAlive` 200 的 80%） |
| 8 | 漏怪痛感 | `initialHp = 12`；四星要求漏 ≤ 2 |
| 9 | 空军节奏 | 首现 W3；含飞行波的间隔 ≤ 5 波；占比 12%~18% |
| 10 | 30 关可通关 | `balance_fill_gate.py` reference（会玩的玩家 / 理想驻防）在 D04 下 **30 关全部完成 25 波且剩余生命 ≥ 1** |
| 11 | 难度梯度 | 同一 reference 下 D01 全通、D04 全通、D08 通关率 ≥ 60%，且漏怪数 D01 < D04 < D08 |
| 12 | 五星可达 | 同一 reference 在 L1/L10/L20/L30 取得 ≥ 4 星，其中 L1 五星 |
| 13 | 运行回归 | Unity 编译 0 error；L1/L10/L20/L30 PlayMode 无异常日志 |

> **为什么不用 `simulate --strategy mixed` 判通关**：`mixed` 是"普通操作代理"，在 v6 现状下 L1 就只能打到 W20（总漏 18、完成 19/25 波）。新体系要更紧张，用它的完成波次当通过线会直接自相矛盾——越紧张越"不通过"。所以 `mixed` 只用于**观察下界**（记录每关完成波次与漏怪，写进报告，**不设通过线、不作为调参依据**），通关判据一律用 `balance_fill_gate.py` 的脚本化驻防。

> **关于"漏怪"的口径（沿用 2026-10-20 的既有指令）**：离线代理 `mixed` 漏怪**不作为失败判据**，也不作为继续调参的理由。它只是"普通操作代理"的下界，不代表真人上限。第 10 条只要求"能跑完全部波次"，第 12 条用 fill-gate 脚本化驻防作为真人理想操作的上界。真实手感以实机试玩为准，仿真达标即可进入 apply。

> 第 10 条若有跑不完 25 波的关：先看是不是 `L*-tighten` 残留叠乘（5.3 警告），再降 `pressureMultiplier` 0.02 重跑。**不要用"降低高关 initialGold"去救**——那会把 5.2 的曲线打回断层。

---

### 8. 红线

- 禁止手改 `Luban/Config/Datas/**/*.xlsx` 与 `Assets/ConfigJson/tb*.json`：全部由脚本生成。拆表后"每关一个文件"**不等于**"可以手工编辑某个关卡文件"——手工改会在下次 apply 被覆盖并破坏 header 契约。
- 不改运行时 C#（`Assets/Scripts/**`）。本次所有改动都在 Excel 结构 + Python 管线 + 配方。
- 不改 `validate()` 的单调性硬校验；不为了让波形好看而放宽它。
- 不新增/删除关卡，不改地图格子内容，不动塔价与塔属性。
- 不复活已删除的塔编号；不改 `FreeTower` 包裹名、`FTProject` 命名空间。
- 编辑器脚本不弹 `DisplayDialog`，结果走 `Debug.Log`；改过 `Assets/Editor/*.cs` 必须等编译完成再跑菜单。
- 跑生成/挂载菜单前确认 `isCompiling == false && isPlaying == false`。
- 每轮只动 5.3 白名单字段；改完 `git diff` 自查没有碰白名单外内容。
- 阶段 A 与阶段 B 不要混在一次 apply 里；混了就失去等价性二分能力。

---

### 9. 交付物

1. `Luban/Config/Datas/Levels/L01..L30/`（180 个文件）+ 精简后的主表 + 改写后的 `__tables__.xlsx`。
2. 改造后的 `.workbuddy/tools/balance_pipeline.py`（含 `verify-layout`）+ 新增 `migrate_split_level_tables.py` + 改造后的 `apply_levelmap_export.py`。
3. `Docs/BalanceEvidence/split-migration.json`（拆表前后行数/hash 对照）。
4. 新配方 `balance_design.json`（`balanceRevision = balance-30x25-tight-v7`）+ apply 产物（xlsx/ConfigJson/Gen/applied_state）。
5. 仿真报告：30 关通过率、每关 5 个坎的环比表、开局可建塔数曲线。
6. PlayMode 回放结果（L1/L10/L20/L30）。
7. 对话内简报：阶段 A 等价性结论 + 阶段 B 每项验收打勾；任何未达标项写明卡在哪、当前值、下一步建议，**不得静默降级**。

---

### 10. 风险与降级

| 风险 | 现象 | 处置 |
|---|---|---|
| `input` 清单过长导致 Luban 变慢 | 导出时间从 <1s 涨到数秒 | 可接受；若 >30s，改用"每关目录 + 单一 input 通配符"（需先验证 Luban 是否支持 `*`，不支持就维持现状） |
| 30 文件 × 6 表让 apply 变慢 | 写盘时间线性增长 | 先按串行实现（180 个小文件通常几秒）；只有实测 >60s 才考虑按 L 并行，且必须避开 `job_lock` 的临界区 |
| 旧聚合文件被其他脚本读取 | 某工具读不到 `Datas/RoundData.xlsx` | 4.5 已覆盖地图编辑器；其余为历史一次性脚本（`add_levels_*`、`apply_m2_*`、`gen_wave_data.py` 等），**不修**，在文件头加 `# LEGACY: 拆表后失效，勿运行` |
| git 仓库膨胀 | 180 个二进制 xlsx | 单关文件很小（Round 25 行约 8KB），总量与原来相当；不要为省体积去掉表头样式 |
| 手工误改单个关卡文件 | 只有一关数据被改，难察觉 | `verify-layout` 增加"文件 mtime 晚于 applied_state 但 hash 不符"告警；提交前跑一次 |
| 阶段 B 参数过激 | 高关 W1 全灭 | 回 5.3 白名单，按 0.02 步长回调 `pressureMultiplier`；禁止降 `initialGold` 斜率救火 |
| 单调性校验挡住坎 | `validate` 报 `not strictly increasing` | 用 5.3 的前向最小修复重算 `L*-tighten`；不要放宽校验 |

**降级方案**：若阶段 A 因 Luban 行为差异无法做到"语义等价"，退回到"只拆 RoundData / EnemyList / EnemyData 三张大表，SceneInfo/LevelMap/LevelRating 保持单表"——这三张是行数爆炸的主因（750/750/10773 行），拆完已解决 95% 的可读性问题。

--- PROMPT 结束 ---
