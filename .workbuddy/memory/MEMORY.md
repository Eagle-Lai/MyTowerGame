# FreedomTower 长期记忆（只留不变量；细节见 Docs/ 与 memory/ 日志）

## 双版本制度（开工先读）
- 家用D=`D:\FreedomTower_1`；公司E=`E:\MyTowerGame`。按工作区路径定版本，记录标 [家用D]/[公司E]，环境严禁跨版套用；两版经 Eagle-Lai/MyTowerGame 同步。
- ★`HotUpdateServer/`、`Bundles/`、`Builds/`(.apk) 被 git 忽略→各机拉完必须重打 AB+重部署，否则"新 dll+旧 AB"混搭。

## 铁律
- 名写法：自由人塔防=文档｜FREEDOM TOWER=副标题｜freedomtower=包名｜FreeTower=YooAsset包裹名(改了热更失效)｜FTProject=命名空间；菜单勿改"塔防"；文档不写盘符。
- 跑生成/挂载菜单前 `isCompiling==false && !isPlaying`；改 `Assets/Editor/*.cs` 后必须等编译完成再跑（否则静默旧程序集，最坑）；先核 MCP 连的是本工程(Application.dataPath)。
- 编辑器脚本不弹 DisplayDialog（走 Debug.Log；危险操作拆两档菜单；DOTweenPro 2 处弹窗不动）。
- ★提交约定（2026-10-16；当晚修订）：**一律全部一起提交**——每次一笔、含全部改动（未跟踪/缓存/产物），不拆不挑。**且必须"先写完记录再提交"**：当天工作日志（memory/YYYY-MM-DD.md）与长期记忆（MEMORY.md）的更新先行完成、与代码同笔落盘；提交后不再写盘（不得不写则并入下一笔；提交 sha 以 git log 为准、不追写）。细则见 Docs/提交与工作记录规范.md。
- git：①push 弹 credential helper→用户级 `~/.gitconfig` `[credential]` 插空 `helper =`，失败重试一次、ls-remote 核 sha；②GitHub 只有 env 代理稳定 `http_proxy=127.0.0.1:7897`；③家用新提交=`git log` 见 Eagle-Lai+清晨日期（可能已 merge）。
- Unity 2022.3.62f3c1 + Built-in RP；screenshot 偶发丢 Overlay 层。

## 程序集/HybridCLR（细节 Docs/HybridCLR_Integration.md）
- 12 程序集；热更6=Assembly-CSharp/LubanLib/Gen/SuperScrollView/Reporter/Runtime。★Assets/Scripts 全归 FTProject.Runtime（验证新代码搜 HotUpdateDlls/Android/FTProject.Runtime.dll）；Assembly-CSharp.dll 恒 5KB 空壳（增删 Assets/ 根脚本须重跑 Generate▸All+拷贝）。
- ★AOT 不得引用热更类型；Boot.unity 先 Assembly.Load 再进 main（Boot0/main1）；入口 IHotUpdateEntry←HotUpdateEntry。dll 名单两处同步 HotUpdateAssembler↔HybridCLRSettings.asset；AOTMetaAssemblies 6 项三处同步；包版本=libil2cpp-version.txt(8.14.1)。
- ★★热更代码新增 Unity/UGUI API 调用，必须**在 AOT 侧真实引用一遍**（防 IL2CPP 裁剪 → 真机 `MissingMethodException: MethodNotFind`，异常会杀死启动协程、黑屏）：字体=`BootUiFontProvider`、UGUI 组件=`BootUiSymbolKeeper`（BootLoader 早期调用；⚠️一 GameObject 只能挂一个 Graphic、探针必须分对象；两函数全 try-catch）。新增热更 UI 时同步扩充该清单。
- ★YooAsset 初始化三步 Initialize→RequestPackageVersion→LoadPackageManifest 才 SetActiveManifest；EnableAddressable=false；同版本二次构建 ErrorCode115。

