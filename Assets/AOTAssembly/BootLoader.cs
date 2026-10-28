using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

namespace FTProject.AOT
{
    // APK-owned shell. No references to any hot-update assembly are permitted here.
    public class BootLoader : MonoBehaviour
    {
        private const int ProbeTimeoutSeconds = 2;
        private static BootLoader _instance;
        private bool _retry;
        private void Awake()
        {
            if (_instance != null && _instance != this) { Destroy(gameObject); return; }
            _instance = this;
            FrameRatePolicy.Apply();
            BootLocalization.Initialize();
            BootUiSymbolKeeper.Ensure();
            StartCoroutine(BootRoutine());
        }
        private void OnDestroy()
        {
            if (_instance == this) { _instance = null; BootUpdateSession.Controls(); BootServerSelection.StopDiscovery(); }
        }
        private IEnumerator WaitRetry(string reason)
        {
            _retry = false;
            Debug.LogWarning("[Boot] Waiting for retry: " + reason);
            BootUpdateSession.Report("Failed", BootUpdateSession.Overall, -1, reason);
            BootUpdateSession.Controls(retry: () => _retry = true);
            while (!_retry) yield return null;
            BootUpdateSession.Controls();
        }
        private IEnumerator BootRoutine()
        {
            // Give the scene-configured HotUpdateView a frame before any IO or DLL work.
            BootUpdateSession.Report("Preparing", 0);
            yield return null;
#if UNITY_EDITOR && !FORCE_AB
            // The editor already owns the current assemblies and builds its own virtual manifest.
            // APK descriptors, staged DLLs and network availability must not affect this mode.
            BootReleaseStore.UseEditorSimulation();
            Debug.Log("[Boot] Editor simulation: current assemblies and project assets; no release server required.");
            Exception loadError = null;
#else
            while (true)
            {
                yield return BootReleaseStore.PrepareBaseline();
                if (BootReleaseStore.Error == null) break;
                yield return WaitRetry(BootReleaseStore.Error);
            }
            yield return HotUpdateAssembler.PrefetchStreamingAssetsToPersistent(null);
            while (true)
            {
                BootUpdateSession.Report("Checking", .05f);
                string winner = null;
                string manual = ReadServerOverride();
                if (!string.IsNullOrEmpty(manual))
                {
                    yield return ProbeCandidatesCo(new[] { manual }, (url, source) => winner = url, errors => Debug.LogWarning(errors));
                }
                else
                {
                    BootServerSelection.StartDiscovery();
                    yield return ProbeCandidatesCo(BootServerSelection.Candidates, (url, source) => winner = url, errors => Debug.LogWarning(errors));
                    if (winner == null)
                    {
                        float deadline = Time.realtimeSinceStartup + 2f;
                        while (!BootServerSelection.DiscoveryFinished && Time.realtimeSinceStartup < deadline) yield return null;
                        string[] discovered = BootServerSelection.TakeDiscovered();
                        if (discovered.Length > 0) yield return ProbeCandidatesCo(discovered, (url, source) => winner = url, errors => Debug.LogWarning(errors));
                    }
                    BootServerSelection.StopDiscovery();
                }
                if (winner == null)
                {
                    BootServerSelection.MarkReachabilityChecked();
                    BootReleaseStore.UseOffline(manual ?? BootServerSelection.Candidates[0]);
                    BootUpdateSession.Report("Offline", .2f, -1);
                    break;
                }
                BootServerSelection.SetSelected(winner, "release probe");
                BootServerSelection.MarkReachabilityChecked();
                var localCandidate = BootReleaseStore.Selected;
                yield return BootReleaseStore.SelectRemote(winner);
                if (BootReleaseStore.Error != null)
                {
                    if (BootReleaseStore.TryUseLocalCandidate(localCandidate, winner, BootReleaseStore.Error)) break;
                    yield return WaitRetry(BootReleaseStore.Error);
                    continue;
                }
                HotUpdateDllDownloader.Result result = null;
                yield return HotUpdateDllDownloader.DownloadAll(winner,
                    (done, total) => BootUpdateSession.Report("DLL", .1f + .2f * done / Mathf.Max(total, 1), (float)done / Mathf.Max(total, 1), done + "/" + total),
                    value => result = value);
                if (result == null || !string.IsNullOrEmpty(result.ErrorSummary) || !BootReleaseStore.VerifyDlls(BootReleaseStore.Selected))
                {
                    string reason = result?.ErrorSummary ?? "DLL set incomplete";
                    if (BootReleaseStore.TryUseLocalCandidate(localCandidate, winner, reason)) break;
                    yield return WaitRetry(reason);
                    continue;
                }
                break;
            }
            BootUpdateSession.Report("Loading DLL", .32f);
            yield return null;
            Exception loadError = null;
            try { HotUpdateAssembler.LoadHotUpdateAssemblies(null); }
            catch (Exception e) { loadError = e; }
            if (loadError != null)
            {
                // Some assemblies may already be resident. Retrying Assembly.Load is unsafe.
                Debug.LogError("[Boot] Assembly load failed; process restart required: " + loadError);
                BootUpdateSession.Report("Restart", .32f, -1, loadError.Message);
                yield break;
            }
#endif
            IHotUpdateEntry entry = HotUpdateEntryLocator.CreateEntry(out string error);
            if (entry == null) { BootUpdateSession.Report("Restart", .32f, -1, error); yield break; }
            try { entry.Start(); }
            catch (Exception e) { loadError = e; }
            if (loadError != null) { BootUpdateSession.Report("Restart", .32f, -1, loadError.Message); yield break; }
            // The inner gate owns retries and liveness; there is no wall-clock scene timeout
            // that can interrupt a healthy download or a player-paused transfer.
            bool done = false, ok = false;
            do
            {
                done = false;
                entry.EnterMainScene((success, reason) => { done = true; ok = success; error = reason; });
                while (!done) yield return null;
                if (!ok) yield return WaitRetry(error);
            } while (!ok);
        }
        private IEnumerator ProbeCandidatesCo(string[] candidates,
            Action<string, string> onWinner, Action<string> onErrorSummary)
        {
            // 每个候选一个探测槽：发出后不 yield 单发请求，统一轮询收割
            ProbeSlot[] slots = new ProbeSlot[candidates.Length];
            slotsErrorSummary = new string[candidates.Length];

            for (int i = 0; i < candidates.Length; i++)
            {
                string root = (candidates[i] ?? "").TrimEnd('/');
                string url = root + "/release.json";

                UnityWebRequest req = UnityWebRequest.Get(url);
                req.timeout = ProbeTimeoutSeconds;
                req.downloadHandler = new DownloadHandlerBuffer();

                slots[i] = new ProbeSlot { Index = i, Url = url, Request = req };
                req.SendWebRequest();   // 异步发出；并发等待靠下面的轮询
            }

            float t0 = Time.realtimeSinceStartup;

            while (true)
            {
                bool allDone = true;

                for (int i = 0; i < slots.Length; i++)
                {
                    ProbeSlot s = slots[i];
                    if (s == null || s.Done)
                    {
                        continue;
                    }

                    if (s.Request.isDone)
                    {
                        s.Done = true;
                        UnityWebRequest r = s.Request;

                        if (r.result == UnityWebRequest.Result.Success
                            && r.responseCode == 200
                            && string.IsNullOrEmpty(r.downloadHandler.text) == false)
                        {
                            // 先成功者胜出：中止其余请求，立刻返回
                            Debug.Log(string.Format(
                                "[Boot] 候选服务器 {0}/{1} 可达（并发探测耗时 {2:F2}s）：{3}",
                                s.Index + 1, slots.Length, Time.realtimeSinceStartup - t0, s.Url));
                            AbortProbeSlots(slots, s.Index);
                            onWinner(candidates[s.Index],
                                string.Format("候选 {0}/{1}", s.Index + 1, slots.Length));
                            yield break;
                        }

                        slotsErrorSummary[s.Index] = string.Format("  候选{0} {1} → {2}（HTTP {3}）",
                            s.Index + 1, s.Url, r.error, r.responseCode);
                    }
                    else
                    {
                        allDone = false;
                    }
                }

                if (allDone)
                {
                    break;
                }
                yield return null;
            }

            // 全部失败：统一中止并释放请求，再上抛错误摘要
            AbortProbeSlots(slots, -1);
            if (onErrorSummary != null)
            {
                onErrorSummary(string.Join("\n", slotsErrorSummary));
            }
        }

