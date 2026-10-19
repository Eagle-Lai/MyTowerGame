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
    ///
    /// 【2026-10-14 新增】右上角两颗按钮 + 塔按钮长按拖拽建造：
    ///   · Btn_Pause  → PauseToggleRequestEvent（GameFlowManager.TogglePause → GameClock.SetPaused）
    ///     ★ 2026-10-18：**不再弹任何窗**，只做暂停/继续开关（点击一次暂停、再点一次恢复）；
    ///       文案两态：未暂停 `Pause` ⇄ 已暂停 `Continue`（RefreshPauseLabel，不挂 TextLocalizer）。
    ///   · Btn_Intro  → PauseRequestEvent（打开暂停菜单 PauseView：继续/重开/设置/退出选关）
    ///     ★ 2026-10-18：弹窗能力由 Btn_Pause 迁移过来；打开菜单**不暂停游戏**
    ///       （暂停只由 Btn_Pause / 热键 P 控制，两个按钮职责互不覆盖）。
    ///   · 塔按钮手势两分：快速点按 = 经典放置态（点击落子）；长按/按住后移动 =
    ///     拖拽建造（TowerDragBeginEvent，ghost 跟手、松手校验落子）——对标《坚守阵地》。
    ///     判定细节见 TowerHoldSec / TowerDragStartPixels 与 OnTowerButtonPressed/Released。
    ///
    /// 【节点层级：文本内嵌在芯片底下】
    ///   GoldText / HpText / RoundText 是 Bg_Gold / Bg_Hp / Bg_Round 的**子节点**
    ///   （不再是 HudView 的直接子节点），所以取值路径是 "Bg_Gold/GoldText" 这种两段式。
    ///   改层级必须与 UIPrefabBuilder.BuildHud 成对改。
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

        // ---- 倍速按钮（P2b）----
        private Button _speedButton;
        private TMP_Text _speedLabel;

        // ---- 右上角：暂停开关 / 暂停菜单（2026-10-14；2026-10-18 职责重划）----
        private Button _pauseButton;
        private Button _introButton;
        /// <summary>
        /// 暂停按钮的文案（2026-10-18 起由本类按状态写：未暂停 = Pause，已暂停 = Continue）。
        /// 【为什么不用 TextLocalizer】它是**两态文本**，和 MuteBtn 同类：挂了本地化组件后，
        ///   切语言会按 prefab 原文（Pause）重刷，把"已暂停 → Continue"冲掉。
        ///   所以该节点刻意不挂 TextLocalizer（见 LocalizationPrefabBinder 的 Btn_Pause 跳过规则），
        ///   切语言时由 OnLanguageChanged → RefreshPauseLabel 按当前状态重算。
        /// </summary>
        private TMP_Text _pauseLabel;

        /// <summary>
        /// 塔按钮：节点名 → (按钮, 塔型, 价格文本)。
        /// 用数组而不是一堆字段，是为了让"进入/退出放置态时统一置灰"这类操作用循环即可。
        /// </summary>
        private Button[] _towerButtons;
        private int[] _towerButtonTypes;
        private TMP_Text[] _towerPriceTexts;

        // 保留 prefab 的 16:9 槽位；窄安全区只整体右移建塔栏，避开左下倍速按钮。
        private RectTransform _hudRect;
        private RectTransform _speedRect;
        private RectTransform[] _towerButtonRects;
        private Vector2[] _towerButtonLayoutOrigins;
        private float _bottomLayoutWidth = -1f;
        private const float BottomControlGap = 24f;

        /// <summary>当前选中的塔类型与等级（M2 起由按钮决定 type；level 固定 1 = 建造等级）</summary>
        private int _towerType = 1;
        private int _towerLevel = 1;

        /// <summary>进入放置模式后按钮变灰，避免重复点</summary>
        private bool _placing;

        // ---- 语言切换重放（2026-10-16）：见 OnLanguageChanged 的完整说明 ----
        /// <summary>回合文本配方：key + 参数 + 中文兜底格式（null = 当前没有回合文本）。</summary>
        private string _roundKey;
        private int _roundArg;
        private string _roundFallback;

        /// <summary>开始按钮文本配方（null = 外部接管中，如自动回合倒计时每秒重写）。</summary>
        private string _startKey;
        private string _startFallback;

        /// <summary>
        /// 建造栏的塔按钮（三类：普通 / 火力 / 减速 —— 2026-10-14 三塔型收敛定案）。
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
        };

        // 与 TowerNodeNames 一一对应（TowerType：1单体/2范围/3减速）
        private static readonly int[] TowerNodeTypes = { 1, 2, 3 };

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
            EventDispatcher.RemoveEventListener<float>(EventName.GameSpeedChangedEvent, OnSpeedChanged);
            EventDispatcher.RemoveEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
            EventDispatcher.RemoveEventListener<bool>(EventName.PauseStateChangedEvent, OnPauseStateChanged);
        }

        // ------------------------------------------------------------------
        // 绑定
        // ------------------------------------------------------------------

        private void BindNodes()
        {
            // 文本内嵌在芯片底之下（Bg_* 的子节点），路径必须是两段式
            _goldText = FindText("Bg_Gold/GoldText");
            _hpText = FindText("Bg_Hp/HpText");
            _roundText = FindText("Bg_Round/RoundText");

            _startButton = FindButton("StartButton");
            _startLabel = FindChildText("StartButton/Label");
            if (_startButton != null)
            {
                _startButton.onClick.AddListener(OnClickStart);
            }
            if (_startLabel != null)
            {
                // 记配方而非直接写死：切语言时由 OnLanguageChanged 按配方重算（见文件下方"语言切换重放"）
                SetStartLabelLocalized("Start", "开始");
            }

            // 倍速按钮（P2b）：点击循环 ×1→×2→×3→×1
            _speedButton = FindButton("SpeedButton");
            _speedLabel = FindChildText("SpeedButton/Label");
            if (_speedButton != null)
            {
                _speedButton.onClick.AddListener(OnClickSpeed);
            }
            // 【为什么要在这里初始化文案】HUD 是进关时才创建的，而 GameSpeedChangedEvent
            //   只在"档位真的变了"时才派发。若只靠事件，按钮会一直显示 prefab 里的占位文字。
            SetSpeedLabel(GameClock.Speed);

            // 塔按钮（五类）
            _towerButtons = new Button[TowerNodeNames.Length];
            _towerButtonTypes = new int[TowerNodeNames.Length];
            _towerPriceTexts = new TMP_Text[TowerNodeNames.Length];
            _towerButtonRects = new RectTransform[TowerNodeNames.Length];
            _towerButtonLayoutOrigins = new Vector2[TowerNodeNames.Length];
            for (int i = 0; i < TowerNodeNames.Length; i++)
            {
                int type = TowerNodeTypes[i];
                _towerButtons[i] = FindButton(TowerNodeNames[i]);
                _towerButtonTypes[i] = type;
                // PriceText 是"可选节点"：老的 prefab 没有它，不应该报错，只是没有价格可显示
                _towerPriceTexts[i] = FindChildText(TowerNodeNames[i] + "/PriceText");
                if (_towerButtons[i] != null)
                {
                    _towerButtonRects[i] = _towerButtons[i].transform as RectTransform;
                    _towerButtonLayoutOrigins[i] = _towerButtonRects[i].anchoredPosition;
                    int captured = type;
                    _towerButtons[i].onClick.AddListener(delegate { OnClickTower(captured); });

                    // 长按拖拽建造：给每个塔按钮挂按压中继（运行时 AddComponent，不进 prefab，
                    // 避免 prefab 与程序集版本错位产生 missing-script）。手势判定集中在 Update。
                    TowerDragButton drag = _towerButtons[i].GetComponent<TowerDragButton>();
                    if (drag == null)
                    {
                        drag = _towerButtons[i].gameObject.AddComponent<TowerDragButton>();
                    }
                    int capturedIdx = i;
                    drag.OnPressed = delegate { OnTowerButtonPressed(capturedIdx); };
                    drag.OnReleased = delegate { OnTowerButtonReleased(capturedIdx); };
                }
            }

            // 右上角：暂停开关 / 暂停菜单（2026-10-14 新增；2026-10-18 职责重划）
            // 【文案口径】Btn_Intro 的 Label 是静态文案（英文原文 Menu 写死在 prefab），
            //   由 LocalizationPrefabBinder 批量挂 TextLocalizer 自动切语言 —— 与其它界面按钮同口径。
            //   但 Btn_Pause 是**两态**（Pause ⇄ Continue），刻意不挂 TextLocalizer，
            //   由 RefreshPauseLabel 按 GameClock.IsPaused 写、并在语言切换时重算。
            // 【为什么监听器只加一次、且不重复绑】这两个按钮的 prefab 上没有任何持久化 onClick
            //   （m_Calls 为空），绑定只发生在 Awake 这一次；重绑会给同一次点击派发两次事件
            //   （表现为"点暂停立刻又恢复"），所以这里保持"一个按钮一个监听"。
            _pauseButton = FindButton("Btn_Pause");
            if (_pauseButton != null)
            {
                _pauseButton.onClick.AddListener(OnClickPause);
            }
            // 暂停按钮是"暂停/继续"两态：文案由 RefreshPauseLabel 按当前状态写（见字段注释）
            _pauseLabel = FindChildText("Btn_Pause/Label");
            RefreshPauseLabel();
            _introButton = FindButton("Btn_Intro");
            if (_introButton != null)
            {
                _introButton.onClick.AddListener(OnClickIntro);
            }

            _hudRect = transform as RectTransform;
            _speedRect = _speedButton != null ? _speedButton.transform as RectTransform : null;
            RefreshBottomLayout();
        }

        private void OnRectTransformDimensionsChange()
        {
            RefreshBottomLayout();
        }

        private void RefreshBottomLayout()
        {
            if (_hudRect == null || _speedRect == null || _towerButtonRects == null ||
                _towerButtonRects.Length == 0 || _towerButtonRects[0] == null)
                return;

            float width = _hudRect.rect.width;
            if (width <= 0f || Mathf.Abs(width - _bottomLayoutWidth) < 0.01f)
                return;
            _bottomLayoutWidth = width;

            // 角落锚的速度按钮会随屏幕变窄向建塔栏靠近。以父级实际宽度计算边界，
            // 不用 Screen.width，避免 CanvasScaler 和安全区改变后再次互叠。
            Rect parent = _hudRect.rect;
            float speedRight = parent.xMin + width * _speedRect.anchorMin.x +
                _speedRect.anchoredPosition.x + _speedRect.rect.width * (1f - _speedRect.pivot.x);
            RectTransform first = _towerButtonRects[0];
            float firstLeft = parent.xMin + width * first.anchorMin.x +
                _towerButtonLayoutOrigins[0].x - first.rect.width * first.pivot.x;
            float shift = Mathf.Max(0f, speedRight + BottomControlGap - firstLeft);
            for (int i = 0; i < _towerButtonRects.Length; i++)
            {
                if (_towerButtonRects[i] == null) continue;
                Vector2 position = _towerButtonLayoutOrigins[i];
                position.x += shift;
                _towerButtonRects[i].anchoredPosition = position;
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
            EventDispatcher.AddEventListener<float>(EventName.GameSpeedChangedEvent, OnSpeedChanged);
            // 语言切换：重放回合文本与开始按钮文本（配方见 OnLanguageChanged）
            EventDispatcher.AddEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
            // 暂停状态变化：刷新暂停按钮的两态文案（Pause ⇄ Continue）
            EventDispatcher.AddEventListener<bool>(EventName.PauseStateChangedEvent, OnPauseStateChanged);
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
            // 【真机诊断埋点】"点开始没反应"排查链第一环：点击是否到达 HUD。
            // 后续链路：StartRoundRequestEvent → GameFlowManager.OnStartRoundRequest。
            Debug.Log("[HUD] 点击开始回合按钮");
            if (_startButton != null)
            {
                _startButton.interactable = false;
                SetStartLabelLocalized("In Progress", "进行中");
            }
            EventDispatcher.TriggerEvent(EventName.StartRoundRequestEvent);
        }

        private void OnClickTower(int type)
        {
            // 拖拽刚触发过的这一帧，Button 的 onClick 也会跟着来（松手仍在按钮上时），
            // 必须吞掉，否则会把刚进入的拖拽放置态当成"再点一次"给切出去。
            if (_suppressTowerClick)
            {
                Debug.Log("[HUD] 吞掉拖拽残留的 onClick（防误切放置态）");
                return;
            }
            // 不在这里判断"是否已在放置态"——那是 TowerPlacement 的职责。
            // 统一发同一个请求事件，由它决定是进入还是退出（单一状态源，避免两边状态不一致）。
            _towerType = type;
            // 【真机诊断埋点】"点塔按钮无反应"排查链第一环：点击是否到达 HUD；
            // 后续链路看 [Place] EnterPlacement（进入放置）或 [Place] ExitPlacement（切换/取消）。
            Debug.Log(string.Format("[HUD] 点击塔按钮 type={0} level={1}", type, _towerLevel));
            EventDispatcher.TriggerEvent<int, int>(EventName.BuildTowerRequestEvent, _towerType, _towerLevel);
        }

        // ------------------------------------------------------------------
        // 塔按钮手势判定：快速点按 = 经典放置态；长按/按住后移动 = 拖拽建造
        // （2026-10-14，对标《坚守阵地》Fieldrunners 的拖拽建造）
        // ------------------------------------------------------------------

        /// <summary>按住多久判定为"长按拖拽"（秒）。取 0.25：比系统长按（0.5）跟手，又不会把普通点按误判成拖拽。</summary>
        private const float TowerHoldSec = 0.25f;

        /// <summary>按住期间位移超过该像素数也直接进入拖拽（对标原作"按住就拖"，不等长按计时走完）。</summary>
        private const float TowerDragStartPixels = 30f;
        private const float TowerDragStartPixelsSq = TowerDragStartPixels * TowerDragStartPixels;

        /// <summary>当前按住中的塔按钮下标；-1 = 没有按住。</summary>
        private int _towerPressIndex = -1;
        private float _towerPressTime;
        private Vector2 _towerPressPos;
        /// <summary>本次按压是否已经触发过拖拽（一次按压最多触发一次）。</summary>
        private bool _towerDragFiredForPress;
        /// <summary>
        /// 拖拽触发后的一帧窗口：吞掉 Button 的 onClick。
        /// 【为什么只保留一帧】click 在松手当帧由 EventSystem 派发；拖拽已触发后
        /// （无论长按触发还是松手触发），同帧的 click 都属于"拖拽手势的收尾"而非新意图。
        /// 下一帧 Update 清零，不影响之后的正常点按。
        /// </summary>
        private bool _suppressTowerClick;

        private void OnTowerButtonPressed(int index)
        {
            // 已有按住中的按钮 → 忽略第二根手指（同一时刻只认一根，防多点同时开拖）
            if (_towerPressIndex >= 0)
            {
                return;
            }
            _towerPressIndex = index;
            // 用 unscaled 时间：即便有界面把 timeScale 压成 0，手势判定也不能停摆
            _towerPressTime = Time.unscaledTime;
            _towerPressPos = Input.mousePosition;
            _towerDragFiredForPress = false;
        }

        private void OnTowerButtonReleased(int index)
        {
            if (index != _towerPressIndex)
            {
                return;
            }
            _towerPressIndex = -1;

            if (_suppressTowerClick || _towerDragFiredForPress)
            {
                return;   // 拖拽已在按住期间触发过，松手交给 TowerPlacement 的松手分支
            }

            // 兜底判定：长按阈值恰好在"松手这一帧"才满足（Update 先于/后于事件系统都可能），
            // 在这里补一次判定，保证"按住足够久再松"必然走拖拽而不是点按。
            float held = Time.unscaledTime - _towerPressTime;
            Vector2 move = (Vector2)Input.mousePosition - _towerPressPos;
            if (held >= TowerHoldSec || move.sqrMagnitude >= TowerDragStartPixelsSq)
            {
                FireTowerDrag(index);
            }
            // 否则是快速点按：什么都不做，让 Button.onClick 走经典放置态（原交互保留）
        }

        private void FireTowerDrag(int index)
        {
            _towerDragFiredForPress = true;
            _suppressTowerClick = true;
            int type = _towerButtonTypes[index];
            // 【真机诊断埋点】长按拖拽触发点；后续链路看 [Place] EnterPlacement（drag 模式）
            Debug.Log(string.Format("[HUD] 塔按钮长按/拖动 → 拖拽建造 type={0} level={1}", type, _towerLevel));
            EventDispatcher.TriggerEvent<int, int>(EventName.TowerDragBeginEvent, type, _towerLevel);
        }

        private void Update()
        {
            // Canvas 初次布局可能晚于 Awake；宽度未变时不写 RectTransform。
            RefreshBottomLayout();
            // 吞 click 的窗口只保留一帧：click 永远发生在松手当帧，下一帧必然已处理完
            _suppressTowerClick = false;

            // 按住期间的长按/位移监测（拖拽实例由 TowerPlacement 创建并跟手）
            if (_towerPressIndex >= 0 && !_towerDragFiredForPress)
            {
                float held = Time.unscaledTime - _towerPressTime;
                Vector2 move = (Vector2)Input.mousePosition - _towerPressPos;
                if (held >= TowerHoldSec || move.sqrMagnitude >= TowerDragStartPixelsSq)
                {
                    FireTowerDrag(_towerPressIndex);
                }
            }
        }

        // ------------------------------------------------------------------
        // 右上角：暂停开关 / 暂停菜单（2026-10-14；2026-10-18 职责重划）
        // ------------------------------------------------------------------

        /// <summary>
        /// 暂停/继续开关（Btn_Pause）。**不弹任何窗**。
        /// 【链路】PauseToggleRequestEvent → GameFlowManager.OnPauseToggleRequest → TogglePause
        ///   → GameClock.SetPaused（timeScale 0/1）。
        /// 【为什么发给流程层而不是直接写 timeScale】HUD 不持有游戏状态（见类注释），
        ///   且暂停的唯一写入口必须只有一处，否则界面与流程层会各写一次、状态互相覆盖。
        /// </summary>
        private void OnClickPause()
        {
            // 【真机诊断埋点】"点暂停没反应"排查链第一环：点击是否到达 HUD。
            // 后续链路看 [Flow] 暂停/继续（timeScale=…）。
            Debug.Log("[HUD] 点击暂停按钮（暂停/继续开关，不弹窗）");
            EventDispatcher.TriggerEvent(EventName.PauseToggleRequestEvent);
        }

        /// <summary>
        /// 打开暂停菜单弹窗（Btn_Intro）。
        /// 【2026-10-18】原 Btn_Pause 的"弹窗"能力迁移到这里：
        ///   本方法**只发打开菜单的请求，不触发暂停**（PauseView 也不再改 timeScale），
        ///   所以点一下不会把游戏停住；想停请按旁边的 Btn_Pause。
        /// </summary>
        private void OnClickIntro()
        {
            // 【真机诊断埋点】"点菜单按钮没反应"排查链第一环；
            // 后续链路：PauseRequestEvent → GameFlowManager.OnPauseRequest → PauseView。
            Debug.Log("[HUD] 点击暂停菜单按钮（只开菜单，不暂停）");
            EventDispatcher.TriggerEvent(EventName.PauseRequestEvent);
        }

        // ------------------------------------------------------------------
        // 倍速（P2b）
        // ------------------------------------------------------------------

        /// <summary>
        /// 点倍速按钮：按档位表循环切下一档。
        /// 【为什么这里只"发请求"而不直接改 GameClock】
        ///   HUD 不持有任何游戏逻辑（见类注释）。改档要校验"是否暂停/是否局中"，
        ///   那是 GameFlowManager 的职责 —— 直接在 UI 里写 GameClock 会绕过校验。
        /// </summary>
        private void OnClickSpeed()
        {
            EventDispatcher.TriggerEvent<float>(
                EventName.GameSpeedChangeRequestEvent, GameClock.NextTier(GameClock.Speed));
        }

        private void OnSpeedChanged(float speed)
        {
            SetSpeedLabel(speed);
        }

        /// <summary>同步倍速按钮文案：「×1 / ×2 / ×3」（非整数档位如 ×2.5 也支持）。</summary>
        private void SetSpeedLabel(float speed)
        {
            if (_speedLabel != null)
            {
                // 用 InvariantCulture：某些区域设置的小数点是逗号，会显示成「×2,5」
                _speedLabel.text = "×" + speed.ToString("0.#", System.Globalization.CultureInfo.InvariantCulture);
            }
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
            // 外部接管（自动回合倒计时每秒重写）→ 清掉配方，语言事件不再重放旧文案；
            // 倒计时每一拍都会用当前语言重新拼串，切换语言后最多一秒自然对齐。
            _startKey = null;
            if (_startLabel != null)
            {
                _startLabel.text = text;
            }
        }

        // ------------------------------------------------------------------
        // 语言切换重放（2026-10-16）
        //
        // 【为什么需要】回合文本与开始按钮文本是"事件驱动 + 手动拼词"的 —— 节点因此也没有
        //   挂 TextLocalizer（挂了反而会在切语言时把"进行中 / 回合 3"这类状态文本冲成 prefab 原文）。
        //   所以把"最近一次显示用的取词配方"记下来，收到 LanguageChangedEvent 时按同一配方重算：
        //   **只重算文本、不重放副作用**（interactable 等交互状态由原事件路径负责，不能重跑）。
        // ------------------------------------------------------------------

        private void OnLanguageChanged(int lang)
        {
            if (_roundKey != null)
            {
                SetRoundTextLocalized(_roundKey, _roundArg, _roundFallback);
            }
            if (_startKey != null)
            {
                SetStartLabelLocalized(_startKey, _startFallback);
            }
            // 暂停按钮的两态文案（Pause / Continue）没有 TextLocalizer，必须在这里重算；
            // 状态从 GameClock 现取，不依赖任何配方 —— 中途暂停/继续都不会让文案过期。
            RefreshPauseLabel();
        }

        /// <summary>暂停状态变化 → 重刷暂停按钮文案（Pause ⇄ Continue）。</summary>
        private void OnPauseStateChanged(bool paused)
        {
            RefreshPauseLabel();
        }

        /// <summary>
        /// 写暂停按钮文案：未暂停 = Pause（暂停），已暂停 = Continue（继续）。
        /// 【状态源是 GameClock.IsPaused】与"暂停的唯一写入口 GameClock.SetPaused"同一份状态，
        ///   不另存一个布尔，免得 UI 与流程层的暂停态各说各话。
        /// </summary>
        private void RefreshPauseLabel()
        {
            if (_pauseLabel == null)
            {
                return;
            }
            bool paused = GameClock.IsPaused;
            _pauseLabel.text = paused
                ? (Localization.Get("Continue") ?? "继续")
                : (Localization.Get("Pause") ?? "暂停");
            LanguageManager.ApplyFont(_pauseLabel);
        }

        /// <summary>写回合文本并记住配方（语言切换时按配方重放）。</summary>
        private void SetRoundTextLocalized(string key, int arg, string fallbackFormat)
        {
            _roundKey = key;
            _roundArg = arg;
            _roundFallback = fallbackFormat;
            LevelConfig level = Configs.GetLevel(PlayerDataManager.Instance.CurrentLevelId);
            int total = level != null ? level.RoundCount : 0;
            SetText(_roundText, Localization.Get(key, arg, total) ?? string.Format(fallbackFormat, arg, total));
            LanguageManager.ApplyFont(_roundText);
        }

        /// <summary>写开始按钮文本并记住配方（语言切换时按配方重放）。</summary>
        private void SetStartLabelLocalized(string key, string fallback)
        {
            _startKey = key;
            _startFallback = fallback;
            if (_startLabel != null)
            {
                _startLabel.text = Localization.Get(key) ?? fallback;
                LanguageManager.ApplyFont(_startLabel);
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
            GameFlowManager flow = GameFlowManager.Instance;
            SetRoundTextLocalized("Wave {0}/{1}", flow != null ? flow.CurrentRoundIndex : 0, "第 {0}/{1} 波");
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
            SetRoundTextLocalized("Wave {0}/{1}", roundIndex, "第 {0}/{1} 波");
        }

        private void OnWaveStart(int waveIndex)
        {
            // WaveStart 是 Round 内编组索引，不能覆盖本关的正式波次序号。
        }

        private void OnRoundClear(int roundIndex)
        {
            SetRoundTextLocalized("Wave {0}/{1} clear", roundIndex, "第 {0}/{1} 波完成");
            // 恢复"开始"按钮，让玩家推进到下一回合
            if (_startButton != null)
            {
                _startButton.interactable = true;
            }
            SetStartLabelLocalized("Next Wave", "下一波");
        }

        private void OnGameOver(bool victory)
        {
            if (_startButton != null)
            {
                _startButton.interactable = false;
            }
            if (_startLabel != null)
            {
                SetStartLabelLocalized(
                    victory ? "Cleared" : "Failed",
                    victory ? "已通关" : "已失败");
            }
            // 结算后倍速按钮不可用（策划案 §7.3：倍速档位在 GameOver 时复位且不再可切）
            if (_speedButton != null)
            {
                _speedButton.interactable = false;
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
