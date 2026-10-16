using System;
using System.Collections;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// Boot 阶段"热更完整性闸门"（2026-10-16 新增）。
    ///
    /// ==================================================================
    /// 【它解决什么问题】
    ///   此前"检查更新 + 差异下载"由 main 场景的 Launcher 执行。检查更新的第一步
    ///   就会**激活新清单（资源版本即刻提交）**，而 bundle 下载在后 —— 一旦下载
    ///   未完成/失败（较大更新、网络中断、玩家杀进程），就会留下
    ///   "清单已切新、bundle 缺失"的中间态；下一次启动时，界面在同步加载路径上
    ///   撞到未缓存的 bundle（转后台下载 + 本次加载失败），表现为
    ///   **一次"界面残缺"的运行**（2026-10-16 模拟器实测：主菜单/选关/HUD 全缺、
    ///   直落第一关的残缺状态）。
    ///
    ///   本类把闸门提前到 **Boot 场景（main 加载之前）**：差异全部下载完成才放行；
    ///   失败/超时 → 留在本界面里自动重试（断点续传，已下载部分保留），
    ///   **绝不带缺失进 main**。
    ///   ⇒ "残缺运行"在结构上不可能再出现：要么完整进游戏，要么停在更新页重试。
    ///
    /// 【放过闸门的两条通路】
    ///   ① 服务器不可达 / 热更未启用（与 ResServerConfig 同一套闸门判定）→ 离线模式直接放行；
    ///   ② 检查更新回调 onDone（无更新，或全部差异已下载完成）。
    ///   失败（onError）**不**放行 —— 显示错误 + 自动重试，直到成功。
    ///
    /// 【为什么界面是"零 AB 依赖"的纯代码 UI】
    ///   更新完成之前，一切挂在 AB 资源上的界面都不可靠：
    ///   · HotUpdateView 是 boot_ui 包资源 —— 新清单激活后它的哈希可能已变、而新
    ///     bundle 尚未下载（这正是"更新前"的定义），同步加载必然失败；
    ///   · TMP 字体（SiYuanSongTi）也在 AB（font 包），同样不可用。
    ///   所以本界面用 UnityEngine.UI（内置模块）+ 系统字体（拿不到则内置字体），
    ///   与 AB / TMP 完全解耦。文案中英二选一：系统字体可用显示中文，
    ///   退内置字体时用英文（内置字体没有 CJK 字形，用中文会出方块）。
    ///
    /// 【为什么"极快通过"时不显示界面】
    ///   无更新时整个检查 &lt; 1 秒。若照样先创建界面再销毁，每次启动都会"闪一下"。
    ///   所以前 0.5 秒（或直到出现下载进度）保持静默 —— 只有确实要花时间的更新
    ///   才显示界面。
    /// </summary>
    public static class BootHotUpdateGate
    {
        /// <summary>
        /// **本会话是否已完整通过闸门**（供 Launcher 判断：Boot 已做过检查/下载，
        /// main 场景里无需再检查 —— 既省一次网络往返，也彻底消除"两次检查间隔内
        /// 服务器恰好发布新版本"的极小窗口）。
        /// 仅在进程内有效；每次启动 Gate 都会重跑并重新置位。
        /// </summary>
        public static bool Completed { get; private set; }

        /// <summary>静默窗口（秒）：此时间内完成则完全不显示界面。</summary>
        private const float SilentWindowSeconds = 0.5f;

        /// <summary>失败后的自动重试间隔（秒）。</summary>
        private const float RetryDelaySeconds = 3f;

        /// <summary>
        /// 运行闸门。
        /// 【回调语义】onComplete 被调用 = 资源已完整（或离线模式放行），可以安全加载 main；
        ///   下载失败时**不会**回调 —— 界面留在原地自动重试，直到完整才放行。
        /// </summary>
        public static void Run(Action onComplete)
        {
            if (onComplete == null)
            {
                return;
            }

            // 兜底①：热更能力未接（"将来新增第四套实现却忘了实现接口"的降级通路）→ 视为无需更新
            IHotUpdateLoader hot = ResLoader.HotUpdate;
            if (hot == null)
            {
                Completed = true;
                onComplete();
                return;
            }

            // 兜底②：服务器不可达 / 热更未启用 → 完全离线模式，不做任何远端请求。
            // （与 YooAssetResLoader.CreateInitOptions 的离线降级、CheckUpdateCo 的
            //   前置闸门同源 —— 三处任何一处判定不可达都不会发起 AB 网络请求。）
            if (ResServerConfig.IsRemoteHotUpdateAllowed() == false)
            {
                Debug.Log("[Boot] 热更闸门：服务器不可达/热更未启用，跳过更新检查，直接进 main（本地资源）。");
                Completed = true;
                onComplete();
                return;
            }

            ResLoaderRunner.Start(RunCo(hot, onComplete));
        }

        private static IEnumerator RunCo(IHotUpdateLoader hot, Action onComplete)
        {
            int attempt = 0;
            BootHotUpdateUI ui = null;
            bool uiDisabled = false;   // 界面创建失败过 → 不再重试（下载/放行照常，见下方防御）

            // 静默期间回调可能已产生状态 —— 先记下来，界面创建后立即补显
            string lastPhase = string.Empty;
            int lastCur = -1;
            int lastTotal = -1;
            long lastBytes = 0;
            long lastTotalBytes = 0;

            while (true)
            {
                attempt++;
                bool done = false;
                bool updated = false;
                bool sawProgress = false;
                string error = null;

                Debug.Log(string.Format("[Boot] 热更闸门：开始检查并同步 AB 资源（第 {0} 次）…", attempt));

                hot.StartCheckUpdate(
                    phase =>
                    {
                        lastPhase = phase;
                        if (ui != null) ui.SetPhase(phase);
                    },
                    (cur, total) =>
                    {
                        lastCur = cur; lastTotal = total; sawProgress = true;
                        if (ui != null) ui.SetProgress(cur, total);
                    },
                    (bytes, totalBytes) =>
                    {
                        lastBytes = bytes; lastTotalBytes = totalBytes;
                        if (ui != null) ui.SetBytes(bytes, totalBytes);
                    },
                    err => { error = err; },
                    upd => { done = true; updated = upd; });

                if (ui == null && uiDisabled == false)
                {
                    // ---- 静默窗口：极快完成（无更新）不创建任何界面 ----
                    float silentStart = Time.realtimeSinceStartup;
                    while (done == false && error == null && sawProgress == false
                           && Time.realtimeSinceStartup - silentStart < SilentWindowSeconds)
                    {
                        yield return null;
                    }

                    if (done)
                    {
                        Completed = true;
                        Debug.Log("[Boot] 热更闸门：资源已完整（检查秒过），放行进 main。");
                        onComplete();
                        yield break;
                    }

                    try
                    {
                        ui = BootHotUpdateUI.Create();
                        if (string.IsNullOrEmpty(lastPhase) == false) ui.SetPhase(lastPhase);
                        if (lastTotal > 0) ui.SetProgress(lastCur < 0 ? 0 : lastCur, lastTotal);
                        if (lastTotalBytes > 0) ui.SetBytes(lastBytes, lastTotalBytes);
                    }
                    catch (System.Exception e)
                    {
                        // 【防御】界面只是"体验层"：创建失败绝不能阻断闸门 ——
                        // 下载与放行必须照常进行，降级为"无界面"继续。
                        // （2026-10-16 实测教训：字体 API 缺失曾直接杀死本协程。）
                        ui = null;
                        uiDisabled = true;
                        Debug.LogError("[Boot] 热更闸门：进度界面创建失败（已降级为无界面，不影响下载与放行）：" + e);
                    }
                }

                // ---- 等待本次检查/下载结束 ----
                while (done == false && error == null)
                {
                    yield return null;
                }

                if (done)
                {
                    Completed = true;
                    Debug.Log(string.Format(
                        "[Boot] 热更闸门：资源完整（本次{0}，共检查 {1} 次），放行进 main。",
                        updated ? "下载了新资源" : "无新资源", attempt));
                    if (ui != null)
                    {
                        ui.ShowDone();
                        yield return new WaitForSecondsRealtime(0.35f);
                        ui.Destroy();
                    }
                    onComplete();
                    yield break;
                }

                // ---- 失败：显示错误 → 倒计时 → 自动重试（断点续传，已下载部分保留）----
                Debug.LogWarning(string.Format(
                    "[Boot] 热更闸门：第 {0} 次更新失败：{1} —— {2} 秒后自动重试（已下载部分保留）。",
                    attempt, error, RetryDelaySeconds));
                if (ui != null) ui.ShowFailure(error);

                float waitStart = Time.realtimeSinceStartup;
                while (Time.realtimeSinceStartup - waitStart < RetryDelaySeconds)
                {
                    if (ui != null) ui.SetRetryCountdown(attempt, RetryDelaySeconds - (Time.realtimeSinceStartup - waitStart));
                    yield return null;
                }

                if (ui != null) ui.ShowRetrying(attempt);
            }
        }
    }

    /// <summary>
    /// 热更闸门用的"零 AB 依赖"进度界面。
    ///
    /// 【为什么不用 HotUpdateView / TMP】见 BootHotUpdateGate 类注释 —— 更新完成前
    ///   AB 资源（含 TMP 字体）都不可靠，本界面必须只用内置模块（UnityEngine.UI）
    ///   与系统字体/内置字体，代码创建、代码销毁。
    /// 【为什么不做交互】失败自动重试（见 Gate），无需按钮；界面纯展示。
    /// </summary>
    internal class BootHotUpdateUI
    {
        private const float BarWidth = 900f;
        private const float BarHeight = 18f;

        private static readonly Color BgColor = new Color(0.043f, 0.059f, 0.078f, 1f);      // #0B0F14
        private static readonly Color AccentColor = new Color(0.208f, 0.878f, 1f, 1f);      // #35E0FF（与 Splash 标题同色）
        private static readonly Color TextColor = new Color(0.910f, 0.941f, 0.980f, 1f);    // #E8F0FA
        private static readonly Color TextDimColor = new Color(0.624f, 0.702f, 0.784f, 1f); // #9FB3C8
        private static readonly Color FailColor = new Color(1f, 0.36f, 0.36f, 1f);          // #FF5C5C

        private static Font s_font;
        private static bool s_useCjk;
        private static bool s_fontResolved;

        private GameObject _root;
        private Text _phaseText;
        private Text _detailText;
        private RectTransform _barFill;

        private int _cur = -1;
        private int _total = -1;
        private long _bytes = 0;
        private long _totalBytes = 0;

        public static BootHotUpdateUI Create()
        {
            EnsureFont();
            BootHotUpdateUI ui = new BootHotUpdateUI();
            ui.Build();
            return ui;
        }

        private static void EnsureFont()
        {
            if (s_fontResolved)
            {
                return;
            }
            s_fontResolved = true;

            // 【为什么从 AOT 桥取字体】HybridCLR 约束：热更代码直接调用
            //   Font.CreateDynamicFontFromOSFont / Resources.GetBuiltinResource<Font>
            //   会因 AOT 侧无引用被 IL2CPP 裁剪 → MissingMethodException（2026-10-16
            //   实测踩坑：异常杀死闸门协程、应用停在黑屏）。字体统一由 AOT 侧
            //   BootUiFontProvider 在 Boot 早期取好（真实调用以保符号），这里只读
            //   静态字段（访问 AOT 已保留成员 = HybridCLR 的安全路径）。
            FTProject.AOT.BootUiFontProvider.Ensure();
            s_font = FTProject.AOT.BootUiFontProvider.UiFont;
            s_useCjk = FTProject.AOT.BootUiFontProvider.UiFontHasCjk;
        }

        private static string T(string cjk, string en)
        {
            return s_useCjk ? cjk : en;
        }

        private void Build()
        {
            _root = new GameObject("~BootHotUpdateUI", typeof(Canvas), typeof(CanvasScaler));
            Canvas canvas = _root.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 30000;   // 压过一切可能的残留界面
            CanvasScaler scaler = _root.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.matchWidthOrHeight = 0.5f;

            // 全屏底（遮住 Boot 场景画面，深浅与游戏主题一致）
            Image bg = NewImage(_root.transform, "Bg", BgColor);
            Stretch(bg.rectTransform);

            // 品牌标题（跨语言恒定，无字体风险）
            Text title = NewText(_root.transform, "Title", "FREEDOM TOWER", 54, AccentColor);
            title.fontStyle = FontStyle.Bold;
            Place(title.rectTransform, 0f, 140f, 1400f, 90f);

            // 状态行
            _phaseText = NewText(_root.transform, "Phase",
                T("正在检查资源更新…", "Checking for updates..."), 30, TextColor);
            Place(_phaseText.rectTransform, 0f, 20f, 1400f, 60f);

            // 进度条：底（半透明白）+ 填充（左锚、宽度随进度）
            Image barBg = NewImage(_root.transform, "BarBg", new Color(1f, 1f, 1f, 0.10f));
            Place(barBg.rectTransform, 0f, -60f, BarWidth, BarHeight);

            Image fill = NewImage(_root.transform, "BarFill", AccentColor);
            _barFill = fill.rectTransform;
            _barFill.anchorMin = new Vector2(0.5f, 0.5f);
            _barFill.anchorMax = new Vector2(0.5f, 0.5f);
            _barFill.pivot = new Vector2(0f, 0.5f);
            _barFill.anchoredPosition = new Vector2(-BarWidth * 0.5f, -60f);
            _barFill.sizeDelta = new Vector2(0f, BarHeight);

            // 细节行（百分比 + 文件数 / 字节量）
            _detailText = NewText(_root.transform, "Detail", string.Empty, 22, TextDimColor);
            Place(_detailText.rectTransform, 0f, -100f, 1400f, 40f);
        }

        public void SetPhase(string phase)
        {
            if (_phaseText != null && string.IsNullOrEmpty(phase) == false)
            {
                _phaseText.text = phase;
                _phaseText.color = TextColor;
            }
        }

        public void SetProgress(int cur, int total)
        {
            _cur = cur;
            _total = total;
            float p = total > 0 ? Mathf.Clamp01((float)cur / total) : 0f;
            if (_barFill != null)
            {
                _barFill.sizeDelta = new Vector2(BarWidth * p, BarHeight);
            }
            RefreshDetail();
        }

        public void SetBytes(long bytes, long totalBytes)
        {
            _bytes = bytes;
            _totalBytes = totalBytes;
            RefreshDetail();
        }

        private void RefreshDetail()
        {
            if (_detailText == null)
            {
                return;
            }

            if (_totalBytes > 0)
            {
                _detailText.text = string.Format("{0:F1} MB / {1:F1} MB",
                    _bytes / 1048576f, _totalBytes / 1048576f);
            }
            else if (_total > 0)
            {
                int pct = Mathf.RoundToInt(Mathf.Clamp01((float)_cur / _total) * 100f);
                _detailText.text = pct + "%  (" + _cur + "/" + _total + ")";
            }
        }

        public void ShowFailure(string reason)
        {
            if (_phaseText != null)
            {
                _phaseText.text = T("更新失败，正在自动重试…", "Update failed, retrying automatically...");
                _phaseText.color = FailColor;
            }
            if (_detailText != null)
            {
                string brief = string.IsNullOrEmpty(reason) ? string.Empty : reason.Replace("\n", " ").Replace("\r", " ");
                if (brief.Length > 140)
                {
                    brief = brief.Substring(0, 140) + "…";
                }
                _detailText.text = brief;
            }
        }

        /// <summary>通用"异常 + 详情"展示（初始化失败等场景复用；配色与更新失败一致）。</summary>
        public void Toast(string title, string detail)
        {
            if (_phaseText != null)
            {
                _phaseText.text = title;
                _phaseText.color = FailColor;
            }
            if (_detailText != null)
            {
                string brief = string.IsNullOrEmpty(detail) ? string.Empty : detail.Replace("\n", " ").Replace("\r", " ");
                if (brief.Length > 140)
                {
                    brief = brief.Substring(0, 140) + "…";
                }
                _detailText.text = brief;
            }
        }

        public void SetRetryCountdown(int attempt, float secondsLeft)
        {
            if (_phaseText == null)
            {
                return;
            }
            int s = Mathf.Max(0, Mathf.CeilToInt(secondsLeft));
            _phaseText.text = s_useCjk
                ? string.Format("更新失败，{0} 秒后自动重试（第 {1} 次）…", s, attempt + 1)
                : string.Format("Update failed, retrying in {0}s (attempt {1})...", s, attempt + 1);
            _phaseText.color = FailColor;
        }

        public void ShowRetrying(int attempt)
        {
            if (_phaseText == null)
            {
                return;
            }
            _phaseText.text = s_useCjk
                ? string.Format("正在重试（第 {0} 次）…", attempt + 1)
                : string.Format("Retrying (attempt {0})...", attempt + 1);
            _phaseText.color = TextColor;
        }

        public void ShowDone()
        {
            if (_phaseText != null)
            {
                _phaseText.text = T("资源已就绪，正在进入游戏…", "Resources ready, entering game...");
                _phaseText.color = TextColor;
            }
            if (_barFill != null)
            {
                _barFill.sizeDelta = new Vector2(BarWidth, BarHeight);
            }
        }

        public void Destroy()
        {
            if (_root != null)
            {
                UnityEngine.Object.Destroy(_root);
                _root = null;
            }
        }

        // ------------------------------------------------------------------
        // 构件小工具（纯代码，无任何资产依赖）
        // ------------------------------------------------------------------

        private static Image NewImage(Transform parent, string name, Color color)
        {
            GameObject go = new GameObject(name, typeof(RectTransform), typeof(Image));
            go.transform.SetParent(parent, false);
            Image img = go.GetComponent<Image>();
            img.color = color;
            img.raycastTarget = false;
            return img;
        }

        private static Text NewText(Transform parent, string name, string content, int size, Color color)
        {
            GameObject go = new GameObject(name, typeof(RectTransform), typeof(Text));
            go.transform.SetParent(parent, false);
            Text t = go.GetComponent<Text>();
            t.font = s_font;
            t.text = content;
            t.fontSize = size;
            t.color = color;
            t.alignment = TextAnchor.MiddleCenter;
            t.horizontalOverflow = HorizontalWrapMode.Overflow;
            t.verticalOverflow = VerticalWrapMode.Overflow;
            t.raycastTarget = false;
            return t;
        }

        private static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = Vector2.zero;
            rt.sizeDelta = Vector2.zero;
        }

        private static void Place(RectTransform rt, float x, float y, float w, float h)
        {
            rt.anchorMin = new Vector2(0.5f, 0.5f);
            rt.anchorMax = new Vector2(0.5f, 0.5f);
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = new Vector2(x, y);
            rt.sizeDelta = new Vector2(w, h);
        }
    }
}
