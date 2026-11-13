using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text.RegularExpressions;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace FTProject.Tests
{
    // Use real backends in a temporary directory; never replace or dispose the player's storage.
    public sealed class WaveHistoryPersistenceTests
    {
        private static readonly FieldInfo Storage = typeof(SaveManager).GetField("_storage", BindingFlags.Instance | BindingFlags.NonPublic);
        private static readonly FieldInfo Loaded = typeof(SaveManager).GetField("_loaded", BindingFlags.Instance | BindingFlags.NonPublic);
        private string _directory;
        private object _previousStorage, _previousLoaded;
        private ISaveStorage _storage;
        private SqliteDatabase _db;

        [SetUp]
        public void Setup()
        {
            _directory = Path.Combine(Path.GetTempPath(), "FT-wave-history-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(_directory);
            _previousStorage = Storage.GetValue(SaveManager.Instance);
            _previousLoaded = Loaded.GetValue(SaveManager.Instance);
            Loaded.SetValue(SaveManager.Instance, true);
        }

        [TearDown]
        public void Cleanup()
        {
            Storage.SetValue(SaveManager.Instance, _previousStorage);
            Loaded.SetValue(SaveManager.Instance, _previousLoaded);
            if (_storage != null) _storage.Dispose();
            Directory.Delete(_directory, true);
        }

        private void Open(bool sqlite)
        {
            if (_storage != null) _storage.Dispose();
            if (sqlite)
            {
                string error;
                Assert.That(SqliteDatabase.TryOpen(Path.Combine(_directory, "waves.db"), out _db, out error), Is.True, error);
                _storage = new SqliteSaveStorage(_db, null);
            }
            else _storage = new JsonSaveStorage(null, _directory);
            _storage.Initialize();
            Storage.SetValue(SaveManager.Instance, _storage);
        }

        private static WaveRestartHistory History(int level = 1, string run = "run-one")
        {
            var result = new WaveRestartHistory { levelId = level, runId = run, contentSignature = "test-content", roundIds = new List<int> { 11, 12, 13 } };
            for (int cursor = 0; cursor < 3; cursor++)
            {
                var metrics = new LevelRunMetrics { runId = run, completedWaveCount = cursor, hp = 9, maxHp = 10,
                    expectedWaveCount = 3, expectedEnemyCount = 6, killed = cursor * 2, successfulSpawned = cursor * 2,
                    combatElapsedSeconds = cursor * 1.25, levelElapsedSeconds = cursor * 2.5 };
                for (int i = 0; i < cursor; i++) metrics.waves.Add(new WaveRunMetrics { ordinal = i + 1, expected = 2, killed = 2, successfulSpawned = 2 });
                var layout = new LevelLayout { levelId = level, roundCursor = cursor, resourcesSaved = true, runSaved = true,
                    gold = 100 + cursor * 7, goldCarry = .375f, hp = 9, maxHp = 10, runMetrics = metrics,
                    towerCount = 1, levelTimerStarted = cursor > 0,
                    towers = new List<TowerLayoutEntry> { new TowerLayoutEntry { row = 2, col = 3, type = 1, level = 2, investedGold = 87, hasInvested = true } } };
                result.checkpoints.Add(new WaveRestartCheckpoint { layout = layout, roundId = result.roundIds[cursor],
                    goldCarry = layout.goldCarry, killed = metrics.killed, combatSeconds = metrics.combatElapsedSeconds,
                    levelSeconds = metrics.levelElapsedSeconds, timerStarted = layout.levelTimerStarted,
                    towerStates = new List<TowerSnapshot> { new TowerSnapshot { row = 2, col = 3, type = 1, level = 2 } } });
            }
            return result;
        }

        private static string ReadPair(int level)
        {
            LevelLayout layout; WaveRestartHistory history;
            Assert.That(LevelLayoutStore.TryGet(level, out layout, out history), Is.True);
            var book = new LevelLayoutBook(); book.levels.Add(layout); if (history != null) book.waveHistories.Add(history);
            return JsonUtility.ToJson(book);
        }

        [TestCase(false)]
        [TestCase(true)]
        public void ReopenRestoresCompleteIndependentPairAndOtherLevel(bool sqlite)
        {
            Open(sqlite);
            var history = History();
            string expected = JsonUtility.ToJson(history);
            Assert.That(LevelLayoutStore.SaveCapturedLevel(history.checkpoints[2].layout, history), Is.True);
            var other = History(2, "run-two");
            Assert.That(LevelLayoutStore.SaveCapturedLevel(other.checkpoints[2].layout, other), Is.True);
            history.checkpoints[0].layout.gold = 9999;
            history.checkpoints[1].layout.runMetrics.waves[0].killed = 999;
            history.checkpoints.Clear();
            Open(sqlite);
            LevelLayout layout; WaveRestartHistory restored;
            Assert.That(LevelLayoutStore.TryGet(1, out layout, out restored), Is.True);
            Assert.That(JsonUtility.ToJson(restored), Is.EqualTo(expected));
            Assert.That(layout.gold, Is.EqualTo(114));
            Assert.That(layout.goldCarry, Is.EqualTo(.375f));
            Assert.That(layout.runMetrics.runId, Is.EqualTo("run-one"));
            restored.checkpoints[0].layout.gold = -10;
            layout.runMetrics.waves.Clear();
            Assert.That(LevelLayoutStore.TryGet(1, out layout, out restored), Is.True);
            Assert.That(JsonUtility.ToJson(restored), Is.EqualTo(expected), "Reads cannot mutate persisted history");
            Assert.That(layout.runMetrics.waves.Count, Is.EqualTo(2));
            Assert.That(LevelLayoutStore.TryGet(2, out layout, out restored), Is.True);
            Assert.That(restored.runId, Is.EqualTo("run-two"));
        }

        [TestCase(false)]
        [TestCase(true)]
        public void FailedReplacementRetainsOldPrimaryAndHistoryAfterReopen(bool sqlite)
        {
            Open(sqlite);
            var history = History();
            Assert.That(LevelLayoutStore.SaveCapturedLevel(history.checkpoints[2].layout, history), Is.True);
            string before = ReadPair(1);
            if (sqlite)
                _db.Execute("CREATE TRIGGER wave_history_abort BEFORE INSERT ON kv_store WHEN NEW.k='layout/campaign' BEGIN SELECT RAISE(ABORT,'wave-history-test-failure'); END");
            else Directory.CreateDirectory(Path.Combine(_directory, "freetower_kv.json.tmp"));
            LogAssert.Expect(LogType.Warning, new Regex(sqlite ? ".*写入键值.*失败.*" : ".*写入键值文件失败.*", RegexOptions.Singleline));
            history.checkpoints.RemoveAt(2);
            Assert.That(LevelLayoutStore.SaveCapturedLevel(history.checkpoints[1].layout, history), Is.False);
            Assert.That(ReadPair(1), Is.EqualTo(before));
            if (sqlite) _db.Execute("DROP TRIGGER wave_history_abort");
            else Directory.Delete(Path.Combine(_directory, "freetower_kv.json.tmp"));
            Open(sqlite);
            Assert.That(ReadPair(1), Is.EqualTo(before), "A failed write must not persist half of the replacement");
            Assert.That(LevelLayoutStore.SaveCapturedLevel(history.checkpoints[1].layout, history), Is.True);
            Open(sqlite);
            LevelLayout layout; WaveRestartHistory read;
            Assert.That(LevelLayoutStore.TryGet(1, out layout, out read), Is.True);
            Assert.That(layout.roundCursor, Is.EqualTo(1));
            Assert.That(read.checkpoints.Count, Is.EqualTo(2));
        }

        [TestCase(false)]
        [TestCase(true)]
        public void NewRunAndCompletedReplayReplaceOnlyTheirOwnHistory(bool sqlite)
        {
            Open(sqlite);
            var old = History(); var other = History(2, "other");
            Assert.That(LevelLayoutStore.SaveCapturedLevel(old.checkpoints[2].layout, old), Is.True);
            Assert.That(LevelLayoutStore.SaveCapturedLevel(other.checkpoints[2].layout, other), Is.True);
            string otherBefore = ReadPair(2);
            var fresh = History(1, "new-run");
            var initial = fresh.checkpoints[0].layout;
            fresh.checkpoints.Clear();
            Assert.That(LevelLayoutStore.SaveCapturedLevel(initial, fresh), Is.True);
            Open(sqlite);
            LevelLayout layout; WaveRestartHistory history;
            Assert.That(LevelLayoutStore.TryGet(1, out layout, out history), Is.True);
            Assert.That(layout.roundCursor, Is.Zero);
            Assert.That(history.runId, Is.EqualTo("new-run"));
            Assert.That(history.checkpoints, Is.Empty);
            layout.runSaved = false; layout.runMetrics = null;
            Assert.That(LevelLayoutStore.SaveCapturedLevel(layout), Is.True);
            Open(sqlite);
            Assert.That(LevelLayoutStore.TryGet(1, out layout, out history), Is.True);
            Assert.That(history, Is.Null);
            Assert.That(ReadPair(2), Is.EqualTo(otherBefore));
        }

        [Test]
        public void LegacyBookAndMismatchedPairCannotAttachForeignHistory()
        {
            Open(false);
            var h = History();
            var layout = h.checkpoints[2].layout;
            SaveManager.Instance.SetUserValue(LevelLayoutStore.StorageKey,
                "{\"formatVersion\":1,\"levels\":[" + JsonUtility.ToJson(layout) + "]}", true);
            Open(false);
            LevelLayout read; WaveRestartHistory history;
            Assert.That(LevelLayoutStore.TryGet(1, out read, out history), Is.True);
            Assert.That(read.roundCursor, Is.EqualTo(2)); Assert.That(history, Is.Null);
            string before = ReadPair(1);
            h.runId = "foreign";
            Assert.That(LevelLayoutStore.SaveCapturedLevel(layout, h), Is.False);
            Assert.That(ReadPair(1), Is.EqualTo(before));
            h.runId = layout.runMetrics.runId;
            Assert.That(LevelLayoutStore.SaveCapturedLevel(h.checkpoints[0].layout, h), Is.False, "Future entries cannot be saved behind the current cursor");
            Assert.That(ReadPair(1), Is.EqualTo(before));
        }
    }
}
