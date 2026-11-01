using System;
using System.IO;
using System.Linq;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject.EditorTools
{
    /// <summary>Idempotent, GUID-preserving production migration. Never touches enemy assets or configuration exports.</summary>
    public static class TacticalForgePrefabBuilder
    {
        public const string Art = "Assets/_UIAssets/UI/TacticalForge";
        private static readonly string[] Pages = { "MainMenuView","SelectView","LevelDetailView","GameIntroView","HudView","TowerInfoView","PauseView","TipsView","TowerCodexView","TowerCodexItem","SellConfirmView","ConfirmView","SettingView","LevelClearView","MonsterCodexView","SplashView","LoadingView","HotUpdateView" };
        private static readonly Color Ink = Hex("080B12"), Panel = Hex("1E2939"), Surface = Hex("101B2B"), Cyan = Hex("35E0FF"), Text = Hex("E8F0FA");
        private const string LogoPath = "Assets/Art/Logo/app_icon_512x512.png";
        private static TMP_FontAsset _font;
        public static bool Applies(string name) { return Pages.Contains(name.Replace("(Clone)","")) || name == "SelectLevelItem"; }
        private static string PathOf(string name)
        {
            if (name == "HotUpdateView") return "Assets/Resources/BootUI/HotUpdateView.prefab";
            if (name == "SplashView" || name == "LoadingView") return "Assets/HotUpdateUI/" + name + ".prefab";
            return "Assets/Prefabs/UI/" + name + ".prefab";
        }
        [MenuItem("Tools/塔防/Tactical Forge/更新实际 UI（保留 GUID）", false, 90)]
        public static void BuildAll()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode) throw new InvalidOperationException("UI migration requires Edit Mode.");
            GenerateArt();
            if (File.Exists(Art+"/Fonts/NotoSansCJKsc-Regular.otf")) TacticalForgeAssets.CreateFont();
            _font = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(Art+"/Fonts/TacticalSans.asset");
            BuildGridItem();
            BuildMonsterItem();
            BuildBriefingEnemyItem();
            foreach (string name in Pages) UpdateExisting(PathOf(name));
            TacticalForgeAssets.CreatePortraits();
            AssetDatabase.SaveAssets();
            Debug.Log("[TacticalForge] Production prefabs updated in place; no enemy/configuration assets changed.");
        }
        [MenuItem("Tools/塔防/Tactical Forge/同步问题文档修正（2026-10-27）", false, 91)]
        public static void ApplyIssueDocumentFixes()
        {
            if(EditorApplication.isPlayingOrWillChangePlaymode)throw new InvalidOperationException("Edit Mode required.");
            GenerateArt();BuildBriefingEnemyItem();
            foreach(string name in new[]{"HotUpdateView","MainMenuView","SelectView","LevelDetailView","GameIntroView","HudView","ConfirmView","PauseView","SettingView","TowerInfoView","SellConfirmView"})UpdateExisting(PathOf(name));
            AssetDatabase.SaveAssets();
            Debug.Log("[UIIssueFix] Updated 11 affected views and the enemy portrait item; retained audio controls and prefab GUIDs.");
        }
        [MenuItem("Tools/塔防/Tactical Forge/同步问题文档修正（2026-10-28）", false, 92)]
        public static void ApplyOctober28DocumentFixes()
        {
            if(EditorApplication.isPlayingOrWillChangePlaymode)throw new InvalidOperationException("Edit Mode required.");
            GenerateArt();
            foreach(string name in new[]{"TowerCodexItem","SplashView","TowerCodexView","GameIntroView","SettingView","PauseView","LevelClearView"})UpdateExisting(PathOf(name));
            AssetDatabase.SaveAssets();
            Debug.Log("[UIIssueFix20261028] Updated six views and the shared tower card, preserving prefab GUIDs and audio controls.");
        }
        [MenuItem("Tools/塔防/Tactical Forge/更新 HUD 建造圆盘（2026-11-01）", false, 93)]
        public static void ApplyTowerBuildMenu()
        {
            if(EditorApplication.isPlayingOrWillChangePlaymode)throw new InvalidOperationException("Edit Mode required.");
            GenerateArt();
            CreateTowerActionArt();
            TacticalForgeAssets.CreatePortraits();
            UpdateExisting(PathOf("HudView"));
            AssetDatabase.SaveAssets();
            Debug.Log("[TacticalForge] HudView.prefab 已写入建造圆盘（TowerBuildMenu：Backdrop + 三塔图标按钮，运行时行为见 TowerBuildMenu.cs）。");
        }
        public static bool UpdateExisting(string path)
        {
            if (!Applies(System.IO.Path.GetFileNameWithoutExtension(path))) return false;
            if (!File.Exists(path))
            {
                if (!path.EndsWith("MonsterCodexView.prefab")) return false;
                var created = new GameObject("MonsterCodexView",typeof(RectTransform),typeof(MonsterCodexView));
                Apply(created); PrefabUtility.SaveAsPrefabAsset(created,path); UnityEngine.Object.DestroyImmediate(created); return true;
            }
            GameObject root = PrefabUtility.LoadPrefabContents(path);
            try { Apply(root); PrefabUtility.SaveAsPrefabAsset(root,path); }
            finally { PrefabUtility.UnloadPrefabContents(root); }
            return true;
        }
        public static void Apply(GameObject root)
        {
            string name = root.name.Replace("(Clone)","");
            if (!Applies(name)) return;
            _font = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(Art+"/Fonts/TacticalSans.asset");
            bool boot = name == "HotUpdateView";
            RectTransform backdrop = root.transform.Find("Bg") as RectTransform;
            if(backdrop!=null && !boot)Ensure<UIFullScreenBackground>(backdrop.gameObject);
            if(boot)
            {
                // Resources embeds the native TMP/font dependencies. Never add hot-update behaviours to the AOT shell.
                foreach(var fit in root.GetComponentsInChildren<UIFitInParent>(true))UnityEngine.Object.DestroyImmediate(fit);
                foreach(var background in root.GetComponentsInChildren<UIFullScreenBackground>(true))UnityEngine.Object.DestroyImmediate(background);
                foreach(var localizer in root.GetComponentsInChildren<TextLocalizer>(true))UnityEngine.Object.DestroyImmediate(localizer);
            }
            foreach (TMP_Text t in root.GetComponentsInChildren<TMP_Text>(true))
            {
                if (_font != null) { t.font=_font; t.fontSharedMaterial=_font.material; }
                t.color=Text; t.enableAutoSizing=true; t.fontSizeMin=Mathf.Min(t.fontSize,22);
                t.fontSizeMax=Mathf.Max(28,t.fontSize); t.overflowMode=TextOverflowModes.Ellipsis;
                t.raycastTarget=false;
            }
            foreach (Image img in root.GetComponentsInChildren<Image>(true))
            {
                string n=img.name;
                if(n=="Bg") {img.color = new Color(Ink.r,Ink.g,Ink.b,name=="TowerInfoView"?0:1);img.sprite=null;}
                else if(n=="Panel" || n=="StatBg" || n=="TipBar") Skin(img,"panel",Panel);
                else if(img.GetComponent<Button>()!=null) Skin(img,"button",Panel);
            }
            foreach (Button button in root.GetComponentsInChildren<Button>(true))
            {
                ColorBlock colors=button.colors; colors.normalColor=Color.white; colors.highlightedColor=Hex("7DE8FF");
                colors.pressedColor=Hex("35E0FF");colors.selectedColor=Color.white;colors.disabledColor=new Color(.4f,.45f,.5f,.5f);button.colors=colors;
            }
            if(name=="TowerCodexItem") {StyleCodexItem(root); return;}
            if(name=="SelectLevelItem") return;
            bool full = new[]{"MainMenuView","SelectView","LevelDetailView","LevelClearView","MonsterCodexView"}.Contains(name);
            if(!boot && !full && name!="TowerCodexView" && name!="TowerInfoView" && name!="HudView")
            {
                var dialog=root.transform.Find("Panel") as RectTransform;
                if(dialog!=null && dialog.anchorMin==dialog.anchorMax)Ensure<UIFitInParent>(dialog.gameObject);
            }
            if(full)
            {
                foreach(var old in root.GetComponentsInChildren<UIFitInParent>(true)) UnityEngine.Object.DestroyImmediate(old);
                foreach(var old in root.GetComponents<UIResponsivePage>()) UnityEngine.Object.DestroyImmediate(old);
                RectTransform panel=Node(root.transform,"Panel"); Stretch(panel);
                Image pi=panel.GetComponent<Image>(); if(pi!=null) {pi.color=Color.clear;pi.raycastTarget=false;}
                foreach(string decoration in new[]{"Panel/TopBar","Panel/Glow","Panel/BottomLine"})
                {var tr=root.transform.Find(decoration);if(tr!=null && tr.GetComponentInChildren<Button>(true)==null)tr.gameObject.SetActive(false);}
            }
            if(name=="MainMenuView")
            {
                Image bg=ImageAt(root.transform,"Bg");bg.sprite=AssetDatabase.LoadAssetAtPath<Sprite>(Art+"/Backgrounds/keyart.png");bg.color=Color.white;bg.raycastTarget=false;Stretch(bg.rectTransform);
                Image shade=ImageAt(root.transform,"MenuShade");shade.sprite=AssetDatabase.LoadAssetAtPath<Sprite>(Art+"/Backgrounds/menu-shade.png");shade.color=Color.white;shade.raycastTarget=false;Stretch(shade.rectTransform);shade.transform.SetSiblingIndex(1);
                Image logo=ImageAt(root.transform,"Panel/Logo");logo.sprite=AssetDatabase.LoadAssetAtPath<Sprite>(LogoPath);logo.color=Color.white;logo.preserveAspect=true;
                var title=TextAt(root.transform,"Panel/GameTitle","FREEDOM\nTOWER",78);title.alignment=TextAlignmentOptions.TopLeft;title.enableWordWrapping=true;
                var sub=TextAt(root.transform,"Panel/Subtitle","自由人塔防  /  TACTICAL FORGE",27);sub.gameObject.SetActive(true);sub.alignment=TextAlignmentOptions.Left;
                ButtonAt(root.transform,"Panel/ContinueBtn","Continue",true);ButtonAt(root.transform,"Panel/MonsterCodexBtn","Monster Codex",false);
                foreach(string p in new[]{"Panel/StatBg/StarText","Panel/StatBg/ClearText"}) root.transform.Find(p).GetComponent<TMP_Text>().alignment=TextAlignmentOptions.Left;
            }
            else if(name=="SelectView")
            {
                foreach(string p in new[]{"Panel/List","Panel/LeftBtn","Panel/RightBtn","Panel/PageText"}) {var n=root.transform.Find(p);if(n!=null) n.gameObject.SetActive(false);}
                Scroll(root.transform,"Panel/Grid",4);
                TextAt(root.transform,"Panel/Preview/Name","",40);
                TextAt(root.transform,"Panel/Preview/Stats","",28);
                var map=Node(root.transform,"Panel/Preview/Map");Ensure<LevelMapPreviewGraphic>(map.gameObject).raycastTarget=false;
                ButtonAt(root.transform,"Panel/Preview/BriefingBtn","View Briefing",true);
                root.GetComponent<SelectView>().ConfigureGrid(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/UI/TacticalLevelItem.prefab"));
            }
            else if(name=="LevelDetailView")
            {
                Ensure<LevelMapPreviewGraphic>(Node(root.transform,"Panel/Map").gameObject).raycastTarget=false;
                for(int i=1;i<=5;i++)root.transform.Find("Panel/Star"+i).GetComponent<Image>().sprite=AssetDatabase.LoadAssetAtPath<Sprite>(Art+"/Icons/star.png");
                Scroll(root.transform,"Panel/EnemyPortraits",1);
                var enemyContent=Node(root.transform,"Panel/EnemyPortraits/Viewport/Content");
                enemyContent.anchorMin=Vector2.zero;enemyContent.anchorMax=new Vector2(0,1);enemyContent.pivot=new Vector2(0,.5f);enemyContent.anchoredPosition=Vector2.zero;enemyContent.sizeDelta=Vector2.zero;
                var enemyGrid=enemyContent.GetComponent<GridLayoutGroup>();enemyGrid.constraint=GridLayoutGroup.Constraint.FixedRowCount;enemyGrid.constraintCount=1;enemyGrid.cellSize=new Vector2(156,140);enemyGrid.spacing=new Vector2(12,0);
                var enemyFit=enemyContent.GetComponent<ContentSizeFitter>();enemyFit.verticalFit=ContentSizeFitter.FitMode.Unconstrained;enemyFit.horizontalFit=ContentSizeFitter.FitMode.PreferredSize;
                var enemyScroll=root.transform.Find("Panel/EnemyPortraits").GetComponent<ScrollRect>();enemyScroll.horizontal=true;enemyScroll.vertical=false;enemyScroll.horizontalScrollbar=null;enemyScroll.verticalScrollbar=null;
                var enemyViewport=Node(root.transform,"Panel/EnemyPortraits/Viewport");Stretch(enemyViewport);enemyViewport.offsetMin=new Vector2(12,8);enemyViewport.offsetMax=new Vector2(-12,-8);
                foreach(var scrollbar in enemyScroll.GetComponentsInChildren<Scrollbar>(true))scrollbar.gameObject.SetActive(false);
                ButtonAt(root.transform,"Panel/IntroBtn","Game Intro",false);
                TextAt(root.transform,"Panel/LockReason","",26);
                foreach(var t in root.GetComponentsInChildren<TMP_Text>(true)) if(t.name!="Label")t.alignment=TextAlignmentOptions.TopLeft;
            }
            else if(name=="HudView")
            {
                foreach(string band in new[]{"TopBar","BottomBar"})
                {var tr=root.transform.Find(band);if(tr!=null)tr.gameObject.SetActive(false);}
                BuildTowerActions(root);
                BuildTowerBuildMenu(root);
            }
            else if(name=="TowerInfoView")
            {
                foreach(var fit in root.GetComponentsInChildren<UIFitInParent>(true))UnityEngine.Object.DestroyImmediate(fit);
                ButtonAt(root.transform,"Panel/RangeBtn","Range",false);
                ImageAt(root.transform,"Panel/TowerIcon").raycastTarget=false;
                TextAt(root.transform,"Panel/UpgradeInfo","",23);
                Image backdropImage=ImageAt(root.transform,"Bg");backdropImage.color=new Color(Ink.r,Ink.g,Ink.b,.66f);backdropImage.raycastTarget=true;
                ImageAt(root.transform,"Panel").raycastTarget=true;
                root.transform.Find("Panel/TowerIcon").gameObject.SetActive(true);
            }
            else if(name=="TowerCodexView")
            {
                var old=root.GetComponent<UIResponsivePage>();if(old!=null)UnityEngine.Object.DestroyImmediate(old);
                foreach(var fit in root.GetComponentsInChildren<UIFitInParent>(true))UnityEngine.Object.DestroyImmediate(fit);
                Stretch(Node(root.transform,"Panel"));
                var panelImage=root.transform.Find("Panel").GetComponent<Image>();if(panelImage!=null){panelImage.color=Color.clear;panelImage.raycastTarget=false;}
                foreach(string p in new[]{"Panel/List","Panel/LeftBtn","Panel/RightBtn","Panel/PageText"})
                {var tr=root.transform.Find(p);if(tr!=null)tr.gameObject.SetActive(false);}
                Scroll(root.transform,"Panel/Cards",3);
                Node(root.transform,"Panel/Cards/Viewport/Content").GetComponent<GridLayoutGroup>().spacing=new Vector2(24,24);
                ButtonAt(root.transform,"Panel/CompareBtn","Compare",false);
                for(int i=0;i<3;i++)ButtonAt(root.transform,"Panel/Tabs/Type"+i,new[]{"Normal Tower","Blast Tower","Frost Tower"}[i],i==0);
                TextAt(root.transform,"Panel/Empty","",30);Place(root,"Panel/Empty",0,0,900,150);
                ButtonAt(root.transform,"Panel/RetryBtn","Retry",true);Place(root,"Panel/RetryBtn",0,-160,360,90);
                root.GetComponent<TowerCodexView>().Configure(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/UI/TowerCodexItem.prefab"));
                Ensure<TacticalForgeLayout>(root).Refresh();
            }
            else if(name=="MonsterCodexView")
            {
                Image background=ImageAt(root.transform,"Bg");Stretch(background.rectTransform);background.color=Ink;background.raycastTarget=false;background.transform.SetAsFirstSibling();
                TextAt(root.transform,"Panel/Title","Monster Codex",46);ButtonAt(root.transform,"Panel/CloseBtn","Back",false);
                Scroll(root.transform,"Panel/Grid",3);
                Node(root.transform,"Panel/Grid/Viewport/Content").GetComponent<GridLayoutGroup>().spacing=new Vector2(24,24);
                TextAt(root.transform,"Panel/Name","",36);
                Image portrait=ImageAt(root.transform,"Panel/Portrait");portrait.preserveAspect=true;portrait.raycastTarget=false;
                TextAt(root.transform,"Panel/Stats","",28);TextAt(root.transform,"Panel/Empty","Config load failed, see Console",30);
                ButtonAt(root.transform,"Panel/RetryBtn","Retry",true);Place(root,"Panel/RetryBtn",0,-100,360,90);
                root.GetComponent<MonsterCodexView>().Configure(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/UI/TacticalMonsterItem.prefab"));
            }
            else if(name=="LoadingView")
            {
                ButtonAt(root.transform,"Panel/RetryBtn","Retry",true);Place(root,"Panel/RetryBtn",-160,-280,280,80);
                ButtonAt(root.transform,"Panel/ReturnBtn","Quit",false);Place(root,"Panel/ReturnBtn",160,-280,280,80);
            }
            else if(name=="SplashView" || boot)
            {
                var logo=ImageAt(root.transform,"Panel/Logo");logo.sprite=AssetDatabase.LoadAssetAtPath<Sprite>(LogoPath);logo.color=Color.white;logo.preserveAspect=true;logo.raycastTarget=false;
                if(boot){Place(root,"Panel/Logo",0,380,176,176);Place(root,"Panel/HotTitle",0,230,900,80);}
                else Place(root,"Panel/Logo",0,130,400,400);
            }
            if(full || name=="HudView" || name=="TowerInfoView" || name=="TowerCodexView")
            {
                var layout=Ensure<TacticalForgeLayout>(root);layout.Refresh();
            }
            if((full && name!="MainMenuView") || name=="TowerCodexView")
            {
                var bg=ImageAt(root.transform,"Bg");bg.sprite=AssetDatabase.LoadAssetAtPath<Sprite>(Art+"/Backgrounds/page-even.png");bg.color=Color.white;bg.raycastTarget=false;Stretch(bg.rectTransform);
                var rule=ImageAt(root.transform,"Panel/ForgeHeaderLine");rule.color=Hex("252F40");rule.raycastTarget=false;
                foreach(string titlePath in new[]{"Panel/Title","Panel/DetailTitle","Panel/CodexTitle"})
                {var t=root.transform.Find(titlePath);if(t!=null)t.GetComponent<TMP_Text>().alignment=TextAlignmentOptions.Left;}
                root.GetComponent<TacticalForgeLayout>().Refresh();
            }
            // A newly created gallery has no legacy backdrop; it must precede the content.
            var backgroundNode=root.transform.Find("Bg");if(backgroundNode!=null)backgroundNode.SetAsFirstSibling();
            if(name=="PauseView")
            {
                var b=root.transform.Find("Panel/ResumeBtn");if(b!=null)Skin(b.GetComponent<Image>(),"button-primary",Cyan);
            }
            if(name=="PauseView" || name=="LevelClearView")
            {
                var bg=ImageAt(root.transform,"Bg");
                bg.sprite=AssetDatabase.LoadAssetAtPath<Sprite>(Art+"/Backgrounds/command-backdrop.png");
                bg.type=Image.Type.Simple;bg.color=Color.white;bg.raycastTarget=true;Stretch(bg.rectTransform);
                if(name=="PauseView")
                {var panel=ImageAt(root.transform,"Panel");Skin(panel,"panel",new Color(.05f,.09f,.14f,.96f));Rim(panel,Hex("42617D"));}
                else
                {
                    var panel=ImageAt(root.transform,"Panel");panel.color=Color.clear;panel.raycastTarget=false;
                    var surface=ImageAt(root.transform,"Panel/ResultSurface");Skin(surface,"panel",new Color(.035f,.065f,.10f,.96f));
                    surface.raycastTarget=false;surface.transform.SetAsFirstSibling();Rim(surface,Hex("30495F"));
                    root.GetComponent<TacticalForgeLayout>().Refresh();
                }
            }
            foreach(string path in new[]{"Panel/PlayBtn","Panel/NextBtn","Panel/UpgradeBtn"})
            {var t=root.transform.Find(path);if(t!=null){Skin(t.GetComponent<Image>(),"button-primary",Cyan);var label=t.GetComponentInChildren<TMP_Text>(true);if(label!=null)label.color=Ink;}}
            string[] dynamicLabels=name=="MainMenuView"?new[]{"Panel/ContinueBtn/Label"}
                :name=="LevelDetailView"?new[]{"Panel/PlayBtn/Label"}
                :name=="LevelClearView"?new[]{"Panel/NextBtn/Label","Panel/RetryBtn/Label"}
                :name=="TowerInfoView"?new[]{"Panel/UpgradeBtn/Label","Panel/SellBtn/Label","Panel/RangeBtn/Label"}
                :name=="TowerCodexView"?new[]{"Panel/CompareBtn/Label"}
                :name=="HudView"?new[]{"Btn_Pause/Label","SpeedButton/Label","StartButton/Label"}:Array.Empty<string>();
            foreach(string path in dynamicLabels)
            {var node=root.transform.Find(path);if(node!=null){var localizer=node.GetComponent<TextLocalizer>();if(localizer!=null)UnityEngine.Object.DestroyImmediate(localizer);}}
            if(name=="SettingView") AudioSettingsPrefabBuilder.Apply(root);
            if(!boot) ApplyContentSurfaces(root,name);
            EditorUtility.SetDirty(root);
        }
        private static void ApplyContentSurfaces(GameObject root,string name)
        {
            var surfaces=Ensure<UIContentSurfaces>(root);surfaces.Clear();
            // Opaque, distinct fills and a visible rim keep secondary controls legible on every panel.
            foreach(var button in root.GetComponentsInChildren<Button>(true))
            {
                var actions=root.transform.Find("TowerActions");
                var buildMenu=root.transform.Find("TowerBuildMenu");
                if(button.name=="Bg" || (actions!=null && button.transform.IsChildOf(actions))
                    || (buildMenu!=null && button.transform.IsChildOf(buildMenu)))continue;
                var image=button.GetComponent<Image>();if(image==null)continue;
                bool primary=button.name=="ResumeBtn" || button.name=="PlayBtn" || button.name=="NextBtn" || button.name=="UpgradeBtn"
                    || (name=="MainMenuView" && (button.name=="StartBtn" || button.name=="ContinueBtn"))
                    || (name=="SelectView" && button.name=="BriefingBtn");
                Skin(image,primary?"button-primary":"button",primary?Cyan:Surface);
                Rim(image,primary?Cyan:Hex("42617D"));
                var label=button.transform.Find("Label");
                if(label!=null){var text=label.GetComponent<TMP_Text>();if(text!=null){text.margin=new Vector4(18,8,18,8);text.color=primary?Ink:Text;text.overflowMode=TextOverflowModes.Ellipsis;}}
            }
            string[] paths;
            switch(name)
            {
                case "GameIntroView":
                    Place(root,"Panel",0,0,1060,820);
                    Place(root,"Panel/Title",0,326,948,84);
                    for(int i=1;i<=4;i++){Place(root,"Panel/Info"+i,0,200-(i-1)*112,884,104);var t=root.transform.Find("Panel/Info"+i).GetComponent<TMP_Text>();t.fontSizeMax=30;t.fontSizeMin=22;t.margin=new Vector4(8,8,8,8);}
                    Place(root,"Panel/BackBtn",-211,-322,526,88);Place(root,"Panel/CloseBtn",283,-322,382,88);
                    SharedContentPlate(root,surfaces,"Panel/ContentBacking",0,32,948,472,new[]{"Panel/Info1","Panel/Info2","Panel/Info3","Panel/Info4"});
                    paths=new[]{"Panel/Title"};break;
                case "PauseView":
                    Place(root,"Panel",0,0,680,720);Place(root,"Panel/Title",0,278,568,84);
                    for(int i=0;i<4;i++)Place(root,"Panel/"+new[]{"ResumeBtn","RestartBtn","SettingsBtn","QuitBtn"}[i],0,140-i*112,568,88);
                    paths=new[]{"Panel/Title"};break;
                case "SettingView":
                    SharedContentPlate(root,surfaces,"Panel/ContentBacking",0,-4,832,600,new[]{"Panel/LanguageText","Panel/AudioMasterLabel","Panel/AudioMasterValue","Panel/AudioMusicLabel","Panel/AudioMusicValue","Panel/AudioSfxLabel","Panel/AudioSfxValue","Panel/AudioMuteToggle/AudioMuteLabel"});
                    paths=new[]{"Panel/Title"};
                    foreach(string audio in new[]{"Master","Music","Sfx"})
                    {
                        var slider=root.transform.Find("Panel/Audio"+audio+"Slider");var image=slider.GetComponent<Image>();image.sprite=null;image.color=Color.clear;
                        var oldRim=slider.GetComponent<Outline>();if(oldRim!=null)UnityEngine.Object.DestroyImmediate(oldRim);
                        var track=(RectTransform)slider.Find("Track");track.offsetMin=new Vector2(16,0);track.offsetMax=new Vector2(-16,0);
                        var fillArea=(RectTransform)slider.Find("FillArea");fillArea.offsetMin=new Vector2(16,0);fillArea.offsetMax=new Vector2(-16,0);
                    }
                    break;
                case "TowerInfoView": paths=new[]{"Panel/Title","Panel/Stats","Panel/UpgradeInfo"};break;
                case "SellConfirmView":
                    Place(root,"Panel/TopBar",0,296,888,96);Place(root,"Panel/TowerIcon",0,182,112,112);
                    Place(root,"Panel/TowerName",0,98,888,60);Place(root,"Panel/WarnText",0,-4,888,116);
                    Place(root,"Panel/RefundLabel",-190,-120,500,64);Place(root,"Panel/RefundValue",262,-120,320,64);
                    Place(root,"Panel/ConfirmBtn",-232,-272,424,88);Place(root,"Panel/CancelBtn",232,-272,424,88);
                    paths=new[]{"Panel/TowerName","Panel/WarnText","Panel/RefundLabel","Panel/RefundValue"};break;
                case "ConfirmView":
                    var icon=ImageAt(root.transform,"Panel/DangerIcon");Skin(icon,"panel",Cyan);
                    var glyph=TextAt(root.transform,"Panel/DangerIcon/StatusGlyph","!",48);Stretch(glyph.rectTransform);glyph.alignment=TextAlignmentOptions.Center;glyph.color=Ink;
                    paths=new[]{"Panel/BodyText"};break;
                case "SelectView":paths=new[]{"Panel/Summary","Panel/Preview/Name","Panel/Preview/Stats"};break;
                case "LevelDetailView":paths=new[]{"Panel/BestStarText","Panel/RatingTarget","Panel/Info1","Panel/Info2","Panel/Info3","Panel/Info4","Panel/Info5","Panel/Info6","Panel/EnemyLabel","Panel/LockReason"};
                    var strip=root.transform.Find("Panel/EnemyPortraits").GetComponent<Image>();Skin(strip,"panel",Surface);Rim(strip,Hex("42617D"));break;
                default:paths=Array.Empty<string>();break;
            }
            foreach(string path in paths)
            {
                var target=root.transform.Find(path) as RectTransform;if(target==null)continue;
                var plate=ImageAt(root.transform,path+"Backing");Skin(plate,"panel",Surface);plate.raycastTarget=false;Rim(plate,Hex("30495F"));
                // Account for removing an existing earlier sibling before inserting it again.
                // Otherwise a second generation moves the opaque plate above its text.
                int index=target.GetSiblingIndex();
                if(plate.transform.GetSiblingIndex()<index)index--;
                plate.transform.SetSiblingIndex(index);surfaces.Add(target,plate.rectTransform);
                var text=target.GetComponent<TMP_Text>();if(text!=null){text.margin=new Vector4(18,8,18,8);text.overflowMode=TextOverflowModes.Ellipsis;text.enableAutoSizing=true;text.fontSizeMin=Mathf.Min(20,text.fontSizeMax);}
            }
            foreach(string title in new[]{"Panel/TopBar/BodyTitle","Panel/TopBar/SellTitle"})
            {var tr=root.transform.Find(title);if(tr!=null)tr.GetComponent<TMP_Text>().margin=new Vector4(20,8,20,8);}
            if(name=="ConfirmView")root.GetComponent<ConfirmView>().ArrangeContent(ConfirmType.Warning);
            surfaces.Refresh();
        }
        private static void SharedContentPlate(GameObject root,UIContentSurfaces surfaces,string path,float x,float y,float w,float h,string[] rows)
        {
            var plate=ImageAt(root.transform,path);Skin(plate,"panel",Surface);Rim(plate,Hex("30495F"));
            plate.raycastTarget=false;Place(root,path,x,y,w,h);plate.transform.SetAsFirstSibling();
            foreach(string row in rows)
            {
                var old=root.transform.Find(row+"Backing");if(old!=null)UnityEngine.Object.DestroyImmediate(old.gameObject);
                var target=root.transform.Find(row) as RectTransform;if(target==null)continue;
                surfaces.Add(target,plate.rectTransform,true);
                var text=target.GetComponent<TMP_Text>();if(text!=null){text.enableAutoSizing=true;text.overflowMode=TextOverflowModes.Ellipsis;}
            }
        }
        private static void Rim(Image image,Color color)
        {var outline=Ensure<Outline>(image.gameObject);outline.effectColor=color;outline.effectDistance=new Vector2(1,-1);outline.useGraphicAlpha=true;}
        private static void BuildGridItem()
        {
            const string path="Assets/Prefabs/UI/TacticalLevelItem.prefab";
            bool existing=File.Exists(path);
            GameObject root=existing?PrefabUtility.LoadPrefabContents(path):new GameObject("TacticalLevelItem",typeof(RectTransform));
            try
            {
                ((RectTransform)root.transform).sizeDelta=new Vector2(192,140);
                var body=ImageAt(root.transform,"Body");Stretch(body.rectTransform);Skin(body,"panel",Panel);
                Ensure<Button>(body.gameObject).targetGraphic=body;Ensure<Outline>(body.gameObject).effectDistance=new Vector2(1,-1);
                var label=TextAt(root.transform,"Body/Label","",30);Stretch(label.rectTransform);label.margin=new Vector4(10,8,10,8);label.alignment=TextAlignmentOptions.Center;
                PrefabUtility.SaveAsPrefabAsset(root,path);
            }
            finally {if(existing)PrefabUtility.UnloadPrefabContents(root);else UnityEngine.Object.DestroyImmediate(root);}
        }
        private static void BuildTowerActions(GameObject root)
        {
            CreateTowerActionArt();
            var actions=Node(root.transform,"TowerActions");
            actions.anchorMin=actions.anchorMax=actions.pivot=new Vector2(.5f,.5f);
            actions.sizeDelta=Vector2.zero;actions.anchoredPosition=Vector2.zero;actions.SetAsLastSibling();
            Button upgrade=RoundAction(root,"UpgradeBtn","Upgrade","upgrade",Cyan,new Vector2(0,146),"−90");
            Button sell=RoundAction(root,"SellBtn","Sell","sell",Hex("FFC94D"),new Vector2(-126,-72),"+22");
            Button more=RoundAction(root,"MoreBtn","More","more",Text,new Vector2(126,-72),null);
            // The plate is decorative: clicks between the three actions still reach the board.
            // 【顺序】Backdrop 必须先建、Configure 后调 —— Configure 里按名抓取并序列化引用。
            var plate=ImageAt(root.transform,"TowerActions/Backdrop");plate.sprite=AssetDatabase.LoadAssetAtPath<Sprite>(Art+"/Buttons/action-disc.png");plate.type=Image.Type.Simple;plate.color=new Color(.035f,.075f,.12f,.78f);plate.raycastTarget=false;
            plate.rectTransform.anchorMin=plate.rectTransform.anchorMax=plate.rectTransform.pivot=new Vector2(.5f,.5f);plate.rectTransform.sizeDelta=new Vector2(388,388);plate.rectTransform.anchoredPosition=Vector2.zero;plate.transform.SetAsFirstSibling();
            Ensure<TowerActionMenu>(root).Configure(actions,upgrade,sell,more);
            actions.gameObject.SetActive(false);
        }
        /// <summary>
        /// 建造圆盘（2026-11-01）：点击可建造空格时弹出的径向菜单 —— 装饰圆盘 + 三个塔图标按钮。
        /// 与 TowerActions 同一套视觉语言（同一张 action-disc / action-circle 贴图与 124px 圆钮）；
        /// 运行时行为见 TowerBuildMenu.cs（塔名/价格/可负担性由运行时按配置写入，prefab 里留空）。
        /// 【幂等】节点与组件都是 Ensure 语义，重跑不会重复创建；Backdrop 必须在 Configure 之后
        /// 再 SetAsFirstSibling 压到按钮底下（装饰、不挡射线）。
        /// </summary>
        private static void BuildTowerBuildMenu(GameObject root)
        {
            CreateTowerActionArt();
            var actions=Node(root.transform,"TowerBuildMenu");
            actions.anchorMin=actions.anchorMax=actions.pivot=new Vector2(.5f,.5f);
            actions.sizeDelta=Vector2.zero;actions.anchoredPosition=Vector2.zero;actions.SetAsLastSibling();
            // 布局口径与 TowerActions 一致：上(0,146) / 左下(-126,-72) / 右下(126,-72)，运行时还会按屏幕边缘内收
            Button normal=IconAction(root,"BuildBtn_Normal",LoadTowerPortrait("normal"),Text,new Vector2(0,146));
            Button power=IconAction(root,"BuildBtn_Power",LoadTowerPortrait("power"),Hex("FFC94D"),new Vector2(-126,-72));
            Button retard=IconAction(root,"BuildBtn_Retard",LoadTowerPortrait("retard"),Cyan,new Vector2(126,-72));
            // 【顺序】同 BuildTowerActions：Backdrop 先建、Configure 后调（序列化引用）。
            var plate=ImageAt(root.transform,"TowerBuildMenu/Backdrop");
            plate.sprite=AssetDatabase.LoadAssetAtPath<Sprite>(Art+"/Buttons/action-disc.png");plate.type=Image.Type.Simple;plate.color=new Color(.035f,.075f,.12f,.78f);plate.raycastTarget=false;
            plate.rectTransform.anchorMin=plate.rectTransform.anchorMax=plate.rectTransform.pivot=new Vector2(.5f,.5f);plate.rectTransform.sizeDelta=new Vector2(388,388);plate.rectTransform.anchoredPosition=Vector2.zero;plate.transform.SetAsFirstSibling();
            Ensure<TowerBuildMenu>(root).Configure(actions,normal,power,retard);
            actions.gameObject.SetActive(false);
        }
        private static Sprite LoadTowerPortrait(string kind)
        {
            return AssetDatabase.LoadAssetAtPath<Sprite>(Art+"/TowerPortraits/tower-"+kind+".png");
        }
        /// <summary>
        /// 建造圆盘的塔图标按钮：圆形底 + 塔头像 + 塔名 + 价格。
        /// 结构对齐 RoundAction（Icon/Label/PriceText 同名子节点，TowerBuildMenu.Configure 按名查找）；
        /// 区别是 Icon 直接用塔头像（无 accent 字形），Label/Price 运行时填充。
        /// </summary>
        private static Button IconAction(GameObject root,string name,Sprite portrait,Color accent,Vector2 position)
        {
            string path="TowerBuildMenu/"+name;
            var button=ButtonAt(root.transform,path,"",false);
            var rect=(RectTransform)button.transform;rect.anchorMin=rect.anchorMax=rect.pivot=new Vector2(.5f,.5f);
            rect.anchoredPosition=position;rect.sizeDelta=new Vector2(124,124);
            var image=button.GetComponent<Image>();image.sprite=AssetDatabase.LoadAssetAtPath<Sprite>(Art+"/Buttons/action-circle.png");image.type=Image.Type.Simple;image.color=Panel;
            Ensure<CircularRaycastFilter>(button.gameObject);
            var outline=Ensure<Outline>(image.gameObject);outline.effectColor=new Color(accent.r,accent.g,accent.b,.6f);outline.effectDistance=new Vector2(1,-1);
            var icon=ImageAt(root.transform,path+"/Icon");icon.sprite=portrait;icon.color=Color.white;icon.raycastTarget=false;icon.preserveAspect=true;
            icon.rectTransform.anchorMin=icon.rectTransform.anchorMax=icon.rectTransform.pivot=new Vector2(.5f,.5f);
            icon.rectTransform.anchoredPosition=new Vector2(0,26);icon.rectTransform.sizeDelta=new Vector2(44,44);
            var label=TextAt(root.transform,path+"/Label","",21);label.enableAutoSizing=true;label.fontSizeMin=15;label.margin=Vector4.zero;
            label.rectTransform.anchorMin=label.rectTransform.anchorMax=label.rectTransform.pivot=new Vector2(.5f,.5f);
            label.rectTransform.anchoredPosition=new Vector2(0,-8);label.rectTransform.sizeDelta=new Vector2(108,28);
            label.enableWordWrapping=false;label.overflowMode=TextOverflowModes.Ellipsis;
            var localizer=label.GetComponent<TextLocalizer>();if(localizer!=null)UnityEngine.Object.DestroyImmediate(localizer);
            var value=TextAt(root.transform,path+"/PriceText","",21);value.alignment=TextAlignmentOptions.Center;value.margin=Vector4.zero;
            value.rectTransform.anchorMin=value.rectTransform.anchorMax=value.rectTransform.pivot=new Vector2(.5f,.5f);
            value.rectTransform.anchoredPosition=new Vector2(0,-38);value.rectTransform.sizeDelta=new Vector2(82,26);
            value.enableWordWrapping=false;value.overflowMode=TextOverflowModes.Ellipsis;value.fontSizeMin=15;
            return button;
        }
        private static Button RoundAction(GameObject root,string name,string key,string icon,Color accent,Vector2 position,string price)
        {
            string path="TowerActions/"+name;
            var button=ButtonAt(root.transform,path,key,false);
            var rect=(RectTransform)button.transform;rect.anchorMin=rect.anchorMax=rect.pivot=new Vector2(.5f,.5f);
            rect.anchoredPosition=position;rect.sizeDelta=new Vector2(124,124);
            var image=button.GetComponent<Image>();image.sprite=AssetDatabase.LoadAssetAtPath<Sprite>(Art+"/Buttons/action-circle.png");image.type=Image.Type.Simple;image.color=Panel;
            Ensure<CircularRaycastFilter>(button.gameObject);
            var outline=Ensure<Outline>(image.gameObject);outline.effectColor=new Color(accent.r,accent.g,accent.b,.6f);outline.effectDistance=new Vector2(1,-1);
            var glyph=ImageAt(root.transform,path+"/Icon");glyph.sprite=AssetDatabase.LoadAssetAtPath<Sprite>(Art+"/Icons/action-"+icon+".png");glyph.color=accent;glyph.raycastTarget=false;
            glyph.rectTransform.anchorMin=glyph.rectTransform.anchorMax=glyph.rectTransform.pivot=new Vector2(.5f,.5f);
            glyph.rectTransform.anchoredPosition=new Vector2(0,price==null?20:28);glyph.rectTransform.sizeDelta=new Vector2(30,30);
            var label=TextAt(root.transform,path+"/Label",key,24);label.enableAutoSizing=true;label.fontSizeMin=18;label.margin=Vector4.zero;
            label.rectTransform.anchorMin=label.rectTransform.anchorMax=label.rectTransform.pivot=new Vector2(.5f,.5f);
            label.rectTransform.anchoredPosition=new Vector2(0,price==null?-18:-4);label.rectTransform.sizeDelta=new Vector2(96,36);
            label.enableWordWrapping=false;label.overflowMode=TextOverflowModes.Ellipsis;
            var localizer=label.GetComponent<TextLocalizer>();if(localizer!=null)UnityEngine.Object.DestroyImmediate(localizer);
            if(price!=null)
            {
                var value=TextAt(root.transform,path+"/PriceText",price,23);value.alignment=TextAlignmentOptions.Center;value.margin=Vector4.zero;
                value.rectTransform.anchorMin=value.rectTransform.anchorMax=value.rectTransform.pivot=new Vector2(.5f,.5f);
                value.rectTransform.anchoredPosition=new Vector2(0,-34);value.rectTransform.sizeDelta=new Vector2(82,28);
                value.enableWordWrapping=false;value.overflowMode=TextOverflowModes.Ellipsis;value.fontSizeMin=16;
            }
            return button;
        }
        private static void CreateTowerActionArt()
        {
            Directory.CreateDirectory(Art+"/Buttons");Directory.CreateDirectory(Art+"/Icons");
            WriteTexture("Buttons/action-circle.png",160,160,(x,y)=>new Color(1,1,1,Mathf.Clamp01(78-Vector2.Distance(new Vector2(x+.5f,y+.5f),new Vector2(80,80)))));
            WriteTexture("Buttons/action-disc.png",256,256,(x,y)=>{float r=Vector2.Distance(new Vector2(x+.5f,y+.5f),new Vector2(128,128));return new Color(1,1,1,Mathf.Clamp01(126-r)*Mathf.Clamp01(r-40));});
            WriteTexture("Icons/action-upgrade.png",48,48,(x,y)=>
                y>=8 && y<=38 && (Mathf.Abs(x-24)<=4 || (y>=24 && Mathf.Abs(Mathf.Abs(x-24)-(38-y))<=3))?Color.white:Color.clear);
            WriteTexture("Icons/action-sell.png",48,48,(x,y)=>
                Mathf.Abs(Vector2.Distance(new Vector2(x,y),new Vector2(24,24))-17)<2.5f || (x>=14 && x<=34 && Mathf.Abs(y-24)<2.5f)?Color.white:Color.clear);
            WriteTexture("Icons/action-more.png",48,48,(x,y)=>
                new[]{10,24,38}.Any(cx=>(x-cx)*(x-cx)+(y-24)*(y-24)<=16)?Color.white:Color.clear);
            foreach(string path in new[]{"Buttons/action-circle.png","Buttons/action-disc.png","Icons/action-upgrade.png","Icons/action-sell.png","Icons/action-more.png"})
            {
                string file=Art+"/"+path;AssetDatabase.ImportAsset(file);
                var importer=(TextureImporter)AssetImporter.GetAtPath(file);
                string before=EditorJsonUtility.ToJson(importer);
                importer.textureType=TextureImporterType.Sprite;importer.spriteImportMode=SpriteImportMode.Single;
                importer.alphaIsTransparency=true;importer.mipmapEnabled=false;importer.spriteBorder=Vector4.zero;
                var android=importer.GetPlatformTextureSettings("Android");android.name="Android";android.overridden=true;android.format=TextureImporterFormat.RGBA32;android.maxTextureSize=256;importer.SetPlatformTextureSettings(android);
                if(before!=EditorJsonUtility.ToJson(importer))importer.SaveAndReimport();
            }
        }
        private static void StyleCodexItem(GameObject root)
        {
            root.GetComponent<TowerCodexItem>().ConfigurePortraits(new[]{"normal","power","retard"}.Select(n=>AssetDatabase.LoadAssetAtPath<Sprite>(Art+"/TowerPortraits/tower-"+n+".png")).ToArray());
            var details=ImageAt(root.transform,"Body/DetailsBacking");Skin(details,"panel",Surface);details.raycastTarget=false;details.transform.SetAsFirstSibling();Rim(details,Hex("30495F"));
            Stretch(Node(root.transform,"Body/CardBg"));
            var bar=Node(root.transform,"Body/TopBar");bar.anchorMin=new Vector2(0,1);bar.anchorMax=new Vector2(1,1);bar.sizeDelta=new Vector2(0,4);
            foreach(string n in new[]{"TypeName","Role","DpsRow","RangeRow","SpeedRow","PriceRow","DescText"})
            {
                RectTransform r=Node(root.transform,"Body/"+n);r.anchorMin=new Vector2(0,1);r.anchorMax=new Vector2(1,1);r.pivot=new Vector2(.5f,1);
                int i=Array.IndexOf(new[]{"TypeName","Role","DpsRow","RangeRow","SpeedRow","PriceRow","DescText"},n);
                r.anchoredPosition=new Vector2(0,-new[]{275,340,405,445,485,525,565}[i]);r.sizeDelta=new Vector2(-48,i==0?60:i==1?56:i==6?65:36);
            }
            var icon=Node(root.transform,"Body/Icon");icon.anchorMin=icon.anchorMax=new Vector2(.5f,1);icon.pivot=new Vector2(.5f,1);icon.anchoredPosition=new Vector2(0,-25);icon.sizeDelta=new Vector2(220,220);
            foreach(var t in root.GetComponentsInChildren<TMP_Text>(true))
            {t.enableWordWrapping=true;t.margin=new Vector4(8,4,8,4);}
        }
        private static void BuildMonsterItem()
        {
            const string path="Assets/Prefabs/UI/TacticalMonsterItem.prefab";
            bool existing=File.Exists(path);
            var root=existing?PrefabUtility.LoadPrefabContents(path):UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/UI/TacticalLevelItem.prefab"));
            root.name="TacticalMonsterItem";
            try
            {
                var portrait=ImageAt(root.transform,"Body/Portrait");portrait.preserveAspect=true;portrait.raycastTarget=false;
                var r=portrait.rectTransform;r.anchorMin=new Vector2(.08f,.35f);r.anchorMax=new Vector2(.92f,.95f);r.offsetMin=r.offsetMax=Vector2.zero;
                var label=Node(root.transform,"Body/Label");label.anchorMin=new Vector2(0,.18f);label.anchorMax=new Vector2(1,.30f);label.offsetMin=new Vector2(24,0);label.offsetMax=new Vector2(-24,0);
                label.GetComponent<TMP_Text>().fontSizeMax=36;label.GetComponent<TMP_Text>().fontSizeMin=26;
                var detail=ImageAt(root.transform,"Body/Details");Skin(detail,"button",Panel);detail.raycastTarget=false;
                var dr=detail.rectTransform;dr.anchorMin=new Vector2(.06f,.04f);dr.anchorMax=new Vector2(.94f,.16f);dr.offsetMin=dr.offsetMax=Vector2.zero;
                var dt=TextAt(root.transform,"Body/Details/Label","View Details",28);Stretch(dt.rectTransform);dt.alignment=TextAlignmentOptions.Center;
                PrefabUtility.SaveAsPrefabAsset(root,path);
            }
            finally{if(existing)PrefabUtility.UnloadPrefabContents(root);else UnityEngine.Object.DestroyImmediate(root);}
        }
        private static void BuildBriefingEnemyItem()
        {
            const string path="Assets/Prefabs/UI/TacticalBriefingEnemyItem.prefab";bool existing=File.Exists(path);
            var root=existing?PrefabUtility.LoadPrefabContents(path):new GameObject("TacticalBriefingEnemyItem",typeof(RectTransform));
            try
            {
                ((RectTransform)root.transform).sizeDelta=new Vector2(156,140);
                var backing=Ensure<Image>(root);Skin(backing,"panel",Panel);backing.raycastTarget=false;Rim(backing,Hex("30495F"));
                var icon=ImageAt(root.transform,"Icon");icon.preserveAspect=true;icon.raycastTarget=false;
                icon.rectTransform.anchorMin=new Vector2(.16f,.30f);icon.rectTransform.anchorMax=new Vector2(.84f,.96f);icon.rectTransform.offsetMin=icon.rectTransform.offsetMax=Vector2.zero;
                var label=TextAt(root.transform,"Label","",22);label.alignment=TextAlignmentOptions.Center;
                label.rectTransform.anchorMin=new Vector2(.04f,.02f);label.rectTransform.anchorMax=new Vector2(.96f,.28f);label.rectTransform.offsetMin=label.rectTransform.offsetMax=Vector2.zero;label.margin=new Vector4(4,0,4,0);label.fontSizeMin=16;
                PrefabUtility.SaveAsPrefabAsset(root,path);
            }
            finally{if(existing)PrefabUtility.UnloadPrefabContents(root);else UnityEngine.Object.DestroyImmediate(root);}
        }
        public static void GenerateArt()
        {
            foreach(string folder in new[]{"Backgrounds","Panels","Buttons","Icons","Effects","Fonts"})Directory.CreateDirectory(Art+"/"+folder);
            string source="Docs/UI_Redesign/2026-10-26/assets/tactical-forge-keyart.png";
            if(!File.Exists(Art+"/Backgrounds/keyart.png"))File.Copy(source,Art+"/Backgrounds/keyart.png");
            WriteTexture("Panels/panel.png",128,128,(x,y)=>
            {bool inside=x+y>16 && x+y<238;bool edge=x<2||y<2||x>125||y>125||x+y<19||x+y>235;return !inside?Color.clear:edge?Hex("53677F"):Color.white;});
            foreach(string n in new[]{"button","button-primary"})WriteTexture("Buttons/"+n+".png",128,128,(x,y)=>x+y<16||x+y>238?Color.clear:Color.white);
            WriteTexture("Backgrounds/menu-shade.png",512,4,(x,y)=>new Color(.031f,.043f,.071f,Mathf.Clamp01(1.35f-x/440f)));
            WriteTexture("Backgrounds/page.png",256,4,(x,y)=>x<133?Hex("080B12"):Hex("0D1824"));
            WriteTexture("Backgrounds/page-even.png",256,4,(x,y)=>x<128?Hex("080B12"):Hex("0D1824"));
            var points=Enumerable.Range(0,10).Select(i=>new Vector2(64+Mathf.Cos((90-i*36)*Mathf.Deg2Rad)*(i%2==0?58:25),64+Mathf.Sin((90-i*36)*Mathf.Deg2Rad)*(i%2==0?58:25))).ToArray();
            WriteTexture("Icons/star.png",128,128,(x,y)=>InsidePolygon(points,x,y)?Color.white:Color.clear);
            WriteTexture("Icons/brand.png",256,256,(x,y)=>
            {float xx=Mathf.Abs(x-128);bool shield=y>20&&y<225&&xx<94&&y>20+xx*.6f;bool rim=xx>82||y<32+xx*.6f||y>214;bool tower=x>101&&x<155&&y>72&&y<190;bool crown=y>180&&y<208&&x>88&&x<168&&((x/13)%2==0);return shield&&(rim||tower||crown)?Color.white:Color.clear;});
            AssetDatabase.Refresh();
            foreach(string file in Directory.GetFiles(Art,"*.png",SearchOption.AllDirectories))
            {
                string path=file.Replace((char)92,'/');var importer=AssetImporter.GetAtPath(path) as TextureImporter;if(importer==null)continue;
                string before=EditorJsonUtility.ToJson(importer);
                importer.textureType=TextureImporterType.Sprite;importer.spriteImportMode=SpriteImportMode.Single;
                importer.alphaIsTransparency=true;importer.mipmapEnabled=false;importer.textureCompression=TextureImporterCompression.Uncompressed;
                importer.maxTextureSize=path.Contains("/TowerPortraits/")?1024:path.Contains("/Portraits/")?512:2048;
                bool photographic=path.Contains("/Portraits/") || path.Contains("/TowerPortraits/") || path.EndsWith("/keyart.png") || path.EndsWith("/command-backdrop.png");
                var android=importer.GetPlatformTextureSettings("Android");android.name="Android";android.overridden=true;
                bool actionArt=System.IO.Path.GetFileName(path).StartsWith("action-",StringComparison.Ordinal);
                android.maxTextureSize=actionArt?256:importer.maxTextureSize;android.format=photographic?TextureImporterFormat.ETC2_RGBA8:TextureImporterFormat.RGBA32;
                android.compressionQuality=50;importer.SetPlatformTextureSettings(android);
                if(path.Contains("/Panels/")||path.Contains("/Buttons/"))importer.spriteBorder=actionArt?Vector4.zero:new Vector4(20,20,20,20);
                if(before!=EditorJsonUtility.ToJson(importer))importer.SaveAndReimport();
            }
        }
        private static void WriteTexture(string path,int w,int h,Func<int,int,Color> pixel)
        {
            if(File.Exists(Art+"/"+path))return;var texture=new Texture2D(w,h,TextureFormat.RGBA32,false);var colors=new Color[w*h];
            for(int y=0;y<h;y++)for(int x=0;x<w;x++)colors[y*w+x]=pixel(x,y);texture.SetPixels(colors);texture.Apply();
            File.WriteAllBytes(Art+"/"+path,texture.EncodeToPNG());UnityEngine.Object.DestroyImmediate(texture);
        }
        private static bool InsidePolygon(Vector2[] points,float x,float y)
        {
            bool inside=false;int j=points.Length-1;
            for(int i=0;i<points.Length;j=i++)if((points[i].y>y)!=(points[j].y>y) && x<(points[j].x-points[i].x)*(y-points[i].y)/(points[j].y-points[i].y)+points[i].x)inside=!inside;
            return inside;
        }
        private static void Scroll(Transform root,string path,int columns)
        {
            RectTransform area=Node(root,path);Image image=Ensure<Image>(area.gameObject);image.color=new Color(1,1,1,.005f);
            var viewport=Node(root,path+"/Viewport");Stretch(viewport);Ensure<RectMask2D>(viewport.gameObject);
            var content=Node(root,path+"/Viewport/Content");content.anchorMin=new Vector2(0,1);content.anchorMax=new Vector2(1,1);content.pivot=new Vector2(.5f,1);content.anchoredPosition=Vector2.zero;content.sizeDelta=Vector2.zero;
            var grid=Ensure<GridLayoutGroup>(content.gameObject);grid.constraint=GridLayoutGroup.Constraint.FixedColumnCount;grid.constraintCount=columns;grid.cellSize=new Vector2(190,140);grid.spacing=new Vector2(16,16);grid.padding=new RectOffset(4,4,4,4);
            Ensure<ContentSizeFitter>(content.gameObject).verticalFit=ContentSizeFitter.FitMode.PreferredSize;
            var scroll=Ensure<ScrollRect>(area.gameObject);scroll.viewport=viewport;scroll.content=content;scroll.horizontal=false;scroll.vertical=true;scroll.movementType=ScrollRect.MovementType.Clamped;scroll.scrollSensitivity=35;
        }
        private static RectTransform Node(Transform root,string path)
        {
            Transform current=root;foreach(string part in path.Split('/'))
            {Transform found=current.Find(part);if(found==null){var go=new GameObject(part,typeof(RectTransform));go.transform.SetParent(current,false);found=go.transform;}current=found;}return (RectTransform)current;
        }
        private static Image ImageAt(Transform root,string path) {return Ensure<Image>(Node(root,path).gameObject);}
        private static TMP_Text TextAt(Transform root,string path,string text,int size)
        {
            var t=Ensure<TextMeshProUGUI>(Node(root,path).gameObject);if(_font!=null){t.font=_font;t.fontSharedMaterial=_font.material;}
            t.text=text;t.fontSize=size;t.fontSizeMax=size;t.fontSizeMin=Mathf.Min(22,size);t.enableAutoSizing=true;t.enableWordWrapping=true;t.overflowMode=TextOverflowModes.Ellipsis;t.color=Text;t.raycastTarget=false;return t;
        }
        private static Button ButtonAt(Transform root,string path,string key,bool primary)
        {
            var image=ImageAt(root,path);Skin(image,primary?"button-primary":"button",primary?Cyan:Panel);
            var b=Ensure<Button>(image.gameObject);b.targetGraphic=image;var label=TextAt(root,path+"/Label",key,28);Stretch(label.rectTransform);label.alignment=TextAlignmentOptions.Center;label.margin=new Vector4(12,6,12,6);
            Ensure<TextLocalizer>(label.gameObject).Key=key;if(primary)label.color=Ink;return b;
        }
        private static void Skin(Image image,string name,Color color)
        {
            if(image==null)return;string folder=name=="panel"?"Panels":"Buttons";image.sprite=AssetDatabase.LoadAssetAtPath<Sprite>(Art+"/"+folder+"/"+name+".png");image.type=Image.Type.Sliced;image.color=color;
        }
        private static T Ensure<T>(GameObject go) where T:Component {return go.GetComponent<T>()??go.AddComponent<T>();}
        private static void Stretch(RectTransform rect) {rect.anchorMin=Vector2.zero;rect.anchorMax=Vector2.one;rect.pivot=new Vector2(.5f,.5f);rect.anchoredPosition=Vector2.zero;rect.sizeDelta=Vector2.zero;rect.localScale=Vector3.one;}
        private static void Place(GameObject root,string path,float x,float y,float w,float h) {var r=(RectTransform)root.transform.Find(path);r.anchorMin=r.anchorMax=r.pivot=new Vector2(.5f,.5f);r.anchoredPosition=new Vector2(x,y);r.sizeDelta=new Vector2(w,h);}
        private static Color Hex(string value) {Color c;ColorUtility.TryParseHtmlString("#"+value,out c);return c;}
    }
}
