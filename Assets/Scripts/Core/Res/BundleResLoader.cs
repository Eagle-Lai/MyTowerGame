using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Networking;

namespace FTProject
{
    /// <summary>
    /// AssetBundle 真机加载实现（P0-3）。
    ///
    /// 职责：
    ///   1. 启动时加载主清单（AssetBundleManifest），之后所有依赖查询由它回答
    ///   2. 按「包」为单位做引用计数 —— 粒度是关卡，不是单个资源
    ///      （单个资源频繁 ±1 会让 Unload 时机极难把握，是 AB 项目的经典坑）
    ///   3. 依赖自动补齐：加载 A 包前先把它的依赖全部加载
    ///   4. 常驻包（ResBundle.Persistent）永不卸载
    ///
    /// 【为什么不用 Assets/Resources】AB 支持热更、支持按需下载、启动快，
    /// 且能精确控制卸载时机；Resources 目录会被全量打进包体且无法增量更新。
    ///
    /// 【为什么编辑器下默认不用它】改一张图都要重新打 AB，开发效率不可接受。
    /// 编辑器走 EditorResLoader（AssetDatabase 直读），
    /// 需要验证真 AB 链路时在 Scripting Define Symbols 加 FORCE_AB。
    /// </summary>
    public class BundleResLoader : IResLoader
    {
        // ---- 包运行时状态 ----
        private readonly Dictionary<string, AssetBundle> _loaded = new Dictionary<string, AssetBundle>(32);
        /// <summary>包的"关卡引用"计数。只有 Preload 会 +1，ReleaseBundle 会 -1。</summary>
        private readonly Dictionary<string, int> _refCount = new Dictionary<string, int>(32);
        /// <summary>正在加载中的包（并发合并：同一包被多次请求只加载一次）</summary>
        private readonly HashSet<string> _loading = new HashSet<string>();

        // ---- 资源缓存 ----
        private readonly Dictionary<string, UnityEngine.Object> _assetCache =
            new Dictionary<string, UnityEngine.Object>(128);

        private AssetBundle _manifestBundle;
        private AssetBundleManifest _manifest;
        private bool _ready;

        /// <summary>异步加载失败时回调此事件（供 UI 提示）</summary>
        public static event Action<string> OnLoadError;

        public bool IsReady { get { return _ready; } }

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
            ResLoaderRunner.Start(InitCo(onDone));
        }

        private IEnumerator InitCo(Action onDone)
        {
            // ① 主清单包：包名与平台目录同名
            string manifestName = ResPathUtil.ManifestBundleName;
            yield return LoadBundleInternalCo(manifestName, null);

            _manifestBundle = GetLoaded(manifestName);
            if (_manifestBundle == null)
            {
                Fail(string.Format(
                    "[Res] 主清单加载失败：{0}\n" +
                    "  排查：①是否已执行「Tools ▸ 资源工具 ▸ 打包 AssetBundle」" +
                    "②平台子目录名是否与当前平台一致（当前应为 {1}）",
                    ResPathUtil.BundlePath(manifestName), ResPathUtil.PlatformFolder));
                if (onDone != null)
                {
                    onDone();
                }
                yield break;
            }

            _manifest = _manifestBundle.LoadAsset<AssetBundleManifest>("AssetBundleManifest");
            if (_manifest == null)
            {
                Fail("[Res] 主清单包内找不到 AssetBundleManifest 资产，包可能已损坏");
                if (onDone != null)
                {
                    onDone();
                }
                yield break;
            }

            // ② 常驻包（config / core_art）开机即加载
            for (int i = 0; i < ResBundle.Persistent.Length; i++)
            {
                AcquireBundle(ResBundle.Persistent[i]);
            }
            // 等所有正在加载的包落地
            while (_loading.Count > 0)
            {
                yield return null;
            }

            _ready = true;
            Debug.Log(string.Format(
                "[Res] AssetBundle 模式初始化完成。平台={0}，已加载包 {1} 个，常驻包 {2} 个。",
                ResPathUtil.PlatformFolder, _loaded.Count, ResBundle.Persistent.Length));

            if (onDone != null)
            {
                onDone();
            }
        }

        // ==================================================================
        // 包管理
        // ==================================================================

