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
    /// 【谁挂它】SceneMainBuilder 在生成 Background 时挂上；
    ///   若场景是老的（没这个组件），GameFlowManager 会在初始化时补挂（见 EnsureParallax）。
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

        private Vector3 _basePos;
        private Vector3 _camStart;
        private Transform _cam;
        private Vector3 _baseScale;
        private bool _ready;

        /// <summary>由创建方调用一次完成初始化（不依赖 Awake 顺序）。</summary>
        public void Init()
        {
            _basePos = transform.position;
            _baseScale = transform.localScale;
            _cam = Camera.main != null ? Camera.main.transform : null;
            _camStart = _cam != null ? _cam.position : Vector3.zero;
            transform.localScale = _baseScale * Mathf.Max(1f, oversize);

            SpriteRenderer sr = GetComponent<SpriteRenderer>();
            if (sr != null)
            {
                Color c = sr.color;
                c.a = alpha;
                sr.color = c;
            }
            _ready = true;
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
