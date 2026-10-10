using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 热更新下载界面（UI 补全 A3 / 效果图 17_HotUpdateView.svg）—— 唯一的上线阻塞项。
    ///
    /// 【它为什么存在】改造前 YooAssetResLoader 只做到"初始化 → 请求版本 → 加载清单"，
    /// 没有版本比对与差异下载，**发版后无法更新资源，只能整包重发**。
    ///
    /// 【状态机】阶段文案来自 `HotUpdateProgressEvent`（由 Launcher 从 IHotUpdateLoader 的回调转发），
    /// 界面不直接调 YooAsset —— 三套资源实现共用同一份 UI（见 IHotUpdateLoader 注释）。
    ///
    /// 【按钮为什么只有 3 颗，没有"进入游戏"】效果图 17 只画了左"暂停"、右"重试"两处按钮位。
    /// 计划里曾考虑加一颗"进入游戏"，但"无需更新"时 Launcher 会**自动**往下走，
    /// 多一颗要玩家点的按钮反而会挡住自动流程（还得处理"不点会怎样"）。
    /// 所以按效果图为准：左槽为"暂停/继续"互斥，右槽为"重试"。
    /// </summary>
    public class HotUpdateView : MonoBehaviour
    {
        public const string LogicalName = "HotUpdateView";

        /// <summary>进度条满宽（必须与 UIPrefabBuilder 里的 ProgressBar 宽度一致）。</summary>
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

        private float _target;
        private float _shown;
        private float _velocity;
        private bool _indeterminate;
        private float _indeterminateT;

        // 下载速率统计（用字节增量 / 时间实时估算，比"平均速率"更能反映当前网络）
        private long _lastBytes = -1;
        private float _lastBytesTime;
        private float _speedBytesPerSec;
        private long _totalBytes;
        private long _currentBytes;
        private int _currentCount;
        private int _totalCount;

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

            if (_title != null) _title.color = TextPrimary;
            if (_percentText != null) _percentText.color = Cyan;
            if (_sizeText != null) _sizeText.color = TextSecondary;
            if (_speedText != null) _speedText.color = TextSecondary;
            if (_detailText != null) _detailText.color = TextTertiary;
            if (_failText != null) _failText.color = Danger;

            if (_pauseBtn != null) _pauseBtn.onClick.AddListener(OnClickPause);
            if (_resumeBtn != null) _resumeBtn.onClick.AddListener(OnClickResume);
            if (_retryBtn != null) _retryBtn.onClick.AddListener(OnClickRetry);

            // 初始为不确定态（"正在检查更新"阶段没有可量化的总量）
            _indeterminate = true;
            ApplyProgress(0f);
            ShowFail(string.Empty);
            SetButtonState(HotButtonState.None);
        }

        private void OnEnable()
        {
            EventDispatcher.AddEventListener<int, int, long, long>(
                EventName.HotUpdateProgressEvent, OnHotUpdateProgress);
            EventDispatcher.AddEventListener<string>(EventName.HotUpdatePhaseEvent, OnHotUpdatePhase);
            EventDispatcher.AddEventListener<string>(EventName.HotUpdateFailedEvent, OnHotUpdateFailed);
            EventDispatcher.AddEventListener(EventName.HotUpdateFinishedEvent, OnHotUpdateFinished);
        }

        private void OnDisable()
        {
            EventDispatcher.RemoveEventListener<int, int, long, long>(
                EventName.HotUpdateProgressEvent, OnHotUpdateProgress);
            EventDispatcher.RemoveEventListener<string>(EventName.HotUpdatePhaseEvent, OnHotUpdatePhase);
            EventDispatcher.RemoveEventListener<string>(EventName.HotUpdateFailedEvent, OnHotUpdateFailed);
            EventDispatcher.RemoveEventListener(EventName.HotUpdateFinishedEvent, OnHotUpdateFinished);
        }

        // ------------------------------------------------------------------
        // 事件
        // ------------------------------------------------------------------

        private void OnHotUpdatePhase(string phase)
        {
            if (string.IsNullOrEmpty(phase))
            {
                return;
            }
            SetPhase(phase);
            _indeterminate = IsIndeterminatePhase(phase);
        }

        private void OnHotUpdateProgress(int cur, int total, long bytes, long totalBytes)
        {
            if (cur >= 0 && total > 0)
            {
                _currentCount = cur;
                _totalCount = total;
            }
            if (totalBytes > 0)
            {
                _totalBytes = totalBytes;
                _currentBytes = bytes;
            }

            if (_totalBytes > 0)
            {
                _indeterminate = false;
                _target = Mathf.Clamp01(_currentBytes / (float)_totalBytes);
                UpdateSpeed(_currentBytes);
            }
            else if (_totalCount > 0)
            {
                _indeterminate = false;
                _target = Mathf.Clamp01(_currentCount / (float)_totalCount);
            }

            RefreshTexts();
        }

        private void OnHotUpdateFailed(string reason)
        {
            _indeterminate = false;
            SetPhase("下载失败");
            ShowFail(reason);
            SetButtonState(HotButtonState.Retry);
        }

        private void OnHotUpdateFinished()
        {
            _indeterminate = false;
            SetPhase("更新完成");
            _target = 1f;
            ShowFail(string.Empty);
            SetButtonState(HotButtonState.None);
        }

        // ------------------------------------------------------------------
        // 按钮
        // ------------------------------------------------------------------

        private void OnClickPause()
        {
            IHotUpdateLoader hot = ResLoader.HotUpdate;
            if (hot != null)
            {
                hot.PauseDownload();
            }
            SetPhase("已暂停");
            SetButtonState(HotButtonState.Resume);
        }

        private void OnClickResume()
        {
            IHotUpdateLoader hot = ResLoader.HotUpdate;
            if (hot != null)
            {
                hot.ResumeDownload();
            }
            SetPhase("正在下载资源...");
            SetButtonState(HotButtonState.Pause);
        }

        private void OnClickRetry()
        {
            ShowFail(string.Empty);
            SetButtonState(HotButtonState.None);
            if (Launcher.Instance != null)
            {
                Launcher.Instance.RetryHotUpdate();
            }
        }

        // ------------------------------------------------------------------
        // 内部
        // ------------------------------------------------------------------

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

        private static bool IsIndeterminatePhase(string phase)
        {
            // "正在检查更新/比对版本/校验文件"这类阶段没有可量化的总字节数，
            // 硬报 0% 会让玩家以为卡住 —— 改成不确定态（来回滑动）。
            return phase.Contains("检查") || phase.Contains("比对") || phase.Contains("校验");
        }

        private void SetButtonState(HotButtonState state)
        {
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
            _failText.text = show ? ("下载失败：" + reason) : string.Empty;
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
            _speedBytesPerSec = (bytes - _lastBytes) / dt;
            _lastBytes = bytes;
            _lastBytesTime = now;
        }

        private void RefreshTexts()
        {
            if (_sizeText != null)
            {
                _sizeText.text = string.Format("已下载 {0:F1} MB / {1:F1} MB",
                    _currentBytes / 1048576f, _totalBytes / 1048576f);
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
                _speedText.text = string.Format("速度 {0:F1} MB/s　剩余约 {1}", mbs, eta);
            }
            if (_detailText != null)
            {
                _detailText.text = string.Format("文件 {0}/{1}　失败 0", _currentCount, _totalCount);
            }
        }

        private void Update()
        {
            float dt = Time.unscaledDeltaTime;

            if (_indeterminate)
            {
                // 不确定态：进度条在 15%~45% 之间来回滑动，表示"在干活但没法量化"
                _indeterminateT += dt * IndeterminateCyclesPerSec;
                float s = (Mathf.Sin(_indeterminateT * Mathf.PI * 2f) + 1f) * 0.5f;
                ApplyProgress(Mathf.Lerp(0.15f, 0.45f, s));
                if (_percentText != null)
                {
                    _percentText.text = "…";
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
                _percentText.text = Mathf.RoundToInt(clamped * 100f) + "%";
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
