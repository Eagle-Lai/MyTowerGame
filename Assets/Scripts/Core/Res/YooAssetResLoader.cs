#if USE_YOOASSET
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;
using UnityEngine.SceneManagement;
using YooAsset;

namespace FTProject
{
    /// <summary>
    /// YooAsset 版资源加载实现（P0-4）。
    ///
    /// 用法：在 Player Settings → Other Settings → Scripting Define Symbols 里加上
    /// <c>USE_YOOASSET</c>，ResLoader.Instance 就会切到本实现；去掉宏即完全回到原链路。
    ///
    /// 【为什么用编译宏而不是直接换掉 BundleResLoader】
    ///   YooAsset 是"按包解析"的 UPM 依赖，网络/代理不通时包拉不下来，一旦直接引用
    ///   它的命名空间就是**整个工程编译不过**。加宏之后：
    ///     没有宏 → 本文件编译为空，工程照常构建（YooAsset 只是没启用）
    ///     加上宏 → 才真正依赖 YooAsset
    ///   这与工程里既有的 FORCE_AB 是同一套思路（见 ResLoader.cs）。
    ///
    /// 【职责边界】业务代码仍然只认 <see cref="IResLoader"/> 的逻辑名，不感知 YooAsset。
    ///   本类把「逻辑名 → ResTable 地址 → YooAsset 定位地址」这一层翻译掉，
    ///   所以换用 YooAsset 不需要改任何业务代码与配置表。
    /// </summary>
    public class YooAssetResLoader : IResLoader, IHotUpdateLoader
    {
        /// <summary>YooAsset 资源包裹名（对应 Bundle Collector 里创建的包裹）</summary>
        public const string PackageName = "FreeTower";

        /// <summary>异步加载失败时回调此事件（与 BundleResLoader 对齐，供 UI 提示）</summary>
        public static event Action<string> OnLoadError;

        /// <summary>逻辑名 → 已持有的资源句柄。**句柄活着 = 资源不被回收**，这是本类的核心不变式。</summary>
        private readonly Dictionary<string, AssetHandle> _handles = new Dictionary<string, AssetHandle>(128);

        /// <summary>逻辑名 → 解析出的 YooAsset 定位地址（避免每次都去探测）</summary>
        private readonly Dictionary<string, string> _locations = new Dictionary<string, string>(256);

        /// <summary>ResTable 的"包名" → 关卡引用计数。只有 Preload 会 +1，ReleaseBundle 会 -1。</summary>
        private readonly Dictionary<string, int> _refCount = new Dictionary<string, int>(32);

        private ResourcePackage _package;
        private bool _ready;

        /// <summary>
        /// 初始化期间的进度回调（UI 补全 A2）。协程里多个出口都要结束，
        /// 用字段而不是层层传参：否则每个 `FinishInit` 调用点都得改签名，漏一个就"进度卡在 40%"。
        /// </summary>
        private Action<float> _initProgress;

        /// <summary>热更新下载器的暂停/续传入口（UI 补全 A3）。null = 当前没有进行中的下载。</summary>
        private ResourceDownloaderOperation _downloader;

        /// <summary>包裹初始化 / 版本请求 / 清单加载的等待上限（秒）。
        /// 超时明确报错，而不是让它静默挂死 —— 挂死的表现是"启动卡住且看不到原因"。</summary>
        private const float WaitTimeoutSeconds = 30f;

        public bool IsReady { get { return _ready; } }

        /// <summary>当前 YooAsset 包裹（后续做资源更新/下载时从这里拿）</summary>
        public ResourcePackage CurrentPackage { get { return _package; } }

        /// <summary>加载前的公共准备结果（同步/异步两条路径共用）</summary>
        private sealed class ResolveResult
        {
            /// <summary>是否通过校验、可以继续加载</summary>
            public bool Ok;
            /// <summary>是否直接命中已持有的句柄（此时 Handle 有效、Location 为空）</summary>
            public bool FromCache;
            /// <summary>命中的句柄</summary>
            public AssetHandle Handle;
            /// <summary>需要加载时的定位地址</summary>
            public string Location;
        }

        // ==================================================================
        // 初始化
        // ==================================================================

        public void Init(Action onDone)
        {
            Init(null, onDone);
        }

        public void Init(Action<float> onProgress, Action onDone)
        {
            if (_ready)
            {
                if (onProgress != null) onProgress(1f);
                if (onDone != null)
                {
                    onDone();
                }
                return;
            }

            _initProgress = onProgress;
            if (onProgress != null) onProgress(0f);

            if (Application.isPlaying)
            {
                ResLoaderRunner.Start(InitCo(onDone));
                return;
            }

            // 非运行态（编辑器工具脚本）：协程不会推进，退化为同步初始化。
            // 这与 ResLoaderRunner.NextFrame 在非运行态"立即执行"的既定约定一致 ——
            // 否则编辑器工具调用 Init 会永远等不到回调。
            InitBlocking();
            if (onDone != null)
            {
                onDone();
            }
        }

        /// <summary>初始化进度回报（三处阶段边界 + 收尾）。回调为空时零开销。</summary>
        private void ReportInitProgress(float value)
        {
            if (_initProgress != null)
            {
                _initProgress(value);
            }
        }

        private IEnumerator InitCo(Action onDone)
        {
            StartPackage();
            if (_package == null)
            {
                FinishInit(onDone);
                yield break;
            }

            string startError;

            // ------------------------------------------------------------------
            // ① 初始化包裹（到这里为止只保证"文件系统就绪"，清单还没加载）。
            // ⚠️ 3.0.x 的 InitializePackageAsync **不加载清单** —— 见下面 ② ③。
            // ⚠️ 它在"包裹已初始化过"时会直接抛 InvalidOperationException
            //    （ResourcePackage.InitializePackageAsync 有重复初始化检测）。
            //    编辑器向导的探针在同一次编辑器会话里可以被反复点，所以先看状态：
            //    已经成功过的直接复用，绝不重复调用。
            // ------------------------------------------------------------------
            string initError = string.Empty;
            EOperationStatus initStatus = _package.InitializeStatus;

            if (initStatus == EOperationStatus.Processing)
            {
                Fail(string.Format(
                    "[Res] YooAsset 包裹「{0}」正在初始化中，无法重复初始化。\n" +
                    "  若这是编辑器向导的探针，请等上一次跑完再点。",
                    PackageName));
                FinishInit(onDone);
                yield break;
            }

            if (initStatus != EOperationStatus.Succeeded)
            {
                InitializePackageOperation initOp = StartInitialize(out initError);
                if (initOp == null)
                {
                    Fail(string.Format("[Res] YooAsset 包裹「{0}」初始化无法启动：{1}", PackageName, initError));
                    FinishInit(onDone);
                    yield break;
                }

                yield return WaitOpCo(initOp, "初始化包裹");
                initStatus = initOp.Status;
                initError = initOp.Error;
            }

            if (initStatus != EOperationStatus.Succeeded)
            {
                Fail(string.Format(
                    "[Res] YooAsset 包裹「{0}」初始化失败：{1}\n" +
                    "  排查：①是否已在 YooAsset ▸ Bundle Collector 里创建同名包裹并配置收集目录\n" +
                    "        ②编辑器模拟模式需要先执行一次「构建模拟清单」\n" +
                    "        ③真机/离线模式需要先构建过资源包",
                    PackageName, initError));
                FinishInit(onDone);
                yield break;
            }

            // ① 包裹初始化完成 = 40%（A2 进度条）：后面还有"请求版本 / 加载清单"两段
            ReportInitProgress(0.4f);

            // ------------------------------------------------------------------
            // ② 请求包裹版本。版本是"加载清单"的必需入参。
            // ------------------------------------------------------------------
            RequestPackageVersionOperation versionOp = StartRequestVersion(out startError);
            if (versionOp == null)
            {
                Fail(string.Format("[Res] YooAsset 请求包裹版本无法启动：{0}", startError));
                FinishInit(onDone);
                yield break;
            }

            yield return WaitOpCo(versionOp, "请求包裹版本");

            if (versionOp.Status != EOperationStatus.Succeeded)
            {
                Fail(string.Format(
                    "[Res] YooAsset 包裹「{0}」请求版本失败：{1}\n" +
                    "  排查：编辑器模拟模式下版本来自模拟清单目录里的 <包裹名>.version 文件，\n" +
                    "        该文件由「构建模拟清单」产出 —— 先跑一次向导的第 ③ 步。",
                    PackageName, versionOp.Error));
                FinishInit(onDone);
                yield break;
            }

            string version = versionOp.PackageVersion;

            // ② 版本就绪 = 70%
            ReportInitProgress(0.7f);

            // ------------------------------------------------------------------
            // ③ 按版本加载清单 —— **这一步才会真正 SetActiveManifest**。
            //    少了它，前面两步都会"成功"，但之后任何加载都报
            //    "Active package manifest not found."。
            // ------------------------------------------------------------------
            LoadPackageManifestOperation manifestOp = StartLoadManifest(version, out startError);
            if (manifestOp == null)
            {
                Fail(string.Format("[Res] YooAsset 加载包裹清单无法启动：{0}", startError));
                FinishInit(onDone);
                yield break;
            }

            yield return WaitOpCo(manifestOp, "加载包裹清单");

            if (manifestOp.Status != EOperationStatus.Succeeded)
            {
                Fail(string.Format(
                    "[Res] YooAsset 包裹「{0}」加载清单失败（版本 {1}）：{2}",
                    PackageName, version, manifestOp.Error));
                FinishInit(onDone);
                yield break;
            }

            _ready = true;
            LogReady();
            FinishInit(onDone);
        }

