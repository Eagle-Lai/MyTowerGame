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
        private readonly Slider[] _volume = new Slider[3];
        private readonly TMP_Text[] _volumeLabels = new TMP_Text[3], _volumeValues = new TMP_Text[3];
        private Toggle _mute;
        private TMP_Text _muteLabel;

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

            InitializeAudioControls();
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
            if (AudioRuntime.Current != null) AudioRuntime.Current.FlushSettings();
            StopAllCoroutines();
            _resetting = false;
            if (_resetBtn != null) _resetBtn.interactable = true;
            if (_closeBtn != null) _closeBtn.interactable = true;
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
            if (LanguageManager.Current != _languages[index]) GameAudio.Play(SoundCue.UiToggle);
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
            StartCoroutine(ResetRoutine());
        }
        private bool _resetting;
        private System.Collections.IEnumerator ResetRoutine()
        {
            if (_resetting) yield break;
            _resetting = true;
            if(_resetBtn!=null)_resetBtn.interactable=false;
            if(_closeBtn!=null)_closeBtn.interactable=false;
            yield return null;
            bool ok = SaveManager.Instance != null && SaveManager.Instance.TryResetAll();
            _resetting=false;
            if(_resetBtn!=null)_resetBtn.interactable=true;
            if(_closeBtn!=null)_closeBtn.interactable=true;
            Refresh();
            if(ok)EventDispatcher.TriggerEvent<string>(EventName.ShowTipEvent,Localization.Get("Save reset")??"Save reset");
            else ConfirmView.Show(Localization.Get("Reset Save")??"Reset Save",
                Localization.Get("Save reset failed")??"Save reset failed. Please retry.",ConfirmType.Danger,DoReset,
                Localization.Get("Retry")??"Retry",Localization.Get("Cancel")??"Cancel");
        }

        private void OnClickClose()
        {
            if (_resetting) return;
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
            SyncAudioControls();
        }


        private void InitializeAudioControls()
        {
            string[] names = { "Master", "Music", "Sfx" };
            for (int i = 0; i < names.Length; i++)
            {
                int index = i;
                var node = transform.Find("Panel/Audio" + names[i] + "Slider");
                _volume[i] = node != null ? node.GetComponent<Slider>() : null;
                _volumeLabels[i] = FindText("Panel/Audio" + names[i] + "Label");
                _volumeValues[i] = FindText("Panel/Audio" + names[i] + "Value");
                if (_volume[i] != null) _volume[i].onValueChanged.AddListener(value => ChangeVolume(index, value));
            }
            var muteNode = transform.Find("Panel/AudioMuteToggle");
            _mute = muteNode != null ? muteNode.GetComponent<Toggle>() : null;
            _muteLabel = FindText("Panel/AudioMuteToggle/AudioMuteLabel");
            if (_mute != null) _mute.onValueChanged.AddListener(value =>
            {
                var audio = AudioPreferences.Normalize(SaveManager.Instance.Settings.audio);
                if (audio.muted == value) return;
                audio.muted = value; SaveManager.Instance.SetAudioPreferences(audio);
                if (AudioRuntime.Current != null) AudioRuntime.Current.FlushSettings();
                GameAudio.Play(SoundCue.UiToggle);
            });
        }
        private void ChangeVolume(int index, float value)
        {
            var audio = AudioPreferences.Normalize(SaveManager.Instance.Settings.audio);
            if (index == 0) audio.master = value; else if (index == 1) audio.music = value; else audio.sfx = value;
            SaveManager.Instance.SetAudioPreferences(audio);
            if (_volumeValues[index] != null) _volumeValues[index].text = Mathf.RoundToInt(value * 100) + "%";
            var feedback = _volume[index].GetComponent<AudioSliderFeedback>(); if (feedback != null) feedback.MarkChanged();
        }
        private void SyncAudioControls()
        {
            var audio = AudioPreferences.Normalize(SaveManager.Instance.Settings.audio);
            float[] values = { audio.master, audio.music, audio.sfx };
            string[] keys = { "Master Volume", "Music Volume", "SFX Volume" };
            for (int i = 0; i < 3; i++)
            {
                if (_volume[i] != null) _volume[i].SetValueWithoutNotify(values[i]);
                if (_volumeValues[i] != null) { _volumeValues[i].text = Mathf.RoundToInt(values[i] * 100) + "%"; LanguageManager.ApplyFont(_volumeValues[i]); }
                if (_volumeLabels[i] != null) { _volumeLabels[i].text = Localization.Get(keys[i]) ?? keys[i]; LanguageManager.ApplyFont(_volumeLabels[i]); }
            }
            if (_mute != null) _mute.SetIsOnWithoutNotify(audio.muted);
            if (_muteLabel != null) { _muteLabel.text = Localization.Get("Mute") ?? "Mute"; LanguageManager.ApplyFont(_muteLabel); }
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
