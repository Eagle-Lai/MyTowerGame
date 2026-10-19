using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using UnityEngine;
using UnityEngine.Networking;

namespace FTProject.AOT
{
    /// <summary>
    /// AOT HTTP downloader for the DLL set pinned by BootReleaseStore.Selected.
    /// Payloads live at releases/{id}/HybridCLR and stage in a descriptor-specific directory.
    /// Range transfers and bounded retries preserve partial downloads; MD5 validation precedes
    /// atomic replacement. Any missing or failed DLL blocks assembly loading and shows Retry.
    /// AOT metadata is always supplied by the matching APK and is never remotely replaced.
    /// </summary>
    public static class HotUpdateDllDownloader
    {
        /// <summary>dll 在服务器上的子目录名（与 StreamingAssets/HybridCLR 同名，便于对照）</summary>
        private const string RemoteSubDir = "HybridCLR";

        /// <summary>校验清单文件名（与 dll 同目录，构建期生成）。</summary>
        private const string Md5ListFileName = "md5.txt";

        /// <summary>单个 dll 的下载超时（秒）。局域网下 1MB 的 dll 通常是毫秒级，30 秒足够宽裕。</summary>
        private const int TimeoutSeconds = 30;

        /// <summary>
        /// **整批下载的总超时（秒）**。超过这个时间无论进行到哪一步都收敛退出，
        /// 未完成的 DLL 集合会停留在更新页，已验证文件留待重试。
        /// </summary>
        private const int TotalTimeoutSeconds = 90;

        /// <summary>单个文件的**额外**重试次数（首次尝试之外）。</summary>
        private const int MaxRetryPerFile = 3;

        /// <summary>重试基础等待（秒）。第 n 次重试等待 = base * 2^(n-1)，上限 <see cref="MaxRetryDelay"/>。</summary>
        private const float RetryBaseDelay = 1f;

        /// <summary>单次重试的最大等待（秒）。</summary>
        private const float MaxRetryDelay = 8f;

        /// <summary>断点续传的**最小文件尺寸**：小于它就不续传（避免为小文件付 Range 请求的开销）。</summary>
        private const long ResumeMinBytes = 256L * 1024L;

        /// <summary>
        /// 本地缓存清单的有效期（秒）。这段时间内不重复请求 md5.txt。
        /// 避免一次启动里为每个 dll 都去拉一遍清单。
        /// </summary>
        private const float Md5ListCacheSeconds = 60f;

        /// <summary>本次下载的结果（供 Boot 日志/界面展示）</summary>
        public sealed class Result
        {
            /// <summary>尝试下载的文件数</summary>
            public int Total;
            /// <summary>成功下载并落盘的文件数</summary>
            public int Downloaded;
            /// <summary>因 md5 一致（已是最新）而跳过的文件数</summary>
            public int UpToDate;
            /// <summary>服务器明确返回 404 的文件数（该发布失败）</summary>
            public int Skipped;
            /// <summary>出错条目摘要（换行分隔，非空即阻止加载）</summary>
            public string ErrorSummary;
            /// <summary>本批次是否因**总超时**而提前收敛</summary>
            public bool TimedOut;

            /// <summary>是否真的更新过至少一个文件（决定"本次启动是不是热更后的新版本"）</summary>
            public bool Updated { get { return Downloaded > 0; } }

            /// <summary>供日志用的单行摘要。</summary>
            public string ToSummary()
            {
                return string.Format(
                    "更新 {0} / 已最新 {1} / 不存在 {2} / 共 {3}{4}",
                    Downloaded, UpToDate, Skipped, Total,
                    TimedOut ? "（总超时提前收敛）" : string.Empty);
            }
        }

