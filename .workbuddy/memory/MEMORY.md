# FreedomTower 项目长期记忆（索引）

> **记录原则（用户已明确）**：不要精简、不要为了篇幅砍内容；过期内容只标注不删。
> **结构**：本文件只放「索引 + 一行铁律摘要」；逐条细节、参数、踩坑原因在分册。需要完整条文时读 `VOL_08`（全文，逐字保留）。
> 2026-11-04 拆分原因：本文件 18.9KB 注入时被截断，尾部铁律丢失；改为索引 + `VOL_08_开工铁律全文.md`。

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
| `VOL_07_工具与UnityMCP.md` | 多实体工程 MCP 规则 + 历史端口线索、Python/脚本兜底、怪物素材、待办与环境事实 |

## 开工必读铁律（摘要；★=优先级，详见 `VOL_08` 同名条目）
- 双版本：[家用D] `D:\FreedomTower_1`｜[公司E] `E:\MyTowerGame`；记录标版本，严禁跨版套结论；同步走 GitHub `Eagle-Lai/MyTowerGame`(main)。
- ★★★**多实体工程 + MCP「失败即问」**：含历史 `D:\FishTestGame` 等；路径/Unity 版本/插件版本/端口/服务名一律按当次实际工程判断。MCP 失败/超时/空表/新会话/域重载/换工程 → 先三项只读核对身份（工作区 + `ProjectVersion.txt` + `manifest.json`）→ 一次低成本自检（插件窗口 URL / `MCPForUnity.HttpUrl` / 客户端配置）→ **定不了就停下来问用户端口**；**禁扫端口、禁试连、禁默认端口**（8080/8082/8084/8086/8088 都只是某次的实测值）。连上后 `set_active_instance` → `project/info` 核对 `projectRoot`。
- 命名：`自由人塔防`=文档名｜`FREEDOM TOWER`=副标题｜`freedomtower`=包名｜`FreeTower`=YooAsset 包裹名（★改则热更全失效）｜`FTProject`=命名空间。
- 跑生成/挂载/导出前必须 `isCompiling==false && isPlaying==false`；改过 `Assets/Editor/*.cs` 等编译完；**动表与 Luban 导出前先查 `EditorApplication.isPlaying`，对局中就先等或问**（写 asmdef/json 会触发重导入甚至域重载）。
- 编辑器脚本不弹 `DisplayDialog`（走 `Debug.Log`）；危险操作拆两档菜单。
- ★提交：**按功能分批**（代码契约→工具→资产→文档，每笔不悬空）；**先写完记录再提交**（当天日档 + 本文件 + 分册同一笔）；提交后不再写盘。
- ★git 代理：先用环境默认 `http_proxy`（会变，先 `env | grep -i proxy`）；带 `-c http.version=HTTP/2`；**单笔 ≤20MB**（130MB 单 commit 必失败）；`cannot lock ref` = 并行竞态先 `ls-remote`；**不要装 git-lfs**；GitHub 偶发 5xx 重试 1-3 次即可过。
- ★★出 APK 前核对 Build Settings：`Boot.unity` 启用 + `Main.unity` 禁用（main 只能从 AB 加载）。
- ★★**Luban 导出与 `Assets/Gen/FTProject.Gen.asmdef`**：直跑 exe/bat 会被 Luban 删掉该 asmdef → 必须 `git checkout -- Assets/Gen/FTProject.Gen.asmdef` 并确认 `git status` 无 ` D`；走编辑器菜单 `Tools/塔防/3. 导出配置表（Luban）` 会自动保留（`KeepFilesInCodeDir`）。差别只在「谁调的 Luban」。
- ★★改热更码真机三件套：重编 dll → AB 有变化才重打（菜单 9 后立刻 deploy）→ 先跑 `启动热更服务器.bat`。
- ★★**配置表只能手工改**（2026-10-21）：`balance_pipeline.py` 的 `apply`/`rollback` 与事务层已整体删除，只保留只读命令（inspect/generate/preview/validate/simulate/verify-layout/stage）。流程＝手工改 xlsx → Luban 导出 → Unity 看 `[Config]` 汇总。
- ★★★**星级评分体系已整体删除**（2026-11-01）：`tblevelrating`、30 张 `LevelRating.xlsx`、`LevelRatingEvaluator/Profile/Result`、`Configs.VerifyRatingContent/CalculateRuntimeContentHash/…` 全移除；**通关一律记 5 星**，失败 0 星，存档字段保留兼容。改数值不再被哈希拦关。
- ★★★**改关卡数值必须先问范围、只改指定范围**（2026-11-01）：先问①哪几关②哪张表/波次/怪种/字段③改成多少（值/倍率/基准）④是否「全部关卡应用」；默认只改被点名的部分，禁顺手统一；跨关只有**当次请求**写明才可；改完必须报「改了哪些关/字段 + 旧值→新值 + 其余未动」的证据。
- ★★★**同一串数值需求连续下发，「替换 vs 叠加」每轮都要重新确认**（2026-11-01 踩坑）：上一轮确认过的口径不延续；脚本要参数化、基线固定为「改动前原值」（`.bak_*`），避免越跑越高。
- ★★★**跨关数值同步要按波次逐条映射，照抄≠等强度**（2026-11-03 L03←L02）：按 `(wave,name,isFlying)` 取源关 hp、独有怪留原值、构成等比取样、奖励取源关；SceneInfo/levelId/击杀奖励/speed/armor/waveType 不动。L03 曾掉到 0.68×，补缩放后 1.08×。
- ★★**以 L01 为模板重建 L02 全 25 波**（2026-11-04）：W1-W4 保留 20/30/36/42 只 + 130/135/140/145 金；W5-W25 按「出怪×144/91、地面 HP×71/42、空中 HP×15/12」，enemyInterval/waveType 照取 L01；全关 16,069 只 / 2,386 金。已知缺陷：L02 敌人行 `levelId` 仍为 1、SceneInfo 名称仍「关卡 1」。
- ★★**证据入库体量口径**（2026-10-30）：结论级文本入库；生成图/运行帧/时序板/集中 GIF/`scope_*.json`/资源副本不入库。**例外**：`Artifacts/` 下零漏怪实战证据全量入库（1352 文件 /130MB），不外推到 `Docs/`。
- ★★**清理磁盘/删大目录**：safe-delete 钩子把删除移入回收站，必须 `Clear-RecycleBin -DriveLetter <X> -Force` 才真正释放；`Remove-Item` 完全无效且不抛异常 → **单文件用 `robocopy <dir> <tmp> <file> /MOV`，清目录用 `robocopy <空目录> <目标> /MIR`**。
- ★★**删 Library 的代价**：3 个 git 包（hybridclr 8.14.1 / unity-mcp 10.3.0 / yooasset 3.0.6）要重新 clone；删剩一半会弹 "Corrupted Library Detected" 并静默退出；从工具启动的 Unity 会被会话清理杀掉 → 最后让用户从 Hub 开。
- ★★**震屏白名单**（2026-10-30）：关卡内只有「漏怪」允许抖，开火/爆炸/命中/结算一律不震；唯一入口 `CameraController.ShakeOnEnemyLeak`，加抖动必须改 API 且先问。
- ★★**局内进度落盘 = 续玩快照**（2026-10-31，推翻 10-30「局内不落盘」）：每过一波存塔阵(row/col/type/level/investedGold)+金币+生命+波次游标+整份 `LevelRunMetrics` 到 kv `layout/campaign`，重进接着打；通关写「重玩起点」；`RefundOf=min(配置售价,累计投入)×返还比例` 唯一口径；卖塔立刻落盘。详见 `VOL_05`。
- ★★**真实子弹系统已删除**（2026-10-31）：塔即时命中；`tbbulletdata` 与 `TowerInfo.bulletId` 保留（AOE 半径/效果仍从这里取）；`BoardSorting.Bullet=400` 留给枪口焰。
- ★★**UI 品牌文案/字号 = 四层同步**（2026-11-02）：`Localization.xlsx` 源表 → `BootLocalization` 常量（AOT 启动层不能依赖热更 `TextLocalizer`）→ 实际 prefab → 生成器（`TacticalForgePrefabBuilder`/`UIPrefabBuilder`/`TacticalForgeLayout`）。品牌：`BrandTitleKey="FREEDOM TOWER"`、`BrandSloganKey` 见 `VOL_03` 第 385 行。
- 日档 `YYYY-MM-DD.md` 追加写，读最近的在最前。
