using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>Shared production layout for authored Tactical Forge prefabs. No visual objects are created at runtime.</summary>
    [ExecuteAlways, DisallowMultipleComponent]
    public sealed class TacticalForgeLayout : MonoBehaviour
    {
        public const float BattleSideInset = 56;
        public const float BattleVerticalInset = 164;
        private Vector2 _size;
        private bool _continue;
        private RectTransform _root;
        private Transform _resume;
        private string _page;
        private Rect _safeArea;
        private bool _towerComparison;
        public void SetTowerComparison(bool value){_towerComparison=value;Refresh();}
        private void OnEnable() { Refresh(true); }
        private void OnDisable()
        {
            if (Application.isPlaying && _page == "HudView" && CameraController.Instance != null)
                CameraController.Instance.SetDisplayArea(new Rect(0, 0, 1, 1));
        }
        private void LateUpdate() { Refresh(false); }
        public void Refresh(bool force = true)
        {
            if (_root == null) _root = transform as RectTransform;
            if (_root == null || _root.rect.width <= 0 || _root.rect.height <= 0) return;
            Vector2 size = _root.rect.size;
            if (force || _page == null)
            {
                _page = gameObject.name.Replace("(Clone)", "");
                _resume = _page == "MainMenuView" ? transform.Find("Panel/ContinueBtn") : null;
            }
            bool hasContinue = _resume != null && _resume.gameObject.activeSelf;
            if (!force && size == _size && hasContinue == _continue && Screen.safeArea == _safeArea) return;
            _size = size; _continue = hasContinue; _safeArea = Screen.safeArea;
            float w = size.x, h = size.y;
            bool narrow = w / h < 1.5f;
            switch (_page)
            {
                case "MainMenuView":
                    float column = Mathf.Min(720f, w * .49f);
                    Put("Panel/Logo",70,48,144,144);
                    Put("Panel/GameTitle",70,205,column,130);
                    Put("Panel/Subtitle",76,350,column,58);
                    Put("Panel/StatBg",76,h*.51f,column,120);
                    Put("Panel/StatBg/ClearText",20,10,column-40,48);
                    Put("Panel/StatBg/StarText",20,62,column-40,48);
                    Put("Panel/StartBtn",70,hasContinue?h-142:h-292,hasContinue?column/3-12:column*.78f,hasContinue?82:108);
                    Put("Panel/ContinueBtn",70,h-292,column*.78f,108);
                    Put("Panel/CodexBtn",hasContinue?70+column/3:70,h-142,column/3-12,82);
                    Put("Panel/MonsterCodexBtn",hasContinue?70+column*2/3:70+column/3,h-142,column/3-12,82);
                    Put("Panel/SettingBtn",w-232,52,168,76);
                    Put("Panel/QuitBtn",w-265,h-118,200,76);
                    Put("Panel/Version",w*.5f-350,h-38,700,30);
                    break;
                case "SelectView":
                    Header(w,"Title");
                    float gridW = (w-160)*.5f;
                    Put("Panel/Summary",64,175,gridW,60);
                    Put("Panel/Grid",64,255,gridW,h-350);
                    Put("Panel/Preview",w*.5f+16,204,gridW,h-284);
                    float pw = gridW;
                    Put("Panel/Preview/Name",12,0,pw-24,65);
                    float mapHeight = Mathf.Clamp((h-520)*.65f,180,380);
                    float actionY = h-402;
                    Put("Panel/Preview/Map",12,85,pw-24,mapHeight);
                    Put("Panel/Preview/Stats",12,mapHeight+105,pw-24,Mathf.Max(72,actionY-mapHeight-125));
                    Put("Panel/Preview/BriefingBtn",12,actionY,pw-24,96);
                    Transform content = transform.Find("Panel/Grid/Viewport/Content");
                    if (content != null)
                    {
                        GridLayoutGroup grid = content.GetComponent<GridLayoutGroup>();
                        int columns = narrow ? 4 : 5;
                        grid.constraintCount = columns;
                        grid.cellSize = new Vector2((gridW-16*(columns-1)-8)/columns,140);
                    }
                    break;
                case "LevelDetailView":
                    Header(w,"DetailTitle");
                    float left = (w-160)*.5f, rightX = w*.5f+16, rightW = left;
                    float bodyHeight = h-369;
                    float detailScale = Mathf.Min(1,bodyHeight/650);
                    float mapH = bodyHeight*.60f;
                    Put("Panel/LevelName",245,114,w-400,42);
                    Put("Panel/Map",64,200,left,mapH);
                    Put("Panel/RatingTarget",64,220+mapH,left,bodyHeight-mapH-20);
                    for(int i=0;i<5;i++) Put("Panel/Star"+(i+1),rightX+16+i*56*detailScale,200,44*detailScale,44*detailScale);
                    Put("Panel/BestStarText",rightX,200+60*detailScale,rightW,64*detailScale);
                    for(int i=0;i<6;i++) Put("Panel/Info"+(i+1),rightX+(i%2)*(rightW+16)/2,200+(140+(i/2)*66)*detailScale,(rightW-16)/2,60*detailScale);
                    Put("Panel/EnemyLabel",rightX,200+350*detailScale,rightW,52*detailScale);
                    Put("Panel/EnemyIcons",rightX,200+404*detailScale,rightW,156*detailScale);
                    Put("Panel/EnemyPortraits",rightX,200+404*detailScale,rightW,156*detailScale);
                    var enemyGrid=transform.Find("Panel/EnemyPortraits/Viewport/Content").GetComponent<GridLayoutGroup>();
                    enemyGrid.cellSize=new Vector2(156*detailScale,140*detailScale);
                    enemyGrid.spacing=new Vector2(12*detailScale,0);
                    Put("Panel/PlayBtn",rightX,h-145,rightW,96);
                    Put("Panel/ReplayBtn",64,h-145,left*.49f,90);
                    Put("Panel/IntroBtn",64+left*.51f,h-145,left*.49f,90);
                    Put("Panel/LockReason",rightX,200+574*detailScale,rightW,65*detailScale);
                    break;
                case "HudView":
                    Put("Bg_Gold",56,40,200,72); Put("Bg_Hp",272,40,220,72);
                    Put("Bg_Round",narrow?508:w*.5f-160,40,narrow?260:320,72);
                    Put("Btn_Pause",w-356,36,140,78); Put("Btn_Intro",w-200,36,144,78);
                    for(int i=0;i<3;i++)
                        Put(new[]{"Btn_Tower_Normal","Btn_Tower_Power","Btn_Tower_Retard"}[i],56+i*164,h-152,148,104);
                    Put("SpeedButton",w-390,h-136,144,88); Put("StartButton",w-230,h-136,174,88);
                    FitBattleDisplay(w,h);
                    break;
                case "TowerInfoView":
                    // Details are an explicit modal opened by More, never a reserved battle rail.
                    float tw = Mathf.Min(940,w-96), th = Mathf.Min(650,h-96);
                    Put("Panel",(w-tw)*.5f,(h-th)*.5f,tw,th);
                    Put("Panel/Title",36,30,tw-220,72);
                    Put("Panel/TowerIcon",40,142,220,220);
                    Put("Panel/Stats",300,142,tw-340,150);
                    Put("Panel/UpgradeInfo",300,302,tw-340,198);
                    Put("Panel/UpgradeBtn",36,th-124,(tw-88)*.5f,88);
                    Put("Panel/SellBtn",tw*.5f+8,th-124,(tw-88)*.5f,88);
                    Put("Panel/RangeBtn",40,390,220,76);
                    Put("Panel/CloseBtn",tw-172,30,136,72);
                    break;
                case "LevelClearView":
                    Header(w,"Title");
                    Put("Panel/LevelName",245,118,w-400,50);
                    float contentW = Mathf.Min(w-200,1400); float cx=(w-contentW)/2;
                    // Reserve the footer first; scale row allocation, never let content enter it.
                    float footerY = h - 145, resultY = 190;
                    float rowScale = Mathf.Min(1, Mathf.Max(.01f, (footerY - 24 - resultY) / 578f));
                    float rowGap = 12 * rowScale;
                    Put("Panel/Stars",cx,resultY,contentW,90*rowScale); resultY += 90*rowScale+rowGap;
                    Put("Panel/StarDetail",cx,resultY,contentW,48*rowScale); resultY += 48*rowScale+rowGap;
                    Put("Panel/RecordTip",cx,resultY,contentW,48*rowScale); resultY += 48*rowScale+rowGap;
                    Put("Panel/Stats",cx,resultY,contentW,60*rowScale); resultY += 60*rowScale+rowGap;
                    Put("Panel/RatingTimes",cx,resultY,contentW,52*rowScale); resultY += 52*rowScale+rowGap;
                    Put("Panel/RatingContext",cx,resultY,contentW,78*rowScale); resultY += 78*rowScale+rowGap;
                    Put("Panel/RatingReasons",cx,resultY,contentW,Mathf.Max(1,footerY-24-resultY));
                    Put("Panel/NextBtn",w*.55f,h-145,w*.4f,92);
                    Put("Panel/RetryBtn",64,h-145,w*.22f,92);
                    Put("Panel/SelectBtn",w*.25f+80,h-145,w*.25f-100,92);
                    break;
                case "MonsterCodexView":
                    Header(w,"Title");
                    Put("Panel/Grid",64,230,w-128,h-330);
                    Put("Panel/Name",w*.48f,240,w*.46f,80);
                    Put("Panel/Portrait",80,250,w*.36f,h-400);
                    Put("Panel/Stats",w*.48f,360,w*.46f,h-450);
                    Put("Panel/Empty",100,300,w-200,180);
                    var monsterGrid=transform.Find("Panel/Grid/Viewport/Content").GetComponent<GridLayoutGroup>();
                    int mc=narrow?2:3;monsterGrid.constraintCount=mc;monsterGrid.cellSize=new Vector2((w-136-24*(mc-1))/mc,Mathf.Min(620,h-360));
                    break;
                case "TowerCodexView":
                    Header(w,"CodexTitle");
                    Put("Panel/Tabs",64,200,w-128,82);
                    for(int i=0;i<3;i++)Put("Panel/Tabs/Type"+i,i*(Mathf.Min(360,(w-160)/3)+16),0,Mathf.Min(360,(w-160)/3),82);
                    Put("Panel/Cards",64,_towerComparison?220:325,w-128,h-(_towerComparison?390:500));
                    Put("Panel/CompareBtn",w-560,h-135,496,86);
                    var cards=transform.Find("Panel/Cards/Viewport/Content");
                    if(cards!=null)
                    {
                        var cardsGrid=cards.GetComponent<GridLayoutGroup>();
                        int cc=narrow?2:3;float cardW=(w-136-24*(cc-1))/cc;
                        cardsGrid.constraintCount=cc;cardsGrid.cellSize=new Vector2(cardW,640);
                        cardsGrid.enabled=_towerComparison;cards.GetComponent<ContentSizeFitter>().enabled=_towerComparison;
                        cards.parent.parent.GetComponent<ScrollRect>().vertical=_towerComparison;
                        var cr=(RectTransform)cards;
                        cr.anchorMin=_towerComparison?new Vector2(0,1):Vector2.zero;cr.anchorMax=Vector2.one;
                        cr.pivot=new Vector2(.5f,1);cr.anchoredPosition=Vector2.zero;cr.sizeDelta=Vector2.zero;
                        foreach(Transform card in cards)
                        {
                            if(!_towerComparison){var r=(RectTransform)card;r.anchorMin=Vector2.zero;r.anchorMax=Vector2.one;r.offsetMin=r.offsetMax=Vector2.zero;}
                            ArrangeTowerCard(card,_towerComparison);
                        }
                    }
                    break;
            }
            var surfaces=GetComponent<UIContentSurfaces>();
            if(surfaces!=null)surfaces.Refresh();
        }
        private void FitBattleDisplay(float width,float height)
        {
            if (!Application.isPlaying || CameraController.Instance == null) return;
            // Equal top/bottom gutters keep the board centered. Selection never changes framing.
            var canvas=GetComponentInParent<Canvas>();
            Camera uiCamera=canvas!=null && canvas.renderMode!=RenderMode.ScreenSpaceOverlay?canvas.worldCamera:null;
            Vector3 a=_root.TransformPoint(new Vector3(_root.rect.xMin+BattleSideInset,_root.rect.yMin+BattleVerticalInset,0));
            Vector3 b=_root.TransformPoint(new Vector3(_root.rect.xMax-BattleSideInset,_root.rect.yMax-BattleVerticalInset,0));
            Vector2 low=RectTransformUtility.WorldToScreenPoint(uiCamera,a);
            Vector2 high=RectTransformUtility.WorldToScreenPoint(uiCamera,b);
            if(Screen.width>0 && Screen.height>0)
                CameraController.Instance.SetDisplayArea(Rect.MinMaxRect(low.x/Screen.width,low.y/Screen.height,high.x/Screen.width,high.y/Screen.height),true);
        }
        private void Header(float w,string title)
        {
            Put("Panel/CloseBtn",64,40,148,76);
            Put("Panel/"+title,245,45,w-480,76);
            Put("Panel/ForgeHeaderLine",64,164,w-128,2);
        }
        public static void ArrangeTowerCard(Transform card,bool comparison)
        {
            var root=card as RectTransform;var body=card.Find("Body") as RectTransform;if(root==null||body==null)return;
            body.anchorMin=Vector2.zero;body.anchorMax=Vector2.one;body.offsetMin=body.offsetMax=Vector2.zero;body.localScale=Vector3.one;
            float w=root.rect.width,h=root.rect.height;if(w<=0 || h<=0)return;
            if(comparison)
            {
                CardPart(card,"CardBg",0,0,w,h);CardPart(card,"TopBar",0,0,w,4);
                CardPart(card,"TypeName",24,24,w-48,64);CardPart(card,"Role",24,96,w-48,60);CardPart(card,"DescText",24,175,w-48,h-190);
            }
            else
            {
                float x=w*.45f, rw=w-x-24;
                CardPart(card,"CardBg",0,0,w*.40f,h);CardPart(card,"TopBar",0,0,w*.40f,4);
                CardPart(card,"Icon",w*.035f,40,w*.33f,h-80);
                bool compact = h < 500;
                float descY = compact ? 148 : 188;
                float statsY = Mathf.Max(descY + 96, h - 192);
                CardPart(card,"TypeName",x,0,rw,compact?56:80);CardPart(card,"Role",x,compact?68:92,rw,compact?48:60);
                CardPart(card,"DescText",x,descY,rw,statsY-descY-16);CardPart(card,"Divider",x,compact?126:165,rw,2);
                string[] rows={"DpsRow","RangeRow","SpeedRow","PriceRow"};
                for(int i=0;i<rows.Length;i++)CardPart(card,rows[i],x,statsY+i*44,rw,40);
            }
            foreach(string name in new[]{"TypeName","Role","DescText","DpsRow","RangeRow","SpeedRow","PriceRow"})
            {var t=card.Find("Body/"+name).GetComponent<TMP_Text>();t.alignment=TextAlignmentOptions.TopLeft;}
        }
        private static void CardPart(Transform card,string name,float x,float y,float w,float h)
        {
            var rect=card.Find("Body/"+name) as RectTransform;if(rect==null)return;
            rect.anchorMin=rect.anchorMax=rect.pivot=new Vector2(0,1);rect.anchoredPosition=new Vector2(x,-y);rect.sizeDelta=new Vector2(w,Mathf.Max(1,h));
        }
        private void Put(string path,float x,float y,float w,float h)
        {
            RectTransform rect=transform.Find(path) as RectTransform;
            if(rect==null)return;
            rect.anchorMin=rect.anchorMax=new Vector2(0,1);rect.pivot=new Vector2(0,1);
            rect.anchoredPosition=new Vector2(x,-y);rect.sizeDelta=new Vector2(Mathf.Max(1,w),Mathf.Max(1,h));rect.localScale=Vector3.one;
        }
    }
}
