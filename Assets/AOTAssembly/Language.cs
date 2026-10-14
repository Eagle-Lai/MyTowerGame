namespace FTProject
{
    /// <summary>
    /// 支持的语言。
    ///
    /// 【为什么 English = 0】它是**硬兜底**：多语言表缺 key 或某语言文本为空时，
    /// 一律回退到英文（见 LanguageManager.GetText 的回退链：当前语言 → 英文 → null）。
    /// 让英文占 0 使 `(Language)0` 天然就是安全默认值。
    /// </summary>
    public enum Language
    {
        English = 0,
        ChineseSimplified = 1,
        ChineseTraditional = 2,
    }

    /// <summary>语言枚举与稳定语言码之间的转换。</summary>
    public static class LanguageUtil
    {
        /// <summary>
        /// 语言码（BCP-47 风格）。
        /// 【为什么存档存码而不是枚举 int】将来在枚举中间插入新语言会让老存档的 int
        /// 含义漂移（例如以后加 Japanese=1，老存档里存的 1 本该是简中却变成日文）。
        /// 存字符串码则永不漂移。
        /// </summary>
        public static string ToCode(this Language lang)
        {
            switch (lang)
            {
                case Language.ChineseSimplified:  return "zh-Hans";
                case Language.ChineseTraditional: return "zh-Hant";
                default:                          return "en";
            }
        }

        /// <summary>语言码 → 枚举。无法识别时回退英文（不报错）。</summary>
        public static Language FromCode(string code)
        {
            if (code == "zh-Hans") return Language.ChineseSimplified;
            if (code == "zh-Hant") return Language.ChineseTraditional;
            return Language.English;
        }

        /// <summary>语言在 UI 上的自显名（设置界面用；刻意不查表，避免"用语言 A 显示语言 B 的名字"时缺 key）。</summary>
        public static string DisplayName(this Language lang)
        {
            switch (lang)
            {
                case Language.ChineseSimplified:  return "简体中文";
                case Language.ChineseTraditional: return "繁體中文";
                default:                          return "English";
            }
        }
    }
}
