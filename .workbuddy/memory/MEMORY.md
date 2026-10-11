# FreedomTower 项目长期记忆

> 只记"踩坑就返工"的不变量；细节见 `Docs/` 与 `YYYY-MM-DD.md`。⚠️ 有注入上限，**新增前先想能不能删**。

## 铁律

- **游戏名 = 《自由人塔防》**，英文名 **FREEDOM TOWER**（工程 `productName: freedomtower`、包名 `com.lzyfreedomtower.freedomtower`，**不填中文名**）。
  ⚠️ 出现《坚守阵地》时**先判断指谁**：指**原版 Fieldrunners** 的引用保留不动；指本工程的才改。
- **品牌标识 6 种写法各有归属，别乱统一**：`自由人塔防`（文档/效果图）｜`FREEDOM TOWER`（游戏内副标题）｜`freedomtower`（productName/包名）｜`FreeTower`（**YooAsset 包裹名 = AB 输出目录名，改了热更失效**）｜`FTProject`（命名空间）｜`freetower_*`（**存档文件名**，英文名 → 中文改名不影响用户存档）。
- ⚠️ **工程由 `com.unity.template.3d@5.0.4` 克隆** → 残留 3D 模板默认值（已修 `Template3D`/`SampleScene`）。遇到"看起来不对的默认值"先查这个根因。
- ⚠️ **Unity 菜单是 `Tools/塔防/...`（~40 处 MenuItem）**："塔防"是**玩法类型**不是游戏名，**不要改**。
- ⚠️ **动手前必须确认 Unity MCP 可用**（用户长期要求）：MCP 挂了就**停下来让用户确认**，不要自作主张先做"不需要编辑器"的部分。
- ⚠️ 编辑器脚本**一律不弹 `EditorUtility.DisplayDialog`**（阻塞主线程 → MCP/CI 卡死）；结果全走 `Debug.Log/Warning/Error`。危险操作拆两档菜单（原菜单直接执行 + 「强制执行：…」带确认，仅人工用）。⚠️ 第三方 `DOTweenPro/Editor/DOTweenAnimationInspector.cs` 的 2 处弹窗**不动**。
- ⚠️ **写交付文档一律不写盘符路径**（用"本工程/工程根目录"）；脚本内路径从脚本自身位置推导。历史路径 `D:\FreedomTower`、`D:\FreedomTower_1` 均已失效，**不要再引用**。
- ⚠️ **`git worktree` 副本**（`workbuddy/main-*`）长期落后，工作区可能压着"看着像改动、实为 HEAD 过期"的**假改动** → 同步前**逐字节 diff**。权威永远是本工程根的 `main`；对齐用 `stash push -u` + `merge --ff-only`。
- ⚠️ **跑生成/挂载类菜单前必须确认 `isCompiling==false && isPlaying==false`**；**改完 `Assets/Editor/*.cs` 必须先 `refresh_unity(compile="request", scope="all")` 等编译完再跑菜单** → 否则 **Unity 静默用旧程序集产出旧结果**（最坑的返工点）。MCP `refresh_unity` schema = `{mode, scope, compile, wait_for_ready}`（**没有** `wait_for_compile`）。
- ⚠️ `screenshot` 偶发丢 Overlay 层（重截即可）；单次延迟数秒~十几秒，抓不到 1.2s 瞬态。⚠️ 改 `UIPrefabBuilder` 后比对 `ui_prefabs_preRebuild/*.prefab` 查回归。
- `git push`：远端 `Eagle-Lai/MyTowerGame.git`（**public** → `fetch`/`ls-remote` 不需凭证，**不能拿它验凭证**）。
  ★ **弹「Select a credential helper」根治**：根因 = PortableGit **系统级** `etc/gitconfig` 的 `credential.helper = helper-selector`。正解 = 用户级 `~/.gitconfig` 的 `[credential]` 段插一条空 `helper =`（清空 helper 列表，丢掉 system 那条），后面跟原 manager。⚠️ 勾 "Always use" 没用（要写系统级，`gitconfig.lock` 残留即失败）；0 字节锁可直接删。⚠️ **不要用 `GIT_CONFIG_SYSTEM=/dev/null`**（会丢 autocrlf/lfs filter → `could not read Username`）。直接 `git push origin main`，偶发失败**重试一次**，成功看 `main -> main` 行 + `git ls-remote --heads origin main` 核对 sha。