        /// <summary>
        /// 获取一个包的"关卡引用"：引用计数 +1，并确保包与其全部依赖已加载。
        /// 与 <see cref="ReleaseBundle"/> 严格配对。
        /// </summary>
        public void AcquireBundle(string bundleName)
        {
            if (string.IsNullOrEmpty(bundleName))
            {
                return;
            }
            int c;
            _refCount.TryGetValue(bundleName, out c);
            _refCount[bundleName] = c + 1;

            if (_loaded.ContainsKey(bundleName) || _loading.Contains(bundleName))
            {
                return;
            }
            ResLoaderRunner.Start(LoadBundleWithDepsCo(bundleName));
        }

        /// <summary>加载一个包及其全部依赖（依赖先加载）</summary>
        private IEnumerator LoadBundleWithDepsCo(string bundleName)
        {
            string[] deps = GetDependencies(bundleName);
            for (int i = 0; i < deps.Length; i++)
            {
                // 依赖包也计入引用，避免被提前卸载
                int c;
                _refCount.TryGetValue(deps[i], out c);
                _refCount[deps[i]] = c + 1;

                if (!_loaded.ContainsKey(deps[i]) && !_loading.Contains(deps[i]))
                {
                    yield return LoadBundleInternalCo(deps[i], null);
                }
            }
            yield return LoadBundleInternalCo(bundleName, null);
        }

        private string[] GetDependencies(string bundleName)
        {
            if (_manifest == null)
            {
                return new string[0];
            }
            string[] deps = _manifest.GetAllDependencies(bundleName);
            return deps ?? new string[0];
        }

        private AssetBundle GetLoaded(string bundleName)
        {
            AssetBundle b;
            return _loaded.TryGetValue(bundleName, out b) ? b : null;
        }

        /// <summary>真正加载一个包（不含依赖处理）。同一包并发请求会被合并。</summary>
        private IEnumerator LoadBundleInternalCo(string bundleName, Action<AssetBundle> onDone)
        {
            if (_loaded.ContainsKey(bundleName))
            {
                if (onDone != null)
                {
                    onDone(_loaded[bundleName]);
                }
                yield break;
            }
            if (_loading.Contains(bundleName))
            {
                // 合并并发请求：等别人加载完
                while (_loading.Contains(bundleName))
                {
                    yield return null;
                }
                if (onDone != null)
                {
                    onDone(GetLoaded(bundleName));
                }
                yield break;
            }

            _loading.Add(bundleName);
            AssetBundle bundle = null;

            if (ResPathUtil.NeedWebRequest)
            {
                // Android：StreamingAssets 在 APK 内，必须走 UnityWebRequest
                using (UnityWebRequest req = UnityWebRequestAssetBundle.GetAssetBundle(
                           ResPathUtil.BundleUrl(bundleName)))
                {
                    yield return req.SendWebRequest();
                    if (req.result == UnityWebRequest.Result.Success)
                    {
                        bundle = DownloadHandlerAssetBundle.GetContent(req);
                    }
                    else
                    {
                        Fail(string.Format("[Res] 包「{0}」下载失败：{1}", bundleName, req.error));
                    }
                }
            }
            else
            {
                string path = ResPathUtil.BundlePath(bundleName);
                if (!File.Exists(path))
                {
                    Fail(string.Format(
                        "[Res] 包文件不存在：{0}\n  排查：是否已执行「Tools ▸ 资源工具 ▸ 打包 AssetBundle」",
                        path));
                }
                else
                {
                    AssetBundleCreateRequest req = AssetBundle.LoadFromFileAsync(path);
                    yield return req;
                    bundle = req.assetBundle;
                    if (bundle == null)
                    {
                        Fail(string.Format("[Res] 包「{0}」加载返回 null，文件可能损坏：{1}", bundleName, path));
                    }
                }
            }

            if (bundle != null)
            {
                _loaded[bundleName] = bundle;
            }
            _loading.Remove(bundleName);

            if (onDone != null)
            {
                onDone(bundle);
            }
        }

        /// <summary>
        /// 同步阻塞加载一个包及其依赖。**只应在调用方漏了 Preload 时作为兜底使用**，
        /// 正常流程一律走异步。
        /// </summary>
        private void LoadBundleBlocking(string bundleName)
        {
            if (_loaded.ContainsKey(bundleName))
            {
                return;
            }
            string[] deps = GetDependencies(bundleName);
            for (int i = 0; i < deps.Length; i++)
            {
                LoadSingleBundleBlocking(deps[i]);
            }
            LoadSingleBundleBlocking(bundleName);
        }