        /// <summary>
        /// 把当前发布的热更 DLL 集合同步到独立暂存目录。
        /// <paramref name="onProgress"/> 参数为 (已完成数, 总数)，用于 Boot 界面进度条。
        /// 本方法**永不抛异常**（全部内部消化为日志 + Result）。
        /// </summary>
        public static System.Collections.IEnumerator DownloadAll(
            string serverRoot,
            Action<int, int> onProgress,
            Action<Result> onDone)
        {
            Result result = new Result();

            string[] names = BuildFileList();
            result.Total = names.Length;

            if (string.IsNullOrEmpty(serverRoot))
            {
                result.ErrorSummary = "未配置服务器地址";
                Finish(result, onProgress, onDone);
                yield break;
            }

            string root = serverRoot.TrimEnd('/');
            string platform = GetPlatformFolder();
            string targetDir = BootReleaseStore.DllDirectory;

            try
            {
                if (Directory.Exists(targetDir) == false)
                {
                    Directory.CreateDirectory(targetDir);
                }
            }
            catch (Exception e)
            {
                result.ErrorSummary = "无法创建目录 " + targetDir + "：" + e.Message;
                Finish(result, onProgress, onDone);
                yield break;
            }

            // ---------- ① 使用已固定描述符内的完整校验清单 ----------
            var md5Map = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            foreach (var file in BootReleaseStore.Selected.dlls) md5Map.Add(file.name, file.md5);

            float deadline = Time.realtimeSinceStartup + TotalTimeoutSeconds;

            // ---------- ③ 逐文件同步 ----------
            for (int i = 0; i < names.Length; i++)
            {
                string fileName = names[i];

                // 总超时检查（每个文件开始前）
                if (Time.realtimeSinceStartup >= deadline)
                {
                    result.TimedOut = true;
                    result.ErrorSummary = AppendLine(result.ErrorSummary,
                        string.Format("总超时（{0} 秒）已到，剩余 {1} 个文件未处理", TotalTimeoutSeconds, names.Length - i));
                    break;
                }

                string target = Path.Combine(targetDir, fileName);

                string expectedMd5;
                bool hasExpected = md5Map.TryGetValue(fileName, out expectedMd5) && string.IsNullOrEmpty(expectedMd5) == false;

                if (hasExpected == false)
                {
                    // 缺失校验值意味着描述符不完整，禁止加载
                    result.ErrorSummary = AppendLine(result.ErrorSummary, "Missing checksum: " + fileName);
                    break;
                }

                // 本地已是最新？→ 跳过下载
                if (IsLocalUpToDate(target, expectedMd5))
                {
                    result.UpToDate++;
                    Report(onProgress, i + 1, names.Length);
                    continue;
                }

                // 真正下载（带重试 / 续传 / 校验 / 原子替换）
                string url = BootReleaseStore.ResourceRoot + "/HybridCLR/" + fileName;
                FileOutcome outcome = FileOutcome.Failed;
                string error = null;

                yield return DownloadOneWithRetryCo(
                    url, target, fileName, expectedMd5, deadline,
                    o => outcome = o,
                    e => error = e);

                switch (outcome)
                {
                    case FileOutcome.Downloaded:
                        result.Downloaded++;
                        break;
                    case FileOutcome.NotFound:
                        result.ErrorSummary = AppendLine(result.ErrorSummary, "HTTP 404: " + fileName);
                        break;
                    case FileOutcome.UpToDate:
                        result.UpToDate++;
                        break;
                    default:
                        result.ErrorSummary = AppendLine(result.ErrorSummary,
                            fileName + "：" + (error ?? "未知错误"));
                        break;
                }

                Report(onProgress, i + 1, names.Length);
            }

            Finish(result, onProgress, onDone);
        }

        /// <summary>单文件的最终结局。</summary>
        private enum FileOutcome
        {
            /// <summary>已下载、校验通过、原子替换成功</summary>
            Downloaded,
            /// <summary>服务器 404：发布不完整，禁止加载</summary>
            NotFound,
            /// <summary>md5 一致，本地已是最新</summary>
            UpToDate,
            /// <summary>其它失败（网络 / 校验 / 写入）—— 保持本地原文件不动</summary>
            Failed,
        }

