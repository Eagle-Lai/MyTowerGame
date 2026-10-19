# FreedomTower 项目长期记忆（完整版）

> **记录原则（用户已明确）**：不要精简、不要为了篇幅砍内容。宁可记忆文件更大更全，也要保留可复用的规则、参数、坑和原因。
> 建议结构：先按主题分区，每条写「结论 + 关键参数/路径 + 为什么」。过期内容只做标注，不直接删。

## 双版本（按路径区分，严禁跨版）
- 家用版 [家用D] = `D:\FreedomTower_1`；公司版 [公司E] = `E:\MyTowerGame`。
- 每次记录必须标注属于哪个版本；严禁把一版的结论套到另一版。
- 两版通过 GitHub `Eagle-Lai/MyTowerGame`(main) 同步。
- Unity `2022.3.62f3c1` + Built-in Render Pipeline（真实路径 `C:\Program Files\Unity 2022.3.62f3c1\`，Unity Hub 目录下那个是空壳）。
- ★`HotUpdateServer/`、`Bundles/` 被 git 忽略 → **各机拉完必须重打 + 重部署**，否则会出现"新 dll + 旧 AB"混搭的诡异现象（功能看着没生效）。
- `Builds/` 只放行 `Builds/Android/freedomtower.apk`，其余忽略。规则见 `Docs/提交与工作记录规范.md` §3。

## 铁律（流程/规范）
- 命名规范：`自由人塔防` = 文档用名｜`FREEDOM TOWER` = 副标题｜`freedomtower` = 包名｜`FreeTower` = YooAsset 包裹名（★改则热更全部失效）｜`FTProject` = 命名空间。菜单里不要改"塔防"字样；文档里不写盘符。
- 跑生成/挂载类菜单前必须满足 `isCompiling == false && isPlaying == false`；改过 `Assets/Editor/*.cs` 要等编译完再跑菜单；动手前先确认 MCP 连的是本工程（不是 CatchFish）。
- 编辑器脚本不弹 `DisplayDialog`（走 `Debug.Log`）；危险操作拆成两档菜单；DOTweenPro 里那 2 处弹窗保持不变。
- ★提交规范：**全部一起提交**（一笔含未跟踪文件/缓存/产物，不拆不挑）；**先写完记录再提交**（当天 `memory/YYYY-MM-DD.md` + `MEMORY.md` 同一笔）；提交后不再写盘。
- ★可能有并行 Unity/MCP/会话在改资产 → 提交前确认 mtime 静止数分钟；openpyxl 打开 xlsx 会独占锁 → Unity Digest 报 Sharing violation；陈旧 `.git/index.lock`（0 字节且无进程持有）直接删。
- git 走 env 代理（Clash 混合端口 **7897** / socks 7898 亦可 7892）。★本环境默认注入 `http_proxy=127.0.0.1:60044`（服务侧代理，对 github.com 返回 `502 CONNECT tunnel failed`）→ **git 命令必须显式覆盖成 7897**：
  `http_proxy=http://127.0.0.1:7897 https_proxy=http://127.0.0.1:7897 git -c http.version=HTTP/2 pull`
- ★>10MB 推送/拉取必加 `-c http.version=HTTP/2`（HTTP/1.1 过代理必 408，且尾部会混"Everything up-to-date"的假象，别被骗）。
- ★`cannot lock ref` = 并行推送竞态 → 先 `git ls-remote` 确认远端 sha，**不要装 git-lfs**。
- 凭据弹窗 → 在 `~/.gitconfig` 的 `[credential]` 段插一行空 `helper =` 后重试，并用 `ls-remote` 核对 sha。

## 程序集 / HybridCLR（详见 Docs/HybridCLR_Integration.md）
- 共 12 个程序集；热更 6 个 = `Assembly-CSharp` / `LubanLib` / `Gen` / `SuperScrollView` / `Reporter` / `Runtime`。
- ★`Assets/Scripts/**` 全部归属 `FTProject.Runtime`；`Assembly-CSharp.dll` 恒为 5KB 空壳（在 `Assets/` 根增删脚本须重跑 `Generate ▸ All`）。
- ★AOT 侧不得引用热更类型；`Boot.unity` 先 `Assembly.Load` 再进 `main`；入口 `IHotUpdateEntry ← HotUpdateEntry`；包版本以 `libil2cpp-version.txt`（8.14.1）为准。
- ★★热更码新增的 Unity/UGUI API 必须在 AOT 侧有真实引用（防 IL2CPP 裁剪 → 真机 `MissingMethodException` 黑屏）：`BootUiFontProvider`、`BootUiSymbolKeeper`（一对象一 Graphic；全部 try-catch 包裹）。
- ★YooAsset 初始化顺序：`Initialize` → `RequestPackageVersion` → `LoadPackageManifest` 之后才 `SetActiveManifest`；`EnableAddressable = false`；同版本二次构建会报 `ErrorCode 115`。

## 热更 / 资源
- dll 走独立 HTTP 下载（`HotUpdateDllDownloader`），地址 `{ServerUrl}/Android/HybridCLR/`；AB 走 YooAsset HostPlayMode。
- ★服务器地址 = UDP 自动发现，唯一源 `Assets/AOTAssembly/BootServerSelection.cs`（广播串 `FTHOTUPD1|port=8000` / UDP 28000；优先级 server.txt > SelectedUrl > 常量）。全在 AOT 里 → 改动必须重新出 APK。
- ★★共用闸门 `ResServerConfig.IsRemoteHotUpdateAllowed()`（未探测 = true｜探测完无胜出 = false）；服务器不可达必须走 OfflinePlayMode（否则 HostPlayMode 60s 硬失败无回退 = 玩家"一直等不进去"）。
- ★★AB 三铁律：
  1. `FT_HOTUPDATE` 宏在三个平台组都必须开；
  2. 请求路径全部平铺在 ServerUrl 根：`FreeTower.version` / `{ver}.hash` / `{ver}.bytes` / `{哈希}.bundle`（★`unitymonos`、`unityshaders` 用裸 hash）；部署跑 `.workbuddy/tools/deploy_free_tower_cdn.py`；
  3. `CheckUpdateCo` 同版本也要校验缺失文件并下载。
- ★★`BootHotUpdateGate`：在 Boot 内跑完检查 + 全量差异下载之后才加载 main；失败时保留零 AB 依赖的内置 UI，3s 后重试；Launcher 靠 `Gate.Completed` 跳过；编辑器内跳过。
- ★★改热更码真机三件套：①重编 dll（菜单 9/9a）；②AB 有变化才重打（菜单 9，旧"菜单 5"勿用）+ deploy + HTTP 自检；③先跑 `启动热更服务器.bat`（不在 = 闸门关 = 看起来像"功能没做"）。
- ★一键热更 = 菜单 10（`Assets/Editor/HotUpdate/`）：预检 ▸ Generate/All ▸ 拷 dll ▸ AB（版本自增）▸ 清单 ▸ 部署 ▸（可选）PUT 远端 ▸ 本地验证 ▸（可选）Play 冒烟。
  - 状态 `Library/FT_HotUpdateStatus.txt`；历史 `Library/FT_HotUpdate/history/`。
  - ★dll 目标若是 junction → 按 ReparsePoint 跳过，别拷穿。
  - ★只停自己起的服务；Play 冒烟默认关，场景 dirty 即跳过。
- 服务器 `.workbuddy/tools/hotupdate_server.py`（HTTP 8000 + UDP 28000）；根 = 平铺 AB 区 + `Android/{HybridCLR,FreeTower}` junction；被 git 忽略、两版各自建。
  - ★自检必须 `curl --noproxy "*"`（否则被系统代理劫持）。
  - 派生进程无法常驻 → 让用户在终端跑 `.bat`（必须是 CRLF 行尾）。

## 配置 / 多语言 / UI
- Luban：改任何 xlsx 必重导（菜单 3）；新表要在 `__tables__.xlsx` 登记；字段从 B 列开始；`ResTable.cs` 是唯一寻址源。
  - ★`gen_code_json.bat` 会删 `FTProject.Gen.asmdef` → CS0246，跑完要还原。
- 多语言：主键 = 英文原文。
  - ★`gen_localization_table.py` 里的 ROWS **已过期**（168 条 vs 表内 352 条），**禁止重跑**（会丢 180+ 词条）。加词条走 `.workbuddy/tools/append_localization_*.py` + 菜单 3。
  - `TextLocalizer` 的 key 留空会自动取文本；回退链：当前语言 → 英文 → 原文。菜单 308 挂载 / 309 清除。
  - 改 SettingView 的文案 → 重建 → 308 → 菜单 4。
  - ★★两态文本（MuteBtn、Btn_Pause 的 Pause⇄Continue）**不能挂 TextLocalizer**（会被刷回原文）；308 时按父节点名跳过，由 View 按状态写入 + 监听语言事件重算。
- ★名字本地化：塔名 = `TowerConfig.DisplayName`｜关卡名 = `Localization.LevelName(id)`｜怪物名 = 123 词条（`Get(name) ?? name`）。★在 `Awake` 里一次性写文案是坑（切语言不刷新）。
- UI 生成器 `UIPrefabBuilder`：改文案/布局 = 改它 + 重编译 + 重生成。
  - ★塔图标 `UI_TowerIcon_{Normal,Power,Retard}` = 96×96 透明底（`ui_hud`），改图跑 `tower_icon_bg_remove.py`。
  - ★logo = `Assets/Art/Logo/app_icon_512x512.png`（ResTable 里登记 `UI_AppLogo`）。
- ★★用 MCP 验证 UI 时严禁 instantiate 预制体的子物体（TMP 的 OnEnable 会把状态写回资产）→ 自搭 Canvas + Image。
- ★refresh/编译会触发 AB 打标 → 改写 UI prefab / .meta 的 `assetBundleName`；提交前用 `diff_ui_prefabs.py --base` 核对。
- ★★全量重建三个副作用：重排 fileID／清空 `assetBundleName`／抹掉 TextLocalizer → 必须「重建 → 308 → 菜单 4」补齐。
  - 关键尺寸：塔按钮 96×96、VolumeSlider 480×65、`TowerCodexItem` / `SelectLevelItem` 根节点 active=false。
  - ResTable 漏登记 = 真机打不开。
- ★HUD 右上两按钮职责：`Btn_Pause` = 只切暂停/继续（不弹窗，两态文本）；`Btn_Intro` = 只打开暂停菜单（不暂停，文案 `Menu`）。暂停的唯一写入口 = `GameClock.SetPaused`，`PauseView` 不写 timeScale；标题按 `IsPaused` 取词。

## 适配（多分辨率）
- Canvas = Overlay，1920×1080，Match 0.5。
- ★根画布不能直接做安全区 → `SafeAreaFitter` 挂到 Bg/Normal/Tips 三个 Panel（`UIManager.EnsureSafeArea`）。
- ★棋盘取景在 `CameraController`（底 2 格 / 顶 1 格 / 侧 1 格 + 安全区 + 相机下移 0.5 格），`BackgroundScale = 2.2`。
- ★边缘锚已固化进 `UIPrefabBuilder`：塔按钮底锚 49、Speed/Start (64,77)、箭头 60 / Codex 34、Close 68、Quit 74；单步重建菜单 310/311/312。
- ★局部布局按父 RectTransform 的**实际可用尺寸**算，不动基准 CanvasScaler。三组件：
  - `UIFullScreenBackground`：Bg 按 root Canvas 世界角点偏移，遮罩不漏边；
  - `UIFitInParent`：固定 Panel 仅在父尺寸不足时等比缩小，留 24，max=1；
  - `UIResponsivePage`：MainMenu 内容列。
- 规则唯一源 `Assets/Editor/UIResolutionLayout.cs`；已有资源用菜单 330 定点更新（**别全量重建**）；验证用 `Assets/Editor/UIResolutionVerifier.cs`（需 Play + 隔离存档）。记录在 `Docs/UIResolution/20261018/`。

## SuperScrollView（★最坑）
- `InitListView` 会一次性快照 viewport → **绝不能放 OnEnable 初始化**；`SelectView.Build` 挂 `_pendingInit`，首帧 `LateUpdate` 再 `DoInitListView`。
- 吸附硬约束：视口宽 = 卡片宽 = 1150×550；`pivot.x = 0`、`anchoredPosition.x = -575`；三处必须同步 `UIPrefabBuilder SelectItemW` ↔ `SelectView ItemWidth(1150/56)` ↔ `SelectLevelItem`。
- 图鉴视口中心 460×640。

## 生命周期 / 存档 / 音频 / 玩法
- `LevelClearView` 胜败共用 `OnGameOver()`；唯一的拆卸入口是 `TeardownLevel()`。
- 存档只走 `SaveManager`（禁 SQL / PlayerPrefs）；改表三步：`CreateStatements` → `CurrentVersion + 1` → `RunMigrations`。
- 音频 = 丢文件 + `gen_audio_catalog.py`；BGM 2 源 + `AudioFadeDriver`；倍速唯一源 `Core/GameClock.cs`（`timeScale` 只取 0/1）。
- ★塔型：Normal1（打飞+走）/ Aoe2 火力仅打走 / Slow3 光环；Pierce4、Laser5 已删（编号不回收，别复用）；对空与否看塔表 `canAttackAir`。
- ★塔攻击表现：普通/火力塔不发子弹，开火 = 即时命中 + 序列帧。
  - `TowerFireFx`：枪口焰挂到炮管 `BarrelPoint` 子节点、local 置零；落点爆炸走对象池；帧由 `gen_tower_fire_frames.py` 生成。
  - ★散帧 meta 必须 `alignment: 9`(Custom) + `spritePivot y = 0.2`；写成 `alignment: 1` = TopLeft（底中应是 7）→ 焰会被甩到炮口右下角。
  - 时长权威 = `BaseBullet.SlowDurationSec` / `DotDurationSec`。
- ★建造交互 v3：点按 = 放置态；长按 0.25s 或位移 30px = 拖拽（ghost 跟手、松手校验、拖回按钮或拖出棋盘静默取消）。
- 地图链路：棋盘 → `levelmap_export.json` → `LevelMap.xlsx` → `tblevelmap.json` → `SceneInfo.xlsx`；日志前缀 `[Place]` / `[HUD]` / `[TowerInfoView]` / `[Audit]`。
- ★新增一关 = 四表齐全：LevelMap(id) + SceneInfo(mapId、RoundList) + RoundData + EnemyList。现役 20 关 × 20 波。
- ★编辑器全解锁 = `SaveManager.UnlockAllLevelsInEditor`（真机仍逐关解锁）。

## 敌人四方向（★获准名单 = AdvancedHen + Monkey，其余须用户点名）
- `Profile`(配置) / `DirectionalVisual`(表现) 显式启用，无配置时走原逻辑；`BaseEnemy` 负责首段方向、主轴滞回、镜像、血条补偿、池化 `ResetForSpawn`（★`Animator.Update(0)` 必须在 `SetActive` 之后调）。
- 两套架构（每片段 9 条 DirectionVisual / Motion 曲线）：
  - ①AdvancedHen = `AnimatorOverrideController`（换 clip，不换状态机）；
  - ②Monkey = **真实 AnimatorController**：新增 WalkUp/WalkDown 状态 + int 参数 `Dir`(0 水平 / 1 上 / 2 下)；AnyState → 垂直态条件 `State==2 && !Action && Dir`；原 `→Walk`/`→Run` 加 `Dir==0` 防抢；`Face()` 自动 `SetInteger("Dir")`。
  - 新怪 = 在 `EnemyDirectionSpec` 加条目。
- Monkey v2 细节（真实控制器由 CopyAsset Bunny 后 API 改造，共享资源零改动）：
  - 原 6 个状态换成 `_Directions` motion + 新增 WalkUp/WalkDown（纯 DirectionVisual 曲线 clip）；垂直奔跑留 WalkUp/Down 靠 Speed 提速。
  - `Face()` 与 `BaseEnemy` 用同款 API = AOT 安全；控制器无 `Dir` 参数时静默无效。
- 构建器 `EnemyDirectionPrefabBuilder`；Monkey 布局：头 2.2@1.95 / 躯干 1.5@0.6 / 臂 1.0@±0.80,0.80 / 腿 0.8@±0.36,-0.20（PPU=100），bob 0.04/0.05/0.13。
  - `BuildAndVerify` 幂等 + 写 `Library/FT_<名>DIR_STATUS.txt`（42 项校验）。
  - ★Verify 坑：clips 是 `AnimationClipPair[]`；双腿交替要在同一时刻比左右差；Death 倾斜按片段时长百分比定点采样；`AnimatorCondition` 的属性名是 `mode` 不是 `conditionMode`。
  - 菜单：Tools ▸ 塔防 ▸ 敌人方向示例 ▸ 1/2 接入、3 方向动画预览窗（走真实 `SetAnimState`/`Face` + `Animator.Update`）。
- ★测试坑：直接 `Instantiate` 不走池 `Init` → `_anim` 未缓存 → `SetAnimState` 静默无效；改 `animator.SetInteger("State", N)` 或走 Init。
- ★AI 分件美术：ImageGen + PIL 拼侧视参考图 + 原 atlas 双图输入，模板 `Docs/EnemyDirectionReview/<怪名>/`（含 `generation_*.txt`）。
  - ★生成品红底非纯色（每图不同）→ 必须从角点采样实际背景色再按距离阈值抠；
  - ★躯干格要"无尾完整椭圆 + 轮廓含底边完整可见"（带尾巴会拼装悬空、重心偏）；
  - Wing 槽位语义按怪适配（Monkey = 手臂）。

## Unity MCP（两版严禁混用）
- ★用户授权（10-16）：可自行连接 / 刷新编译 / 进 Play / 验证，无需逐次申请。
- ★工具表刷不出 → 自写 streamable-HTTP 客户端（`.workbuddy/tmp_monkey_dir/mcp_unity.py`，内置 `ProxyHandler({})`）；`execute_code` 里 codedom 一律用双引号。
- [公司E] `com.coplaydev.unity-mcp` v10.3.0，HTTP `127.0.0.1:8082/mcp`（CatchFish 是自研 ws 8080，勿混）。
  - ★系统代理会劫持 127.0.0.1 → 502，脚本必须 `ProxyHandler({})`；
  - `execute_code` 参数需 `{"action":"execute","code":...}`；
  - 客户端先 `initialize` 取 `mcp-session-id`，再按 SSE 解析。
- [家用D] stdio `uvx mcpforunityserver 3.4.8`；Unity 未启动会卡"连接中" → 兜底自起 stdio/`mcp_unity.py`；桥端口 6401 → 6400；`execute_code` 前先 `manage_tools activate scripting_ext`。
- ★长调用（GenerateAll / BuildNow）客户端会超时但 Unity 仍在跑 → 靠产物时间戳判定，**勿重发**；batchmode 与编辑器互斥。
- 无 MCP 时的兜底：`ReporterHotfixBuild.Start` / `StartDllOnly`；GUI 备用 `FT_AutoBuildTrigger`。

## 真机 [公司E]（MuMu）/ APK [家用D]
- adb 先 `connect 127.0.0.1:16384`；包名 `com.lzyfreedomtower.freedomtower`；★`input tap` 坐标按横屏逻辑 1600x900（截图 1080x600 ×1.481/1.5）；`pm clear` 参数需加引号。
- ★真机要热更的资源（场景/预制体/SO）必须 AB 打包：main 场景 + BootUI 三件套进 AB、`LocalizationSettings` 归 `FTProject.AOT`（维护菜单 5）。改 dll 后须 `pm clear`。
- APK：菜单 6/7，或
  `Unity.exe -batchmode -executeMethod FTProject.EditorTools.BuildApk.BuildNow -buildTarget Android -logFile Logs/batch_apk.log`（完建须手动杀进程）；状态 `Library/FTBuildApkStatus.txt`。
- 坑：Gradle 失败会弹模态框卡死／`TargetSdkVersion:0` 会选出坏包／路径大小写敏感。

## 工具 / 其他
- ★Unity 调用外部 Python 的兜底**禁止硬编码用户路径** → `LevelMapEditorWindow.BuildAbsFallbackCandidates()` 动态扫描；本机命中 `~/.workbuddy/binaries/python/envs/default`（openpyxl 3.1.5）。
- ★`scan_missing_script_refs.py` 必须同时收集 `Assets` + `Packages` + `Library/PackageCache` 的 `.cs.meta`。
- 怪物素材 = 侧视拆件图集（每怪 1 PNG，全朝左）+ `_Common/Animations/<家族>`；朝向靠 `BaseEnemy.FaceMoveDirection` 翻 localScale；表情走动画事件 `SetHead(int)`；`gen_monster_catalog.py` 生成 `MonsterCatalog.cs`。
- 发布就绪核查见 `Docs/ReleaseReadiness/`；云端资料库镜像 `Docs/`（md → space.importer、svg → drive/upload）。

## 已知待办 / 环境事实
- 2026-10-19 [公司E]：已 pull 到 `f3a747a`（UI 多分辨率适配 + HUD 暂停/菜单两按钮职责重划）。拉取含热更码与 Luban xlsx 变更，**尚未**重导配置 / 重编 dll / 重打 AB。
## 出包铁律（2026-10-19 黑屏事故）
- ★★出 APK 前**必须核对 Build Settings 场景列表**：`Boot.unity` 启用 + `Main.unity` 禁用（main 只能从 AB 加载）。
  `733ba00`（金色换皮提交）曾把 EditorBuildSettings 改成只含 Main 且启用 → APK 直接从 Main 空壳场景启动
  （热更脚本打包时被剔除）→ 全脚本 missing、黑屏卡死、logcat 无任何 `[Boot]` 日志。
  识别特征：启动 1 秒内出现 `The referenced script (FTProject.*) is missing` 且完全无 [Boot] 日志 = 起始场景错了，不是热更链路问题。
  已恢复 `ProjectSettings/EditorBuildSettings.asset` 为 ee973da 版本（Boot enabled / Main disabled）。
- ★热更部署铁律（2026-10-19）：AB 构建（菜单9）后**必须立刻跑** `deploy_free_tower_cdn.py`，否则服务器根
  `FreeTower.version` 指针停留在旧版本 → 客户端拿旧清单，新增资源（如 tblevelrating）报"清单找不到定位地址"。
  验证：`curl --noproxy "*" http://127.0.0.1:8000/FreeTower.version` 应等于本地 Bundles 最新版本目录。
  另：`Bundles/Android/FreeTower/{1.0.25,1.0.26}/`（历史版本区）与服务器根平铺区是两回事，前者不被运行时请求。
