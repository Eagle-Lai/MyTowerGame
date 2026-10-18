using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// Fit page content between the header and footer, leaving LoopListView2's cached local
    /// viewport and item dimensions unchanged. Scaling an ancestor preserves that coordinate system.
    /// </summary>
    [DisallowMultipleComponent, RequireComponent(typeof(RectTransform))]
    public sealed class UIResponsivePage : MonoBehaviour
    {
        public enum PageKind { MainMenu, Select, TowerCodex }
        [SerializeField] private PageKind page;
        private RectTransform _panel;
        private RectTransform _list;
        private RectTransform _viewport;
        private RectTransform _left;
        private RectTransform _right;
        private RectTransform[] _menu;
        private Vector2 _lastSize = new Vector2(-1f, -1f);
        private static readonly string[] MenuNames = { "Logo", "GameTitle", "Subtitle", "StartBtn", "CodexBtn", "SettingBtn" };
        private static readonly float[] MenuY = { 270f, 83f, 9f, -66f, -184f, -302f };

        public void Configure(PageKind kind) { page = kind; _panel = null; _lastSize = new Vector2(-1f, -1f); }
        private void OnEnable() { Refresh(); }
        private void LateUpdate() { Refresh(); }

        public void Refresh()
        {
            if (_panel == null)
            {
                _panel = transform.Find("Panel") as RectTransform;
                if (_panel == null) return;
                _list = _panel.Find("List") as RectTransform;
                _viewport = _panel.Find("List/Viewport") as RectTransform;
                _left = _panel.Find("LeftBtn") as RectTransform;
                _right = _panel.Find("RightBtn") as RectTransform;
                _menu = new RectTransform[MenuNames.Length];
                for (int i = 0; i < _menu.Length; i++) _menu[i] = _panel.Find(MenuNames[i]) as RectTransform;
            }
            Vector2 size = _panel.rect.size;
            if (size.x <= 0f || size.y <= 0f || size == _lastSize) return;
            _lastSize = size;
            FitTextWidth("Title", 1400f, size.x);
            FitTextWidth("CodexTitle", 1400f, size.x);
            FitTextWidth("Summary", 1400f, size.x);
            if (page == PageKind.MainMenu)
            {
                // Baseline column bounds [-348,460], with 80 top and 192 bottom reserved.
                float scale = Mathf.Clamp01(Mathf.Min((size.y - 272f) / 808f, (size.x - 64f) / 1000f));
                for (int i = 0; i < _menu.Length; i++)
                {
                    if (_menu[i] == null) continue;
                    _menu[i].localScale = new Vector3(scale, scale, 1f);
                    _menu[i].anchoredPosition = new Vector2(0f, 56f + (MenuY[i] - 56f) * scale);
                }
            }
            else if (page == PageKind.Select && _viewport != null)
            {
                float top = size.y * 0.5f - 262f;
                float bottom = -size.y * 0.5f + 172f;
                float scale = Mathf.Clamp01(Mathf.Min((size.x - 432f) / 1150f, (top - bottom) / 550f));
                float center = Mathf.Clamp(0f, bottom + 275f * scale, top - 275f * scale);
                _viewport.localScale = new Vector3(scale, scale, 1f);
                _viewport.anchoredPosition = new Vector2(-575f * scale, center);
                MoveArrows(center + 10f);
            }
            else if (page == PageKind.TowerCodex && _list != null)
            {
                float top = size.y * 0.5f - 140f;
                float bottom = -size.y * 0.5f + 210f;
                float scale = Mathf.Clamp01(Mathf.Min((size.x - 380f) / 1300f, (top - bottom) / 640f));
                float center = Mathf.Clamp(-10f, bottom + 320f * scale, top - 320f * scale);
                _list.localScale = new Vector3(scale, scale, 1f);
                _list.anchoredPosition = new Vector2(0f, center);
                MoveArrows(center);
            }
        }

        private void FitTextWidth(string name, float maximum, float width)
        {
            RectTransform text = _panel.Find(name) as RectTransform;
            if (text != null) text.SetSizeWithCurrentAnchors(RectTransform.Axis.Horizontal, Mathf.Min(maximum, Mathf.Max(0f, width - 64f)));
        }

        private void MoveArrows(float y)
        {
            if (_left != null) _left.anchoredPosition = new Vector2(_left.anchoredPosition.x, y);
            if (_right != null) _right.anchoredPosition = new Vector2(_right.anchoredPosition.x, y);
        }
    }
}
