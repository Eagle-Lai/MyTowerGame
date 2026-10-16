using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 设置界面（M3-6；2026-10-16 新增语言切换下拉框）。
    ///
    /// 【为什么音量用 Slider】(M3-6 修订)
    ///   音量改为滑动条拖拽调节，所见即所得；VolumeText 仍同步显示百分比。
    ///   Slider 节点树（Background / Fill Area / Handle）由 UIPrefabBuilder 生成，
    ///   本脚本只关心 Panel/VolumeSlider 的 onValueChanged。
    ///
    /// 【语言切换为什么能"实时生效、不用重启"】
    ///   选语言 → LanguageManager.SetLanguage（写存档 + 广播 LanguageChangedEvent）→
    ///   ① 全场景挂了 TextLocalizer / ImageLocalizer 的静态节点**自动**刷新（不需要遍历界面）；
    ///   ② 本界面订阅了同一事件：标题、音量、静音这些"代码手动拼词"的文本在这里重刷，
    ///      下拉框选中值也一并同步；
    ///   ③ 主菜单 / 暂停 / HUD 也各自订阅（它们是设置界面打开时的"背景双人组"），
    ///      关闭设置后看到的每一处文案都已是新语言。
    ///
    /// 【设置写到哪里】SaveManager（持久化），并立刻推给 AudioManager 生效。
    /// </summary>
    public class SettingView : MonoBehaviour
    {
        public const string LogicalName = "SettingView";

        private TMP_Text _volumeText;
        private Slider _volumeSlider;
        private Button _muteBtn;
        private TMP_Text _muteLabel;
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
            _volumeText = FindText("Panel/VolumeText");
            _volumeSlider = FindSlider("Panel/VolumeSlider");
            _muteBtn = FindButton("Panel/MuteBtn");
            _muteLabel = FindText("Panel/MuteBtn/Label");
            _resetBtn = FindButton("Panel/ResetBtn");
            _closeBtn = FindButton("Panel/CloseBtn");
            _languageDropdown = FindDropdown("Panel/LanguageDropdown");

            if (_volumeSlider != null) _volumeSlider.onValueChanged.AddListener(OnVolumeChanged);
            if (_muteBtn != null) _muteBtn.onClick.AddListener(OnClickMute);
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
        // 音量 / 静音 / 重置 / 关闭
        // ------------------------------------------------------------------

        private void OnVolumeChanged(float value)
        {
            SaveManager.Instance.SetVolume(value);
            Refresh();
        }

        private void OnClickMute()
        {
            GameSettings s = SaveManager.Instance.Settings;
            SaveManager.Instance.SetMuted(!s.muted);
            Refresh();
        }

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
            // 【易错点】重置存档会连带把音量也重置回默认 —— 这是"重置"应有的语义，
            // 但要在界面上说清楚，否则玩家会以为设置丢了。
            SaveManager.Instance.ResetAll();
            SaveManager.Instance.ApplyToAudio();
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

            GameSettings s = SaveManager.Instance.Settings;
            SetText(_volumeText,
                Localization.Get("Volume {0}%", Mathf.RoundToInt(s.volume * 100f))
                ?? string.Format("音量 {0}%", Mathf.RoundToInt(s.volume * 100f)));
            LanguageManager.ApplyFont(_volumeText);
            if (_volumeSlider != null) _volumeSlider.SetValueWithoutNotify(s.volume);
            SetText(_muteLabel, s.muted
                ? (Localization.Get("Unmute") ?? "取消静音")
                : (Localization.Get("Mute") ?? "静音"));
            LanguageManager.ApplyFont(_muteLabel);

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

        private Slider FindSlider(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Setting] 缺少滑动条节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Slider>();
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

        private static void SetText(TMP_Text t, string v)
        {
            if (t != null && t.text != v)
            {
                t.text = v;
            }
        }
    }
}
