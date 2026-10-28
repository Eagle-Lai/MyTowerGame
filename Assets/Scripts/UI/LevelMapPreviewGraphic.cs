using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>Read-only presentation of the current formal map, never conceptual key art.</summary>
    [RequireComponent(typeof(CanvasRenderer))]
    public sealed class LevelMapPreviewGraphic : MaskableGraphic
    {
        private LevelMapConfig _map;
        private readonly HashSet<int> _route = new HashSet<int>();
        public void Bind(int levelId)
        {
            Bind(Configs.GetLevelMapOfLevel(levelId));
        }
        public void Bind(LevelMapConfig map)
        {
            _map = map;
            _route.Clear();
            if (_map != null && _map.Rows > 0 && _map.Cols > 0)
            {
                int start = -1, end = -1;
                for (int r = 0; r < _map.Rows; r++)
                    for (int c = 0; c < _map.Cols; c++)
                    {
                        char cell = _map.GetCell(r, c);
                        if (cell == 'S') start = r * _map.Cols + c;
                        if (cell == 'E') end = r * _map.Cols + c;
                    }
                var parent = new Dictionary<int, int>();
                var queue = new Queue<int>();
                if (start >= 0 && end >= 0) { queue.Enqueue(start); parent[start] = -1; }
                int[] dr = { -1, 1, 0, 0 }, dc = { 0, 0, -1, 1 };
                while (queue.Count > 0 && !parent.ContainsKey(end))
                {
                    int current = queue.Dequeue(), r = current / _map.Cols, c = current % _map.Cols;
                    for (int d = 0; d < 4; d++)
                    {
                        int nr = r + dr[d], nc = c + dc[d], next = nr * _map.Cols + nc;
                        if (nr < 0 || nr >= _map.Rows || nc < 0 || nc >= _map.Cols || parent.ContainsKey(next)) continue;
                        char cell = _map.GetCell(nr, nc);
                        if (!BoardGeometry.IsWalkable(BoardGeometry.ParseCell(cell))) continue;
                        parent[next] = current; queue.Enqueue(next);
                    }
                }
                if (end >= 0 && parent.ContainsKey(end))
                    for (int at = end; at >= 0; at = parent[at]) _route.Add(at);
            }
            raycastTarget = false; SetVerticesDirty();
        }
        protected override void OnPopulateMesh(VertexHelper vh)
        {
            vh.Clear();
            if (_map == null || _map.Rows <= 0 || _map.Cols <= 0) return;
            Rect bounds = GetPixelAdjustedRect();
            float unit = Mathf.Min(bounds.width / _map.Cols, bounds.height / _map.Rows);
            Vector2 origin = bounds.center + new Vector2(-_map.Cols * unit, -_map.Rows * unit) * .5f;
            for (int r = 0; r < _map.Rows; r++)
                for (int c = 0; c < _map.Cols; c++)
                {
                    char cell = _map.GetCell(r, c);
                    if (cell == 'X') continue;
                    Color tint = cell == 'S' ? new Color(.12f,.75f,.85f) : cell == 'E' ? new Color(1f,.3f,.37f)
                        : cell == '#' ? new Color(.11f,.15f,.20f) : new Color(.16f,.22f,.29f);
                    float x = origin.x + c * unit, y = origin.y + (_map.Rows - r - 1) * unit;
                    Quad(vh, new Rect(x + 1, y + 1, unit - 2, unit - 2), tint);
                    if (_route.Contains(r * _map.Cols + c))
                        Quad(vh, new Rect(x + unit * .4f, y + unit * .4f, unit * .2f, unit * .2f), new Color(.49f,.91f,1f));
                }
        }
        private static void Quad(VertexHelper vh, Rect r, Color color)
        {
            int n = vh.currentVertCount;
            vh.AddVert(new Vector3(r.xMin,r.yMin),color,Vector2.zero);
            vh.AddVert(new Vector3(r.xMin,r.yMax),color,Vector2.zero);
            vh.AddVert(new Vector3(r.xMax,r.yMax),color,Vector2.zero);
            vh.AddVert(new Vector3(r.xMax,r.yMin),color,Vector2.zero);
            vh.AddTriangle(n,n+1,n+2); vh.AddTriangle(n,n+2,n+3);
        }
    }
}
