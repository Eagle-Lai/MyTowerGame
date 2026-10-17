using System;
using System.Collections.Generic;
using System.IO;
using SimpleJSON;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    public static class BalanceEvidenceTools
    {
        /// <summary>Offline predictions use precisely the same evaluator as actual settlement.</summary>
        public static string EvaluateOfflineReports(string directory)
        {
            int evaluated = 0, failures = 0;
            var summary = new JSONArray();
            foreach (string path in Directory.GetFiles(directory, "result.json", SearchOption.AllDirectories))
            {
                JSONNode node = JSON.Parse(File.ReadAllText(path));
                if (!node["metrics"].IsObject || !node["ratingProfile"].IsObject) continue;
                var metrics = JsonUtility.FromJson<LevelRunMetrics>(node["metrics"].ToString());
                var profile = JsonUtility.FromJson<LevelRatingProfile>(node["ratingProfile"].ToString());
                LevelRatingResult rating = LevelRatingEvaluator.Evaluate(profile, metrics);
                node["predictionStars"] = rating.stars;
                node["ratingStatus"] = "C# LevelRatingEvaluator; offline prediction, not Unity reachability certification";
                node["ratingResult"] = JSON.Parse(JsonUtility.ToJson(rating));
                File.WriteAllText(path, node.ToString(2), new System.Text.UTF8Encoding(false));
                JSONNode s = new JSONObject(); s["profileId"] = node["profileId"].Value;
                s["levelId"] = node["levelId"].AsInt; s["strategyId"] = node["strategyId"].Value;
                s["stars"] = rating.stars; s["valid"] = rating.valid;
                s["combatMs"] = metrics.combatElapsedMs; s["parMs"] = profile.parCombatTimeMs;
                s["hp"] = metrics.hp; s["leaked"] = metrics.leaked; s["gold"] = node["balance"].AsInt;
                s["planHash"] = profile.planHash; s["path"] = path;
                s["reasons"] = JSON.Parse(JsonUtility.ToJson(rating))["reasons"];
                summary.Add(s); evaluated++; if (!rating.valid) failures++;
            }
            JSONNode output = new JSONObject(); output["evaluated"] = evaluated; output["invalidResults"] = failures;
            output["evaluator"] = "FTProject.LevelRatingEvaluator"; output["coverage"] = "offline_prediction_only";
            output["results"] = summary;
            File.WriteAllText(Path.Combine(directory, "rated-matrix.json"), output.ToString(2), new System.Text.UTF8Encoding(false));
            return output.ToString();
        }

        public static string ValidatePrefabContract()
        {
            var results = new JSONArray();
            foreach (string name in new[] { "LevelDetailView", "LevelClearView" })
            {
                string[] guids = AssetDatabase.FindAssets(name + " t:Prefab", new[] { "Assets/Prefabs" });
                foreach (string guid in guids)
                {
                    string path = AssetDatabase.GUIDToAssetPath(guid);
                    if (Path.GetFileNameWithoutExtension(path) != name) continue;
                    GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                    var transforms = prefab.GetComponentsInChildren<Transform>(true);
                    JSONNode entry = new JSONObject(); entry["path"] = path; entry["stars"] = new JSONArray();
                    for (int i = 1; i <= 5; i++)
                    {
                        bool found = Array.Exists(transforms, t => t.name == "Star" + i || t.name == "CurrentStar" + i);
                        entry["stars"].Add(found);
                    }
                    results.Add(entry);
                }
            }
            return results.ToString();
        }

        public static string CaptureWorkbench(string path)
        {
            var window = EditorWindow.GetWindow<LevelBalanceWorkbench>();
            window.Focus(); window.Repaint();
            EditorApplication.delayCall += () =>
            {
                try
                {
                    Rect rect = window.position;
                    Color[] pixels = UnityEditorInternal.InternalEditorUtility.ReadScreenPixel(rect.position, (int)rect.width, (int)rect.height);
                    if (pixels == null || pixels.Length == 0) throw new IOException("Editor capture returned no pixels.");
                    Color first = pixels[0];
                    bool varied = false;
                    for (int i = 0; i < pixels.Length; i += Math.Max(1, pixels.Length / 4096))
                        if (Mathf.Abs(pixels[i].r - first.r) + Mathf.Abs(pixels[i].g - first.g) + Mathf.Abs(pixels[i].b - first.b) > .08f)
                        { varied = true; break; }
                    if (!varied) throw new IOException("Editor capture is uniform/blank. Restore Unity on an accessible Windows desktop before taking a workbench screenshot.");
                    var texture = new Texture2D((int)rect.width, (int)rect.height, TextureFormat.RGB24, false);
                    texture.SetPixels(pixels); texture.Apply();
                    Directory.CreateDirectory(Path.GetDirectoryName(path)); File.WriteAllBytes(path, texture.EncodeToPNG());
                    UnityEngine.Object.DestroyImmediate(texture);
                }
                catch (Exception ex)
                {
                    Directory.CreateDirectory(Path.GetDirectoryName(path));
                    var status = new JSONObject(); status["captured"] = false; status["error"] = ex.Message;
                    File.WriteAllText(path + ".status.json", status.ToString(2));
                    Debug.LogWarning("[BalanceEvidence] " + ex.Message);
                }
            };
            return "Screenshot queued after editor repaint: " + path;
        }
    }
}