## 热更/资源
- dll=独立HTTP(HotUpdateDllDownloader)（{ServerUrl}/Android/HybridCLR/）；AB=YooAsset HostPlayMode。
- ★地址=UDP 自动发现，唯一源 `Assets/AOTAssembly/BootServerSelection.cs`：每秒广播 `FTHOTUPD1|port=8000`(UDP 28000)，真机监听 1.5s、HTTP 探测 1s，取来源 IP→md5.txt 确认；常量候选只剩模拟器 10.0.2.2；server.txt 最优先。GetServerUrl：server.txt>SelectedUrl>常量。全在 AOT 侧→改动必须出 APK。
- ★★可达性闸门：Boot 探测完无条件 MarkReachabilityChecked()；RemoteHotUpdateAllowed（未探测=true｜探测过无胜出=false）经 ResServerConfig.IsRemoteHotUpdateAllowed() 成 dll/AB 共用闸门。不可达时 AB 必走 OfflinePlayMode（HostPlayMode 会 60s 版本请求硬失败无回退="一直等待进不去游戏"根因）+CheckUpdateCo 开头短路 onDone(false)。EnableHotUpdate 是 const（CS0162）须落局部变量。
- ★★AB 三铁律：①FT_HOTUPDATE 宏三平台组必开（不开=静默离线）；②HostPlayMode 请求全平铺 ServerUrl 根：/FreeTower.version(内容=版本号)/FreeTower_{ver}.hash/.bytes/{哈希}.bundle（★无后缀特殊包 unitymonos/unityshaders 文件名=裸 hash 无 .bundle，曾漏致 404，deploy 脚本已修）；部署跑 .workbuddy/tools/deploy_free_tower_cdn.py；③CheckUpdateCo 同版本也校验缺失并下载。★首启竞态已根治（2026-10-16 起，见下条闸门）。
- ★★改热更代码后真机同步三件套：①重编 dll=菜单 9/9a→StreamingAssets/HybridCLR+md5（状态 Library/FTReporterBuildStatus.txt）；②AB 变化才重打=菜单 9 完整流水线（或 YooAsset 向导窗口；旧"菜单 5"是 StreamingAssets/AssetBundles 遗留链路勿用）+deploy_free_tower_cdn.py+HTTP 自检；③测试前先跑启动热更服务器.bat（部署≠在跑；不在=闸门关=完全不热更，形似"功能没做"最易误判）。
- ★热更"中间态"（2026-10-16 模拟器实例）：CheckUpdate **先激活新清单（版本即提交）→再下 bundle**；下载被打断会留下"清单新+bundle 缺"，下次启动界面 sync 撞未缓存失败一次（转后台补下）后自愈=首启竞态变体。**已根治**（见下条闸门）。诊断常识：①"Attempting to load bundle from remote"=sync 撞未缓存（非网络故障）②启动静默=MainMenu 正常（成功不打日志）③UDP 广播是发送型 socket，netstat 无 28000 监听属正常。
- ★★热更完整性闸门（2026-10-16 已实施）：`BootHotUpdateGate`——Boot 场景内跑完"检查更新+全量差异下载"才加载 main；失败/超时留"零 AB 依赖"内置 UI 自动重试（3s、含安全重建）；Init 失败同 UI 重试（`YooAssetResLoader.LastInitError`；重建=DestroyPackageAsync 等完→RemovePackage，⚠️3.x 先 Destroy 再 Remove，2.x DestroyPackage 已移除）。`Launcher.BeginHotUpdate` 靠 `BootHotUpdateGate.Completed` 跳过重复检查。编辑器跳过闸门（编辑链路零变化）。
- 首启释放 PrefetchStreamingAssetsToPersistent，存在跳过。md5 清单 {平台}/HybridCLR/md5.txt（菜单 HybridCLR/4）与 dll 同传。BuildSandboxParameters=High/1MB/30s/并发8；事件 DownloadProgressChanged。
- 热更服务器 .workbuddy/tools/hotupdate_server.py（HTTP 8000+UDP 28000；--self-test）；根=平铺 AB 部署区，Android/{HybridCLR,FreeTower} junction；git 忽略、两版各自建；防火墙规则 FT HotUpdate 8000 已建。★FlyingBird TUN 劫持 curl(502)→自检必须 `curl --noproxy "*"`；bind 10013 重试即好；★派生进程无法常驻→用户终端跑 .bat(CRLF)；停服前先叫停并行会话。

