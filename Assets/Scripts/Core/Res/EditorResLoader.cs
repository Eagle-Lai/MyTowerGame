#if UNITY_EDITOR
using System;
using System.Text;
using UnityEngine;
using UnityEditor;

namespace FTProject
{
    /// <summary>
    /// 编辑器专用资源加载实现：直接用 AssetDatabase 读工程内资源。
    ///
    /// 为什么需要它：如果开发期也走真 AB，改一张图都要重新打一次包，
    /// 开发效率会崩。这是业界通行的"编辑器模拟模式"。
    ///
    /// 【时序约定】LoadAsync 也延迟一帧回调，与 BundleResLoader 行为一致。
    /// </summary>
    public class EditorResLoader : IResLoader, IHotUpdateLoader
    {
        private bool _ready;

        public bool IsReady
        {
            get { return _ready; }
        }

        public void Init(Action onDone)
        {
            Init(null, onDone);
        }

        public void Init(Action<float> onProgress, Action onDone)
        {
            // 编辑器直读模式没有任何"打包清单/依赖"要加载，初始化是**瞬时**的 ——
            // 如实回报 0 → 1，而不是编造一段假进度（假进度在真机上会露出马脚）。
            if (onProgress != null)
            {
                onProgress(0f);
            }
            _ready = true;
            Debug.Log("[Res] 使用编辑器直读模式（EditorResLoader）。如需验证真 AB 链路，" +
                      "请在 Player Settings 的 Scripting Define Symbols 中加入 FORCE_AB。");
            if (onProgress != null)
            {
                onProgress(1f);
            }
            ResLoaderRunner.NextFrame(onDone);
        }

        // ------------------------------------------------------------------
        // 加载
        // ------------------------------------------------------------------

        public T Load<T>(string logicalName) where T : UnityEngine.Object
        {
            ResAddress addr = ResTable.Get(logicalName);
            if (!addr.IsValid)
            {
                return null;
            }

            T asset = AssetDatabase.LoadAssetAtPath<T>(addr.EditorPath);
            if (asset == null)
            {
                LogLoadFailure<T>(logicalName, addr);
            }
            return asset;
        }

        public void LoadAsync<T>(string logicalName, Action<T> onDone) where T : UnityEngine.Object
        {
            T asset = Load<T>(logicalName);
            ResLoaderRunner.NextFrame(() =>
            {
                if (onDone != null)
                {
                    onDone(asset);
                }
            });
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
            //（怪物包是 0.5、塔是 0.8）。把它重置成 1 会让怪物直接大 2 倍，
            // 而且会让"配置表的 scale=1 表示保持美术原样"这个语义失效。
            // SetParent(parent, false) 本身已保留 local 值，不需要额外归一化。
            go.transform.SetParent(parent, false);
            go.transform.localPosition = Vector3.zero;
            go.transform.localRotation = Quaternion.identity;
        }

        // ------------------------------------------------------------------
        // 生命周期（编辑器直读无包概念，均为空操作）
        // ------------------------------------------------------------------

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

        public void Release(string logicalName)
        {
            // 编辑器直读模式无引用计数，空操作
        }

        public void ReleaseBundle(string bundleName)
        {
            // 编辑器直读模式无包概念，空操作
        }

        public void Preload(string[] logicalNames, Action onDone)
        {
            Preload(logicalNames, null, onDone);
        }

        public void Preload(string[] logicalNames, Action<float> onProgress, Action onDone)
        {
            if (logicalNames != null)
            {
                StringBuilder missing = new StringBuilder();
                int okCount = 0;
                for (int i = 0; i < logicalNames.Length; i++)
                {
                    string name = logicalNames[i];
                    ResAddress addr = ResTable.Get(name);
                    if (!addr.IsValid)
                    {
                        missing.Append("\n  · 未登记：" + name);
                        if (onProgress != null)
                        {
                            onProgress((i + 1) / (float)logicalNames.Length);
                        }
                        continue;
                    }
                    if (AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(addr.EditorPath) == null)
                    {
                        missing.Append("\n  · 文件不存在：" + name + "  →  " + addr.EditorPath);
                        if (onProgress != null)
                        {
                            onProgress((i + 1) / (float)logicalNames.Length);
                        }
                        continue;
                    }
                    okCount++;
                    if (onProgress != null)
                    {
                        onProgress((i + 1) / (float)logicalNames.Length);
                    }
                }

                if (missing.Length > 0)
                {
                    Debug.LogError(string.Format(
                        "[Res] 预加载自检发现 {0} 个资源不可用（可用 {1} 个）：{2}",
                        logicalNames.Length - okCount, okCount, missing));
                }
                else
                {
                    Debug.Log(string.Format("[Res] 预加载自检通过，共 {0} 个资源全部就绪。", okCount));
                }
            }
            // 空清单/全部跳过时上面循环一次都没回报，这里兜底到 100%（幂等，不违反单调）
            if (onProgress != null)
            {
                onProgress(1f);
            }
            ResLoaderRunner.NextFrame(onDone);
        }