        /// <summary>带重试的外层。404 与"已是最新"直接返回，不重试。</summary>
        private static System.Collections.IEnumerator DownloadOneWithRetryCo(
            string url, string target, string fileName, string expectedMd5, float deadline,
            Action<FileOutcome> onResult, Action<string> onError)
        {
            string lastError = null;

            for (int attempt = 0; attempt <= MaxRetryPerFile; attempt++)
            {
                if (attempt > 0)
                {
                    // 退避等待（同时检查总超时）
                    float delay = Mathf.Min(RetryBaseDelay * Mathf.Pow(2f, attempt - 1), MaxRetryDelay);
                    Debug.LogWarning(string.Format(
                        "[HotUpdate] 重试 {0}（第 {1}/{2} 次）：{3}，等待 {4:F1}s",
                        fileName, attempt, MaxRetryPerFile, lastError, delay));

                    float wake = Time.realtimeSinceStartup + delay;
                    while (Time.realtimeSinceStartup < wake)
                    {
                        yield return null;
                    }
                }

                // 每次尝试前都重新判总超时
                if (Time.realtimeSinceStartup >= deadline)
                {
                    onResult(FileOutcome.Failed);
                    onError("总超时，放弃重试");
                    yield break;
                }

                FileOutcome outcome = FileOutcome.Failed;
                string error = null;
                bool retryable = false;

                yield return DownloadOneCo(url, target, fileName, expectedMd5,
                    o => outcome = o, e => error = e, r => retryable = r);

                if (outcome == FileOutcome.Downloaded || outcome == FileOutcome.NotFound || outcome == FileOutcome.UpToDate)
                {
                    onResult(outcome);
                    yield break;
                }

                lastError = error;

                if (retryable == false)
                {
                    // 不可重试的错误（例如磁盘写满、md5 不匹配）直接收尾
                    onResult(FileOutcome.Failed);
                    onError(error);
                    yield break;
                }
            }

            onResult(FileOutcome.Failed);
            onError(lastError ?? "重试次数已用尽");
        }

