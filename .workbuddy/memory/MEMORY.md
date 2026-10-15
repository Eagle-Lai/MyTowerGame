# FreedomTower 长期记忆（≤3000字，只留不变量；细节见 Docs/ 与日志）

## 双版本制度（开工先读）
- 家用D=`D:\FreedomTower_1`（Unity 2022.3.62f3c1；Android 工具链 `D:\Android\`；工具在 `C:\Users\78296\`）。
- 公司E=`E:\MyTowerGame`（Unity 已装 Hub；Android 工具链**不完整**：Hub 模块仅 OpenJDK+Tools，SDK/NDK 目录为空；`AppData\Local\Android\Sdk` 残缺无 platforms/NDK；Hub CLI 无 `--headless`（报 bad option），补装模块只能走 Hub GUI；另有 CatchFish `D:\Develop_lzy\CatchFish_Android` Unity2020.3；git 身份=公司电脑）。
- 开工第一步=识别版本（看工作区路径）；记录标 [家用D]/[公司E]；环境严禁跨版套用；2026-09-25~10-11 记录全属家用D。两版经 GitHub `Eagle-Lai/MyTowerGame` 同步（.workbuddy/ 随 git 走）。

## 铁律
- 名写法：自由人塔防=文档｜FREEDOM TOWER=副标题｜freedomtower=包名｜FreeTower=YooAsset包裹名(改了热更失效)｜FTProject=命名空间。菜单 `Tools/塔防` 勿改"塔防"。文档不写盘符。
- 动手前确认 MCP 连的是本工程（查 Application.dataPath）；跑生成/挂载菜单前 `isCompiling==false && !isPlaying`；改 `Assets/Editor/*.cs` 后必须 refresh 编译完再跑（否则静默用旧程序集，最坑）。
- 编辑器脚本不弹 DisplayDialog（走 Debug.Log；危险操作拆两档菜单；DOTweenPro 2 处弹窗不动）。
- git push 弹 credential helper → 用户级 ~/.gitconfig `[credential]` 插空 `helper =`；失败重试一次，`ls-remote` 核 sha。
- Unity 2022.3.62f3c1 + Built-in RP；screenshot 偶发丢 Overlay 层。

## 程序集/HybridCLR（细节 Docs/HybridCLR_Integration.md）
- 12 程序集；热更6=Assembly-CSharp/LubanLib/Gen/SuperScrollView/Reporter/Runtime。Assembly-CSharp=兜底集（增删 Assets/ 根脚本须重跑 Generate▸All+拷贝）。★Assets/Scripts 全部归 **FTProject.Runtime**（asmdef）→ 验证 dll 是否含新代码要字节搜 `HotUpdateDlls/Android/FTProject.Runtime.dll`；Assembly-CSharp.dll 恒 5KB 空壳、mtime 旧属正常，别误判"没编译"（2026-10-14 踩过）。
- ★ AOT 不得引用热更类型；Boot.unity 先 Assembly.Load 再进 main（BuildSettings Boot0/main1）。入口契约 `IHotUpdateEntry←HotUpdateEntry`。
- dll 名单两处同步：HotUpdateAssembler ↔ HybridCLRSettings.asset（改 YAML）；AOTMetaAssemblies 6 项三处同步（AOTGenericReferences↔HotUpdateAssembler↔HybridCLRDllCopier）；包版本=libil2cpp-version.txt(8.14.1)。
- ★ YooAsset 初始化三步：InitializePackageAsync→RequestPackageVersion→LoadPackageManifestAsync 才 SetActiveManifest；漏步报 manifest not found。EnableAddressable=false；同版本二次构建 ErrorCode115。

## 热更/资源
- dll=独立HTTP(HotUpdateDllDownloader)（路径 {ServerUrl}/Android/HybridCLR/）；AB=YooAsset HostPlayMode。★地址=**UDP 自动发现**[2026-10-14 晚]：唯一源 `Assets/AOTAssembly/BootServerSelection.cs`；电脑端 hotupdate_server.py 每秒广播 `FTHOTUPD1|port=8000`(UDP 28000)，真机 Boot 阶段监听 2.5s 取来源 IP 为候选→md5.txt 探测确认防误报；Candidates 常量只剩模拟器 10.0.2.2（NAT 网关永不变，公司场景主路径）；探测与 UDP 监听**并行**（模拟器 ~0.1s 先出即停 UDP；真机 4s 超时后转 UDP 结果二阶段）。server.txt 覆盖仍最高优先（存在则跳过 UDP）。ResServerConfig.GetServerUrl 优先级 server.txt > SelectedUrl > 常量。**选票全 AOT 侧→改这些必须出 APK**。
- ★★ AB 热更三铁律 [2026-10-14 源码+实测]：①**FT_HOTUPDATE 宏三平台组必须开**（不开=静默走离线模式，永远读随包版本且不报错——比报错更隐蔽）；②HostPlayMode 请求**全部平铺在 ServerUrl 根**：`/FreeTower.version`(内容=版本号)/`/FreeTower_{ver}.hash`/`/FreeTower_{ver}.bytes`/`/{哈希}.bundle`（HashName 裸名）——**不是目录式**！部署跑 `.workbuddy/tools/deploy_free_tower_cdn.py`；③CheckUpdateCo 版本相同也校验缺失并下载（同步加载遇"未缓存 bundle"首载必败：SFS 无法同步等远端下载、转后台继续；新资源进沙盒靠启动检查兜底）。
- 首启释放 PrefetchStreamingAssetsToPersistent：存在即跳过（保热更成果）。dll md5 清单 `{平台}/HybridCLR/md5.txt`（菜单 HybridCLR/4）须与 dll 同传；GetPlatformFolder 与 ForProbe 同步改。
- YooAsset 3.0.x 默认值全关 → BuildSandboxParameters 已显式开 High/1MB/30s/并发8；事件 API=DownloadProgressChanged。本地测试 http.server 根=HotUpdateServer（平铺 AB 部署区 + Android/ 两 junction）。

## 配置/多语言/UI
- Luban：改 xlsx 必重导（菜单3，DOTNET_ROLL_FORWARD=LatestMajor）；新表登记 __tables__.xlsx；字段从B列起；导出会删 Assets/Gen 陌生文件→KeepFilesInCodeDir 保护。ResTable.cs=唯一寻址源。★直接跑 gen_code_json.bat 会把 Assets/Gen/FTProject.Gen.asmdef 删掉（保护只在菜单3路径生效）→ 全项目级联 CS0246；编辑器外跑导出后必核对 asmdef（2026-10-14 踩过）。
- 多语言：代码在 Assets/Scripts/Localization；主键=英文原文；表权威源=`.workbuddy/tools/gen_localization_table.py` ROWS→xlsx；向已有 xlsx 幂等追加词条用 `append_localization_rows_20261014.py`（自动备份 .bak；跑完必走菜单3重导）；TextLocalizer key 留空自动取（Text 用 _originalText，绝不用 _text.text）；回退 当前→英文→原文；切语言 SetLanguage+LanguageChangedEvent(Action<int>)；菜单308挂/309清理。
- UI 生成器 UIPrefabBuilder（改文案=改它+重编译+重生成）；TMP；SiYuanSongTi SDF 动态+多图集。

## SuperScrollView（★最坑）
- LoopListView2.InitListView 一次性快照 viewport GetLocalCorners → 绝不能 OnEnable 初始化；SelectView.Build 挂 _pendingInit，首帧 LateUpdate 才 DoInitListView。
- 吸附硬约束：Viewport 宽=卡片宽(1250×550)固定尺寸；pivot.x=0、anchoredPosition.x=-625。清单三处同步：UIPrefabBuilder(SelectItemW/H/Gap)↔SelectView(ItemWidth/ItemGap=1250/56)↔登记名 SelectLevelItem。别用 mOnSnapItemFinished→轮询中心距4px。

## 生命周期/存档/音频/倍速
- LevelClearView 胜败共用，OnGameOver() 打开；星级先读后写。唯一拆卸 TeardownLevel()：操作态→战斗实体→场景残留→界面；HudView 须在其中 Close。
- 存档只走 SaveManager（禁 SQL/PlayerPrefs，例外 KeyProvider）；Android 自带 libsqlite3.so；改表三步 CreateStatements→CurrentVersion+1→RunMigrations。
- 音频：加音频=丢文件+gen_audio_catalog.py；BGM 2源+AudioFadeDriver；倍速唯一源 Core/GameClock.cs（timeScale 只 0/1）。

## Unity MCP [公司E 2026-10-13]
- MyTowerGame=官方包 com.coplaydev.unity-mcp v10.3.0（manifest 钉死）；HTTP 127.0.0.1:8082/mcp；CatchFish=自研 ws8080 桥，严禁混用（曾误加跨工程路由已全撤）。
- mcp.json 条目 UnityMCP-MyTowerGame；服务器随 Unity 开关；换条目后须重启用连接器；调用前核 dataPath。
- 无 MCP / batchmode 替代通道：`ReporterHotfixBuild.Start`（全流水线）/`StartDllOnly`（仅重编 dll+md5）；状态文件 Library/FTReporterBuildStatus.txt 轮询；编辑器开着时用同功能菜单 `Tools/塔防/9 与 9a`。注意 batchmode 与编辑器互斥（工程锁会拒绝启动）；**★启动必须用任务机制（shell `&` 会被会话收割，进程不存活）**；GUI 编辑器场景备用 `FT_AutoBuildTrigger`（写 `Library/FT_AUTOBUILD.trigger`=full/dll/uimainmenu/**feature** → 域重载自动构建；uimainmenu=只重建 MainMenuView.prefab 即 UIPrefabBuilder.RebuildMainMenuOnly，防全量覆盖手工 prefab；**feature=FT_FeatureBuild 一键流水线**：Luban▸GameIntroView.prefab▸HudView 幂等补挂 Btn_Pause/Btn_Intro▸TextLocalizer▸交接 ReporterHotfixBuild，状态文件 Library/FTFeatureBuildStatus.txt）。MCP 直连兜底：WorkBuddy 会话 ToolSearch 搜不到 unity 工具时，用 `.workbuddy/tools/mcp_unity.py`（MCP streamable HTTP 客户端，server=**mcp-for-unity-server 3.4.8**，`call execute_code '{"action":"execute","code":"...return ..."}'` 可跑 C#、read_console 查错误）。

## MuMu 真机调试 [公司E 2026-10-13]
- adb：**优先 SDK 版 `C:\Users\Administrator\AppData\Local\Android\Sdk\platform-tools\adb.exe`**（比 MuMu 内置稳定）；其 server 常被重置→**每条命令开头先 `connect 127.0.0.1:16384` 自愈**；设备名在 `emulator-5554`/`127.0.0.1:16384` 间漂移，动态识别。游戏包 `com.lzyfreedomtower.freedomtower`；模拟器可由 `MuMuManager.exe control -v 0 launch` 拉起。触摸注入：`input motionevent` 连发序列能合成画圈手势（已实测调起 Reporter）；双击因命令间隔>0.35s 无法用 adb 模拟（人工双击应正常）。
- ★ 2026-10-14 已根治（架构级，铁律级结论）：**HybridCLR 真机上挂热更脚本的资源（场景/预制体/SO）必须 AB 打包，Resources/BuildSettings 场景必 missing**。三件套：①main 场景进 AB（收集器 Scene 组），BootLoader 改调 IHotUpdateEntry.EnterMainScene（热更侧 ResLoader.Init→SceneHandle 加载，接口在 AOT 侧定义）；②BootUI 三件套（Splash/Loading/HotUpdateView）进 AB（收集器 BootUI 组+ResTable 登记，ResBundle.BootUi 常驻）；③LocalizationSettings+Language 枚举移入 FTProject.AOT（asmdef 加 Unity.TextMeshPro）。工具：收集器维护菜单 `Tools/塔防/YooAsset 接入/5`（幂等）。★ 坑：Generate/All 的 dll 产物可能落后编辑器编译一拍，重跑菜单 7 即同步；改 dll 后模拟器须 `pm clear` 或卸载重装（persistent 旧 dll 会被"存在即跳过"保住）。

## 工具/其他
- ★缺失脚本排查：`scan_missing_script_refs.py`（静态扫 m_Script 失联 GUID）——必须同时收集 Assets+Packages+Library/PackageCache 的 .cs.meta，否则 uGUI/TMP 包脚本全误报。素材包 29 个怪物 controller 的 2 个 never-existed StateMachineBehaviour（特征=m_GameObject:0 → 报 Game Object '<null>'）已用 Compat 占位脚本修复（Assets/Scripts/Compat/，手写 meta 恢复原 GUID，空实现≡原行为）。
- 点塔交互：放置态点"已有塔格子"=退出放置并选中（TowerPlacement）；诊断日志前缀：[Place]/[HUD]/[TowerInfoView]/[Audit]（RuntimeMissingScriptAudit 进关延时 1s 扫场景 missing 汇总一条）。
- ★建造交互 v3 [2026-10-14]：塔按钮手势两分（HudView 判定，TowerDragButton 中继组件运行时 AddComponent 不进 prefab）——快速点按=经典放置态（BuildTowerRequestEvent，点击落子）；长按0.25s/位移30px=**拖拽建造**（TowerDragBeginEvent→TowerPlacement._dragMode，ghost 跟手+悬停高亮，**松手**校验：可建→TryPlace；不可建→Tips 原因+取消；拖回按钮/棋盘外=静默取消）。拖拽触发后一帧窗口 `_suppressTowerClick` 吞 Button.onClick 防误切放置态。HUD 右上角 Btn_Pause（→PauseRequestEvent→PauseView timeScale=0 可恢复）/Btn_Intro（→OpenGameIntroRequestEvent→GameIntroView，弹窗含「回到选关」BackBtn→QuitToSelectRequestEvent + CloseBtn 自关，Info1..4 动态文本 Awake 查表）。拖拽模式 IsPointerOverUI 已升级触摸感知（fingerId 逐一查，真机修复）。
- 地图链路：棋盘→levelmap_export.json→LevelMap.xlsx→tblevelmap.json→SceneInfo.xlsx。静态校验9个（.workbuddy/tools）改完全跑。
- ★塔型三类定案 [2026-10-14 收敛]：Normal1(飞行+行走)/Aoe2火力=仅行走/Slow3光环(飞行+行走)；Pierce4/Laser5 已整体删除（枚举编号不回收；穿透弹+bullet表pierce列+pierce/laser音效图标全清）。"能否对空"唯一判定=塔表 canAttackAir（FindTarget 与 TickSlowAura 同一条过滤）。旧存档 type=4/5 塔恢复时被跳过（RestoreTower 返回 null），无需迁移。目录 Power=Aoe、Retard=Slow；云端资料库镜像 Docs/（md 用 space.importer、svg 用 drive/upload）。
- 热更服务器：**`.workbuddy/tools/hotupdate_server.py` 一键常驻**[2026-10-14 晚]（HTTP 8000 静态服务 + UDP 28000 广播线程，多网卡定向广播，--self-test 自收验证；替代裸 http.server）。根=**平铺 AB 部署区**；Android/HybridCLR、Android/FreeTower 两 junction 供 dll 下载与查看；git 忽略，两版各自建。家用D：junction→StreamingAssets/HybridCLR 与 Bundles/.../1.0.2，**AB 1.0.2 已部署**；防火墙入站规则 **FT HotUpdate 8000** 已建（真机 HTTP 必需）。发版=构建后跑 deploy_free_tower_cdn.py。★环境坑：FlyingBird TUN 代理会劫持 curl（回 502）→ 自检必须 `curl --noproxy "*"`；起服务器偶发 bind 10013（TUN 抽风）→ 重试即好。
- ★APK 构建 [2026-10-14 家用D 实录]：GUI=菜单 6（纯 APK）/菜单 7（DLL▸AB▸APK 完整）；无编辑器时 **batchmode 通道**：`Unity.exe -batchmode -executeMethod FTProject.EditorTools.BuildApk.BuildNow -buildTarget Android -logFile Logs/batch_apk.log`（任务机制后台起，无弹窗无人值守；完建后 executeMethod 不自动退出须手动杀 Unity）。**★家用D 编辑器真实路径=`C:\Program Files\Unity 2022.3.62f3c1\`（Hub 目录下是空壳）**；状态文件 Library/FTBuildApkStatus.txt。**三铁坑**：①GUI Gradle 失败必弹 ParseAndShowException 模态框卡死主线程（MCP 全堵，须人工关）；②`AndroidTargetSdkVersion:0`=自动选最高已装平台——**坏平台包会骗过它**（家用 D 曾被 `android-37.0` 坏拷贝拖去选 37，Gradle "Failed to find Platform SDK"，包内 `.0` 污染三处不可救→删包回落 android-34；sdkmanager 远程无 37 包）；③SBP/Unity 资产库对路径**大小写敏感**（磁盘 main.unity≠收集器 Main.unity 即炸 cache info，改名须绕临时名两步且含 meta）。
- ★ Unity MCP [家用D 2026-10-14]：stdio uvx mcpforunityserver 3.4.8；**WorkBuddy 连接器在 Unity 未启动时拉起会卡死"连接中"、会话内不恢复**→兜底=自起一次性 stdio 实例（spawn uvx→init→activate scripting_ext→execute_code，全程一个进程）或 http 模式+mcp_unity.py（URL 已支持 UNITY_MCP_URL 环境变量，家用D 默认 8082 是公司E 专用）；Unity 桥端口 6401 被占自动回退 6400，**真相源=`~/.unity-mcp/unity-mcp-status-*.json`（含 unity_port/心跳/project_path）**；execute_code 须先 `manage_tools activate scripting_ext`（会话级，每次新连接都要重新激活）。
