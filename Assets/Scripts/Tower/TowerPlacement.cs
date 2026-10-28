using System.Collections.Generic;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.Rendering;

namespace FTProject
{
    /// <summary>
    /// 塔放置控制器（P0-7）。
    ///
    /// 【相对 v1.0 的关键改动】
    ///   v1.0 用"塔模型挂 Collider，落到节点上由 OnTriggerEnter 把节点染绿"，
    ///   依赖物理系统与节点物件。现在改为**纯数学**：
    ///     屏幕坐标 → 摄像机世界坐标 → BoardGeometry.WorldToCell → (row, col)
    ///   既去掉了物理开销（需求 8），也不再需要 Node/Point 预制体。
    ///
    /// 【校验顺序（与 TowerManager.TryBuild 一致）】
    ///   格子在棋盘内 → 可建造（非障碍/空洞/装饰） → 无塔 → 金币够 → 不会堵死路径
    ///   前 4 项是廉价判断，A* 推演只在"悬停格变化"时做一次（16×9 网格下开销可忽略）。
    ///
    /// 【2026-10-22：两条放置规则调整（需求）】
    ///   ① **预览只画不改**：悬停格变化时就推演出"建成后怪物会走的新路径"并实时画出来，
    ///      但该路径只存在 AStarManager.PreviewPathWorld（箭头视图读），
    ///      怪物逻辑一行都不读 —— 玩家滑动期间怪物仍旧走原路，松手落地后才真正改道
    ///      （落地时 TryBuild 置墙 + RequestRefresh → RefreshPathEvent → CombatSystem 让怪物改道）。
    ///   ② **怪物脚下可以建塔**：只要求"不会把路彻底堵死"，不再禁止"该格上有怪物"。
    ///      建好后由 CombatSystem.RerouteEnemiesThrough 让脚下那只怪立刻重新寻路走出去。
    ///
    /// 【2026-10-14：两种放置态（对标《坚守阵地》Fieldrunners）】
    ///   · 经典（_dragMode=false）：快速点塔按钮进入，ghost 跟鼠标、点击落子 —— 原交互全保留；
    ///   · 拖拽（_dragMode=true）：长按/按住塔按钮移动触发（HudView 发 TowerDragBeginEvent），
    ///     ghost 跟手 + 悬停格高亮（绿可建/红不可建），**松手**才校验落子：
    ///     可建格 → TryPlace（内部扣钱）；不可建格 → 提示具体原因并取消；
    ///     拖回建造栏/棋盘外松手 → 静默取消（原作"拖回原处收回"的语义）。
    ///   两种模式的"移动/悬停高亮/校验"完全共用，只有"落子时机"不同。
    /// </summary>
    public class TowerPlacement : MonoBehaviour
    {
        public static TowerPlacement Instance { get; private set; }

        /// <summary>预览塔的透明度</summary>
        public const float GhostAlpha = 0.55f;

        private Transform _ghostParent;

        private bool _active;
        private int _type;
        private int _level;
        private TowerConfig _cfg;
        /// <summary>
        /// 拖拽建造模式（2026-10-14）：true = 长按拖拽（松手落子/取消）；
        /// false = 经典放置态（点击落子）。两种模式共用移动/高亮/校验逻辑。
        /// </summary>
        private bool _dragMode;
        private GameObject _ghost;
        private readonly List<SpriteRenderer> _ghostRenderers = new List<SpriteRenderer>(8);

        private int _hoverRow = -1;
        private int _hoverCol = -1;
        private CellHighlight _hoverState = CellHighlight.None;
        private bool _canBuild;
        /// <summary>不可建造的原因 key（多语言），显示时查表；空串 = 可建造。</summary>
        private string _blockReason = "Cannot Build Here";
        /// <summary>原因文案里的可选参数（目前只有"金币不足（需要 N）"用到）。</summary>
        private int? _blockArg;

        /// <summary>当前选中的已建造塔（M2-B1）。未选中为 null。</summary>
        private BaseTower _selected;
        private SortingGroup _selectionGroup;
        private int _selectionOrder;

        public bool IsPlacing { get { return _active; } }

        public BaseTower SelectedTower { get { return _selected; } }

        private void Awake()
        {
            Instance = this;
        }

        private void OnEnable()
        {
            EventDispatcher.AddEventListener<int, int>(EventName.BuildTowerRequestEvent, OnBuildRequest);
            EventDispatcher.AddEventListener(EventName.CancelBuildRequestEvent, OnCancelRequest);
            // 拖拽建造（2026-10-14）：HudView 长按塔按钮触发
            EventDispatcher.AddEventListener<int, int>(EventName.TowerDragBeginEvent, OnDragBegin);
            EventDispatcher.AddEventListener<BaseTower>(EventName.DestroyTower, OnSelectedTowerDestroyed);
        }

