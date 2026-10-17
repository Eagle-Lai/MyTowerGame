#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using SimpleJSON;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// Explicit asynchronous integration checks for the real workbench/process pair.
    /// Only Library candidates are generated; this suite never applies formal data or enters PlayMode.
    /// The final phase explicitly requests a real script-domain reload and resumes from its own journal.
    /// </summary>
    [InitializeOnLoad]
    public static class BalanceWorkbenchIntegrationVerifier
    {
        private const BindingFlags InstancePrivate = BindingFlags.Instance | BindingFlags.NonPublic;
        private const BindingFlags StaticPrivate = BindingFlags.Static | BindingFlags.NonPublic;
        private static readonly string DomainToken = Guid.NewGuid().ToString("N");
        private static JSONNode state;
        private static string Root { get { return BalanceWorkbenchProcess.ProjectRoot; } }
        private static string Local { get { return Path.Combine(Root, "Library/BalanceWorkbench"); } }
        private static string StatePath { get { return Path.Combine(Local, "integration-verifier-state.json"); } }
        private static string DraftPath { get { return Path.Combine(Local, "draft.json"); } }

        static BalanceWorkbenchIntegrationVerifier() { EditorApplication.update += Poll; }

        [MenuItem("Tools/塔防/数值验证/运行工作台进程与重载专项", false, 170)]
        public static void RunFromMenu() { Start(); }

        public static string Start()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling || EditorApplication.isUpdating ||
                BalanceWorkbenchProcess.Running || BalancePlayModeVerifier.Running)
                throw new InvalidOperationException("Integration verification requires an idle EditMode editor.");
            if (File.Exists(StatePath) && JSON.Parse(File.ReadAllText(StatePath))["active"].AsBool)
                throw new InvalidOperationException("An integration verification is already active.");
            string acceptance = Path.Combine(Local, "acceptance-driver-state.json");
            if (File.Exists(acceptance) && JSON.Parse(File.ReadAllText(acceptance))["active"].AsBool)
                throw new InvalidOperationException("Finish the apply/rollback acceptance driver first.");

            bool open = Resources.FindObjectsOfTypeAll<LevelBalanceWorkbench>().Length > 0;
            var window = EditorWindow.GetWindow<LevelBalanceWorkbench>();
            Set(window, "_autoPreview", false);
            if (open) Call(window, "PersistDraft");
            state = new JSONObject(); state["active"] = true;
            state["startedUtc"] = DateTime.UtcNow.ToString("O"); state["events"] = new JSONArray();
            state["windowWasOpen"] = open;
            state["draftExisted"] = File.Exists(DraftPath);
            state["originalDraftBase64"] = File.Exists(DraftPath) ? Convert.ToBase64String(File.ReadAllBytes(DraftPath)) : "";
            state["pythonPrefExisted"] = EditorPrefs.HasKey("FT.Balance.Python");
            state["pythonPref"] = EditorPrefs.GetString("FT.Balance.Python", "");
            state["lastOutputPref"] = EditorPrefs.GetString("FT.Balance.LastOutput", "");
            state["lastBackupPref"] = EditorPrefs.GetString("FT.Balance.LastBackup", "");
            state["formalBefore"] = FormalDigest(); state["officialSavesBefore"] = OfficialSaveDigest();
            state["output"] = Path.Combine(Root, "Docs/BalanceEvidence/workbench-integration-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff"));
            Directory.CreateDirectory(state["output"].Value);
            state["coverage"] = "Actual window handlers and owned Python preview processes; real log file lock, cancellation, injected runner clock timeout, actual script-domain reload; no formal apply and no PlayMode.";
            Call(window, "LoadRecipe", Path.Combine(Root, "Luban/BalanceDesign/balance_design.json"));
            Call(window, "PersistDraft");
            state["testDraft"] = Recipe(window).ToString();
            Next("missing-python");
            return StatePath;
        }

        public static string Status() { return File.Exists(StatePath) ? File.ReadAllText(StatePath) : "No integration verifier state"; }

        public static void Cancel()
        {
            LoadState();
            if (state == null || !state["active"].AsBool) return;
            state["error"] = "Integration verification cancelled by caller.";
            if (OwnsCurrentJob() && BalanceWorkbenchProcess.Running) BalanceWorkbenchProcess.Cancel();
            Next("failure-wait");
        }

        private static void Poll()
        {
            if (EditorApplication.isCompiling || EditorApplication.isUpdating) return;
            try
            {
                LoadState();
                if (state == null || !state["active"].AsBool) return;
                if (EditorApplication.isPlayingOrWillChangePlaymode)
                    throw new InvalidOperationException("Integration verification must remain in EditMode.");
                string phase = state["phase"].Value;
                if (phase != "failure-wait" && Age(state["phaseStartedUtc"].Value) > 120)
                    throw new TimeoutException("Integration phase timed out: " + phase);

                if (phase == "missing-python")
                {
                    string previous = BalanceWorkbenchProcess.Python;
                    try
                    {
                        BalanceWorkbenchProcess.Python = Path.Combine(Local, "missing-python-" + Guid.NewGuid().ToString("N") + ".exe");
                        Call(Window(), "Run", "preview");
                        state["jobId"] = BalanceWorkbenchProcess.JobId;
                        state["jobOutput"] = BalanceWorkbenchProcess.DirectoryPath;
                        Check(!BalanceWorkbenchProcess.Running, "an actual missing Python executable refuses startup without creating a live job");
                        Check(BalanceWorkbenchProcess.Log.Contains("Dependency repair:") && BalanceWorkbenchProcess.Log.Contains("unavailable"),
                            "missing dependency reports the executable failure and an actionable repair command");
                    }
                    finally { BalanceWorkbenchProcess.Python = previous; }
                    Check(ReadDraft() == state["testDraft"].Value, "dependency failure preserves the complete draft");
                    Check(FormalDigest() == state["formalBefore"].Value, "dependency failure leaves all formal files unchanged");
                    StartPreview("locked-log");
                    ProbeLockedLogAndReentry();
                    Next("locked-log-wait");
                }
                else if (phase == "locked-log-wait" && !BalanceWorkbenchProcess.Running)
                {
                    CheckPreviewCompleted("log write failure and window reentry do not discard the successful preview outcome");
                    StartPreview("cancel");
                    BalanceWorkbenchProcess.Cancel();
                    Next("cancel-wait");
                }
                else if (phase == "cancel-wait" && !BalanceWorkbenchProcess.Running)
                {
                    CheckCancelled("explicit preview cancellation terminates the owned job and retains a cancellation marker");
                    StartPreview("timeout");
                    Process process = OwnedProcess();
                    Check(process != null && !process.HasExited, "timeout probe observes a real live preview process before the clock injection");
                    DateTime original = (DateTime)GetProcessField("_started");
                    try
                    {
                        SetProcessField("_started", DateTime.UtcNow.AddSeconds(-601));
                        CallProcessPoll();
                    }
                    finally { SetProcessField("_started", original); }
                    state["timeoutProbe"] = "Only the editor runner's private start clock was advanced by reflection. The real non-mutation timeout branch cancels the real preview child; no production timeout parameter is injected.";
                    Next("timeout-wait");
                }
                else if (phase == "timeout-wait" && !BalanceWorkbenchProcess.Running)
                {
                    CheckCancelled("the runner timeout uses the real cancellation path and leaves formal data unchanged");
                    StartPreview("reload");
                    state["reloadJobId"] = BalanceWorkbenchProcess.JobId;
                    state["reloadDirectory"] = BalanceWorkbenchProcess.DirectoryPath;
                    state["beforeReloadToken"] = DomainToken;
                    state["reloadRequestedUtc"] = DateTime.UtcNow.ToString("O");
                    Call(Window(), "PersistDraft");
                    Next("reload-wait");
                    EditorUtility.RequestScriptReload();
                }
                else if (phase == "reload-wait")
                {
                    if (DomainToken == state["beforeReloadToken"].Value) return;
                    if (!state["newDomainObserved"].AsBool)
                    {
                        state["newDomainObserved"] = true;
                        state["afterReloadToken"] = DomainToken;
                        Check(true, "RequestScriptReload actually replaced the script domain and resumed the persisted verifier phase");
                        Check(BalanceWorkbenchProcess.JobId == state["reloadJobId"].Value &&
                              BalanceWorkbenchProcess.DirectoryPath == state["reloadDirectory"].Value,
                            "the process runner recovers the exact journal job identity after domain reload");
                        Check((bool)GetProcessField("_recovered"), "the production runner executed its persisted-job recovery path");
                        state["liveChildObservedAfterReload"] = BalanceWorkbenchProcess.Running;
                        state["recoveryObservation"] = BalanceWorkbenchProcess.Running
                            ? "Observed an owned live child after reload, then waited for its exit."
                            : "Child had already exited by the first resumed observation; validated terminal receipt and recovered outcome instead.";
                        Persist();
                    }
                    if (BalanceWorkbenchProcess.Running) return;
                    CheckPreviewCompleted("the domain-recovered preview publishes its actual successful terminal outcome");
                    JSONNode receipt = JSON.Parse(File.ReadAllText(Path.Combine(state["reloadDirectory"].Value, "cli-exit.json")));
                    Check(receipt["jobId"].Value == state["reloadJobId"].Value && receipt["command"].Value == "preview" && receipt["exitCode"].AsInt == 0,
                        "the recovered outcome matches the real CLI terminal receipt, job ID and command");
                    Check(ReadDraft() == state["testDraft"].Value, "the actual domain reload preserves the complete workbench draft");
                    Finish(true);
                }
                else if (phase == "failure-wait" && !BalanceWorkbenchProcess.Running) Finish(false);
            }
            catch (Exception error)
            {
                if (state == null) return;
                if (string.IsNullOrEmpty(state["error"].Value)) state["error"] = error.ToString();
                if (OwnsCurrentJob() && BalanceWorkbenchProcess.Running)
                {
                    BalanceWorkbenchProcess.Cancel(); Next("failure-wait");
                }
                else Finish(false);
            }
        }

        private static void ProbeLockedLogAndReentry()
        {
            Process process = OwnedProcess();
            Check(process != null && !process.HasExited, "log-lock probe observes a real live owned preview child");
            string jobId = BalanceWorkbenchProcess.JobId;
            string directory = BalanceWorkbenchProcess.DirectoryPath;
            string journalBefore = File.ReadAllText(Path.Combine(directory, "editor-job.json"));
            using (var locked = new FileStream(Path.Combine(directory, "editor.log"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None))
            {
                SetProcessField("_lastPersist", double.NegativeInfinity);
                CallProcessPoll();
                Check(!process.HasExited && BalanceWorkbenchProcess.Running && BalanceWorkbenchProcess.JobId == jobId,
                    "an actual exclusive editor.log lock cannot detach a child observed alive before and after monitor polling");
                Check(BalanceWorkbenchProcess.Log.Contains("Cannot persist diagnostic log"),
                    "the locked log produces a diagnostic while process ownership is retained");
            }
            var window = Window(); Call(window, "PersistDraft"); window.Close();
            var reopened = Window();
            Check(BalanceWorkbenchProcess.Running && BalanceWorkbenchProcess.JobId == jobId &&
                  File.ReadAllText(Path.Combine(directory, "editor-job.json")) == journalBefore,
                "closing and reopening the window leaves the active process and its ownership journal intact");
            var second = ScriptableObject.CreateInstance<LevelBalanceWorkbench>();
            try
            {
                Set(second, "_autoPreview", false); second.Show(); Call(second, "Run", "preview");
                Check(BalanceWorkbenchProcess.Running && BalanceWorkbenchProcess.JobId == jobId && BalanceWorkbenchProcess.DirectoryPath == directory,
                    "a simultaneous second window cannot replace the live preview job");
            }
            finally { second.Close(); }
            Check(Recipe(reopened).ToString() == state["testDraft"].Value, "active-job window reentry preserves the same complete draft");
        }

        private static void StartPreview(string label)
        {
            if (BalanceWorkbenchProcess.Running) throw new InvalidOperationException("Previous job has not terminated.");
            Call(Window(), "Run", "preview");
            state["jobId"] = BalanceWorkbenchProcess.JobId;
            state["jobOutput"] = BalanceWorkbenchProcess.DirectoryPath;
            Check(BalanceWorkbenchProcess.Running, label + " starts an actual asynchronous CLI preview");
            string full = Path.GetFullPath(BalanceWorkbenchProcess.DirectoryPath).Replace('\\', '/');
            string local = Path.GetFullPath(Local).Replace('\\', '/').TrimEnd('/') + "/";
            Check(full.StartsWith(local, StringComparison.OrdinalIgnoreCase), "preview output stays below Library/BalanceWorkbench");
            state[label + "Output"] = BalanceWorkbenchProcess.DirectoryPath;
            Persist();
        }

        private static void CheckPreviewCompleted(string description)
        {
            Check(OwnsCurrentJob() && BalanceWorkbenchProcess.ExitCode == 0, description);
            string path = Path.Combine(state["jobOutput"].Value, "preview.json");
            Check(File.Exists(path) && JSON.Parse(File.ReadAllText(path))["validation"]["passed"].AsBool,
                "the real preview candidate exists and passed the shared core validation");
        }

        private static void CheckCancelled(string description)
        {
            Check(OwnsCurrentJob() && BalanceWorkbenchProcess.ExitCode != 0 && BalanceWorkbenchProcess.ExitCode != int.MinValue &&
                  File.Exists(Path.Combine(state["jobOutput"].Value, "cancel.request")), description);
            Check(ReadDraft() == state["testDraft"].Value, "cancellation keeps the complete draft available for retry");
        }

        private static bool OwnsCurrentJob() { return state != null && BalanceWorkbenchProcess.JobId == state["jobId"].Value && BalanceWorkbenchProcess.DirectoryPath == state["jobOutput"].Value; }
        private static Process OwnedProcess() { return GetProcessField("_process") as Process; }
        private static object GetProcessField(string name) { return typeof(BalanceWorkbenchProcess).GetField(name, StaticPrivate).GetValue(null); }
        private static void SetProcessField(string name, object value) { typeof(BalanceWorkbenchProcess).GetField(name, StaticPrivate).SetValue(null, value); }
        private static void CallProcessPoll() { typeof(BalanceWorkbenchProcess).GetMethod("Poll", StaticPrivate).Invoke(null, null); }
        private static LevelBalanceWorkbench Window() { var w = EditorWindow.GetWindow<LevelBalanceWorkbench>(); Set(w, "_autoPreview", false); return w; }
        private static JSONNode Recipe(LevelBalanceWorkbench w) { return (JSONNode)w.GetType().GetField("_recipe", InstancePrivate).GetValue(w); }
        private static void Set(object owner, string field, object value) { owner.GetType().GetField(field, InstancePrivate).SetValue(owner, value); }
        private static object Call(object owner, string method, params object[] args) { return owner.GetType().GetMethod(method, InstancePrivate).Invoke(owner, args); }
        private static string ReadDraft() { return JSON.Parse(File.ReadAllText(DraftPath)).ToString(); }
        private static double Age(string utc) { return (DateTime.UtcNow - DateTime.Parse(utc, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind)).TotalSeconds; }
        private static void LoadState() { if (state == null && File.Exists(StatePath)) state = JSON.Parse(File.ReadAllText(StatePath)); }
        private static void Next(string phase) { state["phase"] = phase; state["phaseStartedUtc"] = DateTime.UtcNow.ToString("O"); Persist(); }
        private static void Persist() { Directory.CreateDirectory(Local); File.WriteAllText(StatePath, state.ToString(2), new UTF8Encoding(false)); }
        private static void Check(bool passed, string description)
        {
            var entry = new JSONObject(); entry["passed"] = passed; entry["description"] = description;
            entry["elapsedSeconds"] = Age(state["startedUtc"].Value); state["events"].Add(entry); Persist();
            if (!passed) throw new InvalidOperationException(description);
        }

        private static string Hash(byte[] bytes) { using (var sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant(); }
        private static string Digest(IEnumerable<string> paths, string basePath)
        {
            string prefix = Path.GetFullPath(basePath).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
            var entries = new StringBuilder();
            foreach (string path in paths.OrderBy(p => p, StringComparer.Ordinal))
                entries.Append(Path.GetFullPath(path).Substring(prefix.Length).Replace('\\', '/')).Append('\t').Append(Hash(File.ReadAllBytes(path))).Append('\n');
            return Hash(Encoding.UTF8.GetBytes(entries.ToString()));
        }
        private static string FormalDigest()
        {
            return Digest(new[] { "Assets/ConfigJson", "Assets/Gen", "Luban/Config/Datas", "Luban/BalanceDesign" }
                .SelectMany(relative => Directory.GetFiles(Path.Combine(Root, relative), "*", SearchOption.AllDirectories)), Root);
        }
        private static string OfficialSaveDigest()
        {
            string path = Application.persistentDataPath;
            return Digest(Directory.Exists(path) ? Directory.GetFiles(path, "*", SearchOption.AllDirectories)
                .Where(p => !p.Substring(path.Length).Replace('\\', '/').StartsWith("/BalanceTests/", StringComparison.OrdinalIgnoreCase)) : Enumerable.Empty<string>(), path);
        }

        private static void Finish(bool passed)
        {
            if (state == null) return;
            var errors = new List<Exception>();
            try
            {
                foreach (var window in Resources.FindObjectsOfTypeAll<LevelBalanceWorkbench>()) window.Close();
                if (state["draftExisted"].AsBool) File.WriteAllBytes(DraftPath, Convert.FromBase64String(state["originalDraftBase64"].Value));
                else if (File.Exists(DraftPath)) File.Delete(DraftPath);
            }
            catch (Exception error) { errors.Add(error); }
            try
            {
                if (state["pythonPrefExisted"].AsBool) EditorPrefs.SetString("FT.Balance.Python", state["pythonPref"].Value);
                else EditorPrefs.DeleteKey("FT.Balance.Python");
                EditorPrefs.SetString("FT.Balance.LastOutput", state["lastOutputPref"].Value);
                EditorPrefs.SetString("FT.Balance.LastBackup", state["lastBackupPref"].Value);
            }
            catch (Exception error) { errors.Add(error); }
            try { state["formalHashesUnchanged"] = FormalDigest() == state["formalBefore"].Value; }
            catch (Exception error) { errors.Add(error); }
            try { state["officialSaveHashesUnchanged"] = OfficialSaveDigest() == state["officialSavesBefore"].Value; }
            catch (Exception error) { errors.Add(error); }
            state["recoveryErrors"] = new JSONArray(); foreach (Exception error in errors) state["recoveryErrors"].Add(error.ToString());
            state["passed"] = passed && errors.Count == 0 && state["formalHashesUnchanged"].AsBool && state["officialSaveHashesUnchanged"].AsBool;
            state["elapsedSeconds"] = Age(state["startedUtc"].Value);
            state["active"] = false; state["phase"] = state["passed"].AsBool ? "complete" : "failed";
            Persist();
            var result = JSON.Parse(state.ToString()); result.Remove("originalDraftBase64"); result.Remove("testDraft");
            File.WriteAllText(Path.Combine(state["output"].Value, "result.json"), result.ToString(2), new UTF8Encoding(false));
            if (state["windowWasOpen"].AsBool) Window();
        }
    }
}
#endif
