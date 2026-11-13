using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using SimpleJSON;
using UnityEditor;
using UnityEngine;
using AStar;

namespace FTProject.EditorTools
{
    // Opt-in, read-only observations of an isolated balance replay. No gameplay changes.
    [InitializeOnLoad]
    public static class TerminalPressureProbe
    {
        private static readonly FieldInfo Enemies = typeof(CombatSystem).GetField("_enemies", BindingFlags.NonPublic | BindingFlags.Instance);
        private static readonly FieldInfo Path = typeof(BaseEnemy).GetField("_path", BindingFlags.NonPublic | BindingFlags.Instance);
        private static readonly FieldInfo Index = typeof(BaseEnemy).GetField("_pathIndex", BindingFlags.NonPublic | BindingFlags.Instance);
        private static readonly Dictionary<int, JSONNode> Waves = new Dictionary<int, JSONNode>();
        private static readonly Dictionary<string, Dictionary<int, JSONNode>> Runs = new Dictionary<string, Dictionary<int, JSONNode>>();
        private static string RunId;
        private static string Output;
        private static bool Attached;
        static TerminalPressureProbe() { EditorApplication.update += Update; }
        public static void Arm(string output)
        {
            SessionState.SetString("FT.TerminalPressure.Output", output);
        }
        private static void Update()
        {
            string output = SessionState.GetString("FT.TerminalPressure.Output", "");
            if (!EditorApplication.isPlaying || !BalancePlayModeVerifier.Running || string.IsNullOrEmpty(output)) return;
            if (!Attached && CombatSystem.Instance != null && Configs.IsLoaded)
            {
                Output = output; Waves.Clear(); Runs.Clear(); Attached = true;
                EventDispatcher.AddEventListener(EventName.UpdateEvent, Sample);
                EventDispatcher.AddEventListener<BaseEnemy, float>(EventName.EnemyKilledEvent, Killed);
                EventDispatcher.AddEventListener<BaseEnemy, int>(EventName.EnemyReachedEndEvent, Leaked);
            }
            if (Attached) Flush();
        }
        private static JSONNode Layer(BaseEnemy enemy)
        {
            string id = GameFlowManager.Instance.RunMetrics.runId;
            if (id != RunId)
            {
                RunId = id; Waves.Clear(); Runs[id] = new Dictionary<int, JSONNode>();
            }
            int wave = GameFlowManager.Instance.CurrentRoundIndex;
            JSONNode row;
            if (!Waves.TryGetValue(wave, out row))
            {
                row = new JSONObject(); row["wave"] = wave;
                foreach (string key in new[] { "ground", "air" })
                {
                    row[key] = new JSONObject(); row[key]["maxAlive"] = 0; row[key]["maxEhp"] = 0;
                    row[key]["minMargin"] = 1000000.0; row[key]["leaks"] = 0; row[key]["killed"] = 0;
                }
                Waves[wave] = row; Runs[id][wave] = row;
            }
            return row[enemy.Config.IsFlying ? "air" : "ground"];
        }
        private static float Remaining(BaseEnemy e)
        {
            if (e.Config.IsFlying)
                return Vector2.Distance(e.Position, AStarManager.Instance.TargetPoint.Center) / Configs.Global.CellSize;
            var path = Path.GetValue(e) as IList<Point>;
            int index = (int)Index.GetValue(e);
            if (path == null || index >= path.Count) return 0;
            float remaining = Vector2.Distance(e.Position, path[index].Center) / Configs.Global.CellSize;
            remaining += path.Count - index - 1; // Current movement graph uses cardinal unit edges.
            return remaining;
        }
        private static void Sample()
        {
            if (!Attached || !BalancePlayModeVerifier.Running || !SaveManager.IsTestStorage || CombatSystem.Instance == null || GameFlowManager.Instance == null) return;
            var enemies = Enemies.GetValue(CombatSystem.Instance) as List<BaseEnemy>;
            int ground = 0, air = 0; double ge = 0, ae = 0; JSONNode g = null, a = null;
            foreach (var e in enemies)
            {
                if (e == null || !e.IsAlive || e.Config == null) continue;
                // Run and wave cannot change during this read-only callback. Reuse
                // the two layer nodes: RunMetrics returns a deep copy of the ledger.
                var layer = e.Config.IsFlying ? a : g;
                if (layer == null) layer = Layer(e);
                if (e.Config.IsFlying) a = layer; else g = layer;
                if (Remaining(e) > 3.00001f) continue;
                double ehp = e.CurrentHp / Math.Max(.000001, 1 - e.Config.Armor);
                if (e.Config.IsFlying) { air++; ae += ehp; } else { ground++; ge += ehp; }
            }
            if (g != null) { g["maxAlive"] = Math.Max(g["maxAlive"].AsInt, ground); g["maxEhp"] = Math.Max(g["maxEhp"].AsDouble, ge); }
            if (a != null) { a["maxAlive"] = Math.Max(a["maxAlive"].AsInt, air); a["maxEhp"] = Math.Max(a["maxEhp"].AsDouble, ae); }
        }
        private static void Killed(BaseEnemy e, float reward)
        {
            if (!Attached || !SaveManager.IsTestStorage) return;
            var layer = Layer(e); layer["killed"] = layer["killed"].AsInt + 1;
            layer["minMargin"] = Math.Min(layer["minMargin"].AsDouble, Remaining(e));
        }
        private static void Leaked(BaseEnemy e, int damage)
        {
            if (!Attached || !SaveManager.IsTestStorage) return;
            var layer = Layer(e); layer["leaks"] = layer["leaks"].AsInt + 1;
        }
        private static void Flush()
        {
            var result = new JSONArray(); foreach (var run in Runs)
            {
                var row = new JSONObject(); row["runId"] = run.Key; row["waves"] = new JSONArray();
                foreach (var wave in run.Value) row["waves"].Add(wave.Value);
                result.Add(row);
            }
            File.WriteAllText(Output, result.ToString(2));
        }
    }
}