        private void OnDisable()
        {
            EventDispatcher.RemoveEventListener<int, int>(EventName.BuildTowerRequestEvent, OnBuildRequest);
            EventDispatcher.RemoveEventListener(EventName.CancelBuildRequestEvent, OnCancelRequest);
            EventDispatcher.RemoveEventListener<int, int>(EventName.TowerDragBeginEvent, OnDragBegin);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.DestroyTower, OnSelectedTowerDestroyed);
            Deselect();
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                Instance = null;
            }
            DestroyGhost();
        }
        public void SetGhostParent(Transform parent)
        {
            _ghostParent = parent;
        }

        // ------------------------------------------------------------------
        // 进入 / 退出放置模式
        // ------------------------------------------------------------------

        private void OnBuildRequest(int type, int level)
        {
            if (_active)
            {
                ExitPlacement(false);
                return;
            }
            EnterPlacement(type, level, false);
        }

        /// <summary>
        /// 拖拽建造入口（HudView 长按/拖动塔按钮时触发）。
        /// 【与 OnBuildRequest 的关键差别】放置态已激活时**不再退出**，而是"换塔"：
        ///   玩家按住 A 塔拖到一半又按住 B 塔的按钮（interactable=false 不拦截指针事件），
        ///   语义显然是"我要建 B"，直接切过去；同塔同等级则视为重复触发，忽略。
        /// </summary>
        private void OnDragBegin(int type, int level)
        {
            if (_active)
            {
                if (_dragMode && _type == type && _level == level)
                {
                    return;   // 已经在拖同一座塔
                }
                Debug.Log(string.Format("[Place] 拖拽切塔 {0}Lv{1} → {2}Lv{3}", _type, _level, type, level));
                ExitPlacement(false);
            }
            EnterPlacement(type, level, true);
        }

        private void OnCancelRequest()
        {
            ExitPlacement(false);
        }

        /// <summary>经典放置态入口（快速点塔按钮）：保留原交互 —— ghost 跟鼠标、点击落子。</summary>
        public void EnterPlacement(int type, int level)
        {
            EnterPlacement(type, level, false);
        }

        private void EnterPlacement(int type, int level, bool dragMode)
        {
            TowerConfig cfg = Configs.GetTowerByTypeAndLevel(type, level);
            if (cfg == null)
            {
                // 【真机诊断埋点】配置缺失导致"点塔按钮无反应"（同时有 Tips 提示）
                Debug.LogWarning(string.Format("[Place] EnterPlacement 失败：找不到 type={0} level={1} 的塔配置", type, level));
                Tips(Localization.Get("No tower config for type={0} level={1}", type, level)
                    ?? string.Format("找不到 type={0} level={1} 的塔配置", type, level));
                return;
            }
            if (!PlayerDataManager.Instance.TryPeek(cfg.Prices))
            {
                // 【真机诊断埋点】金币不足导致"点塔按钮无反应"（同时有 Tips 提示）
                Debug.Log(string.Format("[Place] EnterPlacement 失败：金币不足（需要 {0}，现有 {1}）",
                    cfg.Prices, PlayerDataManager.Instance.Gold));
                Tips(Localization.Get("Not enough gold, need {0}", cfg.Prices)
                    ?? string.Format("金币不足，需要 {0}", cfg.Prices));
                return;
            }

            _type = type;
            _level = level;
            _cfg = cfg;
            _active = true;
            _dragMode = dragMode;
            // 【真机诊断埋点】放置态进入成功（按钮→配置→金币检查全通过）
            Debug.Log(string.Format("[Place] EnterPlacement {0} Lv.{1} price={2} drag={3}",
                cfg.Name, cfg.Level, cfg.Prices, dragMode));
            _hoverRow = -1;
            _hoverCol = -1;
            _hoverState = CellHighlight.None;

            // 进入放置态时先取消已选中的塔（否则面板不会自动关，两个状态并存会互相干扰）
            Deselect();

            CreateGhost(cfg);
            if (_ghost != null && _dragMode)
            {
                // 拖拽模式：ghost 立即落到手指/鼠标位置 —— 否则从按下到下一帧 Update
                // 之间 ghost 会闪现在世界原点（视觉上"塔凭空出现又跳走"）。
                Vector3 w = ScreenToWorld(Input.mousePosition);
                _ghost.transform.position = new Vector3(w.x, w.y, 0f);
            }
            EventDispatcher.TriggerEvent(EventName.BuildingTower);
            if (_dragMode)
            {
                Tips(Localization.Get("{0}: drag onto a buildable tile and release to place", cfg.DisplayName)
                    ?? string.Format("{0}：拖到可建造格上松手放置，拖回按钮取消", cfg.DisplayName));
            }
            else
            {
                Tips(Localization.Get("{0}: move to a buildable tile and click to place, right-click/ESC to cancel", cfg.DisplayName)
                    ?? string.Format("{0}：移动到可建造格上点击放置，右键/ESC 取消", cfg.DisplayName));
            }
        }

        /// <summary>
        /// 取消放置态（切关 / 重开时由流程层调用）。
        ///
        /// 【为什么不能只调 Deselect】Deselect 管的是"已建造塔的选中态"，
        /// 而放置中的预览体（_ghost）与射程圈走的是另一条分支 ——
        /// 关卡结束时若正处在放置态，预览塔会跟着进到下一关，并且继续跟着鼠标跑。
        /// </summary>
        public void CancelPlacement()
        {
            ExitPlacement(false);
        }

        private void ExitPlacement(bool built)
        {
            if (!_active)
            {
                return;
            }
            _active = false;
            // 【真机诊断埋点】与 EnterPlacement 成对：放置态何时进入/退出必须可追溯。
            // 排查"点塔无反应"时若只看到 Enter 没有 Exit，说明点击被放置分支吞掉 →
            // 对照本文件 UpdatePlacement 里"点已建塔自动退出并选中"的处理是否生效。
            Debug.Log(string.Format("[Place] ExitPlacement built={0}", built));
            ClearHover();
            HideRange();
            DestroyGhost();
            EventDispatcher.TriggerEvent(EventName.CancelBuildRequestEvent);
        }

        private void CreateGhost(TowerConfig cfg)
        {
            DestroyGhost();
            _ghost = ResLoader.Instance.Instantiate(cfg.ResName, _ghostParent);
            if (_ghost == null)
            {
                Debug.LogError("[Place] 预览模型创建失败：" + cfg.ResName);
                _active = false;
                return;
            }
            _ghost.name = "TowerGhost";

            _ghostRenderers.Clear();
            _ghostRenderers.AddRange(_ghost.GetComponentsInChildren<SpriteRenderer>(true));
            // 不改 sortingOrder：prefab 里已排好炮座/炮管的相对层次，改半透明即可
            for (int i = 0; i < _ghostRenderers.Count; i++)
            {
                SpriteRenderer sr = _ghostRenderers[i];
                if (sr == null)
                {
                    continue;
                }
                Color c = sr.color;
                c.a = GhostAlpha;
                sr.color = c;
            }

            // 预览体不参与战斗：BaseTower 未 Init（IsBuilt=false），也不会注册进 CombatSystem
            BaseTower t = _ghost.GetComponent<BaseTower>();
            if (t != null)
            {
                t.SetPreviewAlpha(GhostAlpha);
            }
        }

        private void DestroyGhost()
        {
            if (_ghost != null)
            {
                ResLoader.Instance.ReleaseInstance(_cfg != null ? _cfg.ResName : "Tower_Normal0", _ghost);
                _ghost = null;
            }
        }

        // ------------------------------------------------------------------
        // 选中 / 取消选中（M2-B1：点击已建造塔 → 打开升级/出售面板）
        // ------------------------------------------------------------------

        /// <summary>
        /// 处理"非放置态"下的鼠标左键：命中已建造塔 → 选中并广播事件。
        /// 【为什么放在这里】塔是纯 SpriteRenderer，没有 Collider，
        /// 靠"屏幕坐标 → 格子"反查而不是物理射线，与放置预览共用同一套坐标换算，天然一致。
        ///
        /// 【真机诊断埋点】一次点击 = 一条日志，覆盖全链路判定：
        ///   overUi  —— 是否被 UI 拦截（是则直接 return，不改变选中态）
        ///   inBoard —— 是否落在棋盘格内；(row,col) 为命中格子
        ///   tower   —— 命中格子上的塔（null = 空格子）
        /// 排查"点塔没反应"：看这条日志的断点即可（UI 拦截 / 棋盘外 / 空格 / 正常命中→
        /// 后续应出现 [Place] Select 与 [Flow] OnTowerSelected）。
        /// </summary>
        private void HandleSelectClick()
        {
            bool overUi = IsPointerOverUI();
            BoardView board = BoardView.Instance;
            int row = -1;
            int col = -1;
            bool inBoard = board != null && board.ScreenToCell(Input.mousePosition, out row, out col);
            CellData cell = inBoard ? board.GetCell(row, col) : null;
            BaseTower hit = cell != null ? cell.Tower : null;
            Debug.Log(string.Format("[Place] 点塔判定 screen=({0:F0},{1:F0}) overUi={2} inBoard={3} cell=({4},{5}) tower={6}",
                Input.mousePosition.x, Input.mousePosition.y, overUi, inBoard, row, col, hit != null ? hit.name : "null"));

            // 点在 UI 上不要触发（否则点 HUD 面板会顺手选中/取消塔）
            if (overUi)
            {
                return;
            }
            if (board == null)
            {
                return;
            }
            if (!inBoard)
            {
                // 点到棋盘外 → 视为取消选中
                Deselect();
                return;
            }
            if (hit == null)
            {
                Deselect();
                return;
            }
            Select(hit);
        }

        /// <summary>选中一座塔：广播事件（UI 据此打开面板）。重复点同一座不重复广播。</summary>
        public void Select(BaseTower tower)
        {
            if (tower == null)
            {
                Deselect();
                return;
            }
            if (_selected == tower)
            {
                return;
            }
            // 【顺序不能反】必须先清"旧选中"的高亮，再改 _selected。
            // 反过来的话 ClearSelectionHighlight 看到的就是新塔，旧塔的高亮永远清不掉。
            // 也正因为如此，清理方法必须**接收参数**，不能内部读 _selected。
            ClearSelectionHighlight(_selected);
            _selected = tower;
            GameAudio.Play(SoundCue.TowerSelect);
            ApplySelectionHighlight(_selected);
            // 【真机诊断埋点】选中切换成功（重复点同一座塔会在上方相等判断处静默返回）
            Debug.Log("[Place] Select: " + tower.name);
            EventDispatcher.TriggerEvent<BaseTower>(EventName.TowerSelectedEvent, _selected);
        }

        /// <summary>取消选中：广播事件（UI 据此关闭面板）。</summary>
        public void Deselect()
        {
            if (_selected == null)
            {
                RestoreSelectionOrder();
                return;
            }
            ClearSelectionHighlight(_selected);
            _selected = null;
            EventDispatcher.TriggerEvent(EventName.TowerDeselectedEvent);
        }

        private void OnSelectedTowerDestroyed(BaseTower tower)
        {
            if (_selected == tower) Deselect();
        }

        /// <summary>
        /// 升级（换实例）后把选中态从旧塔迁到新塔。
        /// 若升级的正是当前选中的塔，则静默改指向（不发 Deselect，避免面板闪烁关闭）。
        /// 面板随后通过 TowerUpgradeSuccess 事件重新读 SelectedTower 刷新。
        /// </summary>
        public void ReselectAfterSwap(BaseTower old, BaseTower newer)
        {
            if (_selected != old)
            {
                return;
            }
            ClearSelectionHighlight(old);
            _selected = newer;
            // 新实例是刚 Instantiate + Init 出来的，Init 内部已经 SetTint(white)，
            // 所以这里必须把"选中"的视觉重新贴回去，否则升级后高亮会莫名消失。
            ApplySelectionHighlight(_selected);
        }

        /// <summary>选中态塔身提亮色。偏暖白，与"可建造"的绿色 hover 高亮区分开。</summary>
        private static readonly Color SelectedTint = new Color(1f, 0.95f, 0.72f, 1f);

        /// <summary>
        /// 选中态高亮，三件套一起上：① 塔身提亮 ② 所在格染色 ③ 射程圈。
        ///
        /// 【为什么先做提亮而不是描边】描边需要额外的美术资源（M2 待补），
        /// 而 BaseTower.SetTint 已存在，零新增资源就能给出明确、可用的选中反馈。
        /// 美术到位后把这里换成描边/选中 Sprite，调用方无需改动。
        /// </summary>
        private void ApplySelectionHighlight(BaseTower tower)
        {
            if (tower == null)
            {
                return;
            }
            tower.SetTint(SelectedTint);
            RestoreSelectionOrder();
            _selectionGroup=tower.GetComponent<SortingGroup>();
            if (_selectionGroup!=null)
            {
                _selectionOrder=_selectionGroup.sortingOrder;
                _selectionGroup.sortingOrder=BoardSorting.SelectedTower;
            }
            SetCellHighlight(tower.Cell, CellHighlight.Selected);
            ShowRange(tower.Position, tower.Config != null ? tower.Config.RadiusWorld : 0f);
        }

        /// <summary>
        /// 清除选中高亮。
        /// 【参数是"要清哪一座"】调用发生在 _selected 被改写**之前**，
        /// 所以不能依赖 _selected —— 这是原先的 bug：清理方法读不到旧塔，等于没清。
        /// </summary>
        private void ClearSelectionHighlight(BaseTower tower)
        {
            RestoreSelectionOrder();
            if (tower == null)
            {
                return;
            }
            tower.SetTint(Color.white);
            ResetCellHighlight(tower.Cell);
            HideRange();
        }

        private void RestoreSelectionOrder()
        {
            if (_selectionGroup!=null) _selectionGroup.sortingOrder=_selectionOrder;
            _selectionGroup=null;
        }

        // ------------------------------------------------------------------
        // 高亮 / 射程圈工具（都做了空引用容错：棋盘或占位美术缺失时静默降级）
        // ------------------------------------------------------------------

        private static void SetCellHighlight(CellData cell, CellHighlight h)
        {
            if (cell == null || BoardView.Instance == null)
            {
                return;
            }
            BoardView.Instance.SetHighlight(cell.Row, cell.Col, h);
        }

        private static void ResetCellHighlight(CellData cell)
        {
            if (cell == null || BoardView.Instance == null)
            {
                return;
            }
            BoardView.Instance.ResetHighlight(cell.Row, cell.Col);
        }

        /// <summary>
        /// 显示射程圈。RangeIndicatorView.Ensure 在占位贴图缺失时返回 null ——
        /// 射程圈是"锦上添花"，不该因为一张图没生成就把整局玩法拖下水。
        /// </summary>
        private static void ShowRange(Vector2 center, float radiusWorld)
        {
            RangeIndicatorView v = RangeIndicatorView.Ensure();
            if (v != null)
            {
                v.Show(center, radiusWorld);
            }
        }

        private static void HideRange()
        {
            if (RangeIndicatorView.Instance != null)
            {
                RangeIndicatorView.Instance.Hide();
            }
        }

        /// <summary>
        /// 售卖鼠标下的防御塔（**仅当该塔已被选中时**）。
        /// 【M2 变更】原来右键 = 直接卖，误触风险高；现在改为
        /// 右键 = 关闭面板 / 取消选中，出售必须走面板上的确认按钮。
        /// </summary>
        public bool SellSelected()
        {
            if (_selected == null)
            {
                return false;
            }
            BaseTower tower = _selected;
            Deselect();
            return TowerManager.Instance.Sell(tower);
        }

        // ------------------------------------------------------------------
        // 每帧：跟随鼠标 + 校验 + 高亮
        // ------------------------------------------------------------------

        private void Update()
        {
            if (_active)
            {
                UpdatePlacement();
                return;
            }

            // 非放置态：右键 / ESC 取消选中。
            //
            // 【ESC 的分层语义】优先级是"放置态 > 选中态"，靠上面的 _active 提前 return 实现：
            //   · 放置中按 ESC → ExitPlacement（取消放置，塔还没落地，无损失）
            //   · 非放置态按 ESC → Deselect（面板随之关闭，因为它订阅的是 TowerDeselectedEvent）
            // 两层不会同时生效，也不会互相遗漏。
            if (Input.GetMouseButtonDown(1) || Input.GetKeyDown(KeyCode.Escape))
            {
                Deselect();
                return;
            }
            if (Input.GetMouseButtonDown(0))
            {
                HandleSelectClick();
            }
        }

        private void UpdatePlacement()
        {
            // 右键 / ESC：取消放置
            if (Input.GetMouseButtonDown(1))
            {
                ExitPlacement(false);
                return;
            }
            if (_ghost == null)
            {
                return;
            }

            if (Input.GetKeyDown(KeyCode.Escape))
            {
                ExitPlacement(false);
                return;
            }

            BoardView board = BoardView.Instance;
            if (board == null)
            {
                return;
            }

            int row, col;
            bool inside = board.ScreenToCell(Input.mousePosition, out row, out col);

            if (inside)
            {
                // 悬停格变化时才重新校验（A* 探测不每帧做）
                if (row != _hoverRow || col != _hoverCol)
                {
                    ClearHover();
                    _hoverRow = row;
                    _hoverCol = col;
                    EvaluateCell(board, row, col);
                    _hoverState = _canBuild ? CellHighlight.Buildable : CellHighlight.Blocked;
                    board.SetHighlight(row, col, _hoverState);
                }
                _ghost.transform.position = board.CellCenter3(row, col);
                // 射程圈跟着悬停格走：放置前就能看清这座塔能覆盖到哪几格
                ShowRange(board.CellCenter(row, col), _cfg != null ? _cfg.RadiusWorld : 0f);
            }
            else
            {
                ClearHover();
                HideRange();   // 棋盘外不显示射程，避免圈飘在空地上误导
                // 棋盘外：跟随鼠标自由移动，方便玩家看清塔的样子
                Vector3 world = ScreenToWorld(Input.mousePosition);
                _ghost.transform.position = new Vector3(world.x, world.y, 0f);
            }

            // 拖拽建造（2026-10-14）：按住期间只做"跟手 + 悬停高亮"（上面已共用完成），
            // 落子/取消只在松手瞬间判定 —— 见 UpdateDragPlacement。
            if (_dragMode)
            {
                UpdateDragPlacement(board);
                return;
            }

            // 点击放置（避开 UI，否则点 HUD 按钮也会顺手把塔放下去）。
            //
            // 【交互 v2 —— 双手势兼容】
            //   ① 按下即放（原行为，鼠标/点按用户：点哪放哪）；
            //   ② 松手兜底（触摸拖动用户：按住拖到目标格松手落子）。
            //   TryPlace 成功会 ExitPlacement 退出放置态 → 同一手势的 up 不会再触发，天然防重。
            //   【真机诊断埋点】"不能建造"时按这几个日志定位断点：
            //     down/up/inside/canBuild/overUi 全打出来，哪一环断了一眼可见。
            if (Input.GetMouseButtonDown(0))
            {
                bool overUiDown = IsPointerOverUI();
                bool insideDown = board.ScreenToCell(Input.mousePosition, out int rDown, out int cDown);
                Debug.Log(string.Format("[Place] down overUi={0} inside={1} canBuild={2}", overUiDown, insideDown, _canBuild));
                if (overUiDown)
                {
                    return;
                }
                if (!insideDown)
                {
                    // 棋盘外按下：只提示，不取消（防误触；取消走右键/ESC/再点一次塔按钮）
                    Tips("Tap on a buildable tile to place");
                    return;
                }
                if (_canBuild)
                {
                    TryPlace(board, rDown, cDown);
                }
                else
                {
                    // 【点已建塔=转选中】放置态下点到"已有塔的格子"时，玩家的意图几乎必然
                    // 是"操作这座塔"（升级/出售），而不是"在原地再建一座"（也不可能）。
                    // 旧行为只弹一条"该位置已有防御塔"并留在放置态 —— 点击被放置分支吞掉，
                    // 选中/升级面板永远打不开，玩家体验就是"点塔没反应"。
                    // 现在：退出放置态并把这座塔选中，升级面板随 TowerSelectedEvent 打开。
                    CellData hitCell = board.GetCell(rDown, cDown);
                    if (hitCell != null && hitCell.Tower != null)
                    {
                        BaseTower hitTower = hitCell.Tower;
                        Debug.Log(string.Format("[Place] 放置态点击已建塔 ({0},{1}) → 退出放置并选中 {2}",
                            rDown, cDown, hitTower.name));
                        ExitPlacement(false);
                        Select(hitTower);
                    }
                    else
                    {
                        GameAudio.Play(SoundCue.TowerBuildFail);
                        Tips(BlockReasonText());
                    }
                }
                return;
            }

            if (Input.GetMouseButtonUp(0))
            {
                bool insideUp = board.ScreenToCell(Input.mousePosition, out int rUp, out int cUp);
                bool overUiUp = IsPointerOverUI();
                Debug.Log(string.Format("[Place] up overUi={0} inside={1} canBuild={2}", overUiUp, insideUp, _canBuild));
                if (overUiUp)
                {
                    return;
                }
                // 拖动兜底：down 时按偏了（没放出去），拖到可建格松手 → 放
                if (insideUp && _canBuild)
                {
                    TryPlace(board, rUp, cUp);
                }
            }
        }

        /// <summary>
        /// 拖拽建造的"松手判定"（2026-10-14，需求：松开时执行放置前合法性检测）。
        ///
        /// 【四条出路，语义对标《坚守阵地》】
        ///   ① 松在可建格上 → TryPlace（成功扣钱、失败给原因，见 TryPlace/TowerManager）；
        ///   ② 松在不可建格上 → Tips 具体原因（格子有塔/不可建/金币不足/会堵死路径…）并取消；
        ///   ③ 松在已有塔的格子上 → 提示"该位置已有防御塔"并取消 ——
        ///      拖拽语义是"放下"，与经典模式"点已建塔转选中"不同（那个分支在 down 才有意义）；
        ///   ④ 松在 UI 上（拖回建造栏）或棋盘外 → 静默取消 —— 玩家意图就是"不建了"，
        ///      对标原作"拖回原处收回"，此时再弹提示反而像报错。
        /// </summary>
        private void UpdateDragPlacement(BoardView board)
        {
            if (!Input.GetMouseButtonUp(0))
            {
                return;   // 还按着：跟手/高亮已由共用逻辑处理完
            }

            bool overUiUp = IsPointerOverUI();
            bool insideUp = board.ScreenToCell(Input.mousePosition, out int rUp, out int cUp);
            Debug.Log(string.Format("[Place] drag up overUi={0} inside={1} canBuild={2}", overUiUp, insideUp, _canBuild));

            if (overUiUp)
            {
                ExitPlacement(false);
                return;
            }
            if (!insideUp)
            {
                ExitPlacement(false);
                return;
            }
            if (_canBuild)
            {
                TryPlace(board, rUp, cUp);   // 成功 → 内部 ExitPlacement(true)
                return;
            }

            GameAudio.Play(SoundCue.TowerBuildFail);
            // 松手在不可建格：给出具体原因并取消（需求：不通过则取消放置并给出提示）
            CellData hitCell = board.GetCell(rUp, cUp);
            if (hitCell != null && hitCell.Tower != null)
            {
                Tips(Localization.Get("Tower already there") ?? "该位置已有防御塔");
            }
            else
            {
                Tips(BlockReasonText());
            }
            ExitPlacement(false);
        }

        /// <summary>校验某个格子能否建塔。只做廉价判断 + 一次 A* 推演（推演结果同时用作预览）。</summary>
        private void EvaluateCell(BoardView board, int row, int col)
        {
            _canBuild = false;
            _blockArg = null;
            CellData cell = board.GetCell(row, col);

            if (cell == null)
            {
                _blockReason = "Cannot Build Here";
                ClearPreview();
                return;
            }
            if (!cell.IsBuildable)
            {
                _blockReason = "Not Buildable Here";
                ClearPreview();
                return;
            }
            if (cell.HasTower)
            {
                _blockReason = "Tower already there";
                ClearPreview();
                return;
            }
            // 【2026-10-22】原先这里还有一条"该格上正有怪物 → 不可建造"。
            // 需求改为：只要不堵死路径就允许建，怪物压在脚下由落地后的定点改道解决
            // （见 TowerManager.TryBuildInternal → CombatSystem.RerouteEnemiesThrough）。
            if (!PlayerDataManager.Instance.TryPeek(_cfg.Prices))
            {
                // 带参数的 key：语序可随语言调整
                _blockReason = "Not enough gold, need {0}";
                _blockArg = _cfg.Prices;
                ClearPreview();
                return;
            }
            if (!PreviewPathThrough(row, col))
            {
                _blockReason = "Cannot fully block the path";
                return;   // 预览已在 PreviewPathThrough 内部清掉
            }
            _canBuild = true;
            _blockReason = string.Empty;
        }

        /// <summary>
        /// 推演"在这格建塔后怪物会怎么走"，并把结果挂成**预览路径**。
        /// 返回 false = 这格会把路彻底堵死（预览同时被清空）。
        ///
        /// 【预览为什么不作用于怪物】推演只写 AStarManager.PreviewPathWorld，不写 CurrentPathWorld、
        /// 不发 RefreshPathEvent；怪物与"已生效路径"完全读不到它。落地后 TryBuild 才真正置墙重算。
        /// 【预览为什么一定等于实际】落地做的是同一件事（该格 IsWall 置真后跑一次 A*），
        /// 同一个网格、同一套搜索、同一对起终点 —— 两边不会算出不同的路。
        /// </summary>
        private static bool PreviewPathThrough(int row, int col)
        {
            AStarManager astar = AStarManager.Instance;
            if (astar == null || !astar.IsGridReady)
            {
                // 没有寻路数据时不做堵路判定：悬停高亮不该因为 A* 未就绪就整片变红。
                // 注意落地仍会拦 —— TowerManager.TryBuildInternal 里 `IsFindPath()` 在 Map==null 时返回 false，
                // 会以"不能完全阻断怪物路径"拒绝。这是"棋盘/配置异常"下的降级，不是正常路径。
                return true;
            }
            Vector3[] preview = astar.ComputePathWithExtraWall(row, col);
            if (preview == null)
            {
                astar.ClearPreviewPath();
                return false;
            }
            astar.ShowPreviewPath(preview);
            return true;
        }

        /// <summary>清掉预览路径（幂等：没有预览时是空操作，不会白广播事件）。</summary>
        private static void ClearPreview()
        {
            if (AStarManager.Instance != null)
            {
                AStarManager.Instance.ClearPreviewPath();
            }
        }

        private void TryPlace(BoardView board, int row, int col)
        {
            BaseTower tower = TowerManager.Instance.TryBuild(_type, _level, row, col);
            if (tower == null)
            {
                GameAudio.Play(SoundCue.TowerBuildFail);
                // TryBuild 内部已通过 ShowTipEvent 给出具体原因
                ClearHover();
                return;
            }

            // 建成功后退出放置模式（HudView 收到 BuildTowerSuccess 会复位按钮）
            ExitPlacement(true);
        }

        private void ClearHover()
        {
            if (_hoverRow >= 0 && _hoverCol >= 0 && BoardView.Instance != null)
            {
                BoardView.Instance.ResetHighlight(_hoverRow, _hoverCol);
            }
            _hoverRow = -1;
            _hoverCol = -1;
            _hoverState = CellHighlight.None;
            // 悬停格没了，针对那一格的预览路径也必须一起消失
            // （否则箭头会指向一个玩家已经不在看的格子，滑出棋盘后尤其明显）
            ClearPreview();
        }

        // ------------------------------------------------------------------
        // 工具
        // ------------------------------------------------------------------

        private static Vector3 ScreenToWorld(Vector2 screenPos)
        {
            Camera cam = Camera.main;
            if (cam == null)
            {
                return Vector3.zero;
            }
            return cam.ScreenToWorldPoint(new Vector3(screenPos.x, screenPos.y, -cam.transform.position.z));
        }

        /// <summary>
        /// 指针是否悬在 UI 上。
        /// 【2026-10-14 升级：触摸感知】原版只查 IsPointerOverGameObject()（无参 = 鼠标指针 -1），
        /// 真机触摸的 pointerId ≥ 0，会恒返回 false —— 经典模式下"点 HUD 按钮顺手落塔"、
        /// 拖拽模式下"松手误判成棋盘内"都可能出现。现在：有任何活动触摸时逐一查
        /// IsPointerOverGameObject(fingerId)，两者任一命中即算 overUi。
        /// 编辑器（鼠标）行为不变。
        /// </summary>
        private static bool IsPointerOverUI()
        {
            EventSystem es = EventSystem.current;
            if (es == null)
            {
                return false;
            }
            if (Input.touchCount > 0)
            {
                for (int i = 0; i < Input.touchCount; i++)
                {
                    if (es.IsPointerOverGameObject(Input.GetTouch(i).fingerId))
                    {
                        return true;
                    }
                }
            }
            return es.IsPointerOverGameObject();
        }

        private static void Tips(string msg)
        {
            EventDispatcher.TriggerEvent<string>(EventName.ShowTipEvent, msg);
        }

        /// <summary>
        /// 把 _blockReason（key）解析成当前语言的文案。
        /// 【为什么把 key 存在字段里】_blockReason 在 EvaluateCell 每帧被重算，
        ///   用"存 key + 显示时查表"只需一处映射；若直接存译文，切换语言后残留的
        ///   旧译文会一直挂在字段上（直到下一次 EvaluateCell 才刷新）。
        /// </summary>
        private string BlockReasonText()
        {
            if (string.IsNullOrEmpty(_blockReason))
            {
                return string.Empty;
            }
            string text = _blockArg.HasValue
                ? Localization.Get(_blockReason, _blockArg.Value)
                : Localization.Get(_blockReason);
            return text ?? FallbackBlockReason(_blockReason);
        }

        /// <summary>表里缺 key 时的中文兜底（保证"零破坏"）。</summary>
        private static string FallbackBlockReason(string key)
        {
            switch (key)
            {
                case "Cannot Build Here": return "超出棋盘范围";
                case "Not Buildable Here": return "该位置不可建造";
                case "Tower already there": return "该位置已有防御塔";
                case "Not enough gold, need {0}": return "金币不足（需要 {0}）";
                case "Cannot fully block the path": return "不能完全阻断怪物路径";
                default: return "无法建造";
            }
        }
    }
}
