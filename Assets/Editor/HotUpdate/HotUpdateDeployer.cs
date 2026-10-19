using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using FTProject.AOT;
using System.Net;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>一条"要部署/要上传"的文件记录。</summary>
    public class HotUpdatePlanFile
    {
        /// <summary>本机绝对路径（dll 侧通常是 StreamingAssets/HybridCLR/…）。</summary>
        public string SourcePath;

        /// <summary>相对服务器根的路径：releases/{id}/… 或最后激活的 release.json。</summary>
        public string RelativePath;

        public long Size;
        public string Md5;

        /// <summary>true = 不可变 release 的 HybridCLR/ 下热更 DLL 与校验清单。</summary>
        public bool IsDll;
    }

    /// <summary>一次热更的完整产物清单（AB + dll + 清单自身）。</summary>
    public class HotUpdatePlan
    {
        public string Version;
        public string Platform;
        public string BuildDir;
        public List<HotUpdatePlanFile> Files = new List<HotUpdatePlanFile>();
        public string ManifestPath;
        public long TotalBytes;
        public int BundleCount;
        public int DllCount;

        public string Describe()
        {
            return string.Format("版本 {0} · {1} 个 AB 文件 · {2} 个 dll/清单 · 合计 {3}",
                Version, BundleCount, DllCount, HotUpdateFileUtil.FormatSize(TotalBytes));
        }
    }

    /// <summary>校验结果（失败项要能直接贴到群里排查，所以保留前若干条原文）。</summary>
    public class HotUpdateVerifyResult
    {
        public int Checked;
        public readonly List<string> Failures = new List<string>();
        public readonly List<string> Warnings = new List<string>();

        public bool Ok { get { return Failures.Count == 0; } }

        public string Describe()
        {
            string text = string.Format("校验 {0} 项：失败 {1} · 警告 {2}", Checked, Failures.Count, Warnings.Count);
            if (Failures.Count > 0)
            {
                int show = Math.Min(Failures.Count, 12);
                text += "\n失败明细：\n  · " + string.Join("\n  · ", Failures.GetRange(0, show).ToArray());
                if (Failures.Count > show)
                {
                    text += string.Format("\n  …（还有 {0} 条）", Failures.Count - show);
                }
            }
            if (Warnings.Count > 0)
            {
                int show = Math.Min(Warnings.Count, 8);
                text += "\n警告：\n  · " + string.Join("\n  · ", Warnings.GetRange(0, show).ToArray());
                if (Warnings.Count > show)
                {
                    text += string.Format("\n  …（还有 {0} 条）", Warnings.Count - show);
                }
            }
            return text;
        }
    }

    /// <summary>落盘的热更清单（服务器根 hotupdate_manifest.json，客户端不读，人/CI 读）。</summary>
    [Serializable]
    public class HotUpdateManifestDto
    {
        public string version;
        public string platform;
        public string package;
        public string builtAt;
        public string note;
        public long totalBytes;
        public HotUpdateFileEntryDto[] files;
    }

    [Serializable]
    public class HotUpdateFileEntryDto
    {
        public string path;
        public long size;
        public string md5;
    }

    /// <summary>
    /// Publish immutable releases/{id}/ payloads and activate release.json last.
    /// HTTP validation downloads and hashes the real served bytes, including extensionless bundles.
    /// </summary>
    public static class HotUpdateDeployer
    {
        private const string Md5ListName = "md5.txt";

        // ==================================================================
        // 清单生成
        // ==================================================================

        /// <summary>
        /// 从「AB 构建输出 + 随包 dll」生成部署清单。
        /// 只收客户端真的会请求的文件；`.report` / `link.xml` / `.meta` 一律跳过。
        /// </summary>
        public static HotUpdatePlan BuildPlan(string version, string buildDir, string dllDir,
            string platform, EditorUtil.Report report)
        {
            try
            {
                string stage = Path.Combine("Library", "FTBootReleaseStage", version);
                BootReleaseBuilder.Publish(version, stage, false);
                return PlanForRelease(stage, platform, report);
            }
            catch (Exception e)
            {
                report.Error("Release staging failed: " + e.Message);
                return new HotUpdatePlan { Version = version, Platform = platform };
            }
        }

        public static HotUpdatePlan BuildPlanFromCdn(string version, string cdnRoot, string dllDir,
            string platform, EditorUtil.Report report)
        {
            try { return PlanForRelease(cdnRoot, platform, report); }
            catch (Exception e)
            {
                report.Error("No complete release descriptor: " + e.Message);
                return new HotUpdatePlan { Version = version, Platform = platform };
            }
        }

        private static HotUpdatePlan PlanForRelease(string root, string platform, EditorUtil.Report report)
        {
            string pointer = Path.Combine(root, "release.json");
            var release = JsonUtility.FromJson<BootRelease>(File.ReadAllText(pointer));
            if (!BootReleaseStore.Valid(release)) throw new IOException("Invalid release.json");
            var plan = new HotUpdatePlan { Version = release.resourceVersion, Platform = platform, BuildDir = root };
            string payload = Path.Combine(root, release.contentRoot);
            var inventory = JsonUtility.FromJson<HotUpdateManifestDto>(File.ReadAllText(Path.Combine(payload, "payloads.json")));
            if (inventory == null || inventory.files == null || inventory.version != release.resourceVersion)
                throw new IOException("Release inventory missing or invalid");
            foreach (var entry in inventory.files)
            {
                if (string.IsNullOrEmpty(entry.path) || entry.path.Contains("..") || entry.path.Contains(":") || entry.path.StartsWith("/"))
                    throw new IOException("Invalid inventory path");
                string path = Path.Combine(payload, entry.path);
                if (!File.Exists(path) || new FileInfo(path).Length != entry.size || HotUpdateFileUtil.Md5(path) != entry.md5)
                    throw new IOException("Inventory checksum mismatch: " + entry.path);
                string relative = release.contentRoot + "/" + entry.path;
                AddFile(plan, path, relative, relative.Contains("/HybridCLR/"), report);
            }
            foreach (var dll in release.dlls)
                if (!BootReleaseStore.Matches(Path.Combine(payload, "HybridCLR", dll.name), dll.md5))
                    throw new IOException("Release DLL missing or checksum mismatch: " + dll.name);
            if (!BootReleaseStore.Matches(Path.Combine(payload, "FreeTower_" + release.resourceVersion + ".bytes"), release.manifestMd5))
                throw new IOException("Release manifest checksum mismatch");
            AddFile(plan, Path.Combine(payload, "payloads.json"), release.contentRoot + "/payloads.json", false, report);
            AddFile(plan, Path.Combine(payload, "release.json"), release.contentRoot + "/release.json", false, report);
            // The only mutable activation pointer is always the last operation.
            AddFile(plan, pointer, "release.json", false, report);
            report.Ok(plan.Describe());
            return plan;
        }

        private static void AddFile(HotUpdatePlan plan, string fullPath, string relative, bool isDll,
            EditorUtil.Report report)
        {
            try
            {
                FileInfo info = new FileInfo(fullPath);
                HotUpdatePlanFile file = new HotUpdatePlanFile();
                file.SourcePath = fullPath;
                file.RelativePath = relative.Replace('\\', '/');
                file.Size = info.Length;
                file.Md5 = HotUpdateFileUtil.Md5(fullPath);
                file.IsDll = isDll;
                plan.Files.Add(file);
                plan.TotalBytes += file.Size;
                if (isDll)
                {
                    plan.DllCount++;
                }
                else
                {
                    plan.BundleCount++;
                }
            }
            catch (Exception e)
            {
                report.Error("读取文件失败 " + fullPath + "：" + e.Message);
            }
        }

        /// <summary>写清单 JSON（服务器根 + 本机历史各一份）。</summary>
        public static bool WriteManifest(HotUpdatePlan plan, string outputPath, string note, EditorUtil.Report report)
        {
            try
            {
                HotUpdateManifestDto dto = new HotUpdateManifestDto();
                dto.version = plan.Version;
                dto.platform = plan.Platform;
                dto.package = HotUpdatePaths.PackageName;
                dto.builtAt = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
                dto.note = note;
                dto.totalBytes = plan.TotalBytes;

                dto.files = new HotUpdateFileEntryDto[plan.Files.Count];
                for (int i = 0; i < plan.Files.Count; i++)
                {
                    HotUpdateFileEntryDto entry = new HotUpdateFileEntryDto();
                    entry.path = plan.Files[i].RelativePath;
                    entry.size = plan.Files[i].Size;
                    entry.md5 = plan.Files[i].Md5;
                    dto.files[i] = entry;
                }

                string json = JsonUtility.ToJson(dto, true);
                HotUpdateFileUtil.WriteText(outputPath, json);
                plan.ManifestPath = outputPath;
                report.Ok("清单已写入：" + outputPath);
                return true;
            }
            catch (Exception e)
            {
                report.Error("写清单失败：" + e.Message);
                return false;
            }
        }

        // ==================================================================
        // 本地部署
        // ==================================================================

        /// <summary>Copy immutable payloads with MD5 checks, then atomically replace release.json.
        /// No legacy flat paths or StreamingAssets junctions are written.</summary>
        public static bool DeployLocal(HotUpdatePlan plan, string cdnRoot, EditorUtil.Report report)
        {
            try
            {
                if (!plan.Files.Any(x => x.RelativePath == "release.json")) throw new IOException("Activation descriptor missing");
                foreach (var file in plan.Files.OrderBy(x => x.RelativePath == "release.json"))
                {
                    string target = Path.Combine(cdnRoot, file.RelativePath.Replace('/', Path.DirectorySeparatorChar));
                    Directory.CreateDirectory(Path.GetDirectoryName(target));
                    if (IsSamePath(file.SourcePath, target)) continue;
                    if (file.RelativePath != "release.json" && File.Exists(target))
                    {
                        if (HotUpdateFileUtil.Md5(target) != file.Md5) throw new IOException("Immutable collision: " + file.RelativePath);
                        continue;
                    }
                    File.Copy(file.SourcePath, target + ".tmp", true);
                    if (HotUpdateFileUtil.Md5(target + ".tmp") != file.Md5) throw new IOException("Copy checksum: " + file.RelativePath);
                    BootReleaseStore.AtomicMove(target + ".tmp", target);
                }
                HotUpdateFileUtil.WriteText(Path.Combine(HotUpdatePaths.StateDir, "last_version.txt"), plan.Version);
                report.Ok("Immutable payloads verified; release.json activated last. " + plan.Describe());
                return true;
            }
            catch (Exception e) { report.Error("Local deployment failed: " + e.Message); return false; }
        }

        private static bool IsSamePath(string a, string b)
        {
            try
            {
                return string.Equals(Path.GetFullPath(a), Path.GetFullPath(b), StringComparison.OrdinalIgnoreCase);
            }
            catch (Exception)
            {
                return false;
            }
        }

        // ==================================================================
        // 远端上传（HTTP PUT）
        // ==================================================================

        /// <summary>
        /// 把清单里的全部文件 + 清单自身 PUT 到远端根地址。**阻塞**调用（由流水线放到后台线程）。
        /// 任一个文件失败即中断（避免半套资源上线 → 客户端下载到一半版本）。
        /// </summary>
        /// <param name="progress">(已处理, 总数) 回调，线程安全由调用方保证（只写 volatile 计数）</param>
        public static bool UploadAll(HotUpdatePlan plan, string baseUrl, string header,
            Action<int, int> progress, out string error)
        {
            error = null;
            if (string.IsNullOrEmpty(baseUrl))
            {
                error = "远端地址为空。";
                return false;
            }

            baseUrl = baseUrl.TrimEnd('/');
            if (!baseUrl.StartsWith("http://", StringComparison.OrdinalIgnoreCase)
                && !baseUrl.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
            {
                error = "远端地址必须以 http:// 或 https:// 开头：" + baseUrl;
                return false;
            }

            List<HotUpdatePlanFile> all = new List<HotUpdatePlanFile>(plan.Files.Where(x => x.RelativePath != "release.json"));
            if (!string.IsNullOrEmpty(plan.ManifestPath) && File.Exists(plan.ManifestPath))
            {
                HotUpdatePlanFile manifest = new HotUpdatePlanFile();
                manifest.SourcePath = plan.ManifestPath;
                manifest.RelativePath = HotUpdatePaths.ManifestFileName;
                manifest.Size = new FileInfo(plan.ManifestPath).Length;
                manifest.Md5 = HotUpdateFileUtil.Md5(plan.ManifestPath);
                all.Add(manifest);
            }

            var pointer = plan.Files.FirstOrDefault(x => x.RelativePath == "release.json");
            if (pointer == null) { error = "Activation descriptor missing"; return false; }
            all.Add(pointer);
            int total = all.Count;
            for (int i = 0; i < total; i++)
            {
                HotUpdatePlanFile file = all[i];
                string url = baseUrl + "/" + file.RelativePath;
                string fileError;
                if (!PutFile(url, file.SourcePath, header, out fileError))
                {
                    error = string.Format("上传失败（{0}/{1}）{2}\n  {3}", i + 1, total, file.RelativePath, fileError);
                    return false;
                }
                if (!VerifyHttpFile(file, baseUrl, out fileError))
                {
                    error = "HTTP content verification failed: " + file.RelativePath + " " + fileError;
                    return false;
                }
                if (progress != null) progress(i + 1, total);
            }

            return true;
        }

        private static bool PutFile(string url, string localPath, string header, out string error)
        {
            error = null;
            try
            {
                FileInfo info = new FileInfo(localPath);
                HttpWebRequest request = CreateRequest(url, "PUT");
                request.ContentType = "application/octet-stream";
                request.ContentLength = info.Length;
                ApplyHeader(request, header);

                using (Stream requestStream = request.GetRequestStream())
                using (FileStream fileStream = new FileStream(localPath, FileMode.Open, FileAccess.Read, FileShare.Read))
                {
                    byte[] buffer = new byte[128 * 1024];
                    int read;
                    while ((read = fileStream.Read(buffer, 0, buffer.Length)) > 0)
                    {
                        requestStream.Write(buffer, 0, read);
                    }
                }

                using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                {
                    int code = (int)response.StatusCode;
                    if (code == 200 || code == 201 || code == 202 || code == 204)
                    {
                        return true;
                    }
                    error = "服务器返回 HTTP " + code;
                    return false;
                }
            }
            catch (WebException e)
            {
                error = DescribeWebException(e);
                if (e.Response is HttpWebResponse)
                {
                    HttpWebResponse resp = (HttpWebResponse)e.Response;
                    if ((int)resp.StatusCode == 405)
                    {
                        error += "（服务器不支持 PUT：请改用本地部署，或换成对象存储/CI 上传通道）";
                    }
                }
                return false;
            }
            catch (Exception e)
            {
                error = e.Message;
                return false;
            }
        }

        private static void ApplyHeader(HttpWebRequest request, string header)
        {
            if (string.IsNullOrEmpty(header))
            {
                return;
            }
            int colon = header.IndexOf(':');
            if (colon <= 0)
            {
                return;
            }
            string name = header.Substring(0, colon).Trim();
            string value = header.Substring(colon + 1).Trim();
            if (name.Length == 0)
            {
                return;
            }
            try
            {
                request.Headers[name] = value;
            }
            catch (Exception)
            {
                // 受限头（如 Content-Type）走属性设置；这里静默忽略即可，别让上传因此失败
            }
        }

        // ==================================================================
        // 校验 ①：本地文件完整性
        // ==================================================================

        /// <summary>
        /// 校验"服务器目录里的东西确实是这一版、且和构建产物一模一样"。
        /// 校验对象 = 清单里的每个文件（存在 + 大小 + MD5 一致）。
        /// </summary>
        public static void VerifyLocalFiles(HotUpdatePlan plan, string cdnRoot, bool deployedLocally,
            HotUpdateVerifyResult result)
        {
            foreach (var file in plan.Files)
            {
                string path = deployedLocally ? Path.Combine(cdnRoot, file.RelativePath) : file.SourcePath;
                result.Checked++;
                if (!File.Exists(path) || new FileInfo(path).Length != file.Size || HotUpdateFileUtil.Md5(path) != file.Md5)
                    result.Failures.Add("Payload missing or checksum mismatch: " + file.RelativePath);
            }
        }

        // ==================================================================
        // 校验 ②：HTTP 链路（与客户端同一条请求路径）
        // ==================================================================

        /// <summary>
        /// GET every descriptor, manifest, DLL and bundle through the real HTTP path and compare MD5.
        /// 阻塞调用（由流水线放到后台线程），不碰任何 Unity API。
        /// </summary>
        public static void VerifyHttp(HotUpdatePlan plan, string baseUrl,
            Action<int, int> progress, HotUpdateVerifyResult result)
        {
            int done = 0;
            foreach (var file in plan.Files)
            {
                result.Checked++;
                if (!VerifyHttpFile(file, baseUrl.TrimEnd('/'), out string error))
                    result.Failures.Add("GET " + file.RelativePath + ": " + error);
                progress?.Invoke(++done, plan.Files.Count);
            }
        }

        private static bool VerifyHttpFile(HotUpdatePlanFile file, string baseUrl, out string error)
        {
            error = null;
            try
            {
                var request = CreateRequest(baseUrl.TrimEnd('/') + "/" + file.RelativePath + "?verify=" + DateTime.UtcNow.Ticks, "GET");
                using (var response = (HttpWebResponse)request.GetResponse())
                using (var stream = response.GetResponseStream())
                using (var md5 = System.Security.Cryptography.MD5.Create())
                {
                    string hash = BitConverter.ToString(md5.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
                    if (hash != file.Md5) { error = "MD5 mismatch: " + hash + " expected " + file.Md5; return false; }
                }
                return true;
            }
            catch (Exception e) { error = e.Message; return false; }
        }

        /// <summary>探测某个地址上的版本号（用于"端口被别的服务占着"时判断能不能复用）。</summary>
        public static bool TryGetRemoteVersion(string baseUrl, out string version, out string error)
        {
            version = "";
            string body;
            if (TryGetText(baseUrl.TrimEnd('/') + "/release.json", out body, out error))
            {
                var release = JsonUtility.FromJson<BootRelease>(body);
                if (release != null && !string.IsNullOrEmpty(release.resourceVersion)) { version = release.resourceVersion; return true; }
            }
            if (!TryGetText(baseUrl.TrimEnd('/') + "/" + HotUpdatePaths.VersionFileName, out body, out error)) return false;
            version = body.Trim();
            return true;
        }

        private static bool TryGetText(string url, out string body, out string error)
        {
            body = "";
            error = null;
            try
            {
                HttpWebRequest request = CreateRequest(url, "GET");
                using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                using (StreamReader reader = new StreamReader(response.GetResponseStream(), Encoding.UTF8))
                {
                    body = reader.ReadToEnd();
                }
                return true;
            }
            catch (WebException e)
            {
                error = DescribeWebException(e);
                return false;
            }
            catch (Exception e)
            {
                error = e.Message;
                return false;
            }
        }

        private static HttpWebRequest CreateRequest(string url, string method)
        {
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(url);
            request.Method = method;
            // ★ 必须绕开系统代理：本机 Clash/TUN 会把 127.0.0.1 请求劫持成 502
            request.Proxy = null;
            request.Timeout = 8000;
            request.ReadWriteTimeout = 15000;
            request.KeepAlive = false;
            request.AllowAutoRedirect = true;
            request.UserAgent = "FT-HotUpdate-Verify/1.0";
            return request;
        }

        private static string DescribeWebException(WebException e)
        {
            if (e.Response is HttpWebResponse)
            {
                HttpWebResponse resp = (HttpWebResponse)e.Response;
                return string.Format("HTTP {0} {1}", (int)resp.StatusCode, resp.StatusDescription);
            }
            return e.Status + "：" + e.Message;
        }
    }
}
