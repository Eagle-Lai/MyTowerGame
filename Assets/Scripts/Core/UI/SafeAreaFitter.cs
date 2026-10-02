using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 安全区适配（M4-1）：把挂载的 RectTransform 收进 Screen.safeArea。
    ///
    /// 【为什么需要】刘海屏 / 挖孔屏 / 圆角屏会把屏幕四边一小条挡住。
    /// 不处理的话，HUD 左上角的「金币」正好会被刘海压住 —— 这是移动端最常见的一类"看不见的 bug"。
    ///
    /// 【为什么是改 anchor 而不是改 offset】
    ///   anchorMin/Max 表达的是"占屏幕的比例"，正好对应 safeArea 的定义；
    ///   而 offset 是像素量，换分辨率就要重算。用 anchor 一次写对，之后自适应。
    ///
    /// 【为什么要缓存上一次的值】Update 里每帧比较 Rect 是廉价的，
    ///   但 Apply 会触发 Canvas 重建（改 RectTransform 会影响布局），
    ///   每帧无脑调会在低端机上明显掉帧。
    ///
    /// 【谁挂它】UIManager 在解析到 UICanvas 时会自动补挂（见 UIManager.UICanvas），
    ///   这样不需要重建场景就能生效。
    /// </summary>
    [RequireComponent(typeof(RectTransform))]
    public class SafeAreaFitter : MonoBehaviour
    {
        private RectTransform _rt;
        private Rect _lastSafe;
        private int _lastW = -1;
        private int _lastH = -1;

        private void Awake()
        {
            _rt = GetComponent<RectTransform>();
            Apply();
        }

        private void Update()
        {
            if (Screen.width != _lastW || Screen.height != _lastH || Screen.safeArea != _lastSafe)
            {
                Apply();
            }
        }

        public void Apply()
        {
            if (_rt == null)
            {
                _rt = GetComponent<RectTransform>();
            }
            if (_rt == null || Screen.width <= 0 || Screen.height <= 0)
            {
                return;
            }

            Rect sa = Screen.safeArea;
            _lastSafe = sa;
            _lastW = Screen.width;
            _lastH = Screen.height;

            Vector2 min = sa.position;
            Vector2 max = sa.position + sa.size;
            min.x /= Screen.width;
            min.y /= Screen.height;
            max.x /= Screen.width;
            max.y /= Screen.height;

            _rt.anchorMin = min;
            _rt.anchorMax = max;
            _rt.offsetMin = Vector2.zero;
            _rt.offsetMax = Vector2.zero;
        }
    }
}
