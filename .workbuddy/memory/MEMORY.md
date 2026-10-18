# FreedomTower 长期记忆（只留不变量；细节见 Docs/ 与 memory/ 日志）

## 双版本
- 家用D=`D:\FreedomTower_1`｜公司E=`E:\MyTowerGame`；按路径定版本、记录标 [家用D]/[公司E]，严禁跨版；经 Eagle-Lai/MyTowerGame(main) 同步。Unity 2022.3.62f3c1 + Built-in RP。
- ★`HotUpdateServer/`、`Bundles/` 被 git 忽略→各机拉完必须重打+重部署（否则"新 dll+旧 AB"混搭）；`Builds/` 只放行 `Builds/Android/freedomtower.apk`，其余忽略。规则 Docs/提交与工作记录规范.md §3。

## 铁律
- 命名：自由人塔防=文档｜FREEDOM TOWER=副标题｜freedomtower=包名｜FreeTower=YooAsset 包裹名(改则热更失效)｜FTProject=命名空间；菜单勿改"塔防"；文档不写盘符。
- 跑生成/挂载菜单前 `isCompiling==false && !isPlaying`；改 `Assets/Editor/*.cs` 等编译完再跑；先核 MCP 连的是本工程。
- 编辑器脚本不弹 DisplayDialog（走 Debug.Log；危险操作拆两档菜单；DOTweenPro 2 处弹窗不动）。
- ★提交：全部一起提交（一笔含未跟踪/缓存/产物，不拆不挑）；先写完记录再提交（当天日志+MEMORY.md 同笔），提交后不再写盘。
- ★可能有并行 Unity/MCP/会话在改资产→提交前确认 mtime 静止数分钟；openpyxl 开 xlsx 独占锁→Unity Digest 报 Sharing violation；陈旧 `.git/index.lock`(0 字节无进程) 直接删。
- git push：弹 credential helper→`~/.gitconfig` `[credential]` 插空 `helper =` 重试并 `ls-remote` 核 sha；GitHub 走 env 代理（Clash 7897/7892）。★>10MB 必 `-c http.version=HTTP/2`（1.1 过代理必 408，且尾部混"Everything up-to-date"假象）。★`cannot lock ref`=并行推送竞态，先 ls-remote 确认，勿装 git-lfs。

## 程序集/HybridCLR（Docs/HybridCLR_Integration.md）
- 12 程序集，热更 6=Assembly-CSharp/LubanLib/Gen/SuperScrollView/Reporter/Runtime；★Assets/Scripts 全归 FTProject.Runtime；Assembly-CSharp.dll 恒 5KB 空壳（增删 Assets/ 根脚本须重跑 Generate▸All）。
- ★AOT 不得引用热更类型；Boot.unity 先 Assembly.Load 再进 main；入口 IHotUpdateEntry←HotUpdateEntry；包版本=libil2cpp-version.txt(8.14.1)。
- ★★热更码新增 Unity/UGUI API 必须在 AOT 侧真实引用（防裁剪→真机 MissingMethodException 黑屏）：`BootUiFontProvider`、`BootUiSymbolKeeper`（一对象一 Graphic；全 try-catch）。
- ★YooAsset：Initialize→RequestPackageVersion→LoadPackageManifest 才 SetActiveManifest；EnableAddressable=false；同版本二次构建 ErrorCode115。

