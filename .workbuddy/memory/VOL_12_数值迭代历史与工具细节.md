# VOL_12：数值迭代历史归档 + Codex/波次回退细节（逐字搬出）

> 2026-11-17 从 `MEMORY.md` **逐字搬出，未删改**；原因：本文件再次超过注入上限被截断。
> 这些条目的**数值结论已被 V3 定稿（2026-11-16）整体覆盖**，只作历史与踩坑档案；方法论与工具细节仍可参考。
> 现行口径见 `MEMORY.md`「V3 定稿」条与 `Docs/BalanceV2/07_V3_定稿L01基准换算.md`。

## 一、L02 模板重建（2026-11-04）

- ★★**以 L01 为模板重建 L02 全 25 波**（2026-11-04）：W1-W4 保留 20/30/36/42 只 + 130/135/140/145 金；W5-W25 按「出怪×144/91、地面 HP×71/42、空中 HP×15/12」，enemyInterval/waveType 照取 L01；全关 16,069 只 / 2,386 金。已知缺陷：L02 敌人行 `levelId` 仍为 1、SceneInfo 名称仍「关卡 1」。

## 二、30 关数值体系 V2 落表（2026-11-15，已被 V3 覆盖）

- ★★★**30 关数值体系 V2 已全量落表（2026-11-15，覆盖此前所有关卡数值口径）**：三型塔 30 关共用一套参数、`sellRefundRate=0.7`、W1–W4 无空中、W5 起空中占等效血量 25%–35%、地速 S1 1.0→S5 1.3、怪数约旧版 ×2.5；参照解 750 波零漏怪，再低 10% 则 708/750 漏。链路 `RefSim → table_plan.json → apply_v2_tables.py`，落表后必跑 `check_air_spawn_order.py`。**细节/命令见 `VOL_11`；旧的 L02 定稿数字（下一条）已作废。**

## 三、L02 定稿状态（2026-11-08，已被 V2/V3 二次覆盖）

- ⚠️**下面这条 L02 定稿口径已被 11-15 的 V2 覆盖，原文保留仅作历史档案**，`_l02_hp_*` 系列脚本不要再运行、不要拿来对账。

- ★★★**L02 当前定稿状态（2026-11-08 19:20 重设计 + 20:13 前四轮血量上调；详细过程见 `VOL_09_L02数值迭代全过程.md`）**：重设计以 **L01 零漏怪通关版 Λ 曲线**为基准（α=1.0），数量 ×1.5、总经济 ≈7,200、地图与塔表不动 → **15,345 只**（空中 1,472）｜重设计基线 EHP **7,407,416**｜经济 **7,195.76**（初始 100 + 击杀 4,749.76 + 奖励 2,346）。其后 19:56/20:01/20:09 三轮「W5–W25 +25%」、20:13 一轮「W6–W25 +50%」，终值全关 EHP **21,647,953**（相对重设计 ×2.92），地面血量相对 L01：W6 起 ×4.1~4.55、W5 ×3.06；**Λ 曲线 W6 之后只有 L01 的 33~34%**（比 L01 难约 2 倍），且 **W5→W6 有台阶**。脚本 `_l02_redesign_20261108.py` / `_l02_hp_*_20261108.py`，文档 `Docs/L02_Rebalance_20261108/L02_重设计规格.md`。**已导表**（19:41:28 / 20:14:56 `== succ ==`）。

## 四、L02 数值三条方法论（细则原在 `VOL_09`）

- ★★**L02 数值三条方法论（细则见 `VOL_09`，勿再翻旧轮脚本）**：①血量倍率算法必须是 `m = 地面EHP目标 / Σ(新数量×L01同类血量)`，漏乘数量倍率会让 EHP 偏高 1.5 倍（第一版踩过）；②加数量必须重建出生序列（「空中等距铺槽 + 地面按占比重采样」，空中最小间距 8），**直接复制条目会破「空中不相邻」**；③加数量要主动提示「击杀金币被数量放大」并给持平方案（按每波系数压缩 `reward`，`RoundData.rewardGold` 不动）。⚠️**19:20 重设计后 L02 血量已整体替换，11-07~11-08 早期的 hp 脚本 verify 全部失效，勿再运行**；核对金币必须「旧序列×旧 reward」对「新序列×新 reward」。

## 五、Codex 侧 unityMCP 只能经 python launcher 中转（2026-11-05 家用 D 实测）

- ★★**Codex 侧 unityMCP 只能经 python launcher 中转**（2026-11-05 家用 D 实测）：`uvx`/`uv`/`cmd` 直启一律 `connection closed: initialize response`，真根因是 Codex 不消费子进程 stderr（banner 写满管道阻塞握手）+ uvx trampoline 无法被 Codex 直接 spawn。解=`~/.codex/unity_mcp_launcher.py`（stderr 落 `~/.codex/unity-mcp-server.log`，不绑工程路径），`config.toml` 用 uv 自带 python 启动它；`env` 段非必需已删。改完**桌面版要重启**。WorkBuddy 侧 `mcp.json` 一直正常，别跟着改。详见 `VOL_07`。

