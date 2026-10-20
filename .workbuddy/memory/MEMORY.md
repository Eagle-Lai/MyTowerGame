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

## 开工必读铁律
- 双版本：[家用D] `D:\FreedomTower_1`｜[公司E] `E:\MyTowerGame`。记录必须标版本，严禁跨版套结论；同步走 GitHub `Eagle-Lai/MyTowerGame`(main)。
- 命名：`自由人塔防`=文档名｜`FREEDOM TOWER`=副标题｜`freedomtower`=包名｜`FreeTower`=YooAsset 包裹名（★改则热更全失效）｜`FTProject`=命名空间。
- 跑生成/挂载菜单前必须 `isCompiling == false && isPlaying == false`；改过 `Assets/Editor/*.cs` 要等编译完；动手前先确认 MCP 连的是本工程（不是 CatchFish）。
- 编辑器脚本不弹 `DisplayDialog`（走 `Debug.Log`）；危险操作拆成两档菜单。
- ★提交：**全部一起提交**（一笔含未跟踪/缓存/产物，不拆不挑）；**先写完记录再提交**（当天日档 + 本文件 + 相关分册同一笔）；提交后不再写盘。
- ★git 必须显式覆盖代理到 7897（默认注入的 60044 对 github 返回 502）：`http_proxy=http://127.0.0.1:7897 https_proxy=http://127.0.0.1:7897 git -c http.version=HTTP/2`；>10MB 必带 HTTP/2；`cannot lock ref` = 并行竞态，先 `ls-remote` 核对，**不要装 git-lfs**。
- ★★出 APK 前核对 Build Settings：`Boot.unity` 启用 + `Main.unity` 禁用（main 只能从 AB 加载）。
- ★★改热更码真机三件套：重编 dll → AB 有变化才重打（菜单 9 后立刻 deploy）→ 先跑 `启动热更服务器.bat`。
- 日档 `YYYY-MM-DD.md` 追加写，读最近的在最前。