        private void FinishInit(Action onDone)
        {
            // 无论成功还是失败都推到 100% —— 失败时 Launcher 会立刻中止并用错误文案覆盖进度条，
            // 若进度条停在半路，"卡住"和"失败"在界面上分不出来。
            ReportInitProgress(1f);
            _initProgress = null;
            if (onDone != null)
            {
                onDone();
            }
        }

        /// <summary>
        /// 等待一个 YooAsset 异步操作推进一步。返回 true = 还需要下一帧再看。
        ///
        /// 【为什么要这个函数】同一条 InitCo 要同时服务两种情况：
        ///   运行态     —— 由 YooAssetsDriver.Update 每帧驱动调度器，这里只需让出帧；
        ///   非运行态   —— 编辑器工具脚本下没有 Update，必须用 WaitForCompletion 当场推到底。
        /// 之所以不让两条路径各写一份初始化流程：本次踩的坑正是"两份实现只改了一份"
        /// （异步路径补了「请求版本 / 加载清单」，同步路径没补），结果编辑器工具里探针
        /// 一切正常，进了 Play 就整片报 manifest not found。
        /// </summary>
        private static bool WaitStep(AsyncOperationBase op)
        {
            if (op.IsDone)
            {
                return false;
            }
            if (Application.isPlaying)
            {
                return true;
            }
            op.WaitForCompletion();
            return false;
        }

        /// <summary>
        /// 等待一个 YooAsset 异步操作完成（含超时保护）。初始化三个阶段共用它。
        ///
        /// 【为什么要超时】这些操作由 YooAssetsDriver.Update 每帧驱动调度器。万一驱动器不在场
        /// （例如先在编辑器向导里跑过探针、再进 Play，此时 YooAssets 的静态状态并不干净），
        /// 操作会永远不完成 —— 不设上限就是"启动卡死且看不到原因"。
        /// 宁可超时报错，也不要静默挂死。
        /// </summary>
        private IEnumerator WaitOpCo(AsyncOperationBase op, string stage)
        {
            float deadline = Time.realtimeSinceStartup + WaitTimeoutSeconds;
            while (WaitStep(op))
            {
                if (Time.realtimeSinceStartup > deadline)
                {
                    Fail(string.Format(
                        "[Res] YooAsset 阶段「{0}」超时（{1} 秒）未完成，已放弃。\n" +
                        "  常见原因：YooAssetsDriver 没有被驱动（例如先跑过编辑器向导的探针、再进 Play）。\n" +
                        "  处理：退出 Play 再重新进入，让 YooAssets 重建驱动器后重试。",
                        stage, WaitTimeoutSeconds));
                    yield break;
                }
                yield return null;
            }
        }

        /// <summary>
        /// 请求包裹版本。**必须包 try/catch**，理由同 StartInitialize。
        ///
        /// 【为什么 3.0.x 必须单独走这一步】InitializePackageAsync 只初始化文件系统；
        /// 而 LoadPackageManifestAsync 必须带一个非空版本号（空会直接
        /// SetError("Package version is null or empty.")）。
        /// 编辑器模拟模式下版本取自模拟清单目录里的 <包裹名>.version 文件。
        /// </summary>
        private RequestPackageVersionOperation StartRequestVersion(out string error)
        {
            error = string.Empty;
            try
            {
                return _package.RequestPackageVersionAsync();
            }
            catch (Exception ex)
            {
                error = ex.Message;
                return null;
            }
        }

        /// <summary>
        /// 按版本加载清单。这一步内部会 SetActiveManifest，只有它成功之后，
        /// 后续的 LoadAssetSync / LoadAssetAsync 才不会再抛
        /// "Active package manifest not found."。**必须包 try/catch**，理由同 StartInitialize。
        /// </summary>
        private LoadPackageManifestOperation StartLoadManifest(string packageVersion, out string error)
        {
            error = string.Empty;
            try
            {
                // 超时沿用官方 Sample 的 60 秒；编辑器模拟模式读的是本地文件，实际不会等满。
                return _package.LoadPackageManifestAsync(
                    new LoadPackageManifestOptions(packageVersion, 60));
            }
            catch (Exception ex)
            {
                error = ex.Message;
                return null;
            }
        }

        /// <summary>
        /// 同步初始化（编辑器工具用）。这里刻意**只是把 InitCo 泵一遍**，
        /// 而不是另写一份初始化流程 —— 两份实现必然只改一份，本次踩的坑正是这个：
        /// 异步路径补了「请求版本 / 加载清单」，同步路径没补。
        ///
        /// 非运行态下 WaitStep 一律走 WaitForCompletion 当场推到底、不会 yield，
        /// 所以栈上每个等待协程都是"一次 MoveNext 就结束"。真出现等帧就说明
        /// WaitStep 的约定被破坏了（例如有人删掉 Application.isPlaying 判断），
        /// 那种情况下继续泵会死循环，所以明确报错中止。
        /// </summary>
        private void InitBlocking()
        {
            Stack<IEnumerator> stack = new Stack<IEnumerator>(4);
            stack.Push(InitCo(null));

            while (stack.Count > 0)
            {
                IEnumerator top = stack.Peek();
                if (top.MoveNext() == false)
                {
                    stack.Pop();
                    continue;
                }

                // 嵌套的等待协程（WaitOpCo）要压栈继续展开；`yield return null`
                // 在非运行态属于"不该发生"，落到下面那条分支。
                IEnumerator nested = top.Current as IEnumerator;
                if (nested != null)
                {
                    stack.Push(nested);
                    continue;
                }

                Fail("[Res] YooAsset 同步初始化出现等待帧，已中止（InitBlocking 只适用于非运行态）。");
                return;
            }
        }

        /// <summary>
        /// 启动包裹初始化。**必须包 try/catch**：YooAsset 在这些入口是"抛异常"而不是
        /// "返回失败句柄"（例如包裹已在初始化中、参数非法）。若不接住，异常会沿着
        /// Launcher 的启动回调链一路抛出去，直接中断整个启动流程且看不到原因。
        /// </summary>
        private InitializePackageOperation StartInitialize(out string error)
        {
            error = string.Empty;
            try
            {
                return _package.InitializePackageAsync(CreateInitOptions());
            }
            catch (Exception ex)
            {
                error = ex.Message;
                return null;
            }
        }

        // ------------------------------------------------------------------
        // 下面三个 "Try" 包装的共同理由：YooAsset 的加载入口在异常路径上是**抛异常**
        // （包裹未就绪、参数非法等），而不是返回一个失败的句柄。业务侧（Launcher 的
        // 启动回调、GameFlowManager 的建关流程）都没有 try/catch，一旦抛出去就是
        // "启动卡死且看不到原因"。统一在这里兜住，转成"返回 null + 明确日志"。
        // ------------------------------------------------------------------