- Unity 2022.3.62f3c1，**Built-in RP**（霓虹只能烘进贴图）。

## 环境 / 配置 / 资源

- ★ **Unity 2022.3.62f3c1 装在 `C:\Program Files\Unity 2022.3.62f3c1\`**（带空格、非 Hub 标准目录，Hub `manual:true`）→ 找路径用 `Get-Process Unity`，**别假设** Hub 标准目录；手动注册故 Hub「Add modules」不可用。
- ★ **Android 工具链在 `D:\Android\`**：`jdk\temurin-11`｜`sdk`｜`ndk\23.1.7779620`(r23b)。Unity 侧写 **EditorPrefs 三键** `AndroidSdkRoot/AndroidNdkRoot/JdkPath`（**别用属性 setter，不落盘**）；验证用 `AndroidJavaRoot/AndroidSDKRoot/AndroidNDKRoot.Validate(dir).Success`。
  ⚠️ **cmdline-tools 版本必须 = `6`**（Unity 2022.3 LTS 基线）：装 12.0 时 `sdkmanager` 是 class 61(JDK17)，而 Unity 2022.3 只认证 **JDK 11** → 撞 `UnsupportedClassVersionError`，表现为 `Failed to update Android SDK package list.`（HybridCLR 最后两步挂它下面）。★ **别装 JDK 17 迁就**（Gradle 7.5 只认证 JDK 11，会变成更难查的静默失败）。诊断：`class file version 61.0`=JDK17、`55.0`=JDK11。
- **Luban** 改 `Luban/Config/Datas/*.xlsx` 必重导（菜单`3.导出配置表`，需 `DOTNET_ROLL_FORWARD=LatestMajor`）；新表先登记 `__tables__.xlsx`。
  ⚠️ **xlsx 格式**：第 1 列 A 是 tag 列（值 `##` 开头），**字段从 B 列起**；行1=`##`+字段名、行2=`##type`+类型、行3=`##`+说明、行4+ 数据。字段误放 A 列 → 主键取到数据值、报"主键重复"。
  ⚠️ **列名须是合法 C# 标识符**（用 `zhHans` 而非 `zh-Hans`）。
  ★ **Luban 导出会删除 `Assets/Gen/` 里它不认识的旧文件**（含手工放的 `FTProject.Gen.asmdef`+`.meta`）→ `LubanExporter.cs` 的 `KeepFilesInCodeDir` 备份/还原保护（**改 Editor 脚本后必须先重编译才生效**）。
- **`ResTable.cs` 唯一寻址源**。⚠️ `check_code.py` 只扫 `Get("字面量")` 不扫 `Configs.ConfigKeys` → 加表须手工同步。`ResLoader` 三套按宏切，**新依赖一律加宏**。
- ★ **YooAsset 初始化必须三步**：`InitializePackageAsync`（只建文件系统）→ `RequestPackageVersionAsync()` → `LoadPackageManifestAsync`（**最后才 `SetActiveManifest`**）。漏了症状极欺骗：日志正常，之后每次加载都报 `Active package manifest not found.`。收集器 `EnableAddressable=false`；同版本二次构建抛 `ErrorCode115`。
- 战斗无物理：`EnemyGrid` + `CombatSystem` 集中 tick。**塔无目标绝不开火**。

## 程序集 / HybridCLR（细节见 `Docs/HybridCLR_Integration.md`）

- **程序集 12 个**：AOT 层 = `FTProject.AOT`(+`ThirdParty.AOT`/`iTween`/`Editor`/**`HybridCLRGenerate`**)；**热更层 6 个** = **`Assembly-CSharp`**/`LubanLib`/`Gen`/`ThirdParty.SuperScrollView`/`ThirdParty.Reporter`/`Runtime`(主体)。
- ★ **`Assembly-CSharp` = Unity 默认兜底集**：任何**不在 asmdef 覆盖目录下**的脚本都会落进来（当前只有 `Assets/TestNull.cs`）。**已纳入热更**（Settings + 运行时名单两处）。
  ⚠️ **增删 `Assets/` 根目录的脚本 → `Assembly-CSharp.dll` 有无会变** → 必须重跑 `Generate ▸ All` + 拷贝，否则加载器报"缺少热更 dll"。
