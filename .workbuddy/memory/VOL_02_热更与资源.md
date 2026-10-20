# VOL_02 程序集 / HybridCLR / 热更 / 资源

> 本分册由 `MEMORY.md` 拆分而来，**原文一字未删**。覆盖：12 个程序集与热更清单、dll/AB 两条链路、UDP 发现与闸门、一键热更菜单 10、部署铁律、配置加载失败自恢复。

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

## 热更部署铁律（2026-10-19，原属"出包铁律"一节）
- ★热更部署铁律（2026-10-19）：AB 构建（菜单9）后**必须立刻跑** `deploy_free_tower_cdn.py`，否则服务器根
  `FreeTower.version` 指针停留在旧版本 → 客户端拿旧清单，新增资源（如 tblevelrating）报"清单找不到定位地址"。
  验证：`curl --noproxy "*" http://127.0.0.1:8000/FreeTower.version` 应等于本地 Bundles 最新版本目录。
  另：`Bundles/Android/FreeTower/{1.0.25,1.0.26}/`（历史版本区）与服务器根平铺区是两回事，前者不被运行时请求。

## 配置加载失败自恢复（2026-10-19 新增）[公司E]
- ★`Configs.LoadAsync` 早退条件 = `IsLoaded && FailedTables.Count == 0`（失败后允许重载；旧版失败也置 IsLoaded=true 会"假成功"短路）。
- ★配置加载失败 → `Launcher.HandleConfigLoadFailed()`：3s 后 `BeginHotUpdate(forceRecheck:true)` 重查版本自动自愈，最多 3 次；forceRecheck 用于绕过 Gate 快捷分支。
- "崩溃+卡死"取证套路：crash 缓冲 / dropbox / tombstone 全空 + events 只有 am_kill(stop by relaunch) = 版本错位困住玩家，不是真崩溃；查 `am_kill` 时间线 + 配置加载日志即可定位。
- 一键热更可 `execute_code` 直调 `FTProject.EditorTools.HotUpdatePipeline.StartFull()`（53s 增量）；查状态用逐属性拼接（CodeDom 不认 var+链式）。
- MuMu 横屏 `input tap` 坐标系 = 旋转后 1600x900，非截图像素。
