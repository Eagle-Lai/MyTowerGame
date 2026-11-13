using NUnit.Framework;

namespace FTProject.Tests
{
    public sealed class WaveRestartCheckpointTests
    {
        private int _level, _gold, _hp, _maxHp, _killed, _leaked;
        private float _carry;
        private bool _gameOver;

        [SetUp]
        public void RememberPlayer()
        {
            var p = PlayerDataManager.Instance;
            _level = p.CurrentLevelId; _gold = p.Gold; _hp = p.Hp; _maxHp = p.MaxHp;
            _killed = p.TotalKilled; _leaked = p.TotalLeaked; _carry = p.GoldCarry;
            _gameOver = p.IsGameOver;
        }

        [TearDown]
        public void RestorePlayer()
        {
            PlayerDataManager.Instance.RestoreState(_level, _gold, _hp, _maxHp, _killed, _leaked, _carry);
            // Editor's uninitialized player may legitimately have maxHp=0 or a finished run.
            typeof(PlayerDataManager).GetProperty("MaxHp").SetValue(PlayerDataManager.Instance, _maxHp, null);
            typeof(PlayerDataManager).GetProperty("IsGameOver").SetValue(PlayerDataManager.Instance, _gameOver, null);
        }

        [Test]
        public void RetryingRestoresFractionalRewardsWithoutDuplicatingWaveIncome()
        {
            var p = PlayerDataManager.Instance;
            p.RestoreState(1, 120, 9, 10, 30, 1, .75f);
            p.AddGold(6.5f);
            p.OnEnemyKilled();
            p.LoseHp(1);
            p.RestoreState(1, 120, 9, 10, 30, 1, .75f);
            p.AddGold(.5f);
            Assert.That(p.Gold, Is.EqualTo(121));
            Assert.That(p.GoldCarry, Is.EqualTo(.25f));
            Assert.That(p.Hp, Is.EqualTo(9));
            Assert.That(p.TotalKilled, Is.EqualTo(30));
            Assert.That(p.TotalLeaked, Is.EqualTo(1));
        }

        [TestCase(.99999f)]
        [TestCase(.9999999f)]
        [TestCase(1f)]
        [TestCase(1.00001f)]
        public void RewardRoundingNeverCreatesAnInvalidCheckpointCarry(float reward)
        {
            var p = PlayerDataManager.Instance;
            p.RestoreState(1, 100, 10, 10);
            for (int i = 0; i < 100; i++)
            {
                p.AddGold(reward);
                Assert.That(p.GoldCarry, Is.GreaterThanOrEqualTo(0).And.LessThan(1));
            }
        }

        [Test]
        public void LayoutCaptureAndResourceRestorePreserveFractionalGoldAndClock()
        {
            var p = PlayerDataManager.Instance;
            double combat = GameClock.CombatElapsedSeconds, level = GameClock.LevelElapsedSeconds;
            bool running = GameClock.IsLevelTimerRunning;
            try
            {
                p.RestoreState(1, 100, 9, 10, 0, 0, .875f);
                GameClock.RestoreTimers(12.5, 19.75, true);
                var run = new LevelRunMetrics();
                var layout = LevelLayoutStore.CaptureCurrentLevel(1, 0, run);
                Assert.That(layout.goldCarry, Is.EqualTo(.875f));
                Assert.That(layout.runMetrics.combatElapsedSeconds, Is.EqualTo(12.5));
                Assert.That(layout.runMetrics.levelElapsedSeconds, Is.EqualTo(19.75));
                Assert.That(run.combatElapsedSeconds, Is.Zero, "Capture must not mutate its source");
                p.AddGold(.5f);
                LevelLayoutStore.RestoreResources(layout);
                p.AddGold(.25f);
                Assert.That(p.Gold, Is.EqualTo(101));
                Assert.That(p.GoldCarry, Is.EqualTo(.125f));
            }
            finally { GameClock.RestoreTimers(combat, level, running); }
        }

        [Test]
        public void PauseAndResumeCannotRechargeTheCurrentFrame()
        {
            bool paused = GameClock.IsPaused;
            float speed = GameClock.Speed;
            double combat = GameClock.CombatElapsedSeconds, level = GameClock.LevelElapsedSeconds;
            bool running = GameClock.IsLevelTimerRunning;
            try
            {
                GameClock.SetPaused(false); GameClock.Speed = 1;
                GameClock.RestoreTimers(3, 5, true);
                GameClock.RefreshFrame(UnityEngine.Time.frameCount + 1, .1f);
                double elapsed = GameClock.LevelElapsedSeconds;
                GameClock.SetPaused(true);
                Assert.That(GameClock.DeltaTime, Is.Zero);
                Assert.That(GameClock.LevelElapsedSeconds, Is.EqualTo(elapsed));
                GameClock.RefreshFrame(UnityEngine.Time.frameCount + 2, .1f);
                Assert.That(GameClock.DeltaTime, Is.Zero);
                Assert.That(GameClock.LevelElapsedSeconds, Is.EqualTo(elapsed));
                GameClock.SetPaused(false);
                Assert.That(GameClock.DeltaTime, Is.Zero);
                Assert.That(GameClock.LevelElapsedSeconds, Is.EqualTo(elapsed));
                GameClock.RefreshFrame(UnityEngine.Time.frameCount + 3, .1f);
                Assert.That(GameClock.LevelElapsedSeconds, Is.EqualTo(elapsed + .1f).Within(.000001));
                GameClock.RestoreTimers(3, 5, true);
                Assert.That(GameClock.DeltaTime, Is.Zero, "Restoration must discard the abandoned frame step");
            }
            finally { GameClock.Speed = speed; GameClock.SetPaused(paused); GameClock.RestoreTimers(combat, level, running); }
        }

