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

        /// <summary>Read-only menu query; never discards a player's checkpoint.</summary>
        public static bool TryGetResumableCheckpoint(out int levelId, out int nextWave)
        {
            levelId = 0;
            nextWave = 0;
            SaveManager save = SaveManager.Instance;
            if (save == null || !save.HasSnapshot || !Configs.IsLoaded) return false;
            LevelSnapshot snapshot = save.Snapshot;
            if (snapshot == null || !save.IsUnlocked(snapshot.levelId)) return false;
            LevelConfig level = Configs.GetLevel(snapshot.levelId);
            if (level == null) return false;
            LevelRatingProfile profile = Configs.GetLevelRating(level.Id);
            string reason;
            int waves = level.RoundIds != null ? level.RoundIds.Count : 0;
            if (!LevelCheckpointValidator.IsCompatible(snapshot, profile, waves, out reason) ||
                save.IsRunCommitted(level.Id, snapshot.metrics != null ? snapshot.metrics.runId : null)) return false;
            levelId = level.Id;
            nextWave = Mathf.Min(snapshot.roundCursor + 1, waves);
            return true;
        }

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
        private LevelRatingProfile _ratingProfile;
        private LevelRunMetrics _run;
        private readonly HashSet<BaseEnemy> _unresolvedEnemies = new HashSet<BaseEnemy>();
        private bool _settled;
        private LevelRatingResult _pendingSaveResult;
        public LevelRunMetrics RunMetrics { get { return _run != null ? _run.Clone() : null; } }
        public LevelRatingProfile RatingProfile { get { return _ratingProfile != null ? _ratingProfile.Clone() : null; } }


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
            EventDispatcher.AddEventListener<BaseEnemy, int>(EventName.EnemyKilledEvent, OnRatedEnemyKilled);
            EventDispatcher.AddEventListener<BaseEnemy, int>(EventName.EnemyReachedEndEvent, OnRatedEnemyLeaked);
            EventDispatcher.AddEventListener(EventName.StartRoundRequestEvent, OnStartRequest);
            EventDispatcher.AddEventListener<bool>(EventName.GameOverEvent, OnGameOver);
            // M2：塔选中 → 打开升级/出售面板；升级/出售请求 → 执行
            EventDispatcher.AddEventListener<BaseTower>(EventName.TowerUpgradeRequestEvent, OnTowerUpgradeRequest);
            EventDispatcher.AddEventListener<BaseTower>(EventName.TowerSellRequestEvent, OnTowerSellRequest);
            // UI 补全 C1：出售必须经确认弹窗后才真正执行（只监听"确认"事件）
            EventDispatcher.AddEventListener<BaseTower>(EventName.TowerSellConfirmEvent, OnTowerSellConfirm);
            // M3：关卡选择 / 暂停 / 设置
            EventDispatcher.AddEventListener<int>(EventName.SelectLevelRequestEvent, OnSelectLevelRequest);
            EventDispatcher.AddEventListener(EventName.CloseSelectRequestEvent, OnCloseSelectRequest);
            EventDispatcher.AddEventListener(EventName.PauseRequestEvent, OnPauseRequest);
            EventDispatcher.AddEventListener(EventName.PauseToggleRequestEvent, OnPauseToggleRequest);
            EventDispatcher.AddEventListener(EventName.ResumeRequestEvent, OnResumeRequest);
            EventDispatcher.AddEventListener(EventName.RestartLevelRequestEvent, OnRestartRequest);
            EventDispatcher.AddEventListener(EventName.QuitToSelectRequestEvent, OnQuitToSelectRequest);
            // 2026-10-14：游戏介绍弹窗（HUD 右上角按钮）
            EventDispatcher.AddEventListener(EventName.OpenGameIntroRequestEvent, OnOpenGameIntroRequest);
            EventDispatcher.AddEventListener(EventName.OpenSettingsRequestEvent, OnOpenSettingsRequest);
            EventDispatcher.AddEventListener(EventName.CloseSettingsRequestEvent, OnCloseSettingsRequest);
            // P2b：倍速请求（HudView 发，这里校验后再写 GameClock）
            EventDispatcher.AddEventListener<float>(EventName.GameSpeedChangeRequestEvent, OnGameSpeedChangeRequest);
            // UI 补全 B1：主菜单入口（"开始游戏"+"图鉴"）
            EventDispatcher.AddEventListener(EventName.StartGameRequestEvent, OnStartGameRequest);
            EventDispatcher.AddEventListener<bool>(EventName.OpenCodexRequestEvent, OnOpenCodexRequest);
        }

        private void OnDisable()
        {
            EventDispatcher.RemoveEventListener<bool>(EventName.ConfigLoadedEvent, OnConfigLoaded);
            EventDispatcher.RemoveEventListener<BaseEnemy, int>(EventName.EnemyKilledEvent, OnRatedEnemyKilled);
            EventDispatcher.RemoveEventListener<BaseEnemy, int>(EventName.EnemyReachedEndEvent, OnRatedEnemyLeaked);
            EventDispatcher.RemoveEventListener(EventName.StartRoundRequestEvent, OnStartRequest);
            EventDispatcher.RemoveEventListener<bool>(EventName.GameOverEvent, OnGameOver);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.TowerUpgradeRequestEvent, OnTowerUpgradeRequest);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.TowerSellRequestEvent, OnTowerSellRequest);
            EventDispatcher.RemoveEventListener<int>(EventName.SelectLevelRequestEvent, OnSelectLevelRequest);
            EventDispatcher.RemoveEventListener(EventName.CloseSelectRequestEvent, OnCloseSelectRequest);
            EventDispatcher.RemoveEventListener(EventName.PauseRequestEvent, OnPauseRequest);
            EventDispatcher.RemoveEventListener(EventName.PauseToggleRequestEvent, OnPauseToggleRequest);
            EventDispatcher.RemoveEventListener(EventName.ResumeRequestEvent, OnResumeRequest);
            EventDispatcher.RemoveEventListener(EventName.RestartLevelRequestEvent, OnRestartRequest);
            EventDispatcher.RemoveEventListener(EventName.QuitToSelectRequestEvent, OnQuitToSelectRequest);
            EventDispatcher.RemoveEventListener(EventName.OpenGameIntroRequestEvent, OnOpenGameIntroRequest);
            EventDispatcher.RemoveEventListener(EventName.OpenSettingsRequestEvent, OnOpenSettingsRequest);
            EventDispatcher.RemoveEventListener(EventName.CloseSettingsRequestEvent, OnCloseSettingsRequest);
            EventDispatcher.RemoveEventListener<float>(EventName.GameSpeedChangeRequestEvent, OnGameSpeedChangeRequest);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.TowerSellConfirmEvent, OnTowerSellConfirm);
            EventDispatcher.RemoveEventListener(EventName.StartGameRequestEvent, OnStartGameRequest);
            EventDispatcher.RemoveEventListener<bool>(EventName.OpenCodexRequestEvent, OnOpenCodexRequest);
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                GameAudio.EndLevel();
                Instance = null;
            }
        }

        private void OnConfigLoaded(bool ok)
        {
            if (!ok)
            {
                Debug.LogError("[Flow] 配置表加载失败，已中止建关。请查看上方 [Config] 错误日志。");
                Tips(Localization.Get("Config load failed, see Console") ?? "配置表加载失败，请查看 Console");
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

            // UI 补全 B1：先给玩家一个入口页，而不是直接把他丢在选关页上。
            // 主菜单缺 prefab 时降级为原来的"直接进选关"，不让启动卡住。
            MainMenuView menu = UIManager.Instance.Open<MainMenuView>("MainMenuView", UILayout.NormalPanel);
            if (menu != null)
            {
                return;
            }

            Debug.LogWarning("[Flow] MainMenuView 打开失败（prefab 可能还没生成），降级为直接进选关");
            OpenSelectOrFirstLevel();
        }

        /// <summary>打开选关界面；缺 prefab 时降级直接进第一关（原逻辑，抽出来复用）。</summary>
        private void OpenSelectOrFirstLevel()
        {
            SelectView sv = OpenSelect();
            if (sv == null)
            {
                // 【降级】SelectView.prefab 还没生成时不能把玩家卡在黑屏 ——
                // 直接进第一关，玩法照常，只是没有选关界面。
                Debug.LogWarning("[Flow] SelectView 打开失败（prefab 可能还没生成），降级为直接进入第一关");
                InitLevel(Configs.GetFirstLevelId());
            }
        }

        /// <summary>主菜单点「开始游戏」：关掉主菜单，进选关。</summary>
        private void OnStartGameRequest()
        {
            UIManager.Instance.Close("MainMenuView");
            OpenSelectOrFirstLevel();
        }

        /// <summary>
        /// 主菜单点图鉴。参数 true = 塔图鉴，false = 怪物图鉴。
        /// 【为什么先关主菜单】两个图鉴都是**整页**界面，整页界面叠在主菜单上会让
        /// "返回"到底回到哪一层变得含糊；先关再开，"返回"永远回主菜单。
        /// </summary>
        private void OnOpenCodexRequest(bool isTower)
        {
            UIManager.Instance.Close("MainMenuView");
            if (!isTower)
            {
                if (UIManager.Instance.Open<MonsterCodexView>(MonsterCodexView.LogicalName, UILayout.NormalPanel) == null)
                    UIManager.Instance.Open<MainMenuView>("MainMenuView", UILayout.NormalPanel);
                return;
            }
            TowerCodexView view = UIManager.Instance.Open<TowerCodexView>("TowerCodexView", UILayout.NormalPanel);
            if (view == null)
            {
                Debug.LogWarning("[Flow] TowerCodexView 打开失败（prefab 可能还没生成），回主菜单");
                UIManager.Instance.Open<MainMenuView>("MainMenuView", UILayout.NormalPanel);
            }
        }

        // ==================================================================
        // 建关
        // ==================================================================

        public void InitLevel(int levelId)
        {
            GameAudio.BeginLevel();
            State = GameFlowState.Loading;
            // 进 Loading 就把倍速复位 ×1（P2b 硬性约束③）：新一局应当从最慢档开始
            ResetGameSpeed();

            Level = Configs.GetLevel(levelId);
            Map = Configs.GetLevelMapOfLevel(levelId);
            if (Level == null || Map == null)
            {
                Debug.LogError(string.Format("[Flow] 关卡 {0} 配置不完整，无法建关", levelId));
                Tips(Localization.Get("Level config incomplete") ?? "关卡配置不完整");
                State = GameFlowState.None;
                GameAudio.EndLevel();
                return;
            }

            string err = Map.Validate();
            if (!string.IsNullOrEmpty(err))
            {
                // 只是告警：cells 行长度不足时 GetCell 会按空地兜底，不至于崩
                Debug.LogError(string.Format("[Flow] 棋盘配置 id={0} 校验未通过：{1}", Map.Id, err));
            }

            // 关卡计时起点（UI 补全 B4「最佳用时」）。
            // 【为什么放在这里而不是方法最开头】上面的关卡/棋盘校验失败会提前 return，
            // 那次不算"进了一关"；放在校验之后，计时只在真正开始建关时启动。
            GameClock.ResetLevelTimer();
            _ratingProfile = Configs.GetLevelRating(levelId);
            _ratingProfile = _ratingProfile != null ? _ratingProfile.Clone() : null;
            string ratingError;
            if (!Configs.RatingContentVerified || !Configs.ValidateRatingPlan(_ratingProfile, out ratingError))
            {
                Debug.LogError("[Rating] Level cannot start: rating config missing, invalid, or content hash mismatch");
                State = GameFlowState.None;
                GameAudio.EndLevel();
                return;
            }
            _run = new LevelRunMetrics { runId = System.Guid.NewGuid().ToString("N"), statisticsValid = true, timingValid = true };
            if (_ratingProfile != null)
            {
                _run.profileId = _ratingProfile.profileId; _run.profileRevision = _ratingProfile.profileRevision;
                _run.balanceRevision = _ratingProfile.balanceRevision; _run.ratingRevision = _ratingProfile.ratingRevision; _run.planHash = _ratingProfile.planHash;
                _run.expectedWaveCount = _ratingProfile.expectedWaveCount; _run.expectedEnemyCount = _ratingProfile.expectedEnemyCount;
            }
            _settled = false; _pendingResult = null; _pendingSaveResult = null; _unresolvedEnemies.Clear();
            SaveManager.Instance.EnsureRatingVersion(levelId);

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
                GameAudio.EndLevel();
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

            // ⑧ 预加载本关会用到的资源（打 AB 时提前取好包引用）
            PreloadLevelResources();

            // ⑨ 回合队列
            _roundIds = Level.RoundIds != null ? new List<int>(Level.RoundIds) : new List<int>();
            _roundCursor = 0;

            // ⑩ M3-5：若本关存在局内快照，恢复到"上次退出的那一刻"。
            //    放在最后：棋盘/管理器/HUD 都已就绪，恢复出来的塔才有地方落。
            TryRestoreSnapshot(Level.Id);

            State = GameFlowState.Preparing;
            // The restored cursor must be published together with the restored economy and statistics.
            if (hud != null) hud.RefreshAll();
            if (_roundCursor == _roundIds.Count && _run.completedWaveCount == _roundIds.Count)
            {
                CompleteVictory();
                return;
            }
            Debug.Log(string.Format(
                "[Flow] 关卡 {0}「{1}」就绪：棋盘 {2}×{3}，格子 {4} 世界单位，回合 {5} 个\n{6}",
                Level.Id, Level.Name, Map.Cols, Map.Rows, cellSize, _roundIds.Count,
                AStarManager.Instance.DescribeCurrentPath()));
            Tips(Localization.Get("Level ready: {0}, click Start to fight", Localization.LevelName(Level.Id, Level.Name)) ?? string.Format("关卡就绪：{0}，点击「开始」迎战", Localization.LevelName(Level.Id, Level.Name)));

            // ⑪ 【真机诊断】缺失脚本扫描：延时 1 秒，覆盖 HUD / 资源预加载 / 快照恢复
            //    全部就位后的对象树。无缺失打一行 OK；有缺失则列出"对象路径 + 槽位数"
            //    （[Audit] 前缀），配合 Unity 自身的 "referenced script is missing" 警告
            //    可一步定位缺失脚本的宿主对象。
            RuntimeMissingScriptAudit.RunDeferred(this, 1f);

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
            ctrl.topMarginCells = Mathf.Max(ctrl.topMarginCells, 1.6f);
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
                Tips(Localization.Get("Wave in progress, wait for it to finish") ?? "波次进行中，请等待本波结束");
                return;
            }
            if (State == GameFlowState.GameOver)
            {
                Tips(Localization.Get("Game already ended") ?? "本局已结束");
                return;
            }
            if (State != GameFlowState.Preparing)
            {
                return;
            }
            if (_roundCursor >= _roundIds.Count)
            {
                CompleteVictory();
                return;
            }

            RoundConfig round = Configs.GetRound(_roundIds[_roundCursor]);
            if (round == null)
            {
                Tips(Localization.Get("Wave config missing") ?? "波次配置缺失");
                Debug.LogError(string.Format("[Flow] 找不到回合配置 id={0}", _roundIds[_roundCursor]));
                return;
            }

            // Persist preparation as one complete checkpoint, then freeze all half-wave changes.
            SaveSnapshotNow();
            if (_roundCursor == 0 && _run.completedWaveCount == 0) GameClock.StartLevelTimer();
            _unresolvedEnemies.Clear();
            int expected = 0;
            if (round.WaveIds != null) foreach (int waveId in round.WaveIds) { var group = Configs.GetWaveGroup(waveId); if (group != null) expected += group.EnemyCount; }
            _run.waves.Add(new WaveRunMetrics { ordinal = _roundCursor + 1, expected = expected, combatStartSeconds = GameClock.CombatElapsedSeconds });
            _wave.BeginRound(round);
            State = GameFlowState.RoundRunning;
            EventDispatcher.TriggerEvent<int>(EventName.RoundStartEvent, _roundCursor + 1);
            Tips(Localization.Get("Wave {0}/{1}", _roundCursor + 1, _roundIds.Count)
                ?? string.Format("第 {0}/{1} 波", _roundCursor + 1, _roundIds.Count));
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
            GameAudio.Play(SoundCue.SpeedChange);
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
        /// CombatSystem 先完成本帧战斗，LateUpdate 再推进出生时间轴。
        /// 结束判定使用即时出生/结算账本，覆盖本阶段刚生成的怪物。
        /// </summary>
        private void LateUpdate()
        {
#if UNITY_EDITOR
            if (GameClock.IsManualSimulation) return;
#endif
            TickFlowSimulation();
        }
#if UNITY_EDITOR
        public void StepManualSimulation() { TickFlowSimulation(); }
#endif
        private void TickFlowSimulation()
        {
            // 自动回合倒计时（不受 State 限制，见 TickAutoNextRound 的说明）
            TickAutoNextRound(GameClock.DeltaTime);

            if (State != GameFlowState.RoundRunning)
            {
                return;
            }

            _wave.Tick(GameClock.DeltaTime);

            // The wave may have spawned its final enemy after CombatSystem cached its
            // count this frame. The outcome ledger includes that spawn immediately.
            int alive = _unresolvedEnemies.Count;
            _wave.CheckGroupCleared(alive);

            if (_wave.IsRoundFinished(alive))
            {
                FinishRound();
            }
        }

        private void FinishRound()
        {
            if (State != GameFlowState.RoundRunning || _settled) return;
            if (_unresolvedEnemies.Count > 0) return;
            WaveRunMetrics completed = _run != null && _run.waves.Count > 0 ? _run.waves[_run.waves.Count - 1] : null;
            if (completed == null || completed.successfulSpawned != completed.expected || completed.killed + completed.leaked != completed.expected)
            {
                InvalidateRun("Wave ended with incomplete enemy accounting");
                return;
            }
            _wave.Stop();
            GameClock.SetCombatRunning(false);
            int finishedIndex = _roundCursor + 1;

            // 回合奖励
            if (_roundCursor < _roundIds.Count)
            {
                RoundConfig rc = Configs.GetRound(_roundIds[_roundCursor]);
                if (rc != null && rc.RewardGold > 0)
                {
                    PlayerDataManager.Instance.AddGold(rc.RewardGold);
                    Tips(Localization.Get("Wave reward +{0} gold", rc.RewardGold)
                        ?? string.Format("波次奖励 +{0} 金币", rc.RewardGold));
                }
            }

            EventDispatcher.TriggerEvent<int>(EventName.RoundClearEvent, finishedIndex);

            _roundCursor++;
            _run.completedWaveCount = _roundCursor;
            if (completed != null)
            {
                completed.combatEndSeconds = GameClock.CombatElapsedSeconds;
                completed.levelEndSeconds = GameClock.LevelElapsedSeconds;
                completed.gold = PlayerDataManager.Instance.Gold; completed.hp = PlayerDataManager.Instance.Hp;
                RoundConfig finishedRound = Configs.GetRound(_roundIds[_roundCursor - 1]);
                completed.clearGold = finishedRound != null ? finishedRound.RewardGold : 0;
            }
            State = GameFlowState.RoundComplete;

            // Save the next-wave wait in the same coherent boundary as tower phases.
            float delay = _roundCursor < _roundIds.Count && Configs.Global != null ? Configs.Global.AutoNextRoundDelaySec : 0f;
            _autoNextTimer = Mathf.Max(0f, delay); _autoNextTipAcc = 0f;

            // M3-5：每回合结束存一次快照 —— 这是"退出后继续"的粒度。
            // 【为什么是回合边界】只有此刻状态是自洽的：场上无残留怪物、金币与塔都已结算。
            // 半途存盘就得额外记录每只怪的位置/血量/波次进度，复杂度与收益完全不成比例。
            SaveSnapshotNow();

            if (_roundCursor >= _roundIds.Count)
            {
                CompleteVictory();
            }
            else
            {
                // 回到可开始状态：HUD 收到 RoundClearEvent 会把按钮恢复成「下一回合」
                State = GameFlowState.Preparing;

                // 自动开下一回合：间隔读常数表（Global.autoNextRoundDelayMs）
                // 留出间隔是为了让玩家在两波之间布防/卖塔；设 0 则完全交给玩家手动点
                if (delay > 0f)
                {
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
                    _hud.SetStartButtonLabel(Localization.Get("Next Wave") ?? "下一波");
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
                    _hud.SetStartButtonLabel(Localization.Get("Next Wave ({0})", sec)
                        ?? string.Format("下一波({0})", sec));
                }
                Tips(Localization.Get("Wave complete, next wave starts in {0}s", sec)
                    ?? string.Format("本波完成，{0} 秒后自动开始下一波", sec));
            }
        }

        private void OnGameOver(bool victory)
        {
            GameClock.StopLevelTimer();
            if (_run != null && victory && !_settled) _run.debugOverride = true;
            _wave.Stop();
            State = GameFlowState.GameOver;
            // 结算即离场：倍速复位 ×1，结算界面下按钮也不再可用（HudView 会置灰）
            ResetGameSpeed();
            Debug.Log(string.Format("[Flow] 本局结束：{0}\n{1}",
                victory ? "胜利" : "失败", PlayerDataManager.Instance.DumpDebugInfo()));
            Tips(victory
                ? (Localization.Get("Congratulations!") ?? "恭喜通关！")
                : (Localization.Get("Defense failed...") ?? "防御失败……"));

            // 屏幕震动（UI 补全 C3）：只有"失败"才震，且给最大的系数 1.5 ——
            // 生命归零是本局最重的一次负面事件；胜利时抖一下反而像出错。
            if (!victory && CameraController.Instance != null && Configs.Global != null)
            {
                CameraController.Instance.Shake(
                    Configs.Global.ShakeAmplitude * 1.5f, Configs.Global.ShakeDurationSec);
            }

            ShowClearPopup(victory);
        }
        private LevelRatingResult EvaluateRun(bool victory)
        {
            if (_run == null) return LevelRatingEvaluator.Evaluate(_ratingProfile, null);
            _run.victory = victory;
            var pd = PlayerDataManager.Instance;
            _run.hp = pd != null ? pd.Hp : 0; _run.maxHp = pd != null ? pd.MaxHp : 0;
            _run.combatElapsedSeconds = GameClock.CombatElapsedSeconds;
            _run.levelElapsedSeconds = GameClock.LevelElapsedSeconds;
            return LevelRatingEvaluator.Evaluate(_ratingProfile, _run);
        }
        private void CompleteVictory()
        {
            if (_settled) return;
            _settled = true;
            GameClock.StopLevelTimer();
            State = GameFlowState.GameOver;
            var result = EvaluateRun(true);
            int previousBest = SaveManager.Instance.GetStars(Level.Id);
            bool saved = result.valid && SaveManager.Instance.RecordClear(Level.Id, result);
            _pendingSaveResult = result.valid && !saved ? result : null;
            _pendingResult = BuildClearInfo(true, result.stars, previousBest);
            _pendingResult.ratingResult = result;
            _pendingResult.progressSaved = saved;
            _pendingResult.savePending = result.valid && !saved;
            _pendingResult.newRecord = saved && result.stars > previousBest;
            if (_pendingResult.savePending)
            {
                var reasons = new List<string>(result.reasons); reasons.Add("Record could not be saved; retry save"); result.reasons = reasons.ToArray();
                Debug.LogWarning("[Save] Final checkpoint retained; retry result saving before leaving.");
            }
            EventDispatcher.TriggerEvent<int, int, int>(EventName.LevelClearEvent, Level.Id, result.stars, PlayerDataManager.Instance.Hp);
            PlayerDataManager.Instance.Win();
        }
        public bool RetryPendingClearSave()
        {
            if (_pendingSaveResult == null || _pendingResult == null || Level == null) return false;
            if (!SaveManager.Instance.RecordClear(Level.Id, _pendingSaveResult)) return false;
            _pendingResult.progressSaved = true; _pendingResult.savePending = false;
            _pendingResult.newRecord = _pendingResult.stars > _pendingResult.previousBest;
            _pendingResult.ratingResult = LevelRatingEvaluator.Evaluate(_pendingSaveResult.profile, _pendingSaveResult.metrics);
            _pendingSaveResult = null;
            var view = UIManager.Instance.Open<LevelClearView>(LevelClearView.LogicalName, UILayout.NormalPanel);
            if (view != null) view.Show(_pendingResult);
            return true;
        }
        public void MarkDebugRun() { if (_run != null) _run.debugOverride = true; }
        public void InvalidateRun(string reason)
        {
            if (_run != null) _run.statisticsValid = false;
            GameClock.StopLevelTimer(); _wave.Stop();
            Debug.LogError("[Rating] Formal run invalidated: " + reason);
            State = GameFlowState.GameOver;
            ShowClearPopup(false);
        }
        public void NotifyEnemySpawned(BaseEnemy enemy)
        {
            if (_run == null || State != GameFlowState.RoundRunning || enemy == null) return;
            if (!_unresolvedEnemies.Add(enemy)) { _run.statisticsValid = false; return; }
            _run.successfulSpawned++;
            GameClock.SetCombatRunning(true);
            if (_run.waves.Count > 0)
            {
                var wave = _run.waves[_run.waves.Count - 1]; wave.successfulSpawned++;
                wave.peakAlive = Mathf.Max(wave.peakAlive, _unresolvedEnemies.Count);
            }
        }
        private void OnRatedEnemyKilled(BaseEnemy enemy, int reward) { RecordEnemyOutcome(enemy, false, reward); }
        private void OnRatedEnemyLeaked(BaseEnemy enemy, int damage) { RecordEnemyOutcome(enemy, true, 0); }
        private void RecordEnemyOutcome(BaseEnemy enemy, bool leaked, int reward)
        {
            if (_run == null || enemy == null || !_unresolvedEnemies.Remove(enemy)) return;
            // Read identity before ReachedEnd recycles the object; HP is read only at final settlement.
            int id = enemy.Config != null ? enemy.Config.Id : 0;
            bool boss = _ratingProfile != null && _ratingProfile.bossVariantIds.Contains(id);
            bool critical = _ratingProfile != null && _ratingProfile.criticalVariantIds.Contains(id);
            if (leaked) { _run.leaked++; if (boss) _run.bossLeaked++; if (critical) _run.criticalLeaked++; }
            else _run.killed++;
            if (_run.waves.Count > 0)
            {
                var wave = _run.waves[_run.waves.Count - 1];
                if (leaked) { wave.leaked++; if (boss) wave.bossLeaked++; if (critical) wave.criticalLeaked++; }
                else { wave.killed++; wave.killGold += reward; }
                // The last planned entity has settled; death animation recycling does not count.
                if (wave.successfulSpawned == wave.expected && wave.killed + wave.leaked == wave.expected) GameClock.SetCombatRunning(false);
            }
        }
        private void OnApplicationPause(bool paused) { GameClock.SetBackground(paused); }
        private void OnApplicationFocus(bool focused) { GameClock.SetBackground(!focused); }

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
                // Failure and debug previews use the same evaluator without persisting progress.
                int previousBest = Level != null ? SaveManager.Instance.GetStars(Level.Id) : 0;
                LevelRatingResult result = EvaluateRun(victory);
                info = BuildClearInfo(victory, result.stars, previousBest);
                info.ratingResult = result;
            }
            // Keep the same frozen result if a duplicate event reopens the popup.
            _pendingResult = info;

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
            info.levelName = Level != null ? Localization.LevelName(Level.Id, Level.Name) : null;
            info.stars = Mathf.Clamp(stars, 0, LevelRatingEvaluator.MaxStars);
            info.previousBest = Mathf.Clamp(previousBest, 0, LevelRatingEvaluator.MaxStars);
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
                    info.nextLevelName = Localization.LevelName(s.Id, s.Name);
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
            if (Level == null || _run == null || State == GameFlowState.RoundRunning || State == GameFlowState.GameOver)
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
            snap.formatVersion = 2;
            snap.ratingProfile = _ratingProfile != null ? _ratingProfile.Clone() : null;
            _run.combatElapsedSeconds = GameClock.CombatElapsedSeconds;
            _run.levelElapsedSeconds = GameClock.LevelElapsedSeconds;
            _run.hp = snap.hp; _run.maxHp = snap.maxHp;
            snap.metrics = _run.Clone();
            snap.levelTimerStarted = GameClock.IsLevelTimerRunning;
            snap.autoNextRemainingSeconds = _autoNextTimer;

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
                t.CaptureCheckpointState(ts);
                snap.towers.Add(ts);
            }

            SaveManager.Instance.SetSnapshot(snap);
        }

        /// <summary>
        /// 尝试用快照恢复本关进度。
        ///
        /// Restore the complete checkpoint, including statistics and fractional clocks.
        /// Any incompatible content or missing tower invalidates the entire checkpoint.
        /// </summary>
        private void TryRestoreSnapshot(int levelId)
        {
            if (!SaveManager.Instance.HasSnapshot)
            {
                return;
            }
            LevelSnapshot snap = SaveManager.Instance.Snapshot;
            if (snap == null || snap.levelId != levelId)
            {
                return;
            }
            string invalidReason;
            if (!LevelCheckpointValidator.IsCompatible(snap, _ratingProfile, _roundIds.Count, out invalidReason) || SaveManager.Instance.IsRunCommitted(levelId, snap.metrics != null ? snap.metrics.runId : null))
            {
                Debug.LogWarning("[Rating] Checkpoint discarded; restart current level: " + invalidReason);
                Tips(Localization.Get("Checkpoint incompatible: restart level") ?? "Checkpoint incompatible: restart level");
                SaveManager.Instance.ClearSnapshot(true);
                return;
            }

            PlayerDataManager.Instance.RestoreState(levelId, snap.gold, snap.hp, snap.maxHp, snap.metrics.killed, snap.metrics.leaked);

            int built = 0;
            for (int i = 0; i < snap.towers.Count; i++)
            {
                TowerSnapshot ts = snap.towers[i];
                BaseTower restored = ts != null ? TowerManager.Instance.RestoreTower(ts.type, ts.level, ts.row, ts.col) : null;
                if (restored != null && restored.RestoreCheckpointState(ts))
                {
                    built++;
                }
                else
                {
                    // Never certify a partially restored layout. Reset the whole checkpoint.
                    TowerManager.Instance.ClearAll();
                    PlayerDataManager.Instance.InitFromLevel(Level);
                    SaveManager.Instance.ClearSnapshot(true);
                    AStarManager.Instance.RequestRefresh();
                    Debug.LogWarning("[Rating] Tower restoration failed: checkpoint discarded, level restarted");
                    return;
                }
            }

            _roundCursor = snap.roundCursor;
            _run = snap.metrics.Clone();
            GameClock.RestoreTimers(_run.combatElapsedSeconds, _run.levelElapsedSeconds, snap.levelTimerStarted);
            _autoNextTimer = snap.autoNextRemainingSeconds; _autoNextTipAcc = 0f;

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
            Tips(Localization.Get("Resumed from checkpoint (next wave: {0})", _roundCursor + 1)
                ?? string.Format("已从完整检查点继续（下一波：第 {0} 波）", _roundCursor + 1));
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
            GameAudio.EndLevel();
            _autoNextTimer = 0f;
            // 离开对局必须解除暂停：走统一写入口（原先是裸写 Time.timeScale = 1f）
            SetPausedState(false);

            // 关卡计时停止（UI 补全 B4）。放在这里而不是各出口分别调：
            // TeardownLevel 是唯一的拆卸入口，所有离开对局的路径都会经过它。
            GameClock.StopLevelTimer();

            // ① 玩家操作态
            if (TowerPlacement.Instance != null)
            {
                // ★ 光调 Deselect 不够：放置中的预览体走的是另一条分支，
                //   关卡结束时正在放塔的话，幽灵塔会跟着进下一关。
                TowerPlacement.Instance.CancelPlacement();
                TowerPlacement.Instance.Deselect();
            }
            // 面板的"已打开过"标记跟着实例一起作废，否则下次选中塔会走错分支

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
            // 飘字是"一次性表现"，寿命很短、自己也会消失，但它同样是
            // "上一关的画面"。一起收掉，让 TeardownLevel 成为一个完整的闭环 ——
            // 以后新增这类短命特效时，也照这个模式在这里登记一笔。
            FloatingTextManager.ClearAll();

            // ④ 界面
            UIManager.Instance.Close(TowerInfoView.LogicalName);
            UIManager.Instance.Close(PauseView.LogicalName);
            UIManager.Instance.Close(SettingView.LogicalName);
            // 游戏介绍弹窗（2026-10-14）也归这里关：点弹窗里的「回到选关」同样走
            // TeardownLevel，不在这里关的话弹窗会跟着进到新关卡里盖住画面。
            UIManager.Instance.Close(GameIntroView.LogicalName);
            // 结算弹窗也归这里关：点「下一关 / 重玩 / 返回选关」都会走到 StartLevel/QuitToSelect，
            // 两者第一步都是 TeardownLevel —— 不在这里关，弹窗会跟着进到新关卡里盖住画面。
            UIManager.Instance.Close(LevelClearView.LogicalName);
            // ★ HUD 也必须关。它是**被复用**的界面（UIManager.Open 对已存在的实例直接返回），
            //   不销毁就等于把上一局的按钮状态（"已通关"且不可点）原样带进新关卡 ——
            //   玩家进新关后会发现「开始」按钮点不动，第一回合永远开不了。
            UIManager.Instance.Close(HudView.LogicalName);
            _hud = null;
            State = GameFlowState.None;
        }

        /// <summary>切到指定关卡（或重开同一关）。</summary>
        public void StartLevel(int levelId)
        {
            if (levelId <= 0)
            {
                return;
            }
            if (SaveManager.Instance.HasSnapshot && SaveManager.Instance.Snapshot.levelId != levelId && !SaveManager.Instance.TryClearSnapshot())
            {
                Tips(Localization.Get("Checkpoint could not be cleared; original progress preserved") ?? "无法清除续玩记录，已保留原进度");
                return;
            }
            TeardownLevel();
            UIManager.Instance.Close(SelectView.LogicalName);
            // Selection resumes the compatible checkpoint for the same level.
            BeginLevelWithMask(levelId);
        }

        /// <summary>
        /// 带遮罩的进关（UI 补全 C4）。
        /// 【为什么必须"延迟一帧"】`InitLevel` 全程同步 —— 同帧里 Show 完立刻 Hide，
        /// 遮罩一帧都不会被渲染，等于没做。这里先让遮罩拿到一帧，再干重活。
        /// </summary>
        private void BeginLevelWithMask(int levelId)
        {
            LevelLoadingMask.Show(Localization.Get("Entering level {0}...", levelId)
                ?? string.Format("正在进入第 {0} 关...", levelId));
            StartCoroutine(InitLevelDeferred(levelId));
        }

        private System.Collections.IEnumerator InitLevelDeferred(int levelId)
        {
            yield return null;          // 让遮罩先渲染一帧
            InitLevel(levelId);         // 同步重建（棋盘/路径/实体/界面）
            LevelLoadingMask.Hide();    // 就绪后淡出（unscaled 时间，约 0.18s）
        }

        public void RestartLevel()
        {
            if (Level == null)
            {
                return;
            }
            if (_pendingSaveResult != null && !RetryPendingClearSave()) return;
            if (!SaveManager.Instance.TryClearSnapshot())
            {
                Tips(Localization.Get("Checkpoint could not be cleared; original progress preserved") ?? "无法清除续玩记录，已保留原进度");
                return;
            }
            StartLevel(Level.Id);
        }

        /// <summary>退出当前对局，回到关卡选择。</summary>
        public void QuitToSelect()
        {
            if (_pendingSaveResult != null && !RetryPendingClearSave()) return;
            SaveSnapshotNow();
            TeardownLevel();
            State = GameFlowState.None;
            // 回选关 = 离场：倍速复位 ×1（重开/下一关走 StartLevel→InitLevel，那里也会复位）
            ResetGameSpeed();
            OpenSelect();
        }

        /// <summary>
        /// 打开关卡选择界面。
        /// 【为什么返回 SelectView】调用方（OnConfigLoaded）要判断"是否打开成功"来决定降级路径；
        /// </summary>
        public SelectView OpenSelect()
        {
            SelectView sv = UIManager.Instance.Open<SelectView>(SelectView.LogicalName, UILayout.NormalPanel);
            return sv;
        }

        private void OnSelectLevelRequest(int levelId)
        {
            StartLevel(levelId);
        }

        /// <summary>
        /// 选关界面点「返回」。
        ///
        /// 【修了什么】原实现只 <c>Close(SelectView)</c> 就返回 —— 但选关**没有自己的场景**：
        ///   选关是叠在主菜单上的一层整页界面（见 <see cref="OnStartGameRequest"/>：先把主菜单
        ///   Close 掉才开选关）。只关掉自己，屏幕就只剩背景，玩家**既没回到主菜单、也没回到对局**，
        ///   看起来就是"点了返回没反应"。这里补上"回主菜单"这一步。
        ///
        /// 【为什么用 State 区分】选关有两个入口：
        ///   · 主菜单「开始游戏」→ State 仍是 None（没有对局）→ 返回 = 回主菜单；
        ///   · 对局中「退出选关」(QuitToSelect) → State != None → 返回 = 回对局（先 Teardown 再开选关，
        ///     否则旧棋盘 / HUD 会跟回来，与 <see cref="QuitToSelect"/> 的拆卸口径一致）。
        /// </summary>
        private void OnCloseSelectRequest()
        {
            UIManager.Instance.Close(SelectView.LogicalName);

            if (State == GameFlowState.None)
            {
                // 没有进行中的对局 → 返回主菜单。缺 prefab 时降级：直接进选关（不让启动卡住）。
                MainMenuView menu = UIManager.Instance.Open<MainMenuView>(
                    MainMenuView.LogicalName, UILayout.NormalPanel);
                if (menu == null)
                {
                    Debug.LogWarning("[Flow] MainMenuView 打开失败（prefab 可能还没生成），降级为直接进选关");
                    OpenSelectOrFirstLevel();
                }
                return;
            }

            // 对局中退出的选关 → 返回 = 回对局（先按要求拆卸，再重新建关）
            TeardownLevel();
            State = GameFlowState.None;
            ResetGameSpeed();
            InitLevel(Level != null ? Level.Id : Configs.GetFirstLevelId());
        }

        /// <summary>
        /// 打开暂停**菜单**弹窗（2026-10-18 起由 HUD 的 Btn_Intro 发送）。
        /// 【为什么不在这里暂停】暂停已与"弹窗"解耦：
        ///   · 暂停/继续 = Btn_Pause → <see cref="OnPauseToggleRequest"/> → <see cref="TogglePause"/>；
        ///   · 本方法只负责"把菜单摆出来"，**不动 timeScale**（弹窗想开就开，战斗照常）。
        ///   这样两个按钮的职责互不覆盖，也不会出现"关菜单顺手把暂停丢了"。
        /// </summary>
        private void OnPauseRequest()
        {
            if (State == GameFlowState.GameOver)
            {
                return;   // 已结算就别再开菜单了（结算界面在那儿）
            }
            SetPausedState(true);
            PauseView view = UIManager.Instance.Open<PauseView>(PauseView.LogicalName, UILayout.NormalPanel);
            if (view == null)
            {
                Debug.LogWarning("[Flow] PauseView 打开失败（prefab 可能还没生成）");
            }
        }

        /// <summary>
        /// 暂停 / 继续（HUD 的 Btn_Pause、键盘 P）。
        /// 【为什么暂停也要过流程层】HUD 持有不了"是否局中/是否已结算"这些状态；
        ///   而且暂停唯一的合法写入口必须只有一处（GameClock.SetPaused），否则
        ///   多个界面各写一次 timeScale 就会出现互相覆盖的僵死状态。
        /// </summary>
        private void OnPauseToggleRequest()
        {
            TogglePause();
        }

        /// <summary>暂停态取反。只在"局中"三种状态生效（Loading / None / GameOver 一律忽略）。</summary>
        public void TogglePause()
        {
            if (State != GameFlowState.Preparing &&
                State != GameFlowState.RoundRunning &&
                State != GameFlowState.RoundComplete)
            {
                Debug.Log(string.Format("[Flow] 当前状态 {0} 不接受暂停切换，已忽略", State));
                return;
            }
            bool paused = !GameClock.IsPaused;
            SetPausedState(paused);
            // 【真机诊断埋点】"点暂停没反应"排查链第二环：开关是否真的落到 timeScale 上
            Debug.Log(string.Format("[Flow] {0}（timeScale={1}）", paused ? "暂停" : "继续", Time.timeScale));
        }

        /// <summary>
        /// 暂停状态的**唯一**写入口：改 timeScale + 广播变化（真的变了才广播）。
        /// 【为什么集中在一处】UI（PauseView 标题）与流程层都要看这个状态；
        ///   若各处分别写 timeScale、再各自派事件，就会出现"界面已切文案但时间没停"这类错位。
        /// </summary>
        private void SetPausedState(bool paused)
        {
            bool changed = GameClock.IsPaused != paused;
            GameClock.SetPaused(paused);
            if (changed)
            {
                EventDispatcher.TriggerEvent<bool>(EventName.PauseStateChangedEvent, paused);
            }
        }

        /// <summary>强制恢复运行（离开对局 / 重开 / 热键取消时用），幂等。</summary>
        public void EnsureRunning()
        {
            if (GameClock.IsPaused)
            {
                GameClock.SetPaused(false);
            }
        }

        private void OnResumeRequest()
        {
            UIManager.Instance.Close(PauseView.LogicalName);
            UIManager.Instance.Close(SettingView.LogicalName);
            // 走统一写入口（原先是直接写 Time.timeScale，与流程层的暂停状态容易脱钩）
            SetPausedState(false);
        }

        private void OnRestartRequest()
        {
            RestartLevel();
        }

        private void OnQuitToSelectRequest()
        {
            QuitToSelect();
        }

        /// <summary>
        /// 打开游戏介绍弹窗（GameIntroView，2026-10-14）。
        /// 【2026-10-18 现状】HUD 的 Btn_Intro 已改为打开暂停菜单（PauseRequestEvent），
        ///   本入口暂时**没有发送方**——保留是为了 GameIntroView 的资产/契约不失效
        ///   （将来要恢复入口，加一颗按钮发 OpenGameIntroRequestEvent 即可，流程层不用再改）。
        /// 【为什么不暂停】弹窗是查阅型界面，打开期间战斗照常；暂停只由 Btn_Pause 控制。
        /// </summary>
        private void OnOpenGameIntroRequest()
        {
            GameIntroView view = UIManager.Instance.Open<GameIntroView>(
                GameIntroView.LogicalName, UILayout.NormalPanel);
            if (view == null)
            {
                Debug.LogWarning("[Flow] GameIntroView 打开失败（prefab 可能还没生成）");
            }
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

        // Tower selection is presented by the HUD TowerActionMenu; More opens details.
        private void OnTowerUpgradeRequest(BaseTower tower)
        {
            // 【真机诊断埋点】面板 UpgradeBtn → 这里 → TryUpgrade。
            //   有这条但没升级 → TryUpgrade 内部失败（金币/满级/资源），Tips 有提示；
            //   连这条都没有 → 按钮点击没发事件（prefab 节点缺失或点击被吞）。
            Debug.Log("[Flow] OnTowerUpgradeRequest: " + (tower != null ? tower.name : "null"));
            if (TowerManager.Instance.TryUpgrade(tower) == null) GameAudio.Play(SoundCue.UiInvalid);
        }

        private void OnTowerSellRequest(BaseTower tower)
        {
            // UI 补全 C1：这里**不再直接卖**，改为弹确认窗。
            // 真正执行在 OnTowerSellConfirm（只由 SellConfirmView 的"确认出售"触发）。
            SellConfirmView.Show(tower);
        }

        /// <summary>玩家在出售确认窗里点了"确认出售"——这才是真正执行出售的唯一入口。</summary>
        private void OnTowerSellConfirm(BaseTower tower)
        {
            if (tower == null)
            {
                return;
            }
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

            // ---- M3：暂停热键（2026-10-18 改为与 Btn_Pause 同一语义：只暂停/继续，不弹窗）----
            // 【为什么是 P 而不是 ESC】ESC 已被 TowerPlacement 用作"取消放置 / 取消选中"，
            // 两个系统同帧抢同一个键，必然出现"按一下既取消选中又暂停"。
            //
            // 【为什么这里不用 deltaTime】暂停时 Time.timeScale = 0，
            // 任何依赖 scaled time 的轮询都会停摆 —— 一旦暂停就再也按不回来。
            // GetKeyDown 不受 timeScale 影响，所以这个热键在暂停中依然有效。
            if (Input.GetKeyDown(KeyCode.P))
            {
                // 原先：菜单开着 → 继续；否则开菜单。现在暂停与菜单彻底分开：
                // 热键只当暂停开关（菜单由 HUD 的 Btn_Intro 打开），避免"按 P 弹窗"的旧行为残留。
                TogglePause();
            }

            // 调试快捷键：F1 打印完整状态，F2 强制获胜，F3 性能报告（联调/压测用）
            if (Input.GetKeyDown(KeyCode.F1))
            {
                Debug.Log(DumpDebugInfo());
            }
            else if (Input.GetKeyDown(KeyCode.F2))
            {
                MarkDebugRun();
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