## 六、波次回退 / 本波重试（2026-11-07 上线，2026-11-10 持久化修正）

- ★★**波次回退/本波重试已上线**（2026-11-07）：HUD 右上四按钮＝暂停/重试本波/回到上波/菜单；检查点只在本局内存（不落盘、**不改存档 schema、不动星级**）；入口 `EventName.RestartWaveRequestEvent` / `RestartPreviousWaveRequestEvent`，可用性看 `GameFlowManager.CanRestartCurrentWave` / `CanRestartPreviousWave`；`LevelLayoutStore.CaptureCurrentLevel` / `SaveCapturedLevel` 复用一致边界捕获；`PlayerDataManager.GoldCarry` 随检查点恢复（重试不吞小数金）。准备态可连续回退到第一波开打前。改这块先读 `Docs/WaveRetry/2026-11-07/`。
  **⚠️ 2026-11-10 已覆盖其中「检查点只在本局内存、不落盘」一条**：开波历史 `WaveRestartHistory` 现与波次边界写在同一个加密 KV（`layout/campaign`）里成对持久化，退关/停止运行重进可逐波回退；回退后裁未来分支并落盘，显式新局立即替换旧局；接管前校验 runId/波次表/配置签名/已完成前缀，不符即禁用回退而不猜数据。入口与测试见 `Docs/WaveRetry/2026-11-10/persistent-history/` 与 `WaveHistoryPersistenceTests`。原文其余口径（不改星级、失败不覆盖生命、GoldCarry 随检查点恢复）仍有效。

## 七、git 代理与 tag 推送的踩坑原文（2026-11-08 / 11-13）

- ★★**tag 不会跟着 `git push origin main` 走**（2026-11-08 用户追问）：git 默认只推分支历史，tag 必须显式 `--tags` 或 `--follow-tags`。此前仓库远端 **0 个 tag**（`第一关关卡的数值定稿` 自 2026-11-01 起一直只在本地），2026-11-08 已补推两个：`第一关关卡的数值定稿`(annotated→a3252c9e5)、`L01关卡数值定稿！！！`(lightweight→b27d9c3a0)。**发版/定稿打 tag 后必须单独推一次并 `ls-remote --tags` 复核**；带 `^{}` 的行是 annotated tag 的解引用提示，不是多出来的 tag。
- ★git 代理：先用环境默认 `http_proxy`（会变，先 `env | grep -i proxy`）；带 `-c http.version=HTTP/2`；**单笔 ≤20MB**（130MB 单 commit 必失败）；`cannot lock ref` = 并行竞态先 `ls-remote`；**不要装 git-lfs**；GitHub 偶发 5xx 重试 1-3 次即可过。
  **2026-11-13 补充：环境变量不是唯一来源** —— `~/.gitconfig` 存在 URL 级 `http.https://github.com.proxy`（当时指向已失效的 7892），**优先级高于 `-c http.proxy` 和环境变量**，表现为 `over proxy 127.0.0.1 after 2s` 直接拒连。排查先跑 `git config --show-origin --get-regexp proxy`，覆盖写 `-c http.https://github.com.proxy=http://127.0.0.1:7890`（空串=强制直连）。实测 15 笔 24.35MB 一次推成功。

## 八、跨关数值同步的逐波映射口径（2026-11-03，V3 起已无跨关同步需求）

- ★★★**跨关数值同步要按波次逐条映射，照抄≠等强度**（2026-11-03 L03←L02）：按 `(wave,name,isFlying)` 取源关 hp、独有怪留原值、构成等比取样、奖励取源关；SceneInfo/levelId/击杀奖励/speed/armor/waveType 不动。L03 曾掉到 0.68×，补缩放后 1.08×。

## 九、删 Library 的代价（2026-11-04）

- ★★**删 Library 的代价**：3 个 git 包（hybridclr 8.14.1 / unity-mcp 10.3.0 / yooasset 3.0.6）要重新 clone；删剩一半会弹 "Corrupted Library Detected" 并静默退出；从工具启动的 Unity 会被会话清理杀掉 → 最后让用户从 Hub 开。

## 十、UI 品牌四层同步原文（2026-11-02）

- ★★**UI 品牌文案/字号 = 四层同步**（2026-11-02）：`Localization.xlsx` 源表 → `BootLocalization` 常量（AOT 启动层不能依赖热更 `TextLocalizer`）→ 实际 prefab → 生成器（`TacticalForgePrefabBuilder`/`UIPrefabBuilder`/`TacticalForgeLayout`）。品牌：`BrandTitleKey="FREEDOM TOWER"`、`BrandSloganKey` 见 `VOL_03` 第 385 行。

## 十一、局内进度落盘原文（2026-10-31）

- ★★**局内进度落盘 = 续玩快照**（2026-10-31，推翻 10-30「局内不落盘」）：每过一波存塔阵(row/col/type/level/investedGold)+金币+生命+波次游标+整份 `LevelRunMetrics` 到 kv `layout/campaign`，重进接着打；通关写「重玩起点」；`RefundOf=min(配置售价,累计投入)×返还比例` 唯一口径；卖塔立刻落盘。详见 `VOL_05`。