## 配置/多语言/UI
- Luban：改 xlsx 必重导（菜单3，DOTNET_ROLL_FORWARD=LatestMajor）；新表登记 __tables__.xlsx；字段从 B 列起；ResTable.cs=唯一寻址源。★直接跑 gen_code_json.bat 会删 FTProject.Gen.asmdef→级联 CS0246。
- 多语言：主键=英文原文；权威源 gen_localization_table.py ROWS→xlsx；追加用 append_localization_rows_*.py（跑完走菜单3）；TextLocalizer key 留空自动取；回退 当前→英文→原文；菜单308挂/309清理。
- ★设置界面语言下拉框：SettingView/Panel/LanguageDropdown（CreateDropdown=官方模板；选项=supportedLanguages+DisplayName）；实时刷新=TextLocalizer 静态自动+各 View 订阅语言事件（HUD=文本配方重放）。改 SettingView→重建设置界面→308→菜单4。
- ★内容名本地化三链路：①塔名=TowerConfig.DisplayName（勿直用 .Name）；②关卡名=Localization.LevelName(id)（界面用 "Level {0}" 词条）；③怪物名=123 条词条（Get(name)??name；脚本 add_monster_names_20261016.py）。审计法=Get 字面量↔tblocalization.json 差集/prefab↔TextLocalizer 对比/中文硬编码扫描/View 刷新时机（Awake 一次性=坑）。
- UI 生成器 UIPrefabBuilder（改文案/布局=改它+重编译+重生成）；TMP；SiYuanSongTi SDF 动态+多图集（★动态字体资产随运行增长，font bundle +15~20KB/版正常；unitymonos 联动更新正常）。
- ★塔图标 UI_TowerIcon_{Normal,Power,Retard}=正式美术 96×96 透明底，属 ui_hud；UISkinArtGenerator 按 ManualArtIconNames 名单跳过（勿按尺寸判）；改图跑 tower_icon_bg_remove.py；换图后真机重建 AB。
- ★品牌 logo=Assets/Art/Logo/app_icon_512x512.png（唯一源：生成器 LogoSpritePath/LoadLogoSprite 供 Splash/Loading/MainMenu 三处 Logo 节点；ResTable 登记 UI_AppLogo→ui_hud）；Android 图标 Legacy 6 槽已填（256/128/128/64/48/32）；Round/Adaptive 留空（无分层素材）。
- ★★MCP 验证 UI 严禁 instantiate 预制体子物体：TMP 编辑模式 OnEnable 会把 m_TextStyleHashCode 等写回资产（曾波及 5 个 prefab）。正确=new GameObject 自搭 Canvas+Image，只 LoadAssetAtPath<Sprite>。
- ★refresh/编译触发 AB 打标工具加载全部 ResTable 预制体→改写 UI 预制体与 .meta 的 assetBundleName（曾写坏 SelectLevelItem）。提交前 diff_ui_prefabs.py --base 核对并 checkout 非本意改动。反向同步=prefab 手改回写生成器（Docs/UIPrefab_Sync_ChangeList.md）。
- ★★全量重建三副作用：①重排 fileID ②清空 .meta assetBundleName ③抹掉 TextLocalizer。顺序必须：重建→308 挂 TextLocalizer→菜单4 打标。
- UI 细节（已固化生成器）：塔按钮 96×96；TipsView/TipBar/TipText；TowerCodexItem/SelectLevelItem 根 active=false；TMP 8 处自动字号+4 处居中；VolumeSlider 480×65。
- ResTable（Assets/Scripts/Core/Res/ResTable.cs）=寻址唯一源，界面登记 ResBundle.UiHud；漏登记=真机打不开。残留：MonsterCodexView 登记了但 prefab 不存在→菜单4 恒报缺资源。

