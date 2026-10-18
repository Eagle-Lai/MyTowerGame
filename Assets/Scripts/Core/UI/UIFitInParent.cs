using UnityEngine;

namespace FTProject
{
    /// <summary>Only shrink a fixed-size dialog when its safe-area parent cannot contain it.</summary>
    [DisallowMultipleComponent, RequireComponent(typeof(RectTransform))]
    public sealed class UIFitInParent : MonoBehaviour
    {
        [SerializeField] private Vector2 padding = new Vector2(24f, 24f);
        private RectTransform _rect;
        private Vector2 _lastParentSize;
        private Vector2 _lastSize;

        private void OnEnable() { Refresh(); }
        private void LateUpdate() { Refresh(); }

        public void Refresh()
        {
            if (_rect == null) _rect = (RectTransform)transform;
            RectTransform parent = _rect.parent as RectTransform;
            if (parent == null) return;
            Vector2 available = parent.rect.size;
            Vector2 size = _rect.rect.size;
            if (available.x <= 0f || available.y <= 0f || size.x <= 0f || size.y <= 0f) return;
            float scale = Mathf.Clamp01(Mathf.Min((available.x - 2f * padding.x) / size.x,
                (available.y - 2f * padding.y) / size.y));
            if (_lastParentSize == available && _lastSize == size &&
                Mathf.Approximately(_rect.localScale.x, scale)) return;
            _lastParentSize = available;
            _lastSize = size;
            _rect.localScale = new Vector3(scale, scale, 1f);
        }
    }
}
