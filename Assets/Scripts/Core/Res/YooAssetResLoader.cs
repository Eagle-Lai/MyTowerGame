#if USE_YOOASSET
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Text;
using UnityEngine;
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
    public class YooAssetResLoader : IResLoader
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
            if (_ready)
            {
                if (onDone != null)
                {
                    onDone();
                }
                return;
            }

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

        private static void FinishInit(Action onDone)
        {
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
        /// 按运行环境选择初始化参数。刻意复用既有的 FORCE_AB 宏作为"是否走真资源包"的开关，
        /// 语义与 EditorResLoader / BundleResLoader 的选择口径完全一致：
        ///   编辑器且未定义 FORCE_AB → 编辑器模拟模式（改完资源即可运行，无需构建）
        ///   其它（真机 / 定义了 FORCE_AB） → 离线模式，直接读随包的内置资源
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
#else
            OfflinePlayModeOptions options = new OfflinePlayModeOptions();
            options.BuiltinFileSystemParameters = FileSystemParameters.CreateDefaultBuiltinFileSystemParameters();
            return options;
#endif
        }

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
            ResLoaderRunner.Start(PreloadCo(logicalNames, onDone));
        }

        private IEnumerator PreloadCo(string[] logicalNames, Action onDone)
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
                        continue;
                    }
                    if (result.FromCache)
                    {
                        okCount++;
                        continue;
                    }

                    string startError;
                    AssetHandle handle = TryLoadAsync(result.Location, typeof(UnityEngine.Object), out startError);
                    if (handle == null)
                    {
                        missing.Append("\n  · " + name + "  →  " + startError);
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
                        continue;
                    }

                    _handles[name] = handle;
                    okCount++;
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

            if (onDone != null)
            {
                onDone();
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
