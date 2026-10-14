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
    /// 资产实例路径：`Assets/Resources/Localization/LocalizationSettings.asset`
    ///
    /// 【★ 改 defaultLanguage 字段即可切换游戏默认语言，无需改代码 】
    ///
    /// 【为什么放 Resources 而不是 YooAsset】
    /// LanguageManager 必须在**引导期最早**就能确定语言（SplashView / LoadingView 的文案
    /// 也要本地化），而此时 YooAsset（ResLoader.Init）尚未就绪 —— 走 YooAsset 会"先有鸡还是先有蛋"。
    /// `Assets/Resources/BootUI/` 正是本工程为引导期设的同类兜底路径，有先例。
    /// 放 Resources 意味着**不进 AB、不可热更**，这正是"构建期配置"该有的语义。
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