        /// <summary>
        /// 下载**单个**文件一次。流程：
        ///   ① 判断是否可续传（.part 残留且够大）→ 组 Range 请求
        ///   ② 发送请求
        ///   ③ 成功 → 与 expectedMd5 比对（含断点拼接后的完整文件）
        ///   ④ 校验通过 → 原子替换；否则丢弃 .part，**本地原文件保持不动**
        /// </summary>
        private static System.Collections.IEnumerator DownloadOneCo(
            string url, string target, string fileName, string expectedMd5,
            Action<FileOutcome> onResult, Action<string> onError, Action<bool> onRetryable)
        {
            string partPath = target + ".part";

            // ---------- ① 续传判定 ----------
            long resumeOffset = 0;
            try
            {
                if (File.Exists(partPath))
                {
                    long len = new FileInfo(partPath).Length;
                    if (len >= ResumeMinBytes && len < long.MaxValue)
                    {
                        resumeOffset = len;
                    }
                    else if (len > 0)
                    {
                        // 太小，续传不划算 → 丢掉重下
                        File.Delete(partPath);
                    }
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning("[HotUpdate] 检查续传残留失败 " + fileName + "：" + e.Message);
                try { File.Delete(partPath); } catch (Exception) { }
                resumeOffset = 0;
            }

            UnityWebRequest req = null;
            try
            {
                req = UnityWebRequest.Get(url);
                req.timeout = TimeoutSeconds;

                if (resumeOffset > 0)
                {
                    // 追加写入 + Range 头：从断点处继续
                    var handler = new DownloadHandlerFile(partPath, true);
                    handler.removeFileOnAbort = false;
                    req.downloadHandler = handler;
                    req.SetRequestHeader("Range", string.Format("bytes={0}-", resumeOffset));
                    Debug.Log(string.Format("[HotUpdate] 断点续传 {0}：从 {1:N0} 字节继续", fileName, resumeOffset));
                }
                else
                {
                    // 从零开始：先删残留，避免 DownloadHandlerFile 追加到旧内容上
                    try { if (File.Exists(partPath)) File.Delete(partPath); } catch (Exception) { }
                    var handler = new DownloadHandlerFile(partPath, false);
                    handler.removeFileOnAbort = true;
                    req.downloadHandler = handler;
                }

                yield return req.SendWebRequest();

                // ---------- ③ 网络层结果 ----------
                long httpCode = req.responseCode;

                if (httpCode == 404)
                {
                    // 服务器文件缺失：报告失败，清理该请求残留的 .part
                    CleanupPart(partPath);
                    onResult(FileOutcome.NotFound);
                    onRetryable(false);
                    yield break;
                }

                if (req.result != UnityWebRequest.Result.Success)
                {
                    // 416 = Range 越界（通常是服务端文件变小了）→ 丢掉残留重来一次
                    bool retry = true;
                    string err;
                    if (httpCode == 416)
                    {
                        Debug.LogWarning("[HotUpdate] " + fileName + " 续传位置越界（416），丢弃残留后重试");
                        CleanupPart(partPath);
                    }
                    err = string.Format("{0}（HTTP {1}）", req.error, httpCode);
                    onResult(FileOutcome.Failed);
                    onError(err);
                    onRetryable(retry);
                    yield break;
                }

                // ---------- ④ 完整性校验 ----------
                string actualMd5;
                try
                {
                    actualMd5 = ComputeFileMd5(partPath);
                }
                catch (Exception e)
                {
                    CleanupPart(partPath);
                    onResult(FileOutcome.Failed);
                    onError("读取下载结果失败：" + e.Message);
                    onRetryable(true);   // 可能是 IO 抖动，允许重试
                    yield break;
                }

                if (string.Equals(actualMd5, expectedMd5, StringComparison.OrdinalIgnoreCase) == false)
                {
                    // 校验失败 = 数据坏了 → 丢弃，绝不让它顶掉本地的好文件
                    CleanupPart(partPath);
                    Debug.LogWarning(string.Format(
                        "[HotUpdate] md5 校验失败 {0}：期望 {1}，实际 {2}（已丢弃，保留本地版本）",
                        fileName, expectedMd5, actualMd5));
                    onResult(FileOutcome.Failed);
                    onError(string.Format("md5 校验失败（期望 {0}，实际 {1}）", expectedMd5, actualMd5));
                    onRetryable(true);   // 传输损坏可重试
                    yield break;
                }

                // ---------- ⑤ 原子替换 ----------
                try
                {
                    BootReleaseStore.AtomicMove(partPath, target);

                    long size = new FileInfo(target).Length;
                    Debug.Log(string.Format(
                        "[HotUpdate] dll 已更新：{0}（{1:N0} 字节，md5 校验通过）", fileName, size));

                    onResult(FileOutcome.Downloaded);
                    onRetryable(false);
                }
                catch (Exception e)
                {
                    CleanupPart(partPath);
                    Debug.LogError("[HotUpdate] 替换失败 " + fileName + "：" + e.Message);
                    onResult(FileOutcome.Failed);
                    onError("写入失败：" + e.Message);
                    onRetryable(false);   // 写盘失败重试无意义
                }
            }
            finally
            {
                if (req != null)
                {
                    req.Dispose();
                }
            }
        }

        /// <summary>
        /// 拉取 md5 清单。成功 → 返回 文件名→md5 的字典；失败 → null。
        /// </summary>
        private static System.Collections.IEnumerator FetchMd5ListCo(
            string url, Action<Dictionary<string, string>> onDone)
        {
            Dictionary<string, string> map = null;

            using (UnityWebRequest req = UnityWebRequest.Get(url))
            {
                req.timeout = TimeoutSeconds;
                req.downloadHandler = new DownloadHandlerBuffer();

                yield return req.SendWebRequest();

                if (req.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        map = ParseMd5List(req.downloadHandler.text);
                        Debug.Log(string.Format("[HotUpdate] 已获取校验清单，共 {0} 条", map.Count));
                    }
                    catch (Exception e)
                    {
                        Debug.LogWarning("[HotUpdate] 解析 md5 清单失败：" + e.Message);
                        map = null;
                    }
                }
                else
                {
                    Debug.LogWarning(string.Format(
                        "[HotUpdate] 获取 md5 清单失败（HTTP {0}）：{1}\n  URL: {2}",
                        req.responseCode, req.error, url));
                }
            }

            if (onDone != null)
            {
                onDone(map);
            }
        }

