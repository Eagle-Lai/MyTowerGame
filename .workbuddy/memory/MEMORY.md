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
- dll=独立HTTP(HotUpdateDllDownloader)；AB=YooAsset HostPlayMode（宏 FT_HOTUPDATE，FTYooAssetDefine 菜单3/4）。地址唯一源 Core/Res/ResServerConfig.cs；AOT 侧 BootLoader.ServerUrlForAOT 刻意复制，两处同步。
- 首启释放 PrefetchStreamingAssetsToPersistent：存在即跳过（保热更成果）。dll md5 清单 `{平台}/HybridCLR/md5.txt`（菜单 HybridCLR/4）须与 dll 同传；GetPlatformFolder 与 ForProbe 同步改。
- YooAsset 3.0.x 默认值全关 → BuildSandboxParameters 已显式开 High/1MB/30s/并发8；事件 API=DownloadProgressChanged。本地测试 Python http.server 指 Bundles/<平台>/。

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

## MuMu 真机调试 [公司E 2026-10-13]
- adb=`C:\Program Files\Netease\MuMu\nx_main\adb.exe`；有效设备 `emulator-5554`（127.0.0.1:16384 connect 上但空响应，勿用）。游戏包 `com.lzyfreedomtower.freedomtower`。adb 常闪断 offline，重试即可；模拟器可由 `MuMuManager.exe control -v 0 launch` 拉起。
- 实测：无资源服务器时探测 2 次超时→跳过热更、本地 StreamingAssets dll 12/12 加载、入口执行正常；但 main 场景报大量 referenced script missing + serialization layout mismatch → APK 内置 AB 与 StreamingAssets dll 版本不一致，待查。
- ★ 2026-10-14 已根治（架构级，铁律级结论）：**HybridCLR 真机上挂热更脚本的资源（场景/预制体/SO）必须 AB 打包，Resources/BuildSettings 场景必 missing**。三件套：①main 场景进 AB（收集器 Scene 组），BootLoader 改调 IHotUpdateEntry.EnterMainScene（热更侧 ResLoader.Init→SceneHandle 加载，接口在 AOT 侧定义）；②BootUI 三件套（Splash/Loading/HotUpdateView）进 AB（收集器 BootUI 组+ResTable 登记，ResBundle.BootUi 常驻）；③LocalizationSettings+Language 枚举移入 FTProject.AOT（asmdef 加 Unity.TextMeshPro）。工具：收集器维护菜单 `Tools/塔防/YooAsset 接入/5`（幂等）。★ 坑：Generate/All 的 dll 产物可能落后编辑器编译一拍，重跑菜单 7 即同步；改 dll 后模拟器须 `pm clear` 或卸载重装（persistent 旧 dll 会被"存在即跳过"保住）。

## 工具/其他
- 地图链路：棋盘→levelmap_export.json→LevelMap.xlsx→tblevelmap.json→SceneInfo.xlsx。静态校验9个（.workbuddy/tools）改完全跑。
- TowerType=Normal1/Aoe2/Slow3/Pierce4/Laser5；目录 Power=Aoe、Retard=Slow；云端资料库镜像 Docs/（md 用 space.importer、svg 用 drive/upload）。
- 热更服务器（公司E）：HotUpdateServer/ 目录（junction 到 StreamingAssets+AB），python http.server 8000 后台常驻，防火墙规则 FT HotUpdate 8000；模拟器 ServerUrl=10.0.2.2:8000（TUN 劫持详见 2026-10-14 日志）；真机=局域网 IP 且须与 BootLoader.ServerUrlForAOT 同步改。
