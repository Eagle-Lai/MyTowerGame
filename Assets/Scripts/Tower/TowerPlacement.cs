using System.Collections.Generic;
using AStar;
using UnityEngine;
using UnityEngine.EventSystems;

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
    ///   前 4 项是廉价判断，A* 探测只在"悬停格变化"时做一次（16×9 网格下开销可忽略）。
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
        private GameObject _ghost;
        private readonly List<SpriteRenderer> _ghostRenderers = new List<SpriteRenderer>(8);

        private int _hoverRow = -1;
        private int _hoverCol = -1;
        private CellHighlight _hoverState = CellHighlight.None;
        private bool _canBuild;
        private string _blockReason = "无法建造";

        /// <summary>当前选中的已建造塔（M2-B1）。未选中为 null。</summary>
        private BaseTower _selected;

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
        }

        private void OnDisable()
        {
            EventDispatcher.RemoveEventListener<int, int>(EventName.BuildTowerRequestEvent, OnBuildRequest);
            EventDispatcher.RemoveEventListener(EventName.CancelBuildRequestEvent, OnCancelRequest);
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
            EnterPlacement(type, level);
        }

        private void OnCancelRequest()
        {
            ExitPlacement(false);
        }

        public void EnterPlacement(int type, int level)
        {
            TowerConfig cfg = Configs.GetTowerByTypeAndLevel(type, level);
            if (cfg == null)
            {
                Tips(string.Format("找不到 type={0} level={1} 的塔配置", type, level));
                return;
            }
            if (!PlayerDataManager.Instance.TryPeek(cfg.Prices))
            {
                Tips(string.Format("金币不足，需要 {0}", cfg.Prices));
                return;
            }

            _type = type;
            _level = level;
            _cfg = cfg;
            _active = true;
            _hoverRow = -1;
            _hoverCol = -1;
            _hoverState = CellHighlight.None;

            // 进入放置态时先取消已选中的塔（否则面板不会自动关，两个状态并存会互相干扰）
            Deselect();

            CreateGhost(cfg);
            EventDispatcher.TriggerEvent(EventName.BuildingTower);
            Tips(string.Format("{0}：移动到可建造格上点击放置，右键/ESC 取消", cfg.Name));
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
        /// </summary>
        private void HandleSelectClick()
        {
            // 点在 UI 上不要触发（否则点 HUD 面板会顺手选中/取消塔）
            if (IsPointerOverUI())
            {
                return;
            }

            BoardView board = BoardView.Instance;
            if (board == null)
            {
                return;
            }
            int row, col;
            if (!board.ScreenToCell(Input.mousePosition, out row, out col))
            {
                // 点到棋盘外 → 视为取消选中
                Deselect();
                return;
            }
            CellData cell = board.GetCell(row, col);
            if (cell == null || cell.Tower == null)
            {
                Deselect();
                return;
            }
            Select(cell.Tower);
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
            ApplySelectionHighlight(_selected);
            EventDispatcher.TriggerEvent<BaseTower>(EventName.TowerSelectedEvent, _selected);
        }

        /// <summary>取消选中：广播事件（UI 据此关闭面板）。</summary>
        public void Deselect()
        {
            if (_selected == null)
            {
                return;
            }
            ClearSelectionHighlight(_selected);
            _selected = null;
            EventDispatcher.TriggerEvent(EventName.TowerDeselectedEvent);
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
            if (tower == null)
            {
                return;
            }
            tower.SetTint(Color.white);
            ResetCellHighlight(tower.Cell);
            HideRange();
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

            // 点击放置（避开 UI，否则点 HUD 按钮也会顺手把塔放下去）
            if (Input.GetMouseButtonDown(0) && !IsPointerOverUI())
            {
                if (inside && _canBuild)
                {
                    TryPlace(board, row, col);
                }
                else if (inside)
                {
                    Tips(_blockReason);
                }
            }
        }

        /// <summary>校验某个格子能否建塔。只做廉价判断 + 一次 A* 探测。</summary>
        private void EvaluateCell(BoardView board, int row, int col)
        {
            _canBuild = false;
            CellData cell = board.GetCell(row, col);

            if (cell == null)
            {
                _blockReason = "超出棋盘范围";
                return;
            }
            if (!cell.IsBuildable)
            {
                _blockReason = "该位置不可建造";
                return;
            }
            if (cell.HasTower)
            {
                _blockReason = "该位置已有防御塔";
                return;
            }
            CombatSystem combat = CombatSystem.Instance;
            if (combat != null && combat.HasAliveEnemyNear(cell.Center, board.CellSize * 0.5f))
            {
                _blockReason = "该格上正有怪物";
                return;
            }
            if (!PlayerDataManager.Instance.TryPeek(_cfg.Prices))
            {
                _blockReason = string.Format("金币不足（需要 {0}）", _cfg.Prices);
                return;
            }
            if (WouldBlockPath(row, col))
            {
                _blockReason = "不能完全阻断怪物路径";
                return;
            }
            _canBuild = true;
            _blockReason = string.Empty;
        }

        /// <summary>
        /// 临时把该格设为墙跑一次 A*，判断是否会彻底堵死路径。
        /// 这是《坚守阵地》的核心规则：可以拖延、可以绕路，但不能 100% 封死。
        /// </summary>
        private static bool WouldBlockPath(int row, int col)
        {
            AStarManager astar = AStarManager.Instance;
            if (astar == null || !astar.IsGridReady)
            {
                return false;
            }
            Point point = astar.GetPoint(row, col);
            if (point == null)
            {
                return false;
            }
            bool old = point.IsWall;
            point.IsWall = true;
            bool reachable = astar.IsFindPath();
            point.IsWall = old;   // ★ 无论结果如何都必须还原，否则地图会被永久改坏
            return !reachable;
        }

        private void TryPlace(BoardView board, int row, int col)
        {
            BaseTower tower = TowerManager.Instance.TryBuild(_type, _level, row, col);
            if (tower == null)
            {
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

        private static bool IsPointerOverUI()
        {
            return EventSystem.current != null && EventSystem.current.IsPointerOverGameObject();
        }

        private static void Tips(string msg)
        {
            EventDispatcher.TriggerEvent<string>(EventName.ShowTipEvent, msg);
        }
    }
}
