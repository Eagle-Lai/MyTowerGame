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
