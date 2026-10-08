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

        /// <summary>
        /// 刚算好、等待结算界面展示的这一局成绩。
        ///
        /// 【为什么要暂存一层】结算发生在 <see cref="FinishRound"/>，而弹窗是在
        ///   <see cref="OnGameOver"/> 里统一打开的（胜负两条路都从那里出来）。
        ///   中间隔着 Win() → GameOverEvent 的一次派发，若在那里重新推算，
        ///   "本局**之前**的历史星级"就已经被 RecordClear 覆盖了，再也拿不回来。
        /// </summary>
        private LevelClearInfo _pendingResult;

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
            // P2b：倍速请求（HudView 发，这里校验后再写 GameClock）
            EventDispatcher.AddEventListener<float>(EventName.GameSpeedChangeRequestEvent, OnGameSpeedChangeRequest);
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
            EventDispatcher.RemoveEventListener<float>(EventName.GameSpeedChangeRequestEvent, OnGameSpeedChangeRequest);
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

            SelectView sv = OpenSelect();
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
            // 进 Loading 就把倍速复位 ×1（P2b 硬性约束③）：新一局应当从最慢档开始
            ResetGameSpeed();

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

            // 关卡配置确认可用后才切战斗 BGM。
            // 【为什么放在校验之后】配置不完整会在上面提前 return，那时不该把音乐换成战斗曲。
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.PlayBgm(AudioName.BgmBattle);
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
            HudView hud = UIManager.Instance.Open<HudView>(HudView.LogicalName, UILayout.NormalPanel);
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

            // ⑩ M3-5：若本关存在局内快照，恢复到"上次退出的那一刻"。
            //    放在最后：棋盘/管理器/HUD 都已就绪，恢复出来的塔才有地方落。
            TryRestoreSnapshot(Level.Id);

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
            // 【为什么逐级登记】Normal / Power / Retard 各有 3 个分等级 prefab，升级时要换实例。
            // 这里一次全预载：塔就那么几座，省掉升级瞬间的加载卡顿比省内存更划算。
            // 新增塔型/等级时此处必须同步 —— 漏了会在升级时报"资源加载失败"。
            keys.Add("Tower_Normal0");
            keys.Add("Tower_Normal1");
            keys.Add("Tower_Normal2");
            keys.Add("Tower_Power0");
            keys.Add("Tower_Power1");
            keys.Add("Tower_Power2");
            keys.Add("Tower_Retard0");
            keys.Add("Tower_Retard1");
            keys.Add("Tower_Retard2");
            keys.Add("Bullet_Normal");
            keys.Add(HudView.LogicalName);
            keys.Add("TipsView");
            keys.Add("TowerInfoView");
            // 结算弹窗在本关结束的那一刻才需要，但那正是最不能卡顿的瞬间
            // （玩法已经停了，界面却要等 IO），所以提前预载。
            keys.Add("LevelClearView");

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
        /// 倍速请求（来自 HudView 的 ×1/×2/×3 按钮）。
        /// 【为什么要在这里二次校验，而不是信任 UI】
        ///   UI 只负责"循环切档"，它看不到游戏状态。若只有 UI 把关，
        ///   暂停遮罩或结算界面下只要点到按钮就会改速度（遮罩挡不住键盘/程序化调用）。
        ///   这里四道校验：档位合法 / 未暂停 / 局中状态 / 确有变化。
        /// </summary>
        private void OnGameSpeedChangeRequest(float requested)
        {
            if (!GameClock.IsValidTier(requested))
            {
                return;
            }
            // 暂停期间（timeScale=0）不改档：恢复时要按暂停前的原档位立即生效
            if (Time.timeScale <= 0f)
            {
                return;
            }
            // 只有"局中"允许改档：Loading / None / GameOver 一律忽略
            if (State != GameFlowState.Preparing &&
                State != GameFlowState.RoundRunning &&
                State != GameFlowState.RoundComplete)
            {
                return;
            }
            if (Mathf.Approximately(GameClock.Speed, requested))
            {
                return;
            }

            GameClock.Speed = requested;
            EventDispatcher.TriggerEvent<float>(EventName.GameSpeedChangedEvent, GameClock.Speed);
        }

        /// <summary>
        /// 把倍速复位为 ×1（GameOver / 重开 / 回选关 / 进 Loading 时调用）。
        /// 【为什么要派事件】HudView 的按钮文案靠 GameSpeedChangedEvent 同步；
        ///   只改 GameClock 而不派事件，下一局的按钮会停在上一局的档位文案上。
        /// </summary>
        private void ResetGameSpeed()
        {
            if (Mathf.Approximately(GameClock.Speed, 1f))
            {
                return;   // 本来就是 ×1，不必派多余事件
            }
            GameClock.Reset();
            EventDispatcher.TriggerEvent<float>(EventName.GameSpeedChangedEvent, GameClock.Speed);
        }

        /// <summary>
        /// 用 LateUpdate 而不是 Update：CombatSystem 在本帧的 Update 里已经刷新过
        /// AliveEnemyCount，这里读到的是最新值，回合结束判定不会慢一帧。
        /// </summary>
        private void LateUpdate()
        {
            // 自动回合倒计时（不受 State 限制，见 TickAutoNextRound 的说明）
            TickAutoNextRound(GameClock.DeltaTime);

            if (State != GameFlowState.RoundRunning)
            {
                return;
            }

            _wave.Tick(GameClock.DeltaTime);

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

            // M3-5：每回合结束存一次快照 —— 这是"退出后继续"的粒度。
            // 【为什么是回合边界】只有此刻状态是自洽的：场上无残留怪物、金币与塔都已结算。
            // 半途存盘就得额外记录每只怪的位置/血量/波次进度，复杂度与收益完全不成比例。
            SaveSnapshotNow();

            if (_roundCursor >= _roundIds.Count)
            {
                State = GameFlowState.GameOver;

                // 【为什么结算要写在 Win() 之前】Win() 会派发 GameOverEvent，
                // 界面可能立刻切走；如果存档晚一步写，"刚通关却没解锁下一关"。
                PlayerDataManager pd = PlayerDataManager.Instance;
                int stars = SaveManager.EvaluateStars(pd.Hp, pd.MaxHp);

                // ★ 必须**先读后写**：RecordClear 是"只升不降"的合并，
                //   先写再读就只能拿到合并后的最好成绩，界面便无法区分
                //   "本次打了 2 星"与"历史上最好 3 星"，"新纪录"也就无从判断。
                int previousBest = SaveManager.Instance.GetStars(Level.Id);
                SaveManager.Instance.RecordClear(Level.Id, stars, pd.Hp);

                // 成绩先攒着，由 OnGameOver 统一弹结算界面（胜负共用同一条路径）
                _pendingResult = BuildClearInfo(true, stars, previousBest);

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
            // 结算即离场：倍速复位 ×1，结算界面下按钮也不再可用（HudView 会置灰）
            ResetGameSpeed();
            Debug.Log(string.Format("[Flow] 本局结束：{0}\n{1}",
                victory ? "胜利" : "失败", PlayerDataManager.Instance.DumpDebugInfo()));
            Tips(victory ? "恭喜通关！" : "防御失败……");

            ShowClearPopup(victory);
        }

        // ------------------------------------------------------------------
        // 关卡结算弹窗
        //
        // 【为什么要有这一段】原实现只做了「写档 + 触发 LevelClearEvent + 弹一条 Tips」，
        //   而 **LevelClearEvent 全工程没有任何监听者** —— 事件空放，
        //   所以玩家打通关后看不到任何结算界面。这里把"打开界面"明确落在流程管理器上
        //   （与 PauseView / SettingView / SelectView 的开法一致：UI 只发事件，
        //    由流程层决定开什么、开在哪一层）。
        // ------------------------------------------------------------------

        private void ShowClearPopup(bool victory)
        {
            LevelClearInfo info;
            if (victory && _pendingResult != null)
            {
                info = _pendingResult;              // 正常通关：直接用 FinishRound 算好的成绩
            }
            else
            {
                // 走到这里只有两种情况：
                //   ① 失败 —— 本就没有星级，按当前状态现场拼一份；
                //   ② 调试键 F2 强制获胜 —— 没经过 FinishRound，_pendingResult 是空的。
                // 为了让 F2 也能真实检验"结算 + 记录星级 + 重进游戏读回"这条链路，
                // 这里对胜利补做一次与正式通关完全相同的结算，而不是只画个空壳界面。
                PlayerDataManager pd = PlayerDataManager.Instance;
                int stars = victory && pd != null
                    ? SaveManager.EvaluateStars(pd.Hp, pd.MaxHp)
                    : 0;
                int previousBest = Level != null ? SaveManager.Instance.GetStars(Level.Id) : 0;
                if (victory && Level != null)
                {
                    SaveManager.Instance.RecordClear(Level.Id, stars, pd.Hp);
                }
                info = BuildClearInfo(victory, stars, previousBest);
            }
            _pendingResult = null;

            LevelClearView view = UIManager.Instance.Open<LevelClearView>(
                LevelClearView.LogicalName, UILayout.NormalPanel);
            if (view == null)
            {
                Debug.LogWarning("[Flow] 结算弹窗未能打开（请确认 ui_hud 包里已生成 LevelClearView.prefab）");
                return;
            }
            view.Show(info);
        }

        /// <summary>把"这一局的结果"组装成结算界面需要的数据。</summary>
        private LevelClearInfo BuildClearInfo(bool victory, int stars, int previousBest)
        {
            PlayerDataManager pd = PlayerDataManager.Instance;
            LevelClearInfo info = new LevelClearInfo();
            info.victory = victory;
            info.levelId = Level != null ? Level.Id : 0;
            info.levelName = Level != null ? Level.Name : null;
            info.stars = Mathf.Clamp(stars, 0, 3);
            info.previousBest = Mathf.Clamp(previousBest, 0, 3);
            // 只有"打得比历史最好还好"才算刷新记录；平了不算
            info.newRecord = victory && info.stars > info.previousBest;
            info.hp = pd != null ? pd.Hp : 0;
            info.maxHp = pd != null ? pd.MaxHp : 0;
            info.killed = pd != null ? pd.TotalKilled : 0;
            info.leaked = pd != null ? pd.TotalLeaked : 0;
            FindNextLevel(info);
            return info;
        }

        /// <summary>
        /// 找下一关：**id 大于本关的最小一关**。
        /// 【为什么不是简单 +1】与 SaveManager.PreviousLevelId 同一口径 ——
        ///   按配置表实际存在的关卡取相邻项，这样以后中间插入关卡也不会把链路走错。
        /// </summary>
        private void FindNextLevel(LevelClearInfo info)
        {
            info.nextLevelId = 0;
            info.nextLevelName = null;
            info.hasNext = false;

            if (Level == null || Configs.LevelTable == null || Configs.LevelTable.DataList == null)
            {
                return;
            }
            int cur = Level.Id;
            List<cfg.SceneInfo> all = Configs.LevelTable.DataList;
            for (int i = 0; i < all.Count; i++)
            {
                cfg.SceneInfo s = all[i];
                if (s == null || s.Id <= cur)
                {
                    continue;
                }
                if (info.nextLevelId == 0 || s.Id < info.nextLevelId)
                {
                    info.nextLevelId = s.Id;
                    info.nextLevelName = s.Name;
                }
            }
            info.hasNext = info.nextLevelId > 0;
        }

        // ------------------------------------------------------------------
        // 局内快照（M3-5）
        // ------------------------------------------------------------------

        /// <summary>把当前局内状态写进快照并落盘。</summary>
        public void SaveSnapshotNow()
        {
            if (Level == null)
            {
                return;
            }
            LevelSnapshot snap = new LevelSnapshot();
            snap.valid = true;
            snap.levelId = Level.Id;
            snap.roundCursor = _roundCursor;
            snap.gold = PlayerDataManager.Instance.Gold;
            snap.hp = PlayerDataManager.Instance.Hp;
            snap.maxHp = PlayerDataManager.Instance.MaxHp;

            System.Collections.Generic.IList<BaseTower> towers = TowerManager.Instance.Towers;
            for (int i = 0; i < towers.Count; i++)
            {
                BaseTower t = towers[i];
                if (t == null || t.Cell == null || t.Config == null)
                {
                    continue;
                }
                TowerSnapshot ts = new TowerSnapshot();
                ts.row = t.Cell.Row;
                ts.col = t.Cell.Col;
                ts.type = t.Config.Type;
                ts.level = t.Config.Level;
                snap.towers.Add(ts);
            }

            SaveManager.Instance.SetSnapshot(snap);
        }

        /// <summary>
        /// 尝试用快照恢复本关进度。
        ///
        /// 【为什么 roundCursor &lt;= 0 就跳过】还没打完第一回合时，"继续"和"重开"没有区别，
        /// 而重开的状态更干净（不会有半截的塔）。这种时候宁可让玩家从头开始。
        /// </summary>
        private void TryRestoreSnapshot(int levelId)
        {
            if (!SaveManager.Instance.HasSnapshot)
            {
                return;
            }
            LevelSnapshot snap = SaveManager.Instance.Snapshot;
            if (snap == null || snap.levelId != levelId || snap.roundCursor <= 0)
            {
                return;
            }

            PlayerDataManager.Instance.RestoreState(levelId, snap.gold, snap.hp, snap.maxHp);

            int built = 0;
            for (int i = 0; i < snap.towers.Count; i++)
            {
                TowerSnapshot ts = snap.towers[i];
                if (TowerManager.Instance.RestoreTower(ts.type, ts.level, ts.row, ts.col) != null)
                {
                    built++;
                }
            }

            _roundCursor = Mathf.Clamp(snap.roundCursor, 0, Mathf.Max(0, _roundIds.Count - 1));

            // 【必须重算路径】恢复出来的塔会重新设置 A* 的墙标记，地图阻挡关系变了，
            // 不重算的话怪物会按"没塔时"的旧路径走，一路穿塔而过。
            if (AStarManager.Instance != null)
            {
                AStarManager.Instance.RequestRefresh();
            }
            if (pathArrowView != null && AStarManager.Instance != null)
            {
                pathArrowView.Render(AStarManager.Instance.CurrentPathWorld);
            }

            Debug.Log(string.Format("[Flow] 已恢复第 {0} 关的局内快照：回合进度 {1}/{2}，塔 {3} 座",
                levelId, _roundCursor, _roundIds.Count, built));
            Tips(string.Format("已从上次进度继续（下一回合：第 {0} 回合）", _roundCursor + 1));
        }

        // ------------------------------------------------------------------
        // 关卡切换 / 暂停 / 设置（M3）
        // ------------------------------------------------------------------

        /// <summary>
        /// 彻底清掉当前关卡的一切运行时状态。
        ///
        /// 【为什么必须有这一步】所有管理器都是**静态单例**，不随场景重建而重置；
        /// 而棋盘容器 BoardRoot / PathRoot / TowerRoot… 都是**场景常驻**节点，
        /// 谁往里面建了东西，谁就得负责拆。直接再 InitLevel 一次的话：
        /// 上一关的格子还挂在 BoardRoot 下、塔还挂在已被销毁的格子上、
        /// 怪物还留在空间哈希里、子弹还在飞 —— 会立刻出现一堆空引用与"幽灵塔"。
        ///
        /// 【顺序有讲究，本身就是正确性的一部分】
        ///   ① 先收回"玩家操作态"（放置预览 / 选中高亮 / 射程圈）：
        ///      它们要访问塔与格子（还原塔身颜色、复位格子高亮），
        ///      实体清完再收，就是在操作已经销毁的对象。
        ///   ② 再清战斗实体（它们互相引用：塔注册在 CombatSystem、怪在空间哈希）。
        ///   ③ 然后清棋盘与路径箭头 —— 这两样是"场景视觉残留"的主要来源。
        ///   ④ 最后关界面、恢复时间。
        /// </summary>
        public void TeardownLevel()
        {
            _autoNextTimer = 0f;
            Time.timeScale = 1f;

            // ① 玩家操作态
            if (TowerPlacement.Instance != null)
            {
                // ★ 光调 Deselect 不够：放置中的预览体走的是另一条分支，
                //   关卡结束时正在放塔的话，幽灵塔会跟着进下一关。
                TowerPlacement.Instance.CancelPlacement();
                TowerPlacement.Instance.Deselect();
            }
            // 面板的"已打开过"标记跟着实例一起作废，否则下次选中塔会走错分支
            _towerPanelOpened = false;

            // ② 战斗实体（互相引用，一起清）
            _wave.Stop();
            if (EnemyManager.Instance != null) EnemyManager.Instance.ClearAll();
            if (BulletManager.Instance != null) BulletManager.Instance.RecycleAll();
            if (TowerManager.Instance != null) TowerManager.Instance.ClearAll();
            if (CombatSystem.Instance != null) CombatSystem.Instance.ResetStats();

            // ③ 场景视觉残留：棋盘格子 + 路径箭头。
            //    ★ 这里是"通关后地图没被清掉"的根因所在 —— 原实现只清了实体，
            //      完全没碰 BoardView 建出来的那一堆格子。
            if (boardView != null) boardView.Clear();
            if (pathArrowView != null) pathArrowView.Clear();
            // 飘字 / 激光束都是"一次性表现"，寿命很短、自己也会消失，但它们同样是
            // "上一关的画面"。一起收掉，让 TeardownLevel 成为一个完整的闭环 ——
            // 以后新增这类短命特效时，也照这个模式在这里登记一笔。
            FloatingTextManager.ClearAll();
            LaserBeamView.ClearAll();

            // ④ 界面
            UIManager.Instance.Close(TowerInfoView.LogicalName);
            UIManager.Instance.Close(PauseView.LogicalName);
            UIManager.Instance.Close(SettingView.LogicalName);
            // 结算弹窗也归这里关：点「下一关 / 重玩 / 返回选关」都会走到 StartLevel/QuitToSelect，
            // 两者第一步都是 TeardownLevel —— 不在这里关，弹窗会跟着进到新关卡里盖住画面。
            UIManager.Instance.Close(LevelClearView.LogicalName);
            // ★ HUD 也必须关。它是**被复用**的界面（UIManager.Open 对已存在的实例直接返回），
            //   不销毁就等于把上一局的按钮状态（"已通关"且不可点）原样带进新关卡 ——
            //   玩家进新关后会发现「开始」按钮点不动，第一回合永远开不了。
            UIManager.Instance.Close(HudView.LogicalName);
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
            // 回选关 = 离场：倍速复位 ×1（重开/下一关走 StartLevel→InitLevel，那里也会复位）
            ResetGameSpeed();
            OpenSelect();
        }

        /// <summary>
        /// 打开关卡选择界面，并切到选关 BGM。
        /// 【为什么返回 SelectView】调用方（OnConfigLoaded）要判断"是否打开成功"来决定降级路径；
        /// 顺带把"切选关 BGM"收进这一处，避免多个入口各写一遍。
        /// </summary>
        public SelectView OpenSelect()
        {
            SelectView sv = UIManager.Instance.Open<SelectView>(SelectView.LogicalName, UILayout.NormalPanel);
            if (sv != null && AudioManager.Instance != null)
            {
                AudioManager.Instance.PlayBgm(AudioName.BgmSelect);
            }
            return sv;
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
            // P2b：每帧刷新 GameClock 的本帧缓存值（Time.deltaTime × Speed）。
            // 【放首行的原因】它必须在任何消费点之前跑过一次，本帧全工程才会取到同一个 dt。
            //   GameClock.DeltaTime 本身是惰性按帧缓存的（谁先取谁算），这里只是显式提前算好，
            //   因此即便本 Update 的执行顺序排在 CombatSystem 之后也不影响正确性。
            GameClock.Tick();

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

            // 调试快捷键：F1 打印完整状态，F2 强制获胜，F3 性能报告（联调/压测用）
            if (Input.GetKeyDown(KeyCode.F1))
            {
                Debug.Log(DumpDebugInfo());
            }
            else if (Input.GetKeyDown(KeyCode.F2))
            {
                PlayerDataManager.Instance.Win();
            }
            else if (Input.GetKeyDown(KeyCode.F3))
            {
                // M5-3：真机压测就靠它把"手感"变成可贴出来的数字
                Debug.Log(PerfProbe.Ensure().Report());
            }
        }
    }
}