        [TestCase(GameFlowState.Preparing)]
        [TestCase(GameFlowState.RoundRunning)]
        public void DisplayedWaveNumberUsesTheSameCursorInPreparationAndCombat(GameFlowState state)
        {
            using (var fixture = new HistoryFixture())
            {
                fixture.SetState(state);
                fixture.SetFlow("_roundCursor", 0);
                Assert.That(fixture.flow.CurrentRoundIndex, Is.EqualTo(1));
                Assert.That(fixture.flow.CompletedRoundCount, Is.Zero);
                fixture.SetFlow("_roundCursor", 4);
                Assert.That(fixture.flow.CurrentRoundIndex, Is.EqualTo(5));
                Assert.That(fixture.flow.CompletedRoundCount, Is.EqualTo(4));
            }
        }

        [TestCase("ordinal")]
        [TestCase("spawned")]
        [TestCase("killed")]
        [TestCase("leaked")]
        [TestCase("boss")]
        public void HistoryRejectsMismatchedPerWaveAndGlobalAccounting(string fault)
        {
            using (var fixture = new HistoryFixture())
            {
                var metrics = fixture.layout.runMetrics;
                fixture.layout.roundCursor = 1;
                metrics.completedWaveCount = 1;
                metrics.successfulSpawned = 3; metrics.killed = 2; metrics.leaked = 1;
                metrics.waves.Add(new WaveRunMetrics { ordinal = 1, expected = 3, successfulSpawned = 3, killed = 2, leaked = 1 });
                fixture.SetCheckpoint("roundId", fixture.flow.Level.RoundIds[1]);
                fixture.SetCheckpoint("killed", 2); fixture.SetCheckpoint("leaked", 1);
                fixture.SetFlow("_roundCursor", 2);
                var checkpoint = fixture.history[0]; fixture.history.Clear(); fixture.history.Add(1, checkpoint);
                Assert.That(fixture.flow.CanRestartPreviousWave, Is.True);
                if (fault == "ordinal") metrics.waves[0].ordinal = 2;
                if (fault == "spawned") metrics.successfulSpawned++;
                if (fault == "killed") metrics.killed++;
                if (fault == "leaked") metrics.waves[0].leaked++;
                if (fault == "boss") metrics.waves[0].bossLeaked = 2;
                Assert.That(fixture.flow.CanRestartPreviousWave, Is.False);
                Assert.That(fixture.flow.RestartPreviousWave(), Is.False);
            }
        }

        [Test]
        public void CheckpointCaptureKeepsIndependentCompletedWaveStatistics()
        {
            var run = new LevelRunMetrics { runId = "checkpoint-test", completedWaveCount = 1, killed = 12 };
            run.waves.Add(new WaveRunMetrics { ordinal = 1, killed = 12 });
            var checkpoint = LevelLayoutStore.CaptureCurrentLevel(1, 1, run);
            run.killed += 3;
            run.waves[0].killed = 999;
            run.waves.Add(new WaveRunMetrics { ordinal = 2, killed = 3 });
            Assert.That(checkpoint.roundCursor, Is.EqualTo(1));
            Assert.That(checkpoint.runMetrics.killed, Is.EqualTo(12));
            Assert.That(checkpoint.runMetrics.waves.Count, Is.EqualTo(1));
            Assert.That(checkpoint.runMetrics.waves[0].killed, Is.EqualTo(12));
        }

        [TestCase(GameFlowState.Preparing, true)]
        [TestCase(GameFlowState.RoundRunning, true)]
        [TestCase(GameFlowState.None, false)]
        [TestCase(GameFlowState.Loading, false)]
        [TestCase(GameFlowState.GameOver, false)]
        public void PreviousWaveRequiresLiveRunAndImmediateHistory(GameFlowState state, bool expected)
        {
            using (var fixture = new HistoryFixture())
            {
                fixture.SetState(state);
                Assert.That(fixture.flow.CanRestartPreviousWave, Is.EqualTo(expected));
                fixture.history.Clear();
                Assert.That(fixture.flow.CanRestartPreviousWave, Is.False, "Never skip a missing wave checkpoint");
            }
        }

