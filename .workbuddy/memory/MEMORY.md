# FreedomTower 长期记忆（只留不变量；细节见 Docs/ 与 memory/ 日志）

## 双版本（开工先读）
- 家用D=`D:\FreedomTower_1`；公司E=`E:\MyTowerGame`。按路径定版本、记录标 [家用D]/[公司E]，严禁跨版；经 Eagle-Lai/MyTowerGame(main) 同步。
- ★`HotUpdateServer/`、`Bundles/` 被 git 忽略→AB 各机拉完必须重打+重部署（否则"新 dll+旧 AB"混搭）；★`Builds/` 为 APK 反忽略例外：唯一放行 `Builds/Android/freedomtower.apk`，**家用D 出包后提交、公司E 直接 pull，各机不再各自出包**（旧包 123freedomtower.apk、Burst 调试目录与 Builds 下其余内容仍忽略）。规则见 Docs/提交与工作记录规范.md §3。
- Unity 2022.3.62f3c1 + Built-in RP。

## 铁律
- 命名：自由人塔防=文档｜FREEDOM TOWER=副标题｜freedomtower=包名｜FreeTower=YooAsset包裹名(改了热更失效)｜FTProject=命名空间；菜单勿改"塔防"；文档不写盘符。
- 跑生成/挂载菜单前 `isCompiling==false && !isPlaying`；改 `Assets/Editor/*.cs` 必须等编译完成再跑；先核 MCP 连的是本工程。
- 编辑器脚本不弹 DisplayDialog（走 Debug.Log，危险操作拆两档菜单；DOTweenPro 2 处弹窗不动）。
- ★提交：一律全部一起提交（一笔含未跟踪/缓存/产物，不拆不挑）；必须先写完记录再提交（当天日志+MEMORY.md 与代码同笔），提交后不再写盘。细则 Docs/提交与工作记录规范.md。
- git：push 弹 credential helper→`~/.gitconfig` `[credential]` 插空 `helper =`，重试一次并 `ls-remote` 核 sha；GitHub 只能走 env 代理（端口随 Clash 变，7897/7892 均通）。

## 程序集/HybridCLR（Docs/HybridCLR_Integration.md）
- 12 程序集，热更6=Assembly-CSharp/LubanLib/Gen/SuperScrollView/Reporter/Runtime；★Assets/Scripts 全归 FTProject.Runtime；Assembly-CSharp.dll 恒 5KB 空壳（增删 Assets/ 根脚本须重跑 Generate▸All+拷贝）。
- ★AOT 不得引用热更类型；Boot.unity 先 Assembly.Load 再进 main；入口 IHotUpdateEntry←HotUpdateEntry；dll 名单/AOTMetaAssemblies 多处同步；包版本=libil2cpp-version.txt(8.14.1)。
- ★★热更码新增 Unity/UGUI API 必须在 AOT 侧真实引用一遍（防 IL2CPP 裁剪→真机 `MissingMethodException`，异常杀死启动协程=黑屏）：字体 `BootUiFontProvider`、UGUI `BootUiSymbolKeeper`（一 GameObject 只能挂一个 Graphic、探针分对象；全 try-catch）。
- ★YooAsset 三步 Initialize→RequestPackageVersion→LoadPackageManifest 才 SetActiveManifest；EnableAddressable=false；同版本二次构建 ErrorCode115。

## 热更/资源
- dll=独立 HTTP(HotUpdateDllDownloader) `{ServerUrl}/Android/HybridCLR/`；AB=YooAsset HostPlayMode。
- ★地址=UDP 自动发现，唯一源 `Assets/AOTAssembly/BootServerSelection.cs`（广播 `FTHOTUPD1|port=8000`/UDP 28000；真机监听1.5s+HTTP探测1s；GetServerUrl：server.txt>SelectedUrl>常量；常量只剩 10.0.2.2）。全在 AOT 侧→改动必须出 APK。
- ★★可达性闸门：`ResServerConfig.IsRemoteHotUpdateAllowed()`（未探测=true｜探测过无胜出=false）作 dll/AB 共用闸门；不可达时 AB 必走 OfflinePlayMode（HostPlayMode 会 60s 硬失败无回退="一直等待进不去"根因）+CheckUpdateCo 短路。
- ★★AB 三铁律：①FT_HOTUPDATE 宏三平台组必开；②请求全平铺 ServerUrl 根（FreeTower.version/{ver}.hash/.bytes/{哈希}.bundle；★unitymonos/unityshaders=裸 hash 无 .bundle，曾漏致 404）；部署跑 `.workbuddy/tools/deploy_free_tower_cdn.py`；③CheckUpdateCo 同版本也校验缺失并下载。
- ★★完整性闸门 `BootHotUpdateGate`（2026-10-16 根治"更新中断→残缺运行"）：Boot 内跑完检查+全量差异下载才加载 main；失败/超时留零 AB 依赖内置 UI 3s 自动重试（含安全重建）；Init 失败同 UI 重试（`YooAssetResLoader.LastInitError`；3.x 先 Destroy 再 Remove）。Launcher 靠 Gate.Completed 跳过重复检查；编辑器跳过。
- ★★改热更码后真机三件套：①重编 dll=菜单 9/9a（Library/FTReporterBuildStatus.txt）；②AB 变化才重打=菜单 9（旧"菜单 5"勿用）+deploy+HTTP 自检；③先跑启动热更服务器.bat（不在=闸门关=完全不热更，形似"功能没做"）。
- 服务器 `.workbuddy/tools/hotupdate_server.py`（HTTP 8000+UDP 28000）；根=平铺 AB 部署区，Android/{HybridCLR,FreeTower} junction；git 忽略、两版各自建；防火墙 FT HotUpdate 8000。★自检必须 `curl --noproxy "*"`（TUN 劫持）；派生进程无法常驻→用户终端跑 .bat(CRLF)。

