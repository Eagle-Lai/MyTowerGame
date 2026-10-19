using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Linq;
using SimpleJSON;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject.EditorTools
{
    /// <summary>Renders the shipped prefabs with real view bindings and fonts in an isolated test session.</summary>
    public static class BalanceUiVisualVerifier
    {
        private const int CaptureLayer = 31;
        private static readonly MethodInfo FillDetail = typeof(LevelDetailView).GetMethod("Fill", BindingFlags.Instance | BindingFlags.NonPublic);

        public static string CaptureAll(string outputDirectory)
        {
            if (!EditorApplication.isPlaying || !SaveManager.IsTestStorage || !Configs.IsLoaded || !LanguageManager.IsReady)
                throw new InvalidOperationException("UI capture requires a booted PlayMode scene with isolated balance-test storage.");
            outputDirectory = Path.GetFullPath(outputDirectory);
            Directory.CreateDirectory(outputDirectory);
            var results = new JSONArray();
            Language previousLanguage = LanguageManager.Current;
            GameObject stage = null;
            RenderTexture previousTarget = RenderTexture.active;
            try
            {
                stage = new GameObject("Balance UI capture (temporary)");
                stage.hideFlags = HideFlags.HideAndDontSave;
                var cameraObject = new GameObject("Capture camera"); cameraObject.transform.SetParent(stage.transform, false);
                Camera camera = cameraObject.AddComponent<Camera>(); camera.enabled = false;
                camera.orthographic = true; camera.clearFlags = CameraClearFlags.SolidColor;
                camera.backgroundColor = new Color(.035f, .06f, .10f); camera.cullingMask = 1 << CaptureLayer;
                camera.nearClipPlane = .1f; camera.farClipPlane = 2000f;
                camera.transform.localPosition = new Vector3(0, 0, -1000);
                foreach (var size in new[] { new Vector2Int(1920, 1080), new Vector2Int(1024, 768) })
                {
                    // Match the main scene CanvasScaler: 1920x1080 reference, width/height match=.5.
                    float scale = Mathf.Sqrt(size.x / 1920f * (size.y / 1080f));
                    Vector2 logicalSize = new Vector2(size.x / scale, size.y / scale);
                    camera.orthographicSize = logicalSize.y * .5f;
                    camera.aspect = (float)size.x / size.y;
                    var canvasObject = new GameObject("Actual prefab canvas", typeof(RectTransform), typeof(Canvas));
                    canvasObject.transform.SetParent(stage.transform, false); canvasObject.layer = CaptureLayer;
                    RectTransform canvasRect = (RectTransform)canvasObject.transform; canvasRect.sizeDelta = logicalSize;
                    Canvas canvas = canvasObject.GetComponent<Canvas>(); canvas.renderMode = RenderMode.WorldSpace;
                    canvas.worldCamera = camera; canvas.referencePixelsPerUnit = 100;
                    var target = new RenderTexture(size.x, size.y, 24, RenderTextureFormat.ARGB32);
                    target.Create(); camera.targetTexture = target;
                    try
                    {
                        foreach (Language language in new[] { Language.English, Language.ChineseSimplified, Language.ChineseTraditional })
                        {
                            LanguageManager.SetLanguage(language);
                            foreach (string scenario in new[] { "select-first", "select-last", "detail-L" + Configs.LevelTable.DataList.Max(l => l.Id), "clear-five", "clear-low", "clear-save-pending" })
                            {
                                bool detail = scenario.StartsWith("detail", StringComparison.Ordinal);
                                bool select = scenario.StartsWith("select", StringComparison.Ordinal);
                                string prefabName = select ? "SelectView" : detail ? "LevelDetailView" : "LevelClearView";
                                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/UI/" + prefabName + ".prefab");
                                if (prefab == null) throw new FileNotFoundException("Actual prefab missing: " + prefabName);
                                GameObject instance = UnityEngine.Object.Instantiate(prefab, canvasRect, false);
                                try
                                {
                                    SetLayer(instance.transform);
                                    var root = instance.GetComponent<RectTransform>();
                                    root.anchorMin = Vector2.zero; root.anchorMax = Vector2.one;
                                    root.offsetMin = Vector2.zero; root.offsetMax = Vector2.zero;
                                    if (detail) FillDetail.Invoke(instance.GetComponent<LevelDetailView>(), new object[] { Configs.LevelTable.DataList.Max(l => l.Id) });
                                    else if (!select) instance.GetComponent<LevelClearView>().Show(CreateClearFixture(scenario));
                                    if (select)
                                    {
                                        Canvas.ForceUpdateCanvases();
                                        var view = instance.GetComponent<SelectView>();
                                        typeof(SelectView).GetMethod("LateUpdate", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(view, null);
                                        typeof(SelectView).GetMethod("CenterOnIndexInstant", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(view,
                                            new object[] { scenario == "select-last" ? Configs.LevelTable.DataList.Count - 1 : 0 });
                                        typeof(SelectView).GetMethod("LateUpdate", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(view, null);
                                    }
                                    Canvas.ForceUpdateCanvases();
                                    foreach (var text in instance.GetComponentsInChildren<TMP_Text>(false)) text.ForceMeshUpdate(true, true);
                                    Canvas.ForceUpdateCanvases();
                                    string file = scenario + "-" + language.ToCode() + "-" + size.x + "x" + size.y + ".png";
                                    camera.Render(); RenderTexture.active = target;
                                    var image = new Texture2D(size.x, size.y, TextureFormat.RGB24, false);
                                    try
                                    {
                                        image.ReadPixels(new Rect(0, 0, size.x, size.y), 0, 0); image.Apply();
                                        File.WriteAllBytes(Path.Combine(outputDirectory, file), image.EncodeToPNG());
                                    }
                                    finally { UnityEngine.Object.DestroyImmediate(image); }
                                    JSONNode entry = Analyze(instance, camera);
                                    entry["scenario"] = scenario; entry["language"] = language.ToCode();
                                    entry["width"] = size.x; entry["height"] = size.y; entry["image"] = file;
                                    entry["prefab"] = AssetDatabase.GetAssetPath(prefab);
                                    if (select) { entry["campaignLevelCount"] = Configs.LevelTable.DataList.Count; entry["maximumStars"] = Configs.LevelTable.DataList.Count * 5; }
                                    results.Add(entry);
                                }
                                finally { UnityEngine.Object.DestroyImmediate(instance); }
                            }
                        }
                    }
                    finally
                    {
                        camera.targetTexture = null; RenderTexture.active = previousTarget;
                        target.Release(); UnityEngine.Object.DestroyImmediate(target);
                        UnityEngine.Object.DestroyImmediate(canvasObject);
                    }
                }
            }
            finally
            {
                RenderTexture.active = previousTarget;
                LanguageManager.SetLanguage(previousLanguage);
                if (stage != null) UnityEngine.Object.DestroyImmediate(stage);
            }
            JSONNode report = new JSONObject(); report["coverage"] = "Actual shipped prefabs and view bindings; synthetic settlement fixtures, not gameplay certification; 1920x1080 and 1024x768 using main CanvasScaler match=.5; safe-area/device input remains separate.";
            report["results"] = results; report["images"] = results.Count;
            File.WriteAllText(Path.Combine(outputDirectory, "ui-visual-results.json"), report.ToString(2), new System.Text.UTF8Encoding(false));
            return report.ToString();
        }

        private static LevelClearInfo CreateClearFixture(string scenario)
        {
            int lastLevel = Configs.LevelTable.DataList.Max(l => l.Id);
            var profile = Configs.GetLevelRating(lastLevel);
            if (profile == null) throw new InvalidOperationException("Final level rating is missing");
            bool low = scenario == "clear-low", pending = scenario == "clear-save-pending";
            var metrics = new LevelRunMetrics
            {
                runId = "ui-fixture-" + scenario, profileId = profile.profileId, profileRevision = profile.profileRevision,
                balanceRevision = profile.balanceRevision, ratingRevision = profile.ratingRevision, planHash = profile.planHash,
                expectedWaveCount = profile.expectedWaveCount, completedWaveCount = profile.expectedWaveCount,
                expectedEnemyCount = profile.expectedEnemyCount, successfulSpawned = profile.expectedEnemyCount,
                leaked = low ? 3 : 0, bossLeaked = low ? 1 : 0, criticalLeaked = low ? 2 : 0,
                killed = profile.expectedEnemyCount - (low ? 3 : 0), hp = low ? 1 : 20, maxHp = 20,
                victory = true, statisticsValid = true, timingValid = true,
                combatElapsedSeconds = profile.parCombatTimeMs / 1000d * (low ? 1.5d : 1d)
            };
            metrics.levelElapsedSeconds = metrics.combatElapsedSeconds + 95d;
            int remaining = profile.expectedEnemyCount;
            for (int i = 0; i < profile.expectedWaveCount; i++)
            {
                int expected = remaining / (profile.expectedWaveCount - i); remaining -= expected;
                int leaks = low && i == 0 ? 3 : 0;
                metrics.waves.Add(new WaveRunMetrics { ordinal = i + 1, expected = expected, successfulSpawned = expected,
                    killed = expected - leaks, leaked = leaks, bossLeaked = low && i == 0 ? 1 : 0,
                    criticalLeaked = low && i == 0 ? 2 : 0 });
            }
            var rating = LevelRatingEvaluator.Evaluate(profile, metrics);
            if (!rating.valid) throw new InvalidOperationException("UI fixture is invalid: " + string.Join(", ", rating.reasons));
            if (pending) rating.reasons = new[] { "Record could not be saved; retry save" };
            return new LevelClearInfo { victory = true, levelId = lastLevel, levelName = Localization.LevelName(lastLevel, "Level " + lastLevel),
                stars = rating.stars, previousBest = low ? 5 : 3, newRecord = !low && !pending,
                hp = metrics.hp, maxHp = metrics.maxHp, killed = metrics.killed, leaked = metrics.leaked,
                ratingResult = rating, progressSaved = !pending, savePending = pending,
                hasNext = false, nextLevelId = 0 };
        }

        private static JSONNode Analyze(GameObject instance, Camera camera)
        {
            JSONNode entry = new JSONObject(); entry["texts"] = new JSONArray();
            int issues = 0;
            foreach (var text in instance.GetComponentsInChildren<TMP_Text>(false))
            {
                var missing = new HashSet<char>();
                if (text.font != null)
                    foreach (char c in text.GetParsedText())
                        if (!char.IsWhiteSpace(c) && !text.font.HasCharacter(c, true, false)) missing.Add(c);
                var corners = new Vector3[4]; text.rectTransform.GetWorldCorners(corners);
                Rect visibleBounds = ViewportBounds(corners, camera);
                bool clipped = false;
                for (Transform parent = text.transform.parent; parent != null; parent = parent.parent)
                {
                    var mask = parent.GetComponent<RectMask2D>();
                    var stencil = parent.GetComponent<Mask>();
                    if ((mask == null || !mask.isActiveAndEnabled) && (stencil == null || !stencil.isActiveAndEnabled)) continue;
                    var rect = parent as RectTransform;
                    if (rect == null) continue;
                    rect.GetWorldCorners(corners);
                    Rect clip = ViewportBounds(corners, camera);
                    visibleBounds = Rect.MinMaxRect(Mathf.Max(visibleBounds.xMin, clip.xMin), Mathf.Max(visibleBounds.yMin, clip.yMin),
                        Mathf.Min(visibleBounds.xMax, clip.xMax), Mathf.Min(visibleBounds.yMax, clip.yMax));
                    clipped = true;
                }
                bool visible = visibleBounds.width > 0 && visibleBounds.height > 0;
                bool outside = visible && (visibleBounds.xMin < -.003f || visibleBounds.xMax > 1.003f || visibleBounds.yMin < -.003f || visibleBounds.yMax > 1.003f);
                JSONNode row = new JSONObject(); row["path"] = AnimationUtility.CalculateTransformPath(text.transform, instance.transform);
                row["text"] = text.text; row["fontSize"] = text.fontSize; row["overflow"] = text.isTextOverflowing;
                row["outsideViewport"] = outside; row["missingGlyphs"] = new string(new List<char>(missing).ToArray());
                row["visibleAfterMasks"] = visible; row["ancestorMaskApplied"] = clipped;
                if (visible && (text.isTextOverflowing || outside || missing.Count > 0)) issues++;
                entry["texts"].Add(row);
            }
            entry["issueCount"] = issues;
            return entry;
        }

        private static Rect ViewportBounds(Vector3[] corners, Camera camera)
        {
            Vector2 min = new Vector2(float.PositiveInfinity, float.PositiveInfinity), max = new Vector2(float.NegativeInfinity, float.NegativeInfinity);
            foreach (var corner in corners)
            {
                Vector3 p = camera.WorldToViewportPoint(corner);
                min = Vector2.Min(min, p); max = Vector2.Max(max, p);
            }
            return Rect.MinMaxRect(min.x, min.y, max.x, max.y);
        }

        private static void SetLayer(Transform root)
        {
            root.gameObject.layer = CaptureLayer;
            foreach (Transform child in root) SetLayer(child);
        }
    }
}