- ★ **`FTProject.HybridCLRGenerate` 是为 `AOTGenericReferences.cs` 单建的 AOT asmdef**：否则该文件掉进 `Assembly-CSharp`，一旦后者进热更，这个 AOT 清单就变成热更类型 → **违反铁律**。HybridCLR 生成器只写这一个文件、不删目录内其它文件 → asmdef 放同目录安全。
- ★ **铁律：AOT 主包不得引用热更类型**。`main` 场景与 UI prefab 挂的全是热更脚本 → 必须由**纯 AOT 的 `Boot.unity`** 先 `Assembly.Load` 再进 `main`。BuildSettings = Boot(0)→main(1)。⚠️ **反向引用允许**（热更集可引用 AOT 集，本工程 `Runtime`→`AOT` 为 `: IHotUpdateEntry`）；判违反只看 **AOT 侧是否零热更引用**。
- ★ **跨程序集入口契约 = 接口**：`FTProject.AOT.IHotUpdateEntry` ← `FTProject.HotUpdateEntry`。改名/改签名**编译期报错**；`HotUpdateEntryLocator` 是**唯一保留的反射点**。⚠️ 实现类必须能被无参构造 → `HotUpdateEntry` 是普通 class 非 static；"是否已启动"用静态 `Started`。
- ★ **`DOTween`/`DemiLib`/`LitJson` 是预编译 DLL → 物理上无法热更，只能 AOT**。且 DOTween/iTween 在本工程**零使用**。
- ★ **热更 dll 加载顺序（拓扑）**：`Assembly-CSharp → LubanLib → Gen → SuperScrollView/Reporter → Runtime`。名单两处**必须同步**：`HotUpdateAssembler.HotUpdateAssemblies` ↔ `ProjectSettings/HybridCLRSettings.asset`。⚠️ 编辑器下热更 dll 已在 AppDomain → `Assembly.Load` 前必须**跳过已加载**。
  ⚠️ `ProjectSettings/HybridCLRSettings.asset` 用 Unity API 改**不落盘**（`SaveAssets` 无效）→ 直接改 YAML 文本才生效。
- ⚠️ HybridCLR 包版本必须与 `HybridCLRData/.../libil2cpp-version.txt` 版本戳一致（当前 = **8.14.1**），否则 `Generate/All` 报 "must run Installer"。
- ⚠️ `Generate/All` 后两步需目标平台构建环境（Android → JDK/NDK）；link.xml 生成**不依赖平台**，产出 `Assets/HybridCLRGenerate/link.xml`。
- ⚠️ `Assets/StreamingAssets/HybridCLR/*.dll` 由 `Tools ▸ 塔防 ▸ HybridCLR ▸ 1` 拷贝（源 `HybridCLRData/HotUpdateDlls/<平台>/`）；运行时读取优先级 = `persistentDataPath/HybridCLR/` > `StreamingAssets/HybridCLR/` > `Library/ScriptAssemblies/`(仅编辑器)。
- ★ **AOT 补充元数据 `AOTMetaAssemblies` 共 6 项**：`System.Core`/`UnityEngine.AssetBundleModule`/`UnityEngine.CoreModule`/`UnityEngine.JSONSerializeModule`/`YooAsset`/`mscorlib`。
  **三处名单必须一致**：`AOTGenericReferences.cs` → `HotUpdateAssembler.AOTMetaAssemblies` → `HybridCLRDllCopier.AOTMetaAssemblies`。编辑器工具**不能引用 `FTProject.AOT`** → 两份常量只能手写；菜单会自动双向比对并告警。
- ★ **Boot→main 链路编辑器实测通过**（2026-10-11）：Play 后活动场景 = `main`，YooAsset/配置表/自检全绿 0 error。判据推荐看**活动场景是否变成 `main`**。
- ⚠️ **真机（Android）启动未验证**：APK 内 `StreamingAssets` 是压缩包，`File.Exists/ReadAllBytes` 读不到热更 dll → 必须 `UnityWebRequest` 读，或首启释放到 `persistentDataPath`。**打包前必须处理**（读取链已预留分支）。