        private AssetHandle TryLoadSync(string location, System.Type type, out string error)
        {
            error = string.Empty;
            try
            {
                return _package.LoadAssetSync(location, type);
            }
            catch (Exception ex)
            {
                error = ex.Message;
                return null;
            }
        }

        private AssetHandle TryLoadAsync(string location, System.Type type, out string error)
        {
            error = string.Empty;
            try
            {
                return _package.LoadAssetAsync(location, type);
            }
            catch (Exception ex)
            {
                error = ex.Message;
                return null;
            }
        }

        /// <summary>探测地址是否在清单里。探测本身失败时按"不匹配"处理，由 ResolveLocation 汇总告警。</summary>
        private bool IsLocationValidSafe(string location)
        {
            try
            {
                return _package.IsLocationValid(location);
            }
            catch (Exception)
            {
                return false;
            }
        }

        /// <summary>
        /// YooAssets 全局初始化 + 创建包裹。这两步都是同步的，只有"包裹初始化"才是异步。
        /// </summary>
        private void StartPackage()
        {
            try
            {
                if (YooAssets.IsInitialized == false)
                {
                    YooAssets.Initialize();
                }

                if (YooAssets.TryGetPackage(PackageName, out _package) == false)
                {
                    _package = YooAssets.CreatePackage(PackageName);
                }
            }
            catch (Exception ex)
            {
                _package = null;
                Fail(string.Format("[Res] YooAssets 全局初始化失败：{0}", ex));
            }
        }

        /// <summary>
        /// 按运行环境选择初始化参数。三种模式：
        ///   ① 编辑器模拟模式：编辑器 且 未定义 FORCE_AB（改完资源即可运行，无需构建）
        ///   ② 联机运行模式  ：定义了 FT_HOTUPDATE 且 ResServerConfig.EnableHotUpdate
        ///                      → 启动时去远端比对版本、下载差异（**这就是热更新**）
        ///   ③ 离线模式      ：其余情况，只读随包内置资源
        ///
        /// 【为什么热更单独给一个 FT_HOTUPDATE 宏，而不是复用 FORCE_AB】
        ///   FORCE_AB 的语义是"在编辑器里也走真资源包"，用来验证 AB 链路本身；
        ///   而热更关心的是"去哪里下载"。两者正交：
        ///     · 只有 FORCE_AB       → 编辑器里验证"能读包"，但读的是随包资源（离线）
        ///     · 只有 FT_HOTUPDATE   → 真机上走远端下载
        ///   用一个宏表达两件事，迟早会互相干扰（例如想单独验证离线包却被迫连服务器）。
        ///
        /// ⚠️ 本方法在**每次 Init 时**执行。HostPlayMode 下不会重新下载已经是最新的文件，
        ///    YooAsset 会先比版本、再按清单里的哈希判断哪些 bundle 本地已有 —— 所以
        ///    "每次启动都走一遍"是可接受的开销，不会重复下载。
        /// </summary>
        private static InitializePackageOptions CreateInitOptions()
        {
#if UNITY_EDITOR && !FORCE_AB
            // ⚠️ 编辑器模拟模式**必须先有模拟清单**，且清单所在目录要显式传给文件系统：
            //   EditorFileSystem.OnCreate 在 packageRoot 为空时会直接抛
            //   "package root is null or empty"。而模拟清单的内容必须与当前资源一致，
            //   所以这里按官方 Sample 的做法**当场构建一次**（增量、有依赖缓存，很快），
            //   再把它的输出目录交给文件系统。
            //   EditorSimulateBuildInvoker 在运行时程序集里、内部用反射转发到
            //   YooAsset.Editor，因此运行时脚本可以安全引用它（无需引用编辑器程序集）。
            PackageBuildResult simulate = EditorSimulateBuildInvoker.Build(
                PackageName, (int)EBundleType.VirtualAssetBundle);

            EditorSimulateModeOptions options = new EditorSimulateModeOptions();
            options.EditorFileSystemParameters =
                FileSystemParameters.CreateDefaultEditorFileSystemParameters(simulate.PackageRootDirectory);
            return options;
#elif FT_HOTUPDATE
            // ---- 联机运行模式（热更新的核心）------------------------------------
            // 两个文件系统缺一不可：
            //   BuiltinFileSystem —— 随包的"首包资源"，新装的玩家没网时至少能起来
            //   SandboxFileSystem —— persistentDataPath 下的可写缓存，下载的新资源落在这里
            // YooAsset 会优先用沙盒（新版本），没有才回落到内置（首包版本）。
            string serverUrl = ResServerConfig.GetServerUrl();

            // 【2026-10-15 修复】总闸门：服务器可达性由启动链在 1 秒内探测（见 BootLoader）。
            // 不可达时**绝不进入联机模式** —— 否则版本请求会对不可达地址空等
            // （默认 60s 超时且硬失败），真机表现为"启动一直等待、最终进不去游戏"。
            // （hotEnabled 落局部是为了避开 const 比较的 CS0162，语义不变）
            bool hotEnabled = ResServerConfig.EnableHotUpdate;
            bool bootReachable = FTProject.AOT.BootServerSelection.RemoteHotUpdateAllowed;
            if (hotEnabled == false
                || ResServerConfig.IsValidServerUrl(serverUrl) == false
                || bootReachable == false)
            {
                // 【降级而不是报错】退回离线模式，至少让游戏能进得去 ——
                // 玩家玩到的是随包版本，而不是黑屏或无限等待。
                string reason;
                if (hotEnabled == false)
                {
                    reason = "EnableHotUpdate 总开关为 false";
                }
                else if (ResServerConfig.IsValidServerUrl(serverUrl) == false)
                {
                    reason = "服务器地址非法（\"" + serverUrl + "\"）";
                }
                else
                {
                    reason = "启动探测已判定服务器不可达（1 秒超时内 md5.txt 无响应，且无 UDP 广播来源）";
                }

                Debug.LogWarning(string.Format(
                    "[Res] 远端热更跳过（{0}）→ 使用离线模式：只读随包资源，不产生任何网络请求，游戏照常启动。\n" +
                    "  若这是预期外的降级：请确认热更服务器已启动、设备与电脑同网段，然后重启应用重试。",
                    reason));

                OfflinePlayModeOptions offlineOptions = new OfflinePlayModeOptions();
                offlineOptions.BuiltinFileSystemParameters =
                    FileSystemParameters.CreateDefaultBuiltinFileSystemParameters();
                return offlineOptions;
            }

            if (ResServerConfig.VerboseLog)
            {
                Debug.Log(string.Format(
                    "[Res] 热更已启用。服务器根地址 = {0}\n" +
                    "  YooAsset 将在其后自动追加 \"/<平台>/<包裹>/<版本>/\"，例如：\n" +
                    "  {1}/Android/{2}/<版本>/{2}.version",
                    serverUrl, serverUrl, PackageName));
            }

            FTRemoteService remoteService = new FTRemoteService(serverUrl);

            HostPlayModeOptions hostOptions = new HostPlayModeOptions();
            hostOptions.BuiltinFileSystemParameters =
                FileSystemParameters.CreateDefaultBuiltinFileSystemParameters();
            hostOptions.CacheFileSystemParameters = BuildSandboxParameters(remoteService);
            return hostOptions;
#else
            OfflinePlayModeOptions options = new OfflinePlayModeOptions();
            options.BuiltinFileSystemParameters = FileSystemParameters.CreateDefaultBuiltinFileSystemParameters();
            return options;
#endif
        }

