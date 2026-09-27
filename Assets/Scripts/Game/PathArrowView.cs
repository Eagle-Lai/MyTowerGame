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
    /// </summary>
    public class PathArrowView : MonoBehaviour
    {
        private Transform _root;
        private Sprite _arrowSprite;
        private readonly List<SpriteRenderer> _pool = new List<SpriteRenderer>(128);
        private int _used;
        private bool _inited;

        /// <summary>箭头占格子的比例（相对格子边长，不是相对精灵原生尺寸）</summary>
        private const float ArrowScale = 0.5f;

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
        }

        private void OnDestroy()
        {
            EventDispatcher.RemoveEventListener(EventName.RefreshPathEvent, OnRefreshPath);
            EventDispatcher.RemoveEventListener(EventName.MapInitFinish, OnRefreshPath);
        }

        private void OnRefreshPath()
        {
            Render(AStarManager.Instance != null ? AStarManager.Instance.CurrentPathWorld : null);
        }

        /// <summary>按世界坐标序列摆放箭头</summary>
        public void Render(Vector3[] path)
        {
            _used = 0;
            if (path == null || path.Length < 2 || _arrowSprite == null)
            {
                HideFrom(0);
                return;
            }

            float cellSize = BoardView.Instance != null ? BoardView.Instance.CellSize : 1f;

            // 只画中间段：起点格显示为出生点、终点格显示为终点，画箭头反而看不清
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
                SpriteRenderer sr = GetArrow(_used);
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
                _used++;
            }

            HideFrom(_used);
        }

        private SpriteRenderer GetArrow(int index)
        {
            while (_pool.Count <= index)
            {
                GameObject go = new GameObject("Arrow" + _pool.Count);
                go.transform.SetParent(_root != null ? _root : transform, false);
                SpriteRenderer sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = _arrowSprite;
                sr.sortingOrder = BoardSorting.PathArrow;
                sr.color = new Color(1f, 1f, 1f, 0.75f);
                go.SetActive(false);
                _pool.Add(sr);
            }
            return _pool[index];
        }

        private void HideFrom(int index)
        {
            for (int i = index; i < _pool.Count; i++)
            {
                if (_pool[i] != null && _pool[i].gameObject.activeSelf)
                {
                    _pool[i].gameObject.SetActive(false);
                }
            }
        }

        public void Clear()
        {
            for (int i = 0; i < _pool.Count; i++)
            {
                if (_pool[i] != null)
                {
                    _pool[i].gameObject.SetActive(false);
                }
            }
            _used = 0;
        }

        public int VisibleCount { get { return _used; } }
    }
}
