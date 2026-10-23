using System;
using System.IO;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using System.Text.RegularExpressions;

namespace FTProject.Tests
{
    public class LevelRatingTests
    {
        private static LevelRatingProfile Profile()
        {
            return new LevelRatingProfile { id = 1, difficultyTier = 1, profileId = "D04", profileRevision = "1", balanceRevision = "b1", ratingRevision = "r1", planHash = "hash", expectedWaveCount = 20, expectedEnemyCount = 20, parCombatTimeMs = 100000 };
        }
        private static LevelRunMetrics Metrics(int hp = 20, int leaks = 0, int boss = 0, int critical = 0, long combatMs = 100000)
        {
            var p = Profile();
            var m = new LevelRunMetrics { runId = "run-one", profileId = p.profileId, profileRevision = p.profileRevision, balanceRevision = p.balanceRevision, ratingRevision = p.ratingRevision, planHash = p.planHash, expectedWaveCount = 20, completedWaveCount = 20, expectedEnemyCount = 20, successfulSpawned = 20, killed = 20 - leaks, leaked = leaks, bossLeaked = boss, criticalLeaked = critical, hp = hp, maxHp = 20, victory = true, statisticsValid = true, timingValid = true, combatElapsedSeconds = combatMs / 1000d, levelElapsedSeconds = Math.Max(200d, combatMs / 1000d) };
            for (int i = 0; i < 20; i++) m.waves.Add(new WaveRunMetrics { ordinal = i + 1, expected = 1, successfulSpawned = 1, killed = i < leaks ? 0 : 1, leaked = i < leaks ? 1 : 0, bossLeaked = i < boss ? 1 : 0, criticalLeaked = i < critical ? 1 : 0, combatStartSeconds = i, combatEndSeconds = i + 1 });
            return m;
        }
        [TestCase(20, 0, 5)] [TestCase(19, 1, 4)] [TestCase(18, 2, 4)] [TestCase(17, 3, 3)] [TestCase(15, 5, 3)] [TestCase(14, 6, 2)] [TestCase(10, 10, 2)] [TestCase(9, 11, 1)] [TestCase(1, 19, 1)] [TestCase(0, 20, 0)]
        public void HealthThresholds(int hp, int leaks, int stars) { Assert.That(LevelRatingEvaluator.Evaluate(Profile(), Metrics(hp, leaks)).stars, Is.EqualTo(stars)); }
        [TestCase(100000, 5)] [TestCase(100001, 4)] [TestCase(125000, 4)] [TestCase(125001, 3)] [TestCase(0, 0)] [TestCase(-1, 0)]
        public void MillisecondBoundaries(long time, int stars) { Assert.That(LevelRatingEvaluator.Evaluate(Profile(), Metrics(combatMs: time)).stars, Is.EqualTo(stars)); }
        [Test]
        public void CriticalIdentityCapsAndContradictions()
        {
            Assert.That(LevelRatingEvaluator.Evaluate(Profile(), Metrics(18, 1, 1, 1)).stars, Is.EqualTo(2));
            Assert.That(LevelRatingEvaluator.Evaluate(Profile(), Metrics(18, 1, 0, 1)).stars, Is.EqualTo(3));
            Assert.That(LevelRatingEvaluator.Evaluate(Profile(), Metrics(18, 1)).stars, Is.EqualTo(4), "ordinary heavy is not an elite");
            Assert.That(LevelRatingEvaluator.Evaluate(Profile(), Metrics(20, 1)).stars, Is.LessThan(5));
        }
        [Test]
        public void MissingEvidenceDebugFailureAndVersionsNeverRate()
        {
            foreach (Action<LevelRunMetrics> invalidate in new Action<LevelRunMetrics>[] { m => m.maxHp = 0, m => m.timingValid = false, m => m.statisticsValid = false, m => m.debugOverride = true, m => m.victory = false, m => m.successfulSpawned--, m => m.completedWaveCount--, m => m.planHash = "changed", m => m.balanceRevision = "changed", m => m.ratingRevision = "changed", m => m.profileId = "D08", m => m.profileRevision = "changed", m => m.waves = null })
            { var metrics = Metrics(); invalidate(metrics); var result = LevelRatingEvaluator.Evaluate(Profile(), metrics); Assert.That(result.valid, Is.False); Assert.That(result.stars, Is.Zero); }
        }
        [Test]
        public void NewCampaignRequiresAll25WavesAndRejectsOld20WaveCheckpoint()
        {
            var old = Metrics(); var profile = Profile();
            profile.expectedWaveCount = 25; profile.expectedEnemyCount = 25;
            profile.balanceRevision = "balance-30x25-economy-v2";
            Assert.That(LevelRatingEvaluator.Evaluate(profile, old).valid, Is.False);
            var current = Metrics(); current.balanceRevision = profile.balanceRevision;
            current.expectedWaveCount = current.completedWaveCount = 25;
            current.expectedEnemyCount = current.successfulSpawned = current.killed = 25;
            for (int i = 20; i < 25; i++) current.waves.Add(new WaveRunMetrics { ordinal = i + 1, expected = 1, successfulSpawned = 1, killed = 1, combatStartSeconds = i, combatEndSeconds = i + 1 });
            Assert.That(LevelRatingEvaluator.Evaluate(profile, current).stars, Is.EqualTo(5));
            current.waves.RemoveAt(24);
            Assert.That(LevelRatingEvaluator.Evaluate(profile, current).valid, Is.False);
            var snapshot = new LevelSnapshot { valid = true, formatVersion = 2, levelId = 1, roundCursor = 20, hp = 20, maxHp = 20, gold = 100, metrics = old, ratingProfile = Profile(), levelTimerStarted = true };
            string reason;
            Assert.That(LevelCheckpointValidator.IsCompatible(snapshot, profile, 25, out reason), Is.False);
        }

