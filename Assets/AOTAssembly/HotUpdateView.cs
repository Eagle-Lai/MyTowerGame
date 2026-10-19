using TMPro;
using FTProject.AOT;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    public class HotUpdateView : MonoBehaviour
    {
        public const string LogicalName = "HotUpdateView";

        public const float FillMaxWidth = 900f;

        private const float SmoothSec = 0.25f;
        private const float IndeterminateCyclesPerSec = 0.8f;

        private static readonly Color Cyan = new Color(0.208f, 0.878f, 1f, 1f);              // #35E0FF
        private static readonly Color TextPrimary = new Color(0.910f, 0.941f, 0.980f, 1f);   // #E8F0FA
        private static readonly Color TextSecondary = new Color(0.624f, 0.702f, 0.784f, 1f); // #9FB3C8
        private static readonly Color TextTertiary = new Color(0.369f, 0.451f, 0.588f, 1f);  // #5E7396
        private static readonly Color Danger = new Color(1f, 0.302f, 0.369f, 1f);            // #FF4D5E

        private TMP_Text _title;
        private TMP_Text _phaseText;
        private TMP_Text _percentText;
        private TMP_Text _sizeText;
        private TMP_Text _speedText;
        private TMP_Text _detailText;
        private TMP_Text _failText;
        private RectTransform _fill;
        private RectTransform _glow;
        private Button _pauseBtn;
        private Button _resumeBtn;
        private Button _retryBtn;
        private GameObject _buttonGroup;

        private float _target;
        private float _shown;
        private float _velocity;
        private bool _indeterminate;
        private float _indeterminateT;

        private long _lastBytes = -1;
        private float _lastBytesTime;
        private float _speedBytesPerSec;
        private long _totalBytes;
        private long _currentBytes;
        private int _currentCount;
        private int _totalCount;
        private bool _englishFallback;

        private void Awake()
        {
            _title = FindText("Panel/HotTitle");
            _phaseText = FindText("Panel/PhaseText");
            _percentText = FindText("Panel/PercentText");
            _sizeText = FindText("Panel/SizeText");
            _speedText = FindText("Panel/SpeedText");
            _detailText = FindText("Panel/DetailText");
            _failText = FindText("Panel/FailText");
            _fill = FindRect("Panel/ProgressBar/Fill");
            _glow = FindRect("Panel/ProgressBar/Glow");
            _pauseBtn = FindButton("Panel/BtnGroup/PauseBtn");
            _resumeBtn = FindButton("Panel/BtnGroup/ResumeBtn");
            _retryBtn = FindButton("Panel/BtnGroup/RetryBtn");
            var buttonGroup = transform.Find("Panel/BtnGroup");
            _buttonGroup = buttonGroup != null ? buttonGroup.gameObject : null;
            uint[] missingGlyphs;
            _englishFallback = _phaseText == null || _phaseText.font == null
                || !_phaseText.font.HasCharacters(BootLocalization.Get("Preparing"), out missingGlyphs, true, true);

            if (_title != null) _title.color = TextPrimary;
            if (_percentText != null) _percentText.color = Cyan;
            if (_sizeText != null) _sizeText.color = TextSecondary;
            if (_speedText != null) _speedText.color = TextSecondary;
            if (_detailText != null) _detailText.color = TextTertiary;
            if (_failText != null)
            {
                _failText.color = Danger;
                _failText.enableWordWrapping = true;
                _failText.overflowMode = TextOverflowModes.Ellipsis;
                _failText.enableAutoSizing = true;
                _failText.fontSizeMin = 18;
                _failText.fontSizeMax = 26;
                _failText.rectTransform.sizeDelta = new Vector2(1400, 100);
            }

            if (_pauseBtn != null) _pauseBtn.onClick.AddListener(OnClickPause);
            if (_resumeBtn != null) _resumeBtn.onClick.AddListener(OnClickResume);
            if (_retryBtn != null) _retryBtn.onClick.AddListener(OnClickRetry);

            _indeterminate = true;
            ApplyProgress(0f);
            ShowFail(string.Empty);
            SetButtonState(HotButtonState.None);
        }

        private void OnEnable()
        {
            BootUpdateSession.Changed += RenderSession;
            RenderSession();
        }
        private void OnDisable() { BootUpdateSession.Changed -= RenderSession; }
        private void RenderSession()
        {
            _indeterminate = BootUpdateSession.Stage < 0;
            _target = BootUpdateSession.Overall;
            SetPhase(Localize(BootUpdateSession.Paused ? "Paused" : BootUpdateSession.Phase));
            if (_title != null) _title.text = Localize("Title");
            _currentCount = BootUpdateSession.Files; _totalCount = BootUpdateSession.TotalFiles;
            _currentBytes = BootUpdateSession.Bytes; _totalBytes = BootUpdateSession.TotalBytes;
            UpdateSpeed(_currentBytes);
            RefreshTexts();
            bool failed = BootUpdateSession.Phase == "Failed" || BootUpdateSession.Phase == "Restart";
            ShowFail(failed ? BootUpdateSession.Detail : "");
            if (!failed && _detailText != null && !string.IsNullOrEmpty(BootUpdateSession.Detail))
                _detailText.text = BootUpdateSession.Detail;
            SetButtonState(BootUpdateSession.Retry != null ? HotButtonState.Retry
                : BootUpdateSession.Paused && BootUpdateSession.Resume != null ? HotButtonState.Resume
                : BootUpdateSession.Pause != null ? HotButtonState.Pause : HotButtonState.None);
            SetLabel(_pauseBtn, "Pause"); SetLabel(_resumeBtn, "Resume"); SetLabel(_retryBtn, "Retry");
        }
        private string Localize(string key) { return _englishFallback ? BootLocalization.EnglishText(key) : BootLocalization.Get(key); }
        private void SetLabel(Button button, string key)
        {
            if (button != null) { var label = button.GetComponentInChildren<TMP_Text>(true); if (label != null) label.text = Localize(key); }
        }
        private void OnClickPause() { BootUpdateSession.Pause?.Invoke(); RenderSession(); }
        private void OnClickResume() { BootUpdateSession.Resume?.Invoke(); RenderSession(); }
        private void OnClickRetry()
        {
            var retry = BootUpdateSession.Retry;
            BootUpdateSession.Controls();
            retry?.Invoke();
        }

        private enum HotButtonState
        {
            None,
            Pause,
            Resume,
            Retry
        }

        private void SetPhase(string phase)
        {
            if (_phaseText != null)
            {
                _phaseText.text = phase;
                _phaseText.color = TextPrimary;
            }
        }

        private void SetButtonState(HotButtonState state)
        {
            // The prefab starts with the whole group hidden. Enabling only a child
            // leaves Retry/Pause/Resume invisible and prevents recovery on a clean APK.
            if (_buttonGroup != null) _buttonGroup.SetActive(state != HotButtonState.None);
            SetActive(_pauseBtn, state == HotButtonState.Pause);
            SetActive(_resumeBtn, state == HotButtonState.Resume);
            SetActive(_retryBtn, state == HotButtonState.Retry);
        }

        private static void SetActive(Button b, bool active)
        {
            if (b != null && b.gameObject.activeSelf != active)
            {
                b.gameObject.SetActive(active);
            }
        }

        private void ShowFail(string reason)
        {
            if (_failText == null)
            {
                return;
            }
            bool show = !string.IsNullOrEmpty(reason);
            _failText.text = show ? reason : string.Empty;
            if (_failText.gameObject.activeSelf != show)
            {
                _failText.gameObject.SetActive(show);
            }
        }

        private void UpdateSpeed(long bytes)
        {
            float now = Time.realtimeSinceStartup;
            if (_lastBytes < 0)
            {
                _lastBytes = bytes;
                _lastBytesTime = now;
                return;
            }
            float dt = now - _lastBytesTime;
            if (dt < 0.2f)
            {
                return;   // 采样太密会让速率数字剧烈抖动，看不出真实速度
            }
            _speedBytesPerSec = Mathf.Max(0, (bytes - _lastBytes) / dt);
            _lastBytes = bytes;
            _lastBytesTime = now;
        }

        private void RefreshTexts()
        {
            if (_sizeText != null)
            {
                _sizeText.text = string.Format("{0:F1} MB / {1:F1} MB", _currentBytes / 1048576f, _totalBytes / 1048576f);
            }
            if (_speedText != null)
            {
                float mbs = _speedBytesPerSec / 1048576f;
                string eta = "--:--";
                if (_speedBytesPerSec > 1024f && _totalBytes > _currentBytes)
                {
                    int left = Mathf.Max(0, Mathf.RoundToInt((_totalBytes - _currentBytes) / _speedBytesPerSec));
                    eta = string.Format("{0:00}:{1:00}", left / 60, left % 60);
                }
                _speedText.text = string.Format("{0:F1} MB/s  ETA {1}", mbs, eta);
            }
            if (_detailText != null)
            {
                _detailText.text = string.Format("{0}/{1}", _currentCount, _totalCount);
            }
        }

        private void Update()
        {
            float dt = Time.unscaledDeltaTime;

            if (_indeterminate)
            {
                _indeterminateT += dt * IndeterminateCyclesPerSec;
                ApplyProgress(_target);
                if (_percentText != null)
                {
                    _percentText.text = Localize("Overall") + " " + Mathf.RoundToInt(_target * 100f) + "%  | " + Localize("Stage") + " ...";
                }
                return;
            }

            _shown = Mathf.SmoothDamp(_shown, _target, ref _velocity, SmoothSec, Mathf.Infinity, dt);
            if (Mathf.Abs(_shown - _target) < 0.0005f)
            {
                _shown = _target;
                _velocity = 0f;
            }
            ApplyProgress(_shown);
        }

        private void ApplyProgress(float t)
        {
            float clamped = Mathf.Clamp01(t);
            SetFillWidth(_fill, clamped);
            SetFillWidth(_glow, clamped);
            if (_percentText != null && !_indeterminate)
            {
                _percentText.text = Localize("Overall") + " " + Mathf.RoundToInt(clamped * 100f) + "% | " + Localize("Stage") + " " + Mathf.RoundToInt(Mathf.Clamp01(BootUpdateSession.Stage) * 100f) + "%";
            }
        }

        private static void SetFillWidth(RectTransform rt, float t)
        {
            if (rt == null)
            {
                return;
            }
            Vector2 size = rt.sizeDelta;
            size.x = FillMaxWidth * t;
            rt.sizeDelta = size;
        }

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[HotUpdate] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private RectTransform FindRect(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[HotUpdate] 缺少矩形节点「" + path + "」");
                return null;
            }
            return tr as RectTransform;
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[HotUpdate] 缺少按钮节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Button>();
        }
    }
}
