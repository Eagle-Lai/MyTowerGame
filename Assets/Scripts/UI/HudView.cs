using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 战斗 HUD（P0-9 / M2-A4）。
    ///
    /// 【设计原则】HUD 只做两件事：①把数据变化显示出来 ②把玩家操作转成事件。
    /// 它不持有任何游戏逻辑引用（不碰 TowerManager / WaveManager），
    /// 这样 UI 挂了也不会影响战斗正确性。
    ///
    /// 【节点名必须与 Assets/Editor/UIPrefabBuilder.cs 生成/维护的 prefab 严格一致】，
    /// 否则会在 Console 里看到「HUD 缺少子节点」的错误（查找是显式报错的，不静默失败）。
    /// 因此 prefab 与 .cs 是**成对修改**的。
    ///
    /// 【M2 新增：三颗塔按钮】
    ///   Btn_Tower_Normal (type=1) / Btn_Tower_Power (type=2) / Btn_Tower_Retard (type=3)
    ///   ★ 命名映射：节点里的 "Retard" ⇄ 枚举 TowerType.Slow(3)，同一件事的两种叫法，
    ///     映射只在本文件的 TowerTypeOf 与美术目录两处，别处不要各写一份。
    /// </summary>
    public class HudView : MonoBehaviour
    {
        /// <summary>ResTable / UIManager 用的逻辑名（别再各处写字符串字面量）</summary>
        public const string LogicalName = "HudView";

        // ---- 文本（全工程统一 TMP，不再用 UGUI Text）----
        private TMP_Text _goldText;
        private TMP_Text _hpText;
        private TMP_Text _roundText;

        // ---- 开始按钮 ----
        private Button _startButton;
        private TMP_Text _startLabel;

        /// <summary>
        /// 塔按钮：节点名 → (按钮, 塔型, 价格文本)。
        /// 用数组而不是一堆字段，是为了让"进入/退出放置态时统一置灰"这类操作用循环即可。
        /// </summary>
        private Button[] _towerButtons;
        private int[] _towerButtonTypes;
        private TMP_Text[] _towerPriceTexts;

        /// <summary>当前选中的塔类型与等级（M2 起由按钮决定 type；level 固定 1 = 建造等级）</summary>
        private int _towerType = 1;
        private int _towerLevel = 1;

        /// <summary>进入放置模式后按钮变灰，避免重复点</summary>
        private bool _placing;

        /// <summary>
        /// 建造栏的塔按钮（M2 起五类）。
        ///
        /// 【为什么节点名必须显式映射，不能由配置推导】
        ///   Slow(3) 在美术/节点/资源目录里叫 "Retard" —— 这处不一致无法用字符串规则还原。
        ///   所以塔型 ↔ 节点名 的对应关系**只在这里写一次**，
        ///   UIPrefabBuilder 与 prefab 三处保持同名即可（契约见 Docs/HudView_Sync_and_TowerUI_Plan.md §2）。
        ///
        /// 【为什么在 Awake 里按固定名单绑定，而不是读配置表动态生成】
        ///   HUD 的 Awake 可能早于 Configs 加载完成；靠配置决定"绑哪几个节点"会在时序上翻车。
        ///   所以：**节点绑定固定，是否显示由配置决定**（见 RefreshTowerAffordability）——
        ///   表里没有对应 type 时按钮自动隐藏，等于按表驱动，又不引入时序依赖。
        /// </summary>
        private static readonly string[] TowerNodeNames =
        {
            "Btn_Tower_Normal", "Btn_Tower_Power", "Btn_Tower_Retard",
            "Btn_Tower_Pierce", "Btn_Tower_Laser",
        };

        // 与 TowerNodeNames 一一对应（TowerType：1单体/2范围/3减速/4穿透/5激光）
        private static readonly int[] TowerNodeTypes = { 1, 2, 3, 4, 5 };

        private void Awake()
        {
            BindNodes();
            BindEvents();
        }

        private void OnDestroy()
        {
            EventDispatcher.RemoveEventListener<int, int>(EventName.GoldChangeEvent, OnGoldChanged);
            EventDispatcher.RemoveEventListener<int, int>(EventName.PlayerHpChangeEvent, OnHpChanged);
            EventDispatcher.RemoveEventListener<int>(EventName.RoundStartEvent, OnRoundStart);
            EventDispatcher.RemoveEventListener<int>(EventName.WaveStartEvent, OnWaveStart);
            // 【易错点】OnRoundClear 带一个 int 参数，必须写成 RemoveEventListener<int>；
            // 写成无参形式会匹配到 `RemoveEventListener(string, Action)` 重载并报 CS1503。
            EventDispatcher.RemoveEventListener<int>(EventName.RoundClearEvent, OnRoundClear);
            EventDispatcher.RemoveEventListener<bool>(EventName.GameOverEvent, OnGameOver);
            EventDispatcher.RemoveEventListener(EventName.BuildingTower, OnEnterPlacement);
            EventDispatcher.RemoveEventListener(EventName.CancelBuildRequestEvent, OnExitPlacement);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.BuildTowerSuccess, OnBuildSuccess);
            EventDispatcher.RemoveEventListener(EventName.PlayerStateInitEvent, RefreshAll);
        }

        // ------------------------------------------------------------------
        // 绑定
        // ------------------------------------------------------------------

        private void BindNodes()
        {
            _goldText = FindText("GoldText");
            _hpText = FindText("HpText");
            _roundText = FindText("RoundText");

            _startButton = FindButton("StartButton");
            _startLabel = FindChildText("StartButton/Label");
            if (_startButton != null)
            {
                _startButton.onClick.AddListener(OnClickStart);
            }
            if (_startLabel != null)
            {
                _startLabel.text = "开始";
            }

            // 塔按钮（五类）
            _towerButtons = new Button[TowerNodeNames.Length];
            _towerButtonTypes = new int[TowerNodeNames.Length];
            _towerPriceTexts = new TMP_Text[TowerNodeNames.Length];
            for (int i = 0; i < TowerNodeNames.Length; i++)
            {
                int type = TowerNodeTypes[i];
                _towerButtons[i] = FindButton(TowerNodeNames[i]);
                _towerButtonTypes[i] = type;
                // PriceText 是"可选节点"：老的 prefab 没有它，不应该报错，只是没有价格可显示
                _towerPriceTexts[i] = FindChildText(TowerNodeNames[i] + "/PriceText");
                if (_towerButtons[i] != null)
                {
                    int captured = type;
                    _towerButtons[i].onClick.AddListener(delegate { OnClickTower(captured); });
                }
            }
        }

        private void BindEvents()
        {
            EventDispatcher.AddEventListener<int, int>(EventName.GoldChangeEvent, OnGoldChanged);
            EventDispatcher.AddEventListener<int, int>(EventName.PlayerHpChangeEvent, OnHpChanged);
            EventDispatcher.AddEventListener<int>(EventName.RoundStartEvent, OnRoundStart);
            EventDispatcher.AddEventListener<int>(EventName.WaveStartEvent, OnWaveStart);
            // 同上：带 int 参数的回调必须显式写 <int>
            EventDispatcher.AddEventListener<int>(EventName.RoundClearEvent, OnRoundClear);
            EventDispatcher.AddEventListener<bool>(EventName.GameOverEvent, OnGameOver);
            EventDispatcher.AddEventListener(EventName.BuildingTower, OnEnterPlacement);
            EventDispatcher.AddEventListener(EventName.CancelBuildRequestEvent, OnExitPlacement);
            EventDispatcher.AddEventListener<BaseTower>(EventName.BuildTowerSuccess, OnBuildSuccess);
            EventDispatcher.AddEventListener(EventName.PlayerStateInitEvent, RefreshAll);
        }

        private TMP_Text FindText(string path)
        {
            TMP_Text t = FindChildText(path);
            if (t == null)
            {
                Debug.LogError(string.Format("[HUD] 缺少文本节点「{0}」（prefab 与 HudView.cs 不一致）", path));
            }
            return t;
        }

        /// <summary>
        /// 取子节点上的 TMP 文本组件。
        /// 【TMP_Text 而不是 TextMeshProUGUI】取基类即可，读取 .text 与颜色都不依赖具体子类；
        ///   基类还能兼容以后的 TextMeshPro（世界空间）节点，耦合更小。
        /// </summary>
        private TMP_Text FindChildText(string path)
        {
            Transform tr = transform.Find(path);
            return tr != null ? tr.GetComponent<TMP_Text>() : null;
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogError(string.Format("[HUD] 缺少按钮节点「{0}」（prefab 与 HudView.cs 不一致）", path));
                return null;
            }
            Button b = tr.GetComponent<Button>();
            if (b == null)
            {
                Debug.LogError(string.Format("[HUD] 节点「{0}」上没有 Button 组件", path));
            }
            return b;
        }

        // ------------------------------------------------------------------
        // 交互 → 事件
        // ------------------------------------------------------------------

        private void OnClickStart()
        {
            if (_startButton != null)
            {
                _startButton.interactable = false;
                if (_startLabel != null)
                {
                    _startLabel.text = "进行中";
                }
            }
            EventDispatcher.TriggerEvent(EventName.StartRoundRequestEvent);
        }

        private void OnClickTower(int type)
        {
            // 不在这里判断"是否已在放置态"——那是 TowerPlacement 的职责。
            // 统一发同一个请求事件，由它决定是进入还是退出（单一状态源，避免两边状态不一致）。
            _towerType = type;
            EventDispatcher.TriggerEvent<int, int>(EventName.BuildTowerRequestEvent, _towerType, _towerLevel);
        }

        // ------------------------------------------------------------------
        // 事件 → 显示
        // ------------------------------------------------------------------

        /// <summary>
        /// 更新「开始 / 下一回合」按钮的文字。
        /// 自动回合倒计时会用它显示 "下一回合(3)" 这样的剩余秒数。
        /// </summary>
        public void SetStartButtonLabel(string text)
        {
            if (_startLabel != null)
            {
                _startLabel.text = text;
            }
        }

        /// <summary>
        /// 按当前玩家数据刷新全部显示。
        /// 【为什么必须公开】HUD 是在关卡初始化过程中才被实例化的，而
        /// PlayerStateInitEvent 在它实例化之前就已经触发过一次 —— 只靠监听事件的话，
        /// HUD 会一直显示 prefab 里的占位文案（"金币 0"）直到第一次数值变化。
        /// 所以 GameFlowManager 打开 HUD 后会显式调用一次本方法。
        /// </summary>
        public void RefreshAll()
        {
            PlayerDataManager pd = PlayerDataManager.Instance;
            SetText(_goldText, pd.Gold.ToString());
            SetText(_hpText, string.Format("{0}/{1}", pd.Hp, pd.MaxHp));
            RefreshTowerAffordability();
        }

        private void OnGoldChanged(int current, int delta)
        {
            SetText(_goldText, current.ToString());
            // 金币变化 → 刷新塔按钮可用性（买不起的置灰）
            RefreshTowerAffordability();
        }

        /// <summary>
        /// 按当前金币刷新三颗塔按钮的 interactable。
        /// 放置中时不改（避免和"放置中"的置灰状态打架）。
        /// </summary>
        private void RefreshTowerAffordability()
        {
            if (_towerButtons == null)
            {
                return;
            }
            PlayerDataManager pd = PlayerDataManager.Instance;
            for (int i = 0; i < _towerButtons.Length; i++)
            {
                Button btn = _towerButtons[i];
                if (btn == null)
                {
                    continue;
                }

                // 按配置表决定这颗按钮是否登场：表里没有这个 type 就隐藏，
                // 免得留下"点了没反应"的死按钮。新增塔型 = 加配置行 + 加节点名。
                TowerConfig cfg = Configs.GetTowerByTypeAndLevelSilent(_towerButtonTypes[i], 1);
                if (cfg == null)
                {
                    if (btn.gameObject.activeSelf)
                    {
                        btn.gameObject.SetActive(false);
                    }
                    continue;
                }
                if (!btn.gameObject.activeSelf)
                {
                    btn.gameObject.SetActive(true);
                }

                SetText(_towerPriceTexts[i], cfg.Prices.ToString());

                // 放置中时不动 interactable：那由 SetTowerButtonState 统一管，
                // 两边都写会互相覆盖（"放置中全部置灰"会被这里刷新回可点）。
                if (!_placing)
                {
                    btn.interactable = pd.Gold >= cfg.Prices;
                }
            }
        }

        private void OnHpChanged(int current, int delta)
        {
            PlayerDataManager pd = PlayerDataManager.Instance;
            SetText(_hpText, string.Format("{0}/{1}", current, pd.MaxHp));
        }

        private void OnRoundStart(int roundIndex)
        {
            SetText(_roundText, string.Format("回合 {0}", roundIndex));
        }

        private void OnWaveStart(int waveIndex)
        {
            SetText(_roundText, string.Format("第 {0} 波", waveIndex));
        }

        private void OnRoundClear(int roundIndex)
        {
            SetText(_roundText, string.Format("回合 {0} 完成", roundIndex));
            // 恢复"开始"按钮，让玩家推进到下一回合
            if (_startButton != null)
            {
                _startButton.interactable = true;
            }
            if (_startLabel != null)
            {
                _startLabel.text = "下一回合";
            }
        }

        private void OnGameOver(bool victory)
        {
            if (_startButton != null)
            {
                _startButton.interactable = false;
            }
            if (_startLabel != null)
            {
                _startLabel.text = victory ? "已通关" : "已失败";
            }
        }

        private void OnEnterPlacement()
        {
            _placing = true;
            SetTowerButtonState(false);
        }

        private void OnExitPlacement()
        {
            _placing = false;
            SetTowerButtonState(true);
            RefreshTowerAffordability();
        }

        private void OnBuildSuccess(BaseTower tower)
        {
            // 建完后自动退出放置模式（想连建就再点一次按钮）
            OnExitPlacement();
        }

        /// <summary>统一设置三颗塔按钮的可用性（放置中全部置灰）</summary>
        private void SetTowerButtonState(bool interactable)
        {
            if (_towerButtons == null)
            {
                return;
            }
            for (int i = 0; i < _towerButtons.Length; i++)
            {
                if (_towerButtons[i] != null)
                {
                    _towerButtons[i].interactable = interactable;
                }
            }
        }

        private static void SetText(TMP_Text t, string value)
        {
            if (t != null && t.text != value)
            {
                t.text = value;
            }
        }

        /// <summary>供金币不足时置灰塔按钮（由 TowerPlacement 调用）</summary>
        public void SetTowerButtonInteractable(bool value)
        {
            if (_placing)
            {
                return;
            }
            SetTowerButtonState(value);
        }
    }
}