        /// <summary>
        /// 构建沙盒（可写缓存）文件系统参数，并**显式打开 YooAsset 三个默认关闭的能力**。
        ///
        /// ==================================================================
        /// 【为什么必须显式打开 —— YooAsset 3.0.x 的默认值几乎都是"关着的"】
        ///   读源码 `SandboxFileSystem.cs` 可确认：
        ///     · FileVerifyLevel        = EFileVerifyLevel.Low    ← 只验"文件存在"，不验内容
        ///     · ResumeDownloadMinimumSize = long.MaxValue         ← 断点续传**恒不启用**
        ///     · DownloadWatchdogTimeout   = 0                     ← 看门狗监控**禁用**
        ///   即：不传参的话，"完整性校验 / 断点续传 / 卡死检测"三样全都形同虚设。
        ///   这三样恰好就是需求第 3、4 条要的东西，所以必须在这里显式配置。
        ///
        /// 【每个参数的作用与取值理由】
        ///   ① FileVerifyLevel = High
        ///      用 CRC 校验已缓存文件的完整性。开销是首次构建缓存时多一次全量读，
        ///      收益是**能发现"文件在但内容坏了"**（Low/Middle 都发现不了）。
        ///      对"下载中断后残留半截文件"这类问题，这是唯一能兜住的档位。
        ///
        ///   ② DownloadResumeMinimumSize = 1 MB
        ///      大于等于该尺寸的 bundle 走断点续传（`Range: bytes=N-`）。
        ///      设 1MB 是因为：小文件重下的代价 < 发 Range 请求 + 服务端多一次处理的代价。
        ///      默认的 long.MaxValue 等于"永不续传"，必须改掉。
        ///
        ///   ③ DownloadWatchdogTimeout = 30 秒
        ///      监控"数据接收停滞"：连接还在但 30 秒没有任何新字节 → 判定卡死并重试。
        ///      ⚠️ 这不是"总下载超时"（文件下载本身不设超时，见 YooAsset 源码
        ///      `DownloadAndCacheFileOperation` 里 `timeout = 0` 的注释），
        ///      而是**卡死检测**。真正的总超时由上层 CheckUpdateCo 负责。
        ///
        ///   ④ DownloadMaxConcurrency = 8 / DownloadMaxRequestPerFrame = 4
        ///      默认是 10 / 8。移动端下调是因为：Wi-Fi 弱网下高并发会互相抢带宽，
        ///      反而拉长整体耗时；单帧发 8 个请求也可能在低端机上造成尖峰。
        ///      8/4 是更稳的移动端取值。
        ///
        /// ⚠️ **改这里的参数必须重跑 HybridCLR Generate/All 吗？** 不需要 ——
        ///    本文件属于热更层（FTProject.Runtime），改完热更即可生效。
        /// ==================================================================
        /// </summary>
        private static FileSystemParameters BuildSandboxParameters(FTRemoteService remoteService)
        {
            FileSystemParameters parameters =
                FileSystemParameters.CreateDefaultSandboxFileSystemParameters(remoteService);

            // ① 完整性校验：CRC 级（默认 Low 形同虚设）
            parameters.AddParameter(EFileSystemParameter.FileVerifyLevel, EFileVerifyLevel.High);

            // ② 断点续传：≥1MB 的文件启用（默认 long.MaxValue = 永不启用）
            parameters.AddParameter(EFileSystemParameter.DownloadResumeMinimumSize,
                ResumeDownloadMinimumSizeBytes);

            // ③ 看门狗：30 秒无新数据判定卡死（默认 0 = 禁用）
            parameters.AddParameter(EFileSystemParameter.DownloadWatchdogTimeout,
                DownloadWatchdogTimeoutSeconds);

            // ④ 并发与单帧请求数：移动端更保守的取值（默认 10 / 8）
            parameters.AddParameter(EFileSystemParameter.DownloadMaxConcurrency, DownloadMaxConcurrency);
            parameters.AddParameter(EFileSystemParameter.DownloadMaxRequestPerFrame, DownloadMaxRequestPerFrame);

            if (ResServerConfig.VerboseLog)
            {
                Debug.Log(string.Format(
                    "[Res] 沙盒文件系统参数：校验={0}，断点续传阈值={1:N0} 字节，看门狗={2}s，并发={3}，每帧请求={4}",
                    EFileVerifyLevel.High, ResumeDownloadMinimumSizeBytes,
                    DownloadWatchdogTimeoutSeconds, DownloadMaxConcurrency, DownloadMaxRequestPerFrame));
            }

            return parameters;
        }

        /// <summary>断点续传的最小文件尺寸（字节）。1MB 以下重下比续传更划算。</summary>
        private const long ResumeDownloadMinimumSizeBytes = 1024L * 1024L;

        /// <summary>下载看门狗超时（秒）：数据接收停滞多久判定卡死。</summary>
        private const int DownloadWatchdogTimeoutSeconds = 30;

        /// <summary>下载最大并发数（YooAsset 推荐范围 1–32）。</summary>
        private const int DownloadMaxConcurrency = 8;

        /// <summary>每帧最多发起多少个下载请求（YooAsset 推荐范围 1–10）。</summary>
        private const int DownloadMaxRequestPerFrame = 4;

        private void LogReady()
        {
            string version;
            try
            {
                version = _package.GetPackageVersion();
            }
            catch (Exception)
            {
                version = "(未知)";
            }

            Debug.Log(string.Format(
                "[Res] YooAsset 模式初始化完成。包裹={0}，版本={1}，常驻包 {2} 个（不参与卸载）。" +
                "如需回到原有链路，移除 Scripting Define Symbols 里的 USE_YOOASSET。",
                PackageName, version, ResBundle.Persistent.Length));
        }

        // ==================================================================
        // 加载：公共准备
        // ==================================================================

        /// <summary>
        /// 加载前的公共准备：初始化检查 / 类型检查 / 缓存命中 / 逻辑名解析 / 定位地址解析。
        ///
        /// 【为什么要抽出来】同步与异步两条路径若各写一份，迟早会漂移。
        /// 漂移的典型症状是"同步能加载、异步却报未登记"，排查起来非常费时。
        /// </summary>
        private ResolveResult Resolve(string logicalName, System.Type type)
        {
            ResolveResult result = new ResolveResult();

            if (_ready == false || _package == null)
            {
                Fail(string.Format(
                    "[Res] YooAsset 尚未初始化完成，无法加载「{0}」。\n" +
                    "  正确用法：等 ResLoader.Instance.Init 的回调触发之后再取资源。",
                    logicalName));
                return result;
            }

            if (IsLoadableType(type) == false)
            {
                Fail(string.Format(
                    "[Res] 不能把「{0}」当作 {1} 加载：YooAsset 只支持加载**资源资产**\n" +
                    "  （GameObject / Sprite / TextAsset / AudioClip / RuntimeAnimatorController 等），\n" +
                    "  不接受组件（Behaviour 派生）类型。",
                    logicalName, type.Name));
                return result;
            }

            AssetHandle cached;
            if (_handles.TryGetValue(logicalName, out cached))
            {
                if (cached != null && cached.IsValid)
                {
                    UnityEngine.Object obj = cached.GetAssetObject<UnityEngine.Object>();
                    if (obj != null && type.IsAssignableFrom(obj.GetType()))
                    {
                        result.Ok = true;
                        result.FromCache = true;
                        result.Handle = cached;
                        return result;
                    }
                }

                // 句柄失效、或同一个逻辑名被要求了另一种资源类型：
                // 必须换句柄。这里先 Release 再重载 —— 只从字典里删掉而不 Release
                // 会让旧句柄一直占着 YooAsset 的引用计数，资源永远不回收。
                ReleaseHandle(logicalName);
            }

            ResAddress addr;
            if (ResTable.TryGet(logicalName, out addr) == false || addr.IsValid == false)
            {
                Fail(string.Format("[Res] 资源地址表中找不到逻辑名「{0}」，请在 ResTable.cs 中登记", logicalName));
                return result;
            }

            result.Ok = true;
            result.FromCache = false;
            result.Location = ResolveLocation(logicalName, addr);
            return result;
        }

        /// <summary>YooAsset 只接受 UnityEngine.Object 派生、且非 Behaviour 的类型</summary>
        private static bool IsLoadableType(System.Type type)
        {
            if (type == null)
            {
                return false;
            }
            if (typeof(UnityEngine.Object).IsAssignableFrom(type) == false)
            {
                return false;
            }
            return typeof(Behaviour).IsAssignableFrom(type) == false;
        }

