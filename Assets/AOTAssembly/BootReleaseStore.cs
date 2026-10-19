using System;
using System.Collections;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace FTProject.AOT
{
    [Serializable] public sealed class BootDllFile { public string name; public string md5; }
    [Serializable] public sealed class BootRelease
    {
        public int schema = 2;
        public int playerApi = 2;
        public string aotSignature;
        public string id;
        public string resourceVersion;
        public string manifestMd5;
        public string contentRoot;
        public BootDllFile[] dlls;
    }

    // A release is a complete DLL set plus a pinned YooAsset manifest version.
    // Staged DLLs are immutable; last-good is committed only after the resource gate.
    public static class BootReleaseStore
    {
        public static BootRelease Selected { get; private set; }
        public static string Error { get; private set; }
        public static string ServerRoot { get; private set; }
        public static bool Offline { get; private set; }
        private static BootRelease _baseline;
        public static bool UsesBuiltinManifest => Selected != null && _baseline != null
            && Selected.resourceVersion == _baseline.resourceVersion && Selected.manifestMd5 == _baseline.manifestMd5;
        private static string Root => Path.Combine(Application.persistentDataPath, "BootReleases");
        public static string MetadataDirectory => Path.Combine(Root, "metadata", _baseline.aotSignature);
        public static string DllDirectory => DirectoryFor(Selected);
        public static string ResourceRoot => ServerRoot.TrimEnd('/') + "/" + Selected.contentRoot;
        public static string DirectoryFor(BootRelease release) => Path.Combine(Root, Hash(JsonUtility.ToJson(release)));
        public static string Hash(string value)
        {
            using (var hash = SHA256.Create()) return BitConverter.ToString(hash.ComputeHash(Encoding.UTF8.GetBytes(value))).Replace("-", "").ToLowerInvariant();
        }
        public static string Md5(string file)
        {
            using (var md5 = MD5.Create())
            using (var stream = File.OpenRead(file)) return BitConverter.ToString(md5.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
        }
        public static bool Matches(string path, string hash)
        {
            try { return File.Exists(path) && string.Equals(Md5(path), hash, StringComparison.OrdinalIgnoreCase); }
            catch (Exception) { return false; }
        }
        public static bool Valid(BootRelease release)
        {
            if (release == null || release.schema != 2 || release.playerApi != 2 || string.IsNullOrEmpty(release.aotSignature)
                || string.IsNullOrEmpty(release.id) || string.IsNullOrEmpty(release.resourceVersion)
                || release.manifestMd5 == null || !System.Text.RegularExpressions.Regex.IsMatch(release.manifestMd5, "^[a-fA-F0-9]{32}$")
                || string.IsNullOrEmpty(release.contentRoot) || !release.contentRoot.StartsWith("releases/", StringComparison.Ordinal)
                || release.contentRoot.Contains("..") || release.contentRoot.Contains(":") || release.contentRoot.Contains("\\")
                || release.dlls == null || release.dlls.Length != HotUpdateAssembler.HotUpdateAssemblies.Length) return false;
            foreach (string required in HotUpdateAssembler.HotUpdateAssemblies)
            {
                int count = 0;
                foreach (var file in release.dlls)
                    if (file != null && file.name == required && file.md5 != null
                        && System.Text.RegularExpressions.Regex.IsMatch(file.md5, "^[a-fA-F0-9]{32}$")) count++;
                if (count != 1) return false;
            }
            return _baseline == null || release.aotSignature == _baseline.aotSignature;
        }
        public static bool VerifyDlls(BootRelease release)
        {
            if (!Valid(release)) return false;
            foreach (var file in release.dlls)
                if (!Matches(Path.Combine(DirectoryFor(release), file.name), file.md5)) return false;
            return true;
        }

        public static IEnumerator PrepareBaseline()
        {
            Error = null; Selected = null; _baseline = null; ServerRoot = null; Offline = false;
            string json = null;
            yield return ReadStreaming("boot-release.json", value => json = value);
            try
            {
                var release = JsonUtility.FromJson<BootRelease>(json ?? "");
                if (!Valid(release)) throw new Exception("APK boot-release.json is missing or invalid. Rebuild the APK.");
                _baseline = release;
                Directory.CreateDirectory(DirectoryFor(release));
            }
            catch (Exception e) { Error = e.Message; }
            if (Error != null) yield break;

            // Read APK DLLs into a separate release directory. Never overwrite a downloaded set.
            foreach (var file in _baseline.dlls)
            {
                string destination = Path.Combine(DirectoryFor(_baseline), file.name);
                if (Matches(destination, file.md5)) continue;
                using (var request = UnityWebRequest.Get(StreamingUrl("HybridCLR/" + file.name)))
                {
                    request.timeout = 15;
                    yield return request.SendWebRequest();
                    try
                    {
                        if (request.result != UnityWebRequest.Result.Success) throw new Exception(file.name + ": " + request.error);
                        File.WriteAllBytes(destination + ".tmp", request.downloadHandler.data);
                        if (!Matches(destination + ".tmp", file.md5)) throw new Exception("APK DLL checksum: " + file.name);
                        AtomicMove(destination + ".tmp", destination);
                    }
                    catch (Exception e) { Error = e.Message; }
                }
                if (Error != null) yield break;
            }
            Selected = _baseline;
            try
            {
                string active = Path.Combine(Root, "active.json");
                if (File.Exists(active))
                {
                    var cached = JsonUtility.FromJson<BootRelease>(File.ReadAllText(active));
                    if (VerifyDlls(cached)) Selected = cached;
                }
            }
            catch (Exception e) { Debug.LogWarning("[Release] Ignoring corrupt last-good: " + e.Message); }
            Debug.Log("[Release] Local candidate " + Selected.id + " resources=" + Selected.resourceVersion);
        }

        public static IEnumerator SelectRemote(string root)
        {
            Error = null; ServerRoot = root; Offline = false;
            using (var request = UnityWebRequest.Get(root.TrimEnd('/') + "/release.json?t=" + DateTime.UtcNow.Ticks))
            {
                request.timeout = 8;
                yield return request.SendWebRequest();
                try
                {
                    if (request.result != UnityWebRequest.Result.Success) throw new Exception("Release request: " + request.error);
                    var release = JsonUtility.FromJson<BootRelease>(request.downloadHandler.text);
                    if (!Valid(release)) throw new Exception("Incompatible or incomplete release. This update requires a matching APK.");
                    Directory.CreateDirectory(DirectoryFor(release));
                    // Reuse verified unchanged DLLs, never mix in unverified fallback files.
                    foreach (var file in release.dlls)
                    {
                        string target = Path.Combine(DirectoryFor(release), file.name);
                        string previous = Path.Combine(DllDirectory, file.name);
                        if (!Matches(target, file.md5) && Matches(previous, file.md5)) File.Copy(previous, target, true);
                    }
                    Selected = release;
                    Debug.Log("[Release] Pinned " + release.id + " resources=" + release.resourceVersion);
                }
                catch (Exception e) { Error = e.Message; }
            }
        }

        public static void UseOffline(string root)
        {
            ServerRoot = root; Offline = true;
            Debug.Log("[Release] Offline candidate " + Selected?.id + "; all bundles must pass local verification.");
        }

        // Only call before loading any hot-update assembly. The resource gate must still
        // verify the complete matching manifest and bundles before entering Main.
        public static bool TryUseLocalCandidate(BootRelease candidate, string root, string reason)
        {
            if (!VerifyDlls(candidate)) return false;
            Selected = candidate;
            Error = null;
            Debug.LogWarning("[Release] Update unavailable; using verified local DLL set " + candidate.id + ": " + reason);
            UseOffline(root);
            BootUpdateSession.Report("Offline", .2f, -1);
            return true;
        }

#if UNITY_EDITOR && !FORCE_AB
        public static void UseEditorSimulation()
        {
            Selected = null; _baseline = null; Error = null; ServerRoot = null; Offline = false;
        }
#endif

        public static void RetryPinnedOnline() { Offline = false; }

        public static void Commit()
        {
            if (!VerifyDlls(Selected)) throw new Exception("Cannot activate an incomplete DLL set");
            string target = Path.Combine(Root, "active.json");
            File.WriteAllText(target + ".tmp", JsonUtility.ToJson(Selected, true));
            AtomicMove(target + ".tmp", target);
            Debug.Log("[Release] COMMIT " + Selected.id + " resources=" + Selected.resourceVersion);
        }

        public static void AtomicMove(string temporary, string target)
        {
            // A backup would require a hard link on some Mono platforms; Android FUSE
            // does not consistently support those. The final rename remains atomic.
            if (File.Exists(target)) File.Replace(temporary, target, null);
            else File.Move(temporary, target);
        }
        private static string StreamingUrl(string relative)
        {
            string path = Application.streamingAssetsPath + "/" + relative;
            return path.Contains("://") ? path : new Uri(path).AbsoluteUri;
        }
        private static IEnumerator ReadStreaming(string relative, Action<string> result)
        {
            using (var request = UnityWebRequest.Get(StreamingUrl(relative)))
            {
                request.timeout = 15;
                yield return request.SendWebRequest();
                result(request.result == UnityWebRequest.Result.Success ? request.downloadHandler.text : null);
            }
        }
    }
}
