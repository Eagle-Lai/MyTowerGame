using UnityEngine;

namespace FTProject
{
    /// <summary>Keep the mask on the full canvas while its sibling controls inherit the safe area.</summary>
    [DisallowMultipleComponent, RequireComponent(typeof(RectTransform))]
    public sealed class UIFullScreenBackground : MonoBehaviour
    {
        private readonly Vector3[] _corners = new Vector3[4];
        private RectTransform _rect;

        private void OnEnable()
        {
            Canvas.willRenderCanvases += Refresh;
            Refresh();
        }

        private void OnDisable() { Canvas.willRenderCanvases -= Refresh; }

        public void Refresh()
        {
            if (_rect == null) _rect = (RectTransform)transform;
            RectTransform parent = _rect.parent as RectTransform;
            Canvas canvas = GetComponentInParent<Canvas>();
            if (parent == null || canvas == null) return;
            RectTransform screen = canvas.rootCanvas.transform as RectTransform;
            if (screen == null) return;
            screen.GetWorldCorners(_corners);
            Vector2 min = parent.InverseTransformPoint(_corners[0]);
            Vector2 max = parent.InverseTransformPoint(_corners[2]);
            Vector2 offsetMin = min - parent.rect.min;
            Vector2 offsetMax = max - parent.rect.max;
            if ((_rect.offsetMin - offsetMin).sqrMagnitude > 0.001f) _rect.offsetMin = offsetMin;
            if ((_rect.offsetMax - offsetMax).sqrMagnitude > 0.001f) _rect.offsetMax = offsetMax;
        }
    }
}
