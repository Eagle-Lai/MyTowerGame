using System.Collections;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 界面淡入（M4-3）。由 UIManager 在打开界面时按需补挂。
    ///
    /// 【为什么不用 DOTween】工程里确实带了 DOTween，但界面淡入是"一个 alpha 从 0 到 1"的量级，
    /// 为此引入一条补间链、还要保证 DOTween 已初始化，收益为负。
    /// 十来行的协程更可控，也少一处运行时依赖。
    ///
    /// 【为什么用 unscaledDeltaTime】暂停界面（PauseView）是在 timeScale = 0 下打开的，
    /// 用 scaled 时间的话它永远不会淡入，直接卡在全透明。
    /// </summary>
    public class UIFader : MonoBehaviour
    {
        private CanvasGroup _cg;
        private float _duration;
        private Coroutine _running;

        public void Begin(CanvasGroup cg, float durationSec)
        {
            _cg = cg;
            _duration = Mathf.Max(0.01f, durationSec);
            if (_running != null)
            {
                StopCoroutine(_running);
            }
            _running = StartCoroutine(Run());
        }

        private IEnumerator Run()
        {
            if (_cg == null)
            {
                yield break;
            }
            float t = 0f;
            _cg.alpha = 0f;
            while (t < _duration)
            {
                t += Time.unscaledDeltaTime;
                _cg.alpha = Mathf.Clamp01(t / _duration);
                yield return null;
            }
            _cg.alpha = 1f;
            _running = null;
        }
    }
}
