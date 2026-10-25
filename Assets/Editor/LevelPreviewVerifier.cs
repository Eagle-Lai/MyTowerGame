using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using SimpleJSON;
using SuperScrollView;
using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace FTProject.EditorTools
{
    /// <summary>Exercises the actual shipped prefab, production unlock rules and loader in isolated storage.</summary>
    public static class LevelPreviewVerifier
    {
        private static readonly BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
        private static void Require(bool value, string message) { if (!value) throw new InvalidOperationException(message); }
        private static void Call(SelectView view, string method, params object[] args)
        { typeof(SelectView).GetMethod(method, Private).Invoke(view, args); }
        private static void Refresh(SelectView view)
        {
            Canvas.ForceUpdateCanvases(); Call(view, "LateUpdate");
            SetLayer(view.transform);
            foreach (TMP_Text text in view.GetComponentsInChildren<TMP_Text>(false)) text.ForceMeshUpdate(true, true);
            Canvas.ForceUpdateCanvases();
        }
        private static void SetLayer(Transform node)
        {
            node.gameObject.layer = 31;
            for (int i = 0; i < node.childCount; i++) SetLayer(node.GetChild(i));
        }
        private static LoopListViewItem2 Center(SelectView view, LoopListView2 list, int index)
        {
            Call(view, "CenterOnIndexInstant", index); Refresh(view);
            LoopListViewItem2 item = list.GetShownItemByItemIndex(index);
            Require(item != null, "Missing pooled item at index " + index);
            return item;
        }
        private static void CheckCard(LoopListViewItem2 item, cfg.SceneInfo level)
        {
            var card = item.GetComponent<SelectLevelItemView>();
            Require(card != null && card.BoundLevelId == level.Id, "Incorrect bound level ID");
            Require(card.Preview.enabled && card.Preview.sprite != null && card.Preview.sprite.name == LevelPreviewCatalog.LogicalName(level.Id), "Missing/wrong preview for " + level.Id);
            Require(item.UserIntData1 == level.Id && item.UserObjectData is CanvasGroup, "LoopList user data was overwritten");
            Require(card.Preview.preserveAspect && !card.Preview.raycastTarget, "Invalid preview Image setup");
            Require(!card.Label.isTextOverflowing, "Card text overflows for " + level.Id + ": " + card.Label.text);
        }

        public static string Run(string output)
        {
            Require(EditorApplication.isPlaying && Configs.IsLoaded && ResLoader.Instance.IsReady && SaveManager.IsTestStorage, "Booted Play Mode with isolated test storage is required");
            Directory.CreateDirectory(output);
            JSONNode report = new JSONObject(); report["loader"] = ResLoader.ImplName;
            report["assets"] = new JSONArray(); report["screenshots"] = new JSONArray();
            report["levelCount"] = Configs.LevelTable.DataList.Count;
            GameObject stage = null;
            Language oldLanguage = LanguageManager.Current;
            GameFlowManager flow = GameFlowManager.Instance; bool flowEnabled = flow != null && flow.enabled;
            int enterId = 0, tipCount = 0;
            Action<int> onEnter = id => enterId = id; Action<string> onTip = message => tipCount++;
            try
            {
                VerifyAssets(report);
                if (flowEnabled) flow.enabled = false;
                EventDispatcher.AddEventListener<int>(EventName.SelectLevelRequestEvent, onEnter);
                EventDispatcher.AddEventListener<string>(EventName.ShowTipEvent, onTip);
                using (SaveManager.Instance.UseProductionUnlockRulesForTest())
                {
                    stage = new GameObject("LevelPreview UI verification");
                    stage.hideFlags = HideFlags.HideAndDontSave;
                    var cameraObject = new GameObject("UI verification camera"); cameraObject.transform.SetParent(stage.transform, false);
                    Camera camera = cameraObject.AddComponent<Camera>(); camera.enabled = false; camera.cullingMask = 1 << 31;
                    camera.orthographic = true; camera.clearFlags = CameraClearFlags.SolidColor;
                    camera.backgroundColor = new Color(.035f, .06f, .10f);
                    camera.transform.position = new Vector3(0f, 0f, -1000f); camera.nearClipPlane = .1f; camera.farClipPlane = 2000f;
                    var canvasObject = new GameObject("Canvas", typeof(RectTransform), typeof(Canvas), typeof(GraphicRaycaster));
                    canvasObject.transform.SetParent(stage.transform, false);
                    var canvas = canvasObject.GetComponent<Canvas>(); canvas.renderMode = RenderMode.WorldSpace; canvas.worldCamera = camera;
                    canvas.referencePixelsPerUnit = 100f;
                    RectTransform canvasRect = (RectTransform)canvas.transform; canvasRect.sizeDelta = new Vector2(1920, 1080);
                    camera.orthographicSize = 540f; camera.aspect = 1920f / 1080;
                    var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/UI/SelectView.prefab");
                    for (int reopen = 0; reopen < 2; reopen++)
                    {
                        GameObject instance = UnityEngine.Object.Instantiate(prefab, canvasRect, false);
                        try
                        {
                            var rect = (RectTransform)instance.transform; rect.anchorMin = Vector2.zero; rect.anchorMax = Vector2.one; rect.offsetMin = rect.offsetMax = Vector2.zero;
                            SetLayer(stage.transform); instance.SetActive(true);
                            var view = instance.GetComponent<SelectView>(); Refresh(view);
                            var list = instance.GetComponentInChildren<LoopListView2>();
                            Require(list.ItemTotalCount == Configs.LevelTable.DataList.Count, "Incorrect list count");
                            foreach (Language language in new[] { Language.ChineseSimplified, Language.English, Language.ChineseTraditional })
                            {
                                LanguageManager.SetLanguage(language); view.Build(); Refresh(view);
                                for (int pass = 0; pass < 2; pass++)
                                    for (int n = 0; n < list.ItemTotalCount; n++)
                                    {
                                        int index = pass == 0 ? n : list.ItemTotalCount - 1 - n;
                                        var item = Center(view, list, index);
                                        CheckCard(item, Configs.LevelTable.DataList[index]);
                                        Require(Mathf.Abs(item.DistanceWithViewPortSnapCenter) < 1f, "Snap center mismatch");
                                    }
                                Language other = language == Language.English ? Language.ChineseSimplified : Language.English;
                                LanguageManager.SetLanguage(other); Refresh(view);
                                var visible = Center(view, list, list.ItemTotalCount - 1);
                                CheckCard(visible, Configs.LevelTable.DataList[list.ItemTotalCount - 1]);
                                Require(visible.GetComponent<SelectLevelItemView>().Label.text.Contains("<size=56>"), "Language change replaced dynamic card text");
                            }
                            if (reopen == 0)
                            {
                                VerifyInput(view, list, camera, canvasObject.GetComponent<GraphicRaycaster>(), ref enterId, ref tipCount);
                                var first = Center(view, list, 0).GetComponent<SelectLevelItemView>();
                                first.Bind(int.MaxValue); Require(!first.Preview.enabled && first.Preview.sprite == null, "Missing preview retained old image");
                                first.Bind(int.MaxValue); first.Bind(Configs.LevelTable.DataList[0].Id); CheckCard(first.GetComponent<LoopListViewItem2>(), Configs.LevelTable.DataList[0]);
                                report["missingPreviewFallback"] = true;
                                CaptureScreenshots(view, list, camera, canvasRect, output, report);
                            }
                        }
                        finally { UnityEngine.Object.DestroyImmediate(instance); }
                    }
                    var cache = (System.Collections.IDictionary)typeof(SelectLevelItemView).GetField("Loaded", BindingFlags.Static | BindingFlags.NonPublic).GetValue(null);
                    Require(cache.Count == 0, "Preview references leaked after destroying cards");
                    report["previewReferencesAfterClose"] = cache.Count;
                    report["pooledForwardBackwardPasses"] = 12; report["reopenCount"] = 2;
                    report["inputVerified"] = "Arrows, ScrollRect drag, image raycast passthrough, locked card rejection, centered entry, off-center snap then entry, default detail window";
                }
                report["passed"] = true;
            }
            catch (Exception error) { report["passed"] = false; report["error"] = error.ToString(); }
            finally
            {
                EventDispatcher.RemoveEventListener<int>(EventName.SelectLevelRequestEvent, onEnter);
                EventDispatcher.RemoveEventListener<string>(EventName.ShowTipEvent, onTip);
                UIManager.Instance.Close("LevelDetailView");
                LanguageManager.SetLanguage(oldLanguage);
                if (stage != null) UnityEngine.Object.DestroyImmediate(stage);
                if (flowEnabled && flow != null) flow.enabled = true;
            }
            report["playerOrRealAssetBundleBuildExecuted"] = false;
            File.WriteAllText(Path.Combine(output, "verification.json"), report.ToString(2));
            return report.ToString(2);
        }

        private static void VerifyAssets(JSONNode report)
        {
            var levels = Configs.LevelTable.DataList.Where(level => level != null).ToArray();
            Require(LevelPreviewIdsMatch(levels.Select(level => level.Id).ToArray()), "Generated preview catalog is out of date; generate all previews");
            foreach (var level in levels)
            {
                string path = LevelPreviewCatalog.AssetPath(level.Id), key = LevelPreviewCatalog.LogicalName(level.Id);
                ResAddress address; Require(ResTable.TryGet(key, out address) && address.EditorPath == path && address.Bundle == ResBundle.UiHud, "Preview resource registration invalid");
                var importer = AssetImporter.GetAtPath(path) as TextureImporter;
                Require(importer != null && importer.textureType == TextureImporterType.Sprite && !importer.mipmapEnabled && !importer.isReadable, "Preview importer invalid");
                var sprite = AssetDatabase.LoadAssetAtPath<Sprite>(path);
                Require(sprite != null && sprite.texture.width == 1024 && sprite.texture.height == 576, "Preview size mismatch");
                Require(AssetDatabase.FindAssets(key + " t:Texture2D").Count(guid => Path.GetFileNameWithoutExtension(AssetDatabase.GUIDToAssetPath(guid)) == key) == 1, "Duplicate file-name address: " + key);
#if USE_YOOASSET
                Require(FTBundlePackRule.ResolveBundle(path) == ResBundle.UiHud, "Wrong bundle rule output");
#endif
                var map = Configs.GetLevelMapOfLevel(level.Id);
                JSONNode row = new JSONObject(); row["levelId"] = level.Id; row["mapId"] = map.Id;
                row["rows"] = map.Rows; row["cols"] = map.Cols; row["path"] = path; row["bundle"] = address.Bundle;
                report["assets"].Add(row);
            }
        }
        private static bool LevelPreviewIdsMatch(int[] actual)
        {
            var registered = ResTable.All.Where(pair => pair.Key.StartsWith("LevelPreview_", StringComparison.Ordinal)).Select(pair => pair.Key).OrderBy(key => key);
            return registered.SequenceEqual(actual.Select(LevelPreviewCatalog.LogicalName).OrderBy(key => key));
        }
        private static void VerifyInput(SelectView view, LoopListView2 list, Camera camera, GraphicRaycaster raycaster, ref int enterId, ref int tipCount)
        {
            LanguageManager.SetLanguage(Language.ChineseSimplified); Refresh(view);
            var first = Center(view, list, 0);
            view.transform.Find("Panel/RightBtn").GetComponent<Button>().onClick.Invoke(); list.FinishSnapImmediately(); Refresh(view);
            Require(Mathf.Abs(list.GetShownItemByItemIndex(1).DistanceWithViewPortSnapCenter) < 1f, "Right arrow failed");
            view.transform.Find("Panel/LeftBtn").GetComponent<Button>().onClick.Invoke(); list.FinishSnapImmediately(); Refresh(view);
            Require(Mathf.Abs(list.GetShownItemByItemIndex(0).DistanceWithViewPortSnapCenter) < 1f, "Left arrow failed");
            ScrollRect scroll = list.GetComponent<ScrollRect>();
            var pointer = new PointerEventData(EventSystem.current); pointer.button = PointerEventData.InputButton.Left;
            pointer.position = camera.WorldToScreenPoint(scroll.viewport.TransformPoint(scroll.viewport.rect.center)); pointer.pressPosition = pointer.position;
            pointer.pointerPressRaycast = new RaycastResult { module = raycaster, gameObject = list.gameObject };
            Vector2 before = scroll.content.anchoredPosition; scroll.OnInitializePotentialDrag(pointer); scroll.OnBeginDrag(pointer); list.OnBeginDrag(pointer);
            pointer.position += Vector2.left * 180f; pointer.delta = Vector2.left * 180f; scroll.OnDrag(pointer); list.OnDrag(pointer);
            Require(Vector2.Distance(before, scroll.content.anchoredPosition) > 1f, "Dragging did not move list");
            scroll.OnEndDrag(pointer); list.OnEndDrag(pointer); scroll.StopMovement(); first = Center(view, list, 0);
            camera.Render();
            pointer.position = camera.WorldToScreenPoint(first.transform.Find("Body/MapPreview").position);
            var hits = new List<RaycastResult>(); raycaster.Raycast(pointer, hits);
            Require(hits.Count > 0 && hits[0].gameObject == first.transform.Find("Body").gameObject, "Preview blocked button hit");
            typeof(SelectView).GetField("skipDetail", Private).SetValue(view, true);
            first.GetComponentInChildren<Button>().onClick.Invoke();
            Require(enterId == first.UserIntData1, "Centered card entered wrong level"); enterId = 0;
            var locked = Center(view, list, 1); int tipsBefore = tipCount;
            Require(locked.UserIntData2 == 0, "Expected locked card under production unlock rules");
            locked.GetComponentInChildren<Button>().onClick.Invoke();
            Require(enterId == 0 && tipCount > tipsBefore, "Locked card did not reject entry");
            first = list.GetShownItemByItemIndex(0);
            if (first == null) { Call(view, "EnsureShown", 0); first = list.GetShownItemByItemIndex(0); }
            first.GetComponentInChildren<Button>().onClick.Invoke(); Require(enterId == 0, "Off-center card entered before snapping");
            list.FinishSnapImmediately(); Refresh(view); Require(enterId == Configs.LevelTable.DataList[0].Id, "Off-center pending entry failed");
            typeof(SelectView).GetField("skipDetail", Private).SetValue(view, false);
            first = Center(view, list, 0); first.GetComponentInChildren<Button>().onClick.Invoke();
            Require(UnityEngine.Object.FindObjectOfType<LevelDetailView>() != null, "Default card entry did not open details");
            UIManager.Instance.Close("LevelDetailView");
        }
        private static void CaptureScreenshots(SelectView view, LoopListView2 list, Camera camera, RectTransform canvas, string output, JSONNode report)
        {
            int middle = list.ItemTotalCount / 2;
            foreach (int index in new[] { 0, middle, list.ItemTotalCount - 1 })
            {
                Center(view, list, index);
                string path = Path.Combine(output, "select-level-" + Configs.LevelTable.DataList[index].Id.ToString("D3") + ".png");
                CaptureUi(camera, path, 1920, 1080); report["screenshots"].Add(path);
            }
            foreach (var size in new[] { new Vector2Int(1024,768), new Vector2Int(2340,1080) })
            {
                float scale = Mathf.Sqrt(size.x / 1920f * (size.y / 1080f)); canvas.sizeDelta = new Vector2(size.x / scale, size.y / scale);
                camera.orthographicSize = canvas.rect.height * .5f; camera.aspect = (float)size.x / size.y;
                Center(view, list, 0);
                string path = Path.Combine(output, "select-" + size.x + "x" + size.y + ".png"); CaptureUi(camera, path, size.x, size.y);
                report["screenshots"].Add(path);
            }
            canvas.sizeDelta = new Vector2(1920,1080); camera.orthographicSize = 540f; camera.aspect = 1920f/1080f;
        }
        private static void CaptureUi(Camera camera, string path, int width, int height)
        {
            Canvas.ForceUpdateCanvases(); var old = RenderTexture.active; var previousTarget = camera.targetTexture;
            RenderTexture target = RenderTexture.GetTemporary(width,height,24,RenderTextureFormat.ARGB32); Texture2D image = null;
            try
            {
                camera.targetTexture = target; camera.Render(); RenderTexture.active = target;
                image = new Texture2D(width,height,TextureFormat.RGB24,false); image.ReadPixels(new Rect(0,0,width,height),0,0); image.Apply();
                File.WriteAllBytes(path,image.EncodeToPNG());
            }
            finally { camera.targetTexture = previousTarget; RenderTexture.active=old; RenderTexture.ReleaseTemporary(target); if(image!=null)UnityEngine.Object.DestroyImmediate(image); }
        }
    }
}
