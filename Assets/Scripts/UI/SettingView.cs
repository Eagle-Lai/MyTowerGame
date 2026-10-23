using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>语言选择、存档重置和关闭操作；语言切换立即生效并持久化。</summary>
    public class SettingView : MonoBehaviour
    {
        public const string LogicalName = "SettingView";

        private Button _resetBtn;
        private Button _closeBtn;
        private TMP_Text _title;
        private TMP_Dropdown _languageDropdown;

        /// <summary>下拉框第 i 项 ↔ Language 的映射（顺序 = LocalizationSettings.supportedLanguages）。</summary>
        private readonly List<Language> _languages = new List<Language>();
        private bool _subscribed;

        private void Awake()
        {
            _title = FindText("Panel/Title");
            _resetBtn = FindButton("Panel/ResetBtn");
            _closeBtn = FindButton("Panel/CloseBtn");
            _languageDropdown = FindDropdown("Panel/LanguageDropdown");

            if (_resetBtn != null) _resetBtn.onClick.AddListener(OnClickReset);
            if (_closeBtn != null) _closeBtn.onClick.AddListener(OnClickClose);
            if (_languageDropdown != null) _languageDropdown.onValueChanged.AddListener(OnPickLanguage);
            Button bg = FindButton("Bg");
            if (bg != null) bg.onClick.AddListener(OnClickClose);

            BuildLanguageOptions();
        }

        private void OnEnable()
        {
            // 每次打开都按当前语言全量刷新（UIManager 池化复用实例，Awake 只跑一次）
            Refresh();
            Subscribe();
        }

        private void OnDisable()
        {
            Unsubscribe();
        }

        // ------------------------------------------------------------------
        // 语言切换（2026-10-16）
        // ------------------------------------------------------------------

        /// <summary>
        /// 构建语言下拉框的选项列表。
        ///
        /// 【数据源】LocalizationSettings.supportedLanguages（配置即真理，不硬编码语言集合）；
        ///   资产缺失 / 列表为空时回退到"枚举里的三语言"硬兜底（保持零崩溃口径）。
        /// 【选项文案】LanguageUtil.DisplayName 的**自显名**（"English / 简体中文 / 繁體中文"）——
        ///   刻意不查多语言表：用语言 A 的界面显示语言 B 的名字时，永远不会因缺 key 露馅。
        /// </summary>
        private void BuildLanguageOptions()
        {
            _languages.Clear();
            LocalizationSettings settings = LanguageManager.Settings;
            if (settings != null && settings.supportedLanguages != null)
            {
                for (int i = 0; i < settings.supportedLanguages.Count; i++)
                {
                    Language lang = settings.supportedLanguages[i];
                    if (!_languages.Contains(lang))
                    {
                        _languages.Add(lang);   // 去重：配置里写重了也不给下拉框放两遍
                    }
                }
            }
            if (_languages.Count == 0)
            {
                _languages.Add(Language.English);
                _languages.Add(Language.ChineseSimplified);
                _languages.Add(Language.ChineseTraditional);
            }

            if (_languageDropdown == null)
            {
                return;
            }
            List<string> options = new List<string>(_languages.Count);
            for (int i = 0; i < _languages.Count; i++)
            {
                options.Add(_languages[i].DisplayName());
            }
            _languageDropdown.ClearOptions();
            _languageDropdown.AddOptions(options);
            SyncLanguageDropdown();
        }

        /// <summary>
        /// 下拉框选中项 → 切换语言。
        /// 真正的全局刷新交给 LanguageChangedEvent（唯一入口，见 LanguageManager.SetLanguage）；
        /// 这里补一次 Refresh 是为了覆盖"选中的就是当前语言"（SetLanguage 内部会短路不广播）的情况。
        /// </summary>
        private void OnPickLanguage(int index)
        {
            if (index < 0 || index >= _languages.Count)
            {
                return;
            }
            LanguageManager.SetLanguage(_languages[index]);
            Refresh();
        }

        /// <summary>把下拉框选中值同步到"当前语言"（SetValueWithoutNotify：不触发 onValueChanged 回环）。</summary>
        private void SyncLanguageDropdown()
        {
            if (_languageDropdown == null)
            {
                return;
            }
            int index = _languages.IndexOf(LanguageManager.Current);
            if (index < 0)
            {
                index = 0;      // 当前语言不在候选列表（配置被改过）→ 显示第一项，不强切语言
            }
            if (_languageDropdown.value != index)
            {
                _languageDropdown.SetValueWithoutNotify(index);
            }
        }

        /// <summary>语言已切换（广播回来）→ 重刷本界面手动拼写的文本 + 同步下拉框选中值。</summary>
        private void OnLanguageChanged(int lang)
        {
            Refresh();
        }

        private void Subscribe()
        {
            if (_subscribed)
            {
                return;
            }
            EventDispatcher.AddEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
            _subscribed = true;
        }

        private void Unsubscribe()
        {
            if (!_subscribed)
            {
                return;
            }
            EventDispatcher.RemoveEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
            _subscribed = false;
        }

        // ------------------------------------------------------------------
        // 重置 / 关闭
        // ------------------------------------------------------------------

        private void OnClickReset()
        {
            // UI 补全 C2：重置存档是**不可撤销**的，必须先确认。
            // 改造前这里点一下就真的清了（玩家点错就没了）。
            ConfirmView.Show(
                Localization.Get("Reset Save") ?? "重置存档",
                Localization.Get("This will erase all progress. Continue?") ?? "将清空所有关卡进度与星级，此操作不可撤销。",
                ConfirmType.Danger, DoReset,
                Localization.Get("OK") ?? "确定重置",
                Localization.Get("Cancel") ?? "取消");
        }

        private void DoReset()
        {
            SaveManager.Instance.ResetAll();
            Refresh();
            EventDispatcher.TriggerEvent<string>(EventName.ShowTipEvent,
                Localization.Get("Save reset") ?? "存档已重置");
        }

        private void OnClickClose()
        {
            EventDispatcher.TriggerEvent(EventName.CloseSettingsRequestEvent);
        }

        private void Refresh()
        {
            // 标题：静态文案，但在批量挂载工具的"动态文本排除名单"里（Title），
            // 不走 TextLocalizer —— 由本方法负责随语言刷新。
            if (_title != null)
            {
                _title.text = Localization.Get("Settings") ?? "设置";
                LanguageManager.ApplyFont(_title);
            }

            SyncLanguageDropdown();
        }

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Setting] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Setting] 缺少按钮节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Button>();
        }

        private TMP_Dropdown FindDropdown(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Setting] 缺少下拉框节点「" + path + "」（prefab 可能未重生成？）");
                return null;
            }
            return tr.GetComponent<TMP_Dropdown>();
        }

    }
}