## 热更 / 资源服务器

- ★ **热更产物两条独立链路**：①**dll** 走 AOT 侧独立 HTTP 下载（`HotUpdateDllDownloader`，**刻意不走 YooAsset** —— dll 在 Boot 加载，早于 YooAsset 存在，鸡生蛋）；②**AB** 走 YooAsset `HostPlayMode`。
- ★ `IRemoteService`（YooAsset **3.0.x**，**不是** 2.x 的 `IRemoteServices`）= 单方法 `IReadOnlyList<string> GetRemoteUrls(string fileName)`。⚠️ **`fileName` 已含平台/包裹/版本相对路径**（如 `Android/FreeTower/1.0.1/FreeTower.version`）→ 只拼根 URL，**别再前置平台名**（会 404）。
- ★ 服务器地址唯一源 = `Core/Res/ResServerConfig.cs`（**普通 static class，不是 ScriptableObject** —— 它是资源系统的**输入**，不能自己是资源）。支持 `persistentDataPath/server.txt` 运行时覆盖（跳过 `#` 与空行）。⚠️ **AOT 侧不能引用它** → `BootLoader.ServerUrlForAOT` 是**刻意的复制常量**，改地址要**两处同步**。
- ★ 模式三分支（`YooAssetResLoader.CreateInitOptions`）：`FT_HOTUPDATE` → `HostPlayModeOptions`（`BuiltinFileSystemParameters` + `CacheFileSystemParameters = CreateDefaultSandboxFileSystemParameters(remoteService)`）；否则离线。**未开宏 = 离线玩法**，安全默认。宏由 `Assets/Editor/YooAsset/FTYooAssetDefine.cs` 菜单 3/4 开关。⚠️ 该文件 `ReportStatus()` 引了 `ResServerConfig`（热更集）→ **编辑器工具依赖热更集，改前先确认**。
- ★ **首启预制释放**：`HotUpdateAssembler.PrefetchStreamingAssetsToPersistent` 把内置 dll 从 StreamingAssets 释放到 `persistentDataPath/HybridCLR/`。★ **2026-10-11 起为"基线拷贝"**：整目录指纹 `.baseline.stamp`（一致→整体跳过）+ 中断标记 `.copy.inprogress`（残留→清空重建）+ 磁盘空间检查；**存在即跳过（保热更成果）**。
- ★ **dll 链路有 md5 校验清单**：`{平台}/HybridCLR/md5.txt` 由菜单「HybridCLR/4」生成（`HybridCLRMd5Generator.cs`），**必须与 dll 一起上传**；客户端拿不到清单 = 放弃更新（不盲写）。`HotUpdateDllDownloader` 支持 .part 断点续传/重试 3 次/批次总超时 90s；`BootLoader` 先探测（4s）不可达即离线启动。⚠️ `GetPlatformFolder`（下载器）与 `GetPlatformFolderForProbe`（BootLoader）两份私有常量同步改。
- ★ **YooAsset 3.0.x 默认值坑（必须显式传参）**：文件下载 `timeout=0`（无总超时，批次上限要上层算）、续传 `ResumeDownloadMinimumSize=long.MaxValue`（默认关）、看门狗 `DownloadWatchdogTimeout=0`（默认关）、校验 `FileVerifyLevel.Low`（只验存在）。**已在 `YooAssetResLoader.BuildSandboxParameters()` 显式开启**：High(CRC)/1MB 续传/30s 看门狗/并发 8/每帧 4；`CheckUpdateCo` 加批次总超时 300s（超时 CancelDownload，已下部分保留）。
- ★ **YooAsset 3.0.x 下载链自带能力（实测源码 `Library/PackageCache/com.tuyoogame.yooasset@3b4cfb36cc`）**：
  - **断点续传原生支持**：`SandboxFileSystem.CreateResumeRequest` 用 `<文件>.tmp` 续传，`Range: bytes={offset}-`，但**默认关闭**（`ResumeDownloadMinimumSize = long.MaxValue`）；需 `AddParameter(EFileSystemParameter.DownloadResumeMinimumSize, <bytes>)` 才生效。
  - **重试策略原生支持**：`DownloadRetryController` + `DefaultDownloadRetryPolicy`（线性退避 1s→上限 10s；`httpCode==0`/408/416/429/5xx 可重试，4xx 不可）。次数 = `CreateResourceDownloader(concurrency, retryCount)` 的第二个参数。
  - **下载超时**：文件下载 `timeout = 0`（不设响应超时），只有 `DownloadWatchdogTimeout`（**默认 0 = 禁用**）；要总超时只能**上层自己算**。⚠️ 别指望 YooAsset 内部超时兜底。
  - **完整性校验**：`EFileVerifyLevel`（`Low`=仅存在 / `Middle`=大小 / `High`=CRC），沙箱默认 **`Low`** → 想校验 CRC 要显式 `AddParameter(EFileSystemParameter.FileVerifyLevel, EFileVerifyLevel.High)`。
  - 事件 API（**非** 2.x callback）：`DownloadProgressChanged`/`DownloadError`/`DownloadCompleted`/`DownloadFileStarted`。
