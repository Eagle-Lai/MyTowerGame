using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 战斗 HUD（P0-9）。
    ///
    /// 【设计原则】HUD 只做两件事：①把数据变化显示出来 ②把玩家操作转成事件。
    /// 它不持有任何游戏逻辑引用（不碰 TowerManager / WaveManager），
    /// 这样 UI 挂了也不会影响战斗正确性。
    ///
    /// 节点名必须与 Editor/SceneMainBuilder.cs 生成的 prefab 严格一致，
    /// 否则会在 Console 里看到「HUD 缺少子节点」的错误（查找是显式报错的，不静默失败）。
    /// </summary>
    public class HudView : MonoBehaviour
    {
        // ---- 文本 ----
        private Text _goldText;
        private Text _hpText;
        private Text _roundText;

        // ---- 按钮 ----
        private Button _startButton;
        private Text _startLabel;
        private Button _towerButton;
        private Text _towerLabel;

        /// <summary>当前选中的塔类型与等级（M0 固定 1/1，M2 接塔选择栏）</summary>
        private int _towerType = 1;
        private int _towerLevel = 1;

        /// <summary>进入放置模式后按钮变灰，避免重复点</summary>
        private bool _placing;

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
            _towerButton = FindButton("TowerButton");
            _towerLabel = FindChildText("TowerButton/Label");

            if (_startButton != null)
            {
                _startButton.onClick.AddListener(OnClickStart);
            }
            if (_towerButton != null)
            {
                _towerButton.onClick.AddListener(OnClickTower);
            }
            if (_startLabel != null)
            {
                _startLabel.text = "开始";
            }
            if (_towerLabel != null)
            {
                _towerLabel.text = "建塔";
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

        private Text FindText(string path)
        {
            Text t = FindChildText(path);
            if (t == null)
            {
                Debug.LogError(string.Format("[HUD] 缺少文本节点「{0}」（prefab 与 HudView.cs 不一致）", path));
            }
            return t;
        }

        private Text FindChildText(string path)
        {
            Transform tr = transform.Find(path);
            return tr != null ? tr.GetComponent<Text>() : null;
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

        private void OnClickTower()
        {
            // 不在这里判断"是否已在放置态"——那是 TowerPlacement 的职责。
            // 统一发同一个请求事件，由它决定是进入还是退出（单一状态源，避免两边状态不一致）。
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
        }

        private void OnGoldChanged(int current, int delta)
        {
            SetText(_goldText, current.ToString());
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
            SetTowerButtonState(false, "放置中");
        }

        private void OnExitPlacement()
        {
            _placing = false;
            SetTowerButtonState(true, "建塔");
        }

        private void OnBuildSuccess(BaseTower tower)
        {
            // 建完后自动退出放置模式（想连建就再点一次按钮）
            OnExitPlacement();
        }

        private void SetTowerButtonState(bool interactable, string label)
        {
            if (_towerButton != null)
            {
                _towerButton.interactable = interactable;
            }
            if (_towerLabel != null)
            {
                _towerLabel.text = label;
            }
        }

        private static void SetText(Text t, string value)
        {
            if (t != null && t.text != value)
            {
                t.text = value;
            }
        }

        /// <summary>供金币不足时置灰塔按钮（由 TowerPlacement 调用）</summary>
        public void SetTowerButtonInteractable(bool value)
        {
            if (_towerButton != null && !_placing)
            {
                _towerButton.interactable = value;
            }
        }
    }
}
