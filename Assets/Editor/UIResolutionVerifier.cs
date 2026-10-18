using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using SimpleJSON;
using SuperScrollView;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace FTProject.EditorTools
{
    /// <summary>Exercise shipped UI with real bindings in a disposable canvas and isolated save context.</summary>
    public static class UIResolutionVerifier
    {
        private const int Layer = 31;
        private static readonly Vector2Int[] Sizes = {
            new Vector2Int(1920,1080), new Vector2Int(1280,720), new Vector2Int(1920,1200),
            new Vector2Int(1440,1080), new Vector2Int(2340,1080), new Vector2Int(2400,1080),
            new Vector2Int(2560,1080), new Vector2Int(1440,1080), new Vector2Int(2560,1080), new Vector2Int(1920,1080) };

        public static string CaptureView(string name, string output)
        {
            if (!EditorApplication.isPlaying || !Configs.IsLoaded || !SaveManager.IsTestStorage)
                throw new InvalidOperationException("Requires Play Mode, initialized config and isolated test storage.");
            Directory.CreateDirectory(output);
            JSONNode report = new JSONObject(); report["view"] = name; report["cases"] = new JSONArray();
            GameObject stage = new GameObject("UI resolution capture (temporary)");
            stage.hideFlags = HideFlags.HideAndDontSave;
            RenderTexture previous = RenderTexture.active;
            Language previousLanguage = LanguageManager.Current;
            try
            {
                GameObject cameraObject = new GameObject("Capture camera", typeof(Camera));
                cameraObject.transform.SetParent(stage.transform, false);
                Camera camera = cameraObject.GetComponent<Camera>(); camera.enabled = false;
                camera.orthographic = true; camera.clearFlags = CameraClearFlags.SolidColor;
                camera.backgroundColor = new Color(.035f,.06f,.10f); camera.cullingMask = 1 << Layer;
                camera.nearClipPlane = .1f; camera.farClipPlane = 2000f;
                camera.transform.localPosition = new Vector3(0f,0f,-1000f);
                GameObject canvasObject = new GameObject("Canvas",typeof(RectTransform),typeof(Canvas),typeof(GraphicRaycaster));
                canvasObject.transform.SetParent(stage.transform,false);
                Canvas canvas = canvasObject.GetComponent<Canvas>(); canvas.renderMode = RenderMode.WorldSpace;
                canvas.worldCamera = camera; canvas.referencePixelsPerUnit = 100f;
                RectTransform screen = (RectTransform)canvasObject.transform;
                screen.sizeDelta = new Vector2(1920f,1080f);
                GameObject safeObject = new GameObject("Safe area",typeof(RectTransform)); safeObject.transform.SetParent(screen,false);
                RectTransform safe = (RectTransform)safeObject.transform;
                Stretch(safe);
                string prefabPath = "Assets/Prefabs/UI/"+name+".prefab";
                GameObject instance = UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath), safe, false);
                Stretch((RectTransform)instance.transform);
                GameObject towerObject = new GameObject("UI fixture tower"); towerObject.transform.SetParent(stage.transform, false);
                NormalTower tower = towerObject.AddComponent<NormalTower>(); tower.enabled = false;
                tower.Init(Configs.GetTowerByTypeAndLevelSilent(1, 1), null);
                SetLayer(stage.transform);
                foreach (Language language in new[] { Language.English, Language.ChineseSimplified, Language.ChineseTraditional })
                {
                    instance.SetActive(false);
                    LanguageManager.SetLanguage(language);
                    instance.SetActive(true);
                    if (name == "TowerInfoView") instance.GetComponent<TowerInfoView>().Show(tower);
                    if (name == "SellConfirmView") Invoke(instance.GetComponent<SellConfirmView>(),"Setup",tower);
                    if (name == "HudView")
                    {
                        Invoke(instance.GetComponent<HudView>(),"OnGoldChanged",99999,0);
                        // This canvas is outside a running level: use display fixtures without looking up level id 0.
                        instance.transform.Find("Bg_Hp/HpText").GetComponent<TMP_Text>().text="20/20";
                        TMP_Text round=instance.transform.Find("Bg_Round/RoundText").GetComponent<TMP_Text>();
                        round.text=Localization.Get("Wave {0}/{1}",20,20); LanguageManager.ApplyFont(round);
                        instance.GetComponent<HudView>().SetTowerButtonInteractable(true);
                    }
                    if (name == "LevelDetailView") Invoke(instance.GetComponent<LevelDetailView>(),"Fill",20);
                    if (name == "LevelClearView")
                    {
                        object fixture = typeof(BalanceUiVisualVerifier).GetMethod("CreateClearFixture",BindingFlags.NonPublic|BindingFlags.Static).Invoke(null,new object[]{"clear-five"});
                        instance.GetComponent<LevelClearView>().Show((LevelClearInfo)fixture);
                    }
                    if (name == "TipsView")
                    {
                        instance.GetComponent<CanvasGroup>().alpha = 1f;
                        instance.transform.Find("TipBar/TipText").GetComponent<TMP_Text>().text = language == Language.English ? "Not enough gold to build this tower." : "金币不足，无法建造防御塔。";
                    }
                    for (int i=0;i<Sizes.Length;i++)
                    {
                        Vector2Int size=Sizes[i]; bool inset=i==7 || i==8;
                        // Exact main-scene CanvasScaler match=.5 geometry, also covering resize-back recovery.
                        float scale=Mathf.Sqrt(size.x/1920f*(size.y/1080f));
                        screen.sizeDelta=new Vector2(size.x/scale,size.y/scale);
                        safe.anchorMin=inset ? new Vector2(120f/size.x,24f/size.y) : Vector2.zero;
                        safe.anchorMax=inset ? new Vector2(1f-80f/size.x,1f-48f/size.y) : Vector2.one;
                        safe.offsetMin=safe.offsetMax=Vector2.zero;
                        camera.orthographicSize=screen.rect.height*.5f; camera.aspect=(float)size.x/size.y;
                        Refresh(instance);
                        // Rendering populates CanvasRenderer depth before GraphicRaycaster is exercised.
                        RenderTexture target=new RenderTexture(size.x,size.y,24,RenderTextureFormat.ARGB32);
                        target.Create(); camera.targetTexture=target;
                        try
                        {
                        camera.Render();
                        GraphicRaycaster raycaster=canvasObject.GetComponent<GraphicRaycaster>();
                        JSONNode row=Analyze(instance,safe,screen,camera,raycaster); row["width"]=size.x; row["height"]=size.y;
                        row["inset"]=inset; row["language"]=language.ToCode(); row["resizeStep"]=i;
                        LoopListView2 list=instance.GetComponentInChildren<LoopListView2>();
                        if (list!=null) row["list"]=CheckList(instance,list,safe,camera,raycaster);
                        bool capture=language==Language.English && (i==0 || i==3 || i==6 || i==8)
                            || language==Language.ChineseSimplified && i==8;
                        if (capture)
                        {
                            string file=name+"-"+language.ToCode()+"-"+size.x+"x"+size.y+(inset?"-safe":"")+".png";
                            Refresh(instance); Capture(camera,size,Path.Combine(output,file)); row["image"]=file;
                        }
                        report["cases"].Add(row);
                        }
                        finally { camera.targetTexture=null; target.Release(); UnityEngine.Object.DestroyImmediate(target); }
                    }
                }
            }
            finally
            {
                RenderTexture.active=previous;
                UnityEngine.Object.DestroyImmediate(stage);
                LanguageManager.SetLanguage(previousLanguage);
            }
            File.WriteAllText(Path.Combine(output,name+".json"),report.ToString(2),new System.Text.UTF8Encoding(false));
            return name+": "+report["cases"].Count+" cases captured";
        }

        private static void Refresh(GameObject root)
        {
            Canvas.ForceUpdateCanvases();
            foreach(UIResponsivePage page in root.GetComponentsInChildren<UIResponsivePage>(true)) page.Refresh();
            foreach(UIFitInParent fit in root.GetComponentsInChildren<UIFitInParent>(true)) fit.Refresh();
            foreach(UIFullScreenBackground bg in root.GetComponentsInChildren<UIFullScreenBackground>(true)) bg.Refresh();
            HudView hud=root.GetComponent<HudView>(); if(hud!=null) Invoke(hud,"RefreshBottomLayout");
            SelectView select=root.GetComponent<SelectView>(); if(select!=null) Invoke(select,"LateUpdate");
            TowerCodexView codex=root.GetComponent<TowerCodexView>(); if(codex!=null) Invoke(codex,"LateUpdate");
            foreach(TMP_Text text in root.GetComponentsInChildren<TMP_Text>(false)) text.ForceMeshUpdate(true,true);
            SetLayer(root.transform); // Pool-created cards keep the source prefab's layer until explicitly assigned.
            Canvas.ForceUpdateCanvases();
        }

        private static JSONNode Analyze(GameObject root,RectTransform safe,RectTransform screen,Camera camera,GraphicRaycaster raycaster)
        {
            JSONNode row=new JSONObject(); row["outside"]=new JSONArray(); row["overflows"]=new JSONArray(); row["overlaps"]=new JSONArray(); row["blockedButtons"]=new JSONArray(); row["missingGlyphs"]=new JSONArray();
            foreach(RectTransform rect in root.GetComponentsInChildren<RectTransform>(false))
            {
                if(rect.name=="Bg" || rect.GetComponentInParent<LoopListViewItem2>()!=null) continue;
                bool control=rect.GetComponent<Button>()!=null || rect.GetComponent<Slider>()!=null || rect.GetComponent<TMP_Dropdown>()!=null;
                TMP_Text text=rect.GetComponent<TMP_Text>();
                if(!control && (text==null || string.IsNullOrEmpty(text.text))) continue;
                Rect bounds=Bounds(rect,safe);
                if(!Contains(safe.rect,bounds)) row["outside"].Add(PathOf(rect,root.transform));
                if(text!=null && text.isTextOverflowing) row["overflows"].Add(PathOf(rect,root.transform)+": "+text.text);
                if(text!=null) CheckGlyphs(text,root.transform,row["missingGlyphs"]);
            }
            Button[] buttons=root.GetComponentsInChildren<Button>(false);
            foreach(Button button in buttons)
            {
                if(button.name=="Bg" || !button.IsInteractable() || button.GetComponentInParent<LoopListViewItem2>()!=null) continue;
                RectTransform rect=(RectTransform)button.transform;
                var pointer=new PointerEventData(EventSystem.current);
                pointer.position=camera.WorldToScreenPoint(rect.TransformPoint(rect.rect.center));
                var hits=new List<RaycastResult>(); raycaster.Raycast(pointer,hits);
                if(hits.Count==0 || !hits[0].gameObject.transform.IsChildOf(rect)) row["blockedButtons"].Add(PathOf(rect,root.transform)+(hits.Count>0?" by "+hits[0].gameObject.name:" no raycast hit"));
            }
            for(int a=0;a<buttons.Length;a++) for(int b=a+1;b<buttons.Length;b++)
            {
                if(buttons[a].name=="Bg" || buttons[b].name=="Bg" || buttons[a].transform.parent!=buttons[b].transform.parent) continue;
                if(buttons[a].GetComponentInParent<LoopListViewItem2>()!=null) continue;
                Rect ra=Bounds((RectTransform)buttons[a].transform,safe), rb=Bounds((RectTransform)buttons[b].transform,safe);
                if(Mathf.Min(ra.xMax,rb.xMax)-Mathf.Max(ra.xMin,rb.xMin)>1f && Mathf.Min(ra.yMax,rb.yMax)-Mathf.Max(ra.yMin,rb.yMin)>1f)
                    row["overlaps"].Add(buttons[a].name+" / "+buttons[b].name);
            }
            RectTransform bg=root.transform.Find("Bg") as RectTransform;
            if(bg!=null) row["backgroundCoversCanvas"]=Contains(Bounds(bg,screen),screen.rect);
            return row;
        }

        private static JSONNode CheckList(GameObject root,LoopListView2 list,RectTransform safe,Camera camera,GraphicRaycaster raycaster)
        {
            JSONNode row=new JSONObject(); row["count"]=list.ItemTotalCount; row["viewportWidth"]=list.ViewPortSize;
            row["endpoints"]=new JSONArray(); row["textIssues"]=new JSONArray(); row["missingGlyphs"]=new JSONArray();
            for(int index=0;index<list.ItemTotalCount;index++)
            {
                if(index<0)continue;
                list.MovePanelToItemIndex(index,0f);
                list.SetSnapTargetItemIndex(index); list.FinishSnapImmediately();
                Canvas.ForceUpdateCanvases();
                LoopListViewItem2 item=list.GetShownItemByItemIndex(index);
                if(item==null) { row["endpoints"].Add("missing "+index); continue; }
                RectTransform rect=(RectTransform)item.transform;
                RectTransform viewport=list.GetComponent<ScrollRect>().viewport;
                Vector3 center=rect.TransformPoint(rect.rect.center), reference=viewport.TransformPoint(viewport.rect.center);
                JSONNode endpoint=new JSONObject(); endpoint["index"]=index; endpoint["centerError"]=Vector3.Distance(center,reference);
                row["endpoints"].Add(endpoint);
                Refresh(root);
                foreach(TMP_Text text in item.GetComponentsInChildren<TMP_Text>(false))
                {
                    text.ForceMeshUpdate(true,true);
                    if(text.isTextOverflowing) row["textIssues"].Add(index+"/"+text.name+": "+text.text);
                    CheckGlyphs(text,root.transform,row["missingGlyphs"]);
                    if(!Contains(safe.rect,Bounds(text.rectTransform,safe))) row["textIssues"].Add(index+"/"+text.name+" outside safe area");
                }
            }
            list.MovePanelToItemIndex(0,0f); list.SetSnapTargetItemIndex(0); list.FinishSnapImmediately();
            Refresh(root);
            if(list.ItemTotalCount>1)
            {
                // Invoke the shipped button callback, then finish its requested animation deterministically.
                root.transform.Find("Panel/RightBtn").GetComponent<Button>().onClick.Invoke();
                list.FinishSnapImmediately(); Refresh(root);
                LoopListViewItem2 second=list.GetShownItemByItemIndex(1);
                RectTransform viewport=list.GetComponent<ScrollRect>().viewport;
                row["rightArrowCentered"]=second!=null && Vector3.Distance(((RectTransform)second.transform).TransformPoint(((RectTransform)second.transform).rect.center),viewport.TransformPoint(viewport.rect.center))<1f;
                root.transform.Find("Panel/LeftBtn").GetComponent<Button>().onClick.Invoke();
                list.FinishSnapImmediately(); Refresh(root);
                LoopListViewItem2 first=list.GetShownItemByItemIndex(0);
                row["leftArrowCentered"]=first!=null && Vector3.Distance(((RectTransform)first.transform).TransformPoint(((RectTransform)first.transform).rect.center),viewport.TransformPoint(viewport.rect.center))<1f;
                ScrollRect scroll=list.GetComponent<ScrollRect>();
                var pointer=new PointerEventData(EventSystem.current); pointer.button=PointerEventData.InputButton.Left;
                pointer.position=camera.WorldToScreenPoint(viewport.TransformPoint(viewport.rect.center)); pointer.pressPosition=pointer.position;
                pointer.pointerPressRaycast=new RaycastResult { module=raycaster, gameObject=list.gameObject };
                Vector2 before=scroll.content.anchoredPosition;
                scroll.OnInitializePotentialDrag(pointer); scroll.OnBeginDrag(pointer); list.OnBeginDrag(pointer);
                pointer.position+=Vector2.left*150f; pointer.delta=Vector2.left*150f;
                scroll.OnDrag(pointer); list.OnDrag(pointer);
                row["dragMovedContent"]=Vector2.Distance(before,scroll.content.anchoredPosition)>1f;
                scroll.OnEndDrag(pointer); list.OnEndDrag(pointer); scroll.StopMovement();
            }
            list.MovePanelToItemIndex(0,0f); list.SetSnapTargetItemIndex(0); list.FinishSnapImmediately(); Refresh(root); camera.Render();
            LoopListViewItem2 centerItem=list.GetShownItemByItemIndex(0);
            Button card=centerItem==null?null:centerItem.GetComponentInChildren<Button>();
            if(card!=null)
            {
                var pointer=new PointerEventData(EventSystem.current);
                RectTransform rect=(RectTransform)card.transform;
                pointer.position=camera.WorldToScreenPoint(rect.TransformPoint(rect.rect.center));
                var hits=new List<RaycastResult>(); raycaster.Raycast(pointer,hits);
                row["cardReceivesClick"]=hits.Count>0 && hits[0].gameObject.transform.IsChildOf(rect);
            }
            return row;
        }

        private static void CheckGlyphs(TMP_Text text,Transform root,JSONNode result)
        {
            if(text.font==null)return;
            var missing=new HashSet<char>();
            foreach(char c in text.GetParsedText()) if(!char.IsWhiteSpace(c) && !text.font.HasCharacter(c,true,false)) missing.Add(c);
            if(missing.Count>0) result.Add(PathOf(text.transform,root)+": "+new string(new List<char>(missing).ToArray()));
        }

        private static void Capture(Camera camera,Vector2Int size,string path)
        {
            RenderTexture previous=RenderTexture.active;
            RenderTexture target=new RenderTexture(size.x,size.y,24,RenderTextureFormat.ARGB32);
            Texture2D image=new Texture2D(size.x,size.y,TextureFormat.RGB24,false);
            try
            {
                target.Create(); camera.targetTexture=target; camera.Render(); RenderTexture.active=target;
                image.ReadPixels(new Rect(0,0,size.x,size.y),0,0); image.Apply(); File.WriteAllBytes(path,image.EncodeToPNG());
            }
            finally
            {
                camera.targetTexture=null; RenderTexture.active=previous;
                target.Release(); UnityEngine.Object.DestroyImmediate(target); UnityEngine.Object.DestroyImmediate(image);
            }
        }

        private static Rect Bounds(RectTransform rect,RectTransform reference)
        {
            Vector3[] corners=new Vector3[4]; rect.GetWorldCorners(corners);
            Vector2 min=new Vector2(float.MaxValue,float.MaxValue), max=new Vector2(float.MinValue,float.MinValue);
            foreach(Vector3 corner in corners) { Vector2 p=reference.InverseTransformPoint(corner); min=Vector2.Min(min,p); max=Vector2.Max(max,p); }
            return Rect.MinMaxRect(min.x,min.y,max.x,max.y);
        }
        private static bool Contains(Rect outer,Rect inner) { const float e=1f; return inner.xMin>=outer.xMin-e && inner.xMax<=outer.xMax+e && inner.yMin>=outer.yMin-e && inner.yMax<=outer.yMax+e; }
        private static string PathOf(Transform node,Transform root) { return AnimationUtility.CalculateTransformPath(node,root); }
        private static object Invoke(object target,string method,params object[] args) { return target.GetType().GetMethod(method,BindingFlags.Instance|BindingFlags.NonPublic).Invoke(target,args); }
        private static void Stretch(RectTransform rect) { rect.anchorMin=Vector2.zero;rect.anchorMax=Vector2.one;rect.offsetMin=rect.offsetMax=Vector2.zero;rect.localScale=Vector3.one; }
        private static void SetLayer(Transform node) { node.gameObject.layer=Layer;foreach(Transform child in node) SetLayer(child); }
    }
}
