using System;
using System.IO;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject.EditorTools
{
    /// <summary>Shared layout definitions for new prefabs and non-destructive updates to existing assets.</summary>
    public static class UIResolutionLayout
    {
        [MenuItem("Tools/塔防/高级（单步重建）/同步 UI 分辨率布局（保留现有资源）", false, 330)]
        public static void SyncExisting()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode) throw new InvalidOperationException("Stop Play Mode before updating UI assets.");
            int count = 0;
            foreach (string path in Directory.GetFiles("Assets/Prefabs/UI", "*.prefab"))
            {
                string assetPath = path.Replace('\\', '/');
                GameObject root = PrefabUtility.LoadPrefabContents(assetPath);
                try
                {
                    Apply(root);
                    PrefabUtility.SaveAsPrefabAsset(root, assetPath);
                    count++;
                }
                finally { PrefabUtility.UnloadPrefabContents(root); }
            }
            Debug.Log("[UIResolution] Updated " + count + " UI prefabs, retaining their GUIDs and existing components.");
        }

        public static void Apply(GameObject root)
        {
            string name = root.name;
            if (name == "TowerCodexItem")
            {
                FitText(root, "Body/TypeName", 28f, 40f, false);
                FitText(root, "Body/Role", 20f, 26f, false);
                foreach (string row in new[] { "DpsRow", "RangeRow", "SpeedRow", "PriceRow" })
                    FitText(root, "Body/" + row, 20f, 26f, false);
                FitText(root, "Body/DescText", 16f, 24f, true);
                RectTransform description = root.transform.Find("Body/DescText") as RectTransform;
                description.anchoredPosition = new Vector2(0f, -275f);
                description.sizeDelta = new Vector2(380f, 70f);
                return;
            }
            // Item roots belong to LoopListView2; boot screens retain their existing layout.
            if (!name.EndsWith("View", StringComparison.Ordinal) || name == "SplashView" || name == "LoadingView" || name == "HotUpdateView") return;
            RectTransform bg = root.transform.Find("Bg") as RectTransform;
            if (bg != null)
            {
                Stretch(bg);
                Ensure<UIFullScreenBackground>(bg.gameObject);
            }
            RectTransform panel = root.transform.Find("Panel") as RectTransform;
            if (panel != null && panel.anchorMin == panel.anchorMax)
            {
                Ensure<UIFitInParent>(panel.gameObject);
                // Convert each dialog button without changing its baseline rectangle.
                foreach (Transform child in panel)
                {
                    RectTransform rect = child as RectTransform;
                    if (rect == null || child.GetComponent<Button>() == null || rect.anchorMin != rect.anchorMax) continue;
                    Reanchor(rect, new Vector2(rect.anchorMin.x, 0f), panel.sizeDelta);
                }
            }
            if (name == "TipsView")
            {
                RectTransform bar = root.transform.Find("TipBar") as RectTransform;
                if (bar != null)
                {
                    bar.anchorMin = bar.anchorMax = new Vector2(0.5f, 1f);
                    bar.pivot = new Vector2(0.5f, 0.5f);
                    bar.anchoredPosition = new Vector2(0f, -263f);
                }
            }
            else if (name == "MainMenuView") Ensure<UIResponsivePage>(root).Configure(UIResponsivePage.PageKind.MainMenu);
            else if (name == "SelectView") Ensure<UIResponsivePage>(root).Configure(UIResponsivePage.PageKind.Select);
            else if (name == "TowerCodexView")
            {
                Ensure<UIResponsivePage>(root).Configure(UIResponsivePage.PageKind.TowerCodex);
                RectTransform title = panel.Find("CodexTitle") as RectTransform;
                title.anchorMin = title.anchorMax = new Vector2(0.5f, 1f);
                title.pivot = new Vector2(0.5f, 0.5f);
                title.anchoredPosition = new Vector2(0f, -68f);
                RectTransform viewport = panel.Find("List/Viewport") as RectTransform;
                viewport.anchorMin = viewport.anchorMax = new Vector2(0.5f, 0.5f);
                viewport.pivot = new Vector2(0f, 0.5f);
                viewport.anchoredPosition = new Vector2(-230f, 0f);
                viewport.sizeDelta = new Vector2(460f, 640f);
                RectTransform page = panel.Find("PageText") as RectTransform;
                page.anchorMin = page.anchorMax = new Vector2(0.5f, 0f);
                page.pivot = new Vector2(0.5f, 0.5f);
                page.anchoredPosition = new Vector2(0f, 184f);
            }
            else if (name == "SellConfirmView")
            {
                FitText(root, "Panel/TowerName", 28f, 36f, false);
                FitText(root, "Panel/WarnText", 24f, 30f, true);
                ((RectTransform)panel.Find("TowerName")).sizeDelta = new Vector2(740f, 52f);
                ((RectTransform)panel.Find("WarnText")).sizeDelta = new Vector2(700f, 88f);
            }
            else if (name == "GameIntroView")
            {
                for (int i = 1; i <= 4; i++) FitText(root, "Panel/Info" + i, 24f, 30f, true);
            }
            else if (name == "TowerInfoView") FitText(root, "Panel/Title", 28f, 40f, false);
        }

        private static void FitText(GameObject root, string path, float minimum, float maximum, bool wrap)
        {
            TMP_Text text = root.transform.Find(path).GetComponent<TMP_Text>();
            text.enableWordWrapping = wrap;
            text.enableAutoSizing = true;
            text.fontSizeMin = minimum;
            text.fontSizeMax = maximum;
            text.overflowMode = TextOverflowModes.Overflow;
        }

        private static T Ensure<T>(GameObject go) where T : Component
        {
            T component = go.GetComponent<T>();
            return component != null ? component : go.AddComponent<T>();
        }

        private static void Reanchor(RectTransform rect, Vector2 anchor, Vector2 parentSize)
        {
            Vector2 position = rect.anchoredPosition + Vector2.Scale(rect.anchorMin - anchor, parentSize);
            rect.anchorMin = rect.anchorMax = anchor;
            rect.anchoredPosition = position;
        }

        private static void Stretch(RectTransform rect)
        {
            rect.anchorMin = Vector2.zero;
            rect.anchorMax = Vector2.one;
            rect.offsetMin = rect.offsetMax = Vector2.zero;
        }
    }
}
