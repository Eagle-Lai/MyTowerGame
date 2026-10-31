using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using FTProject.AOT;

namespace FTProject
{
    // Main owns configuration/game initialization, then Splash, then the game-ready event.
    public class Launcher : MonoBehaviour
    {
        public enum BootPhase { Loading, HotUpdate, Splash, Ready, Failed }
        public BootPhase Phase { get; private set; }
        public bool IsBootComplete { get; private set; }
        public static Launcher Instance { get; private set; }
        private const int ConfigLoadMaxAttempts = 3;
        private const float ConfigLoadRetryDelaySec = 3f;
        private int _configLoadAttempts;
        private bool _configBusy;
        private readonly List<IManagerInterface> _managers = new List<IManagerInterface>
        {
            AStarManager.Instance,
            // 存档在其他业务管理器之前初始化。
            SaveManager.Instance,
            AudioManager.Instance,
            PlayerDataManager.Instance,
            EnemyManager.Instance,
            TowerManager.Instance,
            CombatSystem.Instance,
            UIManager.Instance,
        };

        private bool _booted;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Debug.LogWarning("[Launcher] 场景中存在多个 Launcher，已销毁后出现的那个");
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);

            Screen.orientation = ScreenOrientation.AutoRotation;
            Screen.autorotateToPortrait = false;
            Screen.autorotateToPortraitUpsideDown = false;
            Screen.autorotateToLandscapeLeft = true;
            Screen.autorotateToLandscapeRight = true;

            for (int i = 0; i < _managers.Count; i++)
            {
                _managers[i].OnInit();
            }

