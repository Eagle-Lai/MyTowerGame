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

        public bool IsPlacing { get { return _active; } }

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

            CreateGhost(cfg);
            EventDispatcher.TriggerEvent(EventName.BuildingTower);
            Tips(string.Format("{0}：移动到可建造格上点击放置，右键/ESC 取消", cfg.Name));
        }

        private void ExitPlacement(bool built)
        {
            if (!_active)
            {
                return;
            }
            _active = false;
            ClearHover();
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
                ResLoader.Instance.ReleaseInstance(_cfg != null ? _cfg.ResName : "Tower_Normal", _ghost);
                _ghost = null;
            }
        }

        // ------------------------------------------------------------------
        // 售卖（右键直接卖，M0 简化交互）
        // ------------------------------------------------------------------

        /// <summary>
        /// 售卖鼠标下的防御塔。
        /// 返还金币、清理格子占用、通知路径重算都由 TowerManager.Sell 负责，
        /// 这里只做"定位到哪座塔"。
        /// </summary>
        private void TrySellUnderCursor()
        {
            // 点在 UI 上时不要触发（否则点 HUD 按钮会顺手卖掉塔）
            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject())
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
                return;
            }
            CellData cell = board.GetCell(row, col);
            if (cell == null || cell.Tower == null)
            {
                return;
            }

            TowerManager.Instance.Sell(cell.Tower);
        }

        // ------------------------------------------------------------------
        // 每帧：跟随鼠标 + 校验 + 高亮
        // ------------------------------------------------------------------

        private void Update()
        {
            // 右键：放置中 → 取消放置；未放置 → 直接售卖鼠标下的防御塔
            // （M0 的简化售卖交互。后续要做"选中塔 → 弹菜单 → 确认"时，
            //   把 TrySellUnderCursor 换掉即可，其它逻辑不受影响）
            if (Input.GetMouseButtonDown(1))
            {
                if (_active)
                {
                    ExitPlacement(false);
                }
                else
                {
                    TrySellUnderCursor();
                }
                return;
            }

            if (!_active)
            {
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
            }
            else
            {
                ClearHover();
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
