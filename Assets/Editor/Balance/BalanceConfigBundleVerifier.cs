#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using SimpleJSON;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>Build and read the real target-platform config bundle without changing asset labels.</summary>
    public static class BalanceConfigBundleVerifier
    {
        public static string Start()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling ||
                EditorApplication.isUpdating || EditorUtility.scriptCompilationFailed || BalanceWorkbenchProcess.Running)
                throw new InvalidOperationException("Config bundle verification requires idle EditMode with clean scripts.");
            string directory = Path.Combine(BalanceWorkbenchProcess.ProjectRoot,
                "Library/BalanceWorkbench/config-bundle-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff"));
            Directory.CreateDirectory(directory);
            string evidence = Path.Combine(BalanceWorkbenchProcess.ProjectRoot, "Docs/BalanceEvidence/30x25/config-bundle.json");
            Directory.CreateDirectory(Path.GetDirectoryName(evidence));
            var state = new JSONObject(); state["phase"] = "queued"; state["passed"] = false;
            state["output"] = directory; state["target"] = EditorUserBuildSettings.activeBuildTarget.ToString();
            state["startedUtc"] = DateTime.UtcNow.ToString("O");
            File.WriteAllText(evidence, state.ToString(2));
            // Background editors still pump update while inspector delayCall can
            // remain pending until a layout pass. Run exactly once on update.
            EditorApplication.CallbackFunction deferred = null;
            deferred = () => { EditorApplication.update -= deferred; Verify(directory, evidence, state); };
            EditorApplication.update += deferred;
            return evidence;
        }

        private static void Verify(string directory, string evidence, JSONNode state)
        {
            AssetBundle bundle = null;
            try
            {
                state["phase"] = "building"; File.WriteAllText(evidence, state.ToString(2));
                var addresses = ResTable.All.Where(p => p.Value.Bundle == ResBundle.Config).ToArray();
                string[] paths = addresses.Select(p => p.Value.EditorPath).Distinct().OrderBy(p => p, StringComparer.Ordinal).ToArray();
                foreach (string path in paths)
                    if (AssetDatabase.LoadAssetAtPath<TextAsset>(path) == null) throw new InvalidDataException("Config is not a TextAsset: " + path);
                var build = new AssetBundleBuild { assetBundleName = ResBundle.Config, assetNames = paths };
                var manifest = BuildPipeline.BuildAssetBundles(directory, new[] { build },
                    BuildAssetBundleOptions.ChunkBasedCompression | BuildAssetBundleOptions.UseContentHash | BuildAssetBundleOptions.StrictMode,
                    EditorUserBuildSettings.activeBuildTarget);
                if (manifest == null) throw new InvalidDataException("Target config bundle build returned no manifest.");
                bundle = AssetBundle.LoadFromFile(Path.Combine(directory, ResBundle.Config));
                if (bundle == null) throw new InvalidDataException("Target config bundle cannot be loaded in this editor.");
                state["tables"] = new JSONArray();
                var json = new Dictionary<string, string>(StringComparer.Ordinal);
                foreach (var pair in addresses)
                {
                    var asset = bundle.LoadAsset<TextAsset>(pair.Value.Asset);
                    if (asset == null) throw new InvalidDataException("Runtime bundle lookup failed: " + pair.Key + " / " + pair.Value.Asset);
                    string expected = File.ReadAllText(Path.Combine(BalanceWorkbenchProcess.ProjectRoot, pair.Value.EditorPath)).TrimStart('\uFEFF').Replace("\r\n", "\n");
                    if (asset.text.TrimStart('\uFEFF').Replace("\r\n", "\n") != expected)
                        throw new InvalidDataException("Bundle content is stale: " + pair.Key);
                    json[Path.GetFileNameWithoutExtension(pair.Value.EditorPath)] = asset.text.TrimStart('\uFEFF');
                    var row = new JSONObject(); row["logicalName"] = pair.Key; row["asset"] = pair.Value.Asset; row["matchesFormalSource"] = true;
                    state["tables"].Add(row);
                }
                // 【2026-11-01】评级表与 runtimeContentHash 已删除：这里只校验关卡库存完整性。
                var scenes = new cfg.TBSceneInfo(JSON.Parse(json["tbsceneinfo"]));
                if (scenes.DataList == null || scenes.DataList.Count == 0 ||
                    scenes.DataList.Any(level => level.RoundList == null || level.RoundList.Count == 0))
                    throw new InvalidDataException("Loaded bundle level inventory is empty or contains a level without rounds.");
                state["levelCount"] = scenes.DataList.Count;
                state["tableCount"] = json.Count; state["phase"] = "complete"; state["passed"] = true;
                state["coverage"] = "Real active-target config AssetBundle build, runtime address lookup, and every TextAsset compared byte-for-byte with the formal JSON. This does not certify a full Android player/device run.";
            }
            catch (Exception error) { state["phase"] = "failed"; state["error"] = error.ToString(); }
            finally
            {
                if (bundle != null) bundle.Unload(true);
                state["finishedUtc"] = DateTime.UtcNow.ToString("O"); File.WriteAllText(evidence, state.ToString(2));
            }
        }
    }
}
#endif
