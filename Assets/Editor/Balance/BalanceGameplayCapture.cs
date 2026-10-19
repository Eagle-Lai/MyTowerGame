using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using SimpleJSON;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    // Captures the actual battle board and HUD. The replay holds game simulation
    // during layout/font rendering; no run evidence, gold or enemies are injected.
    [InitializeOnLoad]
    public static class BalanceGameplayCapture
    {
        private static readonly BindingFlags Flags = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;
        private static EditorWindow _view;
        private static object _group;
        private static PropertyInfo _selection;
        private static int _oldIndex, _originalCount, _index, _frame, _phase;
        private static readonly List<int> Added = new List<int>();
        private static Language _oldLanguage;
        private static string _out, _pending;
        private static double _started;
        private static JSONArray _rows;
        public static bool Running { get; private set; }

        static BalanceGameplayCapture() { EditorApplication.update += Update; }

        public static void Begin(string directory)
        {
            if (Running || !EditorApplication.isPlaying || !SaveManager.IsTestStorage)
                throw new InvalidOperationException("Battle capture requires an isolated PlayMode scene.");
            _out = directory; Directory.CreateDirectory(_out); Added.Clear(); _rows = new JSONArray();
            _oldLanguage = LanguageManager.Current;
            var assembly = typeof(Editor).Assembly;
            var viewType = assembly.GetType("UnityEditor.GameView");
            _view = EditorWindow.GetWindow(viewType);
            _selection = viewType.GetProperty("selectedSizeIndex", Flags);
            _oldIndex = (int)_selection.GetValue(_view, null);
            var sizesType = assembly.GetType("UnityEditor.GameViewSizes");
            var sizes = sizesType.BaseType.GetProperty("instance", BindingFlags.Public | BindingFlags.Static).GetValue(null, null);
            _group = sizesType.GetProperty("currentGroup", Flags).GetValue(sizes, null);
            _originalCount = (int)_group.GetType().GetMethod("GetTotalCount").Invoke(_group, null);
            _index = _phase = 0; _started = EditorApplication.timeSinceStartup; Running = true;
        }

        private static void Update()
        {
            if (!Running) return;
            try
            {
                if (!EditorApplication.isPlaying || EditorApplication.timeSinceStartup - _started > 90)
                    throw new TimeoutException("Actual battle screenshot rendering timed out.");
                int width = _index < 3 ? 1920 : 1024, height = _index < 3 ? 1080 : 768;
                var language = new[] { Language.English, Language.ChineseSimplified, Language.ChineseTraditional }[_index % 3];
                if (_phase == 0)
                {
                    var assembly = typeof(Editor).Assembly;
                    var type = assembly.GetType("UnityEditor.GameViewSize");
                    var mode = Enum.Parse(assembly.GetType("UnityEditor.GameViewSizeType"), "FixedResolution");
                    var size = Activator.CreateInstance(type, new object[] { mode, width, height, "Balance temporary " + width + "x" + height });
                    int selected = (int)_group.GetType().GetMethod("GetTotalCount").Invoke(_group, null);
                    _group.GetType().GetMethod("AddCustomSize").Invoke(_group, new[] { size }); Added.Add(selected);
                    _selection.SetValue(_view, selected, null);
                    LanguageManager.SetLanguage(language); Canvas.ForceUpdateCanvases(); _view.Repaint();
                    _frame = Time.frameCount; _phase = 1; return;
                }
                if (_phase == 1)
                {
                    _view.Repaint(); if (Time.frameCount < _frame + 5) return;
                    if (Screen.width != width || Screen.height != height)
                        throw new InvalidOperationException("GameView resolution did not become " + width + "x" + height);
                    _pending = Path.Combine(_out, "battle-" + language.ToCode() + "-" + width + "x" + height + ".png");
                    ScreenCapture.CaptureScreenshot(_pending); _phase = 2; _frame = Time.frameCount; return;
                }
                if (!File.Exists(_pending) || Time.frameCount < _frame + 2) return;
                var bytes = File.ReadAllBytes(_pending);
                int pngWidth = (bytes[16] << 24) | (bytes[17] << 16) | (bytes[18] << 8) | bytes[19];
                int pngHeight = (bytes[20] << 24) | (bytes[21] << 16) | (bytes[22] << 8) | bytes[23];
                if (pngWidth != width || pngHeight != height) throw new InvalidDataException("Captured PNG resolution mismatch.");
                var row = new JSONObject(); row["image"] = Path.GetFileName(_pending); row["width"] = width; row["height"] = height;
                row["language"] = language.ToCode(); row["wave"] = GameFlowManager.Instance.CurrentRoundIndex;
                row["towers"] = TowerManager.Instance.Count; row["alive"] = CombatSystem.Instance.AliveEnemyCount;
                row["gold"] = PlayerDataManager.Instance.Gold; row["hp"] = PlayerDataManager.Instance.Hp; _rows.Add(row);
                if (++_index == 6) Finish(null); else _phase = 0;
            }
            catch (Exception error) { Finish(error.ToString()); }
        }

        private static void Finish(string error)
        {
            try
            {
                LanguageManager.SetLanguage(_oldLanguage);
                _selection.SetValue(_view, _oldIndex, null);
                for (int i = Added.Count - 1; i >= 0; i--)
                {
                    // Unity's RemoveCustomSize accepts the combined built-in/custom index.
                    _group.GetType().GetMethod("RemoveCustomSize").Invoke(_group, new object[] { Added[i] });
                }
                if ((int)_group.GetType().GetMethod("GetTotalCount").Invoke(_group, null) != _originalCount)
                    throw new InvalidOperationException("Temporary GameView sizes were not fully removed.");
                _view.Repaint();
            }
            catch (Exception restore) { error = (error ?? "") + "\nRestore: " + restore; }
            var report = new JSONObject(); report["passed"] = error == null && _rows.Count == 6;
            report["coverage"] = "Actual live battle and HUD, two actual GameView resolutions and three languages; simulation held while rendering; original GameView size and language restored.";
            report["results"] = _rows; if (error != null) report["error"] = error;
            File.WriteAllText(Path.Combine(_out, "gameplay-capture.json"), report.ToString(2)); Running = false;
        }
    }
}
