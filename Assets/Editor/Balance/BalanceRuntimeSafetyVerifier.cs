using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using SimpleJSON;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject.EditorTools
{
    /// <summary>
    /// Isolated fault-injection acceptance checks through the real flow, spawn, storage and UI.
    /// Terminal metrics are deliberately constructed fixtures, never gameplay/reachability evidence.
    /// Invoke synchronously in the initialized main scene, in isolated PlayMode, with no replay running.
    /// </summary>
    public static class BalanceRuntimeSafetyVerifier
    {
        private const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
        private static string _scenario;
        private static string _resourceFaultLocation;
        private static JSONObject _scenarioResult;
        private static JSONArray _logs;

        public static string Run(string outputPath)
        {
            if (!EditorApplication.isPlaying || !SaveManager.IsTestStorage || BalancePlayModeVerifier.Running
                || GameClock.IsManualSimulation || GameFlowManager.Instance == null)
                throw new InvalidOperationException("Requires initialized isolated main-scene PlayMode, loaded configs, and no active replay/manual clock");
            var root = new JSONObject(); var results = new JSONArray(); _logs = new JSONArray();
            root["startedUtc"] = DateTime.UtcNow.ToString("o");
            root["resourceLoader"] = ResLoader.ImplName;
            root["scope"] = "Safety fault fixtures only. Constructed terminal metrics do not certify gameplay, calibration, or reachability.";
            root["results"] = results; root["injectedFailureLogs"] = _logs;
            float priorScale = Time.timeScale;
            Application.logMessageReceived += CaptureLog;
            try
            {
                Scenario(results, "capacity_deferral_first_success_clock", Capacity);
                Scenario(results, "pause_and_speed_real_flow", PauseAndSpeed);
                Scenario(results, "missing_resource_invalidates_without_reward", MissingResource);
                Scenario(results, "f2_debug_victory_cannot_save", DebugVictory);
                Scenario(results, "incomplete_wave_cannot_reward_or_save", IncompleteWave);
                Scenario(results, "skipped_waves_cannot_save", SkippedWaves);
                Scenario(results, "sqlite_complete_victory_pending_retry", () => PendingSave(false));
                Scenario(results, "json_complete_victory_pending_retry", () => PendingSave(true));
            }
            finally
            {
                Application.logMessageReceived -= CaptureLog;
                GameFlowManager.Instance.TeardownLevel(); GameClock.StopLevelTimer(); GameClock.Reset();
                Time.timeScale = priorScale; _scenario = null; _scenarioResult = null; _resourceFaultLocation = null;
            }
            bool passed = true; foreach (var item in results) if (!item.Value["passed"].AsBool) passed = false;
            root["passed"] = passed; root["finishedUtc"] = DateTime.UtcNow.ToString("o");
            outputPath = Path.GetFullPath(outputPath); Directory.CreateDirectory(Path.GetDirectoryName(outputPath));
            File.WriteAllText(outputPath, root.ToString(2));
            return outputPath;
        }

        private static void Scenario(JSONArray results, string name, Action test)
        {
            _scenario = name;
            var result = new JSONObject(); result["scenario"] = name; result["startedUtc"] = DateTime.UtcNow.ToString("o"); results.Add(result);
            _scenarioResult = result;
            GameFlowManager flow = GameFlowManager.Instance;
            flow.TeardownLevel();
            using (SaveManager.Instance.SetTestStorageContext("runtime-safety-" + Guid.NewGuid().ToString("N")))
            using (SaveManager.Instance.UseProductionUnlockRulesForTest())
            using (GameClock.BeginManualSimulation())
            {
                try
                {
                    Time.timeScale = 1f;
                    flow.InitLevel(1);
                    Check(flow.State == GameFlowState.Preparing, "Level 1 must initialize");
                    // Synchronous fixtures share no rendered frame between scenarios. Rebuild the
                    // real cached population after teardown before testing any spawn failure path.
                    CountActualEnemies();
                    Check(CombatSystem.Instance.EnemyCount == 0 && CombatSystem.Instance.AliveEnemyCount == 0,
                        "Each isolated fixture starts with an empty actual registry and synchronized population cache");
                    test(); result["passed"] = true;
                }
                catch (Exception ex) { result["passed"] = false; result["error"] = ex.ToString(); }
                finally { flow.TeardownLevel(); GameClock.StopLevelTimer(); GameClock.Reset(); }
            }
            result["finishedUtc"] = DateTime.UtcNow.ToString("o");
        }

        private static void CaptureLog(string condition, string trace, LogType type)
        {
            if (type != LogType.Error && type != LogType.Exception && type != LogType.Warning) return;
            var entry = new JSONObject(); entry["scenario"] = _scenario; entry["utc"] = DateTime.UtcNow.ToString("o");
            entry["type"] = type.ToString(); entry["message"] = condition; entry["stack"] = trace;
            entry["expectedFault"] = (_scenario == "missing_resource_invalidates_without_reward" &&
                (condition.Contains("[Res]") || condition.Contains("[Enemy]") || condition.Contains("[Rating]") || condition.Contains("[ResLoader]")
                || (!string.IsNullOrEmpty(_resourceFaultLocation) && condition.Contains(_resourceFaultLocation))))
                || (_scenario == "incomplete_wave_cannot_reward_or_save" && condition.Contains("incomplete enemy accounting"))
                || ((_scenario == "sqlite_complete_victory_pending_retry" || _scenario == "json_complete_victory_pending_retry") && condition.Contains("[Save]"));
            _logs.Add(entry);
        }

        private static void Check(bool condition, string message) { if (!condition) throw new InvalidOperationException(message); }
        private static object Field(object owner, string name) { return owner.GetType().GetField(name, Private).GetValue(owner); }
        private static void Set(object owner, string name, object value) { owner.GetType().GetField(name, Private).SetValue(owner, value); }
        private static object Call(object owner, string name, params object[] args) { return owner.GetType().GetMethod(name, Private).Invoke(owner, args); }
        private static ISaveStorage Storage { get { return (ISaveStorage)Field(SaveManager.Instance, "_storage"); } }
        private static WaveManager Wave { get { return (WaveManager)Field(GameFlowManager.Instance, "_wave"); } }
        private static void Step(float seconds) { GameClock.StepManualFrame(seconds); GameFlowManager.Instance.StepManualSimulation(); }
        private static void CountActualEnemies() { Call(CombatSystem.Instance, "TickEnemies", 0f); }
        private static void StartWave() { EventDispatcher.TriggerEvent(EventName.StartRoundRequestEvent); }
        private static int FirstEnemyId()
        {
            var round = Configs.GetRound(GameFlowManager.Instance.Level.RoundIds[0]);
            return Configs.GetWaveGroup(round.WaveIds[0]).EnemyIds[0];
        }
        private static float FirstSpawnTime()
        {
            var round = Configs.GetRound(GameFlowManager.Instance.Level.RoundIds[0]);
            return Mathf.Max(0, round.StartDelayMs) / 1000f + Configs.GetWaveGroup(round.WaveIds[0]).StartDelayMs / 1000f;
        }
        private static void NoClear(string context)
        {
            var save = SaveManager.Instance; var p = save.Data.Find(1);
            Check(save.GetStars(1) == 0 && save.TotalStars == 0 && (p == null || p.clearCount == 0), context + ": no stars or clearCount");
            Check(!save.IsUnlocked(2), context + ": level 2 remains locked under actual player rules");
        }

        private static void Capacity()
        {
            int enemyId = FirstEnemyId(), cap = Configs.Global.MaxEnemyAlive; BaseEnemy first = null;
            Check(cap > 0 && cap <= 1000, "Bounded actual configured population");
            for (int i = 0; i < cap; i++)
            {
                BaseEnemy enemy = EnemyManager.Instance.Spawn(enemyId); Check(enemy != null, "Fill actual spawn capacity");
                if (first == null) first = enemy;
                CountActualEnemies();
            }
            Check(CombatSystem.Instance.AliveEnemyCount == cap, "Real combat registry reaches capacity");
            StartWave(); Step(FirstSpawnTime() + .0625f);
            Check(EnemyManager.Instance.LastSpawnFailure == EnemyManager.SpawnFailure.Capacity && Wave.SpawnedCount == 0, "Capacity retains pending timeline entry");
            Check(GameClock.CombatElapsedSeconds == 0d && GameClock.LevelElapsedSeconds > 0d, "Deferred spawning cannot start combat timer");
            Step(.0625f);
            Check(Wave.SpawnedCount == 0 && GameFlowManager.Instance.RunMetrics.successfulSpawned == 0 && GameClock.CombatElapsedSeconds == 0d, "Repeated full frame cannot consume spawn or combat time");
            EnemyManager.Instance.RecycleEnemy(first); CountActualEnemies();
            Step(.0625f); CountActualEnemies();
            Check(Wave.SpawnedCount == 1 && GameFlowManager.Instance.RunMetrics.successfulSpawned == 1, "Exactly the pending item spawns after capacity frees");
            Check(GameClock.CombatElapsedSeconds == 0d, "First successful spawn starts timer after current frame accrual");
            Step(.0625f);
            Check(GameClock.CombatElapsedSeconds == .0625d, "Next frame accrues combat once");
            NoClear("Capacity fixture");
        }

        private static void PauseAndSpeed()
        {
            var flow = GameFlowManager.Instance;
            StartWave(); Step(FirstSpawnTime() + .0625f);
            foreach (float speed in GameClock.Tiers)
            {
                GameClock.Speed = speed;
                double combat = GameClock.CombatElapsedSeconds, level = GameClock.LevelElapsedSeconds;
                int gold = PlayerDataManager.Instance.Gold, count = flow.RunMetrics.successfulSpawned;
                EventDispatcher.TriggerEvent(EventName.PauseToggleRequestEvent);
                Check(GameClock.IsPaused && Time.timeScale == 0f, "real pause event freezes timeScale");
                for (int i = 0; i < 4; i++) { Step(.0625f); EventDispatcher.TriggerEvent(EventName.UpdateEvent); }
                Check(GameClock.CombatElapsedSeconds == combat && GameClock.LevelElapsedSeconds == level &&
                    PlayerDataManager.Instance.Gold == gold && flow.RunMetrics.successfulSpawned == count,
                    "pause freezes both clocks, spawning and money at each speed");
                EventDispatcher.TriggerEvent(EventName.ResumeRequestEvent);
                Step(.0625f);
                Check(GameClock.CombatElapsedSeconds == combat + .0625d * speed &&
                    GameClock.LevelElapsedSeconds == level + .0625d * speed, "resume adds exactly the next step without catch-up");
            }
            GameClock.Speed = 1; NoClear("Pause/speed fixture");
        }

        private static void MissingResource()
        {
            string name = Configs.GetEnemy(FirstEnemyId()).ResName;
            var pools = (IDictionary)Field(EnemyManager.Instance, "_pools");
            var map = (IDictionary)typeof(ResTable).GetField("_map", BindingFlags.NonPublic | BindingFlags.Static).GetValue(null);
            Check(map.Contains(name) && ((ResAddress)map[name]).IsValid, "Resource registration exists before injection");
            object address = map[name]; bool hadPool = pools.Contains(name); object oldPool = hadPool ? pools[name] : null;
            object loader = ResLoader.Instance; Type loaderType = loader.GetType();
            FieldInfo handlesField = loaderType.GetField("_handles", Private), locationsField = loaderType.GetField("_locations", Private), assetsField = loaderType.GetField("_assetCache", Private);
            IDictionary handles = handlesField != null ? (IDictionary)handlesField.GetValue(loader) : null;
            IDictionary locations = locationsField != null ? (IDictionary)locationsField.GetValue(loader) : null;
            IDictionary assets = assetsField != null ? (IDictionary)assetsField.GetValue(loader) : null;
            bool yoo = handles != null && locations != null;
            Check(yoo || assets != null || loaderType.Name == "EditorResLoader", "Fault injection must support the actual resource loader: " + loaderType.Name);
            bool hadHandle = handles != null && handles.Contains(name), hadLocation = locations != null && locations.Contains(name), hadAsset = assets != null && assets.Contains(name);
            object oldHandle = hadHandle ? handles[name] : null, oldLocation = hadLocation ? locations[name] : null, oldAsset = hadAsset ? assets[name] : null;
            int gold = PlayerDataManager.Instance.Gold;
            try
            {
                pools.Remove(name);
                if (yoo)
                {
                    // Keep the original handle alive; removing a dictionary entry must not release it.
                    // Resolve checks handles before ResTable, and locations before candidate fallbacks.
                    handles.Remove(name);
                    _resourceFaultLocation = "__balance_missing_resource_" + Guid.NewGuid().ToString("N");
                    locations[name] = _resourceFaultLocation;
                }
                else
                {
                    if (assets != null) assets.Remove(name);
                    map.Remove(name);
                }
                _scenarioResult["resourceLoader"] = loaderType.Name; _scenarioResult["logicalName"] = name;
                _scenarioResult["injectedLocation"] = _resourceFaultLocation ?? "ResTable entry temporarily absent";
                StartWave(); Step(FirstSpawnTime() + .0625f);
                Check(EnemyManager.Instance.LastSpawnFailure == EnemyManager.SpawnFailure.Resource, "Real resource loader reports missing prefab");
                Check(GameFlowManager.Instance.State == GameFlowState.GameOver, "Resource fault ends the run without clearing");
                Check(Wave.SpawnedCount == 0 && GameClock.CombatElapsedSeconds == 0d, "Failed spawn cannot count or start timer");
                Check(PlayerDataManager.Instance.Gold == gold, "No reward for resource fault"); NoClear("Missing resource");
            }
            finally
            {
                map[name] = address;
                if (handles != null) { handles.Remove(name); if (hadHandle) handles[name] = oldHandle; }
                if (locations != null) { locations.Remove(name); if (hadLocation) locations[name] = oldLocation; }
                if (assets != null) { assets.Remove(name); if (hadAsset) assets[name] = oldAsset; }
                pools.Remove(name); if (hadPool) pools[name] = oldPool;
                _resourceFaultLocation = null;
                bool restored = ((ResAddress)map[name]).Equals((ResAddress)address)
                    && pools.Contains(name) == hadPool && (!hadPool || ReferenceEquals(pools[name], oldPool))
                    && (handles == null || (handles.Contains(name) == hadHandle && (!hadHandle || ReferenceEquals(handles[name], oldHandle))))
                    && (locations == null || (locations.Contains(name) == hadLocation && (!hadLocation || Equals(locations[name], oldLocation))))
                    && (assets == null || (assets.Contains(name) == hadAsset && (!hadAsset || ReferenceEquals(assets[name], oldAsset))));
                _scenarioResult["resourceStateRestored"] = restored;
                Check(restored, "Resource registration, cached handle/location/asset and pool references restored exactly");
            }
        }

        private static void DebugVictory()
        {
            // This is exactly the F2 handler's two calls, including the real Win -> GameOver UI chain.
            GameFlowManager.Instance.MarkDebugRun(); PlayerDataManager.Instance.Win();
            Check(GameFlowManager.Instance.State == GameFlowState.GameOver && GameFlowManager.Instance.RunMetrics.debugOverride, "F2 marks and ends run");
            var info = PopupInfo(); Check(info.stars == 0 && !info.progressSaved && !info.savePending, "F2 popup is unscored and unsaved");
            NoClear("F2 debug victory");
        }

        private static void IncompleteWave()
        {
            StartWave(); int gold = PlayerDataManager.Instance.Gold;
            // Exercise the real private finalization entrance with an unfinished outcome ledger.
            Call(GameFlowManager.Instance, "FinishRound");
            Check(GameFlowManager.Instance.State == GameFlowState.GameOver, "Incomplete wave ends the run without clearing");
            Check(PlayerDataManager.Instance.Gold == gold && GameFlowManager.Instance.RunMetrics.completedWaveCount == 0, "No round reward or cursor credit");
            NoClear("Incomplete wave");
        }

        private static void SkippedWaves()
        {
            Set(GameFlowManager.Instance, "_roundCursor", GameFlowManager.Instance.RunMetrics.expectedWaveCount);
            StartWave();
            var info = PopupInfo();
            Check(GameFlowManager.Instance.State == GameFlowState.GameOver && info.stars == 0 && !info.progressSaved, "Jumping final cursor cannot fabricate a clear");
            NoClear("Skipped waves");
        }

        private static LevelClearView Popup()
        {
            var view = UnityEngine.Object.FindObjectOfType<LevelClearView>(); Check(view != null, "Actual clear popup exists"); return view;
        }
        private static LevelClearInfo PopupInfo() { var info = (LevelClearInfo)Field(Popup(), "_info"); Check(info != null, "Popup has result data"); return info; }

        private static LevelRunMetrics TerminalFixture()
        {
            // 【2026-11-01】评级表删除后，计划量与用时都取自本局账目/关卡配置，不再有 profile。
            var flow = GameFlowManager.Instance; var m = flow.RunMetrics;
            m.runId = "safety-fixture-" + Guid.NewGuid().ToString("N");
            int waves = Math.Max(1, m.expectedWaveCount > 0 ? m.expectedWaveCount : flow.Level.RoundIds.Count);
            m.completedWaveCount = waves; m.successfulSpawned = m.expectedEnemyCount; m.killed = m.expectedEnemyCount;
            m.leaked = m.bossLeaked = 0; m.victory = true; m.debugOverride = false;
            m.hp = m.maxHp = PlayerDataManager.Instance.MaxHp;
            m.combatElapsedSeconds = 100d; m.levelElapsedSeconds = 195d; m.waves.Clear();
            for (int i = 0; i < flow.Level.RoundIds.Count; i++)
            {
                var round = Configs.GetRound(flow.Level.RoundIds[i]); int expected = 0;
                foreach (int group in round.WaveIds) expected += Configs.GetWaveGroup(group).EnemyCount;
                m.waves.Add(new WaveRunMetrics { ordinal = i + 1, expected = expected, successfulSpawned = expected, killed = expected,
                    hp = m.hp, gold = 137, clearGold = round.RewardGold, combatStartSeconds = m.combatElapsedSeconds * i / waves,
                    combatEndSeconds = m.combatElapsedSeconds * (i + 1) / waves, levelEndSeconds = m.levelElapsedSeconds * (i + 1) / waves });
            }
            return m;
        }

        private static void ExecuteDatabase(object database, string sql)
        {
            database.GetType().GetMethod("Execute").Invoke(database, new object[] { sql, new object[0] });
        }

        private static void PendingSave(bool json)
        {
            var save = SaveManager.Instance; var flow = GameFlowManager.Instance;
            ISaveStorage original = Storage, backend = original; SaveData originalData = save.Data;
            string directory = null; object database = null; string blockedPath = null; bool blocked = false;
            if (json)
            {
                directory = Path.Combine(Path.GetDirectoryName(original.Location), "json-flow"); Directory.CreateDirectory(directory);
                Type type = typeof(SaveManager).Assembly.GetType("FTProject.JsonSaveStorage", true);
                object crypto = Field(original, "_crypto");
                backend = (ISaveStorage)Activator.CreateInstance(type, BindingFlags.Instance | BindingFlags.NonPublic, null, new object[] { crypto, directory }, null);
                backend.Initialize(); Set(save, "_storage", backend); Set(save, "_data", new SaveData());
            }
            try
            {
                save.Data.levels.Add(new LevelProgress { levelId = 1, stars = 4, clearCount = 2 }); save.Save();
                var fixture = TerminalFixture(); Set(flow, "_run", fixture); Set(flow, "_roundCursor", fixture.expectedWaveCount);
                PlayerDataManager.Instance.RestoreState(1, 137, fixture.hp, fixture.maxHp, fixture.killed, 0);
                GameClock.RestoreTimers(fixture.combatElapsedSeconds, fixture.levelElapsedSeconds, true);
                // 【2026-10-30】局内不再写快照：这里原来先落一份"终局检查点"再注入写盘故障，
                // 现在只剩"通关记录"这一份要保证原子性，检查点相关断言一并删除。
                string before = JsonUtility.ToJson(save.Data.Find(1));
                if (json) { blockedPath = backend.Location + ".tmp"; Directory.CreateDirectory(blockedPath); }
                else { database = Field(backend, "_db"); ExecuteDatabase(database, "PRAGMA query_only=ON"); }
                blocked = true;
                Call(flow, "CompleteVictory");
                var info = PopupInfo();
                Check(info.savePending && !info.progressSaved && !info.newRecord && info.stars == SaveManager.MaxStars, "Real CompleteVictory -> Win -> popup enters pending state");
                Check(flow.RunMetrics.runId == fixture.runId, "Pending result freezes the original runId");
                Check(JsonUtility.ToJson(save.Data.Find(1)) == before, "Failed commit publishes no progress change");
                Check(JsonUtility.ToJson(backend.LoadLevels()[0]) == before, "Failed backend remains at prior best/count");
                var view = Popup(); var next = (Button)Field(view, "_nextBtn"); Check(next != null && (!next.gameObject.activeInHierarchy || !next.interactable), "Actual Next button unavailable while pending");
                int nextEvents = 0; Action<int> observer = ignored => nextEvents++;
                EventDispatcher.AddEventListener<int>(EventName.SelectLevelRequestEvent, observer);
                try { Call(view, "OnClickNext"); Check(nextEvents == 0, "Programmatic Next handler also blocks unsaved result"); }
                finally { EventDispatcher.RemoveEventListener<int>(EventName.SelectLevelRequestEvent, observer); }
                Call(view, "OnClickRetry"); Check(PopupInfo().savePending && save.Data.Find(1).clearCount == 2, "Retry during fault remains pending without double count");
                if (json) Directory.Delete(blockedPath); else ExecuteDatabase(database, "PRAGMA query_only=OFF"); blocked = false;
                Call(Popup(), "OnClickRetry"); info = PopupInfo();
                Check(info.progressSaved && !info.savePending && info.newRecord && flow.RunMetrics.runId == fixture.runId, "Actual retry button saves same runId and refreshes popup");
                Check(save.Data.Find(1).clearCount == 3 && save.GetStars(1) == 5, "Exactly one clear commits");
                Check(((Button)Field(Popup(), "_nextBtn")).interactable, "Next becomes available after durable success");
                Check(save.RecordClear(1, fixture), "Duplicate same-run result is accepted idempotently");
                Call(flow, "CompleteVictory"); PlayerDataManager.Instance.Win();
                Check(save.Data.Find(1).clearCount == 3 && backend.LoadLevels()[0].committedRunIds.Count == 1, "Duplicate terminal callbacks cannot count again");
                if (json)
                {
                    backend.Dispose(); backend.Initialize();
                    Check(backend.LoadLevels()[0].clearCount == 3, "JSON reopen observes exactly one saved result");
                }
                else
                {
                    using (save.SetTestStorageContext(GetTestContext()))
                        Check(save.Data.Find(1).clearCount == 3 && save.IsRunCommitted(1, fixture.runId), "SQLite close/reopen observes durable one-run result");
                    backend = Storage; database = null;
                }
            }
            finally
            {
                if (blocked) { if (json) Directory.Delete(blockedPath); else ExecuteDatabase(database, "PRAGMA query_only=OFF"); }
                if (json) { backend.Dispose(); Set(save, "_storage", original); Set(save, "_data", originalData); }
            }
        }

        private static string GetTestContext()
        {
            Type factory = typeof(SaveManager).Assembly.GetType("FTProject.SaveStorageFactory", true);
            return (string)factory.GetProperty("ActiveTestContextId", BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic).GetValue(null, null);
        }
    }
}
