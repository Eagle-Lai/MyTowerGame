using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 背景视差（M4-4）：背景随相机移动得比棋盘慢，制造纵深。
    ///
    /// 【为什么用"跟随相机的百分比"而不是滚动 UV】
    ///   背景是一张静态 SpriteRenderer（Paper.png），不是平铺材质；
    ///   移动它的世界坐标是最省、也最不会出问题的做法（不涉及材质实例化）。
    ///
    /// 【为什么要 oversize】背景跟着相机走得更慢 ⇒ 相机移到棋盘边缘时，
    ///   背景会相对"落后"，露出后面的空白。放大一个系数把这点余量吃进去即可。
    ///   系数不需要精确 —— 只要够覆盖"相机可移动范围 × (1 - parallax)"。
    ///
    /// 【谁挂它】SceneMainBuilder 在生成 Background 时挂上并调用 Init（编辑期烘焙一次）；
    ///   运行时由 Awake 自举补调一次。
    ///   ★ 2026-10-16 修复：原先只有编辑期会调 Init，而 _ready 不参与序列化，
    ///   运行时恒为 false → 视差与 oversize 实际上从未生效。Awake 自举后恢复设计行为。
    /// </summary>
    public class BackgroundParallax : MonoBehaviour
    {
        /// <summary>视差强度：0 = 完全跟相机（无纵深感），1 = 完全不动（像贴在无限远）</summary>
        [Range(0f, 1f)]
        public float parallax = 0.85f;

        /// <summary>额外放大倍数，用来覆盖"背景落后于相机"露出的边缘</summary>
        public float oversize = 1.4f;

        /// <summary>背景基础透明度（与 SceneMainBuilder 里设的值保持一致）</summary>
        public float alpha = 0.55f;

        /// <summary>
        /// 背景基准缩放（与 SceneMainBuilder.BackgroundScale 同值，编辑期会覆盖写入）。
        /// ★ 2026-10-16：1.6 → 2.2 —— 相机取景改"底边 2 格留白"后最大缩小档视野更大，
        ///   旧值 1.6×1.4=2.24× 在 19.5:9 起会露出黑边；2.2×1.4=3.08× 可覆盖
        ///   16:9 全缩放档、19.5:9 至约 2.3× 缩档（21:9 全档需 ≈2.35，超出部分露深空底色）。
        /// </summary>
        public float baseScale = 2.2f;

        private Vector3 _basePos;
        private Vector3 _camStart;
        private Transform _cam;
        private bool _ready;

        /// <summary>由创建方调用一次完成初始化（不依赖 Awake 顺序）。可重复调用（幂等）。</summary>
        public void Init()
        {
            _basePos = transform.position;
            _cam = Camera.main != null ? Camera.main.transform : null;
            _camStart = _cam != null ? _cam.position : Vector3.zero;

            // 【为什么要"绝对值"而不是"乘当前值"】Init 会被调用两次
            //   （编辑期 SceneMainBuilder 一次 + 运行时 Awake 自举一次）；
            //   若按当前 scale 再乘一次 oversize 会双重放大（1.6→2.24→3.14 事故）。
            //   绝对值写法幂等：无论场景里存的是什么，结果恒为 baseScale × oversize。
            float s = Mathf.Max(0.01f, baseScale) * Mathf.Max(1f, oversize);
            Vector3 sc = transform.localScale;
            transform.localScale = new Vector3(s, s, sc.z);

            SpriteRenderer sr = GetComponent<SpriteRenderer>();
            if (sr != null)
            {
                Color c = sr.color;
                c.a = alpha;
                sr.color = c;
            }
            _ready = true;
        }

        private void Awake()
        {
            // 运行时自举（原因见类注释：_ready 不序列化，场景里的实例进运行时是 false）。
            if (!_ready)
            {
                Init();
            }
        }

        private void Update()
        {
            if (!_ready)
            {
                return;
            }
            if (_cam == null)
            {
                // 相机可能晚于背景出现（都在场景里，但创建顺序不定）
                _cam = Camera.main != null ? Camera.main.transform : null;
                if (_cam == null)
                {
                    return;
                }
                _camStart = _cam.position;
            }

            Vector3 d = _cam.position - _camStart;
            transform.position = _basePos + new Vector3(d.x, d.y, 0f) * (1f - Mathf.Clamp01(parallax));
        }
    }
}
