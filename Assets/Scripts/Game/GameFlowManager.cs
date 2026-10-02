using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>关卡流程状态</summary>
    public enum GameFlowState
    {
        None = 0,
        /// <summary>配置/资源加载中</summary>
        Loading,
        /// <summary>关卡已就绪，等待玩家点「开始」</summary>
        Preparing,
        /// <summary>回合进行中</summary>
        RoundRunning,
        /// <summary>回合完成，等待进入下一回合</summary>
        RoundComplete,
        /// <summary>胜负已定</summary>
        GameOver,
    }

    /// <summary>
    /// 关卡流程总控（P0-8）。
    ///
    /// 职责边界：
    ///   - 启动顺序编排（资源 → 配置 → 建关）
    ///   - 建关：棋盘 / 寻路网格 / 相机取景 / 管理器父节点 / UI / 预加载
    ///   - 回合推进：把 WaveManager 的一回合接到关卡的多回合链上，并判胜负
    ///   - **不碰具体战斗逻辑**（塔怎么打、怪怎么走都在各自模块里）
    ///
    /// 挂在 main.unity 的 GameFlow 对象上，由 SceneMainBuilder 自动创建并连线。
    /// </summary>
    public class GameFlowManager : MonoBehaviour
    {
        public static GameFlowManager Instance { get; private set; }

        [Header("场景引用（由 SceneMainBuilder 自动填充）")]
        public BoardView boardView;
        public PathArrowView pathArrowView;
        public Transform boardRoot;
        public Transform pathRoot;
        public Transform towerRoot;
        public Transform enemyRoot;
        public Transform bulletRoot;

        [Header("运行参数")]
        [Tooltip("为 0 表示使用配置表里的第一个关卡")]
        public int startLevelId = 0;

        public GameFlowState State { get; private set; }
        public LevelConfig Level { get; private set; }
        public LevelMapConfig Map { get; private set; }

        private readonly WaveManager _wave = new WaveManager();
        private List<int> _roundIds = new List<int>(8);
        private int _roundCursor;

        /// <summary>自动开下一回合的剩余秒数；&lt;=0 表示不在倒计时</summary>
        private float _autoNextTimer;
        /// <summary>倒计时提示的节流（每秒提示一次，避免每帧刷 Tips）</summary>
        private float _autoNextTipAcc;
        /// <summary>HUD 引用（倒计时需要更新按钮文字）</summary>
        private HudView _hud;

        /// <summary>塔升级/出售面板是否已打开（惰性打开，见 OnTowerSelected）</summary>
        private bool _towerPanelOpened;

        /// <summary>当前回合序号（从 1 计，0 = 尚未开始）</summary>
        public int CurrentRoundIndex { get { return _roundCursor + (State == GameFlowState.RoundRunning ? 1 : 0); } }

        // ==================================================================
        // 启动
        // ==================================================================

        private void Awake()
        {
            Instance = this;
        }

        private void OnEnable()
        {
            EventDispatcher.AddEventListener<bool>(EventName.ConfigLoadedEvent, OnConfigLoaded);
            EventDispatcher.AddEventListener(EventName.StartRoundRequestEvent, OnStartRequest);
            EventDispatcher.AddEventListener<bool>(EventName.GameOverEvent, OnGameOver);
            // M2：塔选中 → 打开升级/出售面板；升级/出售请求 → 执行
            EventDispatcher.AddEventListener<BaseTower>(EventName.TowerSelectedEvent, OnTowerSelected);
            EventDispatcher.AddEventListener<BaseTower>(EventName.TowerUpgradeRequestEvent, OnTowerUpgradeRequest);
            EventDispatcher.AddEventListener<BaseTower>(EventName.TowerSellRequestEvent, OnTowerSellRequest);
            // M3：关卡选择 / 暂停 / 设置
            EventDispatcher.AddEventListener<int>(EventName.SelectLevelRequestEvent, OnSelectLevelRequest);
            EventDispatcher.AddEventListener(EventName.CloseSelectRequestEvent, OnCloseSelectRequest);
            EventDispatcher.AddEventListener(EventName.PauseRequestEvent, OnPauseRequest);
            EventDispatcher.AddEventListener(EventName.ResumeRequestEvent, OnResumeRequest);
            EventDispatcher.AddEventListener(EventName.RestartLevelRequestEvent, OnRestartRequest);
            EventDispatcher.AddEventListener(EventName.QuitToSelectRequestEvent, OnQuitToSelectRequest);
            EventDispatcher.AddEventListener(EventName.OpenSettingsRequestEvent, OnOpenSettingsRequest);
            EventDispatcher.AddEventListener(EventName.CloseSettingsRequestEvent, OnCloseSettingsRequest);
        }

        private void OnDisable()
        {
            EventDispatcher.RemoveEventListener<bool>(EventName.ConfigLoadedEvent, OnConfigLoaded);
            EventDispatcher.RemoveEventListener(EventName.StartRoundRequestEvent, OnStartRequest);
            EventDispatcher.RemoveEventListener<bool>(EventName.GameOverEvent, OnGameOver);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.TowerSelectedEvent, OnTowerSelected);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.TowerUpgradeRequestEvent, OnTowerUpgradeRequest);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.TowerSellRequestEvent, OnTowerSellRequest);
            EventDispatcher.RemoveEventListener<int>(EventName.SelectLevelRequestEvent, OnSelectLevelRequest);
            EventDispatcher.RemoveEventListener(EventName.CloseSelectRequestEvent, OnCloseSelectRequest);
            EventDispatcher.RemoveEventListener(EventName.PauseRequestEvent, OnPauseRequest);
            EventDispatcher.RemoveEventListener(EventName.ResumeRequestEvent, OnResumeRequest);
            EventDispatcher.RemoveEventListener(EventName.RestartLevelRequestEvent, OnRestartRequest);
            EventDispatcher.RemoveEventListener(EventName.QuitToSelectRequestEvent, OnQuitToSelectRequest);
            EventDispatcher.RemoveEventListener(EventName.OpenSettingsRequestEvent, OnOpenSettingsRequest);
            EventDispatcher.RemoveEventListener(EventName.CloseSettingsRequestEvent, OnCloseSettingsRequest);
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                Instance = null;
            }
        }

        private void OnConfigLoaded(bool ok)
        {
            if (!ok)
            {
                Debug.LogError("[Flow] 配置表加载失败，已中止建关。请查看上方 [Config] 错误日志。");
                Tips("配置表加载失败，请查看 Console");
                State = GameFlowState.None;
                return;
            }

            // M3：开机先进关卡选择。
            // 【为什么保留 startLevelId 直进】调试时要跳过选关，在 Inspector 里填 startLevelId 即可，
            // 不用改代码、也不用把选关界面拆掉。
            if (startLevelId > 0)
            {
                InitLevel(startLevelId);
                return;
            }

            SelectView sv = UIManager.Instance.Open<SelectView>(SelectView.LogicalName, UILayout.NormalPanel);
            if (sv == null)
            {
                // 【降级】SelectView.prefab 还没生成时不能把玩家卡在黑屏 ——
                // 直接进第一关，玩法照常，只是没有选关界面。
                Debug.LogWarning("[Flow] SelectView 打开失败（prefab 可能还没生成），降级为直接进入第一关");
                InitLevel(Configs.GetFirstLevelId());
            }
        }

        // ==================================================================
        // 建关
        // ==================================================================

        public void InitLevel(int levelId)
        {
            State = GameFlowState.Loading;

            Level = Configs.GetLevel(levelId);
            Map = Configs.GetLevelMapOfLevel(levelId);
            if (Level == null || Map == null)
            {
                Debug.LogError(string.Format("[Flow] 关卡 {0} 配置不完整，无法建关", levelId));
                Tips("关卡配置不完整");
                State = GameFlowState.None;
                return;
            }

            string err = Map.Validate();
            if (!string.IsNullOrEmpty(err))
            {
                // 只是告警：cells 行长度不足时 GetCell 会按空地兜底，不至于崩
                Debug.LogError(string.Format("[Flow] 棋盘配置 id={0} 校验未通过：{1}", Map.Id, err));
            }

            float cellSize = Configs.Global.CellSize;

            // 棋盘左上角原点：让棋盘几何中心正好落在世界原点
            Vector2 origin = new Vector2(-Map.Cols * cellSize * 0.5f, Map.Rows * cellSize * 0.5f);
            Vector2 center = BoardGeometry.BoardCenter(Map.Rows, Map.Cols, cellSize, origin);

            SetupCamera(Map, cellSize, center);

            // ① 视图层：生成格子
            if (boardView == null)
            {
                Debug.LogError("[Flow] boardView 未连线，请执行「Tools ▸ 塔防 ▸ 搭建 main 场景」重新生成场景");
                State = GameFlowState.None;
                return;
            }
            boardView.Build(Map, cellSize, origin, boardRoot);

            // ② 数据层：只建寻路网格（不生成任何物件）
            AStarManager.Instance.BuildGrid(Map, cellSize, origin);
            EventDispatcher.TriggerEvent(EventName.MapInitFinish);

            // ③ 管理器父节点（对象池创建的实例据此归位，保持 Hierarchy 整洁）
            EnemyManager.Instance.SetParent(enemyRoot);
            BulletManager.Instance.SetParent(bulletRoot);
            TowerManager.Instance.SetParent(towerRoot);
            if (TowerPlacement.Instance != null)
            {
                TowerPlacement.Instance.SetGhostParent(towerRoot);
            }

            // ④ 路径可视化
            if (pathArrowView != null)
            {
                pathArrowView.Init(pathRoot);
                pathArrowView.Render(AStarManager.Instance.CurrentPathWorld);
            }

            // ⑥ 打开 UI
            HudView hud = UIManager.Instance.Open<HudView>("HudView", UILayout.NormalPanel);
            if (hud == null)
            {
                Debug.LogWarning("[Flow] HUD 未能打开，玩法仍可运行（无法用鼠标操作，请检查 ui_hud 包）");
            }
            _hud = hud;   // 自动回合倒计时需要更新按钮文字
            UIManager.Instance.Open<TipsView>("TipsView", UILayout.TipsPanel);

            // ⑦ 玩家数据（金币/生命来自关卡配置，不再是硬编码）
            PlayerDataManager.Instance.InitFromLevel(Level);

            // HUD 是在上面才实例化的，错过了 PlayerStateInitEvent，这里补一次刷新
            if (hud != null)
            {
                hud.RefreshAll();
            }

            // ⑧ 预加载本关会用到的资源（打 AB 时提前取好包引用）
            PreloadLevelResources();

            // ⑨ 回合队列
            _roundIds = Level.RoundIds != null ? new List<int>(Level.RoundIds) : new List<int>();
            _roundCursor = 0;

            State = GameFlowState.Preparing;
            Debug.Log(string.Format(
                "[Flow] 关卡 {0}「{1}」就绪：棋盘 {2}×{3}，格子 {4} 世界单位，回合 {5} 个\n{6}",
                Level.Id, Level.Name, Map.Cols, Map.Rows, cellSize, _roundIds.Count,
                AStarManager.Instance.DescribeCurrentPath()));
            Tips(string.Format("关卡就绪：{0}，点击「开始」迎战", Level.Name));

            // 可选：关卡就绪后自动开始第一回合
            // （常数表 Global.autoStartRoundDelayMs；默认 0，留给玩家先看地图 + 布防）
            float firstDelay = Configs.Global != null ? Configs.Global.AutoStartRoundDelaySec : 0f;
            if (firstDelay > 0f)
            {
                _autoNextTimer = firstDelay;
                _autoNextTipAcc = 0f;
                Debug.Log(string.Format("[Flow] {0:F0} 秒后自动开始第一回合", firstDelay));
            }
        }

        private void SetupCamera(LevelMapConfig map, float cellSize, Vector2 center)
        {
            Camera cam = Camera.main;
            if (cam == null)
            {
                Debug.LogError("[Flow] 场景中没有 Tag=MainCamera 的相机，棋盘无法取景");
                return;
            }
            CameraController ctrl = cam.GetComponent<CameraController>();
            if (ctrl == null)
            {
                ctrl = cam.gameObject.AddComponent<CameraController>();
            }
            ctrl.FitBoard(map.Rows, map.Cols, cellSize, center);
        }

        private void PreloadLevelResources()
        {
            List<string> keys = new List<string>(32);
            keys.Add("Tower_Normal");
            keys.Add("Tower_Power");
            keys.Add("Tower_Retard");
            keys.Add("Bullet_Normal");
            keys.Add("HudView");
            keys.Add("TipsView");
            keys.Add("TowerInfoView");

            if (Level.RoundIds != null)
            {
                for (int i = 0; i < Level.RoundIds.Count; i++)
                {
                    RoundConfig rc = Configs.GetRound(Level.RoundIds[i]);
                    if (rc == null || rc.WaveIds == null)
                    {
                        continue;
                    }
                    for (int w = 0; w < rc.WaveIds.Count; w++)
                    {
                        WaveGroupConfig wg = Configs.GetWaveGroup(rc.WaveIds[w]);
                        if (wg == null || wg.EnemyIds == null)
                        {
                            continue;
                        }
                        for (int e = 0; e < wg.EnemyIds.Count; e++)
                        {
                            EnemyConfig ec = Configs.GetEnemy(wg.EnemyIds[e]);
                            if (ec != null && !string.IsNullOrEmpty(ec.ResName) && !keys.Contains(ec.ResName))
                            {
                                keys.Add(ec.ResName);
                            }
                        }
                    }
                }
            }

            ResLoader.Instance.Preload(keys.ToArray(), null);
        }

        // ==================================================================
        // 回合推进
        // ==================================================================

        private void OnStartRequest()
        {
            // 玩家手动推进 → 取消自动倒计时（避免"点了按钮又自动开一回合"）
            _autoNextTimer = 0f;

            if (State == GameFlowState.RoundRunning)
            {
                Tips("回合进行中，请等待本回合结束");
                return;
            }
            if (State == GameFlowState.GameOver)
            {
                Tips("本局已结束");
                return;
            }
            if (State != GameFlowState.Preparing)
            {
                return;
            }
            if (_roundCursor >= _roundIds.Count)
            {
                PlayerDataManager.Instance.Win();
                return;
            }

            RoundConfig round = Configs.GetRound(_roundIds[_roundCursor]);
            if (round == null)
            {
                Tips(string.Format("回合 {0} 配置缺失", _roundIds[_roundCursor]));
                Debug.LogError(string.Format("[Flow] 找不到回合配置 id={0}", _roundIds[_roundCursor]));
                return;
            }

            _wave.BeginRound(round);
            State = GameFlowState.RoundRunning;
            EventDispatcher.TriggerEvent<int>(EventName.RoundStartEvent, _roundCursor + 1);
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.Play(AudioName.RoundStart);
            }
            Tips(string.Format("回合 {0}/{1} 开始", _roundCursor + 1, _roundIds.Count));
        }

        /// <summary>
        /// 用 LateUpdate 而不是 Update：CombatSystem 在本帧的 Update 里已经刷新过
        /// AliveEnemyCount，这里读到的是最新值，回合结束判定不会慢一帧。
        /// </summary>
        private void LateUpdate()
        {
            // 自动回合倒计时（不受 State 限制，见 TickAutoNextRound 的说明）
            TickAutoNextRound(Time.deltaTime);

            if (State != GameFlowState.RoundRunning)
            {
                return;
            }

            _wave.Tick(Time.deltaTime);

            int alive = CombatSystem.Instance != null ? CombatSystem.Instance.AliveEnemyCount : 0;
            _wave.CheckGroupCleared(alive);

            if (_wave.IsRoundFinished(alive))
            {
                FinishRound();
            }
        }

        private void FinishRound()
        {
            _wave.Stop();
            int finishedIndex = _roundCursor + 1;

            // 回合奖励
            if (_roundCursor < _roundIds.Count)
            {
                RoundConfig rc = Configs.GetRound(_roundIds[_roundCursor]);
                if (rc != null && rc.RewardGold > 0)
                {
                    PlayerDataManager.Instance.AddGold(rc.RewardGold);
                    Tips(string.Format("回合奖励 +{0} 金币", rc.RewardGold));
                }
            }

            EventDispatcher.TriggerEvent<int>(EventName.RoundClearEvent, finishedIndex);
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.Play(AudioName.RoundClear);
            }

            _roundCursor++;
            if (_roundCursor >= _roundIds.Count)
            {
                State = GameFlowState.GameOver;

                // 【为什么结算要写在 Win() 之前】Win() 会派发 GameOverEvent，
                // 界面可能立刻切走；如果存档晚一步写，"刚通关却没解锁下一关"。
                PlayerDataManager pd = PlayerDataManager.Instance;
                int stars = SaveManager.EvaluateStars(pd.Hp, pd.MaxHp);
                SaveManager.Instance.RecordClear(Level.Id, stars, pd.Hp);
                EventDispatcher.TriggerEvent<int, int, int>(EventName.LevelClearEvent, Level.Id, stars, pd.Hp);
                Tips(string.Format("通关！获得 {0}", SelectView.Stars(stars)));

                PlayerDataManager.Instance.Win();
            }
            else
            {
                // 回到可开始状态：HUD 收到 RoundClearEvent 会把按钮恢复成「下一回合」
                State = GameFlowState.Preparing;

                // 自动开下一回合：间隔读常数表（Global.autoNextRoundDelayMs）
                // 留出间隔是为了让玩家在两波之间布防/卖塔；设 0 则完全交给玩家手动点
                float delay = Configs.Global != null ? Configs.Global.AutoNextRoundDelaySec : 0f;
                if (delay > 0f)
                {
                    _autoNextTimer = delay;
                    _autoNextTipAcc = 0f;   // 立刻提示一次
                    Debug.Log(string.Format("[Flow] 回合 {0} 完成，{1:F1} 秒后自动开始回合 {2}",
                        finishedIndex, delay, _roundCursor + 1));
                }
                else
                {
                    Debug.Log(string.Format("[Flow] 回合 {0} 完成，等待开始回合 {1}（自动回合已关闭）",
                        finishedIndex, _roundCursor + 1));
                }
            }
        }

        /// <summary>
        /// 自动开下一回合的倒计时。
        /// 【为什么放在 LateUpdate 的最前面、且不受 State 限制】
        /// 上一回合结束时 State 已经回到 Preparing，如果跟着 `State == RoundRunning`
        /// 的早退一起被打断，倒计时就永远不会推进。
        /// </summary>
        private void TickAutoNextRound(float dt)
        {
            if (_autoNextTimer <= 0f)
            {
                return;
            }
            _autoNextTimer -= dt;

            if (_autoNextTimer <= 0f)
            {
                _autoNextTimer = 0f;
                Debug.Log("[Flow] 自动开始下一回合");
                if (_hud != null)
                {
                    _hud.SetStartButtonLabel("下一回合");
                }
                OnStartRequest();
                return;
            }

            // 每秒提示一次倒计时
            _autoNextTipAcc -= dt;
            if (_autoNextTipAcc <= 0f)
            {
                _autoNextTipAcc = 1f;
                int sec = Mathf.CeilToInt(_autoNextTimer);
                if (_hud != null)
                {
                    _hud.SetStartButtonLabel(string.Format("下一回合({0})", sec));
                }
                Tips(string.Format("回合完成，{0} 秒后自动开始下一回合（也可直接点「下一回合」）", sec));
            }
        }

        private void OnGameOver(bool victory)
        {
            _wave.Stop();
            State = GameFlowState.GameOver;
            Debug.Log(string.Format("[Flow] 本局结束：{0}\n{1}",
                victory ? "胜利" : "失败", PlayerDataManager.Instance.DumpDebugInfo()));
            Tips(victory ? "恭喜通关！" : "防御失败……");
        }

        // ------------------------------------------------------------------
        // 关卡切换 / 暂停 / 设置（M3）
        // ------------------------------------------------------------------

        /// <summary>
        /// 彻底清掉当前关卡的一切运行时状态。
        ///
        /// 【为什么必须有这一步】所有管理器都是**静态单例**，不随场景重建而重置。
        /// 直接再 InitLevel 一次的话：上一关的塔还挂在已被销毁的格子上、
        /// 怪物还留在空间哈希里、子弹还在飞 —— 会立刻出现一堆空引用与"幽灵塔"。
        /// 顺序也有讲究：先清战斗实体（它们互相引用），再关界面，最后恢复时间。
        /// </summary>
        public void TeardownLevel()
        {
            _autoNextTimer = 0f;
            Time.timeScale = 1f;

            if (EnemyManager.Instance != null) EnemyManager.Instance.ClearAll();
            if (BulletManager.Instance != null) BulletManager.Instance.RecycleAll();
            if (TowerManager.Instance != null) TowerManager.Instance.ClearAll();

            if (TowerPlacement.Instance != null) TowerPlacement.Instance.Deselect();
            if (CombatSystem.Instance != null) CombatSystem.Instance.ResetStats();

            UIManager.Instance.Close(TowerInfoView.LogicalName);
            UIManager.Instance.Close(PauseView.LogicalName);
            UIManager.Instance.Close(SettingView.LogicalName);
            _hud = null;
        }

        /// <summary>切到指定关卡（或重开同一关）。</summary>
        public void StartLevel(int levelId)
        {
            if (levelId <= 0)
            {
                return;
            }
            TeardownLevel();
            UIManager.Instance.Close(SelectView.LogicalName);
            // 开新局 → 旧快照作废，否则下次进关会莫名其妙"接着上一局"
            SaveManager.Instance.ClearSnapshot(true);
            InitLevel(levelId);
        }

        public void RestartLevel()
        {
            if (Level == null)
            {
                return;
            }
            StartLevel(Level.Id);
        }

        /// <summary>退出当前对局，回到关卡选择。</summary>
        public void QuitToSelect()
        {
            TeardownLevel();
            State = GameFlowState.None;
            OpenSelect();
        }

        public void OpenSelect()
        {
            UIManager.Instance.Open<SelectView>(SelectView.LogicalName, UILayout.NormalPanel);
        }

        private void OnSelectLevelRequest(int levelId)
        {
            StartLevel(levelId);
        }

        private void OnCloseSelectRequest()
        {
            UIManager.Instance.Close(SelectView.LogicalName);
            // 已经在关卡里就什么都不做（返回按钮主要用于"没有对局时"）
        }

        private void OnPauseRequest()
        {
            if (State == GameFlowState.GameOver)
            {
                return;   // 已结算就别再暂停了
            }
            UIManager.Instance.Open<PauseView>(PauseView.LogicalName, UILayout.NormalPanel);
        }

        private void OnResumeRequest()
        {
            UIManager.Instance.Close(PauseView.LogicalName);
            UIManager.Instance.Close(SettingView.LogicalName);
            Time.timeScale = 1f;
        }

        private void OnRestartRequest()
        {
            RestartLevel();
        }

        private void OnQuitToSelectRequest()
        {
            QuitToSelect();
        }

        private void OnOpenSettingsRequest()
        {
            UIManager.Instance.Open<SettingView>(SettingView.LogicalName, UILayout.NormalPanel);
        }

        private void OnCloseSettingsRequest()
        {
            UIManager.Instance.Close(SettingView.LogicalName);
        }

        /// <summary>
        /// 暂停热键。
        /// 【为什么用 P 而不是 ESC】ESC 已经被 TowerPlacement 用作"取消放置 / 取消选中"，
        /// 两个系统同帧抢同一个键必然出现"按一下既取消选中又暂停"。P 无歧义。
        /// 【为什么用 unscaledDeltaTime】暂停时 timeScale=0，用 deltaTime 的话热键轮询会停摆，
        /// 一旦暂停就再也按不回来了。
        /// </summary>
        // ------------------------------------------------------------------
        // 塔选中 / 升级 / 出售（M2）
        // ------------------------------------------------------------------

        /// <summary>
        /// 选中塔 → 惰性打开升级/出售面板。
        ///
        /// 【为什么打开后要显式 Show(tower)】面板是**在 TowerSelectedEvent 的分发过程中**实例化的，
        /// 它的 OnEnable（订阅事件）发生在本次分发之后 —— 于是它收不到"这一次"选中事件。
        /// 所以这里打开后必须手动喂一次，否则面板打开是空白。
        /// </summary>
        private void OnTowerSelected(BaseTower tower)
        {
            if (tower == null)
            {
                return;
            }

            TowerInfoView view;
            if (!_towerPanelOpened)
            {
                view = UIManager.Instance.Open<TowerInfoView>(
                    TowerInfoView.LogicalName, UILayout.NormalPanel);
                if (view == null)
                {
                    // 面板资源未就绪时降级：提示玩家升级/出售暂不可用（逻辑本身没坏）
                    Tips("塔操作面板资源未就绪，暂无法升级/出售（补齐 TowerInfoView 后可用）");
                    return;
                }
                _towerPanelOpened = true;
            }
            else
            {
                UIManager.Instance.Open(TowerInfoView.LogicalName, UILayout.NormalPanel);
                view = UIManager.Instance.Get<TowerInfoView>(TowerInfoView.LogicalName);
            }

            if (view != null)
            {
                view.Show(tower);
            }
        }

        private void OnTowerUpgradeRequest(BaseTower tower)
        {
            TowerManager.Instance.TryUpgrade(tower);
        }

        private void OnTowerSellRequest(BaseTower tower)
        {
            // 二次确认由面板负责（美术补齐后加）；这里直接执行出售
            TowerManager.Instance.Sell(tower);
        }

        private static void Tips(string msg)
        {
            EventDispatcher.TriggerEvent<string>(EventName.ShowTipEvent, msg);
        }

        // ==================================================================
        // 诊断
        // ==================================================================

        public string DumpDebugInfo()
        {
            return string.Format(
                "[Flow] 状态={0} 关卡={1} 回合={2}/{3}\n  {4}\n  {5}\n  {6}",
                State, Level != null ? Level.Id : 0, _roundCursor, _roundIds.Count,
                PlayerDataManager.Instance.DumpDebugInfo(),
                _wave.DumpDebugInfo(),
                CombatSystem.Instance != null ? CombatSystem.Instance.DumpDebugInfo() : "(战斗系统未初始化)");
        }

        private void Update()
        {
            // ---- M3：暂停热键 ----
            // 【为什么是 P 而不是 ESC】ESC 已被 TowerPlacement 用作"取消放置 / 取消选中"，
            // 两个系统同帧抢同一个键，必然出现"按一下既取消选中又暂停"。
            //
            // 【为什么这里不用 deltaTime】暂停时 Time.timeScale = 0，
            // 任何依赖 scaled time 的轮询都会停摆 —— 一旦暂停就再也按不回来。
            // GetKeyDown 不受 timeScale 影响，所以这个热键在暂停中依然有效。
            if (Input.GetKeyDown(KeyCode.P))
            {
                if (UIManager.Instance.IsOpen(PauseView.LogicalName))
                {
                    OnResumeRequest();
                }
                else
                {
                    OnPauseRequest();
                }
            }

            // 调试快捷键：F1 打印完整状态，F2 强制获胜（联调时省时间）
            if (Input.GetKeyDown(KeyCode.F1))
            {
                Debug.Log(DumpDebugInfo());
            }
            else if (Input.GetKeyDown(KeyCode.F2))
            {
                PlayerDataManager.Instance.Win();
            }
        }
    }
}
