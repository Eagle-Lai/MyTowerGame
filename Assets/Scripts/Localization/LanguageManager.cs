using System.Collections.Generic;
using TMPro;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 多语言总门面（静态类，热更层）。
    ///
    /// 职责：
    ///   1. 持有"当前语言"，并在切换时广播 <see cref="EventName.LanguageChangedEvent"/>
    ///   2. 从多语言配置表构建 key→文本 字典（<see cref="LocalizationLookup"/>）
    ///   3. 对外提供**不抛异常**的取词 / 取字体接口
    ///
    /// 【取词回退链】当前语言 → 英文 → null（null 由调用方回退到原文本）。
    /// 【为什么不抛异常】多语言表可能不全、可能还没加载；界面绝不能因为缺一个 key 就崩。
    ///   所以所有接口在"未就绪/找不到"时一律返回 null，最多打印一条限流警告。
    /// </summary>
    public static class LanguageManager
    {
        /// <summary>配置资产在 Resources 下的相对路径（不带扩展名）。</summary>
        private const string SettingsPath = "Localization/LocalizationSettings";

        private static LocalizationSettings _settings;
        private static LocalizationLookup _lookup;

        /// <summary>已经 Warn 过的 key（限流，避免同一个缺失 key 把 Console 刷爆）。</summary>
        private static readonly HashSet<string> _warned = new HashSet<string>();

        /// <summary>当前语言。默认英文（硬兜底），Initialize/SetLanguage 会改写它。</summary>
        public static Language Current { get; private set; } = Language.English;

        /// <summary>是否已完成 Initialize（表已构建）。</summary>
        public static bool IsReady { get; private set; }

        /// <summary>配置资产（懒加载）。可能为 null（资产缺失时）。</summary>
        public static LocalizationSettings Settings
        {
            get { EnsureSettings(); return _settings; }
        }

        // ------------------------------------------------------------------
        // 生命周期
        // ------------------------------------------------------------------

        /// <summary>
        /// 启动时调用一次：确定语言 + 构建字典。
        /// 调用时机：`Launcher` 里 `Configs.LoadAsync` 完成之后、广播 ConfigLoadedEvent 之前。
        /// </summary>
        /// <param name="save">存档管理器（可空）。有玩家显式选择时优先用存档里的语言。</param>
        public static void Initialize(SaveManager save)
        {
            EnsureSettings();

            // 优先级：存档用户选择 → 配置默认语言 → 英文（硬兜底）
            Language lang = Language.English;
            if (save != null && save.TryGetLanguage(out lang))
            {
                // 用了存档里的选择
            }
            else if (_settings != null)
            {
                lang = _settings.defaultLanguage;
            }
            Current = lang;

            RefreshLookup();
            IsReady = true;

            Debug.Log(string.Format("[Loc] 语言初始化完成：{0}（多语言表 {1} 条）",
                Current, _lookup != null ? _lookup.Count : 0));
        }

        /// <summary>从当前配置表重新构建字典。配置表加载完 / 热更替换表之后调用。</summary>
        public static void RefreshLookup()
        {
            if (_lookup == null)
            {
                _lookup = new LocalizationLookup();
            }
            _lookup.Build(Configs.LocalizationTable);
        }

        /// <summary>
        /// 切换语言：写存档 + 广播事件。
        /// 所有 TextLocalizer / ImageLocalizer 订阅了事件，会自动刷新，这里不必遍历场景。
        /// </summary>
        public static void SetLanguage(Language lang)
        {
            if (Current == lang)
            {
                return;
            }
            Current = lang;

            SaveManager sm = SaveManager.Instance;
            if (sm != null)
            {
                sm.SetLanguage(lang);
            }

            EventDispatcher.TriggerEvent<int>(EventName.LanguageChangedEvent, (int)lang);
        }

        // ------------------------------------------------------------------
        // 取词
        // ------------------------------------------------------------------

        /// <summary>取词。回退：当前语言 → 英文 → null。</summary>
        public static string GetText(string key)
        {
            if (string.IsNullOrEmpty(key) || _lookup == null)
            {
                return null;
            }

            LocEntry e;
            if (!_lookup.TryGet(key, out e))
            {
                return null;
            }

            string s = e.Get(Current);
            if (string.IsNullOrEmpty(s))
            {
                s = e.En;   // 该语言为空 → 回退英文
            }
            return string.IsNullOrEmpty(s) ? null : s;
        }

        /// <summary>
        /// 带占位符取词：命中则 string.Format。
        /// 未命中 / 格式串与参数不匹配时返回 null（调用方回退原文本）。
        /// </summary>
        public static string GetText(string key, params object[] args)
        {
            string fmt = GetText(key);
            if (fmt == null)
            {
                return null;
            }
            if (args == null || args.Length == 0)
            {
                return fmt;
            }
            try
            {
                return string.Format(fmt, args);
            }
            catch (System.FormatException)
            {
                Debug.LogWarning(string.Format("[Loc] 文案 key「{0}」占位符与参数不匹配：{1}", key, fmt));
                return fmt;
            }
        }

        // ------------------------------------------------------------------
        // 字体
        // ------------------------------------------------------------------

        /// <summary>取某语言的 TMP 字体；未配置返回 null（调用方判空后跳过设字体，避免设成 null 变方块）。</summary>
        public static TMP_FontAsset GetFont(Language lang)
        {
            EnsureSettings();
            return _settings != null ? _settings.GetFont(lang) : null;
        }

        /// <summary>
        /// 把"当前语言的字体"应用到一段文本 —— 给**不走 TextLocalizer 的手动拼词文本**用
        /// （各 View 标题、HUD 状态行等；TextLocalizer.Refresh 内部做的就是同样的事）。
        /// 【为什么集中在这里】避免每个 View 各抄一份"取字体 → 判空 → 赋值"，
        ///   也让"以后加新语言要配字体"只需要改配置资产这一处。
        /// 字体为 null（该语言没配字体）时静默跳过：宁可沿用旧字体，也不能设成 null 变方块。
        /// </summary>
        public static void ApplyFont(TMP_Text text)
        {
            if (text == null)
            {
                return;
            }
            TMP_FontAsset font = GetFont(Current);
            if (font != null && text.font != font)
            {
                text.font = font;
            }
        }

        // ------------------------------------------------------------------
        // 诊断
        // ------------------------------------------------------------------

        /// <summary>限流警告：同一个 key 只报一次。</summary>
        public static void WarnMissingKeyOnce(string key)
        {
            if (string.IsNullOrEmpty(key) || _warned.Contains(key))
            {
                return;
            }
            _warned.Add(key);
            Debug.LogWarning(string.Format("[Loc] 多语言表缺少 key：「{0}」（已回退原文本）", key));
        }

        /// <summary>
        /// 确保配置资产已加载（幂等）。
        /// 【为什么 public】界面在"记录/取字体"时不一定会先走 Initialize
        ///   （例如 LevelLoadingMask 在极早期就自建文本节点），需要一个显式的加载入口；
        ///   内部有 _settings != null 短路，重复调用零成本。
        /// </summary>
        public static void EnsureSettings()
        {
            if (_settings != null)
            {
                return;
            }
            _settings = Resources.Load<LocalizationSettings>(SettingsPath);
            if (_settings == null)
            {
                Debug.LogError(string.Format(
                    "[Loc] 找不到配置资产 Resources/{0}。请在 Unity 里创建它（右键 ▸ 创建 ▸ 塔防 ▸ 本地化配置）。",
                    SettingsPath));
            }
        }
    }
}
