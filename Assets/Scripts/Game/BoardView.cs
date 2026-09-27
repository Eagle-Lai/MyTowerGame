using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 棋盘视图：按 TBLevelMap 生成格子、提供坐标换算与高亮。
    ///
    /// 【性能注意】格子用 SpriteRenderer 逐个摆放，**不使用 LayoutGroup**
    /// （UGUI 的 LayoutGroup 在子节点增删时会触发整层 Rebuild，是低端机卡顿的常见根因）。
    ///
    /// 【为什么单独成文件】Unity 要求 MonoBehaviour 的类名与文件名一致，
    /// 否则该组件拿不到 MonoScript、无法被序列化进 prefab。
    /// </summary>
    public class BoardView : MonoBehaviour
    {
        public static BoardView Instance { get; private set; }

        /// <summary>格子贴图占格子的比例（留一点缝隙便于目视看清格线）</summary>
        public const float CellFillRatio = 0.94f;

        private Transform _root;
        private float _cellSize = 1f;
        private Vector2 _origin = Vector2.zero;
        private int _rows;
        private int _cols;
        private CellData[,] _cells;
        private CellView[,] _views;
        private Sprite[] _cellSprites;   // 索引与 CellType 对应（0..5）

        public float CellSize { get { return _cellSize; } }
        public Vector2 Origin { get { return _origin; } }
        public int Rows { get { return _rows; } }
        public int Cols { get { return _cols; } }
        public CellData SpawnCell { get; private set; }
        public CellData EndCell { get; private set; }
        public bool IsBuilt { get { return _cells != null; } }

        private void Awake()
        {
            Instance = this;
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                Instance = null;
            }
        }

        /// <summary>
        /// 按配置生成棋盘。
        /// origin 为棋盘左上角的世界坐标；调用方通常把它设为让棋盘居中的位置。
        /// </summary>
        public void Build(LevelMapConfig map, float cellSize, Vector2 origin, Transform root)
        {
            _root = root != null ? root : transform;
            _cellSize = cellSize;
            _origin = origin;
            _rows = map.Rows;
            _cols = map.Cols;

            _cells = new CellData[_rows, _cols];
            _views = new CellView[_rows, _cols];
            SpawnCell = null;
            EndCell = null;

            LoadCellSprites();

            for (int r = 0; r < _rows; r++)
            {
                for (int c = 0; c < _cols; c++)
                {
                    CellType type = BoardGeometry.ParseCell(map.GetCell(r, c));
                    CellData data = new CellData
                    {
                        Row = r,
                        Col = c,
                        Type = type,
                        Center = BoardGeometry.CellCenter(r, c, _cellSize, _origin),
                    };
                    _cells[r, c] = data;

                    GameObject go = new GameObject(string.Format("Cell({0},{1})", r, c));
                    go.transform.SetParent(_root, false);
                    go.transform.position = new Vector3(data.Center.x, data.Center.y, 0f);

                    CellView view = go.AddComponent<CellView>();
                    // 缩放由 CellView 按精灵原生尺寸折算（不用 LayoutGroup，也不写死 scale）
                    view.Setup(data, GetSpriteFor(type), _cellSize, CellFillRatio);
                    _views[r, c] = view;

                    if (type == CellType.Spawn) SpawnCell = data;
                    if (type == CellType.End) EndCell = data;
                }
            }

            if (SpawnCell == null || EndCell == null)
            {
                Debug.LogError("[Board] 棋盘缺少起点(S)或终点(E)，请检查 TBLevelMap 的 cells 配置");
            }
        }

        private void LoadCellSprites()
        {
            if (_cellSprites != null)
            {
                return;
            }
            _cellSprites = new Sprite[6];
            _cellSprites[(int)CellType.Ground] = ResLoader.Instance.Load<Sprite>("Cell_Ground");
            _cellSprites[(int)CellType.Spawn] = ResLoader.Instance.Load<Sprite>("Cell_Spawn");
            _cellSprites[(int)CellType.End] = ResLoader.Instance.Load<Sprite>("Cell_End");
            _cellSprites[(int)CellType.Obstacle] = ResLoader.Instance.Load<Sprite>("Cell_Blocked");
            _cellSprites[(int)CellType.Hole] = ResLoader.Instance.Load<Sprite>("Cell_Blocked");
            _cellSprites[(int)CellType.Decor] = ResLoader.Instance.Load<Sprite>("Cell_Ground");
        }

        private Sprite GetSpriteFor(CellType t)
        {
            int i = (int)t;
            if (_cellSprites == null || i < 0 || i >= _cellSprites.Length)
            {
                return null;
            }
            return _cellSprites[i];
        }

        // ------------------------------------------------------------------
        // 查询与换算
        // ------------------------------------------------------------------

        public bool IsValid(int row, int col)
        {
            return _cells != null && row >= 0 && row < _rows && col >= 0 && col < _cols;
        }

        public CellData GetCell(int row, int col)
        {
            return IsValid(row, col) ? _cells[row, col] : null;
        }

        public CellView GetView(int row, int col)
        {
            return IsValid(row, col) ? _views[row, col] : null;
        }

        public Vector3 CellCenter3(int row, int col)
        {
            return BoardGeometry.CellCenter3(row, col, _cellSize, _origin);
        }

        public Vector2 CellCenter(int row, int col)
        {
            return BoardGeometry.CellCenter(row, col, _cellSize, _origin);
        }

        public bool WorldToCell(Vector2 world, out int row, out int col)
        {
            return BoardGeometry.WorldToCell(world, _cellSize, _origin, _rows, _cols, out row, out col);
        }

        /// <summary>
        /// 屏幕坐标 → 格子索引。
        /// 正交相机下 ScreenToWorldPoint 的 z 必须取 -camera.z，否则结果落在错误的深度。
        /// </summary>
        public bool ScreenToCell(Vector2 screenPos, out int row, out int col)
        {
            row = -1;
            col = -1;
            Camera cam = Camera.main;
            if (cam == null)
            {
                return false;
            }
            Vector3 world = cam.ScreenToWorldPoint(
                new Vector3(screenPos.x, screenPos.y, -cam.transform.position.z));
            return WorldToCell(world, out row, out col);
        }

        /// <summary>棋盘几何中心（相机对准用）</summary>
        public Vector2 BoardCenterWorld()
        {
            return BoardGeometry.BoardCenter(_rows, _cols, _cellSize, _origin);
        }

        // ------------------------------------------------------------------
        // 高亮
        // ------------------------------------------------------------------

        public void SetHighlight(int row, int col, CellHighlight h)
        {
            CellView v = GetView(row, col);
            if (v != null)
            {
                v.SetHighlight(h);
            }
        }

        public void ResetHighlight(int row, int col)
        {
            CellView v = GetView(row, col);
            if (v != null)
            {
                v.ResetHighlight();
            }
        }

        public void ResetAllHighlight()
        {
            if (_views == null)
            {
                return;
            }
            for (int r = 0; r < _rows; r++)
            {
                for (int c = 0; c < _cols; c++)
                {
                    if (_views[r, c] != null)
                    {
                        _views[r, c].ResetHighlight();
                    }
                }
            }
        }
    }
}
