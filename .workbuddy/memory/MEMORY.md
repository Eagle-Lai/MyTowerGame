# FreedomTower 项目长期记忆（索引）

> **记录原则（用户已明确）**：不要精简、不要为了篇幅砍内容；过期内容只标注不删。
> **结构**：本文件只放「索引 + 一行铁律摘要」；逐条细节、参数、踩坑原因在分册。需要完整条文时读 `VOL_08`（全文，逐字保留）。
> 2026-11-04 拆分原因：本文件 18.9KB 注入时被截断，尾部铁律丢失；改为索引 + `VOL_08_开工铁律全文.md`。
> 2026-11-08 再次瘦身：21.8KB 又被截断 → L02 多轮迭代条目**逐字搬入 `VOL_09`**、包体/字体/图集/手势等六条**逐字搬入 `VOL_10`**（均未删改），本文件降到约 **15KB**。

## 分册目录
| 分册 | 内容 |
|---|---|
| `VOL_08_开工铁律全文.md` | **开工必读铁律全文**（2026-11-04 从本文件逐字拆出，未删改） |
| `VOL_01_环境流程与出包.md` | 双版本路径、命名、生成/挂载前置、编辑器脚本约定、提交规范、git 代理、APK 出包、真机 adb |
| `VOL_02_热更与资源.md` | 程序集与 HybridCLR、dll/AB 链路、UDP 发现与闸门、一键热更菜单 10、部署、配置加载失败自恢复 |
| `VOL_03_配置多语言与UI.md` | Luban 表、多语言词条、TextLocalizer、UIPrefabBuilder、全量重建副作用、HUD 两按钮 |
| `VOL_04_适配与SuperScrollView.md` | 多分辨率三组件、安全区、边缘锚数值、SuperScrollView 吸附约束 |
| `VOL_05_玩法存档音频与地图.md` | 关卡生命周期、存档、音频/倍速、塔型与攻击表现、建造交互、地图链路、新增关卡 |
| `VOL_06_敌人四方向.md` | AdvancedHen / Monkey 两套架构、构建器与校验坑、AI 分件美术 |
| `VOL_07_工具与UnityMCP.md` | 多实体工程 MCP 规则 + 历史端口线索、**Codex stdio 起不来 MCP 的根因与修复（2026-11-05）**、Python/脚本兜底、怪物素材、待办与环境事实 |
| `VOL_09_L02数值迭代全过程.md` | **L02 多轮数值迭代逐字归档**（2026-11-08 从本文件搬出，未删改）：×1.2/×1.5 血量四轮、空中 ×1.5、19:20 整体重设计、20:13 W6–W25 +50% |
| `VOL_10_包体优化与交互细节.md` | **包体/字体/图集/手势/建造图标/BuildApk 六条逐字归档**（2026-11-08 从本文件搬出，未删改） |