## 多分辨率/适配（2026-10-16 审计+实施完毕）
- Canvas=Overlay 1920×1080 Match0.5；★根画布不可做安全区（实测写入被 Canvas 复位）→ SafeAreaFitter 已改挂 Bg/Normal/Tips 三 Panel（UIManager.EnsureSafeArea）【已修】。
- ★边缘锚改造已实施（UIPrefabBuilder）：Hud 塔按钮底锚 49px、Speed/Start (64,77)、Select 箭头 60 / Codex 34、Close 68、Quit 74（16:9 零位移）；新增单步重建菜单 310/311/312——重建会丢 TextLocalizer，必须 重建→308→菜单4。
- ★棋盘取景已重写（CameraController）：底 2 格/顶 1 格/侧 1 格 + 屏安全区内缩、相机下移 0.5 格、分辨率变化自动重算；残：20:9+ 底行残叠 ≤16px、21:9 超约 2.3× 缩档露底色。
- ★背景：BackgroundScale 2.2（总 3.08×）+ 场景实例已改 3.08；BackgroundParallax.Init 改绝对幂等 + Awake 自举（修复运行时视差从未生效——_ready 不序列化）。
- 流程备忘：9a 的 AOT 剥离要跑 BuildPlayer，冷缓存 **~10 分钟**属正常（状态文件+CPU/日志增长判断）、**热缓存仅 ~1 分钟**（同日二跑 56 秒实测）；AB 1.0.23 变化 3 包（boot_ui/ui_hud/font）；deploy 后必须自检（含无后缀特殊包），自检脚本 .workbuddy/tmp/http_selftest_1xxx.py（自带临时 HTTP 服务、测完即关）。
- 审计快照：Library/UIAdaptDump.txt（改前）/UIAdaptDump_after.txt（改后）；细节见 2026-10-16 日志。

## SuperScrollView（★最坑）
- InitListView 一次性快照 viewport→绝不能 OnEnable 初始化；SelectView.Build 挂 _pendingInit、首帧 LateUpdate 再 DoInitListView。
- 吸附硬约束：Viewport 宽=卡片宽 1150×550；pivot.x=0、anchoredPosition.x=-575。三处同步 UIPrefabBuilder SelectItemW↔SelectView ItemWidth(1150/56)↔SelectLevelItem。勿用 mOnSnapItemFinished→轮询中心距 4px。

## 生命周期/存档/音频
- LevelClearView 胜败共用 OnGameOver()（星级先读后写）；唯一拆卸 TeardownLevel()（操作态→战斗实体→场景残留→界面）。
- 存档只走 SaveManager（禁 SQL/PlayerPrefs，例外 KeyProvider）；改表三步 CreateStatements→CurrentVersion+1→RunMigrations。
- 音频=丢文件+gen_audio_catalog.py；BGM 2源+AudioFadeDriver；倍速唯一源 Core/GameClock.cs（timeScale 只 0/1）。

## 玩法/交互（当前形态）
- ★塔型三类：Normal1(飞+走)/Aoe2 火力=仅走/Slow3 光环(飞+走)；Pierce4/Laser5 已删（编号不回收）。对空唯一判定=塔表 canAttackAir。旧档 type=4/5 跳过。目录 Power=Aoe、Retard=Slow。
- ★建造交互 v3：快速点按=放置态（BuildTowerRequestEvent）；长按0.25s/位移30px=拖拽建造（ghost 跟手、松手校验、拖回按钮/棋盘外静默取消），触发后一帧 _suppressTowerClick 吞 onClick。HUD 右上 Btn_Pause/Btn_Intro。拖拽 IsPointerOverUI 触摸感知已做。
- 点塔交互：放置态点已有塔格=退出放置并选中。日志前缀 [Place]/[HUD]/[TowerInfoView]/[Audit]。地图链路：棋盘→levelmap_export.json→LevelMap.xlsx→tblevelmap.json→SceneInfo.xlsx；静态校验9个改完全跑。