        /// <summary>
        /// 逻辑名 → YooAsset 定位地址。
        ///
        /// 【为什么要探测而不是写死一个】ResTable 存的是"逻辑名 → (包名, 包内资产名, 编辑器路径)"，
        /// 而 YooAsset 的定位地址由 Bundle Collector 的**寻址规则**决定，默认规则是
        /// 「定位地址: 文件名」→ 地址 = 文件名（不含扩展名）。若有人把规则改成
        /// 「分组名_文件名」「完整路径」等，写死的地址就会整片失效。
        /// 这里按优先级逐个探测（命中即缓存），既容忍规则变化，也不会每次都重复判断。
        /// </summary>
        private string ResolveLocation(string logicalName, ResAddress addr)
        {
            string cached;
            if (_locations.TryGetValue(logicalName, out cached))
            {
                return cached;
            }

            string[] candidates = BuildLocationCandidates(addr);
            for (int i = 0; i < candidates.Length; i++)
            {
                string candidate = candidates[i];
                if (string.IsNullOrEmpty(candidate))
                {
                    continue;
                }
                if (IsLocationValidSafe(candidate))
                {
                    _locations[logicalName] = candidate;
                    return candidate;
                }
            }

            // 一个都没命中：返回首选候选，让 YooAsset 抛出带地址的错误，便于人工比对。
            Debug.LogWarning(string.Format(
                "[Res] 逻辑名「{0}」在 YooAsset 清单里找不到对应定位地址。\n" +
                "  已尝试：{1}\n" +
                "  排查：该资源是否已被 Bundle Collector 的收集目录覆盖？",
                logicalName, string.Join(" / ", candidates)));
            return candidates[0];
        }

        /// <summary>按"最可能命中"的顺序给出候选定位地址</summary>
        private static string[] BuildLocationCandidates(ResAddress addr)
        {
            // ① 文件名：匹配默认寻址规则「定位地址: 文件名」（AddressByFileName）
            string byFileName = string.IsNullOrEmpty(addr.EditorPath)
                ? addr.Asset
                : Path.GetFileNameWithoutExtension(addr.EditorPath);

            // ② ResTable 登记的包内资产名（多数情况下与①相同，是天然的兜底）
            // ③ 完整路径去扩展名：匹配「完整路径」类寻址规则
            string byFullPath = string.IsNullOrEmpty(addr.EditorPath)
                ? string.Empty
                : StripExtension(addr.EditorPath);

            return new string[] { byFileName, addr.Asset, byFullPath, addr.EditorPath };
        }

        private static string StripExtension(string path)
        {
            int dot = path.LastIndexOf('.');
            int slash = path.LastIndexOf('/');
            if (dot > slash && dot > 0)
            {
                return path.Substring(0, dot);
            }
            return path;
        }

        // ==================================================================
        // 加载：同步 / 异步
        // ==================================================================

        public T Load<T>(string logicalName) where T : UnityEngine.Object
        {
            ResolveResult result = Resolve(logicalName, typeof(T));
            if (result.Ok == false)
            {
                return null;
            }
            if (result.FromCache)
            {
                return result.Handle.GetAssetObject<T>();
            }

            AssetHandle handle = LoadSyncInternal(logicalName, typeof(T), result.Location);
            if (handle == null)
            {
                return null;
            }
            return handle.GetAssetObject<T>();
        }

        private AssetHandle LoadSyncInternal(string logicalName, System.Type type, string location)
        {
            string error;
            AssetHandle handle = TryLoadSync(location, type, out error);
            if (handle == null || handle.Status != EOperationStatus.Succeeded)
            {
                Fail(FormatLoadError(logicalName, type, location,
                    handle == null ? error : handle.Error));
                if (handle != null && handle.IsValid)
                {
                    handle.Release();
                }
                return null;
            }

            _handles[logicalName] = handle;
            return handle;
        }

        public void LoadAsync<T>(string logicalName, Action<T> onDone) where T : UnityEngine.Object
        {
            ResLoaderRunner.Start(LoadAsyncCo<T>(logicalName, onDone));
        }

        private IEnumerator LoadAsyncCo<T>(string logicalName, Action<T> onDone) where T : UnityEngine.Object
        {
            ResolveResult result = Resolve(logicalName, typeof(T));

            T asset = null;
            if (result.Ok)
            {
                AssetHandle handle = result.FromCache ? result.Handle : null;
                if (handle == null)
                {
                    string startError;
                    handle = TryLoadAsync(result.Location, typeof(T), out startError);
                    if (handle == null)
                    {
                        Fail(FormatLoadError(logicalName, typeof(T), result.Location, startError));
                    }

                    while (handle != null && handle.IsDone == false)
                    {
                        yield return null;
                    }

                    if (handle != null && handle.Status != EOperationStatus.Succeeded)
                    {
                        Fail(FormatLoadError(logicalName, typeof(T), result.Location, handle.Error));
                        if (handle.IsValid)
                        {
                            handle.Release();
                        }
                        handle = null;
                    }
                    else if (handle != null)
                    {
                        _handles[logicalName] = handle;
                    }
                }

                if (handle != null)
                {
                    asset = handle.GetAssetObject<T>();
                }
            }

            // 与其它两个实现保持一致：即使命中缓存也**至少延迟一帧**再回调，
            // 免得业务代码写出"依赖同步返回"的写法（编辑器直读能跑，真机上必炸）。
            yield return null;
            if (onDone != null)
            {
                onDone(asset);
            }
        }

        private static string FormatLoadError(string logicalName, System.Type type, string location, string error)
        {
            return string.Format(
                "[Res] YooAsset 加载失败：逻辑名「{0}」，类型 {1}\n" +
                "  定位地址：{2}\n" +
                "  错误：{3}\n" +
                "  排查：\n" +
                "   ① 该资源是否已被 Bundle Collector 收集（YooAsset ▸ Bundle Collector）\n" +
                "   ② 收集器的「定位地址」规则是否与上面的地址口径一致（默认是「文件名」）\n" +
                "   ③ 是否已构建过资源包（真机/离线模式）或模拟清单（编辑器模拟模式）",
                logicalName, type.Name, location, error);
        }

        // ==================================================================
        // 实例化
        // ==================================================================

        public GameObject Instantiate(string logicalName, Transform parent = null)
        {
            GameObject prefab = Load<GameObject>(logicalName);
            if (prefab == null)
            {
                return null;
            }

            GameObject go = UnityEngine.Object.Instantiate(prefab);
            go.name = go.name.Replace("(Clone)", string.Empty);
            AttachTo(go, parent);
            return go;
        }

        public void InstantiateAsync(string logicalName, Transform parent, Action<GameObject> onDone)
        {
            LoadAsync<GameObject>(logicalName, prefab =>
            {
                GameObject go = null;
                if (prefab != null)
                {
                    go = UnityEngine.Object.Instantiate(prefab);
                    go.name = go.name.Replace("(Clone)", string.Empty);
                    AttachTo(go, parent);
                }
                if (onDone != null)
                {
                    onDone(go);
                }
            });
        }

        private static void AttachTo(GameObject go, Transform parent)
        {
            if (parent == null)
            {
                return;
            }
            // 【绝不能重置 localScale】预制体根节点的缩放是美术调好的
            //（怪物包是 0.5、塔是 0.8）。重置成 1 会让怪物大 2 倍，
            // 也会让"配置表的 scale=1 表示保持美术原样"这一语义失效。
            go.transform.SetParent(parent, false);
            go.transform.localPosition = Vector3.zero;
            go.transform.localRotation = Quaternion.identity;
        }

        // ==================================================================
        // 生命周期
        // ==================================================================

        public void ReleaseInstance(string logicalName, GameObject instance)
        {
            if (instance == null)
            {
                return;
            }
            if (Application.isPlaying)
            {
                UnityEngine.Object.Destroy(instance);
            }
            else
            {
                UnityEngine.Object.DestroyImmediate(instance);
            }
        }

        /// <summary>释放单个逻辑名的句柄（**不动包级引用计数**，见接口注释）</summary>
        public void Release(string logicalName)
        {
            ReleaseHandle(logicalName);
        }

