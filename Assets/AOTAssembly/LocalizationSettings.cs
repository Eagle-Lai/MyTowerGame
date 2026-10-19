using System;
using System.Collections.Generic;
using TMPro;
using UnityEngine;

namespace FTProject
{
    /// <summary>语言 → TMP 字体资产 的配置项。</summary>
    [Serializable]
    public class LanguageFontEntry
    {
        public Language language;
        public TMP_FontAsset font;
    }

    /// <summary>
    /// 本地化配置资产。
    ///
    /// 资产实例路径：`Assets/Localization/LocalizationSettings.asset`，由 YooAsset 收集。
    ///
    /// 【★ 改 defaultLanguage 字段即可切换游戏默认语言，无需改代码 】
    ///
    /// 类型布局属于 AOT；默认值、支持列表和字体引用由 AB 更新。
    /// DLL 加载前的稳定外壳使用 BootLocalization 的独立最小基线。
    /// </summary>
    [CreateAssetMenu(fileName = "LocalizationSettings", menuName = "塔防/本地化配置", order = 20)]
    public class LocalizationSettings : ScriptableObject
    {
        [Tooltip("默认语言。存档中没有玩家显式选择时使用它。")]
        public Language defaultLanguage = Language.English;

        [Tooltip("支持的语言列表（设置界面按此顺序生成切换项）。")]
        public List<Language> supportedLanguages = new List<Language>
        {
            Language.English,
            Language.ChineseSimplified,
            Language.ChineseTraditional,
        };

        [Tooltip("语言 → TMP 字体资产。切换语言时 TextLocalizer 会取这里的字体换给 TMP。")]
        public List<LanguageFontEntry> fonts = new List<LanguageFontEntry>();

        /// <summary>取某语言的字体；未配置返回 null（调用方判空后跳过设字体，避免设成 null 变方块）。</summary>
        public TMP_FontAsset GetFont(Language lang)
        {
            if (fonts == null) return null;
            for (int i = 0; i < fonts.Count; i++)
            {
                if (fonts[i] != null && fonts[i].language == lang && fonts[i].font != null)
                {
                    return fonts[i].font;
                }
            }
            return null;
        }
    }
}
