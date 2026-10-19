using System;
using System.IO;
using System.Linq;
using System.Text;
using FTProject.AOT;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace FTProject.EditorTools
{
    public static class BootReleaseBuilder
    {
        public const string EvidenceRoot = "Builds/BootRefactor";
        public const string TestRoot = EvidenceRoot + "/Server";
        public const string TestPackage = "com.ftproject.freedomtower.bootvalidation";

        [MenuItem("Tools/塔防/启动重构/配置 Boot 首屏")]
        public static void ConfigureBoot()
        {
            if (EditorApplication.isPlaying) throw new InvalidOperationException("Exit Play before configuring Boot");
            string error;
            if (!AddMainSceneCollector.Ensure(out error)) throw new Exception(error);
            var scene = EditorSceneManager.OpenScene("Assets/Scenes/Boot.unity", OpenSceneMode.Single);
            var existing = scene.GetRootGameObjects().FirstOrDefault(x => x.name == "BootCanvas");
            if (existing == null)
            {
                var canvas = new GameObject("BootCanvas", typeof(RectTransform), typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
                canvas.GetComponent<Canvas>().renderMode = RenderMode.ScreenSpaceOverlay;
                canvas.GetComponent<Canvas>().sortingOrder = 1000;
                var scaler = canvas.GetComponent<CanvasScaler>();
                scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
                scaler.referenceResolution = new Vector2(1920, 1080);
                scaler.matchWidthOrHeight = .5f;
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Resources/BootUI/HotUpdateView.prefab");
                var view = (GameObject)PrefabUtility.InstantiatePrefab(prefab, canvas.transform);
                var rect = view.GetComponent<RectTransform>();
                rect.anchorMin = Vector2.zero; rect.anchorMax = Vector2.one;
                rect.offsetMin = rect.offsetMax = Vector2.zero;
                new GameObject("BootEventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
            }
            EditorBuildSettings.scenes = new[] {
                new EditorBuildSettingsScene("Assets/Scenes/Boot.unity", true),
                new EditorBuildSettingsScene("Assets/Scenes/Main.unity", false) };
            EditorSceneManager.SaveScene(scene);
            AssetDatabase.SaveAssets();
            ValidateShell();
        }

        public static void ValidateShell()
        {
            var enabled = EditorBuildSettings.scenes.Where(x => x.enabled).ToArray();
            if (enabled.Length != 1 || enabled[0].path != "Assets/Scenes/Boot.unity")
                throw new BuildFailedException("Only Boot may be enabled in APK Build Settings; Main must load from YooAsset.");
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Resources/BootUI/HotUpdateView.prefab");
            if (prefab == null || prefab.GetComponent<HotUpdateView>() == null) throw new BuildFailedException("AOT HotUpdateView missing");
            foreach (var component in prefab.GetComponentsInChildren<MonoBehaviour>(true))
            {
                if (component == null) throw new BuildFailedException("Boot UI has a missing script");
                string assembly = component.GetType().Assembly.GetName().Name;
                if (HotUpdateAssembler.HotUpdateAssemblies.Contains(assembly + ".dll"))
                    throw new BuildFailedException("Boot UI depends on hot-update component: " + component.GetType());
            }
            foreach (string dependency in AssetDatabase.GetDependencies("Assets/Scenes/Boot.unity", true))
            {
                if (!dependency.EndsWith(".cs", StringComparison.OrdinalIgnoreCase)) continue;
                var script = AssetDatabase.LoadAssetAtPath<MonoScript>(dependency);
                var type = script != null ? script.GetClass() : null;
                if (type != null && HotUpdateAssembler.HotUpdateAssemblies.Contains(type.Assembly.GetName().Name + ".dll"))
                    throw new BuildFailedException("Boot scene depends on hot-update script: " + dependency);
            }
        }

        public static string AotSignature()
        {
            var paths = Directory.GetFiles("Assets/AOTAssembly", "*.cs").OrderBy(x => x, StringComparer.Ordinal);
            var source = new StringBuilder("BootPlayerApi=2\n");
            foreach (string path in paths) source.Append(path.Replace('\\', '/')).Append('\n').Append(File.ReadAllText(path)).Append('\n');
            source.Append(File.ReadAllText("Assets/link.xml"));
            return BootReleaseStore.Hash(source.ToString());
        }

        // Immutable payloads first; atomic release.json replacement is the last publishing step.
        // Calling this against a test root does not touch the existing HotUpdateServer deployment.
        public static string Publish(string version, string outputRoot, bool writeApkBaseline)
        {
            ValidateShell();
            string build = HotUpdatePaths.BuildDir(version);
            if (!File.Exists(Path.Combine(build, "FreeTower_" + version + ".bytes")))
                throw new FileNotFoundException("Build the requested YooAsset version first", build);
            var release = new BootRelease { aotSignature = AotSignature(), resourceVersion = version };
            release.manifestMd5 = BootReleaseStore.Md5(Path.Combine(build, "FreeTower_" + version + ".bytes"));
            string apkDescriptor = "Assets/StreamingAssets/boot-release.json";
            if (!writeApkBaseline && File.Exists(apkDescriptor))
            {
                var baseline = JsonUtility.FromJson<BootRelease>(File.ReadAllText(apkDescriptor));
                if (baseline.aotSignature != release.aotSignature)
                    throw new BuildFailedException("AOT changed: publish a new APK baseline before building a hot update");
                if (baseline.resourceVersion == version && !string.IsNullOrEmpty(baseline.manifestMd5) && baseline.manifestMd5 != release.manifestMd5)
                    throw new BuildFailedException("Resource version is immutable; increment the version for changed AB content");
            }
            string releaseRoot = Path.Combine(outputRoot, "releases");
            if (Directory.Exists(releaseRoot))
                foreach (string previous in Directory.GetFiles(releaseRoot, "release.json", SearchOption.AllDirectories))
                {
                    var old = JsonUtility.FromJson<BootRelease>(File.ReadAllText(previous));
                    if (old.resourceVersion == version && !string.IsNullOrEmpty(old.manifestMd5) && old.manifestMd5 != release.manifestMd5)
                        throw new BuildFailedException("Resource version already published with different content: " + version);
                }
            release.dlls = HotUpdateAssembler.HotUpdateAssemblies.Select(name => new BootDllFile {
                name = name, md5 = BootReleaseStore.Md5(Path.Combine(HotUpdatePaths.DllDir, name)) }).ToArray();
            string identity = version + "|" + release.aotSignature + "|" + string.Join("|", release.dlls.Select(x => x.name + ":" + x.md5));
            // Include all built resource hashes so rebuilding the same version cannot mutate a release.
            foreach (string file in Directory.GetFiles(build).Where(IsPayload).OrderBy(x => x, StringComparer.Ordinal))
                identity += "|" + Path.GetFileName(file) + ":" + BootReleaseStore.Md5(file);
            release.id = version + "-" + BootReleaseStore.Hash(identity).Substring(0, 16);
            release.contentRoot = "releases/" + release.id;
            string destination = Path.Combine(outputRoot, release.contentRoot);
            Directory.CreateDirectory(destination);
            foreach (string file in Directory.GetFiles(build).Where(IsPayload)) CopyVerified(file, Path.Combine(destination, Path.GetFileName(file)));
            string dllRoot = Path.Combine(destination, "HybridCLR");
            Directory.CreateDirectory(dllRoot);
            foreach (var file in release.dlls) CopyVerified(Path.Combine(HotUpdatePaths.DllDir, file.name), Path.Combine(dllRoot, file.name));
            string dllList = string.Join("\n", release.dlls.Select(x => x.md5 + "  " + x.name)) + "\n";
            string listPath = Path.Combine(dllRoot, "md5.txt");
            if (File.Exists(listPath) && File.ReadAllText(listPath) != dllList) throw new IOException("Immutable DLL checksum list collision");
            File.WriteAllText(listPath, dllList, new UTF8Encoding(false));
            var inventory = new HotUpdateManifestDto { version = version, platform = HotUpdatePaths.PlatformFolder,
                package = "FreeTower", note = "Immutable release payload inventory" };
            inventory.files = Directory.GetFiles(destination, "*", SearchOption.AllDirectories)
                .Where(x => Path.GetFileName(x) != "release.json" && Path.GetFileName(x) != "payloads.json")
                .OrderBy(x => x, StringComparer.Ordinal)
                .Select(x => new HotUpdateFileEntryDto { path = x.Substring(destination.Length + 1).Replace('\\', '/'),
                    size = new FileInfo(x).Length, md5 = BootReleaseStore.Md5(x) }).ToArray();
            inventory.totalBytes = inventory.files.Sum(x => x.size);
            File.WriteAllText(Path.Combine(destination, "payloads.json"), JsonUtility.ToJson(inventory, true), new UTF8Encoding(false));
            string json = JsonUtility.ToJson(release, true);
            File.WriteAllText(Path.Combine(destination, "release.json"), json, new UTF8Encoding(false));
            Directory.CreateDirectory(outputRoot);
            string pointer = Path.Combine(outputRoot, "release.json");
            File.WriteAllText(pointer + ".tmp", json, new UTF8Encoding(false));
            BootReleaseStore.AtomicMove(pointer + ".tmp", pointer);
            if (writeApkBaseline)
            {
                File.WriteAllText("Assets/StreamingAssets/boot-release.json", json, new UTF8Encoding(false));
                AssetDatabase.Refresh();
            }
            Debug.Log("[ReleaseBuild] Published " + release.id + " => " + outputRoot);
            return release.id;
        }

        private static bool IsPayload(string path)
        {
            string extension = Path.GetExtension(path);
            return extension == ".bundle" || extension == ".bytes" || extension == ".hash" || extension == ".version"
                || HotUpdateFileUtil.IsBareHashFile(Path.GetFileName(path));
        }
        private static void CopyVerified(string source, string destination)
        {
            if (File.Exists(destination))
            {
                if (BootReleaseStore.Md5(source) != BootReleaseStore.Md5(destination)) throw new IOException("Immutable payload collision: " + destination);
                return;
            }
            File.Copy(source, destination);
            if (BootReleaseStore.Md5(source) != BootReleaseStore.Md5(destination)) throw new IOException("Copy checksum mismatch: " + destination);
        }

        public static void BuildBaseline()
        {
            var report = new EditorUtil.Report();
            bool ok = FTYooAssetSetupWizard.BuildRealBundlesCore("2.0.0", false, report);
            Directory.CreateDirectory(EvidenceRoot);
            File.WriteAllText(EvidenceRoot + "/ab-baseline.txt", ok + "\n" + report.Text);
            if (!ok) throw new BuildFailedException(report.Text);
            Publish("2.0.0", TestRoot, true);
        }
        public static void ScheduleBaseline() { EditorApplication.delayCall += BuildBaseline; }
        public static void ScheduleIsolatedApk() { EditorApplication.delayCall += BuildIsolatedApk; }

        public static void BuildIsolatedApk()
        {
            string originalId = PlayerSettings.GetApplicationIdentifier(BuildTargetGroup.Android);
            string originalName = PlayerSettings.productName;
            try
            {
                PlayerSettings.SetApplicationIdentifier(BuildTargetGroup.Android, TestPackage);
                PlayerSettings.productName = "FreeTower Boot Validation";
                Directory.CreateDirectory(EvidenceRoot);
                var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
                    scenes = new[] { "Assets/Scenes/Boot.unity" }, target = BuildTarget.Android,
                    locationPathName = EvidenceRoot + "/baseline.apk", options = BuildOptions.Development });
                File.WriteAllText(EvidenceRoot + "/apk-result.txt", report.summary.result + " errors=" + report.summary.totalErrors);
                if (report.summary.result != BuildResult.Succeeded) throw new BuildFailedException("Isolated APK build failed");
            }
            finally
            {
                PlayerSettings.SetApplicationIdentifier(BuildTargetGroup.Android, originalId);
                PlayerSettings.productName = originalName;
                AssetDatabase.SaveAssets();
            }
        }
    }

    public sealed class BootBuildGuard : IPreprocessBuildWithReport
    {
        public int callbackOrder => -1000;
        public void OnPreprocessBuild(BuildReport report)
        {
            BootReleaseBuilder.ValidateShell();
            // HybridCLR exports a temporary scripts-only project to generate stripped metadata.
            // That prerequisite intentionally precedes creation of the final APK baseline.
            if (report.summary.outputPath.Replace('\\', '/').Contains("/StrippedAOTDllsTempProj/")) return;
            string path = "Assets/StreamingAssets/boot-release.json";
            if (!File.Exists(path)) throw new BuildFailedException("Publish an APK baseline release before building");
            var release = JsonUtility.FromJson<BootRelease>(File.ReadAllText(path));
            if (!BootReleaseStore.Valid(release) || release.aotSignature != BootReleaseBuilder.AotSignature())
                throw new BuildFailedException("APK baseline AOT signature is stale; rebuild DLL/AB and publish baseline");
            foreach (var file in release.dlls)
                if (!BootReleaseStore.Matches(Path.Combine(HotUpdatePaths.DllDir, file.name), file.md5))
                    throw new BuildFailedException("APK baseline DLL mismatch: " + file.name);
            string versionFile = "Assets/StreamingAssets/yoo/FreeTower/FreeTower.version";
            if (!File.Exists(versionFile) || File.ReadAllText(versionFile).Trim() != release.resourceVersion)
                throw new BuildFailedException("APK builtin resources and baseline release version differ");
            string builtinManifest = "Assets/StreamingAssets/yoo/FreeTower/FreeTower_" + release.resourceVersion + ".bytes";
            if (!BootReleaseStore.Matches(builtinManifest, release.manifestMd5))
                throw new BuildFailedException("APK builtin manifest differs from the pinned baseline");
        }
    }
}