        [Test]
        public void MigrationPreservesUnlockAndLegacyWithoutMultiplyingStars()
        {
            var p = new LevelProgress { levelId = 1, stars = 3, clearCount = 7, bestTimeMs = 123456, bestHpLeft = 20 };
            Assert.That(SaveProgressMigration.ArchiveForVersion(p, Profile().versionKey), Is.True);
            Assert.That(p.stars, Is.Zero); Assert.That(p.bestTimeMs, Is.Zero); Assert.That(p.Cleared, Is.True); Assert.That(p.clearCount, Is.EqualTo(7));
            Assert.That(p.legacy[0].stars, Is.EqualTo(3)); Assert.That(p.legacy[0].bestTimeMs, Is.EqualTo(123456));
            Assert.That(SaveProgressMigration.ArchiveForVersion(p, Profile().versionKey), Is.False); Assert.That(p.legacy.Count, Is.EqualTo(1));
            p.stars = 5; SaveProgressMigration.ArchiveForVersion(p, Profile().versionKey + "new"); Assert.That(p.stars, Is.Zero); Assert.That(p.legacy.Count, Is.EqualTo(2)); Assert.That(p.Cleared, Is.True);
        }
        [TestCase(1f)] [TestCase(2f)] [TestCase(3f)]
        public void SharedClockCountsOneSimulationStepAndFreezesPreparationAndPause(float speed)
        {
            GameClock.Reset(); GameClock.ResetLevelTimer(); GameClock.Speed = speed;
            using (GameClock.BeginManualSimulation())
            {
                GameClock.StepManualFrame(1f); Assert.That(GameClock.LevelElapsedSeconds, Is.Zero);
                GameClock.StartLevelTimer();
                GameClock.StepManualFrame(1f); Assert.That(GameClock.LevelElapsedSeconds, Is.EqualTo(speed)); Assert.That(GameClock.CombatElapsedSeconds, Is.Zero);
                GameClock.SetCombatRunning(true);
                GameClock.StepManualFrame(0.01f); double before = GameClock.CombatElapsedSeconds;
                GameClock.Tick(); float a = GameClock.DeltaTime; GameClock.Tick(); Assert.That(GameClock.CombatElapsedSeconds, Is.EqualTo(before)); Assert.That(a, Is.EqualTo(0.01f * speed));
                GameClock.SetBackground(true); GameClock.StepManualFrame(50f); Assert.That(GameClock.CombatElapsedSeconds, Is.EqualTo(before));
                GameClock.SetBackground(false); GameClock.SetCombatRunning(false); GameClock.StepManualFrame(2f); Assert.That(GameClock.CombatElapsedSeconds, Is.EqualTo(before));
            }
            GameClock.StopLevelTimer(); GameClock.Reset();
        }
        [TestCase(.05f)] [TestCase(1f / 60f)]
        public void FixedReplayStepMatchesRawClocksAtEverySpeed(float step)
        {
            float priorScale = Time.timeScale;
            try
            {
                Time.timeScale = 1f;
                foreach (float speed in GameClock.Tiers)
                {
                    GameClock.Reset(); GameClock.ResetLevelTimer(); GameClock.Speed = speed;
                    using (GameClock.BeginManualSimulation())
                    {
                        GameClock.StartLevelTimer(); GameClock.SetCombatRunning(true);
                        for (int i = 0; i < 1000; i++)
                        {
                            GameClock.StepManualFrame(step / (double)speed);
                            Assert.That(GameClock.DeltaTime, Is.EqualTo(step));
                        }
                        Assert.That(GameClock.CombatElapsedSeconds, Is.EqualTo((double)step * 1000));
                        Assert.That(GameClock.LevelElapsedSeconds, Is.EqualTo((double)step * 1000));
                    }
                }
            }
            finally { Time.timeScale = priorScale; GameClock.StopLevelTimer(); GameClock.Reset(); }
        }
        [TestCase(1f)] [TestCase(2f)] [TestCase(3f)]
        public void TimeScalePauseAndResumeCannotAccrueOrCatchUpEitherTimer(float speed)
        {
            float priorScale = Time.timeScale;
            try
            {
                Time.timeScale = 1f;
                GameClock.Reset(); GameClock.ResetLevelTimer(); GameClock.Speed = speed;
                using (GameClock.BeginManualSimulation())
                {
                    GameClock.StartLevelTimer(); GameClock.SetCombatRunning(true);
                    GameClock.StepManualFrame(.0625f);
                    double level = GameClock.LevelElapsedSeconds, combat = GameClock.CombatElapsedSeconds;
                    Time.timeScale = 0f;
                    GameClock.StepManualFrame(500f);
                    Assert.That(GameClock.DeltaTime, Is.Zero);
                    Assert.That(GameClock.LevelElapsedSeconds, Is.EqualTo(level));
                    Assert.That(GameClock.CombatElapsedSeconds, Is.EqualTo(combat));
                    Assert.That(GameClock.Speed, Is.EqualTo(speed));
                    Time.timeScale = 1f;
                    GameClock.StepManualFrame(.0625f);
                    Assert.That(GameClock.LevelElapsedSeconds, Is.EqualTo(level + .0625d * speed));
                    Assert.That(GameClock.CombatElapsedSeconds, Is.EqualTo(combat + .0625d * speed));
                }
            }
            finally { Time.timeScale = priorScale; GameClock.StopLevelTimer(); GameClock.Reset(); }
        }
        [Test]
        public void TickAndGetterFrameRefreshAreIdempotent()
        {
            GameClock.Reset(); GameClock.ResetLevelTimer(); GameClock.RestoreTimers(0, 0, true); GameClock.SetCombatRunning(true);
            GameClock.RefreshFrame(int.MaxValue - 3, 0.1f); double once = GameClock.LevelElapsedSeconds;
            GameClock.RefreshFrame(int.MaxValue - 3, 0.1f); Assert.That(GameClock.LevelElapsedSeconds, Is.EqualTo(once));
            GameClock.StopLevelTimer(); GameClock.Reset();
        }
        [Test]
        public void CheckpointClockRestoresStartedFlagAndExcludesOfflineTimeAtFractionalBoundary()
        {
            GameClock.Reset(); GameClock.ResetLevelTimer();
            using (GameClock.BeginManualSimulation())
            {
                GameClock.RestoreTimers(0d, 0d, false); GameClock.StepManualFrame(.0625f);
                Assert.That(GameClock.IsLevelTimerRunning, Is.False); Assert.That(GameClock.LevelElapsedSeconds, Is.Zero);
                GameClock.RestoreTimers(19.9375d, 29.8125d, true);
                Assert.That(GameClock.IsLevelTimerRunning, Is.True); Assert.That(GameClock.CombatElapsedSeconds, Is.EqualTo(19.9375d));
                GameClock.SetBackground(true); GameClock.StepManualFrame(100f);
                Assert.That(GameClock.LevelElapsedSeconds, Is.EqualTo(29.8125d));
                GameClock.SetBackground(false); GameClock.StepManualFrame(.0625f);
                Assert.That(GameClock.LevelElapsedSeconds, Is.EqualTo(29.875d));
                Assert.That(GameClock.CombatElapsedSeconds, Is.EqualTo(19.9375d), "saved inter-wave waiting is excluded from combat");
                GameClock.SetCombatRunning(true); GameClock.StepManualFrame(.0625f);
                Assert.That(GameClock.CombatElapsedSeconds, Is.EqualTo(20d));
            }
            GameClock.StopLevelTimer(); GameClock.Reset();
        }
        [Test]
        public void TowerCheckpointPreservesCooldownSearchAndMuzzlePhaseAndRejectsNonfiniteEvidence()
        {
            const System.Reflection.BindingFlags fields = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic;
            var first = new GameObject("checkpoint-tower-original"); var second = new GameObject("checkpoint-tower-restored");
            try
            {
                var source = first.AddComponent<BaseTower>(); var restored = second.AddComponent<BaseTower>();
                var barrel1 = new GameObject("barrel").transform; barrel1.SetParent(first.transform, false);
                var barrel2 = new GameObject("barrel").transform; barrel2.SetParent(second.transform, false);
                barrel1.localPosition = new Vector3(.125f, -.0625f, 0f); barrel1.localRotation = Quaternion.Euler(0f, 0f, 90f);
                typeof(BaseTower).GetField("_barrel", fields).SetValue(source, barrel1); typeof(BaseTower).GetField("_barrel", fields).SetValue(restored, barrel2);
                typeof(BaseTower).GetField("_fireTimer", fields).SetValue(source, .3125f);
                typeof(BaseTower).GetField("_searchTimer", fields).SetValue(source, .1875f);
                typeof(BaseTower).GetField("_recoilTimer", fields).SetValue(source, .0625f);
                typeof(BaseTower).GetField("_lastDir", fields).SetValue(source, Vector2.up);
                var snapshot = new TowerSnapshot { row = 2, col = 3, type = 1, level = 2 }; source.CaptureCheckpointState(snapshot);
                for (int i = 0; i < 30; i++) snapshot = JsonUtility.FromJson<TowerSnapshot>(JsonUtility.ToJson(snapshot));
                Assert.That(snapshot.HasValidRuntimeState(), Is.True); Assert.That(restored.RestoreCheckpointState(snapshot), Is.True);
                Assert.That((float)typeof(BaseTower).GetField("_fireTimer", fields).GetValue(restored), Is.EqualTo(.3125f));
                Assert.That((float)typeof(BaseTower).GetField("_searchTimer", fields).GetValue(restored), Is.EqualTo(.1875f));
                Assert.That((float)typeof(BaseTower).GetField("_recoilTimer", fields).GetValue(restored), Is.EqualTo(.0625f));
                Assert.That(barrel2.localPosition, Is.EqualTo(barrel1.localPosition));
                Assert.That(Quaternion.Angle(barrel2.localRotation, barrel1.localRotation), Is.LessThan(.001f));
                snapshot.fireTimer = float.NaN; Assert.That(snapshot.HasValidRuntimeState(), Is.False); Assert.That(restored.RestoreCheckpointState(snapshot), Is.False);
                snapshot.fireTimer = .3125f; snapshot.searchTimer = float.PositiveInfinity; Assert.That(snapshot.HasValidRuntimeState(), Is.False);
                snapshot.searchTimer = .1875f; snapshot.barrelLocalRotation = new Quaternion(); Assert.That(snapshot.HasValidRuntimeState(), Is.False);
            }
            finally { UnityEngine.Object.DestroyImmediate(first); UnityEngine.Object.DestroyImmediate(second); }
        }
        [Test]
        public void LastSpawnAfterCachedZeroCannotClearWaveRewardOrWinBeforeOutcome()
        {
            const System.Reflection.BindingFlags fields = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic;
            var previousFlow = GameFlowManager.Instance;
            var flowObject = new GameObject("last-spawn-flow-regression");
            var enemyObject = new GameObject("last-spawn-enemy-regression");
            var combat = CombatSystem.Instance;
            var cachedCount = typeof(CombatSystem).GetField("<AliveEnemyCount>k__BackingField", fields);
            int previousCachedCount = combat.AliveEnemyCount;
            int groupClears = 0, roundClears = 0;
            Action<int> onGroupClear = value => groupClears++;
            Action<int> onRoundClear = value => roundClears++;
            EventDispatcher.AddEventListener<int>(EventName.WaveClearEvent, onGroupClear);
            EventDispatcher.AddEventListener<int>(EventName.RoundClearEvent, onRoundClear);
            try
            {
                var flow = flowObject.AddComponent<GameFlowManager>();
                var enemy = enemyObject.AddComponent<BaseEnemy>();
                typeof(GameFlowManager).GetField("<State>k__BackingField", fields).SetValue(flow, GameFlowState.RoundRunning);
                var metrics = new LevelRunMetrics { statisticsValid = true, timingValid = true };
                metrics.waves.Add(new WaveRunMetrics { ordinal = 1, expected = 1 });
                typeof(GameFlowManager).GetField("_run", fields).SetValue(flow, metrics);
                var wave = (WaveManager)typeof(GameFlowManager).GetField("_wave", fields).GetValue(flow);
                // Reproduce the exact frame boundary: combat saw zero, then the final
                // timeline item spawned in the later GameFlow phase of that frame.
                cachedCount.SetValue(combat, 0);
                var entries = (System.Collections.IList)typeof(WaveManager).GetField("_timeline", fields).GetValue(wave);
                entries.Add(Activator.CreateInstance(entries.GetType().GetGenericArguments()[0]));
                ((System.Collections.Generic.List<bool>)typeof(WaveManager).GetField("_groupCleared", fields).GetValue(wave)).Add(false);
                typeof(WaveManager).GetField("_cursor", fields).SetValue(wave, 1);
                typeof(WaveManager).GetField("_allSpawned", fields).SetValue(wave, true);
                flow.NotifyEnemySpawned(enemy);
                int goldBefore = PlayerDataManager.Instance.Gold;
                using (GameClock.BeginManualSimulation())
                {
                    GameClock.StepManualFrame(0.05f);
                    flow.StepManualSimulation();
                }
                Assert.That(combat.AliveEnemyCount, Is.Zero, "the cached count deliberately remains stale");
                Assert.That(metrics.successfulSpawned, Is.EqualTo(1));
                Assert.That(metrics.killed + metrics.leaked, Is.Zero);
                Assert.That(flow.State, Is.EqualTo(GameFlowState.RoundRunning));
                Assert.That(metrics.completedWaveCount, Is.Zero);
                Assert.That(metrics.statisticsValid, Is.True);
                Assert.That(groupClears, Is.Zero); Assert.That(roundClears, Is.Zero);
                Assert.That(PlayerDataManager.Instance.Gold, Is.EqualTo(goldBefore));
                Assert.That((bool)typeof(GameFlowManager).GetField("_settled", fields).GetValue(flow), Is.False);
            }
            finally
            {
                EventDispatcher.RemoveEventListener<int>(EventName.WaveClearEvent, onGroupClear);
                EventDispatcher.RemoveEventListener<int>(EventName.RoundClearEvent, onRoundClear);
                UnityEngine.Object.DestroyImmediate(enemyObject); UnityEngine.Object.DestroyImmediate(flowObject);
                cachedCount.SetValue(combat, previousCachedCount);
                typeof(GameFlowManager).GetField("<Instance>k__BackingField", System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.NonPublic).SetValue(null, previousFlow);
                GameClock.StopLevelTimer(); GameClock.Reset();
            }
        }
        [TestCase(false, 4)] [TestCase(false, 5)] [TestCase(true, 4)] [TestCase(true, 5)]
        public void StorageRoundtripRetainsStarsCompleteEvidenceAndFractionalTime(bool sqlite, int stars)
        {
            string directory = Path.Combine(Path.GetTempPath(), "FTProject-rating-" + Guid.NewGuid().ToString("N")); Directory.CreateDirectory(directory);
            try
            {
                var profile = Profile(); var m = Metrics(); m.combatElapsedSeconds = 99.999499123456; var result = LevelRatingEvaluator.Evaluate(profile, m);
                var progress = new LevelProgress { levelId = 1, stars = stars, bestTimeMs = 200000, bestCombatTimeMs = 99999, ratingVersionKey = profile.versionKey, bestRating = result, clearCount = 2 };
                var snapshot = new LevelSnapshot { valid = true, levelId = 1, formatVersion = 2, roundCursor = 20, hp = 20, maxHp = 20, gold = 22, metrics = m, ratingProfile = profile, levelTimerStarted = true };
                using (var storage = Open(sqlite, directory)) { storage.SaveLevel(progress); storage.SaveSnapshot(snapshot); }
                using (var storage = Open(sqlite, directory))
                {
                    var loaded = storage.LoadLevels()[0]; Assert.That(loaded.stars, Is.EqualTo(stars)); Assert.That(loaded.bestTimeMs, Is.EqualTo(200000)); Assert.That(loaded.bestRating.metrics.runId, Is.EqualTo(m.runId));
                    var checkpoint = storage.LoadSnapshot(); Assert.That(checkpoint.metrics.combatElapsedSeconds, Is.EqualTo(m.combatElapsedSeconds)); Assert.That(checkpoint.roundCursor, Is.EqualTo(20));
                    for (int i = 0; i < 30; i++) { storage.SaveSnapshot(checkpoint); checkpoint = storage.LoadSnapshot(); }
                    Assert.That(checkpoint.metrics.combatElapsedSeconds, Is.EqualTo(m.combatElapsedSeconds));
                    Assert.That(storage.CommitClear(progress), Is.True); Assert.That(storage.LoadSnapshot().valid, Is.False);
                }
            }
            finally { Directory.Delete(directory, true); }
        }
        private static ISaveStorage Open(bool sqlite, string directory)
        {
            ICryptoService crypto = AesCryptoService.Create(new byte[32]);
            ISaveStorage storage;
            if (sqlite) { SqliteDatabase database; string error; Assert.That(SqliteDatabase.TryOpen(Path.Combine(directory, "test.db"), out database, out error), Is.True, error); storage = new SqliteSaveStorage(database, crypto); }
            else storage = new JsonSaveStorage(crypto, directory);
            storage.Initialize(); return storage;
        }
        [TestCase(false)] [TestCase(true)]
        public void SnapshotWriteAndReplayClearFailuresRetainDurableBoundaryAndRetry(bool sqlite)
        {
            const System.Reflection.BindingFlags fields = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic;
            string directory = Path.Combine(Path.GetTempPath(), "FTProject-checkpoint-failure-" + Guid.NewGuid().ToString("N")); Directory.CreateDirectory(directory);
            var manager = SaveManager.Instance;
            var storageField = typeof(SaveManager).GetField("_storage", fields);
            var dataField = typeof(SaveManager).GetField("_data", fields);
            var loadedField = typeof(SaveManager).GetField("_loaded", fields);
            object originalStorage = storageField.GetValue(manager), originalData = dataField.GetValue(manager), originalLoaded = loadedField.GetValue(manager);
            ISaveStorage storage = null;
            try
            {
                storage = Open(sqlite, directory);
                var boundary = new LevelSnapshot { valid = true, formatVersion = 2, levelId = 1, roundCursor = 4, gold = 137, hp = 19, maxHp = 20, metrics = Metrics(), ratingProfile = Profile() };
                boundary.towers.Add(new TowerSnapshot { row = 2, col = 3, type = 1, level = 2 });
                storage.SaveSnapshot(boundary);
                var data = new SaveData { snapshot = storage.LoadSnapshot() };
                storageField.SetValue(manager, storage); dataField.SetValue(manager, data); loadedField.SetValue(manager, true);
                string before = JsonUtility.ToJson(manager.Snapshot);
                var replacement = JsonUtility.FromJson<LevelSnapshot>(before); replacement.roundCursor = 5; replacement.gold = 200;
                SqliteDatabase database = sqlite ? (SqliteDatabase)storage.GetType().GetField("_db", fields).GetValue(storage) : null;
                if (sqlite) database.Execute("PRAGMA query_only=ON");
                else Directory.CreateDirectory(Path.Combine(directory, "freetower_save.json.tmp"));
                LogAssert.Expect(LogType.Warning, new Regex("\\[Save\\]"));
                Assert.That(manager.TrySetSnapshot(replacement), Is.False);
                Assert.That(JsonUtility.ToJson(manager.Snapshot), Is.EqualTo(before));
                LogAssert.Expect(LogType.Warning, new Regex("\\[Save\\]"));
                manager.SetSnapshot(replacement);
                Assert.That(JsonUtility.ToJson(manager.Snapshot), Is.EqualTo(before));
                LogAssert.Expect(LogType.Warning, new Regex("\\[Save\\]"));
                Assert.That(manager.TryClearSnapshot(), Is.False);
                Assert.That(manager.HasSnapshot, Is.True);
                LogAssert.Expect(LogType.Warning, new Regex("\\[Save\\]"));
                manager.ClearSnapshot(true);
                Assert.That(JsonUtility.ToJson(manager.Snapshot), Is.EqualTo(before));
                using (var reopened = Open(sqlite, directory)) Assert.That(JsonUtility.ToJson(reopened.LoadSnapshot()), Is.EqualTo(before));
                if (sqlite) database.Execute("PRAGMA query_only=OFF");
                else Directory.Delete(Path.Combine(directory, "freetower_save.json.tmp"));
                Assert.That(manager.TrySetSnapshot(replacement), Is.True, "an old error must not poison a later successful write");
                Assert.That(manager.Snapshot.roundCursor, Is.EqualTo(5));
                Assert.That(manager.TryClearSnapshot(), Is.True);
                Assert.That(manager.HasSnapshot, Is.False);
                using (var reopened = Open(sqlite, directory)) Assert.That(reopened.LoadSnapshot().valid, Is.False);
            }
            finally
            {
                if (storage != null) storage.Dispose();
                storageField.SetValue(manager, originalStorage); dataField.SetValue(manager, originalData); loadedField.SetValue(manager, originalLoaded);
                Directory.Delete(directory, true);
            }
        }
        [Test]
        public void CompleteCheckpointRestoresFinalCursorAndRejectsPartialEvidence()
        {
            var profile = Profile(); var m = Metrics(); m.combatElapsedSeconds = 99.999499123456;
            var s = new LevelSnapshot { valid = true, formatVersion = 2, levelId = 1, roundCursor = 20, hp = 20, maxHp = 20, gold = 22, metrics = m, ratingProfile = profile, levelTimerStarted = true };
            string reason;
            Assert.That(LevelCheckpointValidator.IsCompatible(s, profile, 20, out reason), Is.True, reason);
            s = JsonUtility.FromJson<LevelSnapshot>(JsonUtility.ToJson(s));
            Assert.That(s.roundCursor, Is.EqualTo(20)); Assert.That(s.metrics.combatElapsedSeconds, Is.EqualTo(m.combatElapsedSeconds));
            s.autoNextRemainingSeconds = float.NaN; Assert.That(LevelCheckpointValidator.IsCompatible(s, profile, 20, out reason), Is.False);
            s.autoNextRemainingSeconds = 0f;
            s.metrics.planHash = "another-plan"; Assert.That(LevelCheckpointValidator.IsCompatible(s, profile, 20, out reason), Is.False);
            s.metrics.planHash = profile.planHash; s.metrics.killed--; Assert.That(LevelCheckpointValidator.IsCompatible(s, profile, 20, out reason), Is.False);
            s.metrics.killed++;
            s.towers.Add(new TowerSnapshot { row = 1, col = 2, level = 1, type = 1, runtimeStateSaved = true, lastDirection = Vector2.right });
            Assert.That(LevelCheckpointValidator.IsCompatible(s, profile, 20, out reason), Is.True, reason);
            s.towers[0].fireTimer = float.PositiveInfinity; Assert.That(LevelCheckpointValidator.IsCompatible(s, profile, 20, out reason), Is.False); s.towers[0].fireTimer = 0f;
            s.towers.Add(new TowerSnapshot { row = 1, col = 2, level = 2, type = 1, runtimeStateSaved = true, lastDirection = Vector2.right }); Assert.That(LevelCheckpointValidator.IsCompatible(s, profile, 20, out reason), Is.False);
        }
        [TestCase(false)] [TestCase(true)]
        public void LegacyBackendUpgradePreservesOriginalValuesAndSettings(bool sqlite)
        {
            string directory = Path.Combine(Path.GetTempPath(), "FTProject-legacy-" + Guid.NewGuid().ToString("N")); Directory.CreateDirectory(directory);
            try
            {
                if (sqlite)
                {
                    SqliteDatabase database; string error; Assert.That(SqliteDatabase.TryOpen(Path.Combine(directory, "test.db"), out database, out error), Is.True, error);
                    using (database)
                    {
                        database.Execute("CREATE TABLE meta(k TEXT PRIMARY KEY, v TEXT)"); database.Execute("INSERT INTO meta(k,v) VALUES ('schema_version','2')");
                        database.Execute("CREATE TABLE level_progress(level_id INTEGER PRIMARY KEY, stars TEXT, best_hp_left TEXT, clear_count TEXT, last_play_at INTEGER, best_time_ms TEXT, updated_at INTEGER)");
                        database.Execute("CREATE TABLE level_snapshot(id INTEGER PRIMARY KEY, valid INTEGER, level_id INTEGER, round_cursor INTEGER, gold INTEGER, hp INTEGER, max_hp INTEGER, updated_at INTEGER)");
                        ICryptoService crypto = AesCryptoService.Create(new byte[32]);
                        database.Execute("INSERT INTO level_progress(level_id,stars,best_hp_left,clear_count,best_time_ms) VALUES (?1,?2,?3,?4,?5)", 1, crypto.Encrypt("3"), crypto.Encrypt("20"), crypto.Encrypt("7"), crypto.Encrypt("123456"));
                        database.Execute("INSERT INTO level_snapshot(id,valid,level_id,round_cursor,gold,hp,max_hp) VALUES(1,1,1,3,99,18,20)");
                    }
                }
                else File.WriteAllText(Path.Combine(directory, "freetower_save.json"), "{\"version\":1,\"levels\":[{\"levelId\":1,\"stars\":3,\"clearCount\":7,\"bestTimeMs\":123456}],\"settings\":{\"volume\":0.4,\"muted\":true,\"language\":\"zh-Hant\"},\"snapshot\":{\"valid\":true,\"levelId\":1,\"roundCursor\":3}}");
                using (var storage = Open(sqlite, directory))
                {
                    var old = storage.LoadLevels()[0]; Assert.That(old.stars, Is.EqualTo(3)); Assert.That(old.bestTimeMs, Is.EqualTo(123456)); Assert.That(old.clearCount, Is.EqualTo(7)); Assert.That(storage.LoadSnapshot().valid, Is.False);
                    if (!sqlite) { Assert.That(storage.LoadSettings().language, Is.EqualTo("zh-Hant")); Assert.That(File.Exists(Path.Combine(directory, "freetower_save.json.legacy-v1.bak")), Is.True); }
                    SaveProgressMigration.ArchiveForVersion(old, Profile().versionKey); storage.SaveLevel(old);
                }
                using (var storage = Open(sqlite, directory))
                {
                    var migrated = storage.LoadLevels()[0]; Assert.That(migrated.stars, Is.Zero); Assert.That(migrated.Cleared, Is.True); Assert.That(migrated.clearCount, Is.EqualTo(7)); Assert.That(migrated.legacy[0].stars, Is.EqualTo(3)); Assert.That(migrated.legacy[0].bestTimeMs, Is.EqualTo(123456));
                    Assert.That(SaveProgressMigration.ArchiveForVersion(migrated, Profile().versionKey), Is.False);
                }
            }
            finally { Directory.Delete(directory, true); }
        }
        [Test]
        public void JsonCommitFailurePublishesNothingAndCanBeRetriedAfterRestart()
        {
            string directory = Path.Combine(Path.GetTempPath(), "FTProject-save-failure-" + Guid.NewGuid().ToString("N")); Directory.CreateDirectory(directory);
            try
            {
                var before = new LevelProgress { levelId = 1, stars = 4, clearCount = 1, ratingVersionKey = Profile().versionKey };
                var checkpoint = new LevelSnapshot { valid = true, levelId = 1, roundCursor = 20, metrics = Metrics(), ratingProfile = Profile(), formatVersion = 2 };
                var after = new LevelProgress { levelId = 1, stars = 5, clearCount = 2, ratingVersionKey = Profile().versionKey }; after.committedRunIds.Add("run-one");
                using (var storage = Open(false, directory))
                {
                    storage.SaveLevel(before); storage.SaveSnapshot(checkpoint);
                    // File.WriteAllText cannot replace a directory. This simulates a real disk failure
                    // without relying on platform-specific permissions or a fake implementation.
                    Directory.CreateDirectory(Path.Combine(directory, "freetower_save.json.tmp"));
                    LogAssert.Expect(LogType.Warning, new Regex("\\[Save\\] 写档失败"));
                    Assert.That(storage.CommitClear(after), Is.False);
                    Assert.That(storage.LoadLevels()[0].stars, Is.EqualTo(4)); Assert.That(storage.LoadLevels()[0].clearCount, Is.EqualTo(1)); Assert.That(storage.LoadLevels()[0].committedRunIds, Is.Empty);
                    Assert.That(storage.LoadSnapshot().valid, Is.True);
                    // Returned objects must never mutate backend state by aliasing.
                    storage.LoadLevels()[0].committedRunIds.Add("fake"); storage.LoadSnapshot().valid = false;
                    Assert.That(storage.LoadLevels()[0].committedRunIds, Is.Empty); Assert.That(storage.LoadSnapshot().valid, Is.True);
                }
                Directory.Delete(Path.Combine(directory, "freetower_save.json.tmp"));
                using (var storage = Open(false, directory))
                {
                    Assert.That(storage.LoadLevels()[0].stars, Is.EqualTo(4)); Assert.That(storage.LoadSnapshot().valid, Is.True);
                    Assert.That(storage.CommitClear(after), Is.True);
                }
                using (var storage = Open(false, directory))
                {
                    Assert.That(storage.LoadLevels()[0].stars, Is.EqualTo(5)); Assert.That(storage.LoadLevels()[0].clearCount, Is.EqualTo(2)); Assert.That(storage.LoadLevels()[0].committedRunIds, Does.Contain("run-one")); Assert.That(storage.LoadSnapshot().valid, Is.False);
                }
            }
            finally { Directory.Delete(directory, true); }
        }
        [Test]
        public void JsonBackupFailureDoesNotPublishBackupAndFutureFormatsCannotBeOverwritten()
        {
            string directory = Path.Combine(Path.GetTempPath(), "FTProject-backup-failure-" + Guid.NewGuid().ToString("N")); Directory.CreateDirectory(directory);
            try
            {
                using (var storage = Open(false, directory))
                {
                    Directory.CreateDirectory(Path.Combine(directory, "freetower_kv.json.tmp"));
                    LogAssert.Expect(LogType.Warning, new Regex("\\[Save\\] 写入键值文件失败"));
                    storage.SetValue("legacy-backup", "original", true);
                    string value; Assert.That(storage.TryGetValue("legacy-backup", out value), Is.False);
                    Directory.Delete(Path.Combine(directory, "freetower_kv.json.tmp"));
                    storage.SetValue("legacy-backup", "original", true); Assert.That(storage.TryGetValue("legacy-backup", out value), Is.True); Assert.That(value, Is.EqualTo("original"));
                }
                string path = Path.Combine(directory, "freetower_save.json");
                string future = "{\"version\":999,\"levels\":[{\"levelId\":1,\"stars\":5}]}"; File.WriteAllText(path, future);
                LogAssert.Expect(LogType.Warning, new Regex("\\[Save\\] Save format is newer"));
                using (var storage = Open(false, directory))
                {
                    LogAssert.Expect(LogType.Warning, "[Save] Future-format save is read-only");
                    Assert.That(storage.CommitClear(new LevelProgress { levelId = 1, stars = 1 }), Is.False);
                    Assert.That(File.ReadAllText(path), Is.EqualTo(future));
                }
            }
            finally { Directory.Delete(directory, true); }
        }
        [Test]
        public void SqliteBusyBeginRetainsTerminalCheckpointAndRetriesSameClear()
        {
            const System.Reflection.BindingFlags fields = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic;
            string directory = Path.Combine(Path.GetTempPath(), "FTProject-busy-clear-" + Guid.NewGuid().ToString("N")); Directory.CreateDirectory(directory);
            var profile = Profile(); var pendingMetrics = Metrics(); pendingMetrics.runId = "locked-final-clear";
            var pendingResult = LevelRatingEvaluator.Evaluate(profile, pendingMetrics);
            var original = new LevelProgress { levelId = 1, stars = 4, clearCount = 2, bestTimeMs = 240000, bestCombatTimeMs = 120000, ratingVersionKey = profile.versionKey };
            original.committedRunIds.Add("previous-clear");
            var terminal = new LevelSnapshot { valid = true, formatVersion = 2, levelId = 1, roundCursor = 20, gold = 137, hp = 20, maxHp = 20, metrics = pendingMetrics, ratingProfile = profile, levelTimerStarted = true };
            var candidate = JsonUtility.FromJson<LevelProgress>(JsonUtility.ToJson(original));
            candidate.stars = 5; candidate.clearCount = 3; candidate.bestTimeMs = 200000; candidate.bestCombatTimeMs = 100000; candidate.bestRating = pendingResult;
            candidate.committedRunIds.Add(pendingMetrics.runId);
            try
            {
                using (var storage = Open(true, directory))
                {
                    storage.SaveLevel(original); storage.SaveSnapshot(terminal);
                    string progressBefore = JsonUtility.ToJson(storage.LoadLevels()[0]);
                    string checkpointBefore = JsonUtility.ToJson(storage.LoadSnapshot());
                    var database = (SqliteDatabase)storage.GetType().GetField("_db", fields).GetValue(storage);
                    database.Execute("PRAGMA busy_timeout=0");
                    SqliteDatabase other; string error;
                    Assert.That(SqliteDatabase.TryOpen(Path.Combine(directory, "test.db"), out other, out error), Is.True, error);
                    using (other)
                    using (var writer = other.BeginTransaction())
                    {
                        bool committed = true;
                        LogAssert.Expect(LogType.Warning, new Regex("\\[Save\\] Atomic clear commit failed"));
                        Assert.DoesNotThrow(() => committed = storage.CommitClear(candidate), "native BEGIN IMMEDIATE failure must reach the pending-save retry path");
                        Assert.That(committed, Is.False);
                        Assert.That(storage.LastError, Does.Contain("locked"));
                        Assert.That(JsonUtility.ToJson(storage.LoadLevels()[0]), Is.EqualTo(progressBefore), "blocked BEGIN must not publish a clear, best score, or committed runId");
                        Assert.That(JsonUtility.ToJson(storage.LoadSnapshot()), Is.EqualTo(checkpointBefore), "the complete terminal checkpoint remains available while the writer lock is held");
                        writer.Rollback();
                    }
                    Assert.That(storage.CommitClear(candidate), Is.True, "release the real writer lock and retry the exact same frozen result");
                    Assert.That(storage.LastError, Is.Null, "a successful retry clears the previous operation error");
                    Assert.That(storage.LoadSnapshot().valid, Is.False);
                    var committedProgress = storage.LoadLevels()[0];
                    Assert.That(committedProgress.clearCount, Is.EqualTo(3));
                    Assert.That(committedProgress.committedRunIds, Is.EqualTo(candidate.committedRunIds));
                    Assert.That(committedProgress.bestRating.metrics.runId, Is.EqualTo(pendingMetrics.runId));
                    Assert.That(committedProgress.bestRating.metrics.combatElapsedSeconds, Is.EqualTo(pendingMetrics.combatElapsedSeconds));
                }
                using (var reopened = Open(true, directory))
                {
                    Assert.That(JsonUtility.ToJson(reopened.LoadLevels()[0]), Is.EqualTo(JsonUtility.ToJson(candidate)));
                    Assert.That(reopened.LoadSnapshot().valid, Is.False, "restart observes one committed clear and the atomically removed checkpoint");
                }
            }
            finally { Directory.Delete(directory, true); }
        }
        [Test]
        public void SqliteFailedCommitThrowsAndNestedRollbackCannotCommit()
        {
            string directory = Path.Combine(Path.GetTempPath(), "FTProject-tx-failure-" + Guid.NewGuid().ToString("N")); Directory.CreateDirectory(directory);
            try
            {
                SqliteDatabase database; string error; Assert.That(SqliteDatabase.TryOpen(Path.Combine(directory, "test.db"), out database, out error), Is.True, error);
                using (database)
                {
                    database.Execute("CREATE TABLE sample(id INTEGER PRIMARY KEY)");
                    using (var tx = database.BeginTransaction())
                    {
                        database.Execute("INSERT INTO sample(id) VALUES(1)");
                        database.Execute("ROLLBACK"); // Force the actual native COMMIT to fail.
                        Assert.Throws<DatabaseException>(() => tx.Commit());
                    }
                    Assert.That(database.QueryScalar<int>("SELECT COUNT(*) FROM sample", -1), Is.Zero);
                    using (var outer = database.BeginTransaction())
                    {
                        database.Execute("INSERT INTO sample(id) VALUES(2)");
                        using (var inner = database.BeginTransaction()) { inner.Rollback(); }
                        Assert.Throws<DatabaseException>(() => outer.Commit());
                    }
                    Assert.That(database.QueryScalar<int>("SELECT COUNT(*) FROM sample", -1), Is.Zero);
                    using (var retry = database.BeginTransaction()) { database.Execute("INSERT INTO sample(id) VALUES(3)"); retry.Commit(); }
                    Assert.That(database.QueryScalar<int>("SELECT COUNT(*) FROM sample", -1), Is.EqualTo(1));
                }
            }
            finally { Directory.Delete(directory, true); }
        }
    }
}
