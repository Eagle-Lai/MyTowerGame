using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 射程提示圈（M2-C2）。世界空间 SpriteRenderer，跟随"正在放置的塔"或"当前选中的塔"。
    ///
    /// 【为什么是常驻单例，而不是每次 Instantiate / 归还对象池】
    ///   圈全场景只需要一个，切换塔型时改 scale 与 position 即可。
    ///   一旦引入"创建/销毁"或"池化"，就要处理资源释放、事件时序、
    ///   面板与放置态互相覆盖等一堆边界情况 —— 收益为零，风险不小。
    ///
    /// 【为什么不做成 prefab】做成 prefab 就多一个必须在 Unity 里生成的资产，
    ///   而这一步在本机（不开编辑器）是做不到的。改为**运行时按贴图建 GameObject**，
    ///   ResTable 里只登记一张 Range_Ring.png，纯代码即可交付。
    ///
    /// 【缩放为什么按精灵原生尺寸折算】贴图 256×256、PPU=100 → 原生 2.56 世界单位，
    ///   而目标直径是 2 × radius。直接令 scale = 直径会大 2.56 倍。
    ///   与 CellView.Setup 同一套做法：scale = 目标直径 / 原生直径。
    ///   这样以后换任何分辨率的圈图都不用改代码。
    /// </summary>
    public class RangeIndicatorView : MonoBehaviour
    {
        /// <summary>全局唯一实例。未创建 / 资源缺失时为 null，调用方必须容忍。</summary>
        public static RangeIndicatorView Instance { get; private set; }

        /// <summary>ResTable 逻辑名</summary>
        public const string LogicalName = "Range_Ring";

        /// <summary>圈的颜色：半透明白，避免盖住格子与塔</summary>
        private static readonly Color RingColor = new Color(1f, 1f, 1f, 0.55f);

        private SpriteRenderer _sr;
        private float _nativeDiameter = 1f;
        private bool _ready;

        /// <summary>
        /// 取（必要时创建）射程圈实例。
        /// 【失败时返回 null 而不是抛异常】占位美术还没生成时，射程圈属于"锦上添花"，
        /// 不该把玩法一起拖下水 —— 与工程 §3.5「功能缺失不应阻塞」一致。
        /// </summary>
        public static RangeIndicatorView Ensure()
        {
            if (Instance != null)
            {
                return Instance;
            }

            Sprite sp = ResLoader.Instance.Load<Sprite>(LogicalName);
            if (sp == null)
            {
                return null;
            }

            GameObject go = new GameObject("RangeIndicator");
            SpriteRenderer sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sp;
            sr.sortingOrder = BoardSorting.RangeIndicator;   // 已预留 100：格子之上、怪物之下
            sr.color = RingColor;

            RangeIndicatorView v = go.AddComponent<RangeIndicatorView>();
            v._sr = sr;
            v._nativeDiameter = Mathf.Max(sp.bounds.size.x, sp.bounds.size.y);
            v._ready = true;
            Instance = v;
            go.SetActive(false);
            return v;
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                Instance = null;
            }
        }

        /// <summary>显示一个以 center 为圆心、半径 radiusWorld（世界单位）的圈。</summary>
        public void Show(Vector2 center, float radiusWorld)
        {
            if (!_ready || radiusWorld <= 0f)
            {
                Hide();
                return;
            }
            if (!gameObject.activeSelf)
            {
                gameObject.SetActive(true);
            }
            float diameter = radiusWorld * 2f;
            float s = _nativeDiameter > 0.0001f ? diameter / _nativeDiameter : diameter;
            transform.localScale = new Vector3(s, s, 1f);
            transform.position = new Vector3(center.x, center.y, 0f);
        }

        public void Hide()
        {
            if (_ready && gameObject.activeSelf)
            {
                gameObject.SetActive(false);
            }
        }
    }
}
