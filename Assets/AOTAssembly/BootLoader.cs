using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.SceneManagement;

namespace FTProject.AOT
{
    /// <summary>
    /// Boot 场景的唯一挂载脚本（**纯 AOT，不得引用任何热更类型**）。
    ///
    /// ==================================================================
    /// 【它在整个启动链里的位置】
    ///   Boot 场景（AOT）
    ///     └─ BootLoader.Awake
    ///          ├─ ① 加载 AOT 补充元数据 + 全部热更 dll（HotUpdateAssembler）
    ///          ├─ ② 找到 IHotUpdateEntry 的实现类并调用 Start()（热更侧接管）
    ///          └─ ③ 卸载 Boot 场景，进入 main 场景
    ///
    /// 【跨程序集契约：接口，而不是字符串】
    ///   热更侧入口**不再**靠"字符串类型名 + 反射方法名"约定，而是：
    ///
    ///     AOT 侧定义接口 FTProject.AOT.IHotUpdateEntry
    ///     → 热更侧实现它（FTProject.HotUpdateEntry : IHotUpdateEntry）
    ///     → 本类通过 HotUpdateEntryLocator 拿到接口引用并调用 Start()
    ///
    ///   收益（对比旧的字符串反射方案）：
    ///     ✅ 改名 / 改签名 → **编译期报错**，而不是运行时"找不到类型"
    ///     ✅ 接口方法可带强类型参数（以前反射只能无参）
    ///     ✅ 非空性由编译器保证（漏实现接口成员直接编译失败）
    ///     ✅ IDE 可跳转 / 重命名 / 查引用
    ///
    ///   ⚠️ 唯一残留的反射点在 HotUpdateEntryLocator —— 因为 AOT 侧
    ///      **不能 `new` 热更类型**（编译期符号依赖会让 IL2CPP 打包失败），
    ///      "找到实现者"这一步必须运行时完成。但它只做这一件事，
    ///      拿到接口后全部是强类型调用。
    ///
    /// 【为什么不直接在 BootLoader 里 SceneManager.LoadScene("main") 就完事】
    ///   技术上可行（Unity 实例化脚本时才会去已加载程序集里找类型），
    ///   但一旦 main 场景加载后有任何"初始化顺序"要求（例如必须先注册管理器再建关），
    ///   把入口交给热更侧**统一控制**更清晰，也便于热更侧以后改流程而不动 AOT。
    /// ==================================================================
    /// </summary>
    public class BootLoader : MonoBehaviour
    {
        /// <summary>
        /// main 场景名（仅用于日志/注释说明；**实际加载由热更侧 EnterMainScene 完成**，
        /// 场景地址在 HotUpdateEntry.MainSceneAddress —— 场景从 YooAsset AB 加载，
        /// 真机上 Build Settings 只保留 Boot 一个启用场景）。
        /// </summary>
        private const string MainSceneName = "main";

        /// <summary>
        /// 服务器可达性探测的超时（秒）。**刻意远小于下载超时** ——
        /// 探测的目的是"快速判断能不能连上"，连不上就不该让玩家多等。
        /// 需求第 2 条："设置合理超时；不可达则直接使用本地资源正常运行，不得阻塞启动或导致崩溃"。
        /// </summary>
        private const int ProbeTimeoutSeconds = 4;

        /// <summary>探测失败后的重试次数（网络抖动时给一次机会，但不恋战）。</summary>
        private const int ProbeRetryCount = 1;

        private void Awake()
        {
            Application.targetFrameRate = 60;
            DontDestroyOnLoad(gameObject);
            StartCoroutine(BootRoutine());
        }