## 热更/资源
- dll=独立 HTTP(`HotUpdateDllDownloader`) `{ServerUrl}/Android/HybridCLR/`；AB=YooAsset HostPlayMode。
- ★地址=UDP 自动发现，唯一源 `Assets/AOTAssembly/BootServerSelection.cs`（`FTHOTUPD1|port=8000`/UDP 28000；server.txt>SelectedUrl>常量）；全在 AOT→改动必须出 APK。
- ★★共用闸门 `ResServerConfig.IsRemoteHotUpdateAllowed()`（未探测=true｜探测无胜出=false）；不可达必走 OfflinePlayMode（HostPlayMode 60s 硬失败无回退="一直等不进去"）。
- ★★AB 三铁律：①FT_HOTUPDATE 宏三平台组必开；②请求全平铺 ServerUrl 根（FreeTower.version/{ver}.hash/.bytes/{哈希}.bundle；★unitymonos/unityshaders=裸 hash）；部署跑 `.workbuddy/tools/deploy_free_tower_cdn.py`；③CheckUpdateCo 同版本也校验缺失并下载。
- ★★`BootHotUpdateGate`：Boot 内跑完检查+全量差异下载才加载 main；失败留零 AB 依赖内置 UI 3s 重试；Launcher 靠 Gate.Completed 跳过；编辑器跳过。
- ★★改热更码真机三件套：①重编 dll=菜单 9/9a；②AB 变化才重打=菜单 9（旧"菜单5"勿用）+deploy+HTTP 自检；③先跑启动热更服务器.bat（不在=闸门关=形似"功能没做"）。
- ★一键热更=菜单 10（`Assets/Editor/HotUpdate/`）：预检▸Generate/All▸拷 dll▸AB（版本自增）▸清单▸部署▸(可选)PUT 远端▸本地验证▸(可选)Play 冒烟。状态 `Library/FT_HotUpdateStatus.txt`、历史 `Library/FT_HotUpdate/history/`。★dll 目标是 junction→按 ReparsePoint 跳过；★只停自己起的服务；Play 冒烟默认关、场景 dirty 即跳过。
- 服务器 `.workbuddy/tools/hotupdate_server.py`（HTTP 8000+UDP 28000）；根=平铺 AB 区 + Android/{HybridCLR,FreeTower} junction；git 忽略、两版各自建。★自检必须 `curl --noproxy "*"`；派生进程无法常驻→用户终端跑 .bat(CRLF)。

## 配置/多语言/UI
- Luban：改 xlsx 必重导（菜单3）；新表登记 __tables__.xlsx；字段从 B 列起；ResTable.cs=唯一寻址源。★gen_code_json.bat 会删 FTProject.Gen.asmdef→CS0246。
- 多语言：主键=英文原文；★`gen_localization_table.py` 的 ROWS 已过期（168 vs 表 352 条），**禁止重跑**（丢 180+ 词条）→加词条走 `.workbuddy/tools/append_localization_*.py` + 菜单3；TextLocalizer key 留空自动取；回退 当前→英文→原文；菜单 308 挂/309 清。改 SettingView→重建→308→菜单4。★★两态文本（MuteBtn、Btn_Pause Pause⇄Continue）**不能挂 TextLocalizer**（会刷回原文），308 按父节点名跳过，由 View 按状态写+语言事件重算。
- ★名字本地化：塔名=TowerConfig.DisplayName｜关卡名=Localization.LevelName(id)｜怪物名=123 词条（Get(name)??name）；Awake 一次性写文案=坑。
- UI 生成器 UIPrefabBuilder（改文案/布局=改它+重编译+重生成）。★塔图标 UI_TowerIcon_{Normal,Power,Retard}=96×96 透明底（ui_hud），改图跑 tower_icon_bg_remove.py；★logo=`Assets/Art/Logo/app_icon_512x512.png`（ResTable 登记 UI_AppLogo）。
- ★★MCP 验证 UI 严禁 instantiate 预制体子物体（TMP OnEnable 写回资产）→自搭 Canvas+Image。
- ★refresh/编译触发 AB 打标→改写 UI prefab/.meta 的 assetBundleName；提交前 `diff_ui_prefabs.py --base` 核对。
- ★★全量重建三副作用：重排 fileID／清空 assetBundleName／抹掉 TextLocalizer→必须 重建→308→菜单4。关键尺寸：塔按钮 96×96、VolumeSlider 480×65、TowerCodexItem/SelectLevelItem 根 active=false。ResTable 漏登记=真机打不开。
- ★HUD 右上两按钮：`Btn_Pause`=只切暂停/继续（不弹窗，两态文本）；`Btn_Intro`=只开暂停菜单（不暂停，文案 `Menu`）。暂停唯一写入口=`GameClock.SetPaused`，`PauseView` 不写 timeScale；标题按 `IsPaused` 取词。

