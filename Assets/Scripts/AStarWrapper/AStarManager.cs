using System.Collections.Generic;
using AStar;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// A* 寻路管理器（v2.1 的 2D 版）。
    ///
    /// 相对 v1.0 的改动：
    ///   - **只建数据**：不再生成任何 GameObject / LineRenderer（格子由 BoardView 生成）
    ///   - 地图来源从 `StreamingAssets/Map/Map*.txt` 改为 **TBLevelMap 配置表**
    ///   - 新增路径重算节流（RequestRefresh / ProcessRefresh），避免布塔时集中重算卡顿
    ///   - 每次搜索前重置节点的 G/H/Parent —— v1.0 未重置，复用网格时会被上次结果污染
    ///   - GetAStarPath 增加**迭代上限**，杜绝 Parent 链断裂导致的死循环
    ///
    /// 坐标：(row, col) → 世界坐标由 BoardGeometry 统一换算，Center 缓存在 Point 上。
    /// </summary>
    public class AStarManager : BaseManager<AStarManager>
    {
        /// <summary>网格宽度（= 列数 cols，即 X 方向的长度）</summary>
        public int MapWidth { get; private set; }

        /// <summary>网格高度（= 行数 rows，即 Y 方向的长度）</summary>
        public int MapHeight { get; private set; }

        /// <summary>
        /// 网格。
        /// 【索引约定】**`map[col, row]`**，即第一维是列、第二维是行。
        ///
        /// 这个约定不是随意定的，而是**必须服从 AStarWrapper 插件**：
        /// 它内部用 `Point.X` 表示横轴（用 `mapWidth` 做边界判断）、
        /// `Point.Y` 表示纵轴（用 `mapHeight` 做边界判断），并直接 `map[point.X, point.Y]`。
        /// 也就是说 **X = 列、Y = 行**。
        ///
        /// 【踩过的坑】最初写成 `new Point[rows, cols]` 且 `Point(row, col)`（X=行、Y=列），
        /// 两个轴的语义同时反了。后果是插件的边界判断 `point.X &lt; mapWidth - 1`
        /// 实际变成 `row &lt; 15`（恒真），于是 `map[row + 1, col]` 在最后一行越界，
        /// 抛出 IndexOutOfRangeException —— 而该异常又会被事件系统的 try/catch 吞掉，
        /// 表现为"地图生成了、但既没有路径、也没有 HUD、也没有怪物"。
        /// </summary>
        public Point[,] Map { get; private set; }

        public Point StartPoint { get; private set; }
        public Point TargetPoint { get; private set; }

        public bool IsGridReady { get { return Map != null; } }

        /// <summary>当前最短路径的世界坐标（含首尾），供路径箭头渲染</summary>
        public Vector3[] CurrentPathWorld { get; private set; }

        private bool _refreshRequested;
        private int _lastPathHash = -1;
        private readonly List<Point> _pathBuffer = new List<Point>(512);

        public override void OnInit()
        {
            base.OnInit();
        }

        public override void OnDestroy()
        {
            base.OnDestroy();
            Map = null;
            StartPoint = null;
            TargetPoint = null;
            CurrentPathWorld = null;
        }

        // ------------------------------------------------------------------
        // 网格构建
        // ------------------------------------------------------------------

        /// <summary>
        /// 按配置构建寻路网格（只建数据，不生成任何物件）。
        /// </summary>
        public void BuildGrid(LevelMapConfig map, float cellSize, Vector2 origin)
        {
            if (map == null)
            {
                Debug.LogError("[AStar] BuildGrid 收到 null 配置，寻路不可用");
                return;
            }

            MapWidth = map.Cols;      // X 方向 = 列数
            MapHeight = map.Rows;     // Y 方向 = 行数
            // 第一维是列、第二维是行（必须与 AStarWrapper 的 map[point.X, point.Y] 一致）
            Map = new Point[MapWidth, MapHeight];
            StartPoint = null;
            TargetPoint = null;

            for (int r = 0; r < MapHeight; r++)
            {
                for (int c = 0; c < MapWidth; c++)
                {
                    char ch = map.GetCell(r, c);
                    CellType type = BoardGeometry.ParseCell(ch);

                    // Point(X=列, Y=行)
                    Point p = new Point(c, r);
                    p.IsWall = !BoardGeometry.IsWalkable(type);
                    p.Center = BoardGeometry.CellCenter(r, c, cellSize, origin);
                    Map[c, r] = p;

                    if (type == CellType.Spawn)
                    {
                        StartPoint = p;
                    }
                    else if (type == CellType.End)
                    {
                        TargetPoint = p;
                    }
                }
            }

            // 自检：数组维度必须与插件使用的 mapWidth/mapHeight 匹配，
            // 否则边界判断会失效并导致越界（这正是之前的故障原因）
            if (Map.GetLength(0) != MapWidth || Map.GetLength(1) != MapHeight)
            {
                Debug.LogError(string.Format(
                    "[AStar] 网格维度与声明不一致：数组 [{0},{1}] vs mapWidth={2} mapHeight={3}",
                    Map.GetLength(0), Map.GetLength(1), MapWidth, MapHeight));
            }

            if (StartPoint == null || TargetPoint == null)
            {
                Debug.LogError("[AStar] 网格缺少起点(S)或终点(E)，无法寻路");
            }

            _lastPathHash = -1;
            RecomputePath(force: true);
        }

        /// <summary>把某格设为/取消占位（建塔时临时校验用）</summary>
        public void SetWall(int row, int col, bool isWall)
        {
            Point p = GetPoint(row, col);
            if (p != null)
            {
                p.IsWall = isWall;
            }
        }

        public Point GetPoint(int row, int col)
        {
            if (Map == null || row < 0 || row >= MapHeight || col < 0 || col >= MapWidth)
            {
                return null;
            }
            return Map[col, row];   // 第一维是列
        }

        public Point GetEndPoint()
        {
            return TargetPoint;
        }

        // ------------------------------------------------------------------
        // 寻路
        // ------------------------------------------------------------------

        /// <summary>起点到终点是否连通（建塔校验用）</summary>
        public bool IsFindPath()
        {
            return IsFindPath(StartPoint, TargetPoint);
        }

        public bool IsFindPath(Point from, Point to)
        {
            if (Map == null || from == null || to == null)
            {
                return false;
            }
            ResetAllSearchState();
            return AStarWrapper.Instance.FindPath(from, to, Map, MapWidth, MapHeight);
        }

        /// <summary>
        /// 起点 → 终点的完整路径（**含首尾**）。
        /// 注意与 v1.0 的差异：v1.0 的 GetAStarPath 不含起点，需要额外处理；此处直接给全。
        /// </summary>
        public List<Point> GetPath()
        {
            return GetAStarPath(StartPoint, TargetPoint);
        }

        /// <summary>从某个敌人当前所在格重新寻路到终点</summary>
        public List<Point> UpdatePathByEnemyPoint(Point from)
        {
            if (from == null)
            {
                return null;
            }
            return GetAStarPath(from, TargetPoint);
        }

        /// <summary>
        /// 回溯 Parent 链得到路径（含起点与终点）。
        /// 带迭代上限，防止 Parent 链断裂时死循环。
        /// </summary>
        public List<Point> GetAStarPath(Point from, Point to)
        {
            List<Point> result = new List<Point>(256);
            if (Map == null || from == null || to == null)
            {
                return result;
            }

            ResetAllSearchState();
            if (!AStarWrapper.Instance.FindPath(from, to, Map, MapWidth, MapHeight))
            {
                return result;
            }

            // 回溯：[to, ..., from]，随后反转
            int guard = MapWidth * MapHeight + 2;
            Point cur = to;
            while (cur != null && guard-- > 0)
            {
                result.Add(cur);
                if (cur == from)
                {
                    break;
                }
                cur = cur.Parent;
            }

            if (guard <= 0)
            {
                Debug.LogError("[AStar] 路径回溯超出迭代上限，Parent 链可能已断裂");
                result.Clear();
                return result;
            }
            if (cur != from)
            {
                // Parent 链没走到起点，说明路径不完整
                result.Clear();
                return result;
            }

            result.Reverse();
            return result;
        }

        /// <summary>每次搜索前重置所有节点的寻路状态</summary>
        private void ResetAllSearchState()
        {
            if (Map == null)
            {
                return;
            }
            for (int r = 0; r < MapHeight; r++)
            {
                for (int c = 0; c < MapWidth; c++)
                {
                    Point p = Map[c, r];
                    if (p != null)
                    {
                        p.ResetSearchState();
                    }
                }
            }
        }

        // ------------------------------------------------------------------
        // 路径刷新节流
        // ------------------------------------------------------------------

        /// <summary>请求重算路径（建塔/拆塔后调用）。只置脏标记，真正重算在下一次 ProcessRefresh。</summary>
        public void RequestRefresh()
        {
            _refreshRequested = true;
        }

        /// <summary>
        /// 每帧由 CombatSystem 调用，最多重算 Configs.Global.CheckOfflinePerFrame 次。
        /// 路径发生变化时广播 RefreshPathEvent，敌人据此改道。
        /// </summary>
        public void ProcessRefresh()
        {
            if (!_refreshRequested || Map == null)
            {
                return;
            }
            _refreshRequested = false;
            RecomputePath(force: false);
        }

        private void RecomputePath(bool force)
        {
            _pathBuffer.Clear();
            List<Point> path = GetPath();

            if (path.Count == 0)
            {
                Debug.LogWarning("[AStar] 起点到终点不可达！可能是配置表里存在完全阻断，或建塔把路堵死了。");
                CurrentPathWorld = null;
                _lastPathHash = -1;
                return;
            }

            int hash = ComputePathHash(path);
            bool changed = force || hash != _lastPathHash;
            _lastPathHash = hash;

            // 缓存世界坐标供路径箭头渲染
            Vector3[] world = new Vector3[path.Count];
            for (int i = 0; i < path.Count; i++)
            {
                world[i] = new Vector3(path[i].Center.x, path[i].Center.y, 0f);
            }
            CurrentPathWorld = world;

            if (changed)
            {
                EventDispatcher.TriggerEvent(EventName.RefreshPathEvent);
            }
        }

        private static int ComputePathHash(List<Point> path)
        {
            unchecked
            {
                int h = 17;
                for (int i = 0; i < path.Count; i++)
                {
                    h = h * 31 + path[i].X * 397 + path[i].Y;
                }
                return h;
            }
        }

        /// <summary>当前路径长度（格），用于自检日志</summary>
        public int CurrentPathLength
        {
            get { return CurrentPathWorld != null ? CurrentPathWorld.Length : 0; }
        }

        /// <summary>把路径打印成 (row,col) 序列，便于排查配置</summary>
        public string DescribeCurrentPath()
        {
            if (Map == null || StartPoint == null)
            {
                return "(未建网格)";
            }
            List<Point> path = GetPath();
            if (path.Count == 0)
            {
                return "(不可达)";
            }
            System.Text.StringBuilder sb = new System.Text.StringBuilder();
            sb.Append("路径 ").Append(path.Count).Append(" 格：");
            for (int i = 0; i < path.Count; i++)
            {
                if (i > 0)
                {
                    sb.Append(" → ");
                }
                sb.Append('(').Append(path[i].Row).Append(',').Append(path[i].Col).Append(')');
            }
            return sb.ToString();
        }
    }
}
