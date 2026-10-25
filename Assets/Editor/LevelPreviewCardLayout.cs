using System;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject.EditorTools
{
    /// <summary>Shared by targeted prefab migration and normal UI generation.</summary>
    public static class LevelPreviewCardLayout
    {
        public const string PrefabPath = "Assets/Prefabs/UI/SelectLevelItem.prefab";

        public static void Apply(GameObject root)
        {
            Transform body = root.transform.Find("Body");
            if (body == null) throw new InvalidOperationException("SelectLevelItem is missing Body");
            Transform labelNode = body.Find("Label");
            if (labelNode == null) throw new InvalidOperationException("SelectLevelItem is missing Body/Label");
            var label = labelNode.GetComponent<TextMeshProUGUI>();
            var labelRect = (RectTransform)labelNode;
            labelRect.anchorMin = new Vector2(.61f, 0f); labelRect.anchorMax = Vector2.one;
            labelRect.offsetMin = new Vector2(18f, 48f); labelRect.offsetMax = new Vector2(-38f, -48f);
            label.enableWordWrapping = true; label.overflowMode = TextOverflowModes.Ellipsis;
            label.raycastTarget = false;
            TextLocalizer localizer = labelNode.GetComponent<TextLocalizer>();
            if (localizer != null) localizer.enabled = false;

            RectTransform frame = Child(body, "MapPreview");
            frame.anchorMin = new Vector2(0f, .5f); frame.anchorMax = new Vector2(0f, .5f);
            frame.pivot = new Vector2(0f, .5f); frame.anchoredPosition = new Vector2(40f, 0f);
            frame.sizeDelta = new Vector2(650f, 390f);
            Image background = frame.GetComponent<Image>() ?? frame.gameObject.AddComponent<Image>();
            background.color = new Color(.055f, .085f, .13f, .95f); background.raycastTarget = false;

            RectTransform placeholder = Child(frame, "Placeholder");
            Stretch(placeholder, 14f);
            Image placeholderImage = placeholder.GetComponent<Image>() ?? placeholder.gameObject.AddComponent<Image>();
            ResAddress address;
            if (ResTable.TryGet("Cell_Ground", out address))
                placeholderImage.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(address.EditorPath);
            placeholderImage.color = new Color(.25f, .32f, .42f, .45f);
            placeholderImage.type = Image.Type.Tiled; placeholderImage.raycastTarget = false;

            RectTransform imageRect = Child(frame, "Image");
            Stretch(imageRect, 10f);
            Image image = imageRect.GetComponent<Image>() ?? imageRect.gameObject.AddComponent<Image>();
            image.color = Color.white; image.type = Image.Type.Simple; image.preserveAspect = true;
            image.raycastTarget = false; image.sprite = null; image.enabled = false;
            if (root.GetComponent<SelectLevelItemView>() == null) root.AddComponent<SelectLevelItemView>();
        }

        private static RectTransform Child(Transform parent, string name)
        {
            Transform existing = parent.Find(name);
            if (existing != null) return (RectTransform)existing;
            var node = new GameObject(name, typeof(RectTransform));
            node.layer = parent.gameObject.layer; node.transform.SetParent(parent, false);
            return (RectTransform)node.transform;
        }
        private static void Stretch(RectTransform rect, float inset)
        {
            rect.anchorMin = Vector2.zero; rect.anchorMax = Vector2.one;
            rect.offsetMin = Vector2.one * inset; rect.offsetMax = Vector2.one * -inset;
        }

        [MenuItem("Tools/塔防/关卡地图预览/更新选关卡片布局")]
        public static void UpdatePrefab()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
                throw new InvalidOperationException("Update the prefab in Edit Mode");
            GameObject root = PrefabUtility.LoadPrefabContents(PrefabPath);
            try { Apply(root); PrefabUtility.SaveAsPrefabAsset(root, PrefabPath); }
            finally { PrefabUtility.UnloadPrefabContents(root); }
            Debug.Log("[LevelPreview] Updated only SelectLevelItem; existing prefab properties preserved.");
        }
    }
}
