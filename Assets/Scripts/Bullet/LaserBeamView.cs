using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 激光束表现（M2-W3）。**纯表现**，不含任何伤害逻辑 ——
    /// 伤害已经在 BaseTower.Fire 里当场结算（hitscan）。
    ///
    /// 【为什么复用 Bullet_Dot 而不是新增 Laser_Beam.png】
    ///   新增一张贴图就意味着"必须先在 Unity 里跑一次占位美术生成器"才能看到效果；
    ///   而把现成的白色圆点沿 X 拉长，视觉上就是一条光束 —— 零新增资产即可联调。
    ///   将来美术给了正式光束图，只需改下面的 LogicalName（或 ResTable 一行）。
    ///
    /// 【为什么用固定大小的池而不是每次 new GameObject】
    ///   激光塔射速不低，每次开火都创建/销毁会产生持续的托管堆分配，
    ///   在"200 怪 + 50 塔"的压测目标下会被放大。固定 8 条足够覆盖同屏观感，
    ///   超出的会复用最旧的一条（视觉上等价于"更早的那条已经消失了"）。
    /// </summary>
    public class LaserBeamView : MonoBehaviour
    {
        private const string LogicalName = "Bullet_Dot";
        private const int PoolSize = 8;
        private const float LifeSec = 0.06f;
        /// <summary>光束粗细（世界单位）。竖着看就是这条线的宽度。</summary>
        private const float Thickness = 0.10f;

        private static readonly Color BeamColor = new Color(1f, 0.45f, 0.45f, 0.9f);

        private static LaserBeamView _instance;

        private SpriteRenderer[] _srs;
        private float[] _life;
        private int _next;
        private float _nativeSize = 1f;
        private bool _ready;

        /// <summary>画一条从 from 到 to 的光束。贴图缺失时静默跳过（伤害不受影响）。</summary>
        public static void Fire(Vector2 from, Vector2 to)
        {
            if (_instance == null)
            {
                _instance = Create();
                if (_instance == null)
                {
                    return;
                }
            }
            _instance.Show(from, to);
        }

        private static LaserBeamView Create()
        {
            Sprite sp = ResLoader.Instance.Load<Sprite>(LogicalName);
            if (sp == null)
            {
                return null;
            }
            GameObject root = new GameObject("LaserBeams");
            LaserBeamView v = root.AddComponent<LaserBeamView>();
            v.Init(sp);
            return v;
        }

        private void Init(Sprite sp)
        {
            _nativeSize = Mathf.Max(0.0001f, Mathf.Max(sp.bounds.size.x, sp.bounds.size.y));
            _srs = new SpriteRenderer[PoolSize];
            _life = new float[PoolSize];
            for (int i = 0; i < PoolSize; i++)
            {
                GameObject go = new GameObject("Beam" + i);
                go.transform.SetParent(transform, false);
                SpriteRenderer sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = sp;
                sr.sortingOrder = BoardSorting.Bullet + 1;   // 压在弹体之上
                sr.color = BeamColor;
                go.SetActive(false);
                _srs[i] = sr;
            }
            _ready = true;
        }

        private void OnDestroy()
        {
            if (_instance == this)
            {
                _instance = null;
            }
        }

        private void Show(Vector2 from, Vector2 to)
        {
            if (!_ready)
            {
                return;
            }
            Vector2 d = to - from;
            float len = d.magnitude;
            if (len < 0.01f)
            {
                return;
            }

            int i = _next;
            _next = (_next + 1) % PoolSize;

            SpriteRenderer sr = _srs[i];
            Transform t = sr.transform;
            t.position = new Vector3((from.x + to.x) * 0.5f, (from.y + to.y) * 0.5f, 0f);
            t.rotation = Quaternion.Euler(0f, 0f, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg);
            // 缩放按贴图原生尺寸折算（与 CellView / RangeIndicatorView 同一套做法）
            t.localScale = new Vector3(len / _nativeSize, Thickness / _nativeSize, 1f);
            sr.color = BeamColor;
            sr.gameObject.SetActive(true);
            _life[i] = LifeSec;
        }

        private void Update()
        {
            if (!_ready)
            {
                return;
            }
            float dt = Time.deltaTime;
            for (int i = 0; i < _srs.Length; i++)
            {
                if (_life[i] <= 0f)
                {
                    continue;
                }
                _life[i] -= dt;
                if (_life[i] <= 0f)
                {
                    _life[i] = 0f;
                    _srs[i].gameObject.SetActive(false);
                    continue;
                }
                // 渐隐：短寿命 + 淡出，看起来才像"一闪而过"
                Color c = BeamColor;
                c.a *= _life[i] / LifeSec;
                _srs[i].color = c;
            }
        }
    }
}
