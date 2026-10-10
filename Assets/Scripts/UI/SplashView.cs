using TMPro;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 开屏页（UI 补全 A1 / 效果图 15_SplashView.svg）。
    ///
    /// 【它解决什么问题】改造前 `Launcher.Start()` 直接进异步资源初始化，**全程黑屏静默**，
    /// 玩家会以为游戏没启动。开屏页给出"正在启动"的确定反馈，同时承担品牌露出。
    ///
    /// 【为什么自带 CanvasGroup】`UIManager.EnsureFadeIn` 对"prefab 自带 CanvasGroup"的界面
    /// 会整体跳过（见 UIManager.cs）—— 本界面要自己控制整屏淡入节奏，
    /// 与 UIManager 的 0.12s 统一淡入会互相打架。
    ///
    /// 【为什么不用 DOTween】本工程虽然装了 DOTween，但**全工程零处使用**。
    /// 为一个 1.5 秒的开屏动画引入新运行时依赖不划算，这里用 Update 里按 unscaled 时间插值，
    /// 行为完全确定、也能在 timeScale=0 时正常播放。
    /// </summary>
    public class SplashView : MonoBehaviour
    {
        public const string LogicalName = "SplashView";

        /// <summary>整页停留时长（秒）。到点后发 <see cref="EventName.SplashFinishedEvent"/>，由 Launcher 接手。</summary>
        public const float HoldSeconds = 1.5f;

        private const float BgFadeSec = 0.4f;
        private const float FadeSec = 0.5f;
        private const float TitleDelay = 0.3f;
        private const float SubDelay = 0.5f;
        private const float LogoScaleFrom = 0.85f;

        private static readonly Color TitleColor = new Color(0.208f, 0.878f, 1f, 1f);        // #35E0FF
        private static readonly Color SubColor = new Color(0.624f, 0.702f, 0.784f, 1f);       // #9FB3C8
        private static readonly Color TertiaryColor = new Color(0.369f, 0.451f, 0.588f, 1f);  // #5E7396
        private static readonly Color SteelColor = new Color(0.624f, 0.702f, 0.784f, 1f);     // #9FB3C8

        private CanvasGroup _cg;
        private TMP_Text _title;
        private TMP_Text _subtitle;
        private TMP_Text _version;
        private TMP_Text _dots;
        private RectTransform _logo;

        private float _t;
        private bool _fired;

        private void Awake()
        {
            _cg = GetComponent<CanvasGroup>();
            _title = FindText("Panel/GameTitle");
            _subtitle = FindText("Panel/Subtitle");
            _version = FindText("Panel/Version");
            _dots = FindText("Panel/LoadingDots");
            _logo = FindRect("Panel/Logo");

            if (_title != null) _title.color = TitleColor;
            if (_subtitle != null) _subtitle.color = SubColor;
            if (_version != null) _version.color = TertiaryColor;
            if (_dots != null) _dots.color = SteelColor;

            // 版本号**从 Application.version 读**，绝不硬编码 ——
            // 硬编码的版本号在发版后必然与实际包体不一致，且没人会想起来改。
            if (_version != null)
            {
                _version.text = string.IsNullOrEmpty(Application.version)
                    ? string.Empty
                    : "v" + Application.version;
            }

            if (_cg != null) _cg.alpha = 0f;
            if (_logo != null) _logo.localScale = Vector3.one * LogoScaleFrom;
            SetAlpha(_title, 0f);
            SetAlpha(_subtitle, 0f);
            SetAlpha(_version, 0f);
        }

        private void Update()
        {
            if (_fired)
            {
                return;
            }

            float dt = Time.unscaledDeltaTime;
            _t += dt;

            if (_cg != null)
            {
                _cg.alpha = Mathf.Clamp01(_t / BgFadeSec);
            }

            float titleP = Mathf.Clamp01((_t - TitleDelay) / FadeSec);
            SetAlpha(_title, titleP);

            float subP = Mathf.Clamp01((_t - SubDelay) / FadeSec);
            SetAlpha(_subtitle, subP * 0.9f);

            // 版本号最后出现（它是"技术支持"类信息，不该抢品牌标题的注意力）
            SetAlpha(_version, Mathf.Clamp01((_t - SubDelay) / FadeSec));

            if (_logo != null)
            {
                float lp = Mathf.Clamp01(_t / 0.6f);
                _logo.localScale = Vector3.one * Mathf.Lerp(LogoScaleFrom, 1f, EaseOutBack(lp));
            }

            if (_dots != null)
            {
                // 省略号随时间的简单循环（1~3 个点），比转圈图省一张贴图
                int n = 1 + ((int)(_t * 2.5f) % 3);
                string suffix = n == 1 ? "." : (n == 2 ? ".." : "...");
                _dots.text = "正在启动" + suffix;
            }

            if (_t >= HoldSeconds)
            {
                _fired = true;
                EventDispatcher.TriggerEvent(EventName.SplashFinishedEvent);
            }
        }

        /// <summary>回弹缓动：末尾轻微过冲再回收，用于 Logo 入场。</summary>
        private static float EaseOutBack(float p)
        {
            const float c1 = 1.70158f;
            const float c3 = c1 + 1f;
            float x = p - 1f;
            return 1f + c3 * x * x * x + c1 * x * x;
        }

        private static void SetAlpha(TMP_Text t, float a)
        {
            if (t == null)
            {
                return;
            }
            Color c = t.color;
            c.a = Mathf.Clamp01(a);
            t.color = c;
        }

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Splash] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private RectTransform FindRect(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Splash] 缺少矩形节点「" + path + "」");
                return null;
            }
            return tr as RectTransform;
        }
    }
}