## 开工必读铁律（摘要；★=优先级，详见 `VOL_08` 同名条目）
- ★★★**“手动改表”=代码定点修改（2026-11-05 用户澄清，覆盖旧的脚本禁令）**：程序定点定位获授权的单元格/唯一 ID，核对预期旧值后写入新值，保留改前基准、写后回读证明白名单外零改动；禁未授权扩范围/整表重建/擅自批量调平；源表仍走标准 Luban 导出。全文见 `VOL_08` 与 `AGENTS.md`「配置表按授权定点维护」。
- ★★★**空中怪不得相邻出生（2026-11-05）**：按 `EnemyData.isFlying != 0` 判断，任意种类/ID 的空中怪均不得相邻（含跨编组/回合边界），只隔出生位置、不擅自加秒数；改顺序须保留每波 ID 多重集合/数量/属性/间隔。检查跑 `.workbuddy/tools/check_air_spawn_order.py`；跨关授权不自动延续，全文见 `VOL_08` / `AGENTS.md`。
- 双版本：[家用D] `D:\FreedomTower_1`｜[公司E] `E:\MyTowerGame`；记录标版本，严禁跨版套结论；同步走 GitHub `Eagle-Lai/MyTowerGame`(main)。
- ★★★**多实体工程 + MCP「失败即问」**：含历史 `D:\FishTestGame` 等；路径/Unity 版本/插件版本/端口/服务名一律按当次实际工程判断。MCP 失败/超时/空表/新会话/域重载/换工程 → 先三项只读核对身份（工作区 + `ProjectVersion.txt` + `manifest.json`）→ 一次低成本自检（插件窗口 URL / `MCPForUnity.HttpUrl` / 客户端配置）→ **定不了就停下来问用户端口**；**禁扫端口、禁试连、禁默认端口**（8080/8082/8084/8086/8088 都只是某次的实测值）。连上后 `set_active_instance` → `project/info` 核对 `projectRoot`。
  **2026-11-08 补充：WorkBuddy 侧 `uvx` 直启同样会卡 `initialize`（重试 4 次全 timeout）→ 三个客户端统一把 `~/.workbuddy/mcp.json` 的 command 换成 WorkBuddy 自带 python + `~/.codex/unity_mcp_launcher.py`，改完必须重启 WorkBuddy。** 先读 `~/.unity-mcp/unity-mcp-status-*.json`（`reason:"ready"` 就说明桥接健康、问题在客户端），别急着重启 Unity。
- 命名：`自由人塔防`=文档名｜`FREEDOM TOWER`=副标题｜`freedomtower`=包名｜`FreeTower`=YooAsset 包裹名（★改则热更全失效）｜`FTProject`=命名空间。
- 跑生成/挂载/导出前必须 `isCompiling==false && isPlaying==false`；改过 `Assets/Editor/*.cs` 等编译完；**动表与 Luban 导出前先查 `EditorApplication.isPlaying`，对局中就先等或问**（写 asmdef/json 会触发重导入甚至域重载）。
- 编辑器脚本不弹 `DisplayDialog`（走 `Debug.Log`）；危险操作拆两档菜单。
- ★提交：**按功能分批**（代码契约→工具→资产→文档，每笔不悬空）；**先写完记录再提交**（当天日档 + 本文件 + 分册同一笔）；提交后不再写盘。
- ★★**tag 不会跟着 `git push origin main` 走**（2026-11-08 用户追问）：git 默认只推分支历史，tag 必须显式 `--tags` 或 `--follow-tags`。此前仓库远端 **0 个 tag**（`第一关关卡的数值定稿` 自 2026-11-01 起一直只在本地），2026-11-08 已补推两个：`第一关关卡的数值定稿`(annotated→a3252c9e5)、`L01关卡数值定稿！！！`(lightweight→b27d9c3a0)。**发版/定稿打 tag 后必须单独推一次并 `ls-remote --tags` 复核**；带 `^{}` 的行是 annotated tag 的解引用提示，不是多出来的 tag。
- ★git 代理：先用环境默认 `http_proxy`（会变，先 `env | grep -i proxy`）；带 `-c http.version=HTTP/2`；**单笔 ≤20MB**（130MB 单 commit 必失败）；`cannot lock ref` = 并行竞态先 `ls-remote`；**不要装 git-lfs**；GitHub 偶发 5xx 重试 1-3 次即可过。
  **2026-11-13 补充：环境变量不是唯一来源** —— `~/.gitconfig` 存在 URL 级 `http.https://github.com.proxy`（当时指向已失效的 7892），**优先级高于 `-c http.proxy` 和环境变量**，表现为 `over proxy 127.0.0.1 after 2s` 直接拒连。排查先跑 `git config --show-origin --get-regexp proxy`，覆盖写 `-c http.https://github.com.proxy=http://127.0.0.1:7890`（空串=强制直连）。实测 15 笔 24.35MB 一次推成功。
