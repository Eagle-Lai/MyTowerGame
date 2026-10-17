using System;
using System.Collections.Generic;
using System.Linq;
using System.IO;
using SimpleJSON;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// Optional scenarios for BalancePlayModeVerifier. Uses the real selection/quit events,
    /// durable backend, tower transactions and frozen clocks; never changes run evidence.
    /// </summary>
    public static class BalanceCheckpointVerifier
    {
        private static string _scenario;
        private static int _wave;
        private static bool _injected, _waitingForRestore, _restored;
        private static double _restoreStarted;
        private static float _speed;
        private static int _operationRollbackWave;
        private static LevelSnapshot _expected;
        private static JSONNode _checks;
        public static JSONNode CurrentChecks { get { return _checks != null ? JSON.Parse(_checks.ToString()) : new JSONObject(); } }
        public static int ConsumeOperationRollbackWave() { int wave = _operationRollbackWave; _operationRollbackWave = 0; return wave; }

        public static void Begin(GameFlowManager flow, JSONNode request)
        {
            _scenario = request["checkpointScenario"].Value ?? "";
            _speed = request["speed"].AsFloat > 0 ? request["speed"].AsFloat : 1f;
            _wave = request["checkpointWave"].AsInt > 0 ? request["checkpointWave"].AsInt : 2;
            _injected = false; _waitingForRestore = false; _restored = false; _expected = null;
            _operationRollbackWave = 0;
            _checks = new JSONObject(); _checks["scenario"] = _scenario ?? "";
            _checks["coverage"] = "Real PlayMode events and persistent checkpoint; no run metrics or funds injected";
            _checks["checks"] = new JSONArray();
            if (!string.IsNullOrEmpty(_scenario) && !SaveManager.IsTestStorage) throw new InvalidOperationException("Checkpoint verification requires isolated test storage");
            if (_scenario != "" && _scenario != "boundary_resume" && _scenario != "half_wave_rollback" && _scenario != "terminal_duplicate" && _scenario != "speed_baseline") throw new ArgumentException("Unknown checkpointScenario: " + _scenario);
        }

        /// <summary>False means stop this editor-update's simulation steps while real re-entry realizes.</summary>
        public static bool BeforeStep(GameFlowManager flow)
        {
            if (!_waitingForRestore) return true;
            if (EditorApplication.timeSinceStartup - _restoreStarted > 20) throw new TimeoutException("Checkpoint selection/re-entry did not reach Preparing");
            if (flow.State != GameFlowState.Preparing) return false;
            Check(flow.RunMetrics != null && flow.RunMetrics.runId == _expected.metrics.runId, "same runId restored");
            Check(flow.CurrentRoundIndex == _expected.roundCursor, "next wave cursor restored without replay");
            Check(PlayerDataManager.Instance.Gold == _expected.gold && PlayerDataManager.Instance.Hp == _expected.hp && PlayerDataManager.Instance.MaxHp == _expected.maxHp, "gold and HP restored from the same boundary");
            Check(PlayerDataManager.Instance.TotalKilled == _expected.metrics.killed && PlayerDataManager.Instance.TotalLeaked == _expected.metrics.leaked, "player kill/leak HUD statistics restored");
            Check(JsonUtility.ToJson(flow.RunMetrics) == JsonUtility.ToJson(_expected.metrics), "all run and wave evidence restored exactly");
            Check(GameClock.CombatElapsedSeconds == _expected.metrics.combatElapsedSeconds && GameClock.LevelElapsedSeconds == _expected.metrics.levelElapsedSeconds, "raw fractional clocks restored exactly; offline time excluded");
            Check(TowerSignature() == TowerSignature(_expected.towers), "every tower restored; no partial layout accepted");
            Check(TowerRuntimeSignature() == TowerRuntimeSignature(_expected.towers), "tower cooldown, search phase and muzzle pose restored exactly");
            AStarManager.Instance.ProcessRefresh();
            Check(AStarManager.Instance.CurrentPathLength > 0, "restored tower layout has a legal path");
            _waitingForRestore = false; _restored = true;
            Time.timeScale = 1; GameClock.Speed = _speed; GameClock.SetBackground(false);
            // Runtime restores the actual remaining automatic wait. A half-wave checkpoint
            // was captured after this frame's Combat phase, inside OnStartRequest. Replay
            // its remaining Flow phase before the next clock/Combat step, exactly as the
            // same-frame LateUpdate does after the real UI request in normal play.
            if (_scenario != "boundary_resume")
            {
                _operationRollbackWave = _expected.roundCursor + 1;
                EventDispatcher.TriggerEvent(EventName.StartRoundRequestEvent);
                flow.StepManualSimulation();
            }
            _checks["resumeWaitingPolicy"] = _scenario == "boundary_resume" ? "Runtime restores persisted remaining automatic wait; no reflection or timer injection" : "Real Next request followed by original frame's remaining Flow phase; no extra clock or Combat step";
            return true;
        }

        public static void AfterStep(GameFlowManager flow)
        {
            if (_injected || string.IsNullOrEmpty(_scenario) || _scenario == "terminal_duplicate" || _scenario == "speed_baseline") return;
            bool boundary = _scenario == "boundary_resume" && flow.State == GameFlowState.Preparing && flow.CurrentRoundIndex == _wave;
            bool halfWave = false;
            if (_scenario == "half_wave_rollback" && flow.State == GameFlowState.RoundRunning && flow.CurrentRoundIndex == _wave)
            {
                var run = flow.RunMetrics;
                var wave = run != null && run.waves != null && run.waves.Count > 0 ? run.waves[run.waves.Count - 1] : null;
                halfWave = wave != null && wave.successfulSpawned >= Math.Max(2, wave.expected / 2);
            }
            if (!boundary && !halfWave) return;
            _expected = JsonUtility.FromJson<LevelSnapshot>(JsonUtility.ToJson(SaveManager.Instance.Snapshot));
            Check(_expected.valid && _expected.formatVersion == 2, "durable checkpoint exists before interruption");
            if (halfWave)
            {
                var live = flow.RunMetrics;
                Check(live.successfulSpawned > _expected.metrics.successfulSpawned, "interruption occurs after real half-wave spawning");
                Check(GameClock.CombatElapsedSeconds > _expected.metrics.combatElapsedSeconds, "half-wave accumulated combat time before rollback");
                var tower = TowerManager.Instance.Towers.FirstOrDefault(t => t != null && t.Config != null && t.Cell != null);
                int gold = PlayerDataManager.Instance.Gold;
                if (tower != null)
                {
                    int refund = tower.Config.SellPrice;
                    Check(TowerManager.Instance.Sell(tower), "half-wave tower sale is a real legal transaction");
                    Check(PlayerDataManager.Instance.Gold == gold + refund, "half-wave sale changes actual cash before rollback");
                }
                flow.SaveSnapshotNow();
                Check(JsonUtility.ToJson(SaveManager.Instance.Snapshot) == JsonUtility.ToJson(_expected), "half-wave save cannot overwrite the complete checkpoint");
            }
            _injected = true; _waitingForRestore = true; _restoreStarted = EditorApplication.timeSinceStartup;
            int level = flow.Level.Id;
            // Go through the same user-facing routes, including the deferred level-loading frame.
            flow.QuitToSelect();
            Check(flow.State == GameFlowState.None, "quit reaches selection state");
            Check(JsonUtility.ToJson(SaveManager.Instance.Snapshot) == JsonUtility.ToJson(_expected), "quit preserves a coherent boundary checkpoint");
            // Close and reopen the actual SQLite/JSON backend before re-entry. A successful
            // in-memory restore alone would miss serialization and durable-save regressions.
            string context = SessionState.GetString("FT.Balance.TestStorageContext", "");
            if (string.IsNullOrEmpty(context)) context = Path.GetFileName(Path.GetDirectoryName(SaveManager.Instance.StorageLocation));
            using (SaveManager.Instance.SetTestStorageContext(context)) { }
            Check(JsonUtility.ToJson(SaveManager.Instance.Snapshot) == JsonUtility.ToJson(_expected), "checkpoint survives a real backend close and reopen");
            EventDispatcher.TriggerEvent<int>(EventName.SelectLevelRequestEvent, level);
        }

        public static JSONNode Complete(GameFlowManager flow)
        {
            if (_checks == null) { _checks = new JSONObject(); _checks["checks"] = new JSONArray(); }
            if (_scenario == "boundary_resume" || _scenario == "half_wave_rollback")
            {
                Check(_injected && _restored && !_waitingForRestore, "interruption and real re-entry completed");
                _checks["resumedRunId"] = _expected != null && _expected.metrics != null ? _expected.metrics.runId : "";
            }
            if (_scenario == "terminal_duplicate")
            {
                var metrics = flow.RunMetrics;
                Check(metrics != null && metrics.completedWaveCount == metrics.expectedWaveCount && metrics.victory, "all waves completed before terminal idempotency test");
                int level = flow.Level.Id;
                var before = SaveManager.Instance.Data.Find(level);
                Check(before != null && before.committedRunIds.Contains(metrics.runId), "terminal run was atomically committed");
                string progress = JsonUtility.ToJson(before);
                int gold = PlayerDataManager.Instance.Gold;
                var result = LevelRatingEvaluator.Evaluate(flow.RatingProfile, metrics);
                Check(SaveManager.Instance.RecordClear(level, result), "duplicate formal commit recognizes already committed runId");
                EventDispatcher.TriggerEvent<bool>(EventName.GameOverEvent, true);
                flow.StepManualSimulation();
                Check(JsonUtility.ToJson(SaveManager.Instance.Data.Find(level)) == progress, "duplicate victory does not increase clears, stars, times or evidence");
                Check(PlayerDataManager.Instance.Gold == gold, "duplicate victory does not award gold again");
                Check(!SaveManager.Instance.HasSnapshot, "committed final snapshot remains invalid");
                _injected = true;
            }
            _checks["passed"] = true;
            _checks["finalTowerSignature"] = TowerSignature();
            _checks["finalTowerRuntimeSignature"] = TowerRuntimeSignature();
            _checks["combatElapsedSeconds"] = GameClock.CombatElapsedSeconds;
            _checks["levelElapsedSeconds"] = GameClock.LevelElapsedSeconds;
            return JSON.Parse(_checks.ToString());
        }

        /// <summary>
        /// Compare completed run entries after recording them. The caller must use the same
        /// operationsPath and normalized simulation step (baseStep / speed) at 1x, 2x and 3x.
        /// runId and wall time intentionally differ; all gameplay evidence must agree.
        /// </summary>
        public static JSONNode CompareSpeedResults(IEnumerable<JSONNode> results)
        {
            var report = new JSONObject(); report["method"] = "Same operation replay and fixed simulation step; unscaled input step is divided by speed"; report["comparisons"] = new JSONArray();
            var groups = results.Where(r => !string.IsNullOrEmpty(r["speedComparisonGroup"].Value)).GroupBy(r => r["speedComparisonGroup"].Value);
            foreach (var group in groups)
            {
                var runs = group.OrderBy(r => r["speed"].AsFloat).ToList();
                var entry = new JSONObject(); entry["group"] = group.Key;
                bool complete = runs.Count == 3 && runs.Select(r => r["speed"].AsInt).SequenceEqual(new[] { 1, 2, 3 });
                entry["complete"] = complete;
                bool same = complete;
                if (complete)
                {
                    string first = ComparisonSignature(runs[0]);
                    foreach (var run in runs.Skip(1)) same &= ComparisonSignature(run) == first;
                }
                entry["passed"] = same; report["comparisons"].Add(entry);
            }
            report["passed"] = report["comparisons"].Count > 0 && report["comparisons"].Children.All(n => n["passed"].AsBool);
            report["continuationComparisons"] = new JSONArray();
            var all = results.ToList();
            foreach (var run in all.Where(n => new[] { "boundary_resume", "half_wave_rollback", "terminal_duplicate" }.Contains(n["checkpointChecks"]["scenario"].Value)))
            {
                var baseline = all.FirstOrDefault(n => n["checkpointChecks"]["scenario"].Value == "speed_baseline" && n["speed"].AsInt == 1 && n["levelId"].AsInt == run["levelId"].AsInt && n["profileId"].Value == run["profileId"].Value && n["strategy"].Value == run["strategy"].Value);
                var entry = new JSONObject(); entry["scenario"] = run["checkpointChecks"]["scenario"].Value;
                entry["passed"] = baseline != null && ComparisonSignature(baseline) == ComparisonSignature(run);
                entry["comparison"] = "Every raw double clock, wave evidence, cash, tower phases, kills/leaks and final rating; runId normalized";
                report["continuationComparisons"].Add(entry);
            }
            if (report["continuationComparisons"].Count > 0) report["passed"] = report["passed"].AsBool && report["continuationComparisons"].Children.All(n => n["passed"].AsBool);
            return report;
        }

        private static string ComparisonSignature(JSONNode entry)
        {
            LevelRatingResult result = JsonUtility.FromJson<LevelRatingResult>(entry.ToString());
            if (result == null || result.metrics == null) return "missing evidence";
            result.metrics.runId = "same replay";
            // End times and economy in every wave remain in the comparison.
            return result.stars + "|" + result.valid + "|" + JsonUtility.ToJson(result.metrics) + "|" + entry["finalGold"].Value + "|" + entry["checkpointChecks"]["finalTowerSignature"].Value + "|" + entry["checkpointChecks"]["finalTowerRuntimeSignature"].Value;
        }
        private static void Check(bool condition, string description)
        {
            JSONNode item = new JSONObject(); item["description"] = description; item["passed"] = condition;
            _checks["checks"].Add(item);
            if (!condition) { _checks["passed"] = false; throw new InvalidOperationException("Checkpoint verification failed: " + description); }
        }
        private static string TowerSignature()
        {
            return string.Join(";", TowerManager.Instance.Towers.Where(t => t != null && t.Cell != null && t.Config != null).Select(t => t.Cell.Row + ":" + t.Cell.Col + ":" + t.Config.Type + ":" + t.Config.Level).OrderBy(s => s, StringComparer.Ordinal));
        }
        private static string TowerSignature(IEnumerable<TowerSnapshot> towers)
        {
            return string.Join(";", towers.Select(t => t.row + ":" + t.col + ":" + t.type + ":" + t.level).OrderBy(s => s, StringComparer.Ordinal));
        }
        private static string TowerRuntimeSignature()
        {
            var snapshots = new List<TowerSnapshot>();
            foreach (var tower in TowerManager.Instance.Towers)
            {
                if (tower == null || tower.Config == null || tower.Cell == null) continue;
                var item = new TowerSnapshot { row = tower.Cell.Row, col = tower.Cell.Col, type = tower.Config.Type, level = tower.Config.Level };
                tower.CaptureCheckpointState(item); snapshots.Add(item);
            }
            return TowerRuntimeSignature(snapshots);
        }
        private static string TowerRuntimeSignature(IEnumerable<TowerSnapshot> towers)
        {
            return string.Join(";", towers.OrderBy(t => t.row).ThenBy(t => t.col).Select(t => JsonUtility.ToJson(t)));
        }
    }
}
