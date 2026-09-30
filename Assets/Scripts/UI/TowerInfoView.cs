using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 已建塔的升级 / 出售面板（M2-B3/B4/B5，v1 纯逻辑优先版）。
    ///
    /// 【为什么先做"逻辑优先"】升级/出售的**规则**（升级链、费用、返还、点击响应）
    /// 与美术资源无关，先把这部分打通并可用占位 UI 验证，等升级面板美术到位后
    /// 只换 prefab、不改本脚本。所以本脚本对节点**全部做了容错**：
    /// 缺哪个节点就跳过它的刷新，只打一条 warning，不阻断游戏。
    ///
    /// 【节点约定（与 UIPrefabBuilder 生成的一致）】
    ///   TowerInfoView
    ///   ├── Bg            半透明底（点它关闭面板）
    ///   ├── Panel
    ///   │   ├── Title     塔名 + 等级
    ///   │   ├── Stats     攻击力 / 射程 / 攻速 文本
    ///   │   ├── UpgradeBtn（→ Label）  升级
    ///   │   ├── SellBtn  （→ Label）  出售
    ///   │   └── CloseBtn （→ Label）  关闭
    ///
    /// 【交互约定】
    ///   - 打开：收到 TowerSelectedEvent(BaseTower)
    ///   - 关闭：收到 TowerDeselectedEvent，或点 Bg / CloseBtn
    ///   - 升级：发 TowerUpgradeRequestEvent(tower)，由 TowerManager.TryUpgrade 执行（换实例）
    ///   - 出售：本面板弹二次确认（LogWarning 占位 + 直接执行），执行后关闭
    ///
    /// 【不做的事】不直接持有 TowerManager 做业务判断，只发事件；
    /// 但升级/出售的"结果"需要立刻反映到面板（等级/费用），所以订阅升级成功事件来刷新。
    /// </summary>
    public class TowerInfoView : MonoBehaviour
    {
        // 文本
        private Text _title;
        private Text _stats;

        // 按钮
        private Button _upgradeBtn;
        private Text _upgradeLabel;
        private Button _sellBtn;
        private Text _sellLabel;
        private Button _closeBtn;
        private Button _bgBtn;

        /// <summary>当前面板展示的塔</summary>
        private BaseTower _tower;

        /// <summary>面板 prefab 的逻辑名（ResTable 登记）</summary>
        public const string LogicalName = "TowerInfoView";

        private void Awake()
        {
            BindNodes();
            SetContentVisible(false);
        }

        private void OnEnable()
        {
            EventDispatcher.AddEventListener<BaseTower>(EventName.TowerSelectedEvent, OnTowerSelected);
            EventDispatcher.AddEventListener(EventName.TowerDeselectedEvent, OnTowerDeselected);
            EventDispatcher.AddEventListener<BaseTower>(EventName.TowerUpgradeSuccess, OnUpgradeSuccess);
            EventDispatcher.AddEventListener<BaseTower>(EventName.DestroyTower, OnTowerDestroyed);
            EventDispatcher.AddEventListener<int, int>(EventName.GoldChangeEvent, OnGoldChanged);
        }

        private void OnDisable()
        {
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.TowerSelectedEvent, OnTowerSelected);
            EventDispatcher.RemoveEventListener(EventName.TowerDeselectedEvent, OnTowerDeselected);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.TowerUpgradeSuccess, OnUpgradeSuccess);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.DestroyTower, OnTowerDestroyed);
            EventDispatcher.RemoveEventListener<int, int>(EventName.GoldChangeEvent, OnGoldChanged);
        }

        // ------------------------------------------------------------------
        // 绑定（全部容错：缺节点只警告，不报错阻断）
        // ------------------------------------------------------------------

        private void BindNodes()
        {
            _title = FindText("Panel/Title");
            _stats = FindText("Panel/Stats");

            _upgradeBtn = FindButton("Panel/UpgradeBtn");
            _upgradeLabel = FindText("Panel/UpgradeBtn/Label");
            _sellBtn = FindButton("Panel/SellBtn");
            _sellLabel = FindText("Panel/SellBtn/Label");
            _closeBtn = FindButton("Panel/CloseBtn");
            _bgBtn = FindButton("Bg");

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

        private Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning(string.Format(
                    "[TowerInfoView] 缺少文本节点「{0}」—— 面板将跳过该项刷新（美术补齐后自动恢复）", path));
                return null;
            }
            return tr.GetComponent<Text>();
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

        private void OnTowerSelected(BaseTower tower)
        {
            Show(tower);
        }

        /// <summary>
        /// 打开面板并展示指定塔。
        /// 【为什么是公开方法】面板实例化发生在 TowerSelectedEvent 的分发过程中，
        /// 它的 OnEnable 订阅晚于本次分发 → 收不到"这一次"事件。GameFlowManager 打开后
        /// 必须显式调用本方法喂一次数据（详见 GameFlowManager.OnTowerSelected 注释）。
        /// </summary>
        public void Show(BaseTower tower)
        {
            if (tower == null)
            {
                SetContentVisible(false);
                return;
            }
            _tower = tower;
            SetContentVisible(true);
            Refresh();
        }

        private void OnTowerDeselected()
        {
            _tower = null;
            SetContentVisible(false);
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
            _tower = newTower;
            Refresh();
        }

        private void OnTowerDestroyed(BaseTower tower)
        {
            if (_tower == tower)
            {
                _tower = null;
                SetContentVisible(false);
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
                SetText(_title, "防御塔");
                SetText(_stats, string.Empty);
                return;
            }

            TowerConfig cfg = _tower.Config;
            SetText(_title, string.Format("{0}  Lv.{1}", cfg.Name, cfg.Level));
            SetText(_stats, string.Format("攻击 {0:0.#}   射程 {1:0.#} 格   攻速 {2:0.00}s", 
                cfg.Power, cfg.RadiusGrid, cfg.CooldownSec));

            RefreshButtons();
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
                if (cfg.IsMaxLevel)
                {
                    _upgradeBtn.interactable = false;
                    SetText(_upgradeLabel, "已满级");
                }
                else
                {
                    // 下一级一律由 upgradeTo 链决定（与 TowerManager.TryUpgrade 同一口径）
                    TowerConfig next = Configs.GetNextLevel(cfg);
                    int cost = next != null ? next.Prices : 0;
                    _upgradeBtn.interactable = next != null && pd.Gold >= cost;
                    SetText(_upgradeLabel, next != null
                        ? string.Format("升级 ({0})", cost)
                        : "无下一级");
                }
            }

            // ---- 出售 ----
            if (_sellBtn != null)
            {
                float rate = Configs.Global != null ? Configs.Global.SellRefundRate : 1f;
                int refund = Mathf.Max(0, Mathf.RoundToInt(cfg.SellPrice * rate));
                _sellBtn.interactable = true;
                SetText(_sellLabel, string.Format("出售 (+{0})", refund));
            }
        }

        // ------------------------------------------------------------------
        // 操作 → 事件
        // ------------------------------------------------------------------

        private void OnClickUpgrade()
        {
            if (_tower == null)
            {
                return;
            }
            EventDispatcher.TriggerEvent<BaseTower>(EventName.TowerUpgradeRequestEvent, _tower);
            // 结果由 TowerUpgradeSuccess 事件回来刷新
        }

        private void OnClickSell()
        {
            if (_tower == null)
            {
                return;
            }
            // 【v1 无弹窗】直接发请求。二次确认的 UI 在美术补齐后加进来（见 Dev_Plan C-3）。
            EventDispatcher.TriggerEvent<BaseTower>(EventName.TowerSellRequestEvent, _tower);
        }

        private void OnClickClose()
        {
            // 交给 TowerPlacement 统一取消选中（单一状态源）
            if (TowerPlacement.Instance != null)
            {
                TowerPlacement.Instance.Deselect();
            }
            else
            {
                OnTowerDeselected();
            }
        }

        private static void SetText(Text t, string value)
        {
            if (t != null && t.text != value)
            {
                t.text = value;
            }
        }
    }
}
