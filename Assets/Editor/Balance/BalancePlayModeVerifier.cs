using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using SimpleJSON;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// Fixed-step PlayMode replay of the actual scene, WaveManager, CombatSystem, towers,
    /// enemies, A*, economy and sole rating evaluator. It never grants money or skips waves.
    /// </summary>
    [InitializeOnLoad]
    public static class BalancePlayModeVerifier
    {
        private const string RequestKey = "FT.Balance.PlayRequest";
        private static JSONNode _request;
        private static readonly List<JSONNode> Runs = new List<JSONNode>();
        private static readonly List<JSONNode> Operations = new List<JSONNode>();
        private static readonly List<JSONNode> Results = new List<JSONNode>();
        private static readonly List<JSONNode> Boundaries = new List<JSONNode>();
        private static readonly List<JSONNode> EnemyOutcomes = new List<JSONNode>();
        private static readonly List<JSONNode> OperationStages = new List<JSONNode>();
        private static int _initialGold, _initialHp;
        private static readonly List<double> StepCosts = new List<double>();
        private static long _allocatedStart;
        private static string _out, _requestPath, _loadedCandidate, _oldStartScene;
        private static int _runIndex, _shopWave = -1;
        private static double _startWall, _runWall;
        private static bool _initialized, _levelInitialized, _launcherEnabled, _flowEnabled;
        private static IDisposable _manualClock;
        private static Action _flowLate;
        private static JSONNode _plannedOperations;
        private static string _operationError;
        private static bool _waitForFunds;
        private static bool _performanceScreensCaptured;
        private static string _pendingScreenshot;
        private static int _pendingScreenshotWave;
        private static readonly HashSet<int> ReplayedOperations = new HashSet<int>();
        private static int _teardownFrame = -1;
        private static readonly FieldInfo RunField = typeof(GameFlowManager).GetField("_run", BindingFlags.Instance | BindingFlags.NonPublic);
        public static bool Running { get { return !string.IsNullOrEmpty(SessionState.GetString(RequestKey, "")); } }

        static BalancePlayModeVerifier()
        {
            EditorApplication.playModeStateChanged += ModeChanged;
            EditorApplication.update += Update;
        }

        [MenuItem("Tools/塔防/数值验证/运行隔离回放")]
        public static void RunSelected()
        {
            string root = BalanceWorkbenchProcess.ProjectRoot;
            string profile = SessionState.GetString("FT.Balance.TestProfile", "D04");
            JSONNode request = new JSONObject();
            request["output"] = Path.Combine(root, "Library/BalanceWorkbench/PlayMode-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss"));
            request["stepSeconds"] = .05; request["stepsPerUpdate"] = 40;
            request["runs"] = new JSONArray();
            JSONNode run = new JSONObject();
            run["profileId"] = profile; run["levelId"] = SessionState.GetInt("FT.Balance.TestLevel", 1);
            run["strategy"] = SessionState.GetString("FT.Balance.TestStrategy", "mixed"); run["speed"] = 1;
            string candidatePlan = SessionState.GetString("FT.Balance.TestCandidatePlan", "");
            if (File.Exists(candidatePlan))
            {
                JSONNode plan = JSON.Parse(File.ReadAllText(candidatePlan));
                if (plan["profileId"].Value != profile) throw new InvalidOperationException("Candidate profile differs from selection. Generate a new preview.");
                string draftPath = Path.Combine(root, "Library/BalanceWorkbench/draft.json");
                if (File.Exists(draftPath) && JSON.Parse(File.ReadAllText(draftPath)).ToString() != plan["recipe"].ToString())
                    throw new InvalidOperationException("Draft changed since candidate generation. Generate and validate a fresh preview before replay.");
                string candidate = Path.Combine(Path.GetDirectoryName(candidatePlan), "PlayCandidate"); Directory.CreateDirectory(candidate);
                foreach (var kv in plan["tables"]) File.WriteAllText(Path.Combine(candidate, kv.Key + ".json"), kv.Value.ToString(2));
                run["candidateDirectory"] = candidate;
            }
            else if (profile != "D04") throw new InvalidOperationException("Generate the selected candidate before replaying it.");
            request["runs"].Add(run);
            string path = Path.Combine(root, "Library/BalanceWorkbench/play-request.json");
            Directory.CreateDirectory(Path.GetDirectoryName(path)); File.WriteAllText(path, request.ToString(2));
            StartBatch(path);
        }

        public static void StartBatch(string requestPath)
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorUtility.scriptCompilationFailed || Running)
                throw new InvalidOperationException("Replay requires an idle EditMode editor.");
            _requestPath = Path.GetFullPath(requestPath);
            if (!File.Exists(_requestPath)) throw new FileNotFoundException(_requestPath);
            JSON.Parse(File.ReadAllText(_requestPath));
            SessionState.SetString(RequestKey, _requestPath);
            SessionState.SetString("FT.Balance.TestStorageContext", "replay-" + Guid.NewGuid().ToString("N"));
            _oldStartScene = EditorSceneManager.playModeStartScene != null ? AssetDatabase.GetAssetPath(EditorSceneManager.playModeStartScene) : "";
            SessionState.SetString("FT.Balance.OldStartScene", _oldStartScene);
            var scene = AssetDatabase.LoadAssetAtPath<SceneAsset>("Assets/Scenes/main.unity");
            if (scene == null) throw new FileNotFoundException("Assets/Scenes/main.unity");
            EditorSceneManager.playModeStartScene = scene;
            EditorApplication.isPlaying = true;
        }

        [MenuItem("Tools/塔防/数值验证/停止隔离回放")]
        public static void Cancel()
        {
            if (!Running) return;
            if (!string.IsNullOrEmpty(_out)) File.WriteAllText(Path.Combine(_out, "cancel.request"), "cancel");
            Finish("cancelled");
        }

        [MenuItem("Tools/塔防/数值验证/录制关卡视频（单关）")]
        public static void RunVideoCapture()
        {
            StartVideoBatch(new[] { SessionState.GetInt("FT.Balance.TestLevel", 2) });
        }

        [MenuItem("Tools/塔防/数值验证/录制全部关卡视频（L01-L30）")]
        public static void RunAllVideoCaptures()
        {
            var levels = new List<int>();
            for (int i = 1; i <= 30; i++) levels.Add(i);
            StartVideoBatch(levels.ToArray());
        }

        private static void StartVideoBatch(int[] levels)
        {
            string root = BalanceWorkbenchProcess.ProjectRoot;
            string evidence = Path.Combine(root, "Docs/BalanceEvidence/L02-L30-ManualBalance-100Gold");
            string ffmpeg = ResolveFfmpeg();
            double videoSpeed = SessionState.GetFloat("FT.Balance.VideoSpeed", 2f);
            var skipped = new List<string>();

            JSONNode request = new JSONObject();
            request["output"] = Path.Combine(root, "Library/BalanceWorkbench/Video-Batch");
            // 0.02s matches the step used by the stored evidence; capture samples every Nth
            // tick so the mp4 stays smooth without changing combat results.
            request["stepSeconds"] = 0.02;
            request["stepsPerUpdate"] = 1;
            request["batchTimeoutSeconds"] = 36000;
            request["keepPlaying"] = false;
            request["runs"] = new JSONArray();

            foreach (int level in levels)
            {
                string levelTag = "L" + level.ToString("00");
                string operations = level == 1
                    ? Path.Combine(evidence, "L01-reference/best-operations.json")
                    : Path.Combine(evidence, levelTag, "best-operations.json");
                if (!File.Exists(operations))
                    throw new FileNotFoundException("Operations not found: " + operations);
                JSONNode planned = JSON.Parse(File.ReadAllText(operations));
                if (planned == null || planned.Count == 0)
                    throw new InvalidDataException("Operations file is empty: " + operations);

                // Flat layout since 2026-10-24 (user request): every cut lands directly in
                // Docs/LevelVideos/ instead of a per-level subfolder. The recorder derives the
                // frame dir (_frames_Lxx_完整通关) and the run log from this same path.
                string videoPath = Path.Combine(root, "Docs/LevelVideos", levelTag + "_完整通关.mp4");
                // Resume support: a multi-hour batch must not re-render a level that already has a
                // valid cut, otherwise any restart costs a full pass over the finished levels.
                // 16MB is far below a real cut (shortest level is ~80MB) but far above a truncated one.
                // The size alone is not enough: ffmpeg writes the mp4 incrementally, so a level
                // caught mid-encode looks "done" by size (L10 on 2026-10-23 sat at 276MB while
                // its end line was still seconds away). The recorder's run log is the authority.
                string delivered = BalanceVideoRecorder.DeliveredPath(videoPath, videoSpeed);
                string runLog = Path.ChangeExtension(videoPath, ".log.txt");
                bool finished = File.Exists(runLog)
                    && File.ReadAllText(runLog).Contains("end ok=True");
                if (finished && File.Exists(delivered) && new FileInfo(delivered).Length > 16L * 1024 * 1024)
                {
                    skipped.Add(levelTag);
                    continue;
                }

                JSONNode run = new JSONObject();
                run["profileId"] = SessionState.GetString("FT.Balance.TestProfile", "D04");
                run["levelId"] = level; run["strategy"] = "replay"; run["speed"] = 1;
                run["waitForFunds"] = false; run["captureStages"] = false; run["screenshots"] = false;
                run["operationsPath"] = operations; run["wallTimeoutSeconds"] = 7200;
                run["recordVideo"] = true;
                run["videoOutput"] = videoPath;
                run["videoWidth"] = 1280; run["videoHeight"] = 720; run["videoFps"] = 15;
                run["videoFfmpeg"] = ffmpeg;
                // Delivered playback speed. The in-game 2x/3x toggle cannot speed up a fixed-step
                // replay (step / Speed is multiplied back by Speed inside GameClock), so the speed
                // is applied at encode time by declaring a higher input framerate. Only the fast
                // cut is written (user decision 2026-10-23); no separate 1x master.
                run["videoSpeed"] = videoSpeed;
                request["runs"].Add(run);
            }

            if (request["runs"].Count == 0)
            {
                UnityEngine.Debug.Log("[BalanceVideo] nothing to record: all " + levels.Length +
                                      " levels already have a valid cut.");
                return;
            }

            string path = Path.Combine(root, "Library/BalanceWorkbench/video-request-batch.json");
            Directory.CreateDirectory(Path.GetDirectoryName(path));
            File.WriteAllText(path, request.ToString(2));
            UnityEngine.Debug.Log("[BalanceVideo] request written: " + path + " runs=" + request["runs"].Count +
                                  (skipped.Count > 0 ? " skipped=" + string.Join(",", skipped.ToArray()) : ""));
            StartBatch(path);
        }

        private static string ResolveFfmpeg()
        {
            string configured = SessionState.GetString("FT.Balance.Ffmpeg", "");
            if (!string.IsNullOrEmpty(configured) && File.Exists(configured)) return configured;
            string[] candidates =
            {
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                    ".workbuddy/tools/ffmpeg/bin/ffmpeg.exe"),
                @"C:\ffmpeg\bin\ffmpeg.exe"
            };
            foreach (var candidate in candidates) if (File.Exists(candidate)) return candidate;
            throw new FileNotFoundException("ffmpeg not found; set Tools/塔防/数值验证 config or SessionState FT.Balance.Ffmpeg.");
        }

        private static void ModeChanged(PlayModeStateChange state)
        {
            if (state == PlayModeStateChange.EnteredPlayMode && Running)
            {
                _requestPath = SessionState.GetString(RequestKey, "");
                _request = JSON.Parse(File.ReadAllText(_requestPath));
                _out = _request["output"].Value; Directory.CreateDirectory(_out);
                Runs.Clear(); Results.Clear(); Operations.Clear();
                foreach (var kv in _request["runs"]) Runs.Add(kv.Value);
                _runIndex = 0; _startWall = EditorApplication.timeSinceStartup;
                _initialized = false; _levelInitialized = false; _loadedCandidate = null;
                _teardownFrame = -1;
                WriteStatus("waiting_for_scene");
            }
            if (state == PlayModeStateChange.ExitingPlayMode)
            {
                RemoveOutcomeObservers();
                if (_manualClock != null) { _manualClock.Dispose(); _manualClock = null; }
                SessionState.EraseString("FT.Balance.TestStorageContext");
            }
            if (state == PlayModeStateChange.EnteredEditMode)
            {
                string old = SessionState.GetString("FT.Balance.OldStartScene", "");
                EditorSceneManager.playModeStartScene = string.IsNullOrEmpty(old) ? null : AssetDatabase.LoadAssetAtPath<SceneAsset>(old);
                SessionState.EraseString(RequestKey); SessionState.EraseString("FT.Balance.OldStartScene");
            }
        }

        private static void Update()
        {
            if (!EditorApplication.isPlaying || _request == null || !Running) return;
            try
            {
                if (File.Exists(Path.Combine(_out, "cancel.request"))) { Finish("cancelled"); return; }
                double batchLimit = _request["batchTimeoutSeconds"].AsDouble;
                if (batchLimit <= 0) batchLimit = 3600;
                if (EditorApplication.timeSinceStartup - _startWall > batchLimit) { Finish("batch_timeout"); return; }
                var flow = GameFlowManager.Instance;
                if (!_initialized)
                {
                    if (!Configs.IsLoaded || flow == null || Launcher.Instance == null || !Launcher.Instance.IsBootComplete)
                    {
                        if (EditorApplication.timeSinceStartup - _startWall > 120) Finish("scene_or_config_timeout");
                        return;
                    }
                    _launcherEnabled = Launcher.Instance.enabled; _flowEnabled = flow.enabled;
                    Launcher.Instance.enabled = false;
                    _flowLate = (Action)Delegate.CreateDelegate(typeof(Action), flow,
                        typeof(GameFlowManager).GetMethod("StepManualSimulation", BindingFlags.Instance | BindingFlags.Public));
                    _manualClock = GameClock.BeginManualSimulation();
                    BaseTower.EvidenceTrackReentry = true;
                    EventDispatcher.AddEventListener<BaseEnemy, int>(EventName.EnemyKilledEvent, ObserveKilled);
                    EventDispatcher.AddEventListener<BaseEnemy, int>(EventName.EnemyReachedEndEvent, ObserveLeaked);
                    _initialized = true;
                }
                if (_runIndex >= Runs.Count) { Finish("complete"); return; }
                JSONNode run = Runs[_runIndex];
                if (!_levelInitialized)
                {
                    if (_teardownFrame < 0)
                    {
                        flow.TeardownLevel(); _teardownFrame = Time.frameCount;
                        UnityEngine.Rendering.SortingGroup.UpdateAllSortingGroups();
                        return;
                    }
                    if (Time.frameCount == _teardownFrame) return;
                    _teardownFrame = -1;
                    string directory = run["candidateDirectory"].Value;
                    if (!string.IsNullOrEmpty(directory) && directory != _loadedCandidate)
                    {
                        if (!Configs.LoadTestCandidate(directory)) throw new InvalidOperationException("Candidate rejected: " + directory);
                        _loadedCandidate = directory;
                    }
                    string profile = run["profileId"].Value;
                    var rating = Configs.GetLevelRating(run["levelId"].AsInt);
                    if (rating == null || rating.profileId != profile) throw new InvalidOperationException("Requested profile differs from loaded candidate.");
                    // Each trial starts clean even if the previous trial failed halfway through.
                    SaveManager.Instance.ClearSnapshot(true);
                    UIManager.Instance.Close(MainMenuView.LogicalName);
                    UIManager.Instance.Close(SelectView.LogicalName);
                    UIManager.Instance.Close(LevelDetailView.LogicalName);
                    UIManager.Instance.Close("LoadingView");
                    LevelLoadingMask.Hide();
                    flow.InitLevel(run["levelId"].AsInt);
                    _initialGold = PlayerDataManager.Instance.Gold;
                    _initialHp = PlayerDataManager.Instance.Hp;
                    EnemyOutcomes.Clear(); OperationStages.Clear();
                    if (flow.State != GameFlowState.Preparing) throw new InvalidOperationException("Level did not enter Preparing");
                    GameClock.Speed = run["speed"].AsFloat > 0 ? run["speed"].AsFloat : 1;
                    Time.timeScale = 1; GameClock.SetBackground(false);
                    _shopWave = -1; Operations.Clear(); Boundaries.Clear(); StepCosts.Clear();
                    BalanceRenderSampler.Reset();
                    _performanceScreensCaptured = false;
                    BaseTower.EvidenceTrackReentry = !_request["renderedPerformance"].AsBool;
                    _allocatedStart = GC.GetTotalMemory(false); _levelInitialized = true;
                    _operationError = null;
                    _pendingScreenshot = null;
                    _waitForFunds = run["waitForFunds"].AsBool;
                    ReplayedOperations.Clear();
                    _plannedOperations = File.Exists(run["operationsPath"].Value) ? JSON.Parse(File.ReadAllText(run["operationsPath"].Value)) : null;
                    if (_plannedOperations != null)
                    {
                        int previousWave = 0; long previousTime = -1;
                        foreach (var pair in _plannedOperations)
                        {
                            int wave = pair.Value["waveOrdinal"].AsInt; long time = pair.Value["timeMs"].AsLong;
                            if (wave < 1 || wave > rating.expectedWaveCount || time < 0 || wave < previousWave || wave == previousWave && time < previousTime)
                                throw new InvalidDataException("Replay operations must be ordered by wave and earliest time.");
                            previousWave = wave; previousTime = time;
                        }
                    }
                    BalanceCheckpointVerifier.Begin(flow, run);
                    _runWall = EditorApplication.timeSinceStartup;
                    if (run["recordVideo"].AsBool)
                    {
                        if (_plannedOperations == null)
                            throw new InvalidOperationException(
                                "recordVideo requires a valid operationsPath; refusing to record the auto-shop fallback.");
                        string videoPath = run["videoOutput"].Value;
                        if (string.IsNullOrEmpty(videoPath))
                            throw new InvalidOperationException("recordVideo requires videoOutput on the run.");
                        BalanceVideoRecorder.Begin(videoPath,
                            run["videoWidth"].AsInt > 0 ? run["videoWidth"].AsInt : 1280,
                            run["videoHeight"].AsInt > 0 ? run["videoHeight"].AsInt : 720,
                            run["videoFps"].AsDouble > 0 ? run["videoFps"].AsDouble : 15,
                            _request["stepSeconds"].AsDouble,
                            run["videoFfmpeg"].Value,
                            run["videoSpeed"].AsDouble > 0 ? run["videoSpeed"].AsDouble : 1.0);
                    }
                    WriteStatus("running");
                    // Let Unity realize the newly instantiated scene objects for one rendered frame.
                    return;
                }
                int count = Math.Max(1, _request["stepsPerUpdate"].AsInt);
                // Video capture is strictly one fixed tick per captured frame, otherwise the
                // simulated clock and the video timeline drift apart.
                if (BalanceVideoRecorder.Running) count = 1;
                if (BalanceVideoRecorder.Running && !BalanceVideoRecorder.Ready)
                {
                    // Resolution changes land a few frames late; resolve readiness outside PushFrame,
                    // otherwise Ready would never be set and the replay would stall forever.
                    BalanceVideoRecorder.ProbeReady();
                    return;
                }
                if (_request["renderedPerformance"].AsBool && BalanceRenderSampler.Completed && !_performanceScreensCaptured)
                {
                    _performanceScreensCaptured = true;
                    BalanceGameplayCapture.Begin(Path.Combine(_out, "Gameplay-" + run["profileId"].Value + "-L" + run["levelId"].AsInt + "-" + run["strategy"].Value));
                }
                if (BalanceGameplayCapture.Running) return;
                if (_request["renderedPerformance"].AsBool && !BalanceRenderSampler.Active && !BalanceRenderSampler.Completed &&
                    flow.CurrentRoundIndex >= 20 && CombatSystem.Instance.AliveEnemyCount >= 12)
                    BalanceRenderSampler.Begin(flow);
                bool sampling = BalanceRenderSampler.Active;
                if (sampling) { if (!BalanceRenderSampler.NextRenderedFrame()) return; count = 1; }
                float step = _request["stepSeconds"].AsFloat;
                if (step <= 0 || step > .1f) throw new InvalidOperationException("Step must be in (0,.1]");
                for (int i = 0; i < count; i++)
                {
                    if (!BalanceCheckpointVerifier.BeforeStep(flow)) break;
                    if (!string.IsNullOrEmpty(_pendingScreenshot) && flow.State == GameFlowState.RoundRunning &&
                        flow.CurrentRoundIndex == _pendingScreenshotWave && flow.RunMetrics.waves.Count > 0 &&
                        flow.RunMetrics.waves[flow.RunMetrics.waves.Count - 1].successfulSpawned > 0)
                    {
                        ScreenCapture.CaptureScreenshot(_pendingScreenshot); _pendingScreenshot = null;
                        WriteStatus("rendering_wave_screenshot"); return;
                    }
                    int rollbackWave = BalanceCheckpointVerifier.ConsumeOperationRollbackWave();
                    if (rollbackWave > 0 && _plannedOperations != null)
                    {
                        foreach (var actual in Operations)
                            if (actual["waveOrdinal"].AsInt == rollbackWave && actual["timeMs"].AsLong > 0 && actual.HasKey("sourceIndex"))
                                ReplayedOperations.Remove(actual["sourceIndex"].AsInt);
                        int index = -1;
                        foreach (var op in _plannedOperations)
                        {
                            index++;
                            if (op.Value["waveOrdinal"].AsInt == rollbackWave && op.Value["timeMs"].AsLong > 0) ReplayedOperations.Remove(index);
                        }
                        Operations.RemoveAll(op => op["waveOrdinal"].AsInt == rollbackWave && op["timeMs"].AsLong > 0);
                    }
                    if (flow.State == GameFlowState.GameOver) { RecordResult(flow, run, "finished"); return; }
                    var metrics = (LevelRunMetrics)RunField.GetValue(flow);
                    if (metrics != null && metrics.levelElapsedMs > 2400000) { RecordResult(flow, run, "simulation_timeout"); return; }
                    double wallLimit = run["wallTimeoutSeconds"].AsDouble;
                    if (wallLimit <= 0) wallLimit = 300;
                    if (EditorApplication.timeSinceStartup - _runWall > wallLimit) { RecordResult(flow, run, "wall_timeout"); return; }
                    int nextWave = flow.CurrentRoundIndex + 1;
                    if ((flow.State == GameFlowState.Preparing || flow.State == GameFlowState.RoundComplete) && _shopWave != nextWave)
                    {
                        _shopWave = nextWave;
                        if (_plannedOperations != null)
                        {
                            if (!ReplayOperations(nextWave, 0, true)) { RecordResult(flow, run, "operation_rejected"); return; }
                        }
                        else Shop(flow, run["strategy"].Value, nextWave);
                        CaptureBoundary(nextWave, run);
                        if (nextWave == 1) EventDispatcher.TriggerEvent(EventName.StartRoundRequestEvent);
                        // Later waves retain the actual configured 5 second automatic waiting time.
                    }
                    if (_plannedOperations != null && flow.State == GameFlowState.RoundRunning)
                    {
                        var waveMetrics = flow.RunMetrics.waves;
                        double begin = waveMetrics[waveMetrics.Count - 1].combatStartSeconds;
                        long elapsed = LevelRunMetrics.ToMilliseconds(GameClock.CombatElapsedSeconds - begin);
                        int countBeforeReplay = Operations.Count;
                        if (!ReplayOperations(flow.CurrentRoundIndex, elapsed, false))
                        { RecordResult(flow, run, "operation_rejected"); return; }
                        if (Operations.Count > countBeforeReplay && !string.IsNullOrEmpty(_pendingScreenshot)) return;
                    }
                    // Fixed game-time step permits meaningful 1x/2x/3x comparisons.
                    double stepStart = EditorApplication.timeSinceStartup;
                    GameClock.SetBackground(false);
                    GameClock.StepManualFrame(step / (double)GameClock.Speed);
                    TimerManager.Instance.Update(step);
                    EventDispatcher.TriggerEvent(EventName.UpdateEvent);
                    _flowLate();
                    BalanceCheckpointVerifier.AfterStep(flow);
                    StepCosts.Add((EditorApplication.timeSinceStartup - stepStart) * 1000);
                    if (BalanceVideoRecorder.Running)
                    {
                        BalanceVideoRecorder.PushFrame();
                        if (!string.IsNullOrEmpty(BalanceVideoRecorder.LastError))
                            throw new InvalidOperationException("Video capture failed: " + BalanceVideoRecorder.LastError);
                    }
                }
                UnityEngine.Rendering.SortingGroup.UpdateAllSortingGroups();
                WriteStatus("running");
            }
            catch (Exception ex)
            {
                File.WriteAllText(Path.Combine(_out, "failure.txt"), ex.ToString());
                JSONNode failure = new JSONObject();
                failure["exception"] = ex.ToString(); failure["checkpointChecks"] = BalanceCheckpointVerifier.CurrentChecks;
                if (_runIndex < Runs.Count) failure["run"] = Runs[_runIndex];
                if (GameFlowManager.Instance != null && GameFlowManager.Instance.RunMetrics != null)
                    failure["metrics"] = JSON.Parse(JsonUtility.ToJson(GameFlowManager.Instance.RunMetrics));
                File.WriteAllText(Path.Combine(_out, "checkpoint-failure.json"), failure.ToString(2));
                UnityEngine.Debug.LogException(ex);
                Finish("exception");
            }
        }

        private static void Shop(GameFlowManager flow, string strategy, int wave)
        {
            if (strategy == "mistake" && TowerManager.Instance.Count >= 1) return;
            int limit = strategy == "mistake" ? 1 : 8;
            for (int n = 0; n < 30; n++)
            {
                var towers = TowerManager.Instance.Towers;
                int normals = towers.Count(t => t != null && t.Config.Type == 1);
                int powers = towers.Count(t => t != null && t.Config.Type == 2);
                int slows = towers.Count(t => t != null && t.Config.Type == 3);
                int type = 1;
                if (strategy == "power" && normals >= 2) type = 2;
                if (strategy == "mixed")
                {
                    if (normals >= 2 && powers == 0) type = 2;
                    else if (normals >= 3 && powers >= 1 && slows == 0) type = 3;
                    else if (normals >= 4 && powers < 2) type = 2;
                }
                int targetCount = wave < 4 ? 4 : wave < 8 ? 6 : limit;
                if (towers.Count >= targetCount)
                {
                    var candidates = towers.Where(t => t != null && !t.Config.IsMaxLevel)
                        .OrderByDescending(t => UpgradeValue(t, strategy)).ToList();
                    bool upgraded = false;
                    foreach (var tower in candidates)
                    {
                        var next = Configs.GetNextLevel(tower.Config);
                        if (next == null || next.Prices > PlayerDataManager.Instance.Gold) continue;
                        int row = tower.Cell.Row, col = tower.Cell.Col;
                        BaseTower result = TowerManager.Instance.TryUpgrade(tower);
                        if (result != null) { LogOperation("upgrade", result, wave, next.Prices); upgraded = true; break; }
                    }
                    if (upgraded) continue;
                }
                if (towers.Count >= limit) break;
                TowerConfig cfg = Configs.GetTowerByTypeAndLevel(type, 1);
                if (cfg.Prices > PlayerDataManager.Instance.Gold)
                {
                    cfg = Configs.GetTowerByTypeAndLevel(1, 1); type = 1;
                    if (cfg.Prices > PlayerDataManager.Instance.Gold) break;
                }
                CellData cell = FindBuildCell(flow, cfg, strategy);
                if (cell == null) break;
                BaseTower built = TowerManager.Instance.TryBuild(type, 1, cell.Row, cell.Col);
                if (built == null) throw new InvalidOperationException("Selected legal build was rejected");
                AStarManager.Instance.ProcessRefresh();
                LogOperation("build", built, wave, cfg.Prices);
            }
        }

        private static bool ReplayOperations(int wave, long elapsed, bool boundary)
        {
            int operationCountBefore = Operations.Count;
            bool observedBefore = false;
            try
            {
            int index = -1;
            foreach (var kv in _plannedOperations)
            {
                index++;
                JSONNode op = kv.Value;
                if (ReplayedOperations.Contains(index)) continue;
                if (op["waveOrdinal"].AsInt < wave)
                { _operationError = "Previous-wave operation was never affordable: " + op.ToString(); return false; }
                if (op["waveOrdinal"].AsInt != wave) continue;
                long due = op["timeMs"].AsLong;
                if (boundary ? due != 0 : (!_waitForFunds && due == 0) || due > elapsed) continue;
                int row = op["row"].AsInt, col = op["col"].AsInt;
                var cfg = Configs.GetTowerSilent(op["towerId"].AsInt);
                if (cfg == null) { _operationError = "Unknown replay tower"; return false; }
                // Opt-in reactive policy: scheduled times are earliest times; wait only for real kill income.
                // Returning preserves operation order. Unexecuted actions may not silently cross a wave boundary.
                if (_waitForFunds && op["action"].Value != "sell" && cfg.Prices > PlayerDataManager.Instance.Gold)
                    return true;
                if (!boundary && !observedBefore && Runs[_runIndex]["captureStages"].AsBool)
                {
                    CaptureOperationStage(wave, elapsed, "before"); observedBefore = true;
                }
                BaseTower result = null;
                if (op["action"].Value == "build") result = TowerManager.Instance.TryBuild(cfg.Type, cfg.Level, row, col);
                else if (op["action"].Value == "upgrade")
                {
                    var cell = BoardView.Instance.GetCell(row, col);
                    if (cell != null && cell.Tower != null && cell.Tower.Config.UpgradeTo == cfg.Id)
                        result = TowerManager.Instance.TryUpgrade(cell.Tower);
                }
                else if (op["action"].Value == "sell")
                {
                    var cell = BoardView.Instance.GetCell(row, col);
                    int balanceBefore = PlayerDataManager.Instance.Gold;
                    if (cell == null || cell.Tower == null || !TowerManager.Instance.Sell(cell.Tower))
                    { _operationError = "Sell rejected at wave " + wave; return false; }
                    LogOperation("sell", row, col, cfg.Id, wave, balanceBefore - PlayerDataManager.Instance.Gold);
                    Operations[Operations.Count - 1]["requestedTimeMs"] = due;
                    Operations[Operations.Count - 1]["sourceIndex"] = index;
                    ReplayedOperations.Add(index); continue;
                }
                if (result == null)
                {
                    _operationError = "Action rejected at wave " + wave + ": " + op.ToString() + "; actual gold=" + PlayerDataManager.Instance.Gold;
                    return false;
                }
                AStarManager.Instance.ProcessRefresh(); LogOperation(op["action"].Value, result, wave, cfg.Prices);
                Operations[Operations.Count - 1]["requestedTimeMs"] = due;
                Operations[Operations.Count - 1]["sourceIndex"] = index;
                ReplayedOperations.Add(index);
            }
            return true;
            }
            finally
            {
                if (observedBefore && Operations.Count > operationCountBefore)
                    CaptureOperationStage(wave, elapsed, "after");
            }
        }

        // Opt-in observations only. No simulation step occurs between a transaction group and its screenshot.
        private static void CaptureOperationStage(int wave, long elapsed, string phase)
        {
            JSONNode row = new JSONObject();
            row["waveOrdinal"] = wave; row["timeMs"] = elapsed; row["phase"] = phase;
            row["operationCount"] = Operations.Count;
            row["cash"] = PlayerDataManager.Instance.Gold; row["hp"] = PlayerDataManager.Instance.Hp;
            row["pathCells"] = new JSONArray();
            var path = AStarManager.Instance.GetPath();
            if (path != null) foreach (var point in path)
            { var coordinate = new JSONArray(); coordinate.Add(point.X); coordinate.Add(point.Y); row["pathCells"].Add(coordinate); }
            row["layout"] = TowerContributions(); OperationStages.Add(row);
            if (phase == "after" && Runs[_runIndex]["screenshots"].AsBool)
            {
                _pendingScreenshot = Path.Combine(_out, "run" + _runIndex + "-L" + Runs[_runIndex]["levelId"].AsInt +
                    "-wave" + wave + "-at" + elapsed + "-op" + Operations.Count + ".png");
                _pendingScreenshotWave = wave; row["screenshot"] = _pendingScreenshot;
                row["screenshotTiming"] = "After recorded transactions, before next simulation step; rendered frame";
            }
        }

        private static float UpgradeValue(BaseTower tower, string strategy)
        {
            TowerConfig next = Configs.GetNextLevel(tower.Config);
            if (next == null) return -1;
            if (tower.Config.Type == 3) return strategy == "mixed" ? .55f + (tower.Config.Level == 2 ? .1f : 0) : .1f;
            float multiplier = tower.Config.Type == 2 ? 2.2f : 1.3f;
            return multiplier * (next.Power / next.CooldownSec - tower.Config.Power / tower.Config.CooldownSec) / next.Prices;
        }

        private static CellData FindBuildCell(GameFlowManager flow, TowerConfig cfg, string strategy)
        {
            BoardView board = BoardView.Instance; AStarManager astar = AStarManager.Instance;
            CellData best = null; float bestScore = float.NegativeInfinity;
            Vector2 airStart = astar.StartPoint.Center, airEnd = astar.TargetPoint.Center;
            var towers = TowerManager.Instance.Towers;
            for (int row = 0; row < board.Rows; row++)
                for (int col = 0; col < board.Cols; col++)
                {
                    CellData cell = board.GetCell(row, col);
                    if (cell == null || !cell.IsBuildable || cell.HasTower) continue;
                    var point = astar.GetPoint(row, col); if (point == null || point.IsWall) continue;
                    point.IsWall = true; var path = astar.GetPath(); point.IsWall = false;
                    if (path == null || path.Count == 0) continue;
                    float ground = 0, air = 0, overlap = 0;
                    foreach (var p in path)
                        if ((p.Center - cell.Center).sqrMagnitude <= cfg.RadiusWorld * cfg.RadiusWorld) ground++;
                    for (int k = 0; k <= 30; k++)
                        if ((Vector2.Lerp(airStart, airEnd, k / 30f) - cell.Center).sqrMagnitude <= cfg.RadiusWorld * cfg.RadiusWorld) air++;
                    foreach (var tower in towers)
                        if (tower != null && (tower.Position - cell.Center).sqrMagnitude < 5) overlap++;
                    float score = ground + (cfg.CanAttackAir ? air * .45f : 0) + path.Count * .3f;
                    if (cfg.Type == 3)
                    {
                        float friends = 0; foreach (var t in towers) if (t != null && t.Config.Type != 3 && (t.Position - cell.Center).sqrMagnitude < 25) friends++;
                        score += friends * 2;
                    }
                    else score -= overlap * .7f;
                    score += (cell.Center - airStart).magnitude * .02f;
                    if (score > bestScore) { bestScore = score; best = cell; }
                }
            return best;
        }

        private static void LogOperation(string action, BaseTower tower, int wave, int cost)
        {
            LogOperation(action, tower.Cell.Row, tower.Cell.Col, tower.Config.Id, wave, cost);
        }

        // Read-only settlement evidence: callbacks run before pooled enemies are recycled.
        private static void ObserveKilled(BaseEnemy enemy, int reward) { ObserveOutcome(enemy, false, reward); }
        private static void ObserveLeaked(BaseEnemy enemy, int damage) { ObserveOutcome(enemy, true, damage); }
        private static void ObserveOutcome(BaseEnemy enemy, bool leaked, int amount)
        {
            if (!_levelInitialized || _request == null || !_request["captureOutcomes"].AsBool || enemy == null || enemy.Config == null) return;
            var flow = GameFlowManager.Instance;
            JSONNode row = new JSONObject();
            row["waveOrdinal"] = flow.CurrentRoundIndex;
            row["spawnSerial"] = enemy.EvidenceSpawnSerial;
            row["enemyId"] = enemy.Config.Id;
            row["isFlying"] = enemy.Config.IsFlying;
            row["type"] = (int)enemy.Config.Type;
            row["leaked"] = leaked;
            row["rewardOrDamage"] = amount;
            row["remainingHp"] = enemy.CurrentHp;
            row["combatMs"] = GameClock.CombatElapsedMs;
            row["worldX"] = enemy.Position.x; row["worldY"] = enemy.Position.y;
            int r, c;
            if (BoardView.Instance.WorldToCell(enemy.Position, out r, out c))
            { row["row"] = r; row["col"] = c; }
            EnemyOutcomes.Add(row);
        }
        private static void RemoveOutcomeObservers()
        {
            EventDispatcher.RemoveEventListener<BaseEnemy, int>(EventName.EnemyKilledEvent, ObserveKilled);
            EventDispatcher.RemoveEventListener<BaseEnemy, int>(EventName.EnemyReachedEndEvent, ObserveLeaked);
        }

        private static void LogOperation(string action, int row, int col, int towerId, int wave, int cost)
        {
            JSONNode op = new JSONObject(); op["waveOrdinal"] = wave;
            op["levelTimeMs"] = GameClock.LevelElapsedMs;
            var flow = GameFlowManager.Instance;
            var metrics = flow.RunMetrics;
            op["timeMs"] = flow.State == GameFlowState.RoundRunning && metrics.waves.Count > 0
                ? LevelRunMetrics.ToMilliseconds(GameClock.CombatElapsedSeconds - metrics.waves[metrics.waves.Count - 1].combatStartSeconds) : 0;
            op["action"] = action; op["row"] = row; op["col"] = col;
            op["towerId"] = towerId; op["cost"] = cost; op["balanceAfter"] = PlayerDataManager.Instance.Gold;
            op["pathLength"] = Math.Max(0, AStarManager.Instance.CurrentPathLength - 1);
            Operations.Add(op);
        }

        private static JSONNode TowerContributions()
        {
            JSONNode result = new JSONArray();
            foreach (var tower in TowerManager.Instance.Towers)
            {
                if (tower == null) continue;
                JSONNode row = new JSONObject(); row["row"] = tower.Cell.Row; row["col"] = tower.Cell.Col;
                row["towerId"] = tower.Config.Id; row["damage"] = tower.EvidenceDamage;
                row["overkill"] = tower.EvidenceOverkill; row["hits"] = tower.EvidenceHits;
                row["airHits"] = tower.EvidenceAirHits; row["slowApplications"] = tower.EvidenceSlowApplications;
                row["repeatEffectEnemies"] = tower.EvidenceRepeatedEnemyEffects;
                row["repeatEffectDefinition"] = "Same spawned enemy affected, observed leaving circular range, then affected after reentry; pooled spawn serials are distinct";
                var path = AStarManager.Instance.GetPath();
                int passes = 0; bool previousInside = false;
                if (path != null)
                    foreach (var point in path)
                    {
                        bool inside = (point.Center - tower.Position).sqrMagnitude <= tower.Config.RadiusWorld * tower.Config.RadiusWorld;
                        if (inside && !previousInside) passes++;
                        previousInside = inside;
                    }
                row["coveragePasses"] = passes;
                var wall = tower.Cell.Point;
                try
                {
                    wall.IsWall = false; var shortcut = AStarManager.Instance.GetPath();
                    row["shortcutPreventedSteps"] = path != null && shortcut != null ? path.Count - shortcut.Count : 0;
                }
                finally { wall.IsWall = true; }
                row["participated"] = tower.EvidenceHits > 0 || tower.EvidenceSlowApplications > 0;
                result.Add(row);
            }
            return result;
        }

        private static void CaptureBoundary(int wave, JSONNode run)
        {
            JSONNode row = new JSONObject(); row["beforeWave"] = wave;
            row["towerCount"] = TowerManager.Instance.Count; row["cash"] = PlayerDataManager.Instance.Gold;
            row["capacity"] = run["capacity"].AsInt;
            row["occupancy"] = run["capacity"].AsInt > 0 ? (double)TowerManager.Instance.Count / run["capacity"].AsInt : 0;
            row["buildSpent"] = Operations.Where(op => op["action"].Value == "build").Sum(op => op["cost"].AsInt);
            row["upgradeSpent"] = Operations.Where(op => op["action"].Value == "upgrade").Sum(op => op["cost"].AsInt);
            row["pathLength"] = Math.Max(0, AStarManager.Instance.CurrentPathLength - 1);
            row["pathCells"] = new JSONArray();
            var groundPath = AStarManager.Instance.GetPath();
            if (groundPath != null) foreach (var point in groundPath)
            { var coordinate = new JSONArray(); coordinate.Add(point.X); coordinate.Add(point.Y); row["pathCells"].Add(coordinate); }
            row["layout"] = TowerContributions(); Boundaries.Add(row);
            if (run["screenshots"].AsBool && (wave == 1 || wave == 10 || wave == 25))
            {
                string path = Path.Combine(_out, "run" + _runIndex + "-" + run["profileId"].Value + "-L" + run["levelId"].AsInt + "-wave" + wave + ".png");
                _pendingScreenshot = path; _pendingScreenshotWave = wave;
                row["screenshot"] = path;
                row["screenshotTiming"] = "Queued at boundary; capture after this wave first successful spawn; yield simulation for the rendered HUD";
            }
        }

        private static void RecordResult(GameFlowManager flow, JSONNode run, string state)
        {
            LevelRunMetrics metrics = flow.RunMetrics;
            var profile = flow.RatingProfile;
            var result = LevelRatingEvaluator.Evaluate(profile, metrics);
            JSONNode entry = JSON.Parse(JsonUtility.ToJson(result));
            entry["profile"] = JSON.Parse(JsonUtility.ToJson(profile));
            entry["levelId"] = run["levelId"].AsInt; entry["profileId"] = run["profileId"].Value;
            entry["strategy"] = run["strategy"].Value; entry["speed"] = run["speed"].AsFloat;
            entry["speedComparisonGroup"] = run["speedComparisonGroup"].Value;
            entry["state"] = state; entry["stepSeconds"] = _request["stepSeconds"].AsDouble;
            entry["fundingPolicy"] = _waitForFunds ? "Scheduled earliest time; wait for actual funds within the same wave; reject unfinished prior-wave actions" : "Exact scheduled affordability required";
            entry["pendingOperations"] = new JSONArray();
            if (_plannedOperations != null)
            {
                int pendingIndex = -1;
                foreach (var pair in _plannedOperations)
                    if (!ReplayedOperations.Contains(++pendingIndex)) entry["pendingOperations"].Add(JSON.Parse(pair.Value.ToString()));
                if (state == "finished" && entry["pendingOperations"].Count > 0) entry["state"] = "operation_incomplete";
            }
            entry["coverage"] = "Unity PlayMode fixed-step: real scene/pools/4-way A*/tower targeting/AOE/slow/economy/WaveManager/GameClock/sole evaluator; presentation animation uses rendered frames";
            entry["wallSeconds"] = EditorApplication.timeSinceStartup - _runWall;
            entry["operations"] = new JSONArray(); foreach (var op in Operations) entry["operations"].Add(op);
            entry["finalGold"] = PlayerDataManager.Instance.Gold;
            entry["initialGold"] = _initialGold; entry["initialHp"] = _initialHp;
            entry["enemyOutcomes"] = new JSONArray(); foreach (var outcome in EnemyOutcomes) entry["enemyOutcomes"].Add(outcome);
            entry["operationStages"] = new JSONArray(); foreach (var stage in OperationStages) entry["operationStages"].Add(stage);
            entry["finalPathCells"] = new JSONArray();
            var finalPath = AStarManager.Instance.GetPath();
            if (finalPath != null) foreach (var point in finalPath)
            { var coordinate = new JSONArray(); coordinate.Add(point.X); coordinate.Add(point.Y); entry["finalPathCells"].Add(coordinate); }
            entry["waveBoundaries"] = new JSONArray(); foreach (var boundary in Boundaries) entry["waveBoundaries"].Add(boundary);
            entry["towerContributions"] = TowerContributions();
            StepCosts.Sort();
            entry["performance"]["sampleKind"] = "Editor manual simulation CPU steps including editor reentry evidence, presentation frames excluded; not device FPS";
            entry["performance"]["samples"] = StepCosts.Count;
            entry["performance"]["medianStepMs"] = StepCosts.Count == 0 ? 0 : StepCosts[StepCosts.Count / 2];
            entry["performance"]["p95StepMs"] = StepCosts.Count == 0 ? 0 : StepCosts[Math.Min(StepCosts.Count - 1, (int)(StepCosts.Count * .95))];
            entry["performance"]["managedHeapDeltaBytes"] = GC.GetTotalMemory(false) - _allocatedStart;
            entry["performance"]["processor"] = SystemInfo.processorType;
            entry["performance"]["gpu"] = SystemInfo.graphicsDeviceName;
            entry["performance"]["width"] = Screen.width; entry["performance"]["height"] = Screen.height;
            if (_request["renderedPerformance"].AsBool) entry["renderedPerformance"] = BalanceRenderSampler.Report();
            if (!string.IsNullOrEmpty(_operationError)) entry["operationError"] = _operationError;
            entry["storagePath"] = SaveManager.Instance.StorageLocation;
            entry["checkpointChecks"] = BalanceCheckpointVerifier.Complete(flow);
            Results.Add(entry);
            WriteResults();
            // One mp4 per run: flush here so a multi-level batch produces one file per level.
            if (BalanceVideoRecorder.Running)
            {
                if (state == "finished") BalanceVideoRecorder.End();
                else BalanceVideoRecorder.Abort();
                if (!string.IsNullOrEmpty(BalanceVideoRecorder.LastError))
                    File.WriteAllText(Path.Combine(_out, "video-error-L" + run["levelId"].AsInt + ".txt"),
                        BalanceVideoRecorder.LastError);
                entry["videoFrames"] = BalanceVideoRecorder.FrameCount;
                WriteResults();
            }
            _runIndex++; _levelInitialized = false;
            WriteStatus("next_run");
        }

        private static void WriteResults()
        {
            var array = new JSONArray(); foreach (var n in Results) array.Add(n);
            File.WriteAllText(Path.Combine(_out, "unity-results.json"), array.ToString(2));
            if (Results.Exists(n => !string.IsNullOrEmpty(n["speedComparisonGroup"].Value)))
                File.WriteAllText(Path.Combine(_out, "speed-comparison.json"), BalanceCheckpointVerifier.CompareSpeedResults(Results).ToString(2));
        }

        private static void WriteStatus(string phase)
        {
            if (string.IsNullOrEmpty(_out)) return;
            JSONNode n = new JSONObject(); n["phase"] = phase; n["completed"] = _runIndex; n["total"] = Runs.Count;
            n["elapsedSeconds"] = EditorApplication.timeSinceStartup - _startWall;
            if (_runIndex < Runs.Count) n["current"] = Runs[_runIndex];
            if (GameFlowManager.Instance != null)
            {
                n["round"] = GameFlowManager.Instance.CurrentRoundIndex;
                n["combatMs"] = GameClock.CombatElapsedMs; n["levelMs"] = GameClock.LevelElapsedMs;
                n["hp"] = PlayerDataManager.Instance.Hp; n["gold"] = PlayerDataManager.Instance.Gold;
            }
            File.WriteAllText(Path.Combine(_out, "status.json"), n.ToString(2));
        }

        private static void Finish(string phase)
        {
            bool keepPlaying = phase == "complete" && _request != null && _request["keepPlaying"].AsBool;
            WriteStatus(phase); WriteResults();
            // A stale cancel flag would abort the next batch the instant it starts.
            try
            {
                if (!string.IsNullOrEmpty(_out))
                {
                    string cancelFlag = Path.Combine(_out, "cancel.request");
                    if (File.Exists(cancelFlag)) File.Delete(cancelFlag);
                }
            }
            catch { }
            // Single收口点: normally flush the mp4, otherwise kill ffmpeg immediately.
            if (BalanceVideoRecorder.Running)
            {
                if (phase == "complete") BalanceVideoRecorder.End();
                else BalanceVideoRecorder.Abort();
                if (!string.IsNullOrEmpty(BalanceVideoRecorder.LastError))
                    File.WriteAllText(Path.Combine(_out, "video-error.txt"), BalanceVideoRecorder.LastError);
            }
            if (_manualClock != null) { _manualClock.Dispose(); _manualClock = null; }
            BaseTower.EvidenceTrackReentry = false;
            RemoveOutcomeObservers();
            BalanceRenderSampler.Dispose();
            if (Launcher.Instance != null) Launcher.Instance.enabled = _launcherEnabled;
            if (GameFlowManager.Instance != null) GameFlowManager.Instance.enabled = _flowEnabled;
            _request = null;
            if (keepPlaying) SessionState.EraseString(RequestKey);
            if (!keepPlaying) EditorApplication.isPlaying = false;
        }
    }
}
