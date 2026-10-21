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
