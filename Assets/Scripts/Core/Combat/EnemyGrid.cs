using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 均匀网格空间哈希（Uniform Grid Spatial Hash）。
    ///
    /// 用途：替代 v1.0 的 `SphereCollider + OnTriggerEnter` 索敌方案。
    /// 原方案的复杂度是 O(塔数 × 敌人数) 的物理触发器对，低端机上物理宽相/窄相是主要开销。
    /// 本方案把空间查询接管过来：
    ///   - 敌人移动时更新所在格子：**未跨格则零开销**（关键优化）
    ///   - 塔索敌只查询邻域格子，复杂度 O(邻域常数)，与全场怪物总数无关
    ///
    /// cellSize 建议取值 ≈ 最大索敌半径，这样邻域在 3×3 ~ 7×7 个格子之间。
    /// </summary>
    public class EnemyGrid
    {
        private readonly Dictionary<int, List<BaseEnemy>> _cells;
        private readonly float _cellSize;
        private readonly int _cols;   // 用于把 (cx, cy) 压成一维 key

        public EnemyGrid(float cellSize, int cols)
        {
            _cellSize = Mathf.Max(0.1f, cellSize);
            _cols = Mathf.Max(1, cols);
            _cells = new Dictionary<int, List<BaseEnemy>>(256);
        }

        public float CellSize { get { return _cellSize; } }

        private int Key(int cx, int cy)
        {
            // 允许负坐标（棋盘左上为原点时 cy 可能为负）
            return (cy + 4096) * 8192 + (cx + 4096);
        }

        private void CellCoord(Vector2 pos, out int cx, out int cy)
        {
            cx = Mathf.FloorToInt(pos.x / _cellSize);
            cy = Mathf.FloorToInt(pos.y / _cellSize);
        }

        /// <summary>
        /// 同步一个敌人的位置。若未跨越格子则**直接返回**（这是本类最重要的优化）。
        /// </summary>
        public void Update(BaseEnemy e, Vector2 pos)
        {
            if (e == null)
            {
                return;
            }
            int cx, cy;
            CellCoord(pos, out cx, out cy);
            int key = Key(cx, cy);
            if (e.GridKey == key)
            {
                return;
            }
            Remove(e);
            List<BaseEnemy> list;
            if (!_cells.TryGetValue(key, out list))
            {
                list = new List<BaseEnemy>(8);
                _cells[key] = list;
            }
            list.Add(e);
            e.GridKey = key;
        }

        /// <summary>把敌人从它所在格子移除（回收/死亡时调用）</summary>
        public void Remove(BaseEnemy e)
        {
            if (e == null || e.GridKey == 0)
            {
                return;
            }
            List<BaseEnemy> list;
            if (_cells.TryGetValue(e.GridKey, out list))
            {
                list.Remove(e);
                if (list.Count == 0)
                {
                    _cells.Remove(e.GridKey);
                }
            }
            e.GridKey = 0;
        }

        /// <summary>
        /// 查询圆形范围覆盖到的所有格子，把候选敌人追加进 result。
        /// 注意：返回的是**候选集**（含少量范围外的元素），调用方必须再用精确距离过滤。
        /// </summary>
        public void QueryCircle(Vector2 center, float radius, List<BaseEnemy> result)
        {
            if (result == null)
            {
                return;
            }
            int minX = Mathf.FloorToInt((center.x - radius) / _cellSize);
            int maxX = Mathf.FloorToInt((center.x + radius) / _cellSize);
            int minY = Mathf.FloorToInt((center.y - radius) / _cellSize);
            int maxY = Mathf.FloorToInt((center.y + radius) / _cellSize);

            for (int cy = minY; cy <= maxY; cy++)
            {
                for (int cx = minX; cx <= maxX; cx++)
                {
                    List<BaseEnemy> list;
                    if (_cells.TryGetValue(Key(cx, cy), out list))
                    {
                        result.AddRange(list);
                    }
                }
            }
        }

        /// <summary>清理已失效（回收/销毁）的引用，返回清理掉的数量</summary>
        public int CleanupInvalid()
        {
            int removed = 0;
            List<int> emptyKeys = null;
            foreach (KeyValuePair<int, List<BaseEnemy>> kv in _cells)
            {
                List<BaseEnemy> list = kv.Value;
                for (int i = list.Count - 1; i >= 0; i--)
                {
                    BaseEnemy e = list[i];
                    if (e == null || !e.IsAlive)
                    {
                        list.RemoveAt(i);
                        if (e != null)
                        {
                            e.GridKey = 0;
                        }
                        removed++;
                    }
                }
                if (list.Count == 0)
                {
                    if (emptyKeys == null)
                    {
                        emptyKeys = new List<int>();
                    }
                    emptyKeys.Add(kv.Key);
                }
            }
            if (emptyKeys != null)
            {
                for (int i = 0; i < emptyKeys.Count; i++)
                {
                    _cells.Remove(emptyKeys[i]);
                }
            }
            return removed;
        }

        public void Clear()
        {
            _cells.Clear();
        }

        /// <summary>占用格子数（诊断用）</summary>
        public int UsedCellCount { get { return _cells.Count; } }

        public string DumpDebugInfo()
        {
            int total = 0;
            foreach (KeyValuePair<int, List<BaseEnemy>> kv in _cells)
            {
                total += kv.Value.Count;
            }
            return string.Format("EnemyGrid: cells={0}, enemies={1}, cellSize={2}",
                _cells.Count, total, _cellSize);
        }
    }
}
