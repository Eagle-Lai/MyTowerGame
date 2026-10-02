using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 设置界面（M3-6）。
    ///
    /// 【为什么音量用 +/- 按钮而不是 Slider】
    ///   uGUI 的 Slider 需要 Fill/Handle 一整套子节点与三个组件的互相引用，
    ///   写在 prefab 里既长又容易错位。而本工程当前只有"音量 + 静音"两个设置项，
    ///   用两个按钮调档更简单、更好点，也不会因为布局问题失效。
    ///   将来设置项变多时再换 Slider 不迟（本界面对外只暴露 SetVolume，替换成本很低）。
    ///
    /// 【设置写到哪里】SaveManager（持久化），并立刻推给 AudioManager 生效。
    /// </summary>
    public class SettingView : MonoBehaviour
    {
        public const string LogicalName = "SettingView";

        /// <summary>每次点击调整的音量步长</summary>
        private const float Step = 0.1f;

        private Text _volumeText;
        private Button _volDown;
        private Button _volUp;
        private Button _muteBtn;
        private Text _muteLabel;
        private Button _resetBtn;
        private Button _closeBtn;
        private Text _title;

        private void Awake()
        {
            _title = FindText("Panel/Title");
            _volumeText = FindText("Panel/VolumeText");
            _volDown = FindButton("Panel/VolDownBtn");
            _volUp = FindButton("Panel/VolUpBtn");
            _muteBtn = FindButton("Panel/MuteBtn");
            _muteLabel = FindText("Panel/MuteBtn/Label");
            _resetBtn = FindButton("Panel/ResetBtn");
            _closeBtn = FindButton("Panel/CloseBtn");

            if (_volDown != null) _volDown.onClick.AddListener(delegate { StepVolume(-Step); });
            if (_volUp != null) _volUp.onClick.AddListener(delegate { StepVolume(Step); });
            if (_muteBtn != null) _muteBtn.onClick.AddListener(OnClickMute);
            if (_resetBtn != null) _resetBtn.onClick.AddListener(OnClickReset);
            if (_closeBtn != null) _closeBtn.onClick.AddListener(OnClickClose);
            Button bg = FindButton("Bg");
            if (bg != null) bg.onClick.AddListener(OnClickClose);

            if (_title != null)
            {
                _title.text = "设置";
            }
        }

        private void OnEnable()
        {
            Refresh();
        }

        private void StepVolume(float delta)
        {
            GameSettings s = SaveManager.Instance.Settings;
            SaveManager.Instance.SetVolume(s.volume + delta);
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
            // 【易错点】重置存档会连带把音量也重置回默认 —— 这是"重置"应有的语义，
            // 但要在界面上说清楚，否则玩家会以为设置丢了。
            SaveManager.Instance.ResetAll();
            SaveManager.Instance.ApplyToAudio();
            Refresh();
            EventDispatcher.TriggerEvent<string>(EventName.ShowTipEvent, "存档已重置");
        }

        private void OnClickClose()
        {
            EventDispatcher.TriggerEvent(EventName.CloseSettingsRequestEvent);
        }

        private void Refresh()
        {
            GameSettings s = SaveManager.Instance.Settings;
            SetText(_volumeText, string.Format("音量 {0}%", Mathf.RoundToInt(s.volume * 100f)));
            SetText(_muteLabel, s.muted ? "取消静音" : "静音");
        }

        private Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Setting] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Text>();
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

        private static void SetText(Text t, string v)
        {
            if (t != null && t.text != v)
            {
                t.text = v;
            }
        }
    }
}
