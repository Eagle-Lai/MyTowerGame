using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>UI 分层（与场景中 UICanvas 下的三个 Panel 节点一一对应）</summary>
    public enum UILayout
    {
        BgPanel,
        NormalPanel,
        TipsPanel,
    }

    /// <summary>
    /// UI 管理器（v2.1 重写）。
    ///
    /// 相对 v1.0 的改动：
    ///   - **去掉 AssetData / ResourcesManager 依赖**（这两个类已废弃，Resources 目录也不再使用）
    ///   - 界面加载改走 ResLoader（编辑器直读 / 真机 AB 同一套调用）
    ///   - 去掉 BaseView / BaseDisplayObject 那套"new 一个非 MonoBehaviour 的 View 对象"的设计：
    ///     它要求 View 是 `new()` 可构造的普通类，导致 View 拿不到 MonoBehaviour 生命周期、
    ///     也无法用 `transform.Find` 之外的方式引用子节点。现在 View 一律是挂在 prefab 上的
    ///     MonoBehaviour，由 UIManager 负责实例化与层级归属。
    ///
    /// 三层结构（场景中必须齐备，否则 UI 打不开）：
    ///   UICanvas(tag=UICanvas) ├─ BgPanel ├─ NormalPanel └─ TipsPanel
    /// </summary>
    public class UIManager : BaseManager<UIManager>
    {
        private RectTransform _uiCanvas;
        private readonly Dictionary<UILayout, RectTransform> _layers =
            new Dictionary<UILayout, RectTransform>();
        private readonly Dictionary<string, GameObject> _opened =
            new Dictionary<string, GameObject>();

        public RectTransform UICanvas
        {
            get
            {
                if (_uiCanvas == null)
                {
                    GameObject go = GameObject.FindGameObjectWithTag("UICanvas");
                    if (go == null)
                    {
                        Debug.LogError(
                            "[UI] 场景中找不到 Tag 为 UICanvas 的对象。" +
                            "请执行「Tools ▸ 塔防 ▸ 搭建 main 场景」自动创建，或手动给 Canvas 打上该 Tag。");
                        return null;
                    }
                    _uiCanvas = go.GetComponent<RectTransform>();
                }
                return _uiCanvas;
            }
        }

        public RectTransform GetLayer(UILayout type)
        {
            RectTransform rect;
            if (_layers.TryGetValue(type, out rect) && rect != null)
            {
                return rect;
            }

            RectTransform canvas = UICanvas;
            if (canvas == null)
            {
                return null;
            }
            Transform child = canvas.Find(type.ToString());
            if (child == null)
            {
                Debug.LogError(string.Format(
                    "[UI] UICanvas 下缺少子节点「{0}」，无法挂载界面", type));
                return null;
            }
            rect = child as RectTransform;
            _layers[type] = rect;
            return rect;
        }

        // ------------------------------------------------------------------
        // 打开 / 关闭
        // ------------------------------------------------------------------

        /// <summary>
        /// 打开一个界面 prefab（逻辑名对应 ResTable）。
        /// 已打开则直接返回原实例（不重复实例化）。
        /// </summary>
        public GameObject Open(string logicalName, UILayout layout)
        {
            GameObject exist;
            if (_opened.TryGetValue(logicalName, out exist))
            {
                if (exist != null)
                {
                    exist.SetActive(true);
                    return exist;
                }
                _opened.Remove(logicalName);
            }

            RectTransform parent = GetLayer(layout);
            if (parent == null)
            {
                return null;
            }

            GameObject go = ResLoader.Instance.Instantiate(logicalName, parent);
            if (go == null)
            {
                Debug.LogError(string.Format("[UI] 界面「{0}」实例化失败", logicalName));
                return null;
            }

            // 铺满所属层
            RectTransform rt = go.GetComponent<RectTransform>();
            if (rt != null)
            {
                rt.anchorMin = Vector2.zero;
                rt.anchorMax = Vector2.one;
                rt.offsetMin = Vector2.zero;
                rt.offsetMax = Vector2.zero;
                rt.localScale = Vector3.one;
            }
            _opened[logicalName] = go;
            return go;
        }

        /// <summary>打开并取组件</summary>
        public T Open<T>(string logicalName, UILayout layout) where T : Component
        {
            GameObject go = Open(logicalName, layout);
            if (go == null)
            {
                return null;
            }
            T comp = go.GetComponent<T>();
            if (comp == null)
            {
                Debug.LogError(string.Format(
                    "[UI] 界面「{0}」上没有 {1} 组件（prefab 可能没挂脚本）",
                    logicalName, typeof(T).Name));
            }
            return comp;
        }

        public void Close(string logicalName)
        {
            GameObject go;
            if (_opened.TryGetValue(logicalName, out go))
            {
                _opened.Remove(logicalName);
                if (go != null)
                {
                    ResLoader.Instance.ReleaseInstance(logicalName, go);
                }
            }
        }

        public T Get<T>(string logicalName) where T : Component
        {
            GameObject go;
            if (_opened.TryGetValue(logicalName, out go) && go != null)
            {
                return go.GetComponent<T>();
            }
            return null;
        }

        public bool IsOpen(string logicalName)
        {
            GameObject go;
            return _opened.TryGetValue(logicalName, out go) && go != null;
        }

        public override void OnDestroy()
        {
            base.OnDestroy();
            foreach (KeyValuePair<string, GameObject> kv in _opened)
            {
                if (kv.Value != null)
                {
                    Object.Destroy(kv.Value);
                }
            }
            _opened.Clear();
            _layers.Clear();
        }

        public string DumpDebugInfo()
        {
            return string.Format("[UI] 已打开界面 {0} 个：{1}", _opened.Count,
                string.Join("、", new List<string>(_opened.Keys).ToArray()));
        }
    }
}