- ⚠️ 本地测试服务器 = Python `http.server` 指向 `Bundles/<平台>/` 目录即可；**WinSCP 是远端上传客户端，与本机测试无关**。

## 多语言 / 本地化（阶段1~5）

- 代码全在 **热更层 `FTProject.Runtime`**：`Assets/Scripts/Localization/`（`Language`/`LocalizationSettings`/`LocalizationTable`/`LanguageManager`/`Localization`/`TextLocalizer`/`ImageLocalizer`）→ **无需改 asmdef / 动 dll 名单**。
- ★ **阶段5 起：表主键 `id` = 英文原文本身（id == en）** → **英文原文即查找键**：`Localization.Get("Start")`，不再是 `Get("hud.start")`。全工程 151 处已迁移。
- ★ **`TextLocalizer.key` / `ImageLocalizer.key` 是 public 字段**；留空时自动取 key：Text 用 **prefab 序列化原文 `_originalText`**（⚠️ 绝不能用 `_text.text`——刷新后已是译文，会层层套娃）；Image 用 **`_originalSprite.name` → 回退节点名**。
- ★ **取词回退链**：当前语言 → 英文 → `null`（调用方 `?? 原文` 兜底）。接口不抛异常。
- ★ **表的唯一权威源 = `.workbuddy/tools/gen_localization_table.py` 的 `ROWS`**（改表只改它 → 跑脚本 → 菜单「3. 导出配置表」）。表 `Luban/Config/Datas/Localization.xlsx`（列 B=`id`(=英文原文),C=`en`,D=`zhHans`,E=`zhHant`,F=`comment`）。当前 **165 行 / 0 重复 / id==en**。
- ★ **写 key 必须与表完全一致**：写岔不崩（走 `?? 原文`）但**多语言静默失效**。改完做 key 差集比对。
- ★ **插值句整句入表**用 `Get(key, args)`，绝不拼半句；**富文本模板与 `{0:F1}`/`{0:0.#}` 格式符原样留在表串里**。⚠️ 批量替换脚本把含 `\n` 的串写成真实换行 → CS1010，须转义成字面量 `\n`。
- ★ SO 放 **`Resources/Localization/LocalizationSettings.asset`**（引导期最早可读，避开 YooAsset「鸡生蛋」）；`defaultLanguage=English`、`fonts` 每语言一套 FontAsset（en→`LiberationSans SDF`、zh-Hans→`SiYuanSongTi SDF`、zh-Hant 待定）。
- ★ 切语言：`LanguageManager.SetLanguage(lang)` 写存档 + `EventDispatcher.TriggerEvent<int>(EventName.LanguageChangedEvent,(int)lang)`；组件订阅该事件刷新。存档存**语言码字符串**（`LanguageUtil.ToCode/FromCode`），避免枚举扩容漂移。⚠️ **`LanguageChangedEvent` 参数是 int（枚举值）**，订阅用 `Action<int>`。
- ⚠️ **`LanguageManager.EnsureSettings()` 是 public**（幂等）；`LevelLoadingMask`/`FloatingTextManager` 靠它取语言字体，**字体一律 `GetFont(Current)`，别硬编码中文 SDF**。
- ⚠️ **不给"资源层/下载器"加多语言**：`HotUpdateView.IsIndeterminatePhase` 靠 `phase.Contains("检查"/"比对"/"校验")` 判进度态 → 阶段文案改为**展示层「原文→key」映射**，下载器保持原样。
- ⚠️ **状态字段存 key 不存译文**（如 `TowerPlacement._blockReason`）：存译文会在切语言后残留旧值。
- ⚠️ **prefab 静态文本挂载**：黑名单 `DynamicNames`（运行时覆盖文本如 `GoldText`/`PriceText`/`WarnText`）+ 强制白名单 `ForceStaticNames` + 跳过父节点 `SpeedButton` + `IsSymbolOnly`（无 `char.IsLetter` 的纯符号如 `<` `>` `☆`）。⚠️ 挂载节点的原文**必须在表里有一条**，否则静默回退。
- ⚠️ 阶段5 遗留：`ImageLocalizer` 的 key→资源名 路径**尚无 prefab 实际使用**（都走 enSprite/zhHans/zhHant 直填），也**没有"图片多语言"表数据**。