        private void ReleaseHandle(string logicalName)
        {
            AssetHandle handle;
            if (_handles.TryGetValue(logicalName, out handle) == false)
            {
                return;
            }
            _handles.Remove(logicalName);
            if (handle != null && handle.IsValid)
            {
                handle.Release();
            }
        }

        /// <summary>
        /// 整包释放：关卡引用计数 -1，归零时释放该包下全部句柄并让 YooAsset 回收。
        ///
        /// 【与 BundleResLoader 的一处刻意差异】AB 版在这里是"无条件清掉资源缓存"，
        /// 因为物理包还在、资源随时能重新取到；而 YooAsset 里**释放句柄 = 资源引用计数归零**，
        /// 随后的 UnloadUnusedAssets 会把它直接回收 —— 场景还在用的话会当场变白。
        /// 所以这里只在引用计数真正归零时才放句柄，宁可更保守。
        /// </summary>
        public void ReleaseBundle(string bundleName)
        {
            if (string.IsNullOrEmpty(bundleName))
            {
                return;
            }
            if (IsPersistent(bundleName))
            {
                return;   // 常驻包不参与卸载
            }

            if (ReleaseRef(bundleName) > 0)
            {
                return;   // 还有别的关卡引用着这个包
            }

            List<string> keys = ResTable.GetKeysByBundle(bundleName);
            for (int i = 0; i < keys.Count; i++)
            {
                ReleaseHandle(keys[i]);
            }

            // 句柄都放掉了，让 YooAsset 把零引用的物理包收回去。
            // 不等待它：这是后台回收，等它反而会卡住切关。
            if (_package != null)
            {
                try
                {
                    _package.UnloadUnusedAssetsAsync();
                }
                catch (Exception ex)
                {
                    // 回收失败不是致命问题（只是内存晚一点释放），但不能让它打断切关流程。
                    Debug.LogWarning(string.Format("[Res] YooAsset 回收未使用资源失败：{0}", ex.Message));
                }
            }
        }

        private void AcquireRef(string bundleName)
        {
            int count;
            _refCount.TryGetValue(bundleName, out count);
            _refCount[bundleName] = count + 1;
        }

        /// <summary>引用计数 -1，返回剩余计数（0 表示已归零）</summary>
        private int ReleaseRef(string bundleName)
        {
            int count;
            if (_refCount.TryGetValue(bundleName, out count) == false)
            {
                return 0;
            }
            count--;
            if (count <= 0)
            {
                _refCount.Remove(bundleName);
                return 0;
            }
            _refCount[bundleName] = count;
            return count;
        }

        private static bool IsPersistent(string bundleName)
        {
            for (int i = 0; i < ResBundle.Persistent.Length; i++)
            {
                if (ResBundle.Persistent[i] == bundleName)
                {
                    return true;
                }
            }
            return false;
        }

        // ==================================================================
        // 预加载
        // ==================================================================

        public void Preload(string[] logicalNames, Action onDone)
        {
            Preload(logicalNames, null, onDone);
        }

        public void Preload(string[] logicalNames, Action<float> onProgress, Action onDone)
        {
            ResLoaderRunner.Start(PreloadCo(logicalNames, onProgress, onDone));
        }

        // ==================================================================
        // 场景加载（IResLoader.LoadSceneAsync）
        // ==================================================================

        /// <summary>
        /// 异步加载场景（Single 模式）。
        /// 【为什么必须在 YooAssetResLoader 里做】HybridCLR 真机上，挂了热更脚本的
        /// 场景只能从 AssetBundle 加载 —— 包体 BuildSettings 场景在打包时热更程序集
        /// 被剔除，组件烘焙成空壳。YooAsset 的 SceneHandle 走"内置/沙盒"文件系统，
        /// 离线模式读随包 bundle，联机模式读下载后的沙盒，两者都覆盖。
        /// </summary>
        public void LoadSceneAsync(string location, Action<bool, string> onResult)
        {
            if (!_ready)
            {
                Fail("[Res] 场景加载失败：资源系统尚未初始化完成（Init 未成功）");
                if (onResult != null) onResult(false, "资源系统未初始化");
                return;
            }

            SceneHandle handle = _package.LoadSceneAsync(location, LoadSceneMode.Single);
            if (handle == null)
            {
                Fail(string.Format("[Res] 场景加载无法启动：{0}", location));
                if (onResult != null) onResult(false, "场景加载无法启动：" + location);
                return;
            }

            ResLoaderRunner.Start(WaitSceneCo(location, handle, onResult));
        }

        private IEnumerator WaitSceneCo(string location, SceneHandle handle, Action<bool, string> onResult)
        {
            yield return handle;

            if (handle.Status != EOperationStatus.Succeeded)
            {
                string err = string.Format("场景「{0}」加载失败：{1}", location, handle.Error);
                Fail("[Res] " + err);
                if (onResult != null) onResult(false, err);
                yield break;
            }

            Debug.Log(string.Format("[Res] 场景「{0}」加载完成", location));
            if (onResult != null) onResult(true, null);
        }

        private IEnumerator PreloadCo(string[] logicalNames, Action<float> onProgress, Action onDone)
        {
            if (logicalNames != null && logicalNames.Length > 0)
            {
                // ① 对涉及的包取"关卡引用"，与 ReleaseBundle 严格配对
                HashSet<string> bundles = new HashSet<string>();
                for (int i = 0; i < logicalNames.Length; i++)
                {
                    ResAddress addr;
                    if (ResTable.TryGet(logicalNames[i], out addr) && addr.IsValid)
                    {
                        bundles.Add(addr.Bundle);
                    }
                    else
                    {
                        Fail(string.Format("[Res] 预加载发现未登记的逻辑名：{0}", logicalNames[i]));
                    }
                }
                foreach (string bundle in bundles)
                {
                    AcquireRef(bundle);
                }

                // ② 逐个预热并汇总失败清单（一次性打印，不逐条刷屏）
                //
                // 【为什么用 UnityEngine.Object 作预热类型】ResTable 不记资源类型，
                // 这里只求"把物理包拉进内存"这个大头成本（后续按具体类型加载时，
                // 包已常驻，只是再建一个 provider，代价很小）。YooAsset 自己的
                // LoadAssetSync(location) 同理，内部用的就是 typeof(UnityEngine.Object)。
                StringBuilder missing = new StringBuilder();
                int okCount = 0;
                for (int i = 0; i < logicalNames.Length; i++)
                {
                    string name = logicalNames[i];
                    ResolveResult result = Resolve(name, typeof(UnityEngine.Object));
                    if (result.Ok == false)
                    {
                        missing.Append("\n  · " + name);
                        if (onProgress != null) onProgress((i + 1) / (float)logicalNames.Length);
                        continue;
                    }
                    if (result.FromCache)
                    {
                        okCount++;
                        if (onProgress != null) onProgress((i + 1) / (float)logicalNames.Length);
                        continue;
                    }

                    string startError;
                    AssetHandle handle = TryLoadAsync(result.Location, typeof(UnityEngine.Object), out startError);
                    if (handle == null)
                    {
                        missing.Append("\n  · " + name + "  →  " + startError);
                        if (onProgress != null) onProgress((i + 1) / (float)logicalNames.Length);
                        continue;
                    }

                    while (handle.IsDone == false)
                    {
                        yield return null;
                    }

                    if (handle.Status != EOperationStatus.Succeeded)
                    {
                        missing.Append("\n  · " + name + "  →  " + handle.Error);
                        if (handle.IsValid)
                        {
                            handle.Release();
                        }
                        if (onProgress != null) onProgress((i + 1) / (float)logicalNames.Length);
                        continue;
                    }

                    _handles[name] = handle;
                    okCount++;
                    if (onProgress != null) onProgress((i + 1) / (float)logicalNames.Length);
                }

                if (missing.Length > 0)
                {
                    Fail(string.Format(
                        "[Res] YooAsset 预加载：{0}/{1} 个资源就绪，以下不可用：{2}",
                        okCount, logicalNames.Length, missing));
                }
                else
                {
                    Debug.Log(string.Format(
                        "[Res] YooAsset 预加载完成：{0} 个资源全部就绪。", okCount));
                }
            }

            if (onProgress != null) onProgress(1f);
            if (onDone != null)
            {
                onDone();
            }
        }

