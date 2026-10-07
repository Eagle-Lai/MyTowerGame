using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 减速光环表现（减速塔 / 美术名 Retard）。**纯表现**，不含任何减速逻辑 ——
    /// 减速已在 BaseTower.TickSlowAura 里当场结算到每个敌人身上。
    ///
    /// 【为什么需要它】改造前减速是"打中某只怪才减速"，玩家能靠子弹轨迹理解；
    /// 改成范围光环后，如果没有可见的范围提示，玩家会疑惑
    /// "这塔到底管多大范围、到底有没有生效"。所以给两样东西：
    ///   ① 常亮的射程圈（浅蓝）—— 明确"谁在范围内"
    ///   ② 每次结算时的一次脉冲（圈短暂变亮）—— 明确"正在起作用"
    ///
    /// 【为什么复用 Range_Ring 而不是新增贴图】
    ///   与 LaserBeamView 同一考量：新增贴图就必须先在编辑器里跑一次占位美术生成，
    ///   而把现成的圈图换个颜色/透明度就是"光环"。零新增资产即可联调。
    ///   将来美术给了正式光环图，改 LogicalName 一行即可。
    ///
    /// 【为什么挂在塔的 transform 下而不是全局单例】
    ///   射程圈是**每座塔各一个**（同屏可能有多座减速塔），
    ///   挂在塔下能随塔自动销毁、自动跟随位置，省掉一套生命周期管理。
    /// </summary>
    public class SlowAuraView : MonoBehaviour
    {
        /// <summary>ResTable 逻辑名（与射程提示圈共用"圈图"）</summary>
        public const string LogicalName = "Range_Ring";

        /// <summary>常亮射程圈颜色：偏冷的浅蓝 —— 与减速的语义呼应，也和白色射程提示圈区分开</summary>
        private static readonly Color RingColor = new Color(0.55f, 0.8f, 1f, 0.30f);

        /// <summary>脉冲时叠加到的亮度（0~1 之间插值）</summary>
        private static readonly Color PulseColor = new Color(0.75f, 0.92f, 1f, 0.72f);

        /// <summary>排序：压在格子之上、怪物之下（与 RangeIndicator 同一层，避免穿帮）</summary>
        private const int SortingOrder = BoardSorting.RangeIndicator;

        private SpriteRenderer _sr;
        private float _nativeDiameter = 1f;
        private float _radius = 1f;
        private bool _ready;

        /// <summary>
        /// 在指定塔的 transform 下挂一个光环表现。贴图缺失时返回 null（不阻塞玩法）。
        /// </summary>
        public static SlowAuraView Attach(Transform towerRoot, float radiusWorld)
        {
            if (towerRoot == null)
            {
                return null;
            }

            Sprite sp = ResLoader.Instance.Load<Sprite>(LogicalName);
            if (sp == null)
            {
                return null;   // 占位美术未生成：静默跳过，减速逻辑照常生效
            }

            GameObject go = new GameObject("SlowAura");
            go.transform.SetParent(towerRoot, false);
            SpriteRenderer sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sp;
            sr.sortingOrder = SortingOrder;
            sr.color = RingColor;

            SlowAuraView v = go.AddComponent<SlowAuraView>();
            v._sr = sr;
            v._nativeDiameter = Mathf.Max(sp.bounds.size.x, sp.bounds.size.y);
            v._ready = true;
            v.SetRadius(radiusWorld);
            return v;
        }

        /// <summary>设置光环半径（世界单位）。塔升级换实例时会重新 Attach，这里也能改。</summary>
        public void SetRadius(float radiusWorld)
        {
            _radius = Mathf.Max(0.01f, radiusWorld);
            ApplyScale();
        }

        /// <summary>整体显示/隐藏（塔换成非减速塔型时关掉）</summary>
        public void SetVisible(bool visible)
        {
            if (_ready && _sr != null && _sr.gameObject.activeSelf != visible)
            {
                _sr.gameObject.SetActive(visible);
            }
        }

        /// <summary>脉冲强度 0~1（1 = 刚命中，0 = 完全平息）。由 BaseTower.TickVisual 每帧推进。</summary>
        public void SetPulse(float k)
        {
            if (!_ready || _sr == null)
            {
                return;
            }
            float t = Mathf.Clamp01(k);
            _sr.color = Color.Lerp(RingColor, PulseColor, t);
        }

        private void ApplyScale()
        {
            if (!_ready || _sr == null)
            {
                return;
            }
            // 与 RangeIndicatorView / CellView 同一套折算：scale = 目标直径 / 贴图原生直径
            float diameter = _radius * 2f;
            float s = _nativeDiameter > 0.0001f ? diameter / _nativeDiameter : diameter;
            // ★ 塔根节点通常有 0.8 缩放，而本节点是它的子节点 ——
            //   因此这里必须换算回本地尺度，否则光环会比实际射程小 20%，
            //   而射程判定用的是世界单位（Config.RadiusWorld），两者就会对不上。
            Vector3 ps = transform.parent != null ? transform.parent.lossyScale : Vector3.one;
            float px = Mathf.Abs(ps.x) > 0.0001f ? Mathf.Abs(ps.x) : 1f;
            float py = Mathf.Abs(ps.y) > 0.0001f ? Mathf.Abs(ps.y) : 1f;
            transform.localScale = new Vector3(s / px, s / py, 1f);
            transform.localPosition = Vector3.zero;   // 与塔同心
        }
    }
}
