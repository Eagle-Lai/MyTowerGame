using System.Collections.Generic;
using TMPro;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 浮动提示（P0-9）。
    /// 监听 ShowTipEvent，把消息排队显示，避免短时间内多条提示互相覆盖
    ///（塔防里"金币不足"很容易在一秒内被触发好几次）。
    ///
    /// 节点：根 TipsView（CanvasGroup + 本脚本）→ 子节点 TipText(TMP)
    /// </summary>
    public class TipsView : MonoBehaviour
    {
        /// <summary>单条提示的显示时长（秒）</summary>
        private const float HoldSec = 1.2f;
        /// <summary>淡入/淡出时长（秒）</summary>
        private const float FadeSec = 0.15f;

        private sealed class Tip
        {
            public string Message;
            public float Remain;
        }

        private readonly Queue<Tip> _queue = new Queue<Tip>(8);
        private TMP_Text _text;
        private CanvasGroup _group;
        private float _alpha;
        private float _fadeTarget;
        private bool _showing;

        private void Awake()
        {
            _group = GetComponent<CanvasGroup>();
            if (_group == null)
            {
                _group = gameObject.AddComponent<CanvasGroup>();
            }
            _group.blocksRaycasts = false;
            _group.interactable = false;
            _alpha = 0f;
            _group.alpha = 0f;

            Transform tr = transform.Find("TipText");
            if (tr == null)
            {
                Debug.LogError("[Tips] 缺少子节点「TipText」（prefab 与 TipsView.cs 不一致）");
            }
            else
            {
                _text = tr.GetComponent<TMP_Text>();
                if (_text == null)
                {
                    Debug.LogError("[Tips] 节点「TipText」上没有 TMP 文本组件");
                }
            }

            EventDispatcher.AddEventListener<string>(EventName.ShowTipEvent, Show);
        }

        private void OnDestroy()
        {
            EventDispatcher.RemoveEventListener<string>(EventName.ShowTipEvent, Show);
        }

        /// <summary>入队一条提示</summary>
        public void Show(string message)
        {
            if (string.IsNullOrEmpty(message))
            {
                return;
            }
            // 队列过长时丢弃最旧的，保证最新提示一定能显示出来
            while (_queue.Count >= 3)
            {
                _queue.Dequeue();
            }
            Tip t = new Tip();
            t.Message = message;
            t.Remain = HoldSec;
            _queue.Enqueue(t);
        }

        private void Update()
        {
            // 当前没有在显示的，就从队列取一条
            if (!_showing)
            {
                if (_queue.Count == 0)
                {
                    return;
                }
                Tip next = _queue.Dequeue();
                if (_text != null)
                {
                    _text.text = next.Message;
                }
                _showing = true;
                _fadeTarget = 1f;
                // 显示时长与淡出时长都计入 Remain，整体节奏更紧凑
                _holdRemain = next.Remain;
            }

            if (!_showing)
            {
                return;
            }

            // 淡入保持 → 计时结束后淡出
            if (_holdRemain > 0f)
            {
                _holdRemain -= Time.deltaTime;
                if (_holdRemain <= 0f)
                {
                    _fadeTarget = 0f;
                }
            }

            float step = Time.deltaTime / Mathf.Max(0.01f, FadeSec);
            _alpha = Mathf.MoveTowards(_alpha, _fadeTarget, step);
            if (_group != null)
            {
                _group.alpha = _alpha;
            }

            if (_fadeTarget <= 0f && _alpha <= 0f)
            {
                _showing = false;
            }
        }

        private float _holdRemain;
    }
}
