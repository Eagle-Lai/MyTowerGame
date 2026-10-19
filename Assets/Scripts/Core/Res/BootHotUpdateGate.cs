using System;
using System.Collections;
using UnityEngine;
using FTProject.AOT;

namespace FTProject
{
    public static class BootHotUpdateGate
    {
        public static bool Completed { get; private set; }
        private static bool _running;
        public static void Run(Action onComplete)
        {
            if (_running) throw new InvalidOperationException("Resource gate already running");
            if (Completed) { onComplete?.Invoke(); return; }
            _running = true;
            ResLoaderRunner.Start(RunCo(onComplete));
        }
        private static IEnumerator RunCo(Action onComplete)
        {
            try
            {
                while (true)
                {
                    bool done = false, retry = false;
                    string error = null;
                    int count = 0, total = 0;
                    long bytes = 0, totalBytes = 0;
                    var hot = ResLoader.HotUpdate;
                    if (hot == null) { error = "No resource update/verification provider"; }
                    else hot.StartCheckUpdate(
                        phase => BootUpdateSession.Report(BootReleaseStore.Offline ? "Offline" : "Resources", .45f, -1),
                        (cur, all) => { count = cur; total = all; BootUpdateSession.Progress(count, total, bytes, totalBytes); },
                        (cur, all) => { bytes = cur; totalBytes = all; BootUpdateSession.Progress(count, total, bytes, totalBytes); },
                        reason => error = reason,
                        updated => done = true);
                    while (!done && error == null)
                    {
                        BootUpdateSession.Controls(hot.IsDownloading && !hot.IsPaused ? (Action)(() => { hot.PauseDownload(); BootUpdateSession.Paused = true; }) : null,
                            hot.IsDownloading && hot.IsPaused ? (Action)(() => { hot.ResumeDownload(); BootUpdateSession.Paused = false; }) : null);
                        yield return null;
                    }
                    BootUpdateSession.Controls(); BootUpdateSession.Paused = false;
                    if (done)
                    {
                        try
                        {
                            if (!LanguageManager.PrepareStartup()) throw new Exception("Current localization table or settings missing");
                            if (ResLoader.Instance.Load<GameObject>("LoadingView") == null
                                || ResLoader.Instance.Load<GameObject>("SplashView") == null)
                                throw new Exception("Startup views missing from the pinned resource release");
                            Completed = true;
                        }
                        catch (Exception e) { error = e.Message; }
                        if (Completed)
                        {
                            BootUpdateSession.Report("Ready", 1f, 1f);
                            Debug.Log("[BootSequence] ResourcesVerified");
                            onComplete?.Invoke();
                            yield break;
                        }
                    }
                    Debug.LogWarning("[Boot] Resource verification failed: " + error);
                    BootUpdateSession.Report("Failed", .45f, -1, error);
                    BootUpdateSession.Controls(retry: () => retry = true);
                    while (!retry) yield return null;
                    BootUpdateSession.Controls();
                    BootReleaseStore.RetryPinnedOnline();
                    // The descriptor stays pinned after DLL load. Retry only this resource version.
                }
            }
            finally { _running = false; BootUpdateSession.Controls(); }
        }
    }
}
