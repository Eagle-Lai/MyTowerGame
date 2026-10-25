using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>Owns only the card's preview. LoopListView2 user data remains owned by SelectView.</summary>
    [DisallowMultipleComponent]
    public sealed class SelectLevelItemView : MonoBehaviour
    {
        private sealed class Entry { public Sprite Sprite; public int References; }
        private static readonly Dictionary<string, Entry> Loaded = new Dictionary<string, Entry>();
        private static readonly HashSet<string> Missing = new HashSet<string>();
        private Image _preview;
        private Image _placeholder;
        private TMP_Text _label;
        private string _heldKey;
        public int BoundLevelId { get; private set; }
        public TMP_Text Label { get { BindNodes(); return _label; } }
        public Image Preview { get { BindNodes(); return _preview; } }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetSession() { Loaded.Clear(); Missing.Clear(); }

        private void BindNodes()
        {
            if (_preview == null)
            {
                Transform node = transform.Find("Body/MapPreview/Image");
                if (node != null) _preview = node.GetComponent<Image>();
            }
            if (_label == null)
            {
                Transform node = transform.Find("Body/Label");
                if (node != null) _label = node.GetComponent<TMP_Text>();
                if (node != null)
                {
                    // This is formatted dynamic text, never a static localization key.
                    TextLocalizer localizer = node.GetComponent<TextLocalizer>();
                    if (localizer != null) localizer.enabled = false;
                }
            }
            if (_placeholder == null)
            {
                Transform node = transform.Find("Body/MapPreview/Placeholder");
                if (node != null) _placeholder = node.GetComponent<Image>();
            }
        }

        public void Bind(int levelId)
        {
            BindNodes();
            if (BoundLevelId == levelId && _heldKey != null) return;
            ReleasePreview();
            BoundLevelId = levelId;
            if (_preview == null) return;
            _preview.preserveAspect = true;
            _preview.raycastTarget = false;
            string key = LevelPreviewCatalog.LogicalName(levelId);
            if (!ResLoader.Instance.IsReady || Missing.Contains(key)) return;
            ResAddress address;
            if (!ResTable.TryGet(key, out address)) { WarnMissing(key); return; }
#if UNITY_EDITOR
            // Missing development images are expected while authoring new levels.
            if (!System.IO.File.Exists(address.EditorPath)) { WarnMissing(key); return; }
#endif
            Entry entry;
            if (!Loaded.TryGetValue(key, out entry))
            {
                Sprite sprite = ResLoader.Instance.Load<Sprite>(key);
                if (sprite == null) { ResLoader.Instance.Release(key); WarnMissing(key); return; }
                entry = new Entry { Sprite = sprite };
                Loaded.Add(key, entry);
            }
            entry.References++;
            _heldKey = key;
            _preview.sprite = entry.Sprite;
            _preview.enabled = true;
            if (_placeholder != null) _placeholder.enabled = false;
        }

        private static void WarnMissing(string key)
        {
            if (Missing.Add(key)) Debug.LogWarning("[LevelPreview] Missing preview; showing placeholder: " + key);
        }

        private void OnDisable() { ReleasePreview(); BoundLevelId = 0; }
        private void OnDestroy() { ReleasePreview(); }
        private void ReleasePreview()
        {
            if (_preview != null) { _preview.sprite = null; _preview.enabled = false; }
            if (_placeholder != null) _placeholder.enabled = true;
            if (_heldKey == null) return;
            Entry entry;
            if (Loaded.TryGetValue(_heldKey, out entry) && --entry.References == 0)
            {
                Loaded.Remove(_heldKey);
                ResLoader.Instance.Release(_heldKey);
            }
            _heldKey = null;
        }
    }
}