        public string DumpDebugInfo()
        {
            return string.Format("[Res] EditorResLoader：共登记 {0} 条资源地址（编辑器直读，无 AB 加载）。",
                CountKeys());
        }

        // ------------------------------------------------------------------
        // 热更新（IHotUpdateLoader）—— 编辑器直读没有远端概念
        // ------------------------------------------------------------------

        /// <summary>
        /// 编辑器直读模式没有"远端版本/差异下载"，直接判定为"无需更新"。
        /// 【为什么也要实现】不实现的话 UI 侧必须写 `#if USE_YOOASSET`，
        /// 一旦漏写就是"编辑器能跑、打包编译不过"。
        /// </summary>
        public void StartCheckUpdate(
            Action<string> onPhase,
            Action<int, int> onProgress,
            Action<long, long> onBytes,
            Action<string> onError,
            Action<bool> onDone)
        {
            Debug.Log("[Res] EditorResLoader 无热更新能力（编辑器直读），跳过资源更新检查。");
            if (onPhase != null) onPhase("编辑器模式：无需更新资源");
            ResLoaderRunner.NextFrame(() =>
            {
                if (onDone != null) onDone(false);
            });
        }

        public void PauseDownload()
        {
            // 无下载可暂停
        }

        public void ResumeDownload()
        {
            // 无下载可继续
        }

        public bool IsDownloading { get { return false; } }

        public bool IsPaused { get { return false; } }

        // ------------------------------------------------------------------
        // 工具
        // ------------------------------------------------------------------

        private static int CountKeys()
        {
            int n = 0;
            foreach (string unused in ResTable.AllKeys)
            {
                n++;
            }
            return n;
        }

        private static void LogLoadFailure<T>(string logicalName, ResAddress addr) where T : UnityEngine.Object
        {
            string typeName = typeof(T).Name;

            // 对 Sprite 给出更有针对性的排查提示
            if (typeof(T) == typeof(Sprite))
            {
                Texture2D tex = AssetDatabase.LoadAssetAtPath<Texture2D>(addr.EditorPath);
                if (tex != null)
                {
                    Debug.LogError(string.Format(
                        "[Res] 资源「{0}」是图片，但未以 Sprite 形式导入，无法作为 Sprite 加载。\n" +
                        "  路径：{1}\n" +
                        "  修复：选中该图片 → Inspector 顶部 Texture Type 改为「Sprite (2D and UI)」→ Apply",
                        logicalName, addr.EditorPath));
                    return;
                }
            }

            if (typeof(T) == typeof(TextAsset))
            {
                // 踩过的坑：StreamingAssets 下的文件被 Unity 当作"原始文件"处理，
                // 不导入成 TextAsset —— LoadAssetAtPath<Object> 能拿到，<TextAsset> 拿不到。
                bool inStreamingAssets = addr.EditorPath.StartsWith("Assets/StreamingAssets/");
                Debug.LogError(string.Format(
                    "[Res] 文本资源「{0}」加载失败。\n" +
                    "  路径：{1}\n" +
                    "  常见原因：\n" +
                    "   ① 文件扩展名不是 .json/.txt/.bytes，或未被识别为 TextAsset\n" +
                    "   ② {2}\n" +
                    "  修复：确认该路径在普通 Assets 目录下（配置表应为 Assets/ConfigJson/，\n" +
                    "        由 Luban/gen_code_json.bat 导出）",
                    logicalName, addr.EditorPath,
                    inStreamingAssets
                        ? "★该文件在 StreamingAssets 下 —— 这类文件不会被导入成 TextAsset，必须移到普通 Assets 目录"
                        : "文件不存在（先执行对应的生成脚本）"));
                return;
            }

            Debug.LogError(string.Format(
                "[Res] 加载失败：逻辑名「{0}」→ 类型 {1}\n  期望路径：{2}\n" +
                "  排查：①文件是否存在 ②类型是否匹配 ③是否已被移出 Assets 目录",
                logicalName, typeName, addr.EditorPath));
        }
    }
}
#endif
