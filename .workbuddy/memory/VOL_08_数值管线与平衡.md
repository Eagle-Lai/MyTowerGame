# VOL_08 数值管线与平衡（balance_pipeline）

> 2026-10-20 建立。来源：v5 收敛（10-19/20）+ 第一关重平衡 v6 执行全程。
> 原则：宁可全，不要省——这里全是排查过的坑和推导过的结论。

## 管线结构与命令
- 唯一权威编译器 `.workbuddy/tools/balance_pipeline.py`（1145 行），配方 `Luban/BalanceDesign/balance_design.json`。xlsx/ConfigJson/Gen 全是生成物，**禁止手改**。
- 必须用 venv python（有 openpyxl）：`C:/Users/78296/.workbuddy/binaries/python/envs/default/Scripts/python.exe`。全局 3.13.12 没有 openpyxl（inspect 会显示 openpyxlAvailable:false），apply 会挂。
- 命令链：`inspect`（核对 applied 状态）→ 改配方（revision 升位）→ `preview --profile D04`（不写盘）→ `validate` → `simulate --level-min/max` → `apply --profile D04`（写 xlsx+评级+applied_state，50 文件）。输出都在 `Library/BalanceWorkbench/<job>`。
- `simulate` 不跑 validate；apply 内含 validate。strategy: normal/power/mixed/mistake/optimized（离线策略，见下"代理局限"）。

## 核心公式（generate()）
- 数量 `n = countOffset + countLevelCoefficient×L + countWaveCoefficient×w`（整数必须，positive_int 拒小数）。
- EHP 预算：`raw = n×baseEhpPerUnit×(1+levelEhpGrowth×(L-1))×(1+waveLinear×x+waveQuadratic×x²)`，x=w-1；w%5==0 ×pressureMultiplier(1.12)，收官波 ×finalMultiplier；再取 `max(raw, 前波×minBudgetGrowth, 上关同波×minBudgetGrowth)`；profile.ehpMultiplier；最后 wave 级 override（L*-tighten）multiply。
- **预算连续性从不生效**：只要相邻 raw 比值 >minBudgetGrowth(1.02)，budget=raw（v6 下已验证成立）。调参时不用考虑复利项。
- 单怪 hp = targetEhp×weight/Σweight×(1-armor)；击杀金币=roles.reward（与 EHP 无关，goldPerEhp=0）。
- composition() 出怪构成是**脚本硬编码**：L≥2 空中 = w≤5/w∈(11,16) 为 0，否则 floor(n×8%/12%)；精英只在 w15/20 且 L≥5、收官波 boss/elite 兜底（L1 无 boss 时用 canonicalId 123 填 elite）。v6 起 L1 空中改为数据驱动（见下）。
- unlockSchedule 注入机制：解锁波当波若该 role 不在 slots，会**替换最后一个 slot**（不增数量）。

## 硬校验（validate，apply 必过）
- ★★逐关逐波 EHP/数量**严格递增**（对 (L,w-1) 和 (L-1,w) 都要 >）。绑定波是 W25（数量比随 w 递减）。改 counts 或 L1-tighten 会打破它 → 对 L2~L30 做前向最小修复：`T_{L+1} = max(v5值, T_L×(N_L×G_L)/(N_{L+1}×G_{L+1})×1.003)`，N_L=160+2L，G_L=0.98+0.02L。v6 实测 27 关各 +0.9%~+3.9%。
- 其余：跨表 hash、EHP ±0.5%、prefab/注册存在性、塔价链、rating 字段、Par>spawn span。

