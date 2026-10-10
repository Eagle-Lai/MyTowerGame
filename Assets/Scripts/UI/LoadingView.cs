using TMPro;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 资源加载进度界面（UI 补全 A2 / 效果图 16_LoadingView.svg）。
    ///
    /// 【进度从哪来】只听 `LoadingProgressEvent(phase, progress)`，由 Launcher 在启动链各阶段发布。
    /// 界面**不认识** Launcher、ResLoader、Configs —— 换实现不用改这里。
    /// progress 传负数表示失败（见 Launcher.PublishLoadingFailed）。
    ///
    /// 【为什么进度条必须补间，不能直接赋真实值】真实进度是"阶段跳变"的：
    /// 资源系统 0→0.3 几乎是瞬时的，配置表 0.3→0.9 又要等一会儿。
    /// 直接赋值会让数字"啪"地跳一下，看起来像卡顿。这里用 SmoothDamp 追目标值，
    /// 表现为平滑滚动，同时**最终一定收敛到真实值**（不会像固定速度的假进度那样跑飞）。
    /// </summary>
    public class LoadingView : MonoBehaviour
    {
        public const string LogicalName = "LoadingView";

        /// <summary>进度条满宽（必须与 UIPrefabBuilder 里的 ProgressBar 宽度一致）。</summary>
        public const float FillMaxWidth = 900f;

        private const float SmoothSec = 0.3f;
        private const float TipSwitchSec = 3.5f;

        private static readonly Color TextPrimary = new Color(0.910f, 0.941f, 0.980f, 1f);   // #E8F0FA
        private static readonly Color TextSecondary = new Color(0.624f, 0.702f, 0.784f, 1f); // #9FB3C8
        private static readonly Color Gold = new Color(1f, 0.788f, 0.302f, 1f);              // #FFC94D
        private static readonly Color Danger = new Color(1f, 0.302f, 0.369f, 1f);            // #FF4D5E

        /// <summary>
        /// 加载提示池（策划案 §A2 的 7 条）。
        /// ⚠️ 刻意**不写"退回 70%"**：当前 tbglobal 的 sellRefundRate = 1（100%），
        /// 写死 70% 会变成一句与实现不符的假承诺。等数值定稿后再补数字。
        /// </summary>
        private static readonly string[] Tips =
        {
            "可以在任意空地建塔，路径会实时重算",
            "塔没有目标时绝不会浪费火力",
            "出售塔可以退回一部分累计投入",
            "减速塔能大幅提升周围所有塔的输出",
            "飞行怪会无视地面路径，注意覆盖对空",
            "回合之间有布防时间，也可以立即开始",
            "穿透塔能一次打穿一整列敌人",
        };

        private TMP_Text _statusText;
        private TMP_Text _percentText;
        private TMP_Text _tipText;
        private RectTransform _fill;
        private RectTransform _glow;

        private float _target;
        private float _shown;
        private float _velocity;
        private float _tipTimer;
        private int _tipIndex = -1;

        private void Awake()
        {
            _statusText = FindText("Panel/StatusText");
            _percentText = FindText("Panel/PercentText");
            _tipText = FindText("Panel/TipText");
            _fill = FindRect("Panel/ProgressBar/Fill");
            _glow = FindRect("Panel/ProgressBar/Glow");

            if (_percentText != null) _percentText.color = Gold;
            if (_tipText != null) _tipText.color = TextSecondary;

            ApplyProgress(0f);
        }

        private void OnEnable()
        {
            EventDispatcher.AddEventListener<string, float>(EventName.LoadingProgressEvent, OnProgress);
            _tipIndex = -1;
            ShowNextTip();
            _tipTimer = TipSwitchSec;
        }

        private void OnDisable()
        {
            EventDispatcher.RemoveEventListener<string, float>(EventName.LoadingProgressEvent, OnProgress);
        }

        private void OnProgress(string phase, float progress)
        {
            if (progress < 0f)
            {
                SetFailed(phase);
                return;
            }

            if (_statusText != null)
            {
                _statusText.text = phase;
                _statusText.color = TextPrimary;
            }
            if (_percentText != null)
            {
                _percentText.color = Gold;
            }
            _target = Mathf.Clamp01(progress);
        }

        private void Update()
        {
            float dt = Time.unscaledDeltaTime;

            _shown = Mathf.SmoothDamp(_shown, _target, ref _velocity, SmoothSec, Mathf.Infinity, dt);
            if (Mathf.Abs(_shown - _target) < 0.0005f)
            {
                _shown = _target;
                _velocity = 0f;
            }
            ApplyProgress(_shown);

            _tipTimer -= dt;
            if (_tipTimer <= 0f)
            {
                ShowNextTip();
                _tipTimer = TipSwitchSec;
            }
        }

        /// <summary>加载失败：状态文字转红并把原因显示出来，**绝不静默卡住**。</summary>
        public void SetFailed(string reason)
        {
            if (_statusText != null)
            {
                _statusText.text = reason;
                _statusText.color = Danger;
            }
            if (_percentText != null)
            {
                _percentText.color = Danger;
            }
        }

        private void ApplyProgress(float t)
        {
            float clamped = Mathf.Clamp01(t);
            SetFillWidth(_fill, clamped);
            SetFillWidth(_glow, clamped);
            if (_percentText != null)
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

        private void ShowNextTip()
        {
            if (_tipText == null || Tips.Length == 0)
            {
                return;
            }
            // 顺序轮播而不是随机：随机会出现"连续两次同一条"，看起来像没换
            _tipIndex = (_tipIndex + 1) % Tips.Length;
            _tipText.text = Tips[_tipIndex];
        }

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Loading] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private RectTransform FindRect(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Loading] 缺少矩形节点「" + path + "」");
                return null;
            }
            return tr as RectTransform;
        }
    }
}
