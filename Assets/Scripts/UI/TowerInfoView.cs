using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// Explicit tower details dialog, opened only from TowerActionMenu.More.
    /// Closing returns to radial actions without deselecting the tower.
    /// Upgrade/sell dispatch the existing gameplay requests; no economy is implemented here.
    /// </summary>
    public class TowerInfoView : MonoBehaviour
    {
        // 文本
        private TMP_Text _title;
        private TMP_Text _stats;

        // 按钮
        private Button _upgradeBtn;
        private TMP_Text _upgradeLabel;
        private Button _sellBtn;
        private TMP_Text _sellLabel;
        private Button _closeBtn;
        private Button _bgBtn;
        private Button _rangeBtn;
        private TMP_Text _upgradeInfo;
        private Image _towerIcon;
        private bool _rangeVisible = true;

        /// <summary>当前面板展示的塔</summary>
        private BaseTower _tower;

        /// <summary>
        /// 【真机诊断】上一次升级按钮可用性（-1=未知 / 0=置灰 / 1=可点）。
        /// 仅在"变化"时打日志，避免每帧刷屏；随 Show(塔) 切换重置，保证新塔首次刷新必打。
        /// </summary>
        private int _lastUpgradeInteractable = -1;

        /// <summary>面板 prefab 的逻辑名（ResTable 登记）</summary>
        public const string LogicalName = "TowerInfoView";

        private void Awake()
        {
            BindNodes();
            SetContentVisible(false);
        }

        private void OnEnable()
        {
            EventDispatcher.AddEventListener(EventName.TowerDeselectedEvent, OnTowerDeselected);
            EventDispatcher.AddEventListener<BaseTower>(EventName.TowerUpgradeSuccess, OnUpgradeSuccess);
            EventDispatcher.AddEventListener<BaseTower>(EventName.DestroyTower, OnTowerDestroyed);
            EventDispatcher.AddEventListener<int, int>(EventName.GoldChangeEvent, OnGoldChanged);
            // 语言切换：本面板在游戏中可能与暂停/设置同屏（暂停不会关面板），
            // 切语言后必须重刷标题/数值行/按钮文案（2026-10-16 多语言审计）
            EventDispatcher.AddEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
        }

        private void OnDisable()
        {
            EventDispatcher.RemoveEventListener(EventName.TowerDeselectedEvent, OnTowerDeselected);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.TowerUpgradeSuccess, OnUpgradeSuccess);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.DestroyTower, OnTowerDestroyed);
            EventDispatcher.RemoveEventListener<int, int>(EventName.GoldChangeEvent, OnGoldChanged);
            EventDispatcher.RemoveEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
            _tower = null;
        }

        /// <summary>语言已切换 → 重刷当前展示的塔（Refresh 内部同时刷按钮文案）。</summary>
        private void OnLanguageChanged(int lang)
        {
            if (_tower != null && _tower.Config != null)
            {
                Refresh();
            }
        }

        // ------------------------------------------------------------------
        // 绑定（全部容错：缺节点只警告，不报错阻断）
        // ------------------------------------------------------------------

        private void BindNodes()
        {
            _title = FindText("Panel/Title");
            _stats = FindText("Panel/Stats");
            if (_stats != null)
            {
                _stats.enableWordWrapping = true;
                _stats.enableAutoSizing = true;
                _stats.fontSizeMin = 20f;
                _stats.fontSizeMax = 32f;
                Vector2 size = _stats.rectTransform.sizeDelta;
                size.y = Mathf.Max(size.y, 130f);
                _stats.rectTransform.sizeDelta = size;
            }

            _upgradeBtn = FindButton("Panel/UpgradeBtn");
            _upgradeLabel = FindText("Panel/UpgradeBtn/Label");
            _sellBtn = FindButton("Panel/SellBtn");
            _sellLabel = FindText("Panel/SellBtn/Label");
            _closeBtn = FindButton("Panel/CloseBtn");
            _bgBtn = FindButton("Bg");
            _rangeBtn = FindButton("Panel/RangeBtn");
            _upgradeInfo = FindText("Panel/UpgradeInfo");
            _towerIcon = transform.Find("Panel/TowerIcon").GetComponent<Image>();
            if (_rangeBtn != null) _rangeBtn.onClick.AddListener(ToggleRange);

            if (_upgradeBtn != null)
            {
                _upgradeBtn.onClick.AddListener(OnClickUpgrade);
            }
            if (_sellBtn != null)
            {
                _sellBtn.onClick.AddListener(OnClickSell);
            }
            if (_closeBtn != null)
            {
                _closeBtn.onClick.AddListener(OnClickClose);
            }
            if (_bgBtn != null)
            {
                _bgBtn.onClick.AddListener(OnClickClose);
            }
        }

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning(string.Format(
                    "[TowerInfoView] 缺少文本节点「{0}」—— 面板将跳过该项刷新（美术补齐后自动恢复）", path));
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning(string.Format(
                    "[TowerInfoView] 缺少按钮节点「{0}」—— 该操作本版不可用（美术补齐后自动恢复）", path));
                return null;
            }
            return tr.GetComponent<Button>();
        }

        // ------------------------------------------------------------------
        // 事件 → 面板
        // ------------------------------------------------------------------

        /// <summary>More opens the dialog, then supplies its currently selected tower.</summary>
        public void Show(BaseTower tower)
        {
            if (tower == null)
            {
                SetContentVisible(false);
                return;
            }
            _tower = tower;
            _rangeVisible = RangeIndicatorView.Instance != null && RangeIndicatorView.Instance.gameObject.activeSelf;
            // 【真机诊断埋点】面板被打开并喂了数据 —— 升级面板本身是活的
            Debug.Log("[TowerInfoView] Show: " + tower.name);
            _lastUpgradeInteractable = -1;   // 诊断状态随塔切换重置（新塔首次刷新必打一条可用性日志）
            SetContentVisible(true);
            Refresh();
        }

        private void OnTowerDeselected()
        {
            _tower = null;
            SetContentVisible(false);
            UIManager.Instance.Close(LogicalName);
        }

        /// <summary>
        /// 升级成功 → 面板切到**新实例**。
        /// 【为什么直接收参数，而不是回查 TowerPlacement.SelectedTower】
        ///   升级是"换实例"，旧的 BaseTower 已被销毁并归还对象池。
        ///   事件里直接带着新实例，面板不需要再依赖 TowerPlacement 这个全局单例去绕一圈；
        ///   依赖越少，将来换 UI / 换状态机时改动面越小。
        /// </summary>
        private void OnUpgradeSuccess(BaseTower newTower)
        {
            if (TowerPlacement.Instance == null || TowerPlacement.Instance.SelectedTower != newTower) return;
            _tower = newTower;
            Refresh();
        }

        private void OnTowerDestroyed(BaseTower tower)
        {
            if (_tower == tower)
            {
                OnTowerDeselected();
            }
        }

        private void OnGoldChanged(int current, int delta)
        {
            if (_tower != null)
            {
                RefreshButtons();
            }
        }

        /// <summary>显示/隐藏面板内容（保留本组件启用，以便持续监听事件）</summary>
        private void SetContentVisible(bool visible)
        {
            if (_bgBtn != null)
            {
                _bgBtn.gameObject.SetActive(visible);
            }
            Transform panel = transform.Find("Panel");
            if (panel != null)
            {
                panel.gameObject.SetActive(visible);
            }
        }

        // ------------------------------------------------------------------
        // 刷新
        // ------------------------------------------------------------------

        private void Refresh()
        {
            if (_tower == null || _tower.Config == null)
            {
                SetText(_title, Localization.Get("Tower Panel") ?? "防御塔");
                SetText(_stats, string.Empty);
                return;
            }

            TowerConfig cfg = _tower.Config;
            if (_towerIcon != null)
            {
                string suffix = cfg.Type == 2 ? "Power" : cfg.Type == 3 ? "Retard" : "Normal";
                Sprite icon = ResLoader.Instance.IsReady ? ResLoader.Instance.Load<Sprite>("UI_TowerIcon_" + suffix) : null;
                _towerIcon.sprite = icon;
                _towerIcon.enabled = icon != null;
                _towerIcon.preserveAspect = true;
            }
            // 塔名走 DisplayName（多语言表；缺条目回退英文原文）
            SetText(_title, string.Format("{0}  Lv.{1}", cfg.DisplayName, cfg.Level));
            // 带上 DPS：升级值不值得，玩家看"攻击力"是看不出来的，
            // 而 power / CD 才是这条升级链真正在卖的东西。
            if (cfg.IsSlowAura)
            {
                SetText(_stats, Localization.Get("Slow {0:P0}  Range {1}  Refresh {2:0.00}s  DPS 0",
                        cfg.EffectValue, cfg.RadiusGrid, cfg.CooldownSec)
                    ?? string.Format("减速 {0:P0}   覆盖 {1} 格   刷新 {2:0.00}s   DPS 0",
                        cfg.EffectValue, cfg.RadiusGrid, cfg.CooldownSec));
            }
            else SetText(_stats, Localization.Get("ATK {0}  RNG {1}  SPD {2}s  DPS {3}",
                    cfg.Power, cfg.RadiusGrid, cfg.CooldownSec, cfg.CooldownSec > 0 ? Mathf.Round(cfg.Power / cfg.CooldownSec * 10f) / 10f : 0f)
                ?? string.Format("攻击 {0:0.#}   射程 {1:0.#} 格   攻速 {2:0.00}s   DPS {3:0.#}",
                    cfg.Power, cfg.RadiusGrid, cfg.CooldownSec, cfg.CooldownSec > 0 ? Mathf.Round(cfg.Power / cfg.CooldownSec * 10f) / 10f : 0f));

            RefreshButtons();
            RefreshRange();
        }

        /// <summary>
        /// 刷新升级/出售按钮：文案（含费用）+ 可用性。
        /// - 升级：满级 → 禁用并显示「已满级」；否则显示「升级 (费用)」，金币不足置灰
        /// - 出售：始终可用，显示「出售 (+返还)」
        /// </summary>
        private void RefreshButtons()
        {
            if (_tower == null || _tower.Config == null)
            {
                return;
            }
            TowerConfig cfg = _tower.Config;
            PlayerDataManager pd = PlayerDataManager.Instance;

            // ---- 升级 ----
            if (_upgradeBtn != null)
            {
                // 下一级一律由 upgradeTo 链决定（与 TowerManager.TryUpgrade 同一口径）
                TowerConfig next = cfg.IsMaxLevel ? null : Configs.GetNextLevel(cfg);
                if (cfg.IsMaxLevel)
                {
                    _upgradeBtn.interactable = false;
                    SetText(_upgradeLabel, Localization.Get("MAX") ?? "已满级");
                }
                else
                {
                    int cost = next != null ? next.Prices : 0;
                    _upgradeBtn.interactable = next != null && pd.Gold >= cost;
                    SetText(_upgradeLabel, next != null
                        ? (Localization.Get("Upgrade ({0})", cost) ?? string.Format("升级 ({0})", cost))
                        : (Localization.Get("No Next Level") ?? "无下一级"));
                }
                string detail = cfg.IsMaxLevel ? (Localization.Get("MAX") ?? "MAX")
                    : next == null ? (Localization.Get("No Next Level") ?? "No Next Level")
                    : TowerPresentation.UpgradeSummary(cfg, next);
                if(next != null && pd.Gold < next.Prices) detail += "\n" + (Localization.Get("Not enough gold") ?? "Not enough gold") + "  −" + (next.Prices-pd.Gold);
                SetText(_upgradeInfo,detail);

                // 【真机诊断埋点】升级按钮可用性**变化时**打一条：置灰的 Button 不会触发
                // onClick，"点升级没反应"时先看这条——若为"置灰"，原因（金币不足/无下一级/
                // 满级）直接列在括号里，不需要再猜。
                int state = _upgradeBtn.interactable ? 1 : 0;
                if (state != _lastUpgradeInteractable)
                {
                    _lastUpgradeInteractable = state;
                    Debug.Log(string.Format(
                        "[TowerInfoView] 升级按钮可用性={0}（塔={1} Lv.{2} 金币={3} 下一级费用={4} 满级={5} 有下一级={6}）",
                        _upgradeBtn.interactable ? "可点" : "置灰",
                        cfg.Name, cfg.Level, pd.Gold,
                        next != null ? next.Prices : -1, cfg.IsMaxLevel, next != null));
                }
            }

            // ---- 出售 ----
            if (_sellBtn != null)
            {
                // 返还额走统一口径（TowerManager.RefundOf）：还原塔按阵型记录里的累计投入算，
                // 与它退出前能卖的钱一致（2026-11-01 起；老存档没有投入字段时仍为 +0）
                int refund = TowerManager.RefundOf(_tower);
                _sellBtn.interactable = true;
                // 文案常驻（不再有"确认态"，所以不需要"别把它刷回去"的保护）
                SetText(_sellLabel, Localization.Get("Sell (+{0})", refund)
                    ?? string.Format("出售 (+{0})", refund));
            }
        }

        // ------------------------------------------------------------------
        // 出售：发起请求（确认交给 SellConfirmView）
        // ------------------------------------------------------------------
        // 【为什么把"原地两段式确认"删掉】UI 补全 C1 把确认升级成了独立弹窗。
        // 原地改文案的问题：① 玩家看不到这次要退回多少金币；② 面板任何一次刷新都可能
        // 把"确认出售？"的文案刷回"出售 (+46)"，确认态很难维护；
        // ③ 文案顶掉价格后，玩家不知道自己点的是哪座塔。
        // 现在本面板只负责"发起请求"，确认 + 金额展示都在 SellConfirmView 里完成。

        private void OnClickSell()
        {
            if (_tower == null)
            {
                return;
            }
            EventDispatcher.TriggerEvent<BaseTower>(EventName.TowerSellRequestEvent, _tower);
        }

        private void OnClickUpgrade()
        {
            if (_tower == null)
            {
                return;
            }
            // 【真机诊断埋点】UpgradeBtn 确实被点到了
            Debug.Log("[TowerInfoView] OnClickUpgrade: " + _tower.name);
            EventDispatcher.TriggerEvent<BaseTower>(EventName.TowerUpgradeRequestEvent, _tower);
            // 结果由 TowerUpgradeSuccess 事件回来刷新
        }

        private void OnClickClose()
        {
            // Closing details returns to the selected tower's radial actions.
            UIManager.Instance.Close(LogicalName);
        }

        private void ToggleRange() { _rangeVisible=!_rangeVisible;RefreshRange(); }
        private void RefreshRange()
        {
            if(_tower==null || _tower.Config==null)return;
            RangeIndicatorView range=RangeIndicatorView.Ensure();
            if(range!=null) {if(_rangeVisible)range.Show(_tower.Position,_tower.Config.RadiusWorld);else range.Hide();}
            if(_rangeBtn!=null)SetText(_rangeBtn.GetComponentInChildren<TMP_Text>(),
                (_rangeVisible?"✓ ":"○ ")+(Localization.Get("Range")??"Range"));
        }

        private static void SetText(TMP_Text t, string value)
        {
            if (t != null && t.text != value)
            {
                t.text = value;
            }
        }
    }
}