## 适配（多分辨率）
- Canvas=Overlay 1920×1080 Match0.5；★根画布不可做安全区→SafeAreaFitter 挂 Bg/Normal/Tips 三 Panel（UIManager.EnsureSafeArea）；★棋盘取景在 CameraController（底2/顶1/侧1格+安全区+相机下移0.5格），BackgroundScale 2.2。
- ★边缘锚已固化进 UIPrefabBuilder（塔按钮底锚49、Speed/Start(64,77)、箭头60/Codex34、Close68、Quit74；单步重建菜单 310/311/312）。
- ★局部布局按父 RectTransform **实际可用尺寸**，不动基准 CanvasScaler。三组件：`UIFullScreenBackground`（Bg 按 root Canvas 世界角点偏移，遮罩不漏边）、`UIFitInParent`（固定 Panel 仅父不足时等比缩小、留 24、max=1）、`UIResponsivePage`（MainMenu 内容列）。规则唯一源 `Assets/Editor/UIResolutionLayout.cs`；已有资源用菜单 330 定点更新（别全量重建）；验证 `Assets/Editor/UIResolutionVerifier.cs`（需 Play+隔离存档）。记录 Docs/UIResolution/20261018/。

## SuperScrollView（★最坑）
- InitListView 一次性快照 viewport→绝不能 OnEnable 初始化；SelectView.Build 挂 _pendingInit、首帧 LateUpdate 再 DoInitListView。
- 吸附硬约束：视口宽=卡片宽 1150×550；pivot.x=0、anchoredPosition.x=-575；三处同步 UIPrefabBuilder SelectItemW↔SelectView ItemWidth(1150/56)↔SelectLevelItem。图鉴视口中心 460×640。

## 生命周期/存档/音频/玩法
- LevelClearView 胜败共用 OnGameOver()；唯一拆卸 TeardownLevel()。存档只走 SaveManager（禁 SQL/PlayerPrefs）；改表三步 CreateStatements→CurrentVersion+1→RunMigrations。
- 音频=丢文件+gen_audio_catalog.py；BGM 2源+AudioFadeDriver；倍速唯一源 Core/GameClock.cs（timeScale 只 0/1）。
- ★塔型：Normal1(飞+走)/Aoe2 火力仅走/Slow3 光环；Pierce4/Laser5 已删（编号不回收）；对空=塔表 canAttackAir。
- ★塔攻击表现：普通/火力塔不发子弹，开火=即时命中+序列帧（TowerFireFx 枪口焰挂 **BarrelPoint 子节点、local 置零**+落点爆炸池；生成器 gen_tower_fire_frames.py）；★散帧 meta 必须 `alignment: 9`(Custom)+`spritePivot y=0.2`；**alignment:1=TopLeft（底中=7）→ 焰被甩到炮口右下角**；时长权威=BaseBullet.SlowDurationSec/DotDurationSec。
- ★建造交互 v3：点按=放置态；长按0.25s/位移30px=拖拽（ghost 跟手、松手校验、拖回按钮/棋盘外静默取消）。
- 地图链路：棋盘→levelmap_export.json→LevelMap.xlsx→tblevelmap.json→SceneInfo.xlsx；日志前缀 [Place]/[HUD]/[TowerInfoView]/[Audit]。
- ★新增一关=四表齐全：LevelMap(id)+SceneInfo(mapId、RoundList)+RoundData+EnemyList。现役 20 关×20 波。
- ★编辑器全解锁=`SaveManager.UnlockAllLevelsInEditor`（真机仍逐关解锁）。

