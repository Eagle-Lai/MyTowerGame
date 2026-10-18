using System;
using System.Collections.Generic;
using System.IO;
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

        /// <summary>相对服务器根的路径，统一用 '/'（AB 平铺在根，dll 在 &lt;平台&gt;/HybridCLR/）。</summary>
        public string RelativePath;

        public long Size;
        public string Md5;

        /// <summary>true = 热更 dll 侧文件（要进 &lt;平台&gt;/HybridCLR/）。</summary>
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
    /// 一键热更的"落地"部分：生成清单 ▸ 本地部署 ▸ 远端上传 ▸ 校验。
    ///
    /// 【部署布局 —— 与 deploy_free_tower_cdn.py 完全一致，不要"优化"成分目录】
    ///   {服务器根}/FreeTower.version          版本号（客户端请求最新版本的入口）
    ///   {服务器根}/FreeTower_{版本}.hash       清单哈希
    ///   {服务器根}/FreeTower_{版本}.bytes      清单本体
    ///   {服务器根}/{哈希}.bundle               全量资源包（EFileNameStyle.HashName → 平铺）
    ///   {服务器根}/{32位裸哈希}                unitymonos / unityshaders 特殊包（**无 .bundle**）
    ///   {服务器根}/{平台}/HybridCLR/*.dll+md5.txt
    /// 漏掉裸哈希文件 → 跨版本加载场景 404（2026-10-16 实测踩过）。
    ///
    /// 【上传协议】远端只支持 HTTP PUT（对象存储/静态托管网关的通用做法）。
    ///   若服务器不支持 PUT，会明确报 405 —— 那种情况请继续用本地部署 + 自有运维通道，
    ///   不要在这里偷偷改成"假装成功"。
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
            HotUpdatePlan plan = new HotUpdatePlan();
            plan.Version = version;
            plan.Platform = platform;
            plan.BuildDir = buildDir;

            report.Head("生成热更清单（版本 " + version + "）");

            if (!Directory.Exists(buildDir))
            {
                report.Error("AB 输出目录不存在：" + buildDir);
                return plan;
            }

            string[] files = Directory.GetFiles(buildDir);
            int skipped = 0;
            for (int i = 0; i < files.Length; i++)
            {
                string name = Path.GetFileName(files[i]);
                if (!ShouldDeployBundleFile(name, version))
                {
                    skipped++;
                    continue;
                }
                AddFile(plan, files[i], name, false, report);
            }

            AddDllFiles(plan, dllDir, platform, report);

            if (plan.Files.Count == 0)
            {
                report.Error("清单为空：AB 目录和 dll 目录都没有可部署文件。");
            }
            else
            {
                report.Skip(string.Format("跳过非部署文件 {0} 个（.report / link.xml / .meta 等）", skipped));
                report.Ok(plan.Describe());
            }
            return plan;
        }

        /// <summary>
        /// 「仅本地验证」模式用：不依赖 AB 构建目录，直接按服务器根**已有**文件建清单。
        /// 这样即使换机 / 清过 Bundles，也能验证"服务器上现在这一版到底完不完整"。
        /// </summary>
        public static HotUpdatePlan BuildPlanFromCdn(string version, string cdnRoot, string dllDir,
            string platform, EditorUtil.Report report)
        {
            HotUpdatePlan plan = new HotUpdatePlan();
            plan.Version = version;
            plan.Platform = platform;
            plan.BuildDir = "";

            report.Head("按服务器根现有文件生成清单（版本 " + version + "）");

            if (!Directory.Exists(cdnRoot))
            {
                report.Error("服务器根目录不存在：" + cdnRoot);
                return plan;
            }

            if (string.IsNullOrEmpty(version))
            {
                report.Error("服务器根没有 " + HotUpdatePaths.VersionFileName + "，无法确定要验证的版本。");
                return plan;
            }

            // ① AB 侧：根目录平铺文件（跳过清单自身/日志/子目录）
            string[] files = Directory.GetFiles(cdnRoot);
            for (int i = 0; i < files.Length; i++)
            {
                string name = Path.GetFileName(files[i]);
                if (!ShouldDeployBundleFile(name, version))
                {
                    continue;
                }
                AddFile(plan, files[i], name, false, report);
            }

            // ② dll 侧
            AddDllFiles(plan, dllDir, platform, report);

            report.Ok(plan.Describe());
            return plan;
        }

        /// <summary>
        /// 哪些文件属于"客户端会请求的 AB 产物"。
        /// 判定：版本文件 / 本版清单 hash+bytes / *.bundle / 32 位裸哈希特殊包。
        /// </summary>
        private static bool ShouldDeployBundleFile(string name, string version)
        {
            if (string.IsNullOrEmpty(name))
            {
                return false;
            }
            if (name == HotUpdatePaths.VersionFileName)
            {
                return true;
            }
            if (name == "FreeTower_" + version + ".hash" || name == "FreeTower_" + version + ".bytes")
            {
                return true;
            }
            if (name.EndsWith(".bundle", StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
            return HotUpdateFileUtil.IsBareHashFile(name);
        }

        private static void AddDllFiles(HotUpdatePlan plan, string dllDir, string platform, EditorUtil.Report report)
        {
            if (!Directory.Exists(dllDir))
            {
                report.Error("随包 dll 目录不存在：" + dllDir);
                return;
            }

            string[] files = Directory.GetFiles(dllDir);
            for (int i = 0; i < files.Length; i++)
            {
                string name = Path.GetFileName(files[i]);
                bool isDll = name.EndsWith(".dll", StringComparison.OrdinalIgnoreCase);
                bool isMd5 = string.Equals(name, Md5ListName, StringComparison.OrdinalIgnoreCase);
                if (!isDll && !isMd5)
                {
                    continue;
                }
                AddFile(plan, files[i], platform + "/" + HotUpdatePaths.DllFolderName + "/" + name, true, report);
            }
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

        /// <summary>
        /// 把清单里的文件铺到本地服务器根（= HTTP 8000 发布的目录）。
        ///
        /// 【dll 目录是 junction 时跳过拷贝】HotUpdateServer/Android/HybridCLR 指向
        /// Assets/StreamingAssets/HybridCLR，往 junction 写就是往源目录写；源 == 目标
        /// 会抛 IOException。此时文件本来就在目标位置上，跳过即可。
        /// </summary>
        public static bool DeployLocal(HotUpdatePlan plan, string cdnRoot, EditorUtil.Report report)
        {
            report.Head("部署到本地资源服务器：" + cdnRoot);

            try
            {
                Directory.CreateDirectory(cdnRoot);

                string dllServerDir = Path.Combine(cdnRoot, plan.Platform, HotUpdatePaths.DllFolderName);
                bool dllIsJunction = HotUpdateFileUtil.IsReparsePoint(dllServerDir);
                if (dllIsJunction)
                {
                    report.Skip("dll 目录是 junction（直连 StreamingAssets/HybridCLR），无需拷贝：" + dllServerDir);
                }
                else if (plan.DllCount > 0)
                {
                    Directory.CreateDirectory(dllServerDir);
                }

                int copied = 0;
                int skipped = 0;
                for (int i = 0; i < plan.Files.Count; i++)
                {
                    HotUpdatePlanFile file = plan.Files[i];
                    string target;
                    if (file.IsDll)
                    {
                        if (dllIsJunction)
                        {
                            skipped++;
                            continue;
                        }
                        target = Path.Combine(dllServerDir, Path.GetFileName(file.RelativePath));
                    }
                    else
                    {
                        target = Path.Combine(cdnRoot, Path.GetFileName(file.RelativePath));
                    }

                    if (IsSamePath(file.SourcePath, target))
                    {
                        skipped++;
                        continue;
                    }

                    File.Copy(file.SourcePath, target, true);
                    copied++;
                }

                // 版本号文件：内容必须是纯版本号（客户端直接 trim 后当版本用）
                HotUpdateFileUtil.WriteText(
                    Path.Combine(cdnRoot, HotUpdatePaths.VersionFileName), plan.Version);

                // 清单：先写本机历史，再拷一份到服务器根
                string historyDir = Path.Combine(HotUpdatePaths.StateDir, "history");
                Directory.CreateDirectory(historyDir);
                string historyFile = Path.Combine(historyDir, plan.Version + ".json");
                if (!WriteManifest(plan, historyFile, "本地部署", report))
                {
                    return false;
                }
                File.Copy(historyFile, Path.Combine(cdnRoot, HotUpdatePaths.ManifestFileName), true);

                HotUpdateFileUtil.WriteText(
                    Path.Combine(HotUpdatePaths.StateDir, "last_version.txt"), plan.Version);

                report.Ok(string.Format("拷贝 {0} 个文件（跳过 {1} 个：junction/同位文件）", copied, skipped));
                report.Ok("版本号文件已更新：" + HotUpdatePaths.VersionFileName + " = " + plan.Version);
                report.Ok("部署完成：" + plan.Describe());
                return true;
            }
            catch (Exception e)
            {
                report.Error("本地部署失败：" + e.Message);
                return false;
            }
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

            List<HotUpdatePlanFile> all = new List<HotUpdatePlanFile>(plan.Files);
            if (!string.IsNullOrEmpty(plan.ManifestPath) && File.Exists(plan.ManifestPath))
            {
                HotUpdatePlanFile manifest = new HotUpdatePlanFile();
                manifest.SourcePath = plan.ManifestPath;
                manifest.RelativePath = HotUpdatePaths.ManifestFileName;
                manifest.Size = new FileInfo(plan.ManifestPath).Length;
                manifest.Md5 = HotUpdateFileUtil.Md5(plan.ManifestPath);
                all.Add(manifest);
            }

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
                if (progress != null)
                {
                    progress(i + 1, total);
                }
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
        /// 校验对象 = 清单里的每个文件（存在 + 大小一致），外加 dll 的 md5 清单一致性。
        /// </summary>
        public static void VerifyLocalFiles(HotUpdatePlan plan, string cdnRoot, bool deployedLocally,
            HotUpdateVerifyResult result)
        {
            // ① 版本号文件
            if (deployedLocally)
            {
                string versionFile = Path.Combine(cdnRoot, HotUpdatePaths.VersionFileName);
                result.Checked++;
                if (!File.Exists(versionFile))
                {
                    result.Failures.Add("服务器根缺少 " + HotUpdatePaths.VersionFileName);
                }
                else
                {
                    string content = File.ReadAllText(versionFile).Trim();
                    if (content != plan.Version)
                    {
                        result.Failures.Add(string.Format(
                            "版本号文件内容不符：{0}（期望 {1}）", content, plan.Version));
                    }
                }
            }

            // ② 每个文件：存在 + 大小
            for (int i = 0; i < plan.Files.Count; i++)
            {
                HotUpdatePlanFile file = plan.Files[i];
                string path = deployedLocally
                    ? Path.Combine(cdnRoot, file.RelativePath.Replace('/', Path.DirectorySeparatorChar))
                    : file.SourcePath;

                result.Checked++;
                if (!File.Exists(path))
                {
                    result.Failures.Add("文件缺失：" + file.RelativePath + "（" + path + "）");
                    continue;
                }
                long size = new FileInfo(path).Length;
                if (size != file.Size)
                {
                    result.Failures.Add(string.Format(
                        "文件大小不符：{0}（{1} vs {2}）", file.RelativePath, size, file.Size));
                }
            }

            // ③ dll 的 md5 清单：清单里的每一项都要和实际文件对得上，且计划里的 dll 都要在清单里
            VerifyDllMd5List(plan, result);

            // ④ 若服务器根有上一版清单，顺手核对（能抓出"部署到一半"）
            VerifyExistingManifest(plan, cdnRoot, result);
        }

        private static void VerifyDllMd5List(HotUpdatePlan plan, HotUpdateVerifyResult result)
        {
            string dllDir = HotUpdatePaths.DllDir;
            string listFile = Path.Combine(dllDir, Md5ListName);
            result.Checked++;
            if (!File.Exists(listFile))
            {
                result.Failures.Add("缺少 dll md5 清单：" + listFile);
                return;
            }

            Dictionary<string, string> listed = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            foreach (string line in File.ReadAllLines(listFile))
            {
                string text = line.Trim();
                if (text.Length == 0 || text.StartsWith("#"))
                {
                    continue;
                }
                int split = text.IndexOf("  ", StringComparison.Ordinal);
                if (split <= 0)
                {
                    continue;
                }
                string md5 = text.Substring(0, split).Trim();
                string name = text.Substring(split + 2).Trim();
                if (name.Length > 0)
                {
                    listed[name] = md5;
                }
            }

            if (listed.Count == 0)
            {
                result.Failures.Add("dll md5 清单为空：" + listFile);
                return;
            }

            // 清单里的条目必须和实际文件一致（防止"清单是旧的、dll 是新的"）
            foreach (KeyValuePair<string, string> kv in listed)
            {
                string path = Path.Combine(dllDir, kv.Key);
                result.Checked++;
                if (!File.Exists(path))
                {
                    result.Failures.Add("md5 清单里的 dll 不存在：" + kv.Key);
                    continue;
                }
                string actual = HotUpdateFileUtil.Md5(path);
                if (!string.Equals(actual, kv.Value, StringComparison.OrdinalIgnoreCase))
                {
                    result.Failures.Add(string.Format("dll md5 不符：{0}（实际 {1} vs 清单 {2}）",
                        kv.Key, actual, kv.Value));
                }
            }

            // 计划里的热更 dll 必须都进了清单（漏登记 = 客户端跳过更新）
            for (int i = 0; i < plan.Files.Count; i++)
            {
                HotUpdatePlanFile file = plan.Files[i];
                if (!file.IsDll)
                {
                    continue;
                }
                string name = Path.GetFileName(file.RelativePath);
                if (string.Equals(name, Md5ListName, StringComparison.OrdinalIgnoreCase))
                {
                    continue;
                }
                if (!listed.ContainsKey(name))
                {
                    result.Warnings.Add("md5 清单未包含：" + name + "（客户端不会更新它）");
                }
            }
        }

        private static void VerifyExistingManifest(HotUpdatePlan plan, string cdnRoot, HotUpdateVerifyResult result)
        {
            string path = Path.Combine(cdnRoot, HotUpdatePaths.ManifestFileName);
            if (!File.Exists(path))
            {
                result.Warnings.Add("服务器根没有 " + HotUpdatePaths.ManifestFileName + "（旧部署遗留，可忽略）");
                return;
            }

            try
            {
                HotUpdateManifestDto dto = JsonUtility.FromJson<HotUpdateManifestDto>(File.ReadAllText(path));
                if (dto == null || dto.files == null)
                {
                    result.Warnings.Add("服务器根的清单无法解析（可能不是本工具写的）");
                    return;
                }

                for (int i = 0; i < dto.files.Length; i++)
                {
                    HotUpdateFileEntryDto entry = dto.files[i];
                    string file = Path.Combine(cdnRoot, entry.path.Replace('/', Path.DirectorySeparatorChar));
                    result.Checked++;
                    if (!File.Exists(file))
                    {
                        result.Failures.Add("清单登记但服务器上不存在：" + entry.path);
                        continue;
                    }
                    long size = new FileInfo(file).Length;
                    if (entry.size > 0 && size != entry.size)
                    {
                        result.Failures.Add(string.Format("清单大小不符：{0}（{1} vs {2}）",
                            entry.path, size, entry.size));
                    }
                }
            }
            catch (Exception e)
            {
                result.Warnings.Add("核对服务器清单异常：" + e.Message);
            }
        }

        // ==================================================================
        // 校验 ②：HTTP 链路（与客户端同一条请求路径）
        // ==================================================================

        /// <summary>
        /// 用**和客户端完全一样的 URL** 请求一遍：版本文件 → 清单 hash/bytes → 每个 bundle/dll。
        /// 只做 HEAD（拿到 200 + Content-Length 即证明"这个路径真的能下到"）；
        /// 版本文件用 GET 读内容，确认版本号确实是本次要发布的。
        /// 阻塞调用（由流水线放到后台线程），不碰任何 Unity API。
        /// </summary>
        public static void VerifyHttp(HotUpdatePlan plan, string baseUrl,
            Action<int, int> progress, HotUpdateVerifyResult result)
        {
            baseUrl = baseUrl.TrimEnd('/');
            int total = plan.Files.Count + 1;
            int done = 0;

            // ① 版本号文件（GET 读内容）
            string versionError;
            string versionBody;
            result.Checked++;
            if (!TryGetText(baseUrl + "/" + HotUpdatePaths.VersionFileName, out versionBody, out versionError))
            {
                result.Failures.Add("GET " + HotUpdatePaths.VersionFileName + " 失败：" + versionError);
            }
            else if (versionBody.Trim() != plan.Version)
            {
                result.Failures.Add(string.Format("HTTP 上的版本号是 {0}，期望 {1}", versionBody.Trim(), plan.Version));
            }
            done++;
            if (progress != null) progress(done, total);

            // ② 每个文件 HEAD
            for (int i = 0; i < plan.Files.Count; i++)
            {
                HotUpdatePlanFile file = plan.Files[i];
                string url = baseUrl + "/" + file.RelativePath;
                long length;
                string error;
                result.Checked++;
                if (!TryHead(url, out length, out error))
                {
                    result.Failures.Add("HEAD " + file.RelativePath + " 失败：" + error);
                }
                else if (length >= 0 && file.Size > 0 && length != file.Size)
                {
                    result.Failures.Add(string.Format("HTTP 文件大小不符：{0}（{1} vs {2}）",
                        file.RelativePath, length, file.Size));
                }
                done++;
                if (progress != null) progress(done, total);
            }
        }

        /// <summary>探测某个地址上的版本号（用于"端口被别的服务占着"时判断能不能复用）。</summary>
        public static bool TryGetRemoteVersion(string baseUrl, out string version, out string error)
        {
            version = "";
            string body;
            if (!TryGetText(baseUrl.TrimEnd('/') + "/" + HotUpdatePaths.VersionFileName, out body, out error))
            {
                return false;
            }
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

        private static bool TryHead(string url, out long length, out string error)
        {
            length = -1;
            error = null;
            try
            {
                HttpWebRequest request = CreateRequest(url, "HEAD");
                using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                {
                    length = response.ContentLength;
                    return true;
                }
            }
            catch (WebException e)
            {
                // 少数静态服务不实现 HEAD（405/501）：退回 GET 只读 1 字节验证可达性
                HttpWebResponse resp = e.Response as HttpWebResponse;
                if (resp != null)
                {
                    int code = (int)resp.StatusCode;
                    if (code == 405 || code == 501)
                    {
                        return TryGetLength(url, out length, out error);
                    }
                }
                error = DescribeWebException(e);
                return false;
            }
            catch (Exception e)
            {
                error = e.Message;
                return false;
            }
        }

        private static bool TryGetLength(string url, out long length, out string error)
        {
            length = -1;
            error = null;
            try
            {
                HttpWebRequest request = CreateRequest(url, "GET");
                request.AddRange(0, 0);
                using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                {
                    length = response.ContentLength;
                    // 206 时 ContentLength 是分片长度（=1），不做大小比较
                    if ((int)response.StatusCode == 206)
                    {
                        length = -1;
                    }
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
