namespace FTProject
{
    /// <summary>
    /// 一条资源地址：逻辑名 → (AB 包名, 包内资产名, 编辑器路径)。
    ///
    /// 【重要】这是资源寻址的**唯一数据源**，三处共用同一份数据：
    ///   1. EditorResLoader（编辑器）用 EditorPath 直读
    ///   2. ABNameSetter（Editor 工具）用 EditorPath 给资源自动打 AssetBundle 标记
    ///   3. BundleResLoader（真机）用 Bundle + Asset 异步加载
    ///
    /// 之所以强调"唯一数据源"：编辑器路径规则与 AB 打标规则一旦分叉，
    /// 就会出现"编辑器能跑、真机丢资源"这种最难排查的问题。
    ///
    /// 【配置表为什么不放 StreamingAssets】见 ResTable 里 config 段的注释 ——
    /// StreamingAssets 下的文件不会被导入成 TextAsset，编辑器读不到内容。
    /// </summary>
    public struct ResAddress
    {
        /// <summary>AssetBundle 名，如 "tower_normal"</summary>
        public string Bundle;

        /// <summary>包内资产名，如 "Tower_Normal0"</summary>
        public string Asset;

        /// <summary>编辑器下的资源路径（相对工程根），如 "Assets/Prefabs/Tower/Normal/Tower_Normal0.prefab"</summary>
        public string EditorPath;

        public ResAddress(string bundle, string asset, string editorPath)
        {
            Bundle = bundle;
            Asset = asset;
            EditorPath = editorPath;
        }

        public bool IsValid
        {
            get { return !string.IsNullOrEmpty(EditorPath); }
        }

        public override string ToString()
        {
            return string.Format("bundle={0}, asset={1}, path={2}", Bundle, Asset, EditorPath);
        }
    }
}