## Unity MCP（两版配置不同，严禁混用）
- [公司E] 官方包 com.coplaydev.unity-mcp v10.3.0，HTTP 127.0.0.1:8082/mcp；CatchFish=自研 ws8080 桥勿混。
- [家用D] stdio uvx mcpforunityserver 3.4.8；Unity 未启动时拉起会卡"连接中"→兜底自起 stdio 实例或 mcp_unity.py；桥端口 6401→6400，真相源 ~/.unity-mcp/unity-mcp-status-*.json；execute_code 先 manage_tools activate scripting_ext（每次重激活）。
- ★长调用（GenerateAll/BuildNow）客户端超时但 Unity 继续→靠产物时间戳/状态文件判定，勿重发。
- ★编辑器 Play 直接跑最新编译代码→改完 .cs 编译通过即可 Play 验证；Play 可 instantiate 预制体实例（编辑模式严禁）。
- 无 MCP 时 ReporterHotfixBuild.Start/StartDllOnly（状态 Library/FTReporterBuildStatus.txt）；batchmode 与编辑器互斥；★启动必须用任务机制；GUI 备用 FT_AutoBuildTrigger（Library/FT_AUTOBUILD.trigger，状态 FTFeatureBuildStatus.txt）。

## 真机调试 [公司E]（MuMu）
- adb 优先 SDK 版；每条命令先 connect 127.0.0.1:16384；包 com.lzyfreedomtower.freedomtower；adb root 可用。★input tap=横屏逻辑 1600x900（截图 1080x600 ×1.481/1.5）；pm clear 需引号。
- ★真机挂热更脚本的资源（场景/预制体/SO）必须 AB 打包：main 场景+BootUI 三件套进 AB、LocalizationSettings 移 FTProject.AOT；维护菜单 Tools/塔防/YooAsset 接入/5；Generate/All 的 dll 可能落后一拍重跑菜单 7；改 dll 后须 pm clear。

## APK 构建 [家用D]
- GUI=菜单 6/7；batchmode：`Unity.exe -batchmode -executeMethod FTProject.EditorTools.BuildApk.BuildNow -buildTarget Android -logFile Logs/batch_apk.log`（完建不自动退出须手动杀）。★编辑器真实路径=`C:\Program Files\Unity 2022.3.62f3c1\`（Hub 下是空壳）；状态 Library/FTBuildApkStatus.txt。
- 三铁坑：①GUI Gradle 失败弹模态框卡死主线程；②AndroidTargetSdkVersion:0=自动选最高已装平台，坏包会骗过它（曾选坏 android-37.0，删包回落 34）；③SBP/资产库路径大小写敏感（改名绕临时名两步含 meta）。

## 工具/其他
- ★scan_missing_script_refs.py：须同时收集 Assets+Packages+Library/PackageCache 的 .cs.meta，否则包脚本全误报。29 个怪物 controller 的 2 个 never-existed StateMachineBehaviour 已用 Compat 占位修复（手写 meta 恢复原 GUID）。
- 怪物素材=侧视拆件图集+_Common/Animations/<家族>；朝向靠 BaseEnemy.FaceMoveDirection 翻转 localScale；表情走动画事件 SetHead(int)→MonsterAnimEventReceiver；gen_monster_catalog.py 生成 MonsterCatalog.cs。
- 云端资料库镜像 Docs/（md 用 space.importer、svg 用 drive/upload）。
