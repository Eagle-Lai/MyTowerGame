namespace FTProject
{
    /// <summary>
    /// 资源加载统一入口。按编译宏自动选择实现：
    ///   - 编辑器 且 未定义 FORCE_AB  → EditorResLoader（AssetDatabase 直读，改完即可运行）
    ///   - 编辑器 且 定义了 FORCE_AB  → BundleResLoader（用于验证真 AB 链路）
    ///   - 打包后（Player）          → BundleResLoader
    ///
    /// 用法：ResLoader.Instance.Instantiate("Tower_Normal0", parent)
    ///
    /// 想验证真 AB 链路时，在 Player Settings → Other Settings → Scripting Define Symbols
    /// 里加上 FORCE_AB 即可，无需改代码。
    ///
    /// 【注意】协程宿主 ResLoaderRunner 单独放在 ResLoaderRunner.cs ——
    /// 它是 MonoBehaviour，Unity 要求类名与文件名一致。
    /// </summary>
    public static class ResLoader
    {
#if UNITY_EDITOR && !FORCE_AB
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
