using UnityEngine;
using UnityEngine.Rendering;

namespace FTProject.AOT
{
    /// <summary>启动场景与热更新运行时共用的帧率策略。</summary>
    public static class FrameRatePolicy
    {
        public const int TargetFrameRate = 60;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        public static void Apply()
        {
            QualitySettings.vSyncCount = 0;
            OnDemandRendering.renderFrameInterval = 1;
            Application.targetFrameRate = TargetFrameRate;
        }
    }
}