## v6 第一关重平衡（apply-v6-20261020, revision balance-30x25-tight-v6）
- 白名单内：countOffset 6→10、countWaveCoefficient 3→6、countLevelCoefficient 2（不动）、rewardBase 22→26、minSpawnMs 240→200、roles.air.weight 0.3→1.0；formula.initialGold 620 不动（保 L2+ 开局）。
- L1 专属（白名单外，用户授权）：L1-tighten 1.191→**1.9175（K=1.61）**；新增 L1-gold-v6 override（initialGold replace 230，先例 L3-gold 等 9 个）；unlockSchedule air W7/W8/W10→W3/W4/W5。
- 脚本两处（用户授权）：composition L1 空中改 `0 if w<3 else max(1,floor(n*.13))`（air1 表删除）；守卫 `L==1 and w<7`→`w<3`。
- L1 结果：initialGold 230、W1 N=18/EHP 345/hp19、W3 首批 3 飞行、W10 72 只/EHP 5415、W15 EHP 14090、W25 162 只/EHP 55215/普通怪 hp 297、总怪量 2250、飞行 276=12.3%、含飞行波 23/25、spawn W25=210ms。
- **K=1.61 的由来**：单调性硬校验给出 K 上限 1.614（L1W19 对 L2 的比较，r=0.969），K≥1.866 才能满足 W1 EHP≥400 → W1/W25 两窗口与「不碰 L2~L30」不可兼得，用户拍板保梯子。K=2.4（prompt 原意）会强制 T2~T30 级联 +20%~+92% 且收入跟不上 → L20 实测 W1 全灭（A 方案）。
- **总怪量 2400 与 W25≤170 数学互斥**：线性 n 下 Σ=25s+325cw，W1∈[16,20]+W25≤170 ⇒ Σ≤2300。取 2250（s=12,cw=6）。用户"不做限定"。

## 用户指令（2026-10-20 明确）
- ★「如果当前数值出现漏怪了，不要修改，视为符合要求」——仿真/回放漏怪不作为调参依据，如实记录即可。
- ★「按照当前内容保持，后续我自己玩了觉得数值不对的话，我会再修改」——不做大重校准，不动收入端（roles.reward/goldPerLevel 均未动）。
- 授权改管线脚本两处（L1 飞行排布 + W3 守卫）。红线仍是：不改运行时 C#、不手改 xlsx/ConfigJson、编辑器脚本不弹窗。

## 离线仿真代理的局限（重要）
- mixed（普通操作代理）在 L1 新经济下 **W20 倒下**（PlayMode 实测：W1~14 零漏、W15 漏 4、W20 hp0，总漏 18、杀 1425/2250、完成 19/25 波、金币死亡时 645）。优化点在塔位升级份额策略，不代表真人上限。
- optimized 策略在低开局经济（≤230）下 W4 就崩（它的建墙优先开局依赖高 initialGold），不能当"理想操作"代理；真正的五星 reference 是 fill-gate 脚本化驻防（balance_fill_gate.py）。
- A 方案（prompt 建议值全套：base 24/levelGrowth 0.07/wl 0.12/wq 0.028）L20 W1 即全灭（EHP ×10 vs 收入 ×1.5）——**全局公式动不得，L1 增压只能走 L1 专属 override**。严格白名单内数学不可行（L1 要 base≥18.6 vs 30 关可通关要 base≤10.6）。
- 实验证据存 `Library/BalanceWorkbench/v6-experiments/`（recipeA/B/B2/B3 + 各 sim 输出）。

## apply 后链路（v6 实测）
1. `apply` → 2. Unity 菜单 `Tools/塔防/3. 导出配置表（Luban）`（LubanExporter.cs 直调 exe，**自带 asmdef 备份还原**；日志里 Luban 的 `[remove] FTProject.Gen.asmdef` 是中途行为，导出后已还原，用 ls 复核）→ 3. `refresh_unity(force)`（会域重载断线，等 5~8s 重连）→ 4. execute_code 查 `scriptCompilationFailed` → read_console 查 error CS（历史遗留 Unity Remote Exception 可忽略）→ 5. PlayMode：SessionState `FT.Balance.TestLevel/Profile/Strategy` → 菜单 `Tools/塔防/数值验证/运行隔离回放`（要求空闲 EditMode，自动设 main.unity 为启动场景、跑完自动退出），输出 `Library/BalanceWorkbench/PlayMode-*/`（status.json 可轮询，unity-results.json 为终局）。
- 真机生效还差：重打 AB（菜单 9）→ deploy → 启动热更服务器.bat（三件套，本次未做，用户未要求）。

## v7：按关拆表 + 节奏重构（2026-10-21 实测落地）

