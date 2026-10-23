using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 路径箭头渲染（§6.1.4）。
    ///
    /// 监听 RefreshPathEvent，按 AStarManager.CurrentPathWorld 摆放箭头。
    /// 箭头对象池化复用 —— 每次建塔都会重算路径，反复 Instantiate/Destroy 会产生大量 GC。
    ///
    /// 【M0 简化】只画"当前路径经过的每一格"，不区分拐角与直行朝向差异以外的美化。
    ///
    /// 【2026-10-22 新增预览层】放置防御塔时，悬停格会实时推演"建成后怪物会走哪里"，
    /// 用**另一种颜色**画在真实路径之上（PreviewPathEvent → PreviewPathWorld）。
    /// 两套箭头各用各的对象池，互不顶替：预览消失时真实路径必须原样还在，
    /// 否则玩家会看到"只是滑了一下，路径箭头就没了"。
    /// </summary>
    public class PathArrowView : MonoBehaviour
    {
        private Transform _root;
        private Sprite _arrowSprite;
        private readonly List<SpriteRenderer> _pool = new List<SpriteRenderer>(128);
        private int _used;
        /// <summary>预览箭头（放置态专用），与真实路径箭头分池</summary>
        private readonly List<SpriteRenderer> _previewPool = new List<SpriteRenderer>(128);
        private int _previewUsed;
        private bool _inited;

        /// <summary>箭头占格子的比例（相对格子边长，不是相对精灵原生尺寸）</summary>
        private const float ArrowScale = 0.5f;

        /// <summary>真实路径箭头：白色半透明（现状不变）</summary>
        private static readonly Color PathColor = new Color(1f, 1f, 1f, 0.75f);

        /// <summary>
        /// 预览箭头：红色（2026-10-22 用户定：预览线路显示为红色）。
        /// 与白色真实路径一眼可分，且"红 = 将要变成这样"的语义比青色更直觉。
        /// </summary>
        private static readonly Color PreviewColor = new Color(1f, 0.23f, 0.23f, 0.9f);

        /// <summary>箭头精灵的原生世界尺寸（由 Init 从 Sprite 实测，避免写死缩放）</summary>
        private float _arrowNativeSize = 0.64f;

        public void Init(Transform root)
        {
            // 幂等：重复进关卡时不要重复注册监听（EventDispatcher 用委托 += 实现，
            // 重复注册会让每次路径刷新触发多次渲染）
            if (_inited)
            {
                if (root != null)
                {
                    _root = root;
                }
                return;
            }
            _inited = true;
            _root = root;
            _arrowSprite = ResLoader.Instance.Load<Sprite>("Path_Arrow");
            if (_arrowSprite != null)
            {
                _arrowNativeSize = Mathf.Max(_arrowSprite.bounds.size.x, _arrowSprite.bounds.size.y);
                if (_arrowNativeSize < 0.0001f)
                {
                    _arrowNativeSize = 0.64f;
                }
            }
            else
            {
                Debug.LogWarning("[Path] 箭头贴图未就绪，路径可视化将不显示（不影响玩法）");
            }
            EventDispatcher.AddEventListener(EventName.RefreshPathEvent, OnRefreshPath);
            EventDispatcher.AddEventListener(EventName.MapInitFinish, OnRefreshPath);
            // 放置预览：只画箭头，不驱动怪物（见 AStarManager.PreviewPathWorld 的说明）
            EventDispatcher.AddEventListener(EventName.PreviewPathEvent, OnPreviewPathChanged);
        }

        private void OnDestroy()
        {
            EventDispatcher.RemoveEventListener(EventName.RefreshPathEvent, OnRefreshPath);
            EventDispatcher.RemoveEventListener(EventName.MapInitFinish, OnRefreshPath);
            EventDispatcher.RemoveEventListener(EventName.PreviewPathEvent, OnPreviewPathChanged);
        }

        private void OnRefreshPath()
        {
            Render(AStarManager.Instance != null ? AStarManager.Instance.CurrentPathWorld : null);
        }

        private void OnPreviewPathChanged()
        {
            RenderPreview(AStarManager.Instance != null ? AStarManager.Instance.PreviewPathWorld : null);
        }

        /// <summary>按世界坐标序列摆放箭头</summary>
        public void Render(Vector3[] path)
        {
            _used = LayoutArrows(path, _pool, "Arrow", PathColor, BoardSorting.PathArrow);
            HideFrom(_pool, _used);
        }

        /// <summary>
        /// 摆放预览箭头。
        /// 【为什么与真实路径逐格比对】若这一格建塔并不会改变路线（新路 == 旧路），
        /// 两条箭头会完全重叠，看起来像渲染重影；这时不画预览，画面语义反而更准确。
        /// </summary>
        public void RenderPreview(Vector3[] path)
        {
            Vector3[] current = AStarManager.Instance != null ? AStarManager.Instance.CurrentPathWorld : null;
            if (SamePath(path, current))
            {
                path = null;
            }
            _previewUsed = LayoutArrows(path, _previewPool, "PreviewArrow", PreviewColor, BoardSorting.PathArrow + 1);
            HideFrom(_previewPool, _previewUsed);
        }

        /// <summary>两条路径是否逐格相同（世界坐标误差 1e-4 内视为同一点）</summary>
        private static bool SamePath(Vector3[] a, Vector3[] b)
        {
            if (a == null || b == null)
            {
                return a == b;
            }
            if (a.Length != b.Length)
            {
                return false;
            }
            for (int i = 0; i < a.Length; i++)
            {
                if ((a[i] - b[i]).sqrMagnitude > 0.0001f)
                {
                    return false;
                }
            }
            return true;
        }

        /// <summary>
        /// 把路径摆成箭头，返回用掉的箭头数。
        /// 真实路径与预览路径共用这一份布局逻辑 —— 两者几何必须完全一致，
        /// 复制两份迟早分叉（一处改了缩放/朝向，另一处忘了改）。
        /// </summary>
        private int LayoutArrows(Vector3[] path, List<SpriteRenderer> pool, string namePrefix,
            Color color, int sortingOrder)
        {
            if (path == null || path.Length < 2 || _arrowSprite == null)
            {
                return 0;
            }

            float cellSize = BoardView.Instance != null ? BoardView.Instance.CellSize : 1f;

            // 只画中间段：起点格显示为出生点、终点格显示为终点，画箭头反而看不清
            int used = 0;
            for (int i = 0; i < path.Length - 1; i++)
            {
                Vector2 cur = path[i];
                Vector2 next = path[i + 1];
                Vector2 dir = next - cur;
                if (dir.sqrMagnitude < 0.0001f)
                {
                    continue;
                }

                // 在格子之间插一个箭头（指向下一格），避免每格都画导致视觉噪杂
                SpriteRenderer sr = GetArrow(pool, namePrefix, used, color, sortingOrder);
                if (sr == null)
                {
                    break;
                }
                Vector2 mid = (cur + next) * 0.5f;
                sr.transform.position = new Vector3(mid.x, mid.y, 0f);
                // 按精灵原生尺寸折算，自适应任何格子边长与箭头图分辨率
                float s = cellSize * ArrowScale / _arrowNativeSize;
                sr.transform.localScale = new Vector3(s, s, 1f);

                float angle = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
                sr.transform.localRotation = Quaternion.Euler(0f, 0f, angle - 90f);
                sr.gameObject.SetActive(true);
                used++;
            }
            return used;
        }

        private SpriteRenderer GetArrow(List<SpriteRenderer> pool, string namePrefix, int index,
            Color color, int sortingOrder)
        {
            while (pool.Count <= index)
            {
                GameObject go = new GameObject(namePrefix + pool.Count);
                go.transform.SetParent(_root != null ? _root : transform, false);
                SpriteRenderer sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = _arrowSprite;
                sr.sortingLayerName = BoardSorting.LayerMain;
                sr.sortingOrder = sortingOrder;
                sr.color = color;
                go.SetActive(false);
                pool.Add(sr);
            }
            return pool[index];
        }

        private static void HideFrom(List<SpriteRenderer> pool, int index)
        {
            for (int i = index; i < pool.Count; i++)
            {
                if (pool[i] != null && pool[i].gameObject.activeSelf)
                {
                    pool[i].gameObject.SetActive(false);
                }
            }
        }

        public void Clear()
        {
            HideFrom(_pool, 0);
            HideFrom(_previewPool, 0);
            _used = 0;
            _previewUsed = 0;
        }

        public int VisibleCount { get { return _used; } }

        /// <summary>预览箭头可见数量（自检/测试用：预览是否真的画出来了）</summary>
        public int VisiblePreviewCount { get { return _previewUsed; } }
    }
}