        // ==================================================================
        // 热更新（UI 补全 A3）—— 唯一的上线阻塞项
        // ==================================================================
        // ⚠️【与手册骨架的关键差异，别照抄网上 2.x 教程】
        //   手册 §7.2 的骨架用了 `UpdatePackageVersionAsync` + `CreateResourceDownloader(...)`
        //   + `OnDownloadProgressCallback` + `BeginDownload()`，那是 **YooAsset 2.x** 的 API。
        //   本工程是 **3.0.6**：`UpdatePackageVersionAsync` / `UpdatePackageManifestAsync` 已废弃，
        //   只在 Compatibility 层留了 [Obsolete] 包装。3.0.x 的正确对应关系是：
        //     · 「取最新版本」      = `RequestPackageVersionAsync()`（它本来就查远端最新）
        //     · 「更新/加载清单」   = `LoadPackageManifestAsync(version)` —— 即已有的第③步，
        //                             它会下载并激活新清单，**不再有独立的 Update 步骤**
        //     · 「下载进度」        = `DownloadProgressChanged` 事件（不是 OnDownloadProgressCallback）
        //     · 「开始下载」        = `StartDownload()`（不是 BeginDownload）
        //   ⚠️ 三步初始化契约不变：Init 里仍是 初始化 → 请求版本 → 加载清单（最后 SetActiveManifest）。
        //      本方法在 **Init 之后**调用，复用同一个 _package，绝不重复初始化。

        /// <summary>
        /// IHotUpdateLoader 入口：把 CheckUpdateCo 交给本工程的协程宿主驱动。
        /// 【为什么必须交给 ResLoaderRunner】UI 层拿不到（也不该拿）IEnumerator，
        /// 统一由 ResLoaderRunner 启动，保证"运行态逐帧推进、非运行态当场跑完"两条路径一致。
        /// </summary>
        public void StartCheckUpdate(
            Action<string> onPhase,
            Action<int, int> onProgress,
            Action<long, long> onBytes,
            Action<string> onError,
            Action<bool> onDone)
        {
            ResLoaderRunner.Start(CheckUpdateCo(onPhase, onProgress, onBytes, onError, onDone));
        }

        /// <summary>
        /// 检查并执行资源热更新。协程，需由 ResLoaderRunner.Start 驱动。
        /// 回调语义：<paramref name="onDone"/> 的参数 = **本次是否真的下载过内容**。
        /// 出错时只调 <paramref name="onError"/>（不调 onDone），由界面决定是否重试。
        /// </summary>
        public IEnumerator CheckUpdateCo(
            Action<string> onPhase,
            Action<int, int> onProgress,
            Action<long, long> onBytes,
            Action<string> onError,
            Action<bool> onDone)
        {
            if (_package == null || !_ready)
            {
                if (onError != null)
                {
                    onError("资源系统尚未初始化完成，无法检查更新");
                }
                yield break;
            }

            // ---- ⓪ 前置闸门（2026-10-15）：服务器不可达 / 热更未配置时，
            //      **不发起任何远端请求**，直接按"无需更新"放行，用本地资源继续启动。
            //      与 CreateInitOptions 的离线降级同源（那边保证包按离线模式初始化，
            //      这边连"检查"都跳过）—— 双保险：任何路径都不会再出现
            //      "检查更新"长时间等待（此前版本请求默认 60s 超时且硬失败）。
            if (ResServerConfig.IsRemoteHotUpdateAllowed() == false)
            {
                if (onPhase != null) onPhase("当前模式：无需更新资源");
                Debug.Log("[Res] 跳过资源更新检查：远端热更未启用（服务器不可达 / 未配置），直接使用本地资源。");
                yield return null;   // 让阶段文案至少显示一帧，避免界面一闪而过看不出原因
                if (onDone != null) onDone(false);
                yield break;
            }

            // ---- ① 请求最新版本 -------------------------------------------------
            if (onPhase != null) onPhase("正在检查更新...");

            string startError;
            RequestPackageVersionOperation versionOp = StartRequestVersion(out startError);
            if (versionOp == null)
            {
                if (onError != null) onError("请求资源版本失败：" + startError);
                yield break;
            }

            yield return WaitOpCo(versionOp, "检查更新-请求版本");

            if (versionOp.Status != EOperationStatus.Succeeded)
            {
                if (onError != null) onError("请求资源版本失败：" + versionOp.Error);
                yield break;
            }

            string latestVersion = versionOp.PackageVersion;
            string currentVersion = _package.GetPackageVersion();

            // 【版本日志（P：版本号显示与日志）】无论是否需要更新，都把
            // "当前版本 → 远端最新版本" 打出来 —— 这是排查"真机到底跑的哪个资源版本"
            // 时最常看的一条日志，只在版本变化时打会漏掉"版本相同但文件缺失"的情形。
            Debug.Log(string.Format(
                "[Version][Res] 检查更新：当前资源版本={0}，远端最新版本={1}",
                string.IsNullOrEmpty(currentVersion) ? "(未知)" : currentVersion,
                string.IsNullOrEmpty(latestVersion) ? "(未知)" : latestVersion));

            // ---- ② 比对版本 -----------------------------------------------------
            if (onPhase != null) onPhase("正在比对资源版本...");
            yield return null;   // 让 PhaseText 至少显示一帧，否则"比对"会被瞬间跳过看不见

            bool versionChanged = !string.IsNullOrEmpty(latestVersion) && latestVersion != currentVersion;
            if (versionChanged)
            {
                Debug.Log(string.Format("[Res] 发现新资源版本：{0} → {1}，开始更新。",
                    string.IsNullOrEmpty(currentVersion) ? "(未知)" : currentVersion, latestVersion));

                // ---- ③ 加载（必要时下载）新清单并激活 ----------------------------
                // ⚠️ 这一步等价于 2.x 的 UpdatePackageManifest，**必须**做：
                //    只下 bundle 不换清单，之后所有加载都会按旧清单去找 → 找不到新资源。
                if (onPhase != null) onPhase("正在加载资源清单...");

                LoadPackageManifestOperation manifestOp = StartLoadManifest(latestVersion, out startError);
                if (manifestOp == null)
                {
                    if (onError != null) onError("加载资源清单失败：" + startError);
                    yield break;
                }

                yield return WaitOpCo(manifestOp, "检查更新-加载清单");

                if (manifestOp.Status != EOperationStatus.Succeeded)
                {
                    if (onError != null) onError("加载资源清单失败：" + manifestOp.Error);
                    yield break;
                }
            }
            else
            {
                // 【2026-10-14 修复】版本号相同 ≠ 文件齐全，必须继续走 ④ 校验缺失。
                //
                // 反例（本次踩坑）：HostPlayMode 下"同步加载一个既不在沙盒、也不在内置包
                // 里的 bundle"会**立即失败**——SandboxFileSystem 无法在同步上下文里等待
                // 远端下载，只能把下载转后台继续（见 SFSDownloadBundleOperation 的
                // continueDownloadInBackground 分支），本次加载返回错误。
                // 典型受害者：**本次热更新增、而 APK 内置包没有的资源** —— 首次启动时
                // 用同步接口去加载它们必然失败一次（要等下一轮加载才命中缓存）。
                // 旧逻辑"版本相同 → 资源已是最新 → 直接返回"会让这些文件永远补不上：
                // 启动时没人负责把差异下载进沙盒（场景走异步加载能自愈，普通同步加载不能）。
                //
                // 所以版本相同时也继续走到 ④：用下载器把"清单 vs 沙盒缓存"的缺失差异
                // 补齐。**内置包已有的文件会被自动识别并走本地导入，不产生网络流量**；
                // 真正的下载量只有"新增资源"那部分（通常很小）。
                if (onPhase != null) onPhase("正在校验资源完整性...");
                yield return null;   // 让 PhaseText 至少显示一帧
            }

            // ---- ④ 差异下载（版本相同也执行；无缺失时 TotalDownloadCount == 0 自然短路）----
            ResourceDownloaderOperation downloader;
            try
            {
                // YooAsset 3.0.6 走 options 结构（2.x 的 `CreateResourceDownloader(并发, 重试)` 已移除）
                var options = new ResourceDownloaderOptions(10, 3);   // 并发 10，失败重试 3
                downloader = _package.CreateResourceDownloader(options);
            }
            catch (System.Exception ex)
            {
                if (onError != null) onError("创建下载任务失败：" + ex.Message);
                yield break;
            }

            if (downloader == null || downloader.TotalDownloadCount == 0)
            {
                // 版本号变了但没有需要下载的资源（例如只改了清单里的哈希）→ 视为"无需下载"
                if (onPhase != null) onPhase("资源已是最新");
                Debug.Log(string.Format(
                    "[Version][Res] 无需下载资源，更新后资源版本={0}（与远端一致）。",
                    string.IsNullOrEmpty(latestVersion) ? "(未知)" : latestVersion));
                if (onDone != null) onDone(false);
                yield break;
            }

            if (onPhase != null) onPhase("正在下载资源...");

            _downloader = downloader;
            IsPaused = false;
            string lastError = null;
            bool timedOut = false;

            downloader.DownloadProgressChanged += args =>
            {
                if (onProgress != null) onProgress(args.CurrentDownloadCount, args.TotalDownloadCount);
                if (onBytes != null) onBytes(args.CurrentDownloadBytes, args.TotalDownloadBytes);
            };
            downloader.DownloadError += args =>
            {
                lastError = string.IsNullOrEmpty(args.FileName)
                    ? args.ErrorInfo
                    : args.FileName + "：" + args.ErrorInfo;
            };

            downloader.StartDownload();

            // ---- 总超时保护（需求 5："整个更新流程需设置总超时"）------------------
            // 【为什么 YooAsset 自己不管这个】
            //   看源码 DownloadAndCacheFileOperation 的注释写得很明确：
            //     `int timeout = 0; //注意：文件下载不做超时检测`
            //   它只提供 DownloadWatchdogTimeout（卡死检测），不提供整批下载的上限。
            //   所以"整批多久没下完就放弃"必须由调用方算。
            //
            // 【超时后的行为 —— 关键：不阻断启动】
            //   调用 CancelDownload() 让下载器收敛（它会 abort 所有在途请求），
            //   然后用 onError 通知界面。此时**已下完的那部分 bundle 是有效的**
            //   （YooAsset 是逐文件落缓存 + 逐个校验，不是整批原子提交），
            //   下次启动会从这里继续（断点续传已开启）。
            //   ⇒ 最坏情况 = 这次少更了一部分资源，但游戏仍能用**上一次的完整清单**启动。
            //     （清单是最后才 SetActiveManifest 的，没下完就不会切清单 —— 安全。）
            float deadline = Time.realtimeSinceStartup + TotalDownloadTimeoutSeconds;

            while (downloader.IsDone == false)
            {
                if (Time.realtimeSinceStartup >= deadline && timedOut == false)
                {
                    timedOut = true;
                    Debug.LogWarning(string.Format(
                        "[Res] 资源下载超过总超时 {0} 秒，取消本次下载（已下载部分保留，下次续传）。",
                        TotalDownloadTimeoutSeconds));
                    try
                    {
                        downloader.CancelDownload();
                    }
                    catch (System.Exception ex)
                    {
                        Debug.LogWarning("[Res] 取消下载时抛异常（忽略）：" + ex.Message);
                    }
                }
                yield return null;
            }

            _downloader = null;

            if (timedOut)
            {
                // 超时走错误通道：界面可据此提示"网络较慢，可稍后重试"，而不是假装成功。
                if (onError != null)
                {
                    onError(string.Format(
                        "资源下载超时（超过 {0} 秒）。已下载部分已保留，可稍后重试或直接使用当前版本。",
                        TotalDownloadTimeoutSeconds));
                }
                yield break;
            }

            if (downloader.Status != EOperationStatus.Succeeded)
            {
                if (onError != null)
                {
                    onError(string.IsNullOrEmpty(lastError) ? downloader.Error : lastError);
                }
                yield break;
            }

            Debug.Log(string.Format("[Res] 热更新完成，共下载 {0} 个文件。", downloader.TotalDownloadCount));

            // 【版本日志】更新完成后再取一次激活版本 —— 清单已在 ③ 换成远端最新，
            // 这条就是用户要的"更新完后的版本号"（与上面"当前资源版本"成对出现）。
            string updatedVersion;
            try
            {
                updatedVersion = _package.GetPackageVersion();
            }
            catch (Exception)
            {
                updatedVersion = "(未知)";
            }
            Debug.Log(string.Format(
                "[Version][Res] 资源热更新完成，更新后资源版本={0}（更新前={1}）。",
                updatedVersion, string.IsNullOrEmpty(currentVersion) ? "(未知)" : currentVersion));

            if (onPhase != null) onPhase("更新完成");
            if (onDone != null) onDone(true);
        }

