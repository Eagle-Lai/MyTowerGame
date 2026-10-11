namespace FTProject
{
    /// <summary>
    /// 多语言取词快捷入口（业务层主要用它）。
    ///
    /// 等价于 <see cref="LanguageManager.GetText"/>，但更短、更好读：
    /// <code>
    /// SetText(label, Localization.Get("Start") ?? "开始");
    /// SetText(round, Localization.Get("Round {0}", idx) ?? string.Format("回合 {0}", idx));
    /// </code>
    ///
    /// 【零破坏约定】所有 Get 在"未命中/表未就绪"时返回 null，
    /// 调用方一律用 `?? 原文` 兜底 —— 这样即使多语言表不全，界面也照旧显示旧文案，不会空白。
    /// </summary>
    public static class Localization
    {
        public static string Get(string key)
        {
            return LanguageManager.GetText(key);
        }

        public static string Get(string key, params object[] args)
        {
            return LanguageManager.GetText(key, args);
        }

        /// <summary>当前语言（只读）。</summary>
        public static Language Current
        {
            get { return LanguageManager.Current; }
        }
    }
}