## 配置/多语言/UI
- Luban：改 xlsx 必重导（菜单3）；新表登记 __tables__.xlsx；字段从 B 列起；ResTable.cs=唯一寻址源。★跑 gen_code_json.bat 会删 FTProject.Gen.asmdef→级联 CS0246。
- 多语言：主键=英文原文；权威源 gen_localization_table.py ROWS→xlsx；追加 append_localization_rows_*.py；TextLocalizer key 留空自动取；回退 当前→英文→原文；菜单308挂/309清。
- ★语言下拉：SettingView/Panel/LanguageDropdown（CreateDropdown=官方模板，选项=supportedLanguages）；实时刷新=TextLocalizer 静态自动+各 View 订阅语言事件（HUD=文本配方重放）。改 SettingView→重建→308→菜单4。
- ★名字本地化三链路：塔名=TowerConfig.DisplayName｜关卡名=Localization.LevelName(id)｜怪物名=123 词条（Get(name)??name）；Awake 一次性写文案=坑。
- UI 生成器 UIPrefabBuilder（改文案/布局=改它+重编译+重生成）；SiYuanSongTi SDF 动态+多图集（动态字体资产随运行增长，font bundle +15~20KB/版正常）。
- ★塔图标 UI_TowerIcon_{Normal,Power,Retard}=正式美术 96×96 透明底（ui_hud）；UISkinArtGenerator 按 ManualArtIconNames 跳过；改图跑 tower_icon_bg_remove.py。
- ★品牌 logo=`Assets/Art/Logo/app_icon_512x512.png`（唯一源，供 Splash/Loading/MainMenu；ResTable 登记 UI_AppLogo）；Android Legacy 6 槽已填，Round/Adaptive 留空。
- ★★MCP 验证 UI 严禁 instantiate 预制体子物体（TMP OnEnable 会写回资产）；改为 new GameObject 自搭 Canvas+Image。
- ★refresh/编译触发 AB 打标工具加载全部 ResTable 预制体→改写 UI prefab/.meta 的 assetBundleName。提交前 `diff_ui_prefabs.py --base` 核对；反向同步见 Docs/UIPrefab_Sync_ChangeList.md。
- ★★全量重建三副作用：重排 fileID／清空 .meta assetBundleName／抹掉 TextLocalizer→必须 重建→308→菜单4。UI 关键尺寸：塔按钮 96×96、VolumeSlider 480×65、TowerCodexItem/SelectLevelItem 根 active=false。
- ResTable（Assets/Scripts/Core/Res/ResTable.cs）=唯一寻址源，界面登记 ResBundle.UiHud；漏登记=真机打不开。残留：MonsterCodexView 登记无 prefab→菜单4 恒报缺资源。

## 适配（2026-10-16 实施完，细节见日志）
- Canvas=Overlay 1920×1080 Match0.5；★根画布不可做安全区（写入被 Canvas 复位）→ SafeAreaFitter 挂 Bg/Normal/Tips 三 Panel（UIManager.EnsureSafeArea）。
- ★边缘锚已固化进 UIPrefabBuilder（塔按钮底锚49、Speed/Start(64,77)、箭头60/Codex34、Close68、Quit74；单步重建菜单 310/311/312）；★棋盘取景在 CameraController（底2/顶1/侧1格+安全区内缩+相机下移0.5格）；BackgroundScale 2.2。

## SuperScrollView（★最坑）
- InitListView 一次性快照 viewport→绝不能 OnEnable 初始化；SelectView.Build 挂 _pendingInit、首帧 LateUpdate 再 DoInitListView。
- 吸附硬约束：Viewport 宽=卡片宽 1150×550；pivot.x=0、anchoredPosition.x=-575；三处同步 UIPrefabBuilder SelectItemW↔SelectView ItemWidth(1150/56)↔SelectLevelItem。