## 编辑器工具（`Assets/Editor/`）

- ★ 多语言菜单（`Tools/塔防/高级（单步重建）/`）：**308 = 批量挂多语言组件（TextLocalizer）**（遍历 17 个 prefab，幂等）；**309 = 清理误挂的多语言组件**。脚本 `LocalizationPrefabBinder.cs` / `LocalizationPrefabCleaner.cs`。
- ★ **UI 预制体生成器 = `UIPrefabBuilder.cs`**（菜单「生成 UI 预制体（全量重建）」）→ 静态文案字面量就在里面；改文案 = 改它 + 重编译 + 重生成。
- ⚠️ `Assets/Editor/EditorUtil.cs` 的 `Report` API = `Ok/Warn/Skip/Error`，**没有 `Info`**。

## UI / 字体

- **统一 TMP，禁新增 UGUI Text**。⚠️ `SiYuanSongTi SDF.asset` **必须"动态+多图集"**：单图集只装 ~119 字，关掉后新字（★☆×难度…）**渲染成空白且不报错**；判据 `TryAddCharacters("难★")`==false 即满。
- ⚠️ **塔按钮锚点必须 (0.5,0.5)**（`spec.Pos` 以画布中心为原点），写左下锚点 → 整排塔按钮出屏、无法建塔。
- ⚠️ `SpeedButton/StartButton` 在塔栏**两侧**（SideBtnX=786,SideBtnY=77）；效果图的"底中"会挡住第 3/4 颗塔按钮。
- ⚠️ **节点名契约**：View 的 `Find("Panel/X")` 与生成器无映射层，写岔只静默打「缺少节点」→ 成对改 + `check_ui_contract.py`。
- 箭头等新字形用 ASCII（`<` `>`）：中文 SDF 缺字形只渲染空白不报错。

## 列表 / SuperScrollView

- `SelectView` = **整页全屏**横向画廊（Panel 铺满 1920×1080），条目资产 `Assets/Prefabs/UI/SelectLevelItem.prefab`（生成器产出，**不必登记 ResTable**，靠引用进包）。
- 交互约定：**居中的那一关才算"选中"**，点居中卡→同帧进关；点非居中卡→先动画滑到正中再进关；左右箭头只挪不进关；未解锁只提示。
- ⚠️ **横向吸附几何**：条目能居中程度 = (视口宽−条目宽)/2，且需 **步长 ≥ 视口宽** → 条目宽必须 ≡ 视口宽，否则首/末条永远偏心。
- ⚠️ 要"邻卡可见"就得**视口比可视区窄**：`RectMask2D` 放 List（1300），Viewport 收窄 900 且与之同心。
- ⚠️ **Viewport pivot.x 必须预置 0**（`AdjustPivot` 会强改），矩形一律用 `offsetMin/offsetMax` 描述。
- ⚠️ **别用 `mOnSnapItemFinished` 判断"滑到位"**（其 `mCurSnapNearestItemIndex` 只在容器移动帧才重算，会提前触发）→ 改为**每帧轮询目标条目到视口中心的距离**；阈值 4px，兜底 2.5s。
- ⚠️ `InitListView` 只可调一次（`_listInited` 守）；条目池化复用 → `onClick` **只在 `IsInitHandlerCalled` 首次挂**，回调读 `UserIntData1/2`。
- 视觉层（缩放/淡化）挂卡片的 `Body` 子节点，**不能缩条目根节点**（pivot 固定 (0,0.5)）。首次定位延后到第一帧 `LateUpdate`。

