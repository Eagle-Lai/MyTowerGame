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

                    // M4-1：安全区适配。
                    // 【为什么在这里自动补挂而不是要求重建场景】UICanvas 是按 Tag 在运行时找到的，
                    // 在这里补挂不需要改场景，老场景也能立刻生效 ——
                    // 否则每个已有工程都得重跑一次「搭建 main 场景」才不挡刘海。
                    if (_uiCanvas != null && _uiCanvas.GetComponent<SafeAreaFitter>() == null)
                    {
                        _uiCanvas.gameObject.AddComponent<SafeAreaFitter>();
                    }
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

            // 【引导期界面的兜底路径】开屏页 / 加载页必须在 ResLoader.Init **之前**就能显示 ——
            //   而 YooAsset 在 Init 完成前拒绝加载任何资源（"尚未初始化完成，无法加载"）。
            //   于是启动界面走 ResTable/YooAsset 是**先有鸡还是先有蛋**，必然失败。
            //   这类"引导期界面"改放 `Assets/Resources/BootUI/` 下：
            //     · Resources 不依赖任何资源系统初始化，Init 之前就能取到；
            //     · `Assets/Resources` 不在 BundleCollectorSetting 的收集目录里
            //       → 不会进任何 AB 包、也不会被热更替换（引导期界面本来就不该热更）。
            //   资源系统一旦就绪，同一个 UIManager.Open 仍走正常链路（下面前半段）。
            GameObject go = null;
            ResAddress addr;
            if (ResLoader.Instance.IsReady && ResTable.TryGet(logicalName, out addr))
            {
                go = ResLoader.Instance.Instantiate(logicalName, parent);
            }
            if (go == null)
            {
                go = InstantiateBootUi(logicalName, parent);
                if (go != null)
                {
                    _bootOpened.Add(logicalName);
                }
            }
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
            EnsureFadeIn(go);
            EnsureClickSfx(go);
            return go;
        }

        /// <summary>界面淡入时长（秒，走 unscaled 时间 —— 暂停界面是在 timeScale=0 下打开的）</summary>
        private const float FadeInSec = 0.12f;

        /// <summary>引导期界面的 Resources 相对目录（见 Open 里关于"先有鸡还是先有蛋"的说明）。</summary>
        private const string BootUiDir = "BootUI/";

        /// <summary>
        /// 记录哪些已打开界面是"引导期从 Resources 加载"的。
        /// 【为什么要单独记】这类实例不是 ResLoader 创建的，不能交给 ReleaseInstance
        /// （它会去 ResTable 查地址 → 查不到就报错，而且 YooAsset 那边也没有对应句柄）。
        /// 它们只由本类 Destroy。
        /// </summary>
        private readonly HashSet<string> _bootOpened = new HashSet<string>();

        /// <summary>
        /// 从 `Resources/BootUI/` 取引导期界面并实例化。取不到返回 null（由调用方报错）。
        /// 只有 3 个界面走这里：SplashView / LoadingView / HotUpdateView。
        /// </summary>
        private static GameObject InstantiateBootUi(string logicalName, Transform parent)
        {
            GameObject prefab = Resources.Load<GameObject>(BootUiDir + logicalName);
            if (prefab == null)
            {
                return null;
            }
            GameObject go = Object.Instantiate(prefab, parent, false);
            go.name = logicalName;
            Debug.Log(string.Format(
                "[UI] 资源系统尚未就绪，界面「{0}」从 Resources/{1} 以引导期模式加载", logicalName, BootUiDir));
            return go;
        }

        /// <summary>
        /// 给新打开的界面补一个淡入（M4-3）。
        ///
        /// 【为什么"自带 CanvasGroup 的界面就跳过"】TipsView 用 CanvasGroup 自己管淡入淡出，
        /// 我们再插一脚就会两边抢 alpha，表现为"提示一闪一闪"。
        /// 约定：prefab 自带 CanvasGroup ⇒ 该界面自己负责透明度，UIManager 不插手。
        /// 这样不改任何 prefab 就能给 M3 新界面加上转场。
        /// </summary>
        private static void EnsureFadeIn(GameObject go)
        {
            if (go == null || go.GetComponent<CanvasGroup>() != null)
            {
                return;
            }
            CanvasGroup cg = go.AddComponent<CanvasGroup>();
            UIFader fader = go.AddComponent<UIFader>();
            fader.Begin(cg, FadeInSec);
        }

        /// <summary>
        /// 给界面挂一个"全局点击音"（M4-W7）。已挂则跳过。
        ///
        /// 【为什么统一挂在这里，而不是让每个 View 自己播】
        ///   本项目按钮多且部分是运行时创建的（SelectView 每次显示都会重造关卡按钮）。
        ///   统一代管的收益是：新加按钮**自动**有声音，不用记得写、也不用全局搜字符串；
        ///   代价只是每个界面每 0.4 秒重扫一次按钮（见 <see cref="UiClickSfx"/>）。
        /// </summary>
        private static void EnsureClickSfx(GameObject go)
        {
            if (go == null || go.GetComponent<UiClickSfx>() != null)
            {
                return;
            }
            go.AddComponent<UiClickSfx>();
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
                    // 【为什么要先 SetActive(false)】Destroy 要到本帧末才真正生效。
                    // 而"切关"是在同一帧里 Close 旧的 + Open 新的（例如 HUD），
                    // 不先隐藏的话，同屏会短暂存在两份界面，且旧界面仍会响应事件。
                    go.SetActive(false);
                    if (_bootOpened.Remove(logicalName))
                    {
                        // 引导期界面不是 ResLoader 创建的 → 直接 Destroy，不走 ReleaseInstance
                        Object.Destroy(go);
                    }
                    else
                    {
                        ResLoader.Instance.ReleaseInstance(logicalName, go);
                    }
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
