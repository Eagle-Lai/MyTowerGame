using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using SimpleJSON;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>One asynchronous CLI job per project. No Unity API runs on reader threads.</summary>
    [InitializeOnLoad]
    public static class BalanceWorkbenchProcess
    {
        private const string StateKey = "FT.Balance.Job";
        private const string TerminalKey = "FT.Balance.LastCompletedJob";
        private static Process _process;
        private static readonly StringBuilder Output = new StringBuilder();
        private static readonly object Gate = new object();
        private static double _lastPersist;
        private static DateTime _started;
        private static bool _recovered;
        private static bool _exitHandled;
        private static bool _completionPending;
        private static bool _logFailureReported;
        private static string _lastMonitorError;
        private static string _pipelineLog = "";
        public static string JobId { get; private set; }
        public static string Command { get; private set; }
        public static string DirectoryPath { get; private set; }
        public static int ExitCode { get; private set; } = int.MinValue;
        public static bool Running { get { return _process != null; } }
        public static bool IsMutation { get { return Command == "apply" || Command == "rollback"; } }
        public static double ElapsedSeconds { get { return Math.Max(0, (DateTime.UtcNow - _started).TotalSeconds); } }
        public static string Log { get { lock (Gate) return Output.ToString() + (string.IsNullOrEmpty(_pipelineLog) ? "" : "\nPipeline log:\n" + _pipelineLog); } }
        public static event Action Completed;

        static BalanceWorkbenchProcess()
        {
            EditorApplication.update += Poll;
            string saved = SessionState.GetString(StateKey, "");
            bool terminal = string.IsNullOrEmpty(saved);
            if (terminal) saved = SessionState.GetString(TerminalKey, "");
            if (string.IsNullOrEmpty(saved)) return;
            try
            {
                JSONNode n = JSON.Parse(saved);
                JobId = n["jobId"]; Command = n["command"]; DirectoryPath = n["directory"];
                _started = DateTime.Parse(n["started"], null, System.Globalization.DateTimeStyles.RoundtripKind);
                var journal = JSON.Parse(File.ReadAllText(Path.Combine(DirectoryPath, "editor-job.json")));
                if (journal["jobId"].Value != JobId || journal["pid"].AsInt != n["pid"].AsInt ||
                    journal["processStartUtcTicks"].Value != n["processStartUtcTicks"].Value ||
                    journal["command"].Value != Command || journal["directory"].Value != DirectoryPath)
                    throw new InvalidOperationException("Saved job journal no longer matches the owned job.");
                // A generated-C# import may reload the domain after Poll has already
                // observed process exit. Restore that terminal result without reopening
                // or controlling its now potentially recycled PID.
                if (terminal)
                {
                    if (!n["completed"].AsBool || !n["observedExitCode"].IsNumber)
                        throw new InvalidOperationException("Saved terminal job has no observed exit outcome.");
                    RecoverExitedJob(n["observedExitCode"].AsInt);
                    return;
                }
                try { _process = Process.GetProcessById(n["pid"].AsInt); }
                catch (ArgumentException) { RecoverExitedJob(); return; }
                if (_process.HasExited) { _process.Dispose(); _process = null; RecoverExitedJob(); return; }
                if (_process.StartTime.ToUniversalTime().Ticks.ToString() != n["processStartUtcTicks"].Value ||
                    !Path.IsPathRooted(n["executable"].Value) ||
                    !string.Equals(Path.GetFullPath(n["executable"].Value), n["executable"].Value, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidOperationException("Saved process identity no longer matches this job; no process will be controlled.");
                // Mono's MainModule getter can throw IndexOutOfRangeException even for an
                // owned Windows child. PID plus its OS creation time pins the same process;
                // compare the live module path as an additional check whenever available.
                string actualExecutable = TryGetExecutable(_process);
                if (actualExecutable != null && !string.Equals(actualExecutable, n["executable"].Value, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidOperationException("Recovered process executable differs from the owned job.");
                _recovered = true;
                Append("Recovered job after domain reload. Candidate and transaction files will be read after process exit.");
            }
            catch (Exception ex)
            {
                if (_process != null) _process.Dispose(); _process = null;
                SessionState.EraseString(StateKey);
                ExitCode = -1; _completionPending = true;
                Append("Previous job stopped during reload: " + ex.Message + ". Inspect its transaction journal before retrying.");
            }
        }

        private static void RecoverExitedJob(int? observedExitCode = null)
        {
            _recovered = true;
            string logPath = Path.Combine(DirectoryPath, "editor.log");
            if (File.Exists(logPath) && !File.Exists(Path.Combine(DirectoryPath, "pipeline.log"))) Append(File.ReadAllText(logPath));
            string receiptPath = Path.Combine(DirectoryPath, "cli-exit.json");
            ExitCode = observedExitCode ?? -1;
            if (File.Exists(receiptPath))
            {
                JSONNode receipt = JSON.Parse(File.ReadAllText(receiptPath));
                DateTime finished;
                if (receipt["jobId"].Value != JobId || receipt["command"].Value != Command ||
                    !DateTime.TryParse(receipt["finishedUtc"].Value, System.Globalization.CultureInfo.InvariantCulture,
                        System.Globalization.DateTimeStyles.RoundtripKind, out finished) || finished.ToUniversalTime() < _started.ToUniversalTime() ||
                    !receipt["exitCode"].IsNumber)
                    throw new InvalidOperationException("Exited job receipt does not match the saved job.");
                ExitCode = receipt["exitCode"].AsInt;
                if (observedExitCode.HasValue && ExitCode != observedExitCode.Value)
                    throw new InvalidOperationException("CLI receipt differs from the observed process exit code.");
                Append("Recovered completed job after domain reload; exit code " + ExitCode + ".");
            }
            else Append(observedExitCode.HasValue ? "Restored the exit code observed before domain reload; no CLI receipt was produced." :
                "Owned process exited during reload without a terminal receipt; outcome is unknown. Inspect its transaction journal before retrying.");
            RefreshPipelineLog();
            PersistTerminalOutcome();
            // Subscribers in window OnEnable are installed after static initialization.
            _completionPending = true;
        }

        public static string ProjectRoot { get { return Path.GetFullPath(Path.Combine(Application.dataPath, "..")); } }
        public static string Pipeline { get { return Path.Combine(ProjectRoot, ".workbuddy/tools/balance_pipeline.py"); } }
        public static string Python
        {
            get
            {
                string saved = EditorPrefs.GetString("FT.Balance.Python", "");
                if (!string.IsNullOrWhiteSpace(saved)) return saved;
                string bundled = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
                    ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe");
                if (File.Exists(bundled)) return bundled;
                string mapPython = EditorPrefs.GetString("FTProject.LevelMapEditor.PythonPath", "");
                return File.Exists(mapPython) ? mapPython : "python";
            }
            set { EditorPrefs.SetString("FT.Balance.Python", value); }
        }

        private static string ResolveExecutable(string executable)
        {
            if (File.Exists(executable)) return Path.GetFullPath(executable);
            foreach (string directory in (Environment.GetEnvironmentVariable("PATH") ?? "").Split(Path.PathSeparator))
                foreach (string extension in new[] { "", ".exe", ".cmd" })
                {
                    string candidate = Path.Combine(directory.Trim('"'), executable + extension);
                    if (File.Exists(candidate)) return Path.GetFullPath(candidate);
                }
            throw new FileNotFoundException("Python executable is unavailable; select its full path in the workbench.", executable);
        }

        private static string TryGetExecutable(Process process)
        {
            try { return Path.GetFullPath(process.MainModule.FileName); }
            catch (Exception ex) when (ex is IndexOutOfRangeException || ex is ArgumentOutOfRangeException || ex is System.ComponentModel.Win32Exception || ex is InvalidOperationException)
            { return null; }
        }

        // Windows CommandLineToArgvW quoting. Never pass draft JSON through a command shell.
        public static string Quote(string value)
        {
            var b = new StringBuilder("\"");
            int slashes = 0;
            foreach (char c in value ?? "")
            {
                if (c == '\\') { slashes++; continue; }
                if (c == '"') { b.Append('\\', slashes * 2 + 1).Append(c); slashes = 0; continue; }
                b.Append('\\', slashes).Append(c); slashes = 0;
            }
            return b.Append('\\', slashes * 2).Append('"').ToString();
        }

        public static bool Start(string command, string arguments, string outputDirectory)
        {
            if (Running || EditorApplication.isCompiling || EditorApplication.isUpdating)
                return false;
            if (EditorApplication.isPlaying && (command == "apply" || command == "rollback"))
            {
                Append("Apply/rollback requires EditMode. Running games keep their frozen configuration.");
                return false;
            }
            if (!File.Exists(Pipeline)) { Append("Missing pipeline: " + Pipeline); return false; }
            try
            {
                Directory.CreateDirectory(outputDirectory);
                JobId = Path.GetFileName(outputDirectory); Command = command;
                DirectoryPath = outputDirectory; ExitCode = int.MinValue;
                _started = DateTime.UtcNow; _recovered = false; _exitHandled = false;
                _completionPending = false; _logFailureReported = false; _lastMonitorError = null;
                _pipelineLog = "";
                SessionState.EraseString(TerminalKey);
                lock (Gate) Output.Clear();
                var start = new ProcessStartInfo
                {
                    FileName = ResolveExecutable(Python),
                    Arguments = Quote(Pipeline) + " " + command + " " + arguments,
                    WorkingDirectory = ProjectRoot,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    StandardOutputEncoding = Encoding.UTF8,
                    StandardErrorEncoding = Encoding.UTF8,
                    CreateNoWindow = true
                };
                start.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
                start.EnvironmentVariables["DOTNET_ROLL_FORWARD"] = "LatestMajor";
                // Python owns this file for its entire lifetime. Progress never depends on
                // a stdout reader belonging to a Unity AppDomain that may be unloaded.
                start.EnvironmentVariables["FT_BALANCE_EDITOR_LOG"] = Path.GetFullPath(Path.Combine(outputDirectory, "pipeline.log"));
                _process = new Process { StartInfo = start };
                _process.OutputDataReceived += (s, e) => { if (e.Data != null) Append(e.Data); };
                _process.ErrorDataReceived += (s, e) => { if (e.Data != null) Append(e.Data); };
                _process.Start();
                _process.BeginOutputReadLine(); _process.BeginErrorReadLine();
                JSONNode state = new JSONObject();
                state["jobId"] = JobId; state["command"] = Command; state["directory"] = DirectoryPath;
                state["pid"] = _process.Id; state["started"] = _started.ToString("O");
                state["processStartUtcTicks"] = _process.StartTime.ToUniversalTime().Ticks.ToString();
                state["executable"] = start.FileName;
                SessionState.SetString(StateKey, state.ToString());
                File.WriteAllText(Path.Combine(outputDirectory, "editor-job.json"), state.ToString(2));
                Append("Started " + command + " · " + JobId);
                return true;
            }
            catch (Exception ex)
            {
                Append(ex.ToString() + "\nDependency repair: " + Python + " -m pip install openpyxl");
                if (_process != null)
                {
                    try
                    {
                        if (!_process.HasExited) _process.Kill();
                        if (!_process.HasExited) { Append("Startup failed; the owned process is still monitored until it exits."); return false; }
                    }
                    catch (Exception stop) { Append("Failed to stop owned child after startup failure; monitoring retained: " + stop.Message); return false; }
                    _process.Dispose();
                }
                _process = null; SessionState.EraseString(StateKey); return false;
            }
        }

        public static void Cancel()
        {
            if (!Running) return;
            // The pipeline owns its transaction. Cancellation is cooperative, including commit safety.
            try { File.WriteAllText(Path.Combine(DirectoryPath, "cancel.request"), DateTime.UtcNow.ToString("O")); }
            catch (Exception ex) { Append("Cannot write cancellation request; job remains monitored: " + ex.Message); return; }
            Append("Cancellation requested at next safe boundary. Transaction recovery remains available.");
            if (!IsMutation)
            {
                try { if (!_process.HasExited) _process.Kill(); }
                catch (Exception ex) { Append(ex.Message); }
            }
        }

        private static void Append(string line)
        {
            lock (Gate)
            {
                Output.AppendLine(line);
                if (Output.Length > 250000) Output.Remove(0, Output.Length - 200000);
            }
        }

        private static void Poll()
        {
            if (_completionPending) { NotifyCompleted(); return; }
            if (_process == null) return;
            try
            {
                if (EditorApplication.timeSinceStartup - _lastPersist > 1)
                {
                    _lastPersist = EditorApplication.timeSinceStartup;
                    PersistLog();
                }
                if (!_process.HasExited)
                {
                    if (ElapsedSeconds > (Command == "simulate" ? 3600 : 600) && !IsMutation) Cancel();
                    return;
                }
                ExitCode = _process.ExitCode;
                _process.Dispose(); _process = null;
                PersistTerminalOutcome();
                Append("Finished with exit code " + ExitCode + " in " + ElapsedSeconds.ToString("F2") + "s" +
                       (_recovered ? " (recovered)" : ""));
                PersistLog();
                NotifyCompleted();
            }
            catch (Exception ex)
            {
                // A diagnostic or transient OS failure must never detach a live mutation.
                if (_lastMonitorError != ex.Message) { Append("Job monitor (ownership retained): " + ex.Message); _lastMonitorError = ex.Message; }
            }
        }

        private static void PersistLog()
        {
            RefreshPipelineLog();
            try { File.WriteAllText(Path.Combine(DirectoryPath, "editor.log"), Log, new UTF8Encoding(false)); _logFailureReported = false; }
            catch (Exception ex)
            {
                if (!_logFailureReported) Append("Cannot persist diagnostic log; job ownership is retained: " + ex.Message);
                _logFailureReported = true;
            }
        }

        private static void PersistTerminalOutcome()
        {
            string saved = SessionState.GetString(StateKey, "");
            if (string.IsNullOrEmpty(saved)) saved = SessionState.GetString(TerminalKey, "");
            if (!string.IsNullOrEmpty(saved))
            {
                JSONNode state = JSON.Parse(saved);
                state["completed"] = true;
                state["observedExitCode"] = ExitCode;
                SessionState.SetString(TerminalKey, state.ToString());
            }
            SessionState.EraseString(StateKey);
        }

        private static void RefreshPipelineLog()
        {
            string path = Path.Combine(DirectoryPath, "pipeline.log");
            if (!File.Exists(path)) return;
            try
            {
                using (var file = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete))
                using (var reader = new StreamReader(file, Encoding.UTF8, true))
                {
                    string value = reader.ReadToEnd();
                    _pipelineLog = value.Length <= 200000 ? value : value.Substring(value.Length - 200000);
                }
            }
            catch (IOException) { /* Next poll retries; losing diagnostic IO cannot detach a job. */ }
            catch (UnauthorizedAccessException) { }
        }

        private static void NotifyCompleted()
        {
            _completionPending = false;
            if (_exitHandled) return;
            _exitHandled = true;
            var callbacks = Completed;
            if (callbacks == null) return;
            foreach (Action callback in callbacks.GetInvocationList())
                try { callback(); }
                catch (Exception ex) { Append("Job completion observer failed: " + ex.Message); }
        }
    }
}