## 结算 / 生命周期 / 存档

- `LevelClearView` 胜败共用（`LevelClearInfo.victory`），在 `OnGameOver()` 打开（别监听 `LevelClearEvent`）。⚠️ **星级先读后写**（RecordClear 只升不降）。下一关=**大于本关的最小 id**。F2=强制获胜。
- **唯一拆卸 `TeardownLevel()`** 四段：①操作态→②战斗实体→③场景残留→④界面；①在②前。
- ⚠️ `BoardRoot/PathRoot/TowerRoot/EnemyRoot/BulletRoot` 场景常驻，往其下 new 的模块**必须自带清空并登记**。⚠️ HudView 必须在 TeardownLevel Close。⚠️ **`RecycleBullet` 绝不能补 `UnregisterBullet`**。`TipsView` 不随切关关闭。
- 存档：只走 `SaveManager`；**禁**直接 SQL/`IDatabase`、**禁**新增 `PlayerPrefs`（例外 KeyProvider）。见 `Docs/LocalPersistence_SQLite_Design.md`。**Android 必须自带 `libsqlite3.so`**（系统的是平台私有库，targetSdk≥24 拒 dlopen），ARMv7 必须 softfp。**改表三步**：`SaveSchema.CreateStatements` → `CurrentVersion`+1 → `RunMigrations` 补 ALTER；**密文 TEXT 不能参与 SQL 排序/聚合**。

## 音频 / 倍速

- 音频 18 个在 `Assets/Audio/{SFX,BGM}/`。**加音频 = 丢文件 + 跑 `gen_audio_catalog.py`**；常量在 `Data/AudioName.cs`。
- BGM 用**固定 2 源 + `AudioFadeDriver`**（长音进音效池会被"顶掉最旧"误杀）。⚠️ **音量只由 `ApplyBgmVolume()` 写** = 基准×淡化系数×主音量×(静音?0:1)，驱动只改系数；用 `unscaledDeltaTime`。
- `UiClickSfx` 由 `UIManager.Open` 自动挂、每 0.4s 重扫 Button → 新界面不用写点击音。
- **倍速唯一源 `Core/GameClock.cs`**：`DeltaTime=dT×Speed` 按帧号惰性缓存（与执行顺序无关）；`timeScale` 只允许 0/1。改档走请求事件→GameFlowManager 四道校验→`GameSpeedChangedEvent`；`ResetGameSpeed()` 在 InitLevel/OnGameOver/QuitToSelect。**CombatSystem 改一行即覆盖怪/塔/弹**。

## 工具 / 命名

- 地图编辑器唯一通路：棋盘→`levelmap_export.json`→LevelMap.xlsx→tblevelmap.json；⚠️ 只加棋盘不加 `SceneInfo.xlsx` 进不去。
- **云端资料库**已镜像 `Docs/`：文件夹「自由人塔防 · 项目文档」＝在线文档 + 子夹「UI 效果图」(22 张 SVG)，再同步就往这里放。⚠️ **两条链路别混**：`.md` 走 `space.importer.create-doc`（大文档必须 `--stdin` 传 JSON）；`.svg` 走 `drive/upload_drive_file.py`（**网盘接口拒收 md**）。
- 静态校验 9 个（`.workbuddy/tools/`）改动后全跑；⚠️ `check_arity` 的 `_CHANGED` 不许留已删文件；⚠️ shell 跑 Python 别用 `\s`/`\b`/`\w`。**沙箱内不能编译**。
  ⚠️ `check_arity.split_args` 的坑：`=>` 的 `>` **不可**当泛型闭合（会把 depth 推负）；`total > 0` 的比较符同理；泛型 `<`/`>` 用**独立 `gen` 计数器**，且**无花括号 lambda 止于顶层逗号**。
- `TowerType` Normal1/Aoe2/Slow3/Pierce4/Laser5；目录里 **Power**=Aoe、**Retard**=Slow。换塔美术要**四层同步** resName→ResTable→代码预载→prefab+meta；Pierce/Laser 占位 `Tower_Normal0`。