        private void LoadSingleBundleBlocking(string bundleName)
        {
            if (_loaded.ContainsKey(bundleName))
            {
                return;
            }
            if (ResPathUtil.NeedWebRequest)
            {
                Fail(string.Format(
                    "[Res] 包「{0}」在本平台只能异步加载（StreamingAssets 位于包内），" +
                    "请改用 LoadAsync/Preload。", bundleName));
                return;
            }
            string path = ResPathUtil.BundlePath(bundleName);
            if (!File.Exists(path))
            {
                Fail(string.Format("[Res] 包文件不存在：{0}", path));
                return;
            }
            AssetBundle bundle = AssetBundle.LoadFromFile(path);
            if (bundle == null)
            {
                Fail(string.Format("[Res] 包「{0}」同步加载失败：{1}", bundleName, path));
                return;
            }
            _loaded[bundleName] = bundle;
        }

        // ==================================================================
        // 加载接口
        // ==================================================================

        public T Load<T>(string logicalName) where T : UnityEngine.Object
        {
            UnityEngine.Object cached;
            if (_assetCache.TryGetValue(logicalName, out cached) && cached != null)
            {
                return cached as T;
            }

            ResAddress addr = ResTable.Get(logicalName);
            if (!addr.IsValid)
            {
                return null;
            }

            AssetBundle bundle = GetLoaded(addr.Bundle);
            if (bundle == null)
            {
                // 同步兜底：调用方漏了 Preload。这里会阻塞主线程，
                // 所以一定要打警告把它暴露出来，而不是静默接受。
                Debug.LogWarning(string.Format(
                    "[Res] 包「{0}」尚未加载，正在同步阻塞加载（应在进关卡前 Preload，否则会掉帧）：{1}",
                    addr.Bundle, logicalName));
                LoadBundleBlocking(addr.Bundle);
                bundle = GetLoaded(addr.Bundle);
            }
            if (bundle == null)
            {
                return null;
            }

            return LoadFromBundle<T>(logicalName, addr, bundle);
        }

        private T LoadFromBundle<T>(string logicalName, ResAddress addr, AssetBundle bundle) where T : UnityEngine.Object
        {
            T asset = bundle.LoadAsset<T>(addr.Asset);
            if (asset == null)
            {
                // 兜底：资产名可能带扩展名，用全量资产表再找一次
                UnityEngine.Object[] all = bundle.LoadAllAssets();
                for (int i = 0; i < all.Length; i++)
                {
                    if (all[i] != null && all[i].name == addr.Asset)
                    {
                        asset = all[i] as T;
                        break;
                    }
                }
            }
            if (asset == null)
            {
                Fail(string.Format(
                    "[Res] 包内找不到资产：包={0} 资产={1}（逻辑名 {2}）\n" +
                    "  排查：ABNameSetter 是否把该资源打进了正确的包、asset 名是否与文件名一致",
                    addr.Bundle, addr.Asset, logicalName));
                return null;
            }
            _assetCache[logicalName] = asset;
            return asset;
        }

        public void LoadAsync<T>(string logicalName, Action<T> onDone) where T : UnityEngine.Object
        {
            ResLoaderRunner.Start(LoadAsyncCo<T>(logicalName, onDone));
        }

        private IEnumerator LoadAsyncCo<T>(string logicalName, Action<T> onDone) where T : UnityEngine.Object
        {
            UnityEngine.Object cached;
            if (_assetCache.TryGetValue(logicalName, out cached) && cached != null)
            {
                yield return null;
                if (onDone != null)
                {
                    onDone(cached as T);
                }
                yield break;
            }

            ResAddress addr = ResTable.Get(logicalName);
            if (!addr.IsValid)
            {
                if (onDone != null)
                {
                    onDone(null);
                }
                yield break;
            }

            AcquireBundle(addr.Bundle);
            while (_loading.Count > 0)
            {
                yield return null;
            }

            AssetBundle bundle = GetLoaded(addr.Bundle);
            T asset = bundle != null ? LoadFromBundle<T>(logicalName, addr, bundle) : null;
            // 与编辑器实现保持一致：至少延迟一帧再回调，避免业务写出依赖同步返回的代码
            yield return null;
            if (onDone != null)
            {
                onDone(asset);
            }
        }

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

