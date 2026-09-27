using System;
using System.Collections;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 协程宿主。用于把异步回调统一延迟到下一帧，
    /// 使编辑器实现与真机实现的时序行为完全一致
    ///（否则容易写出"编辑器同步返回能跑、真机异步就崩"的代码）。
    /// </summary>
    public static class ResLoaderRunner
    {
        private static ResLoaderRunnerBehaviour _host;

        private static ResLoaderRunnerBehaviour Host
        {
            get
            {
                if (_host == null)
                {
                    GameObject go = new GameObject("[ResLoaderRunner]");
                    UnityEngine.Object.DontDestroyOnLoad(go);
                    go.hideFlags = HideFlags.HideAndDontSave;
                    _host = go.AddComponent<ResLoaderRunnerBehaviour>();
                }
                return _host;
            }
        }

        /// <summary>
        /// 延迟到下一帧执行回调。
        /// 编辑模式（未运行）下协程不会推进，退化为立即执行 —— 这是有意为之，
        /// 保证 Editor 工具脚本也能正常拿到结果。
        /// </summary>
        public static void NextFrame(Action action)
        {
            if (action == null)
            {
                return;
            }
            if (!Application.isPlaying)
            {
                action();
                return;
            }
            Host.StartCoroutine(NextFrameCo(action));
        }

        private static IEnumerator NextFrameCo(Action action)
        {
            yield return null;
            action();
        }

        /// <summary>
        /// 在共享宿主上启动一个协程（BundleResLoader 的异步加载用）。
        /// 非运行态返回 null —— 编辑模式的资源加载由 EditorResLoader 承担，
        /// 不会走到这里。
        /// </summary>
        public static Coroutine Start(IEnumerator routine)
        {
            if (routine == null || !Application.isPlaying)
            {
                return null;
            }
            return Host.StartCoroutine(routine);
        }
    }
}
