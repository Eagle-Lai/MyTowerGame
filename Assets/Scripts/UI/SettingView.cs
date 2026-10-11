using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 设置界面（M3-6）。
    ///
    /// 【为什么音量用 Slider】(M3-6 修订)
    ///   音量改为滑动条拖拽调节，所见即所得；VolumeText 仍同步显示百分比。
    ///   Slider 节点树（Background / Fill Area / Handle）由 UIPrefabBuilder 生成，
    ///   本脚本只关心 Panel/VolumeSlider 的 onValueChanged。
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

        private void Awake()
        {
            _title = FindText("Panel/Title");
            _volumeText = FindText("Panel/VolumeText");
            _volumeSlider = FindSlider("Panel/VolumeSlider");
            _muteBtn = FindButton("Panel/MuteBtn");
            _muteLabel = FindText("Panel/MuteBtn/Label");
            _resetBtn = FindButton("Panel/ResetBtn");
            _closeBtn = FindButton("Panel/CloseBtn");

            if (_volumeSlider != null) _volumeSlider.onValueChanged.AddListener(OnVolumeChanged);
            if (_muteBtn != null) _muteBtn.onClick.AddListener(OnClickMute);
            if (_resetBtn != null) _resetBtn.onClick.AddListener(OnClickReset);
            if (_closeBtn != null) _closeBtn.onClick.AddListener(OnClickClose);
            Button bg = FindButton("Bg");
            if (bg != null) bg.onClick.AddListener(OnClickClose);

            if (_title != null)
            {
                _title.text = Localization.Get("Settings") ?? "设置";
            }
        }

        private void OnEnable()
        {
            Refresh();
        }

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
            GameSettings s = SaveManager.Instance.Settings;
            SetText(_volumeText,
                Localization.Get("Volume {0}%", Mathf.RoundToInt(s.volume * 100f))
                ?? string.Format("音量 {0}%", Mathf.RoundToInt(s.volume * 100f)));
            if (_volumeSlider != null) _volumeSlider.SetValueWithoutNotify(s.volume);
            SetText(_muteLabel, s.muted
                ? (Localization.Get("Unmute") ?? "取消静音")
                : (Localization.Get("Mute") ?? "静音"));
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

        private static void SetText(TMP_Text t, string v)
        {
            if (t != null && t.text != v)
            {
                t.text = v;
            }
        }
    }
}
