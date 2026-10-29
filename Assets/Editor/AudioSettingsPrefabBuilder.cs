using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject.EditorTools
{
    /// <summary>Extends only the authored settings dialog and preserves its identity and skin.</summary>
    public static class AudioSettingsPrefabBuilder
    {
        public static void Apply(GameObject root)
        {
            var panel = root.transform.Find("Panel") as RectTransform;
            if (panel == null) return;
            panel.anchorMin = panel.anchorMax = panel.pivot = new Vector2(.5f, .5f);
            panel.anchoredPosition = Vector2.zero; panel.sizeDelta = new Vector2(940, 860);
            if (panel.GetComponent<UIFitInParent>() == null) panel.gameObject.AddComponent<UIFitInParent>();
            Place(panel.Find("Title") as RectTransform, 0, 354, 800, 66);
            Place(panel.Find("LanguageText") as RectTransform, -250, 258, 310, 56);
            Place(panel.Find("LanguageDropdown") as RectTransform, 165, 258, 440, 64);
            string[] names = { "Master", "Music", "Sfx" };
            string[] keys = { "Master Volume", "Music Volume", "SFX Volume" };
            var template = panel.Find("Title").GetComponent<TMP_Text>();
            for (int i = 0; i < names.Length; i++)
            {
                float y = 144 - i * 112;
                Label(panel, "Audio" + names[i] + "Label", keys[i], template, -220, y + 24, 370, 48);
                Label(panel, "Audio" + names[i] + "Value", "", template, 335, y + 24, 110, 48).alignment = TextAlignmentOptions.Right;
                var rect = Node(panel, "Audio" + names[i] + "Slider");
                Place(rect, 0, y - 24, 760, 46);
                var hit = rect.GetComponent<Image>() ?? rect.gameObject.AddComponent<Image>(); hit.color = Color.clear; hit.raycastTarget = true;
                var slider = rect.GetComponent<Slider>() ?? rect.gameObject.AddComponent<Slider>();
                var bg = Image(rect, "Track", new Color(.08f, .12f, .18f)); Stretch(bg.rectTransform, new Vector2(0, .38f), new Vector2(1, .62f));
                var fillArea = Node(rect, "FillArea"); Stretch(fillArea, new Vector2(0, .38f), new Vector2(1, .62f));
                var oldFill = rect.Find("Fill"); if (oldFill != null) oldFill.SetParent(fillArea, false);
                var fill = Image(fillArea, "Fill", new Color(.21f, .88f, 1)); Stretch(fill.rectTransform, Vector2.zero, Vector2.one);
                // Slider drives the handle's anchors to stretch vertically; a zero-height rail keeps its visual height fixed.
                var handleArea = Node(rect, "HandleArea"); Stretch(handleArea, new Vector2(0, .5f), new Vector2(1, .5f));
                handleArea.offsetMin = new Vector2(16, 0); handleArea.offsetMax = new Vector2(-16, 0);
                var oldHandle = rect.Find("Handle"); if (oldHandle != null) oldHandle.SetParent(handleArea, false);
                var handle = Image(handleArea, "Handle", new Color(.91f, .95f, 1));
                handle.rectTransform.anchorMin = handle.rectTransform.anchorMax = new Vector2(0, .5f);
                handle.rectTransform.pivot = new Vector2(.5f, .5f);
                handle.rectTransform.anchoredPosition = Vector2.zero;
                handle.rectTransform.sizeDelta = new Vector2(28, 38);
                slider.minValue = 0; slider.maxValue = 1; slider.wholeNumbers = false;
                slider.fillRect = fill.rectTransform; slider.handleRect = handle.rectTransform; slider.targetGraphic = handle;
                slider.direction = Slider.Direction.LeftToRight; slider.SetValueWithoutNotify(i == 1 ? .65f : .8f);
                if (rect.GetComponent<AudioSliderFeedback>() == null) rect.gameObject.AddComponent<AudioSliderFeedback>();
            }
            var mute = Node(panel, "AudioMuteToggle"); Place(mute, 0, -242, 760, 60);
            var toggle = mute.GetComponent<Toggle>() ?? mute.gameObject.AddComponent<Toggle>();
            var muteHit = mute.GetComponent<Image>() ?? mute.gameObject.AddComponent<Image>(); muteHit.color = Color.clear; muteHit.raycastTarget = true;
            var box = Image(mute, "Box", new Color(.08f, .12f, .18f)); Place(box.rectTransform, 348, 0, 54, 54);
            var check = Image(box.transform, "Check", new Color(.21f, .88f, 1)); Place(check.rectTransform, 0, 0, 32, 32);
            Label(mute, "AudioMuteLabel", "Mute", template, -180, 0, 400, 54);
            toggle.targetGraphic = box; toggle.graphic = check; toggle.SetIsOnWithoutNotify(false);
            Place(panel.Find("ResetBtn") as RectTransform, -210, -347, 380, 76);
            Place(panel.Find("CloseBtn") as RectTransform, 210, -347, 380, 76);
            // Popup template must render above the audio controls when opened.
            panel.Find("LanguageDropdown").SetAsLastSibling();
        }

        private static RectTransform Node(Transform parent, string name)
        {
            var existing = parent.Find(name) as RectTransform;
            if (existing != null) return existing;
            var go = new GameObject(name, typeof(RectTransform)); go.transform.SetParent(parent, false); return (RectTransform)go.transform;
        }
        private static TMP_Text Label(Transform parent, string name, string text, TMP_Text template, float x, float y, float w, float h)
        {
            var rect = Node(parent, name); Place(rect, x, y, w, h);
            var label = rect.GetComponent<TMP_Text>() ?? rect.gameObject.AddComponent<TextMeshProUGUI>();
            label.font = template.font; label.fontSharedMaterial = template.fontSharedMaterial;
            label.text = text; label.color = template.color; label.fontSize = 30; label.enableAutoSizing = true;
            label.fontSizeMin = 24; label.fontSizeMax = 30; label.alignment = TextAlignmentOptions.Left;
            label.margin = new Vector4(16, 6, 16, 6); label.overflowMode = TextOverflowModes.Ellipsis;
            label.raycastTarget = false;
            var localizer = label.GetComponent<TextLocalizer>(); if (localizer != null) Object.DestroyImmediate(localizer);
            return label;
        }
        private static Image Image(Transform parent, string name, Color color)
        {
            var rect = Node(parent, name); var image = rect.GetComponent<Image>() ?? rect.gameObject.AddComponent<Image>();
            image.color = color; image.raycastTarget = true; return image;
        }
        private static void Place(RectTransform r, float x, float y, float w, float h)
        {
            if (r == null) return;
            r.anchorMin = r.anchorMax = r.pivot = new Vector2(.5f, .5f);
            r.anchoredPosition = new Vector2(x, y); r.sizeDelta = new Vector2(w, h); r.localScale = Vector3.one;
        }
        private static void Stretch(RectTransform r, Vector2 min, Vector2 max)
        { r.anchorMin = min; r.anchorMax = max; r.offsetMin = r.offsetMax = Vector2.zero; }
    }
}