## 生命周期/存档/音频/玩法
- LevelClearView 胜败共用 OnGameOver()；唯一拆卸 TeardownLevel()。存档只走 SaveManager（禁 SQL/PlayerPrefs）；改表三步 CreateStatements→CurrentVersion+1→RunMigrations。
- 音频=丢文件+gen_audio_catalog.py；BGM 2源+AudioFadeDriver；倍速唯一源 Core/GameClock.cs（timeScale 只 0/1）。
- ★塔型三类：Normal1(飞+走)/Aoe2 火力=仅走/Slow3 光环(飞+走)；Pierce4/Laser5 已删（编号不回收）；对空判定=塔表 canAttackAir。
- ★建造交互 v3：快速点按=放置态；长按0.25s/位移30px=拖拽建造（ghost 跟手、松手校验、拖回按钮/棋盘外静默取消）；HUD 右上 Btn_Pause/Btn_Intro。
- 地图链路：棋盘→levelmap_export.json→LevelMap.xlsx→tblevelmap.json→SceneInfo.xlsx；日志前缀 [Place]/[HUD]/[TowerInfoView]/[Audit]。

## 敌人四方向（2026-10-16 起；★仅 AdvancedHen 示例获准，其余 118 个须等用户明确审核）
- EnemyDirectionalProfile(配置)/EnemyDirectionalVisual(表现) 显式启用，无配置敌人走原逻辑；BaseEnemy 负责实际首段方向、主轴滞回、镜像恢复、血条补偿、对象池 ResetForSpawn（★池化实例 Animator.Update(0) 须在 GameObjSetActive 之后）。
- 每怪独立 AnimatorOverrideController（保留原曲线/时长/事件+追加垂直姿态）；接入菜单 Tools>塔防>敌人方向示例>1（校验 12 张分件齐全）；MonsterPrefabBuilder 重建时重应用配置并保留 GUID。
- 材料 Docs/EnemyDirectionReview/<怪名>/；真实美术需 OPENAI_API_KEY（imagegen CLI=image_gen.py，默认 gpt-image-2），密钥不入库、不写记录。

## Unity MCP（两版配置不同，严禁混用）
- ★用户授权（2026-10-16）：本工程已接入 Unity MCP，可自行连接/刷新编译/进 Play/运行验证，无需再申请。
- [公司E] com.coplaydev.unity-mcp v10.3.0，HTTP 127.0.0.1:8082/mcp（CatchFish=自研 ws8080 勿混）；★系统代理会劫持 127.0.0.1→502，脚本须内置 ProxyHandler({})；execute_code 需 `{"action":"execute","code":...}`。
- [家用D] stdio uvx mcpforunityserver 3.4.8；Unity 未启动会卡"连接中"→兜底自起 stdio/mcp_unity.py；桥端口 6401→6400；execute_code 先 manage_tools activate scripting_ext。
- ★长调用（GenerateAll/BuildNow）客户端超时但 Unity 继续→靠产物时间戳判定，勿重发；"菜单 6"可能延迟到编译后，勿据"未见 START"重发。
- 无 MCP 时 ReporterHotfixBuild.Start/StartDllOnly；batchmode 与编辑器互斥；GUI 备用 FT_AutoBuildTrigger。

## 真机 [公司E]（MuMu）／APK [家用D]
- adb 先 connect 127.0.0.1:16384；包 com.lzyfreedomtower.freedomtower；★input tap=横屏逻辑 1600x900（截图 1080x600 ×1.481/1.5）；pm clear 需引号。★真机挂热更脚本的资源（场景/预制体/SO）必须 AB 打包（main 场景+BootUI 三件套进 AB、LocalizationSettings 移 FTProject.AOT，维护菜单 Tools/塔防/YooAsset 接入/5）；改 dll 后须 pm clear。
- APK：菜单 6/7 或 `Unity.exe -batchmode -executeMethod FTProject.EditorTools.BuildApk.BuildNow -buildTarget Android -logFile Logs/batch_apk.log`（完建须手动杀）；★编辑器真实路径 `C:\Program Files\Unity 2022.3.62f3c1\`（Hub 下是空壳）；状态 Library/FTBuildApkStatus.txt。坑：Gradle 失败弹模态框卡死主线程／AndroidTargetSdkVersion:0 会选坏包／路径大小写敏感。

## 工具/其他
- ★scan_missing_script_refs.py 须同时收集 Assets+Packages+Library/PackageCache 的 .cs.meta；2 个 never-existed StateMachineBehaviour 已 Compat 占位修复。
- 怪物素材=侧视拆件图集（每怪 1 PNG 全朝左）+_Common/Animations/<家族>；朝向靠 BaseEnemy.FaceMoveDirection 翻 localScale；表情走动画事件 SetHead(int)；gen_monster_catalog.py 生成 MonsterCatalog.cs。
- 发布就绪核查产物 Docs/ReleaseReadiness/（探针+evidence JSON）；云端资料库镜像 Docs/（md 用 space.importer、svg 用 drive/upload）。