            // M5-3：性能探针常驻（只在按 F3 / 到达自动打印间隔时才输出，平时零日志）
            PerfProbe.Ensure();

        }

        private void Start()
        {
            if (_booted)
            {
                return;
            }
            _booted = true;
            BootResAndConfig();
        }

        /// <summary>
        /// 启动链（UI 补全 §5.1 重写）。
        ///
        /// 【旧实现的两个问题】
        ///   ① 全程黑屏静默：ResLoader.Init → Configs.LoadAsync 是纯嵌套回调，没有任何界面；
        ///   ② 没有热更新：发版后无法更新资源，只能整包重发。
        ///
        /// 【进度口径】LoadingView 只显示 [0,1] 的**总进度**，各阶段权重见常量：
        ///   资源系统 → 0.30；配置表 → 0.90；收尾 → 1.00；热更新有自己的界面与进度条，不占本进度。
        /// </summary>
        private void BootResAndConfig()
        {
            Debug.Log(VersionInfo.BuildLogSummary());
            StartCoroutine(PrepareMain());
        }
        private IEnumerator PrepareMain()
        {
            // Direct Main in the editor uses the same ordering and waits for resource readiness.
            if (!ResLoader.Instance.IsReady)
            {
                UIManager.Instance.Open<HotUpdateView>("HotUpdateView", UILayout.NormalPanel);
                BootUpdateSession.Report("Initializing", .4f);
                bool done = false;
                ResLoader.Instance.Init(() => done = true);
                while (!done) yield return null;
                if (!ResLoader.Instance.IsReady)
                {
                    Phase = BootPhase.Failed;
                    BootUpdateSession.Report("Failed", .4f, -1, "Resource initialization failed");
                    BootUpdateSession.Controls(retry: () => StartCoroutine(PrepareMain()));
                    yield break;
                }
            }
            BeginHotUpdate();
        }
        private void BeginHotUpdate(bool forceRecheck = false)
        {
            if (!forceRecheck && BootHotUpdateGate.Completed) { BeginLoadingConfig(); return; }
            Phase = BootPhase.HotUpdate;
            UIManager.Instance.Close("LoadingView");
            UIManager.Instance.Open<HotUpdateView>("HotUpdateView", UILayout.NormalPanel);
            BootUpdateSession.Report("Resources", .45f);
            var hot = ResLoader.HotUpdate;
            if (hot == null) { ShowFailure("Resource verifier unavailable", () => BeginHotUpdate(forceRecheck)); return; }
            hot.StartCheckUpdate(
                phase => BootUpdateSession.Report("Resources", .45f),
                (cur, total) => BootUpdateSession.Progress(cur, total, 0, 0),
                (bytes, totalBytes) => BootUpdateSession.Progress(BootUpdateSession.Files, BootUpdateSession.TotalFiles, bytes, totalBytes),
                error => ShowFailure(error, () => BeginHotUpdate(forceRecheck)),
                updated => BeginLoadingConfig());
        }
        public void RetryHotUpdate() { if (Phase == BootPhase.Failed) BeginHotUpdate(true); }
        private void ShowFailure(string error, System.Action retry)
        {
            Phase = BootPhase.Failed;
            Debug.LogWarning("[Launcher] Startup stopped: " + error);
            UIManager.Instance.Close("LoadingView");
            UIManager.Instance.Open<HotUpdateView>("HotUpdateView", UILayout.NormalPanel);
            BootUpdateSession.Report("Failed", .9f, -1, error);
            BootUpdateSession.Controls(retry: retry);
        }
        private void BeginLoadingConfig()
        {
            if (_configBusy) return;
            if (!LanguageManager.PrepareStartup())
            {
                ShowFailure("Localization resources missing", () => BeginHotUpdate(true)); return;
            }
            Phase = BootPhase.Loading;
            BootUpdateSession.Controls();
            UIManager.Instance.Close("HotUpdateView");
            var loading = UIManager.Instance.Open<LoadingView>("LoadingView", UILayout.NormalPanel);
            if (loading == null) { ShowFailure("LoadingView missing from active resource release", () => BeginHotUpdate(true)); return; }
            Debug.Log("[BootSequence] LoadingView");
            _configBusy = true;
            Configs.LoadAsync(
                (done, total) => PublishLoading(Localization.Get("Loading config...") ?? "Loading config...", total > 0 ? .1f + .8f * done / total : .1f),
                ok =>
                {
                    _configBusy = false;
                    if (Debug.isDebugBuild && ResLoader.Instance is YooAssetResLoader diagnostics)
                        Debug.Log("[BootDiagnostics] Config attempt=" + (_configLoadAttempts + 1) + " ok=" + ok + " " + diagnostics.Diagnostics());
                    if (!ok) { HandleConfigLoadFailed(); return; }
                    LanguageManager.Initialize(SaveManager.Instance);
                    CombatSystem.Instance.RebuildGridFromConfig();
                    try { if (BootReleaseStore.Selected != null) BootReleaseStore.Commit(); }
                    catch (System.Exception e) { ShowFailure(e.Message, () => BeginHotUpdate(true)); return; }
                    PublishLoading(Localization.Get("Ready") ?? "Ready", 1f);
                    StartCoroutine(FinishLoading());
                });
        }
        private static void PublishLoading(string phase, float progress)
        {
            EventDispatcher.TriggerEvent<string, float>(EventName.LoadingProgressEvent, phase, progress);
        }
        private void HandleConfigLoadFailed()
        {
            _configLoadAttempts++;
            if (_configLoadAttempts < ConfigLoadMaxAttempts)
            {
                PublishLoading(Localization.Get("Config load failed, retrying...") ?? "Config load failed, retrying...", -.1f);
                StartCoroutine(RetryConfigLoadCo());
                return;
            }
            Phase = BootPhase.Failed;
            var view = UIManager.Instance.Open<LoadingView>(LoadingView.LogicalName, UILayout.NormalPanel);
            if (view == null) { ShowFailure("LoadingView unavailable", () => BeginHotUpdate(true)); return; }
            view.SetFailed(Localization.Get("Config load failed, see Console") ?? "Config load failed, see Console");
            view.SetRecovery(() =>
            {
                _configLoadAttempts = 0;
                BeginHotUpdate(true);
            }, () => Application.Quit());
        }
        private IEnumerator RetryConfigLoadCo()
        {
            yield return new WaitForSecondsRealtime(ConfigLoadRetryDelaySec);
            // Never advance to another release after its DLLs have been loaded.
            // Reverify/repair only the pinned resource version, preserving bounded config retries.
            BeginHotUpdate(forceRecheck: true);
        }
        private IEnumerator FinishLoading()
        {
            yield return new WaitForSecondsRealtime(.25f);
            UIManager.Instance.Close("LoadingView");
            Phase = BootPhase.Splash;
            EventDispatcher.AddEventListener(EventName.SplashFinishedEvent, OnSplashFinished);
            if (UIManager.Instance.Open<SplashView>("SplashView", UILayout.NormalPanel) == null)
            {
                EventDispatcher.RemoveEventListener(EventName.SplashFinishedEvent, OnSplashFinished);
                ShowFailure("SplashView missing from active resource release", () => StartCoroutine(FinishLoading()));
                yield break;
            }
            Debug.Log("[BootSequence] SplashView");
        }
        private void OnSplashFinished()
        {
            EventDispatcher.RemoveEventListener(EventName.SplashFinishedEvent, OnSplashFinished);
            UIManager.Instance.Close("SplashView");
            Phase = BootPhase.Ready;
            IsBootComplete = true;
            Debug.Log("[BootSequence] GameReady");
            EventDispatcher.TriggerEvent<bool>(EventName.ConfigLoadedEvent, true);
        }
        private void Update()
        {
            TimerManager.Instance.Update(Time.deltaTime);
            // CombatSystem 是唯一的 UpdateEvent 订阅者（见 CombatSystem.OnInit）
            EventDispatcher.TriggerEvent(EventName.UpdateEvent);
        }

        private void OnDestroy()
        {
            if (Instance != this)
            {
                return;
            }
            EventDispatcher.RemoveEventListener(EventName.SplashFinishedEvent, OnSplashFinished);
            BootUpdateSession.Controls();
            if (AudioRuntime.Current != null) AudioRuntime.Current.FlushSettings();
            for (int i = 0; i < _managers.Count; i++)
            {
                _managers[i].OnDestroy();
            }
            Instance = null;
        }
    }
}