        [TestCase("run")]
        [TestCase("level")]
        [TestCase("round")]
        [TestCase("metrics")]
        [TestCase("hp")]
        [TestCase("carry")]
        [TestCase("timer")]
        [TestCase("modal")]
        [TestCase("restoring")]
        [TestCase("settled")]
        public void InvalidOrBusyHistoryCannotChangePlayerData(string fault)
        {
            using (var fixture = new HistoryFixture())
            {
                Assert.That(fixture.flow.CanRestartPreviousWave, Is.True);
                if (fault == "run") fixture.layout.runMetrics.runId = "another-run";
                if (fault == "level") fixture.layout.levelId++;
                if (fault == "round") fixture.SetCheckpoint("roundId", -1);
                if (fault == "metrics") fixture.layout.runMetrics.completedWaveCount = 3;
                if (fault == "hp") fixture.layout.hp = 0;
                if (fault == "carry") fixture.SetCheckpoint("goldCarry", float.NaN);
                if (fault == "timer") fixture.SetCheckpoint("levelSeconds", double.PositiveInfinity);
                if (fault == "modal") fixture.SetFlow("_restartWaveConfirmOpen", true);
                if (fault == "restoring") fixture.SetFlow("_restoringWave", true);
                if (fault == "settled") fixture.SetFlow("_settled", true);
                var p = PlayerDataManager.Instance;
                int gold = p.Gold, hp = p.Hp;
                Assert.That(fixture.flow.CanRestartPreviousWave, Is.False);
                Assert.That(fixture.flow.RestartPreviousWave(), Is.False);
                Assert.That(p.Gold, Is.EqualTo(gold));
                Assert.That(p.Hp, Is.EqualTo(hp));
            }
        }

        [Test]
        public void FirstWavePreparationAndRunningCannotGoBackFurther()
        {
            using (var fixture = new HistoryFixture())
            {
                fixture.SetFlow("_roundCursor", 0);
                Assert.That(fixture.flow.CanRestartPreviousWave, Is.False);
                fixture.SetState(GameFlowState.RoundRunning);
                Assert.That(fixture.flow.CanRestartPreviousWave, Is.False);
                Assert.That(fixture.flow.RestartPreviousWave(), Is.False);
            }
        }

        [TestCase(double.NaN)]
        [TestCase(double.PositiveInfinity)]
        [TestCase(-1d)]
        [TestCase(1d)]
        public void InvalidRepeatedClockCannotBeUsedAsCheckpoint(double seconds)
        {
            using (var fixture = new HistoryFixture())
            {
                Assert.That(fixture.flow.CanRestartPreviousWave, Is.True);
                fixture.layout.runMetrics.combatElapsedSeconds = seconds;
                Assert.That(fixture.flow.CanRestartPreviousWave, Is.False);
                fixture.layout.runMetrics.combatElapsedSeconds = 0;
                fixture.layout.runMetrics.levelElapsedSeconds = seconds;
                Assert.That(fixture.flow.CanRestartPreviousWave, Is.False);
            }
        }

        // Inactive fixture does not run Awake/OnEnable or subscribe to the live event dispatcher.
        private sealed class HistoryFixture : System.IDisposable
        {
            private const System.Reflection.BindingFlags Flags = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic;
            private readonly UnityEngine.GameObject owner;
            private readonly object checkpoint;
            public readonly GameFlowManager flow;
            public readonly LevelLayout layout;
            public readonly System.Collections.IDictionary history;

            public HistoryFixture()
            {
                owner = new UnityEngine.GameObject("wave-history-test");
                owner.SetActive(false);
                flow = owner.AddComponent<GameFlowManager>();
                var json = SimpleJSON.JSON.Parse(System.IO.File.ReadAllText(UnityEngine.Application.dataPath + "/ConfigJson/tbsceneinfo.json"));
                var level = new LevelConfig(new cfg.SceneInfo(json[0]));
                typeof(GameFlowManager).GetProperty("Level").SetValue(flow, level, null);
                SetFlow("_roundIds", new System.Collections.Generic.List<int>(level.RoundIds));
                SetFlow("_roundCursor", 1);
                SetFlow("_run", new LevelRunMetrics { runId = "history-test" });
                SetState(GameFlowState.Preparing);
                layout = new LevelLayout { levelId = level.Id, roundCursor = 0, resourcesSaved = true,
                    runSaved = true, gold = 100, hp = 10, maxHp = 10,
                    runMetrics = new LevelRunMetrics { runId = "history-test" },
                    towers = new System.Collections.Generic.List<TowerLayoutEntry>() };
                checkpoint = new WaveRestartCheckpoint();
                SetCheckpoint("layout", layout);
                SetCheckpoint("roundId", level.RoundIds[0]);
                history = (System.Collections.IDictionary)typeof(GameFlowManager).GetField("_waveRestartHistory", Flags).GetValue(flow);
                history.Add(0, checkpoint);
            }

            public void SetState(GameFlowState state) { typeof(GameFlowManager).GetProperty("State").SetValue(flow, state, null); }
            public void SetFlow(string name, object value) { typeof(GameFlowManager).GetField(name, Flags).SetValue(flow, value); }
            public void SetCheckpoint(string name, object value) { checkpoint.GetType().GetField(name).SetValue(checkpoint, value); }
            public void Dispose() { UnityEngine.Object.DestroyImmediate(owner); }
        }
    }
}
