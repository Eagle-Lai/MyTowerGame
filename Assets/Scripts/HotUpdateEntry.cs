using System;
using System.Collections;
using UnityEngine;
using FTProject.AOT;

namespace FTProject
{
    public class HotUpdateEntry : IHotUpdateEntry
    {
        public static bool Started { get; private set; }
        private static bool _entering;
        public void Start()
        {
            if (Started) return;
            Started = true;
            Debug.Log("[BootSequence] DLLReady");
        }
        public void EnterMainScene(Action<bool, string> onResult)
        {
            if (_entering) { onResult(false, "Scene entry already running"); return; }
            _entering = true;
            ResLoaderRunner.Start(EnterMainCo(onResult));
        }
        private IEnumerator EnterMainCo(Action<bool, string> onResult)
        {
            try
            {
                while (true)
                {
                    bool initialized = false;
                    BootUpdateSession.Report("Initializing", .4f);
                    ResLoader.Instance.Init(() => initialized = true);
                    while (!initialized) yield return null;
                    if (ResLoader.Instance.IsReady) break;
                    var loader = ResLoader.Instance as YooAssetResLoader;
                    bool retry = false;
                    BootUpdateSession.Report("Failed", .4f, -1, loader?.LastInitError ?? "Resource initialization failed");
                    BootUpdateSession.Controls(retry: () => retry = true);
                    while (!retry) yield return null;
                    BootUpdateSession.Controls();
                    if (loader == null) { onResult(false, "No safe resource rebuild provider"); yield break; }
                    var destroy = loader.BeginRetryDestroy();
                    while (destroy != null && !destroy.IsDone) yield return null;
                    loader.CompleteRetryRebuild();
                }
                bool gated = false;
                BootHotUpdateGate.Run(() => gated = true);
                while (!gated) yield return null;
                BootUpdateSession.Controls();
                Debug.Log("[BootSequence] Main");
                ResLoader.Instance.LoadSceneAsync("Assets/Scenes/Main.unity", onResult);
            }
            finally { _entering = false; }
        }
    }
}
