using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 格子类型（对应 TBLevelMap 的字符）
    /// </summary>
    public enum CellType
    {
        /// <summary>'.' 可建造地砖（可通行）</summary>
        Ground = 0,
        /// <summary>'S' 起点</summary>
        Spawn = 1,
        /// <summary>'E' 终点</summary>
        End = 2,
        /// <summary>'#' 障碍（不可通行、不可建造）</summary>
        Obstacle = 3,
        /// <summary>'X' 空洞（不可通行、不可建造）</summary>
        Hole = 4,
        /// <summary>'P' 装饰地砖（可通行、不可建造）</summary>
        Decor = 5,
    }

    /// <summary>格子高亮状态</summary>
    public enum CellHighlight
    {
        None = 0,
        /// <summary>可建造（绿）</summary>
        Buildable = 1,
        /// <summary>不可建造 / 会堵死路径（红）</summary>
        Blocked = 2,
    }

    /// <summary>
    /// 棋盘几何计算（**唯一坐标换算入口**）。
    ///
    /// 约定（贯穿全局，务必统一）：
    ///   - 棋盘以左上角为原点，x 向右为正，y 向下为负（2D 习惯）
    ///   - 格子边长 CellSize（世界单位），由 TBGlobal.cellSize 配置，默认 1.0（与 PPU=100 对齐）
    ///   - 任意模块都不得自行换算坐标，一律调用本类
    /// </summary>
    public static class BoardGeometry
    {
        /// <summary>格子中心的局部坐标（相对棋盘原点）</summary>
        public static Vector2 CellCenterLocal(int row, int col, float cellSize)
        {
            return new Vector2((col + 0.5f) * cellSize, -(row + 0.5f) * cellSize);
        }

        /// <summary>格子中心的世界坐标</summary>
        public static Vector2 CellCenter(int row, int col, float cellSize, Vector2 origin)
        {
            return origin + CellCenterLocal(row, col, cellSize);
        }

        /// <summary>格子中心的世界坐标（Vector3 版，便于直接赋 transform.position）</summary>
        public static Vector3 CellCenter3(int row, int col, float cellSize, Vector2 origin)
        {
            Vector2 v = CellCenter(row, col, cellSize, origin);
            return new Vector3(v.x, v.y, 0f);
        }

        /// <summary>世界坐标 → 格子索引（纯数学除法，不依赖物理）</summary>
        public static bool WorldToCell(Vector2 world, float cellSize, Vector2 origin,
            int rows, int cols, out int row, out int col)
        {
            Vector2 local = world - origin;
            col = Mathf.FloorToInt(local.x / cellSize);
            row = Mathf.FloorToInt(-local.y / cellSize);
            return row >= 0 && row < rows && col >= 0 && col < cols;
        }

        /// <summary>棋盘整体尺寸（宽, 高）</summary>
        public static Vector2 BoardSize(int rows, int cols, float cellSize)
        {
            return new Vector2(cols * cellSize, rows * cellSize);
        }

        /// <summary>棋盘几何中心的世界坐标（相机对准这里）</summary>
        public static Vector2 BoardCenter(int rows, int cols, float cellSize, Vector2 origin)
        {
            Vector2 half = BoardSize(rows, cols, cellSize) * 0.5f;
            return new Vector2(origin.x + half.x, origin.y - half.y);
        }

        /// <summary>TBLevelMap 字符 → 格子类型</summary>
        public static CellType ParseCell(char c)
        {
            switch (c)
            {
                case 'S': return CellType.Spawn;
                case 'E': return CellType.End;
                case '#': return CellType.Obstacle;
                case 'X': return CellType.Hole;
                case 'P': return CellType.Decor;
                default: return CellType.Ground;   // '.' 及未知字符都当可建造地砖
            }
        }

        /// <summary>怪物能否通行</summary>
        public static bool IsWalkable(CellType t)
        {
            return t != CellType.Obstacle && t != CellType.Hole;
        }

        /// <summary>玩家能否在此建塔</summary>
        public static bool IsBuildable(CellType t)
        {
            return t == CellType.Ground;
        }

        /// <summary>该格子类型对应的占位美术逻辑名（ResTable 中的 key）</summary>
        public static string GetCellSpriteKey(CellType t)
        {
            switch (t)
            {
                case CellType.Spawn: return "Cell_Spawn";
                case CellType.End: return "Cell_End";
                case CellType.Obstacle: return "Cell_Blocked";
                case CellType.Hole: return "Cell_Blocked";
                case CellType.Decor: return "Cell_Blocked";
                default: return "Cell_Ground";
            }
        }
    }

    /// <summary>
    /// 单个格子的**纯数据**。不持有 GameObject 引用（这是 v1.0 的核心缺陷：
    /// 原 Point 直接持有 transform/gameObject，导致数据与视图强耦合、无法单元测试）。
    /// </summary>
    public class CellData
    {
        public int Row;
        public int Col;
        public CellType Type;
        /// <summary>格子中心世界坐标（由 BoardView 在 Build 时写入）</summary>
        public Vector2 Center;
        /// <summary>对应的寻路节点</summary>
        public AStar.Point Point;
        /// <summary>该格上已建造的塔（业务查询用）</summary>
        public BaseTower Tower;

        public bool IsWalkable { get { return BoardGeometry.IsWalkable(Type); } }
        public bool IsBuildable { get { return BoardGeometry.IsBuildable(Type); } }
        public bool HasTower { get { return Tower != null; } }

        public override string ToString()
        {
            return string.Format("Cell({0},{1}) {2}", Row, Col, Type);
        }
    }

    /// <summary>
    /// 渲染层级约定（统一在此声明，避免各改各的）。
    /// 注意：完全不使用 UGUI 承载玩法对象，全部为世界空间 SpriteRenderer。
    ///
    /// 配合 Graphics Settings 的 Transparency Sort Mode = Custom Axis (0,-1,0)，
    /// 同层内会按 Y 从大到小绘制，从而实现"靠下的物体盖住靠上的"。
    /// </summary>
    public static class BoardSorting
    {
        /// <summary>背景（在格子之下）</summary>
        public const int Background = -100;
        public const int Cell = 0;
        public const int PathArrow = 10;
        /// <summary>射程提示圈（在格子之上、怪物之下，避免挡住塔与怪）</summary>
        public const int RangeIndicator = 100;
        public const int Enemy = 200;      // 与怪物素材包 SortingGroup 默认值一致
        public const int Tower = 300;      // 塔默认盖住怪
        public const int Bullet = 400;
        public const int Overlay = 500;    // 血条 / 伤害数字
    }
}