        private IEnumerator BootRoutine()
        {
            SetStatus("正在加载热更程序集…");
            SetProgress(0f);

            // ⓪-a 首启预取：把随包 dll 从 StreamingAssets 释放到 persistentDataPath。
            //      Android 上 APK 内的 StreamingAssets 用 File IO 读不到，必须先释放；
            //      已存在（上次热更下来的）则不覆盖，避免把热更成果冲掉。
            //      【幂等 + 快速路径】内部用整目录指纹判定，指纹一致时零 IO 直接返回（见 HotUpdateAssembler）。
            SetStatus("正在准备热更程序集…");
            SetProgress(0.01f);
            yield return StartCoroutine(HotUpdateAssembler.PrefetchStreamingAssetsToPersistent(null));

            // ⓪-b 服务探测 → 可达才做 dll 热更；不可达直接跳过，用本地资源继续。
            //      需求第 2 条：探测必须有超时，且失败**绝不能阻塞启动**。
            yield return StartCoroutine(ProbeAndDownloadDllsCo());

            // ① 加载 dll（这一步在真机上稍慢，逐帧让出避免卡死界面）
            bool loaded = false;
            Exception loadError = null;

            yield return StartCoroutine(LoadAssembliesCo(
                (done, total) =>
                {
                    float p = total > 0 ? (float)done / total : 0f;
                    SetProgress(p * 0.8f);
                    SetStatus(string.Format("加载热更程序集 {0}/{1}", done, total));
                },
                () => { loaded = true; },
                e => { loadError = e; }));

            if (!loaded || loadError != null)
            {
                string msg = loadError != null ? loadError.Message : "未知错误";
                SetStatus("热更加载失败：\n" + msg);
                Debug.LogError("[Boot] 热更程序集加载失败：" + msg);
                yield break; // 停在这里，保留错误界面，不要静默进游戏
            }

            SetProgress(0.85f);
            SetStatus("正在启动游戏…");
            yield return null;

            // ② 找到 IHotUpdateEntry 实现并调用（热更侧接管）
            IHotUpdateEntry entry = HotUpdateEntryLocator.CreateEntry(out string entryError);
            if (entry == null)
            {
                SetStatus("启动失败：\n" + entryError);
                Debug.LogError("[Boot] 获取热更入口失败：" + entryError);
                yield break;
            }

            try
            {
                entry.Start();
                Debug.Log("[Boot] 热更入口已执行：" + entry.GetType().FullName + ".Start()");
            }
            catch (Exception e)
            {
                SetStatus("启动失败：\n" + e.Message);
                Debug.LogError("[Boot] 调用热更入口 Start() 抛异常：" + e);
                yield break;
            }

            SetProgress(1f);
            SetStatus("准备就绪");
            yield return null;

            // ③ 进入 main（**由热更侧加载场景**）
            //    【为什么不再 SceneManager.LoadScene】HybridCLR 真机上，挂了热更脚本的
            //    场景打进 Build Settings 会在打包时被烘焙成空壳（热更程序集在
            //    IFilterBuildAssemblies 阶段被剔除），运行时表现为
            //    "missing script / serialization layout" 错误。
            //    所以 main 场景必须从 AssetBundle 加载，而资源系统的模式选择
            //    （联机/离线）只有热更侧知道 —— 交棒给 IHotUpdateEntry.EnterMainScene。
            //    场景以 Single 模式激活后本场景自动卸载，本协程随之自然终止
            //    （成功路径不需要收尾动作）；失败则把错误显示在启动界面上。
            bool sceneDone = false;
            bool sceneOk = false;
            string sceneError = null;
            entry.EnterMainScene((ok, err) =>
            {
                sceneDone = true;
                sceneOk = ok;
                sceneError = err;
            });

            float guard = 0f;
            while (!sceneDone)
            {
                yield return null;
                guard += Time.unscaledDeltaTime;
                if (guard > 60f)
                {
                    SetStatus("启动失败：\n加载 main 场景超时（60s）");
                    Debug.LogError("[Boot] 加载 main 场景超时 —— 资源系统可能卡在初始化，详情见上方 [Res] 日志。");
                    yield break;
                }
            }

            if (!sceneOk)
            {
                SetStatus("启动失败：\n" + sceneError);
                Debug.LogError("[Boot] 热更侧加载 main 场景失败：" + sceneError);
                yield break;
            }

            // 成功路径：场景激活瞬间本场景已卸载，一般走不到这里；走到也无害。
            SetStatus("准备就绪");
        }

