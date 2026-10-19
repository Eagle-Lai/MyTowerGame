using System;
using System.Collections.Generic;
using System.Linq;
using SimpleJSON;
using Unity.Profiling;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>Bounded rendered-frame sample of a real late-wave board in isolated PlayMode.</summary>
    public static class BalanceRenderSampler
    {
        private static ProfilerRecorder _main, _gc, _batches;
        private static readonly List<double> FrameMs = new List<double>();
        private static readonly List<long> MainNs = new List<long>(), GcBytes = new List<long>(), Batches = new List<long>();
        private static int _lastFrame, _warmup, _peakAlive, _towers, _wave;
        private static double _lastWall;
        public static bool Active { get; private set; }
        public static bool Completed { get; private set; }

        public static void Reset()
        {
            Dispose(); Active = Completed = false; FrameMs.Clear(); MainNs.Clear(); GcBytes.Clear(); Batches.Clear();
            _peakAlive = _towers = _wave = 0;
        }

        public static void Begin(GameFlowManager flow)
        {
            _main = ProfilerRecorder.StartNew(ProfilerCategory.Internal, "Main Thread", 1);
            _gc = ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC Allocated In Frame", 1);
            _batches = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Batches Count", 1);
            // Flush accelerated-replay visual effects before measuring rendered combat.
            Active = true; _warmup = 120; _lastFrame = -1; _lastWall = EditorApplication.timeSinceStartup;
            _towers = TowerManager.Instance.Count; _wave = flow.CurrentRoundIndex;
        }

        public static bool NextRenderedFrame()
        {
            if (Time.frameCount == _lastFrame) return false;
            double now = EditorApplication.timeSinceStartup;
            _lastFrame = Time.frameCount;
            _peakAlive = Math.Max(_peakAlive, CombatSystem.Instance.AliveEnemyCount);
            if (_warmup-- <= 0)
            {
                FrameMs.Add((now - _lastWall) * 1000);
                if (_main.Valid) MainNs.Add(_main.LastValue);
                if (_gc.Valid) GcBytes.Add(_gc.LastValue);
                if (_batches.Valid) Batches.Add(_batches.LastValue);
            }
            _lastWall = now;
            if (FrameMs.Count >= 180) { Active = false; Completed = true; Dispose(); }
            return true;
        }

        public static JSONNode Report()
        {
            var row = new JSONObject();
            row["coverage"] = "Actual Unity Editor PlayMode rendered frames during late-wave combat; one 1/60 game step per rendered frame; editor overhead included; not Android device FPS";
            row["completed"] = Completed; row["samples"] = FrameMs.Count; row["warmupFrames"] = 120; row["wave"] = _wave;
            row["towerCount"] = _towers; row["alivePeak"] = _peakAlive;
            row["frameMs"] = JSON.Parse(JsonUtility.ToJson(new DoubleValues { values = FrameMs.ToArray() }))["values"];
            if (FrameMs.Count > 0) { var sorted = FrameMs.OrderBy(v => v).ToArray(); row["medianFrameMs"] = sorted[sorted.Length / 2]; row["p95FrameMs"] = sorted[(int)(sorted.Length * .95)]; }
            Add(row, "mainThreadNs", MainNs); Add(row, "gcAllocatedBytes", GcBytes); Add(row, "batches", Batches);
            return row;
        }
        [Serializable] private class DoubleValues { public double[] values; }
        private static void Add(JSONNode node, string key, List<long> values)
        {
            node[key] = new JSONArray(); foreach (long value in values) node[key].Add(value);
            node[key + "Available"] = values.Count > 0;
        }
        public static void Dispose() { _main.Dispose(); _gc.Dispose(); _batches.Dispose(); }
    }
}
