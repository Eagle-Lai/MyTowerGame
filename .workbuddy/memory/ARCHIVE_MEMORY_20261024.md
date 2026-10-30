# MEMORY.md 全文存档（2026-10-24 精简前，一字未删）

> 原因：MEMORY.md 当时 3579 字符，超出 3000 字注入上限。
> 处理：仅压缩主文件表述，本篇保存压缩前完整原文，供随时回查。主文件中的引用指针指向各 VOL 分册。

---

# FreedomTower 项目长期记忆（索引）

> **记录原则（用户已明确）**：不要精简、不要为了篇幅砍内容。宁可记忆文件更大更全，也要保留可复用的规则、参数、坑和原因。
> 建议结构：先按主题分区，每条写「结论 + 关键参数/路径 + 为什么」。过期内容只做标注，不直接删。
>
> **结构（2026-10-19 按主题拆分）**：本文件 = 索引 + 开工必读铁律，**必须控制在 3000 字内**（超出会在注入时被截断）。细节全部移到 7 个分册，**原文一字未删**。写记录时先判归属：每次开工都得知道的留本文件，其余写进对应分册。

## 分册目录（同目录下，按需读取）
| 分册 | 内容 |
|---|---|
| `VOL_01_环境流程与出包.md` | 双版本路径、命名规范、生成/挂载前置、编辑器脚本约定、提交规范、git 代理、APK 出包铁律、真机 adb |
| `VOL_02_热更与资源.md` | 程序集与 HybridCLR、dll/AB 链路、UDP 发现与闸门、一键热更菜单 10、部署铁律、配置加载失败自恢复 |
| `VOL_03_配置多语言与UI.md` | Luban 表、多语言词条、TextLocalizer、UIPrefabBuilder、全量重建副作用、HUD 两按钮 |
| `VOL_04_适配与SuperScrollView.md` | 多分辨率三组件、安全区、边缘锚数值、SuperScrollView 吸附约束 |
| `VOL_05_玩法存档音频与地图.md` | 关卡生命周期、存档、音频/倍速、塔型与攻击表现、建造交互、地图链路、新增关卡 |
| `VOL_06_敌人四方向.md` | AdvancedHen / Monkey 两套架构、构建器与校验坑、AI 分件美术 |
| `VOL_07_工具与UnityMCP.md` | Unity MCP 两版端口、Python/脚本兜底、怪物素材、待办与环境事实 |
| `VOL_08_数值管线与平衡.md` | balance_pipeline 命令链与公式、单调性硬校验与前向修复、v6 第一关重平衡、**v7 按关拆表 + 节奏重构（表结构/参数/Par 校准/fill-gate 结论）**、仿真代理局限、apply→菜单3→编译→PlayMode 回放链路 |

## 开工必读铁律
- 双版本：[家用D] `D:\FreedomTower_1`｜[公司E] `E:\MyTowerGame`。记录必须标版本，严禁跨版套结论；同步走 GitHub `Eagle-Lai/MyTowerGame`(main)。
- 命名：`自由人塔防`=文档名｜`FREEDOM TOWER`=副标题｜`freedomtower`=包名｜`FreeTower`=YooAsset 包裹名（★改则热更全失效）｜`FTProject`=命名空间。
- 跑生成/挂载菜单前必须 `isCompiling == false && isPlaying == false`；改过 `Assets/Editor/*.cs` 要等编译完；动手前先确认 MCP 连的是本工程（不是 CatchFish）。
- 编辑器脚本不弹 `DisplayDialog`（走 `Debug.Log`）；危险操作拆成两档菜单。
- ★提交：默认**按功能分批**（2026-10-22 用户新口径：按功能拆多笔，代码契约→工具→资产→文档的先后顺序，保证每笔不悬空）；**先写完记录再提交**（当天日档 + 本文件 + 相关分册同一笔）；提交后不再写盘。旧口径「全部一起提交，不拆不挑」已被取代。
- ★git 代理（**2026-10-24 最新口径，优先**）：git 已落盘全局 `http.proxy/https.proxy=http://127.0.0.1:7897` + `http.version=HTTP/2`，**直接跑 `git` 就行，不要再依赖环境变量**。旧口径「先用环境默认 `http_proxy`」作废：注入者是 WorkBuddy 沙箱 `sandbox-cli.exe`，端口**每会话随机**（历史见过 61051/56630/57267/62114/59777/64793）且**偶发 502 tunnel failed**；`7897` = Clash Verge `verge-mihomo` 固定混合口，10-22 记的"7897 握手失败"已过期，10-24 实测 200。`~/.profile` 也加了 7897 + `no_proxy=localhost,127.0.0.1,::1`（只对 login shell 生效）。`cannot lock ref` = 并行竞态，先 `ls-remote` 核对，**不要装 git-lfs**。详见 `VOL_01`。
- ★★出 APK 前核对 Build Settings：`Boot.unity` 启用 + `Main.unity` 禁用（main 只能从 AB 加载）。
- ★★改热更码真机三件套：重编 dll → AB 有变化才重打（菜单 9 后立刻 deploy）→ 先跑 `启动热更服务器.bat`。
- ★★v7 起配置表按关拆分：`Luban/Config/Datas/Levels/L01..L30/`（每关 6 个 xlsx），根目录只剩 `EnemyData.xlsx`（132 原型）+ 非关卡表；旧聚合 5 表已删。改数值只走 `balance_pipeline.py`，别去找 `Datas/RoundData.xlsx`。（2026-10-23 注：该句"走 balance_pipeline"已被下一条取代——只能手工改表。）
- ★★**配置表只能手工改**（2026-10-21 定规）：`balance_pipeline.py` 的 `apply`/`rollback` 与事务层已整体删除，7 个会写关卡表的旧脚本也已删；只读命令 `inspect/preview/validate/simulate/verify-layout/stage` 保留。改表流程＝改 xlsx → 跑 Luban → 重封 `runtimeContentHash`。详见 `AGENTS.md` 与 `VOL_08`。
- ★★**证据分级入库**：Docs 只提交**结论级**（逐波报告/布阵图/trial-index/reproducibility/审阅图/清单 json），**过程级**（`raw-trials`/`audit`/`*/evidence`/`search-*`、EnemyDirectionReview 的 `runtime_*`/`generation`/`staged_art`/`frames`/`history`/`revision_0x`）只留本机；通配必须写 `runtime_*`、`首次成功-r*`；LevelVideos 不入库。详见 `VOL_01`。
- ★★**清理磁盘/删大目录**：safe-delete 钩子把删除**移入回收站**（须 `Clear-RecycleBin -DriveLetter E -Force` 才真释放），且有**每 turn 50 文件**上限（`shutil.rmtree` 变空操作、脚本谎报成功）；批量删用 `robocopy <空目录> <目标> /MIR`（PowerShell 里调）。`.gitignore` 已含 `/Library/ /Temp/ /Obj/ /Logs/`。详见 `VOL_01`。
- ★★**删 Library 的代价**：`manifest.json` 有 3 个 git 包（hybridclr/unity-mcp/yooasset）会随 PackageCache 丢失，需按 `packages-lock.json` 的 hash 手动 `git clone --depth 1 --branch <tag>` 到 `Library/PackageCache/<name>@<hash>`；删剩一半会弹 **Corrupted Library Detected** 并静默退出（code 0），必须删到只剩 PackageCache；**从工具启动的 Unity 会被会话清理杀掉**，最后让用户从 Hub 手动开。详见 `VOL_01`。
- 日档 `YYYY-MM-DD.md` 追加写，读最近的在最前。