### 表结构（★永久变更，后续所有数值工作都按这个找表）
- `Luban/Config/Datas/Levels/L01..L30/` 每关 6 个 xlsx：`SceneInfo / RoundData / EnemyList / LevelMap / LevelRating / EnemyData`，共 180 个。
- `Datas/EnemyData.xlsx` 只剩 **132 行原型**（id<100000）；关卡变体（desc 含 `level=N; wave=M`）全部进各自 `Levels/Lxx/EnemyData.xlsx`（每关 186~393 行）。
- `Datas/` 根下 `SceneInfo/RoundData/EnemyList/LevelMap/LevelRating.xlsx` **已删除**；`__tables__.xlsx` 的 `input` 列改成 30 个 `Levels/Lxx/xxx.xlsx`，`TBEnemyData` 第一位是 `EnemyData.xlsx`（原型必须先入表，32 个路径）。
- 迁移脚本 `.workbuddy/tools/migrate_split_level_tables.py`（`--dry-run` 先看行数）；备份在 `Luban/BalanceDesign/Versions/split-20261021_104857/`；证据 `Docs/BalanceEvidence/split-migration.json`。
- **等价性实测**：拆分前后 `Assets/ConfigJson/tb*.json` 8 张表**字节完全一致**，只有 `tbrounddata/tbenemylist/tbenemydata` 三张的行序变了（改为按 L01..L30 分块，id 不再全局升序）→ `runtimeContentHash` 随之变，这是**唯一**允许的表内变化。
- 判据链条：`SceneInfo.RoundList → RoundData → EnemyList`，变体归关**只认 desc 的 level=**（id 数值范围含 profile 位，不可猜）。

### 管线改造（10 处，函数级）
- 新增常量 `LEVEL_TABLES / LEVEL_TABLE_FILES / LEGACY_AGGREGATES`、`level_rel/level_path/level_file_path`、`level_row_index(plan)`、`table_sources(table)`、`sync_tables_input()`、`verify_layout()`。
- `excel_write` 改成"复制整棵 Datas（含 Levels）→ 按 L 分组逐文件写"，`tbenemydata` 原型写主表、变体写分关文件；新增文件从主表克隆表头。
- `write_rating_excel(datas_root, rows)` 签名变了（原来是单文件路径）。
- `commit_files` 支持 `src=None` 的**删除事务项**（旧聚合文件必须消失，回滚从 backup 恢复）。
- `check_managed_conflicts` 改为"跨所有 Levels 文件建 id→文件索引 + 同 id 出现在两个文件即报错"（约 5s）。
- 新子命令 `verify-layout`：30 目录 × 6 表齐全 / 归属闭包 / 无重复主键 / `__tables__` 与磁盘一致。**apply 前会自动跑一次**。
- `composition()` 空军改成数据驱动：`air_first` 取 `unlockSchedule` 里 air 最小 wave，占比取 `roles.air.share`（不再写死 L1=13%、L>1=8%）。
- `generate()` 新增 `formula.rewardPeakMultiplier`（`w%5==0` 时波奖励乘）。

### v7 数值（balance-30x25-tight-v7 / D04）
`initialGold 100, goldPerLevel 20, initialHp 12, autoNextRoundDelayMs 2500`；
`countLevel 1 / countWave 6 / countOffset 38`（n=L+6w+38，45→218）；
`baseEhpPerUnit 5.5, levelEhpGrowth 0.008, waveLinear 0.015, waveQuadratic 0.0321`；
`pressureMultiplier 1.46, finalMultiplier 1.78, minBudgetGrowth 1.02`；
`spawnBase 280, spawnWaveReduction 7, spawnLevelReduction 2, minSpawn 128, maxSpawn 280`；
`tailBaseMs 10000, tailTierGrowthMs 400`；`fourStarTimePermille 1150`；`roles.air.share 0.12 / weight 0.45 / damage 1`。
- **overrides 全清**（40 条：L1-gold-v6 + 30 条 L*-tighten + 9 条历史 L*-gold）。历史金币覆盖与新曲线直接冲突（L5=2060 对曲线 180），必须一起删，否则 7.2#4 必挂。
- 实测指标：坎/普比 1.567（备用口径 1.441）；数量环比 ≤1.194；L1 开局 3.12 塔；单关 510~536s（8.5~8.9min）；W25 span 22.3~26.0s；W25/W1 148~199；空军首现 W3、间隔 1、占比 11~13%。
- **三处未达标（已写进报告，不许静默降级）**：① 普通波环比 max 1.312（W4，超 0.012）；② 后期关 W1 span 到 13.1s（数量必须逐关递增 + W1 要 5~9s 数学上不可兼得，只保住 L1~L3）；③ 空军占比 11.1%（floor 取整，低于 12% 下限 0.9 个点）。