        /// <summary>
        /// **服务探测 + 条件性 dll 热更**。
        ///
        /// ==================================================================
        /// 【为什么探测与下载要捆在一起做】
        ///   探测本身也要发网络请求，如果"探测完再另起一个方法去下载"，
        ///   中间会多一次协程切换与状态传递；更重要的是**探测结果（serverUrl）
        ///   只有这里知道**，绑在一起可以避免把 URL 到处传。
        ///
        /// 【探测怎么算"可达"】
        ///   对 `md5.txt`（热更 dll 目录下的校验清单）发一次 GET，
        ///   超时 <see cref="ProbeTimeoutSeconds"/> 秒。判定：
        ///     · HTTP 200 且内容非空 → 可达
        ///     · 其它（超时 / DNS 失败 / 404 / 5xx）→ 不可达
        ///   选 `md5.txt` 而不是根路径，是因为它是"这次热更真正需要的东西" ——
        ///   根路径可能返回 200（比如 nginx 默认页），但热更目录其实没部署。
        ///   探测的**结果**顺带被复用：可达时下载器马上会再拉一次，
        ///   代价是一次很小的请求，换来逻辑上的强保证。
        ///
        /// 【不可达时的行为 —— 需求第 2 条的核心】
        ///   什么都不做，直接返回。后续 LoadAssembliesCo 会从
        ///   persistentDataPath / StreamingAssets 读到本地已有的 dll，
        ///   游戏**完全正常启动**。整个过程只多花最多 4 秒（一次探测超时）。
        /// ==================================================================
        /// </summary>
        private IEnumerator ProbeAndDownloadDllsCo()
        {
            const string ServerUrlForAOT = "http://10.0.2.2:8000";   // ★ 必须与 ResServerConfig.ServerUrl 一致（模拟器 NAT 网关；真机换局域网 IP，改这里 + ResServerConfig 两处同步）

            SetStatus("正在检查资源服务器…");
            SetProgress(0.02f);

            // 允许用 persistentDataPath/server.txt 覆盖（与 ResServerConfig 的约定一致），
            // 这样换服务器时**不用重新打包 dll 链路的地址**。
            string serverUrl = ReadServerOverride() ?? ServerUrlForAOT;

            if (string.IsNullOrEmpty(serverUrl))
            {
                Debug.Log("[Boot] 未配置服务器地址，跳过 dll 热更（使用本地资源）");
                yield break;
            }

            // ---------- ① 探测 ----------
            bool reachable = false;
            string probeError = null;
            yield return StartCoroutine(ProbeServerCo(serverUrl, r => reachable = r, e => probeError = e));

            if (reachable == false)
            {
                // 【关键】不可达 = 正常情况（离线玩、服务器没开），**绝不阻塞启动**
                Debug.LogWarning("[Boot] 资源服务器不可达（" + (probeError ?? "未知原因")
                    + "），跳过热更，使用本地资源正常启动。");
                SetProgress(0.17f);
                yield break;
            }

            // ---------- ② 可达 → 执行 dll 热更 ----------
            SetStatus("正在同步热更 dll…");
            HotUpdateDllDownloader.Result result = null;

            yield return StartCoroutine(HotUpdateDllDownloader.DownloadAll(
                serverUrl,
                (done, total) =>
                {
                    SetProgress(total > 0 ? 0.02f + 0.13f * ((float)done / total) : 0.15f);
                    SetStatus(string.Format("同步热更 dll {0}/{1}", done, total));
                },
                r => result = r));

            if (result == null)
            {
                Debug.LogWarning("[Boot] 热更 dll 同步未返回结果，按'无需更新'继续");
                yield break;
            }

            // ---------- ③ 结果日志（关键节点上报） ----------
            if (result.Updated)
            {
                Debug.Log("[Boot] 热更 dll 同步完成：" + result.ToSummary());
            }
            else if (string.IsNullOrEmpty(result.ErrorSummary))
            {
                // 全部已最新 / 服务器未部署 → 都是"无需更新"，属正常情况
                Debug.Log("[Boot] 热更 dll 无更新（" + result.ToSummary() + "），使用包内版本。");
            }

            if (string.IsNullOrEmpty(result.ErrorSummary) == false)
            {
                Debug.LogWarning(
                    "[Boot] 部分热更 dll 同步失败（不影响启动，将继续使用本地版本）：\n" +
                    result.ErrorSummary);
            }
        }

        /// <summary>
        /// 探测服务器可达性。
        ///
        /// 【探测目标为什么是 md5.txt】见 <see cref="ProbeAndDownloadDllsCo"/> 注释。
        /// 【为什么带重试】局域网下首次连接偶发失败（ARP 未预热 / Wi-Fi 唤醒），
        ///   给一次机会能显著降低"明明服务器开着却探测失败"的概率。
        ///   但**只重试一次**且不等退避 —— 探测必须快，不能让启动变慢。
        /// 【URL 平台目录】与下载器保持一致：{root}/{platform}/HybridCLR/md5.txt
        /// </summary>
        private IEnumerator ProbeServerCo(string serverRoot, Action<bool> onResult, Action<string> onError)
        {
            string root = serverRoot.TrimEnd('/');
            string url = string.Format("{0}/{1}/{2}/{3}",
                root, GetPlatformFolderForProbe(), "HybridCLR", "md5.txt");

            for (int attempt = 0; attempt <= ProbeRetryCount; attempt++)
            {
                float t0 = Time.realtimeSinceStartup;
                bool ok = false;
                string err = null;

                using (UnityWebRequest req = UnityWebRequest.Get(url))
                {
                    req.timeout = ProbeTimeoutSeconds;
                    req.downloadHandler = new DownloadHandlerBuffer();

                    yield return req.SendWebRequest();

                    if (req.result == UnityWebRequest.Result.Success
                        && req.responseCode == 200
                        && string.IsNullOrEmpty(req.downloadHandler.text) == false)
                    {
                        ok = true;
                    }
                    else
                    {
                        err = string.Format("{0}（HTTP {1}）", req.error, req.responseCode);
                    }
                }

                float elapsed = Time.realtimeSinceStartup - t0;

                if (ok)
                {
                    Debug.Log(string.Format("[Boot] 资源服务器可达（探测耗时 {0:F2}s）：{1}", elapsed, url));
                    onResult(true);
                    yield break;
                }

                Debug.LogWarning(string.Format("[Boot] 服务器探测失败（第 {0} 次，耗时 {1:F2}s）：{2}",
                    attempt + 1, elapsed, err));

                if (attempt < ProbeRetryCount)
                {
                    // 极短等待后重试（0.3s，不引入可观延迟）
                    float wake = Time.realtimeSinceStartup + 0.3f;
                    while (Time.realtimeSinceStartup < wake)
                    {
                        yield return null;
                    }
                }
                else
                {
                    if (onError != null)
                    {
                        onError(err);
                    }
                }
            }
        }

