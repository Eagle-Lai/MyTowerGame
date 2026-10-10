using System;

namespace FTProject
{
    /// <summary>
    /// 资源热更新能力（UI 补全 A3 / HotUpdateView 的数据源）。
    ///
    /// ==================================================================
    /// 【为什么单独抽一个接口，而不是直接调 YooAssetResLoader】
    ///   只有 YooAsset 那套实现才真的有"远端版本比对 + 差异下载"。
    ///   编辑器直读 / 纯 AssetBundle 两套没有远端概念，但**也必须实现本接口**，
    ///   否则 UI 侧就得写 `#if USE_YOOASSET`，一处漏写就是"编辑器能跑、打包编译不过"。
    ///   统一口径：没有远端能力时立刻回调 onDone(false)（= 无需更新），界面照常往下走。
    ///
    /// 【为什么是"启动式"而不是返回 IEnumerator】
    ///   本工程运行时协程统一由 ResLoaderRunner 驱动（见 ResLoaderRunner.cs），
    ///   UI 层不应该拿到 IEnumerator（它不知道谁来推进，很容易写出"永远不执行"的协程）。
    ///   所以这里只暴露"启动 + 回调"。
    /// ==================================================================
    /// </summary>
    public interface IHotUpdateLoader
    {
        /// <summary>
        /// 启动一次"检查更新 → 必要时下载"。
        /// <paramref name="onDone"/> 的参数 = **本次是否真的下载过内容**。
        /// 失败只回调 <paramref name="onError"/>（不回调 onDone），由界面决定是否重试。
        /// 所有回调都在主线程、逐帧推进中触发。
        /// </summary>
        void StartCheckUpdate(
            Action<string> onPhase,
            Action<int, int> onProgress,
            Action<long, long> onBytes,
            Action<string> onError,
            Action<bool> onDone);

        /// <summary>暂停下载（无下载进行中时空操作）。</summary>
        void PauseDownload();

        /// <summary>继续下载（无下载进行中时空操作）。</summary>
        void ResumeDownload();

        /// <summary>是否正在下载。</summary>
        bool IsDownloading { get; }

        /// <summary>是否已暂停。</summary>
        bool IsPaused { get; }
    }
}
