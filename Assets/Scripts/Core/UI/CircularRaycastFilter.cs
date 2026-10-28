using UnityEngine;

namespace FTProject
{
    /// <summary>Matches round action buttons without readable textures or alpha-test memory.</summary>
    [DisallowMultipleComponent, RequireComponent(typeof(RectTransform))]
    public sealed class CircularRaycastFilter : MonoBehaviour, ICanvasRaycastFilter
    {
        private RectTransform _rect;

        public bool IsRaycastLocationValid(Vector2 screenPoint, Camera eventCamera)
        {
            if (_rect == null) _rect = (RectTransform)transform;
            Vector2 local;
            if (!RectTransformUtility.ScreenPointToLocalPointInRectangle(_rect, screenPoint, eventCamera, out local)) return false;
            Rect bounds = _rect.rect;
            if (bounds.width <= 0 || bounds.height <= 0) return false;
            Vector2 delta = local - bounds.center;
            float x = delta.x / (bounds.width * .5f), y = delta.y / (bounds.height * .5f);
            return x * x + y * y <= 1f;
        }
    }
}