- ★★出 APK 前核对 Build Settings：`Boot.unity` 启用 + `Main.unity` 禁用（main 只能从 AB 加载）。
- ★★**Luban 导出与 `Assets/Gen/FTProject.Gen.asmdef`**：直跑 exe/bat 会被 Luban 删掉该 asmdef → 必须 `git checkout -- Assets/Gen/FTProject.Gen.asmdef` 并确认 `git status` 无 ` D`；走编辑器菜单 `Tools/塔防/3. 导出配置表（Luban）` 会自动保留（`KeepFilesInCodeDir`）。差别只在「谁调的 Luban」。
- ★★改热更码真机三件套：重编 dll → AB 有变化才重打（菜单 9 后立刻 deploy）→ 先跑 `启动热更服务器.bat`。
- ★★**配置表只能手工改**（2026-10-21；“手工”含义已由上文 2026-11-05 澄清为代码定点修改）：`balance_pipeline.py` 的 `apply`/`rollback` 与事务层已整体删除，只保留只读命令（inspect/generate/preview/validate/simulate/verify-layout/stage）。流程＝代码定点改 xlsx → Luban 导出 → Unity 看 `[Config]` 汇总；不恢复旧流水线。
- ★★★**星级评分体系已整体删除**（2026-11-01）：`tblevelrating`、30 张 `LevelRating.xlsx`、`LevelRatingEvaluator/Profile/Result`、`Configs.VerifyRatingContent/CalculateRuntimeContentHash/…` 全移除；**通关一律记 5 星**，失败 0 星，存档字段保留兼容。改数值不再被哈希拦关。
- ★★★**改关卡数值必须先问范围、只改指定范围**（2026-11-01）：先问①哪几关②哪张表/波次/怪种/字段③改成多少（值/倍率/基准）④是否「全部关卡应用」；默认只改被点名的部分，禁顺手统一；跨关只有**当次请求**写明才可；改完必须报「改了哪些关/字段 + 旧值→新值 + 其余未动」的证据。
- ★★★**同一串数值需求连续下发，「替换 vs 叠加」每轮都要重新确认**（2026-11-01 踩坑）：上一轮确认过的口径不延续；脚本要参数化、基线固定为「改动前原值」（`.bak_*`），避免越跑越高。
- ★★★**跨关数值同步要按波次逐条映射，照抄≠等强度**（2026-11-03 L03←L02）：按 `(wave,name,isFlying)` 取源关 hp、独有怪留原值、构成等比取样、奖励取源关；SceneInfo/levelId/击杀奖励/speed/armor/waveType 不动。L03 曾掉到 0.68×，补缩放后 1.08×。
- ★★**以 L01 为模板重建 L02 全 25 波**（2026-11-04）：W1-W4 保留 20/30/36/42 只 + 130/135/140/145 金；W5-W25 按「出怪×144/91、地面 HP×71/42、空中 HP×15/12」，enemyInterval/waveType 照取 L01；全关 16,069 只 / 2,386 金。已知缺陷：L02 敌人行 `levelId` 仍为 1、SceneInfo 名称仍「关卡 1」。
- ★★★**改表不算完成，必须导表成功（2026-11-08 用户定规）**：动过 `Luban/Config/Datas/**` 源表后，**只有 Luban 导出真实成功、`Assets/ConfigJson` 更新、`[Config]` 汇总无失败表，任务才算结束**；「源表已改、导出未跑」只能报「未完成，卡在导出」，禁止当作完成收尾。多轮改表可合并成最后一轮后一次性导出，但不许跨天遗留。完整条文见 `AGENTS.md`「配置表按授权定点维护」末条。
- ★★★**L02 当前定稿状态（2026-11-08 19:20 重设计 + 20:13 前四轮血量上调；详细过程见 `VOL_09_L02数值迭代全过程.md`）**：重设计以 **L01 零漏怪通关版 Λ 曲线**为基准（α=1.0），数量 ×1.5、总经济 ≈7,200、地图与塔表不动 → **15,345 只**（空中 1,472）｜重设计基线 EHP **7,407,416**｜经济 **7,195.76**（初始 100 + 击杀 4,749.76 + 奖励 2,346）。其后 19:56/20:01/20:09 三轮「W5–W25 +25%」、20:13 一轮「W6–W25 +50%」，终值全关 EHP **21,647,953**（相对重设计 ×2.92），地面血量相对 L01：W6 起 ×4.1~4.55、W5 ×3.06；**Λ 曲线 W6 之后只有 L01 的 33~34%**（比 L01 难约 2 倍），且 **W5→W6 有台阶**。脚本 `_l02_redesign_20261108.py` / `_l02_hp_*_20261108.py`，文档 `Docs/L02_Rebalance_20261108/L02_重设计规格.md`。**已导表**（19:41:28 / 20:14:56 `== succ ==`）。
- ★★**L02 数值三条方法论（细则见 `VOL_09`，勿再翻旧轮脚本）**：①血量倍率算法必须是 `m = 地面EHP目标 / Σ(新数量×L01同类血量)`，漏乘数量倍率会让 EHP 偏高 1.5 倍（第一版踩过）；②加数量必须重建出生序列（「空中等距铺槽 + 地面按占比重采样」，空中最小间距 8），**直接复制条目会破「空中不相邻」**；③加数量要主动提示「击杀金币被数量放大」并给持平方案（按每波系数压缩 `reward`，`RoundData.rewardGold` 不动）。⚠️**19:20 重设计后 L02 血量已整体替换，11-07~11-08 早期的 hp 脚本 verify 全部失效，勿再运行**；核对金币必须「旧序列×旧 reward」对「新序列×新 reward」。
- ★★**证据入库体量口径**（2026-10-30）：结论级文本入库；生成图/运行帧/时序板/集中 GIF/`scope_*.json`/资源副本不入库。**例外**：`Artifacts/` 下零漏怪实战证据全量入库（1352 文件 /130MB），不外推到 `Docs/`。
- ★★**清理磁盘/删大目录**：safe-delete 钩子把删除移入回收站，必须 `Clear-RecycleBin -DriveLetter <X> -Force` 才真正释放；`Remove-Item` 完全无效且不抛异常 → **单文件用 `robocopy <dir> <tmp> <file> /MOV`，清目录用 `robocopy <空目录> <目标> /MIR`**。
- ★★**删 Library 的代价**：3 个 git 包（hybridclr 8.14.1 / unity-mcp 10.3.0 / yooasset 3.0.6）要重新 clone；删剩一半会弹 "Corrupted Library Detected" 并静默退出；从工具启动的 Unity 会被会话清理杀掉 → 最后让用户从 Hub 开。
- ★★**震屏白名单**（2026-10-30）：关卡内只有「漏怪」允许抖，开火/爆炸/命中/结算一律不震；唯一入口 `CameraController.ShakeOnEnemyLeak`，加抖动必须改 API 且先问。
- ★★**局内进度落盘 = 续玩快照**（2026-10-31，推翻 10-30「局内不落盘」）：每过一波存塔阵(row/col/type/level/investedGold)+金币+生命+波次游标+整份 `LevelRunMetrics` 到 kv `layout/campaign`，重进接着打；通关写「重玩起点」；`RefundOf=min(配置售价,累计投入)×返还比例` 唯一口径；卖塔立刻落盘。详见 `VOL_05`。
- ★★**真实子弹系统已删除**（2026-10-31）：塔即时命中；`tbbulletdata` 与 `TowerInfo.bulletId` 保留（AOE 半径/效果仍从这里取）；`BoardSorting.Bullet=400` 留给枪口焰。
- ★★**UI 品牌文案/字号 = 四层同步**（2026-11-02）：`Localization.xlsx` 源表 → `BootLocalization` 常量（AOT 启动层不能依赖热更 `TextLocalizer`）→ 实际 prefab → 生成器（`TacticalForgePrefabBuilder`/`UIPrefabBuilder`/`TacticalForgeLayout`）。品牌：`BrandTitleKey="FREEDOM TOWER"`、`BrandSloganKey` 见 `VOL_03` 第 385 行。
- ★★**包体优化与交互细节一组（逐字全文见 `VOL_10_包体优化与交互细节.md`）**：TMP 缺字只补字不换字体｜字体源文件是 7038 字子集版（新增文案后重跑 `gen_font_subset_chars.py`）｜怪物方向图集按内容裁紧且导入必须 `npotScale=None`｜建造按钮图标用 `TowerBuildIcons`｜`BuildApk` 校验读 `AndroidExternalToolsSettings`｜真机手势双指缩放+单指长按拖动。
- ★★**Codex 侧 unityMCP 只能经 python launcher 中转**（2026-11-05 家用 D 实测）：`uvx`/`uv`/`cmd` 直启一律 `connection closed: initialize response`，真根因是 Codex 不消费子进程 stderr（banner 写满管道阻塞握手）+ uvx trampoline 无法被 Codex 直接 spawn。解=`~/.codex/unity_mcp_launcher.py`（stderr 落 `~/.codex/unity-mcp-server.log`，不绑工程路径），`config.toml` 用 uv 自带 python 启动它；`env` 段非必需已删。改完**桌面版要重启**。WorkBuddy 侧 `mcp.json` 一直正常，别跟着改。详见 `VOL_07`。
- ★★**波次回退/本波重试已上线**（2026-11-07）：HUD 右上四按钮＝暂停/重试本波/回到上波/菜单；检查点只在本局内存（不落盘、**不改存档 schema、不动星级**）；入口 `EventName.RestartWaveRequestEvent` / `RestartPreviousWaveRequestEvent`，可用性看 `GameFlowManager.CanRestartCurrentWave` / `CanRestartPreviousWave`；`LevelLayoutStore.CaptureCurrentLevel` / `SaveCapturedLevel` 复用一致边界捕获；`PlayerDataManager.GoldCarry` 随检查点恢复（重试不吞小数金）。准备态可连续回退到第一波开打前。改这块先读 `Docs/WaveRetry/2026-11-07/`。
  **⚠️ 2026-11-10 已覆盖其中「检查点只在本局内存、不落盘」一条**：开波历史 `WaveRestartHistory` 现与波次边界写在同一个加密 KV（`layout/campaign`）里成对持久化，退关/停止运行重进可逐波回退；回退后裁未来分支并落盘，显式新局立即替换旧局；接管前校验 runId/波次表/配置签名/已完成前缀，不符即禁用回退而不猜数据。入口与测试见 `Docs/WaveRetry/2026-11-10/persistent-history/` 与 `WaveHistoryPersistenceTests`。原文其余口径（不改星级、失败不覆盖生命、GoldCarry 随检查点恢复）仍有效。
- ★★**20 关地图重排**（2026-11-13 现有状态，前序会话完成、未写日档）：L06–L10、L23、L28、L29 障碍清零；L16/L20/L21/L22/L24/L26/L27/L30 障碍减量；L12/L13/L18–L24/L27–L30 起终点重排（L08/L09 终点移到角点）。源表 `LevelMap.xlsx` 20 份 + `tblevelmap.json` + `LevelPreviews` 20 张同步。L01–L05/L11/L14/L15/L17/L25 地图未动，难度影响未复核。
- ★★**同屏怪物上限 `maxEnemyAlive` 已整体下线**（2026-11-07）：TBGlobal 删字段、`EnemyManager.SpawnFailure.Capacity` 与 `WaveManager` 满员延迟全部移除，`LevelRunMetrics.spawnDeferredCount` 删除；平衡侧 `balance_sim.mjs` / `balance_simulator.py` / 报表列（`delayedSpawns`、`spawnDeferredSteps`）同步去掉。再看到"容量保护 / 延迟出怪"的口径都是旧文档。
- 日档 `YYYY-MM-DD.md` 追加写，读最近的在最前。
