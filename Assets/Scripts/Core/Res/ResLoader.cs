namespace FTProject
{
    /// <summary>
    /// 资源加载统一入口。按编译宏自动选择实现：
    ///   - 定义了 USE_YOOASSET        → YooAssetResLoader（YooAsset 第三方资源系统）
    ///   - 编辑器 且 未定义 FORCE_AB  → EditorResLoader（AssetDatabase 直读，改完即可运行）
    ///   - 编辑器 且 定义了 FORCE_AB  → BundleResLoader（用于验证真 AB 链路）
    ///   - 打包后（Player）          → BundleResLoader
    ///
    /// 用法：ResLoader.Instance.Instantiate("Tower_Normal0", parent)
    ///
    /// 想验证真 AB 链路时，在 Player Settings → Other Settings → Scripting Define Symbols
    /// 里加上 FORCE_AB 即可，无需改代码。
    ///
    /// 想切到 YooAsset 时，在同一个位置加上 USE_YOOASSET（见 YooAssetResLoader.cs）。
    /// 它优先于上面两个分支；去掉宏即完全回到原链路。之所以做成宏而不是直接换实现：
    /// YooAsset 是 UPM 包，拉不下来时**整个工程会编译不过**，加宏才能保证"没装也能构建"。
    /// 注意：YooAssetResLoader 内部也复用 FORCE_AB 来区分"编辑器模拟模式 / 离线模式"，
    /// 所以两个宏同时定义时的语义是「用 YooAsset 且走真资源包」。
    ///
    /// 【注意】协程宿主 ResLoaderRunner 单独放在 ResLoaderRunner.cs ——
    /// 它是 MonoBehaviour，Unity 要求类名与文件名一致。
    /// </summary>
    public static class ResLoader
    {
#if USE_YOOASSET
        private static readonly IResLoader _instance = new YooAssetResLoader();
#elif UNITY_EDITOR && !FORCE_AB
        private static readonly IResLoader _instance = new EditorResLoader();
#else
        private static readonly IResLoader _instance = new BundleResLoader();
#endif

        public static IResLoader Instance
        {
            get { return _instance; }
        }

        /// <summary>当前使用的实现名（日志与 UI 自检用）</summary>
        public static string ImplName
        {
            get { return _instance.GetType().Name; }
        }
    }
}