        /// <summary>中止并释放除胜出者以外的全部探测请求（胜出者本体用完即释；-1 = 全部释放）。</summary>
        private static void AbortProbeSlots(ProbeSlot[] slots, int winnerIndex)
        {
            for (int i = 0; i < slots.Length; i++)
            {
                ProbeSlot s = slots[i];
                if (s == null || s.Request == null)
                {
                    continue;
                }
                if (i != winnerIndex)
                {
                    s.Request.Abort();
                }
                s.Request.Dispose();
            }
        }

        private string[] slotsErrorSummary = new string[0];

        /// <summary>并发探测的单发请求槽位（Index 对应候选数组下标）。</summary>
        private class ProbeSlot
        {
            public int Index;
            public string Url;
            public UnityWebRequest Request;
            public bool Done;
        }

        /// <summary>读 persistentDataPath/server.txt 的第一行（跳过空行与 # 注释）。没有则返回 null。</summary>
        private static string ReadServerOverride()
        {
            try
            {
                string file = System.IO.Path.Combine(Application.persistentDataPath, "server.txt");
                if (System.IO.File.Exists(file) == false)
                {
                    return null;
                }

                string[] lines = System.IO.File.ReadAllLines(file);
                for (int i = 0; i < lines.Length; i++)
                {
                    string line = lines[i].Trim();
                    if (line.Length == 0 || line.StartsWith("#"))
                    {
                        continue;
                    }
                    return line.TrimEnd('/');
                }
            }
            catch (Exception)
            {
                // 读不到就当没覆盖，用常量地址
            }
            return null;
        }

    }
}
