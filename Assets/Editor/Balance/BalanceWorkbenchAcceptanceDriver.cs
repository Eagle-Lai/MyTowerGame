#if UNITY_EDITOR
// Reproducible acceptance driver for the real window handlers and transactional pipeline.
// Every editor/process operation is asynchronous and isolated from official saves.
using System;
using System.Collections.Generic;
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
    [InitializeOnLoad]
    public static class BalanceWorkbenchAcceptanceDriver
    {
        private const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
        private const string EnvSession = "FT.Balance.Acceptance.PreviousKey";
        private static JSONNode state;
        private static string Root { get { return BalanceWorkbenchProcess.ProjectRoot; } }
        private static string StatePath { get { return Path.Combine(Root, "Library/BalanceWorkbench/acceptance-driver-state.json"); } }
        private static string DraftPath { get { return Path.Combine(Root, "Library/BalanceWorkbench/draft.json"); } }
        static BalanceWorkbenchAcceptanceDriver() { EditorApplication.update += Poll; }

        public static string Start()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling ||
                BalanceWorkbenchProcess.Running || BalancePlayModeVerifier.Running)
                throw new InvalidOperationException("Acceptance requires an idle EditMode editor.");
            if (File.Exists(StatePath) && JSON.Parse(File.ReadAllText(StatePath))["active"].AsBool)
                throw new InvalidOperationException("An acceptance driver is already active.");
            string integration = Path.Combine(Root, "Library/BalanceWorkbench/integration-verifier-state.json");
            if (File.Exists(integration) && JSON.Parse(File.ReadAllText(integration))["active"].AsBool)
                throw new InvalidOperationException("Finish the process integration verifier before apply/rollback acceptance.");
            bool open = Resources.FindObjectsOfTypeAll<LevelBalanceWorkbench>().Length > 0;
            bool draftExisted = File.Exists(DraftPath);
            byte[] originalDraft = draftExisted ? File.ReadAllBytes(DraftPath) : null;
            var window = EditorWindow.GetWindow<LevelBalanceWorkbench>();
            Set(window, "_autoPreview", false); Call(window, "PersistDraft");
            if (open) { draftExisted = File.Exists(DraftPath); originalDraft = draftExisted ? File.ReadAllBytes(DraftPath) : null; }
            state = new JSONObject(); state["active"] = true; state["startedUtc"] = DateTime.UtcNow.ToString("O");
            state["events"] = new JSONArray(); state["windowWasOpen"] = open;
            state["draftExisted"] = draftExisted;
            state["originalDraftBase64"] = originalDraft != null ? Convert.ToBase64String(originalDraft) : "";
            state["lastOutputPref"] = EditorPrefs.GetString("FT.Balance.LastOutput", "");
            state["lastBackupPref"] = EditorPrefs.GetString("FT.Balance.LastBackup", "");
            state["formalBefore"] = FormalHashes(); state["officialSavesBefore"] = OfficialSaveHashes();
            state["keyShardBefore"] = KeyShardHash();
            state["output"] = Path.Combine(Root, "Docs/BalanceEvidence/workbench-acceptance-" + DateTime.UtcNow.ToString("yyyyMMdd-HHmmss"));
            Directory.CreateDirectory(state["output"].Value);
            state["initialPlanHash"] = JSON.Parse(File.ReadAllText(Path.Combine(Root, "Assets/ConfigJson/tblevelrating.json")))[0]["planHash"].Value;
            // Loading a recipe is the same private handler used by Restore Applied Recipe.
            Call(window, "LoadRecipe", Path.Combine(Root, "Luban/BalanceDesign/balance_design.json"));
            Set(window, "_preset", 3); Recipe(window)["selectedProfileId"] = "D04"; Call(window, "Changed");
            state["beforeWave"] = Recipe(window).ToString();
            Undo.IncrementCurrentGroup();
            Set(window, "_level", 1); Set(window, "_wave", 2); Set(window, "_scope", 0);
            Set(window, "_target", 0); Set(window, "_field", "targetEhp"); Set(window, "_operation", 1); Set(window, "_value", "1.01");
            Call(window, "AddOverride"); Undo.FlushUndoRecordObjects(); Undo.IncrementCurrentGroup();
            state["waveOverrideId"] = Recipe(window)["overrides"][Recipe(window)["overrides"].Count - 1]["id"].Value;
            state["afterWave"] = Recipe(window).ToString();
            Check(state["afterWave"].Value != state["beforeWave"].Value, "same window handler adds L1 W2 EHP x1.01");
            Next("undo"); return StatePath;
        }

        public static string Status() { return File.Exists(StatePath) ? File.ReadAllText(StatePath) : "No acceptance driver state"; }
        private static void Poll()
        {
            if (EditorApplication.isCompiling || EditorApplication.isUpdating) return;
            try
            {
                if (state == null && File.Exists(StatePath)) state = JSON.Parse(File.ReadAllText(StatePath));
                if (state == null || !state["active"].AsBool) return;
                string phase = state["phase"].Value;
                if (EditorApplication.isPlayingOrWillChangePlaymode && phase != "play-wait") return;
                if ((DateTime.UtcNow - DateTime.Parse(state["phaseStartedUtc"].Value, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind)).TotalSeconds > 720)
                    throw new TimeoutException("Acceptance stage timed out: " + phase);
                if (phase == "undo") { Undo.PerformUndo(); Next("undo-check"); }
                else if (phase == "undo-check")
                {
                    Check(Recipe(Window()).ToString() == state["beforeWave"].Value, "Unity Undo restores the exact recipe");
                    Undo.PerformRedo(); Next("redo-check");
                }
                else if (phase == "redo-check")
                {
                    var w = Window(); Check(Recipe(w).ToString() == state["afterWave"].Value, "Unity Redo restores the exact override");
                    Set(w, "_scope", 1); Set(w, "_wave", 3); Set(w, "_lastWave", 4);
                    Set(w, "_value", "1.001"); Call(w, "AddOverride");
                    var range = Recipe(w)["overrides"][Recipe(w)["overrides"].Count - 1];
                    state["rangeOverrideId"] = range["id"].Value;
                    Check(range["scope"].Value == "range" && range["levelId"].AsInt == 1 && range["waveStart"].AsInt == 3 && range["waveEnd"].AsInt == 4,
                        "same window handler records an exact L1 W3-W4 range override");
                    Set(w, "_scope", 2); Set(w, "_level", 2); Call(w, "AddOverride");
                    var level = Recipe(w)["overrides"][Recipe(w)["overrides"].Count - 1];
                    state["levelOverrideId"] = level["id"].Value;
                    Check(level["scope"].Value == "level" && level["levelId"].AsInt == 2 && !level.HasKey("waveOrdinal"),
                        "same window handler records a whole-level override without a wave cursor");
                    Set(w, "_target", 3); Set(w, "_scope", 3); Set(w, "_towerId", 1);
                    Set(w, "_field", "power"); Set(w, "_operation", 0); Set(w, "_value", "7"); Call(w, "AddOverride");
                    SwitchProfile(w, 0); Check(Recipe(w)["selectedProfileId"].Value == "D01", "draft profile switches to D01");
                    SwitchProfile(w, 3); Check(Recipe(w)["selectedProfileId"].Value == "D04", "draft profile switches back to D04");
                    string custom = "ACCEPTANCE_" + DateTime.UtcNow.ToString("yyyyMMddHHmmss");
                    Set(w, "_newPreset", custom); Call(w, "SaveAsPreset"); state["profileId"] = custom;
                    Check(Recipe(w)["selectedProfileId"].Value == custom, "Save As creates and selects a stable custom preset");
                    Check(Recipe(w)["overrides"].Children.Count(n => n["profileId"].Value == custom) >= 4, "custom preset copies wave, range, level and tower overrides");
                    state["customRecipe"] = Recipe(w).ToString(); Call(w, "PersistDraft"); w.Close(); Next("reopen");
                }
                else if (phase == "reopen")
                {
                    var w = Window(); Check(Recipe(w).ToString() == state["customRecipe"].Value, "close and reopen restores the complete local draft");
                    Check(Equal(FormalHashes(), state["formalBefore"]), "edits, Undo, preset switch and draft recovery leave formal files unchanged");
                    StartJob(w, "preview", "preview-wait");
                }
                else if (phase == "preview-wait" && JobDone())
                {
                    string output = state["jobOutput"].Value;
                    var p = JSON.Parse(File.ReadAllText(Path.Combine(output, "preview.json")));
                    Check(p["validation"]["passed"].AsBool && p["changes"].Count > 0, "preview validates and lists concrete differences");
                    var plan = JSON.Parse(File.ReadAllText(Path.Combine(output, "resolved-plan.json")));
                    Check(plan["tables"]["tbtowerinfo"].Children.First(n => n["id"].AsInt == 1)["power"].AsDouble == 7, "resolved shared core contains tower 1 power 7");
                    string suffix = "-" + state["profileId"].Value;
                    var waves = plan["waves"].Children.ToArray();
                    Check(waves.Single(n => n["levelId"].AsInt == 1 && n["waveOrdinal"].AsInt == 2)["overrideSources"]["targetEhp"]["id"].Value == state["waveOverrideId"].Value + suffix,
                        "resolved shared core applies the single-wave override to its exact wave");
                    string rangeId = state["rangeOverrideId"].Value + suffix;
                    Check(waves.Count(n => n["overrideSources"]["targetEhp"]["id"].Value == rangeId) == 2 &&
                          waves.Where(n => n["overrideSources"]["targetEhp"]["id"].Value == rangeId).All(n => n["levelId"].AsInt == 1 && (n["waveOrdinal"].AsInt == 3 || n["waveOrdinal"].AsInt == 4)),
                        "resolved shared core applies the range to exactly L1 W3 and W4");
                    string levelId = state["levelOverrideId"].Value + suffix;
                    Check(waves.Count(n => n["overrideSources"]["targetEhp"]["id"].Value == levelId) == plan["wavesPerLevel"].AsInt &&
                          waves.Where(n => n["overrideSources"]["targetEhp"]["id"].Value == levelId).All(n => n["levelId"].AsInt == 2),
                        "resolved shared core applies the level override to the complete configured inventory of L2 only");
                    state["candidatePlanHash"] = plan["tables"]["tblevelrating"][0]["planHash"].Value;
                    Check(state["candidatePlanHash"].Value != state["initialPlanHash"].Value, "custom candidate changes rating content identity");
                    Check(Equal(FormalHashes(), state["formalBefore"]), "preview does not change Excel, Gen, ConfigJson or authority recipe");
                    Check(Equal(OfficialSaveHashes(), state["officialSavesBefore"]), "preview never opens or writes official saves");
                    StartJob(Window(), "validate", "validate-wait");
                }
                else if (phase == "validate-wait" && JobDone())
                {
                    Check(JSON.Parse(File.ReadAllText(Path.Combine(state["jobOutput"].Value, "validation.json")))["passed"].AsBool, "window fast validation succeeds");
                    StartJob(Window(), "apply", "apply-wait");
                }
                else if (phase == "apply-wait" && JobDone())
                {
                    state["applyOutput"] = state["jobOutput"].Value;
                    state["transaction"] = Path.Combine(state["applyOutput"].Value, "transaction.json");
                    Check(JSON.Parse(File.ReadAllText(state["transaction"].Value))["phase"].Value == "committed", "staged Excel and real Luban apply commit one transaction");
                    Check(JSON.Parse(File.ReadAllText(Path.Combine(state["applyOutput"].Value, "validation.json")))["passed"].AsBool, "formal readback validation succeeds");
                    var formal = JSON.Parse(File.ReadAllText(Path.Combine(Root, "Assets/ConfigJson/tblevelrating.json")))[0];
                    state["appliedPlanHash"] = formal["planHash"].Value; state["runtimeContentHash"] = formal["runtimeContentHash"].Value;
                    Check(state["appliedPlanHash"].Value == state["candidatePlanHash"].Value, "formal export contains previewed planHash");
                    string report = Path.Combine(state["output"].Value, "report"); Directory.CreateDirectory(report);
                    // Same copy/filter behavior as the window's report-export action (no folder dialog).
                    foreach (string file in Directory.GetFiles(state["applyOutput"].Value))
                        if (new[] { ".json", ".csv", ".md", ".log" }.Contains(Path.GetExtension(file))) File.Copy(file, Path.Combine(report, Path.GetFileName(file)), true);
                    Check(File.Exists(Path.Combine(report, "waves.csv")) && File.Exists(Path.Combine(report, "report.md")) && File.Exists(Path.Combine(report, "preview.json")), "JSON, CSV and readable Markdown reports export");
                    string oldKey = Environment.GetEnvironmentVariable("FT_SAVE_KEY");
                    SessionState.SetString(EnvSession, oldKey ?? ""); SessionState.SetBool(EnvSession + ".exists", oldKey != null);
                    Environment.SetEnvironmentVariable("FT_SAVE_KEY", Convert.ToBase64String(new byte[32]));
                    state["testKeyOverrideSet"] = true;
                    string playOutput = Path.Combine(state["output"].Value, "new-formal-game"); state["playOutput"] = playOutput;
                    var request = new JSONObject(); request["output"] = playOutput; request["stepSeconds"] = .0625; request["stepsPerUpdate"] = 60;
                    var run = new JSONObject(); run["profileId"] = state["profileId"].Value; run["levelId"] = 1; run["strategy"] = "mixed"; run["speed"] = 1;
                    request["runs"] = new JSONArray(); request["runs"].Add(run);
                    string path = Path.Combine(Path.GetDirectoryName(StatePath), "acceptance-play-request.json"); File.WriteAllText(path, request.ToString(2));
                    Next("play-wait"); BalancePlayModeVerifier.StartBatch(path);
                }
                else if (phase == "play-wait" && !EditorApplication.isPlayingOrWillChangePlaymode && !BalancePlayModeVerifier.Running)
                {
                    var results = JSON.Parse(File.ReadAllText(Path.Combine(state["playOutput"].Value, "unity-results.json")));
                    Check(results.Count == 1 && results[0]["state"].Value == "finished", "a real new PlayMode game completes after formal apply");
                    Check(results[0]["profile"]["planHash"].Value == state["appliedPlanHash"].Value && results[0]["profile"]["runtimeContentHash"].Value == state["runtimeContentHash"].Value, "new game loads applied planHash and exact runtime content hash");
                    Check(results[0]["storagePath"].Value.Replace('\\', '/').Contains("/BalanceTests/"), "new game writes only its independent test storage");
                    Check(Equal(OfficialSaveHashes(), state["officialSavesBefore"]), "apply and isolated new game leave every official save byte unchanged");
                    StartRollback();
                }
                else if ((phase == "rollback-wait" || phase == "emergency-rollback-wait") && JobDone())
                {
                    Check(JSON.Parse(File.ReadAllText(state["transaction"].Value))["phase"].Value == "rolled_back", "window rollback restores the entire apply transaction");
                    Check(Equal(FormalHashes(), state["formalBefore"]), "rollback restores every formal file hash and removes appended files exactly");
                    Finish(string.IsNullOrEmpty(state["error"].Value));
                }
                else if ((phase == "failure-wait-play-exit" || phase == "failure-wait-job") && !EditorApplication.isPlayingOrWillChangePlaymode && !BalanceWorkbenchProcess.Running)
                {
                    string transaction = state["transaction"].Value;
                    if (string.IsNullOrEmpty(transaction)) transaction = Path.Combine(state["jobOutput"].Value, "transaction.json");
                    if (File.Exists(transaction) && JSON.Parse(File.ReadAllText(transaction))["phase"].Value == "committed")
                    { state["transaction"] = transaction; state["emergencyRollbackAttempted"] = true; StartRollback(true); }
                    else Finish(false);
                }
            }
            catch (Exception ex)
            {
                if (state == null) return;
                state["error"] = ex.ToString();
                if (EditorApplication.isPlayingOrWillChangePlaymode && BalancePlayModeVerifier.Running)
                { Next("failure-wait-play-exit"); BalancePlayModeVerifier.Cancel(); return; }
                if (BalanceWorkbenchProcess.Running)
                { Next("failure-wait-job"); BalanceWorkbenchProcess.Cancel(); return; }
                string transaction = state["transaction"].Value;
                if (string.IsNullOrEmpty(transaction) && !string.IsNullOrEmpty(state["jobOutput"].Value)) transaction = Path.Combine(state["jobOutput"].Value, "transaction.json");
                if (!state["emergencyRollbackAttempted"].AsBool && File.Exists(transaction) && JSON.Parse(File.ReadAllText(transaction))["phase"].Value == "committed" && !EditorApplication.isPlayingOrWillChangePlaymode && !BalanceWorkbenchProcess.Running)
                { state["transaction"] = transaction; state["emergencyRollbackAttempted"] = true; StartRollback(true); }
                else Finish(false);
            }
        }

        private static LevelBalanceWorkbench Window() { var w = EditorWindow.GetWindow<LevelBalanceWorkbench>(); Set(w, "_autoPreview", false); return w; }
        private static JSONNode Recipe(LevelBalanceWorkbench w) { return (JSONNode)Get(w, "_recipe"); }
        private static void Set(object owner, string field, object value) { owner.GetType().GetField(field, Private).SetValue(owner, value); }
        private static object Get(object owner, string field) { return owner.GetType().GetField(field, Private).GetValue(owner); }
        private static object Call(object owner, string method, params object[] args) { return owner.GetType().GetMethod(method, Private).Invoke(owner, args); }
        private static void SwitchProfile(LevelBalanceWorkbench w, int index) { Call(w, "BeforeEdit", "切换数值预设"); Set(w, "_preset", index); var nodes = (List<JSONNode>)Call(w, "ProfileNodes"); Recipe(w)["selectedProfileId"] = nodes[index]["id"].Value; Call(w, "Changed"); }
        private static void StartJob(LevelBalanceWorkbench w, string command, string phase)
        {
            Call(w, "Run", command);
            if (!BalanceWorkbenchProcess.Running) throw new InvalidOperationException("Window did not start " + command);
            state["jobOutput"] = BalanceWorkbenchProcess.DirectoryPath;
            if (command == "preview")
            {
                string ownedJob = BalanceWorkbenchProcess.JobId;
                var second = ScriptableObject.CreateInstance<LevelBalanceWorkbench>();
                try
                {
                    Set(second, "_autoPreview", false); second.Show(); Call(second, "Run", "preview");
                    Check(BalanceWorkbenchProcess.Running && BalanceWorkbenchProcess.JobId == ownedJob && BalanceWorkbenchProcess.DirectoryPath == state["jobOutput"].Value,
                        "a second live workbench cannot replace or duplicate the active preview job");
                }
                finally { second.Close(); }
            }
            Next(phase);
        }
        private static bool JobDone() { if (BalanceWorkbenchProcess.Running) return false; if (BalanceWorkbenchProcess.ExitCode != 0) throw new InvalidOperationException("Window process failed: " + BalanceWorkbenchProcess.Log); return true; }
        private static void StartRollback(bool emergency = false) { var w = Window(); Set(w, "_rollbackPath", state["transaction"].Value); StartJob(w, "rollback", emergency ? "emergency-rollback-wait" : "rollback-wait"); }
        private static void Next(string phase) { state["phase"] = phase; state["phaseStartedUtc"] = DateTime.UtcNow.ToString("O"); Persist(); }
        private static void Persist() { Directory.CreateDirectory(Path.GetDirectoryName(StatePath)); File.WriteAllText(StatePath, state.ToString(2), new UTF8Encoding(false)); }
        private static void Check(bool condition, string description) { var e = new JSONObject(); e["passed"] = condition; e["description"] = description; e["elapsedSeconds"] = (DateTime.UtcNow - DateTime.Parse(state["startedUtc"].Value, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind)).TotalSeconds; state["events"].Add(e); Persist(); if (!condition) throw new InvalidOperationException(description); }
        private static bool Equal(JSONNode a, JSONNode b) { return a.ToString() == b.ToString(); }
        private static string HashBytes(byte[] data) { using (var hash = SHA256.Create()) return BitConverter.ToString(hash.ComputeHash(data)).Replace("-", "").ToLowerInvariant(); }
        private static string KeyShardHash() { return PlayerPrefs.HasKey("FT.KeyShard.B.v1") ? HashBytes(Encoding.UTF8.GetBytes(PlayerPrefs.GetString("FT.KeyShard.B.v1"))) : "absent"; }
        private static JSONNode HashFiles(IEnumerable<string> files, string root) { var hashes = new JSONObject(); foreach (var p in files.OrderBy(p => p, StringComparer.Ordinal)) hashes[Path.GetFullPath(p).Substring(Path.GetFullPath(root).Length).Replace('\\', '/')] = HashBytes(File.ReadAllBytes(p)); return hashes; }
        private static JSONNode FormalHashes() { return HashFiles(new[] { "Assets/ConfigJson", "Assets/Gen", "Luban/Config/Datas", "Luban/BalanceDesign" }.SelectMany(p => Directory.GetFiles(Path.Combine(Root, p), "*", SearchOption.AllDirectories)), Root); }
        private static JSONNode OfficialSaveHashes() { string path = Application.persistentDataPath; return HashFiles(Directory.Exists(path) ? Directory.GetFiles(path, "*", SearchOption.AllDirectories).Where(p => !p.Substring(path.Length).Replace('\\', '/').StartsWith("/BalanceTests/", StringComparison.OrdinalIgnoreCase)) : Enumerable.Empty<string>(), path); }
        private static void Finish(bool passed)
        {
            if (state == null) return;
            if (state["testKeyOverrideSet"].AsBool)
            {
                Environment.SetEnvironmentVariable("FT_SAVE_KEY", SessionState.GetBool(EnvSession + ".exists", false) ? SessionState.GetString(EnvSession, "") : null);
                SessionState.EraseString(EnvSession); SessionState.EraseBool(EnvSession + ".exists"); state["testKeyOverrideSet"] = false;
            }
            foreach (var w in Resources.FindObjectsOfTypeAll<LevelBalanceWorkbench>()) w.Close();
            if (state["draftExisted"].AsBool) File.WriteAllBytes(DraftPath, Convert.FromBase64String(state["originalDraftBase64"].Value));
            else if (File.Exists(DraftPath)) File.Delete(DraftPath);
            EditorPrefs.SetString("FT.Balance.LastOutput", state["lastOutputPref"].Value); EditorPrefs.SetString("FT.Balance.LastBackup", state["lastBackupPref"].Value);
            state["formalHashesRestored"] = Equal(FormalHashes(), state["formalBefore"]);
            state["officialSaveHashesUnchanged"] = Equal(OfficialSaveHashes(), state["officialSavesBefore"]);
            state["keyShardUnchanged"] = KeyShardHash() == state["keyShardBefore"].Value;
            state["passed"] = passed && state["formalHashesRestored"].AsBool && state["officialSaveHashesUnchanged"].AsBool && state["keyShardUnchanged"].AsBool;
            state["active"] = false; state["phase"] = state["passed"].AsBool ? "complete" : "failed";
            state["elapsedSeconds"] = (DateTime.UtcNow - DateTime.Parse(state["startedUtc"].Value, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind)).TotalSeconds;
            Persist();
            var result = JSON.Parse(state.ToString()); result.Remove("originalDraftBase64"); result.Remove("beforeWave"); result.Remove("afterWave"); result.Remove("customRecipe");
            File.WriteAllText(Path.Combine(state["output"].Value, "result.json"), result.ToString(2), new UTF8Encoding(false));
            if (state["windowWasOpen"].AsBool) EditorWindow.GetWindow<LevelBalanceWorkbench>();
        }
    }
}
#endif