        /// <summary>
        /// 解析校验清单。容忍以下格式差异：
        ///   · `#` 开头的注释行、空行
        ///   · md5 与文件名之间用**空格或制表符**分隔（兼容 `md5sum` 输出）
        ///   · 文件名前可能有 `*` 前缀（`md5sum -b` 二进制模式）
        ///   · md5 大小写不敏感（统一转小写存储）
        ///   · 行尾 `\r`（Windows 生成的清单）
        /// </summary>
        private static Dictionary<string, string> ParseMd5List(string text)
        {
            var map = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            if (string.IsNullOrEmpty(text))
            {
                return map;
            }

            string[] lines = text.Split('\n');
            for (int i = 0; i < lines.Length; i++)
            {
                string line = lines[i].Trim();
                if (line.Length == 0 || line[0] == '#')
                {
                    continue;
                }

                // 取第一个空白符切分
                int sep = -1;
                for (int c = 0; c < line.Length; c++)
                {
                    if (line[c] == ' ' || line[c] == '\t')
                    {
                        sep = c;
                        break;
                    }
                }
                if (sep <= 0)
                {
                    continue;
                }

                string hash = line.Substring(0, sep).Trim().ToLowerInvariant();
                string file = line.Substring(sep).Trim();

                // 去掉 md5sum 二进制模式的 `*` 前缀
                if (file.StartsWith("*", StringComparison.Ordinal))
                {
                    file = file.Substring(1);
                }
                // 只取文件名（清单里可能写了相对路径）
                file = Path.GetFileName(file);

                if (hash.Length != 32 || file.Length == 0)
                {
                    continue;
                }

                map[file] = hash;
            }
            return map;
        }

        /// <summary>本地文件是否已是最新（md5 一致）。任何异常都返回 false（宁可重下）。</summary>
        private static bool IsLocalUpToDate(string path, string expectedMd5)
        {
            try
            {
                if (File.Exists(path) == false)
                {
                    return false;
                }
                string actual = ComputeFileMd5(path);
                return string.Equals(actual, expectedMd5, StringComparison.OrdinalIgnoreCase);
            }
            catch (Exception)
            {
                return false;
            }
        }

        /// <summary>计算文件 md5（流式读取，避免大文件一次性进内存）。</summary>
        private static string ComputeFileMd5(string path)
        {
            using (var md5 = MD5.Create())
            using (var stream = File.OpenRead(path))
            {
                byte[] hash = md5.ComputeHash(stream);
                var sb = new System.Text.StringBuilder(hash.Length * 2);
                for (int i = 0; i < hash.Length; i++)
                {
                    sb.Append(hash[i].ToString("x2"));
                }
                return sb.ToString();
            }
        }

        private static void CleanupPart(string partPath)
        {
            try
            {
                if (File.Exists(partPath))
                {
                    File.Delete(partPath);
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning("[HotUpdate] 清理临时文件失败 " + partPath + "：" + e.Message);
            }
        }

        private static void Report(Action<int, int> onProgress, int done, int total)
        {
            if (onProgress != null)
            {
                onProgress(done, total);
            }
        }

        private static void Finish(Result result, Action<int, int> onProgress, Action<Result> onDone)
        {
            Report(onProgress, result.Total, result.Total);
            if (onDone != null)
            {
                onDone(result);
            }
        }

        private static string AppendLine(string existing, string line)
        {
            return string.IsNullOrEmpty(existing) ? line : (existing + "\n" + line);
        }

        /// <summary>要同步的完整热更 DLL 名单；不包含 AOT 元数据</summary>
        private static string[] BuildFileList()
        {
            return HotUpdateAssembler.HotUpdateAssemblies;
        }

        /// <summary>
        /// 平台目录名。**必须与 YooAsset 的构建输出平台名一致**，
        /// 否则服务器上的目录名对不上（YooAsset 用 BuildTarget 的名字，如 "Android"）。
        /// </summary>
        private static string GetPlatformFolder()
        {
#if UNITY_ANDROID
            return "Android";
#elif UNITY_IOS
            return "iOS";
#elif UNITY_STANDALONE_WIN
            return "StandaloneWindows64";
#elif UNITY_STANDALONE_OSX
            return "StandaloneOSX";
#else
            return "Unknown";
#endif
        }
    }
}