        /// <summary>
        /// 整批资源下载的总超时（秒）。超过则取消本次下载并走错误通道。
        /// 需求第 5 条要求整个更新流程有总超时；YooAsset 只提供看门狗（卡死检测），
        /// 不提供批次总上限，所以在这里自己算。
        /// </summary>
        private const float TotalDownloadTimeoutSeconds = 300f;

        /// <summary>暂停当前下载（无进行中的下载时空操作）。</summary>
        public void PauseDownload()
        {
            IsPaused = true;
            if (_downloader != null)
            {
                _downloader.PauseDownload();
            }
        }

        /// <summary>继续当前下载（无进行中的下载时空操作）。</summary>
        public void ResumeDownload()
        {
            IsPaused = false;
            if (_downloader != null)
            {
                _downloader.ResumeDownload();
            }
        }

        /// <summary>是否正在下载（界面按钮状态用）。</summary>
        public bool IsDownloading
        {
            get { return _downloader != null && _downloader.IsDone == false; }
        }

        /// <summary>
        /// 是否处于"已暂停"。
        /// 【为什么自己记一个标记】YooAsset 的下载器没有暴露"暂停中"查询，
        /// 而界面必须能区分"正在下载"与"已暂停"（按钮要在"暂停/继续"之间切换）。
        /// 由本类的 PauseDownload/ResumeDownload 维护，不依赖底层实现。
        /// </summary>
        public bool IsPaused { get; private set; }

        /// <summary>
        /// 当前激活的资源清单版本（IHotUpdateLoader 实现）。
        /// 【为什么 try/catch】清单未激活（Init 失败/进行中）时 YooAsset 会抛异常；
        /// 版本号是展示性信息，取不到就返回 null，绝不让 UI/日志因为取版本而炸。
        /// </summary>
        public string CurrentResourceVersion
        {
            get
            {
                if (_package == null || !_ready)
                {
                    return null;
                }
                try
                {
                    return _package.GetPackageVersion();
                }
                catch (Exception)
                {
                    return null;
                }
            }
        }

        private void Fail(string message)
        {
            Debug.LogError(message);
            if (OnLoadError != null)
            {
                OnLoadError(message);
            }
        }

        // ==================================================================
        // 诊断
        // ==================================================================

        public string DumpDebugInfo()
        {
            StringBuilder sb = new StringBuilder();
            sb.AppendLine(string.Format(
                "[Res] YooAssetResLoader：包裹={0}，持有句柄 {1} 个，引用记录 {2} 个包，定位地址缓存 {3} 条",
                PackageName, _handles.Count, _refCount.Count, _locations.Count));
            foreach (KeyValuePair<string, int> kv in _refCount)
            {
                sb.AppendLine(string.Format("  · {0,-18} ref={1}{2}",
                    kv.Key, kv.Value, IsPersistent(kv.Key) ? "（常驻）" : string.Empty));
            }
            return sb.ToString();
        }

        /// <summary>引用计数是否全部归零（除常驻包外）—— 泄漏自检用</summary>
        public bool HasLeak()
        {
            foreach (KeyValuePair<string, int> kv in _refCount)
            {
                if (kv.Value > 0 && IsPersistent(kv.Key) == false)
                {
                    return true;
                }
            }
            return false;
        }
    }
}
#endif
