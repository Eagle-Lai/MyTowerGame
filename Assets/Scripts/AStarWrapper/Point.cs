
using UnityEngine;

namespace AStar
{
    /// <summary>
    /// A* 寻路节点（v2.1 的 2D 版）。
    ///
    /// 相对 v1.0 的改动：
    ///   - **移除** GameObject / Transform 强引用（数据与视图解耦，便于单元测试）
    ///   - position(Vector3) → Center(Vector2)，坐标体系改为 2D 世界坐标
    ///   - 保留 X / Y 字段名：AStarWrapper 依赖它们，X 为行、Y 为列
    ///
    /// 注意：AStarWrapper 只用到 F / G / H / Parent / UpdateParent / X / Y / IsWall，
    /// 不涉及任何 Unity 对象引用。
    /// </summary>
    [System.Serializable]
    public class Point
    {
        /// <summary>父节点（回溯路径用）</summary>
        public Point Parent { get; set; }

        public float F { get; set; }
        public float G { get; set; }
        public float H { get; set; }

        /// <summary>
        /// 横轴坐标 —— **列索引 col**。
        ///
        /// 【为什么 X 是列】AStarWrapper 插件把 X 当横轴（用 mapWidth 判断边界）、
        /// Y 当纵轴（用 mapHeight 判断边界），并直接以 `map[X, Y]` 访问网格。
        /// 所以数组必须声明为 `new Point[cols, rows]`。
        /// 这套命名沿用了原插件的字段名，改名的代价大于保留（插件是第三方代码，不宜改）。
        /// </summary>
        public int X { get; set; }

        /// <summary>纵轴坐标 —— **行索引 row**。详见 X 的说明。</summary>
        public int Y { get; set; }

        /// <summary>是否为墙（障碍格 或 被塔占用）</summary>
        public bool IsWall;

        /// <summary>格子中心的世界坐标（2D），由 AStarManager.BuildGrid 写入</summary>
        public Vector2 Center;

        /// <summary>行索引（本项目代码一律用 Row/Col，避免 X/Y 的轴歧义）</summary>
        public int Row { get { return Y; } }

        /// <summary>列索引</summary>
        public int Col { get { return X; } }

        public Point(int x, int y, Point parent = null)
        {
            X = x;
            Y = y;
            Parent = parent;
            IsWall = false;
        }

        /// <summary>更新 G / F 值与父节点</summary>
        public void UpdateParent(Point parent, float g)
        {
            Parent = parent;
            G = g;
            F = G + H;
        }

        /// <summary>重置寻路状态（重用节点时调用，避免上次的 G/H/Parent 残留）</summary>
        public void ResetSearchState()
        {
            Parent = null;
            F = 0f;
            G = 0f;
            H = 0f;
        }

        public override string ToString()
        {
            return string.Format("Point(row={0}, col={1}, wall={2})", Row, Col, IsWall);
        }
    }
}
