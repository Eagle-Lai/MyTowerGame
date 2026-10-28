using System;
using System.IO;
using System.Linq;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject.EditorTools
{
    /// <summary>Disposable edit-mode render of production prefab geometry, without Play Mode, gameplay or save operations.</summary>
    public static class TacticalForgePreview
    {
        public static string Capture(string name,int width=1920,int height=1080,string language="en",string state="formal-config",string outputFolder=null)
        {
            if(EditorApplication.isPlayingOrWillChangePlaymode)throw new InvalidOperationException("Edit mode preview only.");
            string output=outputFolder??"Docs/UI_Redesign/Implementation/2026-10-26/evidence";Directory.CreateDirectory(output);
            string path=name=="HotUpdateView"?"Assets/Resources/BootUI/HotUpdateView.prefab":name=="SplashView"||name=="LoadingView"?"Assets/HotUpdateUI/"+name+".prefab":"Assets/Prefabs/UI/"+name+".prefab";
            GameObject stage=new GameObject("Tactical Forge disposable preview");stage.hideFlags=HideFlags.HideAndDontSave;
            var scene=UnityEditor.SceneManagement.EditorSceneManager.NewPreviewScene();
            UnityEngine.SceneManagement.SceneManager.MoveGameObjectToScene(stage,scene);
            RenderTexture previous=RenderTexture.active;var target=new RenderTexture(width,height,24);
            try
            {
                var cameraObject=new GameObject("Preview camera",typeof(Camera));cameraObject.transform.SetParent(stage.transform,false);
                var camera=cameraObject.GetComponent<Camera>();camera.scene=scene;camera.enabled=false;camera.orthographic=true;camera.clearFlags=CameraClearFlags.SolidColor;camera.backgroundColor=new Color(.031f,.043f,.071f);camera.cullingMask=1<<31;camera.nearClipPlane=.1f;camera.farClipPlane=2000;camera.transform.localPosition=new Vector3(0,0,-1000);
                var canvasObject=new GameObject("Preview canvas",typeof(RectTransform),typeof(Canvas));canvasObject.transform.SetParent(stage.transform,false);
                float scale=Mathf.Sqrt(width/1920f*(height/1080f));Vector2 logical=new Vector2(width/scale,height/scale);
                ((RectTransform)canvasObject.transform).sizeDelta=logical;var canvas=canvasObject.GetComponent<Canvas>();canvas.renderMode=RenderMode.WorldSpace;canvas.worldCamera=camera;
                camera.orthographicSize=logical.y/2;camera.aspect=(float)width/height;target.Create();camera.targetTexture=target;
                var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(path);if(prefab==null)throw new FileNotFoundException(path);
                var root=UnityEngine.Object.Instantiate(prefab,canvasObject.transform,false);root.name=name;
                RectTransform rect=(RectTransform)root.transform;rect.anchorMin=Vector2.zero;rect.anchorMax=Vector2.one;rect.sizeDelta=rect.anchoredPosition=Vector2.zero;
                foreach(var behaviour in root.GetComponentsInChildren<MonoBehaviour>(true))if(!(behaviour is Graphic)&&!(behaviour is TacticalForgeLayout)&&!(behaviour is LayoutGroup)&&!(behaviour is ContentSizeFitter))behaviour.enabled=false;
                Populate(root,name,language,state);
                foreach(var mask in root.GetComponentsInChildren<RectMask2D>(true))mask.enabled=true;
                foreach(var group in root.GetComponentsInChildren<CanvasGroup>(true))group.alpha=1;
                Canvas.ForceUpdateCanvases();foreach(var layout in root.GetComponentsInChildren<TacticalForgeLayout>(true))layout.Refresh();
                foreach(var fit in root.GetComponentsInChildren<UIFitInParent>(true))fit.Refresh();
                foreach(var surfaces in root.GetComponentsInChildren<UIContentSurfaces>(true))surfaces.Refresh();
                foreach(var t in root.GetComponentsInChildren<TMP_Text>(true))t.ForceMeshUpdate(true,true);
                foreach(Transform t in root.GetComponentsInChildren<Transform>(true))t.gameObject.layer=31;canvasObject.layer=31;
                Canvas.ForceUpdateCanvases();camera.Render();RenderTexture.active=target;
                var image=new Texture2D(width,height,TextureFormat.RGB24,false);
                string file=output+"/"+name+"-"+language+"-"+width+"x"+height+"-"+state+"-isolated-editor-preview.png";
                try{image.ReadPixels(new Rect(0,0,width,height),0,0);image.Apply();File.WriteAllBytes(file,image.EncodeToPNG());}
                finally{UnityEngine.Object.DestroyImmediate(image);}
                WriteTextBounds(root,file+".json");
                return System.IO.Path.GetFullPath(file);
            }finally{RenderTexture.active=previous;target.Release();UnityEngine.Object.DestroyImmediate(target);UnityEditor.SceneManagement.EditorSceneManager.ClosePreviewScene(scene);}
        }

        // Reads shipping exports only. No Configs/SaveManager/LanguageManager singleton state is changed.
        private static void Populate(GameObject root,string name,string language,string state)
        {
            var words=SimpleJSON.JSONNode.Parse(File.ReadAllText("Assets/ConfigJson/tblocalization.json"));
            Func<string,string> tr=key=>
            {
                foreach(SimpleJSON.JSONNode row in words.Children)
                    if((string)row["id"]==key)return (string)row[language=="zh-Hans"?"zhHans":language=="zh-Hant"?"zhHant":"en"];
                return key;
            };
            foreach(var localizer in root.GetComponentsInChildren<TextLocalizer>(true))
            {
                var text=localizer.GetComponent<TMP_Text>();
                text.text=tr(string.IsNullOrEmpty(localizer.Key)?text.text:localizer.Key);
            }
            var levels=new cfg.TBSceneInfo(SimpleJSON.JSONNode.Parse(File.ReadAllText("Assets/ConfigJson/tbsceneinfo.json"))).DataList;
            var maps=new cfg.TBLevelMap(SimpleJSON.JSONNode.Parse(File.ReadAllText("Assets/ConfigJson/tblevelmap.json"))).DataList;
            var level=new LevelConfig(levels[0]);
            var map=maps.FirstOrDefault(x=>x.LevelId==level.Id);
            Action<string,string> textAt=(path,value)=>{var node=root.transform.Find(path);if(node!=null)node.GetComponent<TMP_Text>().text=value;};
            if(name=="ConfirmView")
            {
                bool danger=state.Contains("danger"), info=state.Contains("info"), success=state.Contains("success");
                textAt("Panel/TopBar/BodyTitle",tr(danger?"Reset Save":info?"Game Intro":success?"Save reset":"Restart Level"));
                textAt("Panel/BodyText",tr(danger?"This will erase all progress. Continue?":"Restart this level?"));
                if(info)textAt("Panel/BodyText",string.Join("\n\n",new[]{tr("Stop the monsters before they reach your base: build towers on the open tiles beside the path."),tr("Long-press a tower button, drag it onto the board, then release to build."),tr("You may slow the monsters down, but never fully block their path."),tr("Survive every round to win the level.")}));
                textAt("Panel/ConfirmBtn/Label",tr(danger||info||success?"OK":"Restart Level"));textAt("Panel/CancelBtn/Label",tr("Cancel"));
                root.GetComponent<ConfirmView>().ArrangeContent(danger?ConfirmType.Danger:info?ConfirmType.Info:success?ConfirmType.Success:ConfirmType.Warning);
            }
            if(name=="GameIntroView")
            {
                textAt("Panel/Title",tr("Game Intro"));
                string[] keys={"Stop the monsters before they reach your base: build towers on the open tiles beside the path.","Long-press a tower button, drag it onto the board, then release to build.","You may slow the monsters down, but never fully block their path.","Survive every round to win the level."};
                for(int i=0;i<keys.Length;i++)textAt("Panel/Info"+(i+1),tr(keys[i]));
            }
            if(name=="SellConfirmView")
            {
                textAt("Panel/TowerName",tr("Normal Tower")+"  Lv.1");
                var globals=SimpleJSON.JSONNode.Parse(File.ReadAllText("Assets/ConfigJson/tbglobal.json"));float rate=globals[0]["sellRefundRate"].AsFloat;
                textAt("Panel/WarnText",string.Format(tr("Refund {0}% of total investment.\nThis cannot be undone."),Mathf.RoundToInt(rate*100)));
                textAt("Panel/RefundValue","22");
            }
            if(name=="SettingView")
            {
                textAt("Panel/Title",tr("Settings")); textAt("Panel/LanguageText",tr("Language"));
                string[] audioNames={"Master","Music","Sfx"}; string[] audioKeys={"Master Volume","Music Volume","SFX Volume"};
                for(int i=0;i<3;i++){textAt("Panel/Audio"+audioNames[i]+"Label",tr(audioKeys[i]));textAt("Panel/Audio"+audioNames[i]+"Value",i==1?"65%":"80%");}
                textAt("Panel/AudioMuteToggle/AudioMuteLabel",tr("Mute"));
                root.transform.Find("Panel/LanguageDropdown/Label").GetComponent<TMP_Text>().text=language=="en"?"English":language=="zh-Hans"?"简体中文":"繁體中文";
            }
            if(name=="MainMenuView")
            {
                root.transform.Find("Panel/ContinueBtn").gameObject.SetActive(false);
                textAt("Panel/StatBg/ClearText",string.Format(tr("Cleared {0}/{1}"),0,levels.Count));
                textAt("Panel/StatBg/StarText","0/"+(levels.Count*LevelRatingEvaluator.MaxStars));
            }
            if(name=="SelectView")
            {
                Transform content=root.transform.Find("Panel/Grid/Viewport/Content");
                var template=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/UI/TacticalLevelItem.prefab");
                foreach(var row in levels)
                {
                    var item=UnityEngine.Object.Instantiate(template,content,false);item.SetActive(true);
                    item.transform.Find("Body/Label").GetComponent<TMP_Text>().text=SelectView.FormatGridLabel(row.Id,row.Id==level.Id,tr(state.Contains("legacy")?"Legacy clear; current version unrated":"Current version unrated"));
                }
                textAt("Panel/Title",tr("Select Level"));
                textAt("Panel/Summary",string.Format(tr("Cleared {0}/{1}"),0,levels.Count));
                textAt("Panel/Preview/Name",string.Format(tr("Level {0}"),level.Id));
                textAt("Panel/Preview/Stats",string.Format(tr("Waves     {0}"),level.RoundCount)+"\n"+tr("Current version unrated"));
                if(map!=null)root.transform.Find("Panel/Preview/Map").GetComponent<LevelMapPreviewGraphic>().Bind(new LevelMapConfig(map));
            }
            if(name=="LevelDetailView")
            {
                textAt("Panel/DetailTitle",string.Format(tr("Level {0} Detail"),level.Id));
                textAt("Panel/LevelName",string.Format(tr("Level {0}"),level.Id));
                textAt("Panel/BestStarText",tr(state.Contains("legacy")?"Legacy clear; current version unrated":"Current version unrated"));
                for(int i=1;i<=5;i++)root.transform.Find("Panel/Star"+i).GetComponent<Image>().color=new Color(.28f,.35f,.44f);
                var rating=SimpleJSON.JSONNode.Parse(File.ReadAllText("Assets/ConfigJson/tblevelrating.json")).Children.FirstOrDefault(x=>x["id"].AsInt==level.Id);
                string[] profileKeys={"Very Easy","Easy","Below Medium","Medium","Above Medium","Hard","Very Hard","Extreme"};
                string profileId=rating!=null?(string)rating["profileId"]:"";int profileTier;
                string profileName=profileId.Length>1 && int.TryParse(profileId.Substring(1),out profileTier) && profileTier>=1 && profileTier<=profileKeys.Length?tr(profileKeys[profileTier-1]):profileId;
                textAt("Panel/Info1",string.Format(tr("Waves     {0}"),level.RoundCount));
                textAt("Panel/Info2",string.Format(tr("Balance preset: {0}"),profileName));
                textAt("Panel/Info3",string.Format(tr("Start Gold {0}"),level.InitialGold));
                textAt("Panel/Info4",string.Format(tr("Start HP   {0}"),level.InitialHp));
                textAt("Panel/Info5",tr(new[]{"Campaign Stage I","Campaign Stage II","Campaign Stage III","Campaign Stage IV","Campaign Stage V"}[Mathf.Clamp(level.Difficulty,1,5)-1]));
                textAt("Panel/Info6",string.Format(tr("Best combat: {0}"),RatingPresentation.Time(0)));
                string target=rating!=null?string.Format(tr("Five-star target: full HP, no leaks, all enemies defeated; combat ≤ {0}"),RatingPresentation.Time(rating["parCombatTimeMs"].AsLong)):tr("Rating config missing or invalid");
                textAt("Panel/RatingTarget",target+"\n"+tr("Combat time excludes preparation, inter-wave waits and pauses")+(rating!=null && (string)rating["calibrationStatus"]=="verified_unity_reference"?"":"\n"+tr("Time baseline pending verification")));
                bool locked=state.Contains("locked");
                textAt("Panel/LockReason",locked?tr("Clear the previous level first"):"");
                root.transform.Find("Panel/LockReason").gameObject.SetActive(locked);
                root.transform.Find("Panel/PlayBtn").gameObject.SetActive(!locked);
                root.transform.Find("Panel/ReplayBtn").gameObject.SetActive(!locked);
                textAt("Panel/EnemyLabel",tr("Enemies in this level"));
                textAt("Panel/EnemyIcons",tr("Current version unrated"));
                var roundRows=SimpleJSON.JSONNode.Parse(File.ReadAllText("Assets/ConfigJson/tbrounddata.json"));
                var groupRows=SimpleJSON.JSONNode.Parse(File.ReadAllText("Assets/ConfigJson/tbenemylist.json"));
                var waveIds=new System.Collections.Generic.HashSet<int>();var enemyIds=new System.Collections.Generic.HashSet<int>();
                foreach(SimpleJSON.JSONNode row in roundRows.Children)if(level.RoundIds.Contains(row["id"].AsInt))foreach(SimpleJSON.JSONNode id in row["EnemyIndexs"].Children)waveIds.Add(id.AsInt);
                foreach(SimpleJSON.JSONNode row in groupRows.Children)if(waveIds.Contains(row["id"].AsInt))foreach(SimpleJSON.JSONNode id in row["EnemyIndexs"].Children)enemyIds.Add(id.AsInt);
                var enemyRows=new cfg.TBEnemyData(SimpleJSON.JSONNode.Parse(File.ReadAllText("Assets/ConfigJson/tbenemydata.json"))).DataList.Where(x=>enemyIds.Contains(x.Id)).GroupBy(x=>x.ResName).Select(x=>x.First());
                var itemPrefab=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/UI/TacticalBriefingEnemyItem.prefab");
                foreach(var enemy in enemyRows)
                {
                    var item=UnityEngine.Object.Instantiate(itemPrefab,root.transform.Find("Panel/EnemyPortraits/Viewport/Content"),false);
                    item.transform.Find("Icon").GetComponent<Image>().sprite=AssetDatabase.LoadAssetAtPath<Sprite>("Assets/_UIAssets/UI/TacticalForge/Portraits/"+enemy.ResName+".png");
                    item.transform.Find("Label").GetComponent<TMP_Text>().text=tr(enemy.Name);
                }
                root.transform.Find("Panel/EnemyIcons").gameObject.SetActive(false);
                if(map!=null)root.transform.Find("Panel/Map").GetComponent<LevelMapPreviewGraphic>().Bind(new LevelMapConfig(map));
            }
            if(name=="LevelClearView")
            {
                bool pending=state=="synthetic-savefailed" || state.Contains("savefailed");
                textAt("Panel/Title",tr("Level Clear!"));textAt("Panel/LevelName",string.Format(tr("Level {0}"),level.Id));
                textAt("Panel/Stars",SelectView.StarRichText(3));
                textAt("Panel/StarDetail",string.Format(tr("This {0}    Best {1}"),"3/5","2/5"));
                root.transform.Find("Panel/RecordTip").gameObject.SetActive(true);
                textAt("Panel/RecordTip",pending?tr("Record could not be saved; retry save"):tr("★ New Record! Best stars improved"));
                textAt("Panel/Stats",string.Format(tr("HP {0}/{1}    Kills {2}    Leaks {3}"),8,10,120,2));
                textAt("Panel/RatingTimes",string.Format(tr("Combat {0} / Par {1} · Level {2}"),"02:15.000","02:00.000","03:10.000"));
                textAt("Panel/RatingContext",tr("Very Easy")+" · "+string.Format(tr("Balance preset: {0}"),tr("Very Easy"))+"\n"+string.Format(tr("Boss leaks {0} · Critical leaks {1}"),1,2));
                textAt("Panel/RatingReasons",tr("Defense failed")+" · "+tr("Invalid combat timer")+" · "+tr("Incomplete waves")+" · "+tr("Spawn count mismatch")+" · "+tr("Enemy accounting mismatch"));
                root.transform.Find("Panel/NextBtn").gameObject.SetActive(!pending);
                textAt("Panel/RetryBtn/Label",tr(pending?"Retry Save":"Replay"));
            }
            if(name=="HudView")
            {
                textAt("Bg_Gold/GoldText",level.InitialGold.ToString());
                textAt("Bg_Hp/HpText",level.InitialHp+"/"+level.InitialHp);
                textAt("Bg_Round/RoundText",tr("Ready"));
                var board=new GameObject("Formal map layout preview",typeof(RectTransform),typeof(LevelMapPreviewGraphic));board.transform.SetParent(root.transform,false);board.transform.SetAsFirstSibling();
                var boardRect=(RectTransform)board.transform;boardRect.anchorMin=Vector2.zero;boardRect.anchorMax=Vector2.one;boardRect.offsetMin=new Vector2(TacticalForgeLayout.BattleSideInset,TacticalForgeLayout.BattleVerticalInset);boardRect.offsetMax=-boardRect.offsetMin;
                if(map!=null)board.GetComponent<LevelMapPreviewGraphic>().Bind(new LevelMapConfig(map));
                var actions=(RectTransform)root.transform.Find("TowerActions");actions.gameObject.SetActive(state!="formal-prepare");
                var rootRect=((RectTransform)root.transform).rect;
                int columns=map.Cols, rows=map.Rows;
                float unit=Mathf.Min((rootRect.width-2*TacticalForgeLayout.BattleSideInset)/columns,(rootRect.height-2*TacticalForgeLayout.BattleVerticalInset)/rows);
                float column=state.Contains("left")?0:state.Contains("right")?columns-1:columns/2;
                float row=state.Contains("top")?0:state.Contains("bottom")?rows-1:rows/2;
                Vector2 selected=new Vector2((column-(columns-1)*.5f)*unit,((rows-1)*.5f-row)*unit);
                actions.anchoredPosition=selected;
                Vector2 upgradePosition,sellPosition,morePosition;
                if(!TowerActionMenu.TryGetButtonPositions(selected,rootRect,out upgradePosition,out sellPosition,out morePosition))throw new InvalidOperationException("No safe tower-action arrangement for preview.");
                ((RectTransform)actions.Find("UpgradeBtn")).anchoredPosition=upgradePosition-selected;
                ((RectTransform)actions.Find("SellBtn")).anchoredPosition=sellPosition-selected;
                ((RectTransform)actions.Find("MoreBtn")).anchoredPosition=morePosition-selected;
                if(state!="formal-prepare")
                {
                    var center=new GameObject("Synthetic selected tower",typeof(RectTransform),typeof(Image));center.transform.SetParent(root.transform,false);
                    var centerRect=(RectTransform)center.transform;centerRect.anchoredPosition=actions.anchoredPosition;centerRect.sizeDelta=new Vector2(96,96);
                    center.GetComponent<Image>().sprite=AssetDatabase.LoadAssetAtPath<Sprite>("Assets/_UIAssets/UI/UI_TowerIcon_Normal.png");center.GetComponent<Image>().preserveAspect=true;center.GetComponent<Image>().raycastTarget=false;
                    actions.SetAsLastSibling();
                }
                textAt("TowerActions/UpgradeBtn/Label",tr("Upgrade"));textAt("TowerActions/SellBtn/Label",tr("Sell"));
                textAt("TowerActions/MoreBtn/Label",tr("More"));
                if(state=="synthetic-more")
                {
                    actions.gameObject.SetActive(false);
                    var detail=UnityEngine.Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/UI/TowerInfoView.prefab"),root.transform,false);detail.name="TowerInfoView";
                    var detailRect=(RectTransform)detail.transform;detailRect.anchorMin=Vector2.zero;detailRect.anchorMax=Vector2.one;detailRect.sizeDelta=detailRect.anchoredPosition=Vector2.zero;
                    foreach(var behaviour in detail.GetComponentsInChildren<MonoBehaviour>(true))if(!(behaviour is Graphic)&&!(behaviour is TacticalForgeLayout))behaviour.enabled=false;
                    Populate(detail,"TowerInfoView",language,state);
                }
            }
            if(name=="TowerInfoView")
            {
                var towerRows=new cfg.TBTowerInfo(SimpleJSON.JSONNode.Parse(File.ReadAllText("Assets/ConfigJson/tbtowerinfo.json"))).DataList;
                int towerType=state.Contains("slow")?3:state.Contains("blast")?2:1;
                int towerLevel=state.Contains("level2")?2:state.Contains("max")?3:1;
                var tower=new TowerConfig(towerRows.First(x=>x.Type==towerType&&x.Level==towerLevel));
                var nextRow=towerRows.FirstOrDefault(x=>x.Id==tower.UpgradeTo);
                var next=nextRow!=null?new TowerConfig(nextRow):null;
                root.transform.Find("Bg").gameObject.SetActive(true);root.transform.Find("Panel").gameObject.SetActive(true);
                textAt("Panel/Title",tr(tower.Name)+"  Lv."+tower.Level);
                textAt("Panel/Stats",tower.IsSlowAura?string.Format(tr("Slow {0:P0}  Range {1}  Refresh {2:0.00}s  DPS 0"),tower.EffectValue,tower.RadiusGrid,tower.CooldownSec)
                    :string.Format(tr("ATK {0}  RNG {1}  SPD {2}s  DPS {3}"),tower.Power,tower.RadiusGrid,tower.CooldownSec,Mathf.Round(tower.Power/tower.CooldownSec*10)/10));
                string upgradeText=next!=null?TowerPresentation.UpgradeSummary(tower,next,tr):tr("MAX");
                if(next!=null&&state.Contains("poor"))upgradeText+="\n"+tr("Not enough gold")+"  −"+(next.Prices-20);
                textAt("Panel/UpgradeInfo",upgradeText);
                textAt("Panel/UpgradeBtn/Label",next!=null?string.Format(tr("Upgrade ({0})"),next.Prices):tr("MAX"));
                root.transform.Find("Panel/UpgradeBtn").GetComponent<Button>().interactable=next!=null&&!state.Contains("poor");
                var globals=SimpleJSON.JSONNode.Parse(File.ReadAllText("Assets/ConfigJson/tbglobal.json"));
                float refundRate=globals[0]["sellRefundRate"].AsFloat;
                textAt("Panel/SellBtn/Label",string.Format(tr("Sell (+{0})"),Mathf.Max(0,Mathf.RoundToInt(tower.SellPrice*refundRate))));
                textAt("Panel/RangeBtn/Label",tr("Range"));
                var icon=root.transform.Find("Panel/TowerIcon").GetComponent<Image>();icon.sprite=AssetDatabase.LoadAssetAtPath<Sprite>("Assets/_UIAssets/UI/UI_TowerIcon_"+TowerCodexItem.IconSuffix(tower.Type)+".png");icon.color=Color.white;
            }
            if(name=="TowerCodexView")
            {
                bool comparison=state=="formal-compare";
                root.GetComponent<TacticalForgeLayout>().SetTowerComparison(comparison);
                textAt("Panel/CompareBtn/Label",tr(comparison?"Back":"Compare"));
                root.transform.Find("Panel/Empty").gameObject.SetActive(false);root.transform.Find("Panel/RetryBtn").gameObject.SetActive(false);
                var allTowers=new cfg.TBTowerInfo(SimpleJSON.JSONNode.Parse(File.ReadAllText("Assets/ConfigJson/tbtowerinfo.json"))).DataList;
                var towers=allTowers.Where(x=>x.Level==1);
                var template=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/UI/TowerCodexItem.prefab");
                int index=0;
                foreach(var row in towers)
                {
                    var tab=root.transform.Find("Panel/Tabs/Type"+index);tab.gameObject.SetActive(!comparison);tab.GetComponentInChildren<TMP_Text>(true).text=tr(row.Name);
                    var card=UnityEngine.Object.Instantiate(template,root.transform.Find("Panel/Cards/Viewport/Content"),false);card.SetActive(comparison||index==0);card.GetComponent<TowerCodexItem>().enabled=false;index++;
                    var t=new TowerConfig(row);card.transform.Find("Body/TypeName").GetComponent<TMP_Text>().text=tr(t.Name);
                    card.transform.Find("Body/Icon").GetComponent<Image>().sprite=AssetDatabase.LoadAssetAtPath<Sprite>("Assets/_UIAssets/UI/UI_TowerIcon_"+(t.Type==2?"Power":t.Type==3?"Retard":"Normal")+".png");
                    card.transform.Find("Body/Role").GetComponent<TMP_Text>().text=tr(t.Type==2?"Area blast · swarm clearer":t.Type==3?"Slows enemies · control":"Single-target rapid fire");
                    card.transform.Find("Body/DpsRow").GetComponent<TMP_Text>().text=t.IsSlowAura?string.Format(tr("Slow {0:P0} · DPS 0"),t.EffectValue):string.Format(tr("Damage   {0}"),t.Power);
                    card.transform.Find("Body/RangeRow").GetComponent<TMP_Text>().text=string.Format(tr("Range    {0:F1}"),t.RadiusGrid);
                    card.transform.Find("Body/SpeedRow").GetComponent<TMP_Text>().text=string.Format(tr("Speed    {0:F2}"),t.CooldownSec);
                    card.transform.Find("Body/PriceRow").GetComponent<TMP_Text>().text=string.Format(tr("Cost     {0}"),t.Prices);
                    card.transform.Find("Body/DescText").GetComponent<TMP_Text>().text=TowerPresentation.Description(t,tr);
                    if(comparison)
                    {
                        foreach(string child in new[]{"Icon","DpsRow","RangeRow","SpeedRow","PriceRow","Divider"})card.transform.Find("Body/"+child).gameObject.SetActive(false);
                        card.transform.Find("Body/DescText").GetComponent<TMP_Text>().text=string.Join("\n\n",allTowers.Where(x=>x.Type==t.Type).OrderBy(x=>x.Level).Select(x=>
                        {
                            var value=new TowerConfig(x);return "Lv."+value.Level+"\n"+(value.IsSlowAura?string.Format(tr("Slow {0:P0} · DPS 0"),value.EffectValue):string.Format(tr("Damage   {0}"),value.Power))+"\n"+string.Format(tr("Range    {0:F1}"),value.RadiusGrid)+" · "+value.CooldownSec.ToString("0.00")+"s\n"+string.Format(tr("Cost     {0}"),value.Prices);
                        }).ToArray());
                    }
                }
            }
            if(name=="MonsterCodexView")
            {
                bool detail=state=="formal-detail";root.transform.Find("Panel/Grid").gameObject.SetActive(!detail);
                foreach(string child in new[]{"Name","Portrait","Stats"})root.transform.Find("Panel/"+child).gameObject.SetActive(detail);
                root.transform.Find("Panel/Empty").gameObject.SetActive(false);root.transform.Find("Panel/RetryBtn").gameObject.SetActive(false);
                var enemies=new cfg.TBEnemyData(SimpleJSON.JSONNode.Parse(File.ReadAllText("Assets/ConfigJson/tbenemydata.json"))).DataList.GroupBy(x=>x.ResName).Select(x=>x.First()).OrderBy(x=>x.Id).ToArray();
                var template=AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/UI/TacticalMonsterItem.prefab");
                foreach(var enemy in enemies)
                {
                    var item=UnityEngine.Object.Instantiate(template,root.transform.Find("Panel/Grid/Viewport/Content"),false);item.SetActive(true);
                    item.transform.Find("Body/Label").GetComponent<TMP_Text>().text=tr(enemy.Name);
                    item.transform.Find("Body/Details/Label").GetComponent<TMP_Text>().text=tr("View Details");
                    item.transform.Find("Body/Portrait").GetComponent<Image>().sprite=AssetDatabase.LoadAssetAtPath<Sprite>("Assets/_UIAssets/UI/TacticalForge/Portraits/"+enemy.ResName+".png");
                }
                textAt("Panel/Name",tr(enemies[0].Name));
                root.transform.Find("Panel/Portrait").GetComponent<Image>().sprite=AssetDatabase.LoadAssetAtPath<Sprite>("Assets/_UIAssets/UI/TacticalForge/Portraits/"+enemies[0].ResName+".png");
                textAt("Panel/Stats","HP "+enemies[0].Hp+"\n"+tr("Speed")+" "+enemies[0].Speed+"\nFORMAL CONFIG ROW "+enemies[0].Id);
            }
            var notice=new GameObject("Preview evidence label",typeof(RectTransform),typeof(TextMeshProUGUI));notice.transform.SetParent(root.transform,false);
            var label=notice.GetComponent<TextMeshProUGUI>();label.font=root.GetComponentInChildren<TMP_Text>(true).font;label.fontSize=16;label.color=new Color(.62f,.70f,.78f);label.raycastTarget=false;
            label.text="EDITOR PREVIEW • formal configuration / isolated synthetic progress • no save I/O";
            var r=(RectTransform)notice.transform;r.anchorMin=new Vector2(0,0);r.anchorMax=new Vector2(1,0);r.pivot=new Vector2(.5f,0);r.anchoredPosition=new Vector2(0,8);r.sizeDelta=new Vector2(-128,30);
        }

        public static string ValidateAssets()
        {
            if(EditorApplication.isPlayingOrWillChangePlaymode)throw new InvalidOperationException("Edit mode only.");
            var paths=Directory.GetFiles("Assets/Prefabs/UI","*.prefab").Concat(new[]{"Assets/HotUpdateUI/SplashView.prefab","Assets/HotUpdateUI/LoadingView.prefab","Assets/Resources/BootUI/HotUpdateView.prefab"});
            var issues=new System.Collections.Generic.List<string>();int count=0;
            foreach(string file in paths)
            {
                string path=file.Replace('\\','/');var asset=AssetDatabase.LoadAssetAtPath<GameObject>(path);count++;
                if(asset==null){issues.Add("Missing prefab: "+path);continue;}
                foreach(Transform node in asset.GetComponentsInChildren<Transform>(true))
                {
                    if(GameObjectUtility.GetMonoBehavioursWithMissingScriptCount(node.gameObject)>0)issues.Add(path+" missing script: "+node.name);
                    foreach(Component component in node.GetComponents<Component>())
                    {
                        if(component==null)continue;
                        var serialized=new SerializedObject(component);var property=serialized.GetIterator();
                        while(property.NextVisible(true))
                            if(property.propertyType==SerializedPropertyType.ObjectReference && property.objectReferenceValue==null && property.objectReferenceInstanceIDValue!=0)
                                issues.Add(path+" broken reference: "+node.name+"/"+property.propertyPath);
                    }
                }
            }
            string boot="Assets/Resources/BootUI/HotUpdateView.prefab";
            var dependencies=AssetDatabase.GetDependencies(boot,true);
            foreach(string dependency in dependencies)
                if(dependency.EndsWith(".cs") && dependency.StartsWith("Assets/Scripts/"))issues.Add("AOT shell depends on hot-update script: "+dependency);
            string output="Docs/UI_Redesign/Implementation/2026-10-26/evidence/prefab-reference-check.json";
            var report=new SimpleJSON.JSONObject();report["prefabsChecked"]=count;report["issueCount"]=issues.Count;
            var errors=new SimpleJSON.JSONArray();foreach(string issue in issues)errors.Add(issue);report["issues"]=errors;
            var fonts=new SimpleJSON.JSONArray();foreach(string dependency in dependencies.Where(x=>x.Contains("/Fonts/")))fonts.Add(dependency);report["bootEmbeddedFontDependencies"]=fonts;
            File.WriteAllText(output,report.ToString(2));return output+"; issues="+issues.Count;
        }
        private static void WriteTextBounds(GameObject root,string output)
        {
            var report=new SimpleJSON.JSONObject();var issues=new SimpleJSON.JSONArray();var truncated=new SimpleJSON.JSONArray();
            var backingIssues=new SimpleJSON.JSONArray();var covered=new SimpleJSON.JSONArray();int count=0,backingCount=0;
            foreach(var text in root.GetComponentsInChildren<TMP_Text>(false))
            {
                if(!text.enabled || text.name=="Preview evidence label")continue;count++;
                Rect bounds=text.rectTransform.rect;bool outside=false;
                for(int i=0;i<text.textInfo.characterCount;i++)
                {
                    var c=text.textInfo.characterInfo[i];if(!c.isVisible)continue;
                    if(c.bottomLeft.x<bounds.xMin-.5f||c.topRight.x>bounds.xMax+.5f||c.bottomLeft.y<bounds.yMin-.5f||c.topRight.y>bounds.yMax+.5f)outside=true;
                }
                string path=AnimationUtility.CalculateTransformPath(text.transform,root.transform);
                if(outside)issues.Add(path);
                if(text.isTextTruncated)truncated.Add(path);
                // Validate actual glyphs against the authored backing, not just the text rectangle.
                Transform sibling=text.transform.parent!=null?text.transform.parent.Find(text.name+"Backing"):null;
                Image backing=sibling!=null?sibling.GetComponent<Image>():null;
                if(backing!=null && backing.transform.GetSiblingIndex()>text.transform.GetSiblingIndex())covered.Add(path);
                for(Transform ancestor=text.transform.parent;backing==null && ancestor!=null && ancestor!=root.transform;ancestor=ancestor.parent)
                {var image=ancestor.GetComponent<Image>();if(image!=null && image.enabled && image.color.a>.01f)backing=image;}
                if(backing==null)continue;
                backingCount++;bool outsideBacking=false;Rect plate=backing.rectTransform.rect;
                for(int i=0;i<text.textInfo.characterCount;i++)
                {
                    var c=text.textInfo.characterInfo[i];if(!c.isVisible)continue;
                    foreach(Vector3 corner in new[]{c.bottomLeft,c.topLeft,c.topRight,c.bottomRight})
                    {
                        Vector3 point=backing.rectTransform.InverseTransformPoint(text.transform.TransformPoint(corner));
                        if(point.x<plate.xMin-.5f || point.x>plate.xMax+.5f || point.y<plate.yMin-.5f || point.y>plate.yMax+.5f)outsideBacking=true;
                    }
                }
                if(outsideBacking)backingIssues.Add(path);
            }
            report["visibleTextCount"]=count;report["glyphsOutsideTextRect"]=issues;report["truncatedText"]=truncated;
            report["textBackingsChecked"]=backingCount;report["glyphsOutsideBacking"]=backingIssues;report["backingsAboveText"]=covered;
            File.WriteAllText(output,report.ToString(2));
        }
    }
}