        /// <summary>
        /// 探测用的平台目录名。**必须与 HotUpdateDllDownloader.GetPlatformFolder 一致**
        /// （两处都是 AOT 私有方法，无法共享 —— 改一处务必改另一处）。
        /// </summary>
        private static string GetPlatformFolderForProbe()
        {
#if UNITY_ANDROID
            return "Android";
#elif UNITY_IOS
            return "iOS";
#elif UNITY_STANDALONE_WIN
            return "StandaloneWindows64";
#elif UNITY_STANDALONE_OSX
            return "StandaloneOSX";
#else
            return "Unknown";
#endif
        }

        /// <summary>读 persistentDataPath/server.txt 的第一行（跳过空行与 # 注释）。没有则返回 null。</summary>
        private static string ReadServerOverride()
        {
            try
            {
                string file = System.IO.Path.Combine(Application.persistentDataPath, "server.txt");
                if (System.IO.File.Exists(file) == false)
                {
                    return null;
                }

                string[] lines = System.IO.File.ReadAllLines(file);
                for (int i = 0; i < lines.Length; i++)
                {
                    string line = lines[i].Trim();
                    if (line.Length == 0 || line.StartsWith("#"))
                    {
                        continue;
                    }
                    return line.TrimEnd('/');
                }
            }
            catch (Exception)
            {
                // 读不到就当没覆盖，用常量地址
            }
            return null;
        }

        /// <summary>把 HotUpdateAssembler 的同步加载过程包成协程，逐步骤让出一帧。</summary>
        private IEnumerator LoadAssembliesCo(Action<int, int> onProgress,
            Action onDone, Action<Exception> onError)
        {
            Exception caught = null;
            Action<int, int> progressAdapter = (d, t) =>
            {
                // 借用一个可变盒子把进度传出去（协程内不能直接 yield 在回调里）
                _pendingProgress = d;
                _pendingTotal = t;
            };

            // 同步执行（放在独立线程会让 Unity API 不可用；dll 加载本身是纯 CPU 操作）
            try
            {
                HotUpdateAssembler.LoadHotUpdateAssemblies(progressAdapter);
            }
            catch (Exception e)
            {
                caught = e;
            }

            // 让出一帧，让 UI 刷新最后一次进度
            if (_pendingTotal > 0)
            {
                onProgress(_pendingProgress, _pendingTotal);
            }
            yield return null;

            if (caught != null)
            {
                onError(caught);
            }
            else
            {
                onDone();
            }
        }

        private int _pendingProgress;
        private int _pendingTotal;

        /// <summary>
        /// 输出启动阶段文案。**统一走 Console**（需求第 4 条的"关键日志上报"）。
        ///
        /// 【为什么这里不再有 UI 字段】原实现挂了 `UnityEngine.UI.Text` / `Slider`
        ///   两个 [SerializeField] 字段，但 Boot.unity 里它们**一直是 null**
        ///   （场景序列化值就是 fileID: 0），等于死代码；且 AOT 程序集引用 UGUI
        ///   与"统一 TMP"的约定相悖。启动期的可视反馈由热更侧的 HotUpdateView 负责
        ///   （它在 main 场景里，那时热更代码已加载完毕，可以用 TMP）。
        /// </summary>
        private void SetStatus(string text)
        {
            Debug.Log("[Boot] " + text);
        }

        /// <summary>
        /// 进度占位。保留方法是为了让启动链的调用点保持"有阶段、有进度"的形状，
        /// 将来若要恢复可视化，只需在此处接一个 UI 实现，**不改动业务代码**。
        /// </summary>
        private void SetProgress(float p)
        {
            _lastProgress = Mathf.Clamp01(p);
        }

        private float _lastProgress;
    }
}
