# FreedomTower 项目长期记忆

> 只记"踩坑就返工"的不变量；细节见 `Docs/` 与 `YYYY-MM-DD.md`。⚠️ 有注入上限（超出会被截断），新增前先想能不能删。

## ★ 双版本制度（2026-10-12 确立，开工先读）

本工程有两份**并行副本**，经 GitHub `Eagle-Lai/MyTowerGame` 同步（`.workbuddy/` 记忆随 git 走）：

| 版本 | 机器 | 工作区 | 机器环境 / 状态 |
|---|---|---|---|
| **家用D盘** | 家用电脑 | `D:\FreedomTower_1` | Unity 2022.3.62f3c1；Android 工具链 `D:\Android\`；工具/venv 在 `C:\Users\78296\` |
| **公司E盘** | 公司电脑（`BF-202610081033`） | `E:\MyTowerGame` | 2026-10-12 clone；Unity/Android 工具链未装；git 未配 user.name |

- ★ **开工第一步 = 识别版本**：看当前工作区路径（`E:\MyTowerGame`→公司E盘；`D:\FreedomTower_1`→家用D盘）；拿不准停下问用户，别猜。
- ★ **记录必须标版本**：日志 / 记忆条目标 `[家用D]` 或 `[公司E]`；只在一版做过的改动要显式注明（两版内容可能分叉）。
- ★ **环境严禁跨版本套用**：上表"机器环境"只对各自机器有效（如 `D:\Android` 在公司机上不存在）。
- 历史归属：2026-09-25 ~ 10-11 全部记录产自**家用D盘**（用户 2026-10-12 确认）。

## 铁律

- **游戏名《自由人塔防》/ FREEDOM TOWER**；6 种写法各有归属：`自由人塔防`=文档｜`FREEDOM TOWER`=游戏内副标题｜`freedomtower`=productName/包名｜`FreeTower`=**YooAsset 包裹名**（改了热更失效）｜`FTProject`=命名空间｜`freetower_*`=存档名。⚠️《坚守阵地》：指原版 Fieldrunners 的引用保留。
- 工程克隆自 `com.unity.template.3d@5.0.4` → 异常默认值先查模板残留（Template3D/SampleScene 已修）。
- Unity 菜单 = `Tools/塔防/...`（~40 处）："塔防"是玩法类型不是游戏名，不要改。
- ★ 动手前确认 MCP **连的是本工程**（在线≠连对：查 `Application.dataPath`／Unity 进程 `-projectPath`）；挂了停下让用户确认、别自作主张。
- ★ 跑生成/挂载菜单前必须 `isCompiling==false && isPlaying==false`；改 `Assets/Editor/*.cs` 后必须 `refresh_unity(compile="request", scope="all")` 等编译完再跑菜单 → 否则静默用旧程序集（最坑返工点）。
- 编辑器脚本一律不弹 `EditorUtility.DisplayDialog`（阻塞 MCP/CI），结果走 `Debug.Log`；危险操作拆两档菜单。第三方 DOTweenPro 的 2 处弹窗不动。
- 交付文档不写盘符路径（用"本工程/工程根"）——两台机器盘符不同（见「双版本制度」），写死必错；旧 `D:\FreedomTower`（无 _1）已不存在。
- `git push`：远端 `Eagle-Lai/MyTowerGame.git`（public：fetch 免凭证，不能拿它验凭证）。弹「Select a credential helper」根治 = 用户级 `~/.gitconfig` `[credential]` 插空 `helper =`；别用 `GIT_CONFIG_SYSTEM=/dev/null`。失败重试一次，看 `main -> main` + `ls-remote` 核 sha。
- worktree 副本（若出现 `workbuddy/main-*`）：常落后 → 同步前逐字节 diff；权威永远是工程根。
- Unity 2022.3.62f3c1 + Built-in RP（霓虹只能烘进贴图）。`screenshot` 偶发丢 Overlay 层；改 `UIPrefabBuilder` 后对比 `ui_prefabs_preRebuild/*.prefab`。

## 环境 / 配置 / 资源

- [家用D] Unity 在 `C:\Program Files\Unity 2022.3.62f3c1\`（非 Hub 标准目录；找路径用 `Get-Process Unity`；Hub「Add modules」不可用）。**公司E盘未装**。
- [家用D] Android 工具链 `D:\Android\`：jdk\temurin-11｜sdk｜ndk\23.1（**公司E盘未装**）；Unity 侧写 EditorPrefs 三键（属性 setter 不落盘）。**cmdline-tools 必须 = 6**（12.0→class 61=JDK17→`UnsupportedClassVersionError`；别迁就 JDK 17）。
- Luban：改 `Luban/Config/Datas/*.xlsx` 必重导（菜单`3.导出配置表`，`DOTNET_ROLL_FORWARD=LatestMajor`）；新表先登记 `__tables__.xlsx`。
- ⚠️ xlsx：字段从 B 列起（A 列 tag）；行1/2/3=名/类型/说明；列名须合法 C# 标识符。★ 导出会删 `Assets/Gen/` 里它不认识的文件 → `LubanExporter.KeepFilesInCodeDir` 保护（改 Editor 脚本先重编译）。
- `ResTable.cs` = 唯一寻址源（`check_code.py` 不扫 `Configs.ConfigKeys`，加表要手工同步）；`ResLoader` 三套按宏切，新依赖一律加宏。
- ★ YooAsset 初始化必须三步：`InitializePackageAsync` → `RequestPackageVersionAsync` → `LoadPackageManifestAsync`（最后才 `SetActiveManifest`）；漏中间步 → 之后每次加载报 `Active package manifest not found.`。`EnableAddressable=false`；同版本二次构建 `ErrorCode115`。
- 战斗无物理：`EnemyGrid` + `CombatSystem` 集中 tick；塔无目标绝不开火。

## 程序集 / HybridCLR（细节 Docs/HybridCLR_Integration.md）

- 12 程序集。AOT = `FTProject.AOT`(+`ThirdParty.AOT`/`iTween`/`Editor`/`HybridCLRGenerate`)；热更 6 = `Assembly-CSharp`/`LubanLib`/`Gen`/`ThirdParty.SuperScrollView`/`ThirdParty.Reporter`/`Runtime`。
- ★ `Assembly-CSharp` = 兜底集（当前仅 `Assets/TestNull.cs`），已纳入热更。⚠️ 增删 `Assets/` 根脚本 → 必须重跑 `Generate ▸ All` + 拷贝，否则报缺 dll。
- ★ `FTProject.HybridCLRGenerate` 为 `AOTGenericReferences.cs` 单建（否则它掉进兜底集变热更类型、违铁律）。
- ★ 铁律：**AOT 主包不得引用热更类型**。纯 AOT `Boot.unity` 先 `Assembly.Load` 再进 `main`；BuildSettings Boot(0)→main(1)；反向引用允许。
- 入口契约 = 接口：`FTProject.AOT.IHotUpdateEntry` ← `FTProject.HotUpdateEntry`；`HotUpdateEntryLocator` 是唯一反射点；实现类须可无参构造。
- `DOTween`/`DemiLib`/`LitJson` 是预编译 DLL → 只能 AOT；DOTween/iTween 零使用。
- 热更 dll 顺序：`Assembly-CSharp → LubanLib → Gen → SuperScrollView/Reporter → Runtime`；名单两处同步：`HotUpdateAssembler.HotUpdateAssemblies` ↔ `HybridCLRSettings.asset`（Unity API 改不落盘 → 直接改 YAML）。编辑器下跳过已加载。
- HybridCLR 包版本必须 = `HybridCLRData/.../libil2cpp-version.txt` 戳（8.14.1），否则 `Generate/All` 报 must run Installer。
- ★ `AOTMetaAssemblies` 6 项：`System.Core`/`UnityEngine.AssetBundleModule`/`UnityEngine.CoreModule`/`UnityEngine.JSONSerializeModule`/`YooAsset`/`mscorlib`。三处同步：`AOTGenericReferences.cs` ↔ `HotUpdateAssembler` ↔ `HybridCLRDllCopier`（编辑器工具不能引 AOT 集 → 常量手写，菜单自动比对）。
- `StreamingAssets/HybridCLR/*.dll` 由菜单 HybridCLR/1 拷贝（源 `HybridCLRData/HotUpdateDlls/<平台>/`）；运行时优先级 = persistentDataPath > StreamingAssets > Library/ScriptAssemblies(仅编辑器)。
- ★ Boot→main 编辑器实测通过（2026-10-11，判据看活动场景变 `main`）。⚠️ 真机未验证：APK 内 StreamingAssets 是压缩包 → 必须 `UnityWebRequest` 或首启释放，**打包前必须处理**。

## 热更 / 资源服务器

- 两条链路：①dll = AOT 侧独立 HTTP（`HotUpdateDllDownloader`，刻意不走 YooAsset）；②AB = YooAsset `HostPlayMode`。
- `IRemoteService`(3.0.x) = `GetRemoteUrls(fileName)`；⚠️ fileName 已含平台/包裹/版本，只拼根 URL。
- 地址唯一源 = `Core/Res/ResServerConfig.cs`（static class；`persistentDataPath/server.txt` 可覆盖）。AOT 侧不能引它 → `BootLoader.ServerUrlForAOT` 是刻意复制常量，**两处同步**。
- 模式分支（`YooAssetResLoader.CreateInitOptions`）：`FT_HOTUPDATE`→HostPlayMode，否则离线；宏开关 `Assets/Editor/YooAsset/FTYooAssetDefine.cs` 菜单 3/4（该文件引 ResServerConfig → 编辑器工具依赖热更集）。
- 首启释放 `PrefetchStreamingAssetsToPersistent`：`.baseline.stamp` 指纹一致→跳过；`.copy.inprogress` 残留→清空重建；**存在即跳过（保热更成果）**。
- dll 链路 md5 清单 `{平台}/HybridCLR/md5.txt`（菜单 HybridCLR/4）必须与 dll 同传；拿不到=放弃更新。下载器 .part 续传/重试 3/批超时 90s；BootLoader 探测 4s。⚠️ `GetPlatformFolder` 与 `GetPlatformFolderForProbe` 同步改。
- ★ YooAsset 3.0.x 默认值全关（无总超时/续传关/看门狗关/校验 Low）→ `BuildSandboxParameters()` 已显式开 High(CRC)/1MB/30s/并发8/每帧4；`CheckUpdateCo` 批超时 300s；重试=原生 `DownloadRetryController`（4xx 不重试）。事件 API = `DownloadProgressChanged` 等（非 2.x callback）。
- 本地测试 = Python `http.server` 指 `Bundles/<平台>/`。

## 多语言（阶段1~5）

- 代码全在 `Assets/Scripts/Localization/`（热更层；无需动 asmdef/dll 名单）。**主键 id = 英文原文**：`Localization.Get("Start")`。
- 表权威源 = `.workbuddy/tools/gen_localization_table.py` 的 `ROWS`（改它→跑脚本→菜单`3.导出配置表`）→ `Luban/Config/Datas/Localization.xlsx`。
- `Text/ImageLocalizer.key` public；留空自动取 key：Text 用序列化 `_originalText`（**绝不能用 `_text.text`**）；Image 用 `_originalSprite.name`→节点名。回退链：当前语言→英文→null（`?? 原文`）。
- ⚠️ 写 key 必须与表一致（写岔静默失效）；插值句整句入表 `Get(key,args)`；`\n` 须转义（CS1010）。
- SO=`Resources/Localization/LocalizationSettings.asset`；字体 en→LiberationSans、zh-Hans→SiYuanSongTi。
- 切语言 = `SetLanguage` + `LanguageChangedEvent`（**参数 int，`Action<int>`**）；存档存语言码；字体一律 `GetFont(Current)`；`EnsureSettings()` public 幂等。
- ⚠️ 不给资源层/下载器加多语言；状态字段存 key 不存译文。
- prefab 挂载：黑名单 `DynamicNames`+白名单 `ForceStaticNames`+跳过 `SpeedButton`+`IsSymbolOnly`；节点原文必须在表里，否则静默回退。

## 编辑器工具 / UI / 字体

- 多语言菜单 `308` 挂 TextLocalizer（17 prefab）/ `309` 清理误挂。
- UI 生成器 = `UIPrefabBuilder.cs`（改文案=改它+重编译+重生成）；`EditorUtil.Report`=`Ok/Warn/Skip/Error`（无 `Info`）。
- 统一 TMP；`SiYuanSongTi SDF` 必须**动态+多图集**（满后新字空白不报错）。
- ⚠️ 塔按钮锚点 (0.5,0.5)；`SpeedButton/StartButton` 在塔栏两侧；节点名 `Find("Panel/X")` 无映射 → 成对改 + `check_ui_contract.py`；新字形用 ASCII。

## 列表 / SuperScrollView

- `SelectView` 全屏横向画廊；条目 `Prefabs/UI/SelectLevelItem.prefab`（生成器产出，不必登记 ResTable）。
- 交互：居中才算选中；点非居中先滑正中；箭头只挪。⚠️ 吸附：条目宽须 ≡ 视口宽；邻卡可见=RectMask2D(1300)+Viewport(900) 同心；Viewport pivot.x=0，用 offsetMin/Max。
- ⚠️ 别用 `mOnSnapItemFinished` 判滑到位 → 每帧轮询中心距（4px，兜底 2.5s）。
- `InitListView` 只调一次；`onClick` 只在 `IsInitHandlerCalled` 首挂、读 `UserIntData1/2`；视觉层挂 `Body`；首次定位延到首帧 `LateUpdate`。

## 结算 / 生命周期 / 存档

- `LevelClearView` 胜败共用，`OnGameOver()` 打开（别监听 `LevelClearEvent`）；星级先读后写；下一关=大于本关的最小 id；F2=强制胜。
- 唯一拆卸 `TeardownLevel()` 顺序：操作态→战斗实体→场景残留→界面。`*Root` 场景常驻，往其下 new 的须自带清空并登记；HudView 须在其中 Close；`RecycleBullet` 绝不能补 `UnregisterBullet`；`TipsView` 不随切关关。
- 存档只走 `SaveManager`；禁直接 SQL、禁新增 `PlayerPrefs`（例外 KeyProvider）；见 `Docs/LocalPersistence_SQLite_Design.md`。Android 须自带 `libsqlite3.so`（targetSdk≥24 拒 dlopen；ARMv7 softfp）。改表三步：`SaveSchema.CreateStatements`→`CurrentVersion`+1→`RunMigrations`；密文 TEXT 不能参与 SQL 排序/聚合。

## 音频 / 倍速

- 音频在 `Assets/Audio/{SFX,BGM}/`；加音频=丢文件+`gen_audio_catalog.py`；常量 `Data/AudioName.cs`。BGM 固定 2 源+`AudioFadeDriver`；音量只由 `ApplyBgmVolume()` 写；`unscaledDeltaTime`；`UiClickSfx` 自动挂。
- 倍速唯一源 `Core/GameClock.cs`（帧号惰性缓存；timeScale 只允许 0/1）；改档走请求事件→四道校验→`GameSpeedChangedEvent`；CombatSystem 改一行覆盖怪/塔/弹。

## 工具 / 命名

- 地图编辑链路：棋盘→`levelmap_export.json`→LevelMap.xlsx→tblevelmap.json；还须进 `SceneInfo.xlsx`。
- 云端资料库镜像 `Docs/`：md 走 `space.importer.create-doc`（大文档 `--stdin`），svg 走 `drive/upload_drive_file.py`（网盘拒收 md）。
- 静态校验 9 个（`.workbuddy/tools/`）改完全跑；`check_arity._CHANGED` 不留已删文件；shell 跑 Python 别用 `\s\b\w`；`split_args`：`=>`/比较符 `>` 不当泛型闭合、泛型用独立 `gen` 计数、无花括号 lambda 止于顶层逗号。
- `TowerType`=Normal1/Aoe2/Slow3/Pierce4/Laser5；目录 Power=Aoe、Retard=Slow；换塔美术四层同步 resName→ResTable→预载→prefab+meta；Pierce/Laser 占位 `Tower_Normal0`。
