#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
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
                var rating = new cfg.TBLevelRating(JSON.Parse(json["tblevelrating"]));
                var calculate = typeof(Configs).GetMethod("CalculateRuntimeContentHash", BindingFlags.Static | BindingFlags.NonPublic);
                string hash = (string)calculate.Invoke(null, new object[] { json, rating.DataList });
                var scenes = new cfg.TBSceneInfo(JSON.Parse(json["tbsceneinfo"]));
                if (rating.DataList.Count != scenes.DataList.Count || rating.DataList.Any(r => r.RuntimeContentHash != hash ||
                    !scenes.DataList.Any(level => level.Id == r.Id && level.RoundList.Count == r.ExpectedWaveCount)))
                    throw new InvalidDataException("Loaded bundle ratings, level wave inventories, and content identity differ.");
                state["runtimeContentHash"] = hash; state["ratingRows"] = rating.DataList.Count;
                state["tableCount"] = json.Count; state["phase"] = "complete"; state["passed"] = true;
                state["coverage"] = "Real active-target config AssetBundle build, runtime address lookup, every TextAsset compared with formal JSON, runtime hash calculated by the production Configs method. This does not certify a full Android player/device run.";
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