## 敌人四方向（★获准名单=AdvancedHen+Monkey，其余 117 个须用户点名）
- Profile(配置)/DirectionalVisual(表现) 显式启用，无配置走原逻辑；BaseEnemy 管首段方向、主轴滞回、镜像、血条补偿、池化 ResetForSpawn（★Animator.Update(0) 须在 SetActive 之后）。
- 两架构（每片段 9 条 DirectionVisual/Motion 曲线）：①AdvancedHen=AnimatorOverrideController；②Monkey=**真实 AnimatorController**，新增 WalkUp/WalkDown + int 参数 **Dir**(0水平/1上/2下)；AnyState→垂直态 State==2&&!Action&&Dir，原 →Walk/→Run 加 Dir==0 防抢；`Face()` 自动 SetInteger("Dir")。新怪=EnemyDirectionSpec 加条目。
- ★构建器 `EnemyDirectionPrefabBuilder`；Monkey 布局 头2.2@1.95/躯干1.5@0.6/臂1.0@±0.80,0.80/腿0.8@±0.36,-0.20（PPU=100）；BuildAndVerify 幂等+写 Library/FT_<名>DIR_STATUS.txt。★Verify 坑：clips 是 AnimationClipPair[]；双腿交替比同一时刻左右差；AnimatorCondition 属性名是 mode。菜单 1/2 接入、3 预览。
- ★测试坑：直接 Instantiate 不走池 Init→_anim 未缓存→SetAnimState 静默无效；改 `animator.SetInteger("State",N)` 或走 Init。
- ★AI 分件美术：ImageGen + PIL 拼侧视参考图+原 atlas 双图输入，模板 Docs/EnemyDirectionReview/<怪名>/；★品红底非纯色→角点采样实际底色再阈值；★躯干格要"无尾完整椭圆+含底边"。

## Unity MCP（两版严禁混用）
- ★用户授权（10-16）：可自行连接/刷新编译/进 Play/验证，无需再申请。★工具表刷不出 unity-mcp→自写 streamable-HTTP 客户端（`.workbuddy/tmp_monkey_dir/mcp_unity.py`，ProxyHandler({})）；execute_code codedom 一律双引号。
- [公司E] v10.3.0 HTTP 127.0.0.1:8082/mcp（CatchFish=ws8080 勿混）；★系统代理劫持 127.0.0.1→502，须 ProxyHandler({})；execute_code 需 `{"action":"execute","code":...}`。
- [家用D] stdio uvx mcpforunityserver 3.4.8；Unity 未启动→兜底自起 stdio/mcp_unity.py；桥端口 6401→6400；execute_code 先 manage_tools activate scripting_ext。
- ★长调用（GenerateAll/BuildNow）客户端超时但 Unity 继续→靠产物时间戳判定，勿重发；batchmode 与编辑器互斥。

## 真机 [公司E]（MuMu）／APK [家用D]
- adb 先 connect 127.0.0.1:16384；包 com.lzyfreedomtower.freedomtower；★input tap=横屏逻辑 1600x900；pm clear 需引号。★真机要热更的资源（场景/预制体/SO）必须 AB 打包（main 场景+BootUI 三件套、LocalizationSettings 归 FTProject.AOT）；改 dll 后须 pm clear。
- APK：菜单 6/7 或 `Unity.exe -batchmode -executeMethod FTProject.EditorTools.BuildApk.BuildNow -buildTarget Android -logFile Logs/batch_apk.log`（完建须手动杀）；★真实路径 `C:\Program Files\Unity 2022.3.62f3c1\`（Hub 下是空壳）；状态 Library/FTBuildApkStatus.txt。坑：Gradle 失败弹模态框卡死／TargetSdkVersion:0 选坏包／路径大小写敏感。

## 工具/其他
- ★Unity 调外部 Python 解释器兜底**禁止硬编码用户路径**→`LevelMapEditorWindow.BuildAbsFallbackCandidates()` 动态扫描；本机命中 `~/.workbuddy/binaries/python/envs/default`（openpyxl 3.1.5）。
- ★scan_missing_script_refs.py 须同时收集 Assets+Packages+Library/PackageCache 的 .cs.meta。
- 怪物素材=侧视拆件图集（每怪 1 PNG 全朝左）+_Common/Animations/<家族>；朝向靠 BaseEnemy.FaceMoveDirection 翻 localScale；表情走动画事件 SetHead(int)；gen_monster_catalog.py 生成 MonsterCatalog.cs。
- 发布就绪核查 Docs/ReleaseReadiness/；云端资料库镜像 Docs/（md→space.importer、svg→drive/upload）。
