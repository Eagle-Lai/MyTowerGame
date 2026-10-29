using System;
using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>Keeps authored sibling backplates behind their text without changing view binding paths.</summary>
    [ExecuteAlways, DisallowMultipleComponent]
    public sealed class UIContentSurfaces : MonoBehaviour
    {
        [Serializable]
        public struct Surface
        {
            public RectTransform content;
            public RectTransform background;
            public bool shared;
        }

        [SerializeField] private List<Surface> surfaces = new List<Surface>();
        public void Clear() { surfaces.Clear(); }
        public void Add(RectTransform content, RectTransform background, bool shared = false)
        { surfaces.Add(new Surface { content = content, background = background, shared = shared }); }
        public RectTransform BackingFor(RectTransform content)
        {
            foreach (var pair in surfaces) if (pair.content == content) return pair.background;
            return null;
        }
        private void OnEnable() { Refresh(); }
        private void LateUpdate() { Refresh(); }

        public void Refresh()
        {
            foreach (var pair in surfaces)
            {
                var source = pair.content;
                var plate = pair.background;
                if (source == null || plate == null) continue;
                // Shared plates retain their authored extent when individual rows are hidden.
                if (pair.shared) continue;
                bool visible = source.gameObject.activeSelf;
                if (plate.gameObject.activeSelf != visible) plate.gameObject.SetActive(visible);
                if (plate.anchorMin != source.anchorMin) plate.anchorMin = source.anchorMin;
                if (plate.anchorMax != source.anchorMax) plate.anchorMax = source.anchorMax;
                if (plate.pivot != source.pivot) plate.pivot = source.pivot;
                if (plate.anchoredPosition != source.anchoredPosition) plate.anchoredPosition = source.anchoredPosition;
                if (plate.sizeDelta != source.sizeDelta) plate.sizeDelta = source.sizeDelta;
                if (plate.localScale != source.localScale) plate.localScale = source.localScale;
            }
        }
    }
}
