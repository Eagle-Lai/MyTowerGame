using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>Nonmodal tower actions owned by the HUD. Only More opens the details prefab.</summary>
    [DisallowMultipleComponent]
    public sealed class TowerActionMenu : MonoBehaviour
    {
        [SerializeField] private RectTransform menu;
        [SerializeField] private Button upgradeButton;
        [SerializeField] private Button sellButton;
        [SerializeField] private Button moreButton;
        [SerializeField] private TMP_Text upgradeLabel;
        [SerializeField] private TMP_Text upgradePrice;
        [SerializeField] private TMP_Text sellLabel;
        [SerializeField] private TMP_Text sellPrice;
        [SerializeField] private TMP_Text moreLabel;
        private BaseTower _tower;
        private RectTransform _root;
        private Canvas _canvas;
        private Camera _worldCamera;
        private int _lastActionFrame = -1;
        private Vector2 _lastAnchor;
        private Rect _lastBounds;
        private bool _hasPlacement;

        public void Configure(RectTransform actions, Button upgrade, Button sell, Button more)
        {
            menu=actions; upgradeButton=upgrade; sellButton=sell; moreButton=more;
            upgradeLabel=upgrade.transform.Find("Label").GetComponent<TMP_Text>();
            upgradePrice=upgrade.transform.Find("PriceText").GetComponent<TMP_Text>();
            sellLabel=sell.transform.Find("Label").GetComponent<TMP_Text>();
            sellPrice=sell.transform.Find("PriceText").GetComponent<TMP_Text>();
            moreLabel=more.transform.Find("Label").GetComponent<TMP_Text>();
        }

        private void Awake()
        {
            _root=(RectTransform)transform;
            _canvas=GetComponentInParent<Canvas>();
            if (menu==null || upgradeButton==null || sellButton==null || moreButton==null)
            {
                Debug.LogError("[TowerActionMenu] HUD action references are missing; rebuild the HUD prefab.");
                enabled=false;
                return;
            }
            upgradeButton.onClick.AddListener(Upgrade);
            sellButton.onClick.AddListener(Sell);
            moreButton.onClick.AddListener(More);
            SetVisible(false);
        }

        private void OnEnable()
        {
            EventDispatcher.AddEventListener<BaseTower>(EventName.TowerSelectedEvent, Select);
            EventDispatcher.AddEventListener(EventName.TowerDeselectedEvent, Deselect);
            EventDispatcher.AddEventListener<BaseTower>(EventName.TowerUpgradeSuccess, Upgraded);
            EventDispatcher.AddEventListener<BaseTower>(EventName.DestroyTower, Destroyed);
            EventDispatcher.AddEventListener<int,int>(EventName.GoldChangeEvent, GoldChanged);
            EventDispatcher.AddEventListener<int>(EventName.LanguageChangedEvent, LanguageChanged);
            if (TowerPlacement.Instance!=null) Select(TowerPlacement.Instance.SelectedTower);
        }

        private void OnDisable()
        {
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.TowerSelectedEvent, Select);
            EventDispatcher.RemoveEventListener(EventName.TowerDeselectedEvent, Deselect);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.TowerUpgradeSuccess, Upgraded);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.DestroyTower, Destroyed);
            EventDispatcher.RemoveEventListener<int,int>(EventName.GoldChangeEvent, GoldChanged);
            EventDispatcher.RemoveEventListener<int>(EventName.LanguageChangedEvent, LanguageChanged);
            Deselect();
        }

        private void OnDestroy()
        {
            if(upgradeButton!=null) upgradeButton.onClick.RemoveListener(Upgrade);
            if(sellButton!=null) sellButton.onClick.RemoveListener(Sell);
            if(moreButton!=null) moreButton.onClick.RemoveListener(More);
        }

        private void Select(BaseTower tower) { _tower=tower; _hasPlacement=false; RefreshButtons(); SetVisible(false); }
        private void Deselect() { _tower=null; SetVisible(false); }
        private void Destroyed(BaseTower tower) { if(_tower==tower) Deselect(); }
        private void Upgraded(BaseTower tower)
        {
            if(TowerPlacement.Instance!=null && TowerPlacement.Instance.SelectedTower==tower) Select(tower);
        }
        private void GoldChanged(int gold,int delta) { RefreshButtons(); }
        private void LanguageChanged(int language) { RefreshButtons(); }

        private void LateUpdate()
        {
            bool visible=_tower!=null && _tower.IsBuilt && !HasModal();
            if (!visible) { SetVisible(false); return; }
            if(_worldCamera==null)
                _worldCamera=CameraController.Instance!=null ? CameraController.Instance.GetComponent<Camera>() : Camera.main;
            if(_worldCamera==null || _root==null) { SetVisible(false); return; }
            Vector3 point=_worldCamera.WorldToScreenPoint(_tower.Position);
            if(point.z<=0) { SetVisible(false); return; }
            Camera uiCamera=_canvas!=null && _canvas.renderMode!=RenderMode.ScreenSpaceOverlay ? _canvas.worldCamera : null;
            Vector2 local;
            if(!RectTransformUtility.ScreenPointToLocalPointInRectangle(_root,point,uiCamera,out local))return;
            // Keep the anchor on the tower. Near an edge, turn the buttons inward instead
            // of moving the entire cluster across the selected tower.
            if (!_hasPlacement || local != _lastAnchor || _root.rect != _lastBounds)
            {
                Vector2 upgrade, sell, more;
                if (!TryGetButtonPositions(local, _root.rect, out upgrade, out sell, out more))
                { SetVisible(false); return; }
                menu.localPosition = new Vector3(local.x, local.y, 0);
                ((RectTransform)upgradeButton.transform).anchoredPosition = upgrade - local;
                ((RectTransform)sellButton.transform).anchoredPosition = sell - local;
                ((RectTransform)moreButton.transform).anchoredPosition = more - local;
                _lastAnchor = local; _lastBounds = _root.rect; _hasPlacement = true;
            }
            SetVisible(true);
        }

        /// <summary>Button centers in HUD-local space; the tower anchor is never clamped.</summary>
        public static bool TryGetButtonPositions(Vector2 target, Rect bounds,
            out Vector2 upgrade, out Vector2 sell, out Vector2 more)
        {
            // Include the visible button rim and the same gutters used by the board.
            Rect centers = Rect.MinMaxRect(bounds.xMin + TacticalForgeLayout.BattleSideInset + 66,
                bounds.yMin + TacticalForgeLayout.BattleVerticalInset + 66,
                bounds.xMax - TacticalForgeLayout.BattleSideInset - 66,
                bounds.yMax - TacticalForgeLayout.BattleVerticalInset - 66);
            upgrade = target + new Vector2(0, 146);
            sell = target + new Vector2(-126, -72);
            more = target + new Vector2(126, -72);
            if (Fits(centers, upgrade) && Fits(centers, sell) && Fits(centers, more)) return true;

            float inward = Mathf.Atan2(bounds.center.y - target.y, bounds.center.x - target.x) * Mathf.Rad2Deg;
            // A fan still lies on a circle around the real tower. Tighter corner fans
            // use a larger radius so the 124px buttons retain at least an 8px gap.
            for (int shape = 0; shape < 3; shape++)
            {
                float radius = shape == 0 ? 180 : shape == 1 ? 220 : 280;
                float spread = shape == 0 ? 120 : shape == 1 ? 80 : 60;
                for (int step = 0; step < 24; step++)
                {
                    float turn = step == 0 ? 0 : ((step + 1) / 2) * 15 * (step % 2 == 1 ? 1 : -1);
                    float angle = inward + turn;
                    upgrade = target + Direction(angle + spread * .5f) * radius;
                    sell = target + Direction(angle) * radius;
                    more = target + Direction(angle - spread * .5f) * radius;
                    if (Fits(centers, upgrade) && Fits(centers, sell) && Fits(centers, more)) return true;
                }
            }
            return false;
        }

        private static Vector2 Direction(float degrees)
        { float angle = degrees * Mathf.Deg2Rad; return new Vector2(Mathf.Cos(angle), Mathf.Sin(angle)); }
        private static bool Fits(Rect bounds, Vector2 point)
        { return point.x >= bounds.xMin && point.x <= bounds.xMax && point.y >= bounds.yMin && point.y <= bounds.yMax; }

        private static bool HasModal()
        {
            var ui=UIManager.Instance;
            return ui.IsOpen(TowerInfoView.LogicalName) || ui.IsOpen(SellConfirmView.LogicalName)
                || ui.IsOpen(PauseView.LogicalName) || ui.IsOpen(SettingView.LogicalName)
                || ui.IsOpen(GameIntroView.LogicalName) || ui.IsOpen(LevelClearView.LogicalName)
                || ui.IsOpen("ConfirmView");
        }

        private void RefreshButtons()
        {
            if(_tower==null || _tower.Config==null || upgradeButton==null)return;
            var cfg=_tower.Config;
            var next=cfg.IsMaxLevel?null:Configs.GetNextLevel(cfg);
            upgradeButton.interactable=next!=null && PlayerDataManager.Instance.Gold>=next.Prices;
            upgradeLabel.text=Localization.Get("Upgrade")??"升级";
            upgradePrice.text=cfg.IsMaxLevel ? (Localization.Get("MAX")??"MAX") : next!=null?"−"+next.Prices:"—";
            // Keep the reason visible when the action is unaffordable; never imply a free upgrade.
            upgradePrice.color=next!=null && PlayerDataManager.Instance.Gold<next.Prices
                ? new Color(1f,.48f,.38f) : new Color(.89f,.95f,1f);
            sellLabel.text=Localization.Get("Sell")??"出售";
            // 返还额走统一口径（TowerManager.RefundOf）：还原塔投入为 0，这里会如实显示 +0
            sellPrice.text="+"+TowerManager.RefundOf(_tower);
            moreLabel.text=Localization.Get("More")??"More";
        }

        private bool CanAct()
        {
            if(_tower==null || !_tower.IsBuilt || _lastActionFrame==Time.frameCount || HasModal())return false;
            _lastActionFrame=Time.frameCount;
            return true;
        }
        private void Upgrade()
        {
            if(!CanAct() || !upgradeButton.interactable)return;
            EventDispatcher.TriggerEvent<BaseTower>(EventName.TowerUpgradeRequestEvent,_tower);
        }
        private void Sell()
        {
            if(!CanAct())return;
            EventDispatcher.TriggerEvent<BaseTower>(EventName.TowerSellRequestEvent,_tower);
            SetVisible(false);
        }
        private void More()
        {
            if(!CanAct())return;
            var view=UIManager.Instance.Open<TowerInfoView>(TowerInfoView.LogicalName,UILayout.NormalPanel);
            if(view!=null) { view.Show(_tower); SetVisible(false); }
            else EventDispatcher.TriggerEvent<string>(EventName.ShowTipEvent,
                Localization.Get("Tower panel not ready, cannot upgrade/sell yet")??"塔详情暂不可用");
        }
        private void SetVisible(bool value)
        {
            if(menu!=null && menu.gameObject.activeSelf!=value)menu.gameObject.SetActive(value);
        }
    }
}
