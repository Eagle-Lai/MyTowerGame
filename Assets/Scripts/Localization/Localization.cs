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

        /// <summary>
        /// 关卡显示名（2026-10-16 多语言审计新增）。
        /// 【背景】SceneInfo 表里的 name 是"关卡 N"形态的**中文单一语言数据** ——
        ///   英文/繁体界面下直接透传会出现"中文关卡名"。界面统一改用词条
        ///   "Level {0}" 按 id 格式化（Level 2 / 关卡 2 / 關卡 2）。
        /// 【将来若把关卡名升级为专名】把这里演进为"查表 name"即可，调用点不用动。
        /// </summary>
        public static string LevelName(int levelId, string fallback)
        {
            return LanguageManager.GetText("Level {0}", levelId) ?? fallback;
        }
    }
}