### Par 校准（★顺序不能反）
`balance_fill_gate.py run --levels 1..30` → `balance_par.py calibrate --run <gate目录> --out ... --write --force`。**必须先冻结数值再写 Par**（`combatBasisHash` 覆盖 targetEhp/塔/子弹/地图/节奏，改任何一项 Par 全部失效）。校准后 `parCalibrationCurrent` 应 = 30（v7 L3 因参考驻防漏 1 只被工具跳过，手工补了一条，par=671000）。
- gate 的 G4 时间带是 `0.90 ≤ combat/par ≤ 1.05`；校准因子 x1.06 → 实测都在 0.943~0.944。

### fill-gate 实测（v7）
- **30 关满驻防 + 升级：29 关 0 漏 12 血通关，L3 漏 1 只（11 血）**——满足"完成 25 波且剩余生命 ≥1"。
- 但**占位阶梯 G1/G2/G3 在多个关卡不成立**（50%/85% 驻防也能清场）→ 难度与驻防规模脱钩，这是"压平 `levelEhpGrowth` + 压平数量曲线"的直接副作用，是**已知未解决项**。
- **空军是唯一的结构性杀手**：只要 `roles.air.weight=1.0`，地面迷宫型参考驻防在 W25 必漏 ≥6 只（12 血直接归零）→ 30 关全灭。把 weight 降到 0.45 后 29/30 过关。真机手感是否"空军太软"需实机确认。

### PlayMode 实测（v7 / D04 / mixed）
L1 18/25 波、L10 19/25、L20 19/25、L30 19/25，全 `hp=0`（mixed 代理在 W18~19 崩）。**mixed 只作下界，不作判据**；但它"各关都到 18~19 波"说明关卡间难度体感被压平（与 G1~G3 不成立同源）。
- 批量回放用法：写 `Library/BalanceWorkbench/play-request-batch.json`（runs 数组）→ `execute_code` 调 `FTProject.EditorTools.BalancePlayModeVerifier.StartBatch(path)`，4 关一次跑完只要 14s（40 步/帧 × 0.05s）。

## 2026-10-21 用户定规：配置表只能手工改（apply 已删除）

- `balance_pipeline.py` 删除：`apply_plan`、`commit_files`、`job_lock`、`restore_transaction`、`rollback`、`check_managed_conflicts`、`assert_sources`；CLI 去掉 `apply`/`rollback`，`main()` 前置拦截给中文错误。
- 新增 `assert_safe_out()`：`stage` 的 `--out` 落到 `Luban/` 或 `Assets/` 直接拒绝。
- `verify_layout` 放宽：手工改表产生的"孤儿行 / 未被引用的 enemyList"降级为 `notes`；"引用了不存在的变体"仍是 `problems`。
- 删除 7 个会写关卡表的脚本（都在 git 历史里）：`migrate_split_level_tables.py`、`migrate_config.py`、`gen_m3_levelmaps.py`、`gen_m3_waves_rounds.py`、`apply_m2_monsters.py`、`add_levels_9_15_20261017.py`、`add_levels_16_20_20261017.py`；`test_balance_transactions.py` 一并删（测的是已移除的事务层）。
- 保留：`apply_levelmap_export.py`（地图编辑器写单关 LevelMap）、`_manual_l1_tune.py`（按倍率改 L1 的人工工具）。
- **手工改表标准流程**：改 `Levels/Lxx/*.xlsx` → `Luban.ClientServer.exe -j cfg -c <cache> -- -d Defines/__root__.xml --input_data_dir Luban/Config/Datas --output_code_dir <tmp>/Gen --output_data_dir Assets/ConfigJson ...`（或 Unity 菜单 3）→ 重算 `runtimeContentHash`（算法见 `Configs.CalculateRuntimeContentHash`，Python 复刻已验证能对上旧值）→ Unity 日志确认 `[Rating] Runtime configuration SHA256 verified`。
- 回归：`test_balance_pipeline.py` 17 项全过；`verify-layout` 通过（L1 有 3 行孤儿变体，属手工换空军后的正常残留）。
