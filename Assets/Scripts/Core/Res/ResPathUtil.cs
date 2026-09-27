using System.IO;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 资源包路径规则（**构建与运行共用**）。
    ///
    /// 【重要】打包脚本（Editor/BuildAssetBundles.cs）与运行时（BundleResLoader）
    /// 必须调用同一份方法计算路径，否则会出现"打到了 A 目录、运行时去 B 目录找"的问题。
    ///
    /// 目录结构：
    ///   Assets/StreamingAssets/AssetBundles/&lt;平台&gt;/&lt;包名&gt;
    /// 例：Assets/StreamingAssets/AssetBundles/Windows/config
    /// </summary>
    public static class ResPathUtil
    {
        /// <summary>所有平台包的统一根目录名（相对 StreamingAssets）</summary>
        public const string RootFolderName = "AssetBundles";

        /// <summary>主清单所在的包名（与平台目录同名，Unity 构建时的默认行为）</summary>
        public static string ManifestBundleName
        {
            get { return PlatformFolder; }
        }

        /// <summary>
        /// 当前平台对应的子目录名。
        /// 用固定字符串而非 Application.platform，保证构建脚本与运行时一致。
        ///
        /// 【注意】这里只判断**构建目标**相关的宏（UNITY_ANDROID 等），
        /// 不要用 UNITY_EDITOR_OSX 这类"编辑器所在系统"的宏 ——
        /// 在 Mac 上给 Windows 打包时会误判成 macOS。
        /// </summary>
        public static string PlatformFolder
        {
            get
            {
#if UNITY_ANDROID
                return "Android";
#elif UNITY_IOS
                return "iOS";
#elif UNITY_STANDALONE_OSX
                return "macOS";
#elif UNITY_STANDALONE_LINUX
                return "Linux";
#elif UNITY_WEBGL
                return "WebGL";
#else
                return "Windows";
#endif
            }
        }

        /// <summary>StreamingAssets 下的包根目录（绝对路径或 Android 下的 jar 内 URL）</summary>
        public static string RuntimeRoot
        {
            get { return Path.Combine(Application.streamingAssetsPath, RootFolderName, PlatformFolder); }
        }

        /// <summary>工程内的构建输出目录（Editor 打包脚本用）</summary>
        public static string BuildOutputRoot
        {
            get { return Path.Combine(Application.dataPath, "StreamingAssets/" + RootFolderName + "/" + PlatformFolder); }
        }

        /// <summary>某个包的完整路径</summary>
        public static string BundlePath(string bundleName)
        {
            return Path.Combine(RuntimeRoot, bundleName);
        }

        /// <summary>Android 下 StreamingAssets 位于 APK 内，需用 URL 形式经 UnityWebRequest 读取</summary>
        public static bool NeedWebRequest
        {
            get
            {
#if UNITY_ANDROID && !UNITY_EDITOR
                return true;
#else
                return false;
#endif
            }
        }

        /// <summary>把包路径转成 URL（Android 下 StreamingAssets 就在 APK 里，直接拼 jar 路径）</summary>
        public static string BundleUrl(string bundleName)
        {
            return RuntimeRoot + "/" + bundleName;
        }
    }
}
