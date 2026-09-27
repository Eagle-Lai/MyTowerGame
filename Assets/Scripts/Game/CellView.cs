using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 单个格子的视图（世界空间 SpriteRenderer）。
    /// 只负责显示与高亮，不含任何游戏逻辑。
    ///
    /// 【为什么单独成文件】Unity 要求 MonoBehaviour 的类名与文件名一致，
    /// 否则该组件拿不到 MonoScript、无法被序列化进 prefab。
    /// </summary>
    public class CellView : MonoBehaviour
    {
        private SpriteRenderer _sr;
        private Color _baseColor = Color.white;
        private CellHighlight _highlight = CellHighlight.None;

        public CellData Data { get; private set; }

        /// <summary>
        /// 初始化。
        /// 【关于缩放】生成出来的格子贴图是 128×128 像素、PPU=100 → 原生 1.28 世界单位，
        /// 而格子边长是 1.0。如果直接 localScale = 0.94 会得到 1.20 单位，格子互相重叠。
        /// 正确做法是**按精灵原生尺寸折算**：scale = 目标尺寸 / 原生尺寸。
        /// 这样以后换任何分辨率的格子图都不用改代码。
        /// </summary>
        public void Setup(CellData data, Sprite sprite, float cellSize, float fillRatio = 0.94f)
        {
            Data = data;
            _sr = GetComponent<SpriteRenderer>();
            if (_sr == null)
            {
                _sr = gameObject.AddComponent<SpriteRenderer>();
            }
            _sr.sprite = sprite;
            _sr.sortingOrder = BoardSorting.Cell;

            float target = cellSize * fillRatio;
            float native = 1f;
            if (sprite != null)
            {
                native = Mathf.Max(sprite.bounds.size.x, sprite.bounds.size.y);
            }
            float s = native > 0.0001f ? target / native : target;
            transform.localScale = new Vector3(s, s, 1f);

            // 障碍/空洞用暗色区分，便于目视核对配置表
            switch (data.Type)
            {
                case CellType.Obstacle:
                case CellType.Hole:
                    _baseColor = new Color(0.35f, 0.35f, 0.4f, 1f);
                    break;
                case CellType.Spawn:
                    _baseColor = new Color(0.6f, 0.9f, 0.6f, 1f);
                    break;
                case CellType.End:
                    _baseColor = new Color(0.95f, 0.6f, 0.6f, 1f);
                    break;
                default:
                    _baseColor = Color.white;
                    break;
            }
            transform.position = new Vector3(data.Center.x, data.Center.y, 0f);
            _sr.color = _baseColor;
        }

        public void SetHighlight(CellHighlight h)
        {
            if (_sr == null || _highlight == h)
            {
                return;
            }
            _highlight = h;
            switch (h)
            {
                case CellHighlight.Buildable:
                    _sr.color = new Color(0.4f, 1f, 0.4f, 1f);
                    break;
                case CellHighlight.Blocked:
                    _sr.color = new Color(1f, 0.35f, 0.35f, 1f);
                    break;
                default:
                    _sr.color = _baseColor;
                    break;
            }
        }

        public void ResetHighlight()
        {
            SetHighlight(CellHighlight.None);
        }
    }
}