        /// <summary>
        /// 释放单个资源的缓存引用（**不卸载包**）。
        /// 包级生命周期由 ReleaseBundle 管理，见接口注释。
        /// </summary>
        public void Release(string logicalName)
        {
            _assetCache.Remove(logicalName);
        }

        /// <summary>
        /// 整包释放：引用计数 -1，归零后 Unload(false)。
        /// 依赖包的引用也一并归还。
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

            ReleaseRef(bundleName);

            string[] deps = GetDependencies(bundleName);
            for (int i = 0; i < deps.Length; i++)
            {
                ReleaseRef(deps[i]);
            }

            // 清理该包下资源的缓存引用（包卸载后这些 Object 必然失效）
            List<string> keys = ResTable.GetKeysByBundle(bundleName);
            for (int i = 0; i < keys.Count; i++)
            {
                _assetCache.Remove(keys[i]);
            }

            Resources.UnloadUnusedAssets();
        }

        private void ReleaseRef(string bundleName)
        {
            int c;
            if (!_refCount.TryGetValue(bundleName, out c))
            {
                return;
            }
            c--;
            if (c > 0)
            {
                _refCount[bundleName] = c;
                return;
            }
            _refCount.Remove(bundleName);

            if (IsPersistent(bundleName))
            {
                return;
            }

            AssetBundle bundle;
            if (_loaded.TryGetValue(bundleName, out bundle))
            {
                _loaded.Remove(bundleName);
                if (bundle != null)
                {
                    // ★ unloadAllLoadedObjects 必须为 false：
                    // 传 true 会把仍在场景中使用的 Texture/Mesh 一起销毁，导致花屏/丢失
                    bundle.Unload(false);
                }
            }
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

        public void Preload(string[] logicalNames, Action onDone)
        {
            ResLoaderRunner.Start(PreloadCo(logicalNames, onDone));
        }

        private IEnumerator PreloadCo(string[] logicalNames, Action onDone)
        {
            if (logicalNames != null)
            {
                // 收集涉及的包（去重），逐一取得关卡引用
                HashSet<string> bundles = new HashSet<string>();
                for (int i = 0; i < logicalNames.Length; i++)
                {
                    ResAddress addr = ResTable.Get(logicalNames[i]);
                    if (addr.IsValid)
                    {
                        bundles.Add(addr.Bundle);
                    }
                    else
                    {
                        Fail(string.Format("[Res] 预加载发现未登记的逻辑名：{0}", logicalNames[i]));
                    }
                }
                foreach (string b in bundles)
                {
                    AcquireBundle(b);
                }
                while (_loading.Count > 0)
                {
                    yield return null;
                }

                // 预热资产（避免首次访问卡顿）
                int ok = 0;
                foreach (string name in logicalNames)
                {
                    ResAddress addr;
                    if (!ResTable.TryGet(name, out addr))
                    {
                        continue;
                    }
                    AssetBundle bundle = GetLoaded(addr.Bundle);
                    if (bundle != null && bundle.LoadAsset(addr.Asset) != null)
                    {
                        ok++;
                    }
                }
                Debug.Log(string.Format("[Res] 预加载完成：{0}/{1} 个资源就绪。", ok, logicalNames.Length));
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
            System.Text.StringBuilder sb = new System.Text.StringBuilder();
            sb.AppendLine(string.Format("[Res] BundleResLoader：已加载 {0} 个包，缓存 {1} 个资源",
                _loaded.Count, _assetCache.Count));
            foreach (KeyValuePair<string, AssetBundle> kv in _loaded)
            {
                int c;
                _refCount.TryGetValue(kv.Key, out c);
                sb.AppendLine(string.Format("  · {0,-18} ref={1}{2}",
                    kv.Key, c, IsPersistent(kv.Key) ? "（常驻）" : string.Empty));
            }
            return sb.ToString();
        }

        /// <summary>引用计数是否全部归零（除常驻包外）—— 泄漏自检用</summary>
        public bool HasLeak()
        {
            foreach (KeyValuePair<string, int> kv in _refCount)
            {
                if (kv.Value > 0 && !IsPersistent(kv.Key))
                {
                    return true;
                }
            }
            return false;
        }
    }
}
