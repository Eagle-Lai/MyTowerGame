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
- 12 程序集；热更6=Assembly-CSharp/LubanLib/Gen/SuperScrollView/Reporter/Runtime。Assembly-CSharp=兜底集（增删 Assets/ 根脚本须重跑 Generate▸All+拷贝）。
- ★ AOT 不得引用热更类型；Boot.unity 先 Assembly.Load 再进 main（BuildSettings Boot0/main1）。入口契约 `IHotUpdateEntry←HotUpdateEntry`。
- dll 名单两处同步：HotUpdateAssembler ↔ HybridCLRSettings.asset（改 YAML）；AOTMetaAssemblies 6 项三处同步（AOTGenericReferences↔HotUpdateAssembler↔HybridCLRDllCopier）；包版本=libil2cpp-version.txt(8.14.1)。
- ★ YooAsset 初始化三步：InitializePackageAsync→RequestPackageVersion→LoadPackageManifestAsync 才 SetActiveManifest；漏步报 manifest not found。EnableAddressable=false；同版本二次构建 ErrorCode115。

## 热更/资源
- dll=独立HTTP(HotUpdateDllDownloader)（路径 {ServerUrl}/Android/HybridCLR/）；AB=YooAsset HostPlayMode。地址唯一源 Core/Res/ResServerConfig.cs；AOT 侧 BootLoader.ServerUrlForAOT 刻意复制，两处同步。
- ★★ AB 热更三铁律 [2026-10-14 源码+实测]：①**FT_HOTUPDATE 宏三平台组必须开**（不开=静默走离线模式，永远读随包版本且不报错——比报错更隐蔽）；②HostPlayMode 请求**全部平铺在 ServerUrl 根**：`/FreeTower.version`(内容=版本号)/`/FreeTower_{ver}.hash`/`/FreeTower_{ver}.bytes`/`/{哈希}.bundle`（HashName 裸名）——**不是目录式**！部署跑 `.workbuddy/tools/deploy_free_tower_cdn.py`；③CheckUpdateCo 版本相同也校验缺失并下载（同步加载遇"未缓存 bundle"首载必败：SFS 无法同步等远端下载、转后台继续；新资源进沙盒靠启动检查兜底）。
- 首启释放 PrefetchStreamingAssetsToPersistent：存在即跳过（保热更成果）。dll md5 清单 `{平台}/HybridCLR/md5.txt`（菜单 HybridCLR/4）须与 dll 同传；GetPlatformFolder 与 ForProbe 同步改。
- YooAsset 3.0.x 默认值全关 → BuildSandboxParameters 已显式开 High/1MB/30s/并发8；事件 API=DownloadProgressChanged。本地测试 http.server 根=HotUpdateServer（平铺 AB 部署区 + Android/ 两 junction）。

## 配置/多语言/UI
- Luban：改 xlsx 必重导（菜单3，DOTNET_ROLL_FORWARD=LatestMajor）；新表登记 __tables__.xlsx；字段从B列起；导出会删 Assets/Gen 陌生文件→KeepFilesInCodeDir 保护。ResTable.cs=唯一寻址源。
- 多语言：代码在 Assets/Scripts/Localization；主键=英文原文；表权威源=`.workbuddy/tools/gen_localization_table.py` ROWS→xlsx；TextLocalizer key 留空自动取（Text 用 _originalText，绝不用 _text.text）；回退 当前→英文→原文；切语言 SetLanguage+LanguageChangedEvent(Action<int>)；菜单308挂/309清理。
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
- 无 MCP / batchmode 替代通道：`ReporterHotfixBuild.Start`（全流水线）/`StartDllOnly`（仅重编 dll+md5）；状态文件 Library/FTReporterBuildStatus.txt 轮询；编辑器开着时用同功能菜单 `Tools/塔防/9 与 9a`。注意 batchmode 与编辑器互斥（工程锁会拒绝启动）；**★启动必须用任务机制（shell `&` 会被会话收割，进程不存活）**；GUI 编辑器场景备用 `FT_AutoBuildTrigger`（写 `Library/FT_AUTOBUILD.trigger`=full/dll → 域重载自动构建）。

## MuMu 真机调试 [公司E 2026-10-13]
- adb：**优先 SDK 版 `C:\Users\Administrator\AppData\Local\Android\Sdk\platform-tools\adb.exe`**（比 MuMu 内置稳定）；其 server 常被重置→**每条命令开头先 `connect 127.0.0.1:16384` 自愈**；设备名在 `emulator-5554`/`127.0.0.1:16384` 间漂移，动态识别。游戏包 `com.lzyfreedomtower.freedomtower`；模拟器可由 `MuMuManager.exe control -v 0 launch` 拉起。触摸注入：`input motionevent` 连发序列能合成画圈手势（已实测调起 Reporter）；双击因命令间隔>0.35s 无法用 adb 模拟（人工双击应正常）。
- ★ 2026-10-14 已根治（架构级，铁律级结论）：**HybridCLR 真机上挂热更脚本的资源（场景/预制体/SO）必须 AB 打包，Resources/BuildSettings 场景必 missing**。三件套：①main 场景进 AB（收集器 Scene 组），BootLoader 改调 IHotUpdateEntry.EnterMainScene（热更侧 ResLoader.Init→SceneHandle 加载，接口在 AOT 侧定义）；②BootUI 三件套（Splash/Loading/HotUpdateView）进 AB（收集器 BootUI 组+ResTable 登记，ResBundle.BootUi 常驻）；③LocalizationSettings+Language 枚举移入 FTProject.AOT（asmdef 加 Unity.TextMeshPro）。工具：收集器维护菜单 `Tools/塔防/YooAsset 接入/5`（幂等）。★ 坑：Generate/All 的 dll 产物可能落后编辑器编译一拍，重跑菜单 7 即同步；改 dll 后模拟器须 `pm clear` 或卸载重装（persistent 旧 dll 会被"存在即跳过"保住）。

## 工具/其他
- ★缺失脚本排查：`scan_missing_script_refs.py`（静态扫 m_Script 失联 GUID）——必须同时收集 Assets+Packages+Library/PackageCache 的 .cs.meta，否则 uGUI/TMP 包脚本全误报。素材包 29 个怪物 controller 的 2 个 never-existed StateMachineBehaviour（特征=m_GameObject:0 → 报 Game Object '<null>'）已用 Compat 占位脚本修复（Assets/Scripts/Compat/，手写 meta 恢复原 GUID，空实现≡原行为）。
- 点塔交互：放置态点"已有塔格子"=退出放置并选中（TowerPlacement）；诊断日志前缀：[Place]/[HUD]/[TowerInfoView]/[Audit]（RuntimeMissingScriptAudit 进关延时 1s 扫场景 missing 汇总一条）。
- 地图链路：棋盘→levelmap_export.json→LevelMap.xlsx→tblevelmap.json→SceneInfo.xlsx。静态校验9个（.workbuddy/tools）改完全跑。
- TowerType=Normal1/Aoe2/Slow3/Pierce4/Laser5；目录 Power=Aoe、Retard=Slow；云端资料库镜像 Docs/（md 用 space.importer、svg 用 drive/upload）。
- 热更服务器（公司E）：python http.server 8000 常驻于 HotUpdateServer/（根=**平铺 AB 部署区**；Android/HybridCLR、Android/FreeTower 两 junction 供 dll 下载与查看）；模拟器 ServerUrl=10.0.2.2:8000（TUN 劫持详见 2026-10-14 日志）；真机=局域网 IP 且须与 BootLoader.ServerUrlForAOT 同步改。发版=构建后跑 deploy_free_tower_cdn.py。
