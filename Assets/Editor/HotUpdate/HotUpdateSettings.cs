using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 一键热更链路里所有路径/文件名的**唯一来源**。
    ///
    /// 【为什么集中一份】这条链路横跨 4 个目录：
    ///   · 编译产物   HybridCLRData/HotUpdateDlls/&lt;平台&gt;/      （HybridCLR 生成）
    ///   · 随包 dll   Assets/StreamingAssets/HybridCLR/          （dll 热更的"原点"）
    ///   · AB 构建    Bundles/&lt;平台&gt;/FreeTower/&lt;版本&gt;/       （YooAsset 输出）
    ///   · 服务器根   HotUpdateServer/release.json               （最后激活的指针）
    ///   · 不可变内容 releases/{id}/                             （完整 DLL + AB）
    /// 客户端固定同一 release 的 resourceVersion、manifestMd5 和 DLL 校验值。
    /// 不再把根目录 FreeTower.version 或 Android/HybridCLR 当作新启动协议入口。
    /// </summary>
    public static class HotUpdatePaths
    {
        /// <summary>YooAsset 包裹名（= AB 输出目录名，改了热更必失效）。</summary>
        public const string PackageName = "FreeTower";

        /// <summary>随包 dll 子目录（运行时按此路径读）。</summary>
        public const string DllFolderName = "HybridCLR";

        /// <summary>YooAsset 版本文件名（位于不可变 release 内；旧部署探测也可读取）。</summary>
        public const string VersionFileName = "FreeTower.version";

        /// <summary>本地热更服务器根（git 忽略，各机自建；HTTP 8000 指向它）。</summary>
        public const string CdnRootRelative = "HotUpdateServer";

        /// <summary>构建记录/历史目录（git 忽略，只本机用）。</summary>
        public const string StateDirRelative = "Library/FT_HotUpdate";

        /// <summary>外部轮询用状态文件（MCP / CI 读它判断流水线进度）。</summary>
        public const string StatusFileRelative = "Library/FT_HotUpdateStatus.txt";

        /// <summary>本次运行日志（面板展示 + 失败时贴给同事）。</summary>
        public const string LogFileRelative = "Logs/HotUpdate/last_run.log";

        /// <summary>部署到服务器根的清单文件名（服务端可读，客户端不读）。</summary>
        public const string ManifestFileName = "hotupdate_manifest.json";

        /// <summary>工程根（不依赖进程工作目录：batchmode 的 cwd 未必是工程根）。</summary>
        public static string ProjectRoot
        {
            get { return Path.GetDirectoryName(Application.dataPath); }
        }

        /// <summary>把工程内相对路径转成绝对路径（分隔符统一）。</summary>
        public static string Resolve(string relative)
        {
            if (string.IsNullOrEmpty(relative))
            {
                return ProjectRoot;
            }
            return Path.Combine(ProjectRoot, relative.Replace('/', Path.DirectorySeparatorChar));
        }

        public static string CdnRoot { get { return Resolve(CdnRootRelative); } }

        /// <summary>随包 dll 目录（md5 清单也在这里）。</summary>
        public static string DllDir
        {
            get { return Path.Combine(Application.dataPath, "StreamingAssets", DllFolderName); }
        }

        public static string StateDir { get { return Resolve(StateDirRelative); } }

        public static string StatusFile { get { return Resolve(StatusFileRelative); } }

        public static string LogFile { get { return Resolve(LogFileRelative); } }

        /// <summary>当前构建目标的平台目录名（Android / iOS / StandaloneWindows64 …）。</summary>
        public static string PlatformFolder
        {
            get { return EditorUserBuildSettings.activeBuildTarget.ToString(); }
        }

        /// <summary>AB 构建根：Bundles/&lt;平台&gt;/&lt;包裹&gt;（YooAsset 默认输出根）。</summary>
        public static string BuildRoot(BuildTarget target)
        {
            return Path.Combine(ProjectRoot, "Bundles", target.ToString(), PackageName);
        }

        public static string BuildRoot()
        {
            return BuildRoot(EditorUserBuildSettings.activeBuildTarget);
        }

        /// <summary>某版本的 AB 输出目录：Bundles/&lt;平台&gt;/&lt;包裹&gt;/&lt;版本&gt;。</summary>
        public static string BuildDir(BuildTarget target, string version)
        {
            return Path.Combine(BuildRoot(target), version);
        }

        public static string BuildDir(string version)
        {
            return BuildDir(EditorUserBuildSettings.activeBuildTarget, version);
        }

        /// <summary>仅供旧工具识别历史布局；新发布使用 release.contentRoot + /HybridCLR。</summary>
        public static string DllServerRelative
        {
            get { return PlatformFolder + "/" + DllFolderName; }
        }
    }

    /// <summary>
    /// 一键热更的可调项。
    ///
    /// 【存哪】EditorPrefs（机器级）。理由：
    ///   · 远端上传地址/凭据是**本机环境**，不该进 git（进 git 会随仓库泄给所有人）；
    ///   · 版本号覆盖、是否 Play 冒烟属于"这次想怎么跑"，跨会话记住比每次重填省事。
    /// 单次运行的快照另外写进 SessionState（域重载后不丢），见 <see cref="HotUpdateOptions"/>。
    /// </summary>
    public static class HotUpdateSettings
    {
        private const string Prefix = "FT.HotUpdate.";

        /// <summary>① 部署到本地 HotUpdateServer（默认开：模拟器/真机都靠它）。</summary>
        public static bool DeployLocal
        {
            get { return EditorPrefs.GetBool(Prefix + "DeployLocal", true); }
            set { EditorPrefs.SetBool(Prefix + "DeployLocal", value); }
        }

        /// <summary>② 上传到远端资源服务器（默认关：没配地址时不要误触发）。</summary>
        public static bool UploadRemote
        {
            get { return EditorPrefs.GetBool(Prefix + "UploadRemote", false); }
            set { EditorPrefs.SetBool(Prefix + "UploadRemote", value); }
        }

        /// <summary>远端根地址，如 https://cdn.example.com/freedomtower（不带结尾斜杠）。</summary>
        public static string RemoteBaseUrl
        {
            get { return EditorPrefs.GetString(Prefix + "RemoteBaseUrl", ""); }
            set { EditorPrefs.SetString(Prefix + "RemoteBaseUrl", (value ?? "").Trim()); }
        }

        /// <summary>可选附加请求头，格式 "Name: Value"（如 Authorization: Bearer xxx）。</summary>
        public static string RemoteHeader
        {
            get { return EditorPrefs.GetString(Prefix + "RemoteHeader", ""); }
            set { EditorPrefs.SetString(Prefix + "RemoteHeader", (value ?? "").Trim()); }
        }

        /// <summary>③ 构建完成后做本地运行验证（文件完整性 + HTTP 链路）。</summary>
        public static bool VerifyAfterBuild
        {
            get { return EditorPrefs.GetBool(Prefix + "Verify", true); }
            set { EditorPrefs.SetBool(Prefix + "Verify", value); }
        }

        /// <summary>④ 验证后进入 Play 观察 8 秒（默认关：会占用编辑器）。</summary>
        public static bool PlaySmoke
        {
            get { return EditorPrefs.GetBool(Prefix + "PlaySmoke", false); }
            set { EditorPrefs.SetBool(Prefix + "PlaySmoke", value); }
        }

        /// <summary>⑤ 彻底重建 AB（清空 SBP 缓存与整个包裹根），默认关。</summary>
        public static bool FullRebuild
        {
            get { return EditorPrefs.GetBool(Prefix + "FullRebuild", false); }
            set { EditorPrefs.SetBool(Prefix + "FullRebuild", value); }
        }

        /// <summary>手动指定版本号（留空 = 自动递增）。</summary>
        public static string VersionOverride
        {
            get { return EditorPrefs.GetString(Prefix + "Version", ""); }
            set { EditorPrefs.SetString(Prefix + "Version", (value ?? "").Trim()); }
        }

        /// <summary>本地验证用的端口（与 HotUpdateServer 的 HTTP 端口一致，默认 8000）。</summary>
        public static int VerifyPort
        {
            get { return EditorPrefs.GetInt(Prefix + "Port", 8000); }
            set { EditorPrefs.SetInt(Prefix + "Port", value); }
        }
    }

    /// <summary>
    /// 单次运行的选项快照（进 SessionState，域重载后继续按原选项跑）。
    ///
    /// 【为什么不用 static 字段】HybridCLR Generate/All 会重写 AOTGenericReferences.cs，
    /// 触发编译 + 域重载；static 字段会被清空，流水线就会"忘了自己要部署到哪"。
    /// </summary>
    [Serializable]
    public class HotUpdateOptions
    {
        public bool local;
        public bool remote;
        public bool verify;
        public bool play;
        public bool fullRebuild;
        public bool verifyOnly;
        public string remoteUrl;
        public string remoteHeader;
        public string versionOverride;

        public static HotUpdateOptions FromSettings(bool verifyOnly)
        {
            HotUpdateOptions o = new HotUpdateOptions();
            o.verifyOnly = verifyOnly;
            o.local = HotUpdateSettings.DeployLocal;
            o.remote = HotUpdateSettings.UploadRemote;
            o.verify = HotUpdateSettings.VerifyAfterBuild;
            o.play = HotUpdateSettings.PlaySmoke && !verifyOnly;
            o.fullRebuild = HotUpdateSettings.FullRebuild && !verifyOnly;
            o.remoteUrl = HotUpdateSettings.RemoteBaseUrl;
            o.remoteHeader = HotUpdateSettings.RemoteHeader;
            o.versionOverride = verifyOnly ? "" : HotUpdateSettings.VersionOverride;
            return o;
        }

        /// <summary>写回 EditorPrefs（只写"下次也想要"的项，verifyOnly 是单次语义）。</summary>
        public void SaveToSettings()
        {
            HotUpdateSettings.DeployLocal = local;
            HotUpdateSettings.UploadRemote = remote;
            HotUpdateSettings.RemoteBaseUrl = remoteUrl;
            HotUpdateSettings.RemoteHeader = remoteHeader;
            HotUpdateSettings.VerifyAfterBuild = verify;
            HotUpdateSettings.PlaySmoke = play;
            HotUpdateSettings.FullRebuild = fullRebuild;
            HotUpdateSettings.VersionOverride = versionOverride;
        }
    }

    /// <summary>
    /// 资源包版本号的解析 / 扫描 / 自增。
    ///
    /// 【为什么"自增"要三处取最大】历史实现只扫 Bundles 目录（BuildApkFull / ReporterHotfixBuild
    /// 都一样）。但 Bundles 是 git 忽略的构建产物，换机、清缓存、或只 pull 了别人出的包时，
    /// 本地目录可能比服务器旧 → 直接扫会**撞回一个已经发布过的版本号**，客户端因为
    /// "版本号没变"而完全不下载（表现为"改了代码但真机没反应"）。
    /// 因此这里取三者最大：①本地已构建的版本 ②服务器 release.json ③上次构建记录。
    /// </summary>
    public static class HotUpdateVersionUtil
    {
        public static bool TryParse(string version, out int major, out int minor, out int patch)
        {
            major = minor = patch = 0;
            if (string.IsNullOrEmpty(version))
            {
                return false;
            }
            string[] parts = version.Trim().Split('.');
            if (parts.Length != 3)
            {
                return false;
            }
            return int.TryParse(parts[0], NumberStyles.Integer, CultureInfo.InvariantCulture, out major)
                && int.TryParse(parts[1], NumberStyles.Integer, CultureInfo.InvariantCulture, out minor)
                && int.TryParse(parts[2], NumberStyles.Integer, CultureInfo.InvariantCulture, out patch);
        }

        public static bool IsValid(string version)
        {
            int a, b, c;
            return TryParse(version, out a, out b, out c);
        }

        public static string Bump(string version)
        {
            int major, minor, patch;
            if (!TryParse(version, out major, out minor, out patch))
            {
                return "1.0.0";
            }
            return string.Format(CultureInfo.InvariantCulture, "{0}.{1}.{2}", major, minor, patch + 1);
        }

        private static int Compare(string a, string b)
        {
            int am, an, ap, bm, bn, bp;
            if (!TryParse(a, out am, out an, out ap)) return -1;
            if (!TryParse(b, out bm, out bn, out bp)) return 1;
            if (am != bm) return am.CompareTo(bm);
            if (an != bn) return an.CompareTo(bn);
            return ap.CompareTo(bp);
        }

        /// <summary>已激活 release.json 的资源版本；无新协议指针时兼容旧版本文件。</summary>
        public static string GetDeployedVersion()
        {
            try
            {
                string pointer = Path.Combine(HotUpdatePaths.CdnRoot, "release.json");
                if (File.Exists(pointer))
                {
                    var release = JsonUtility.FromJson<FTProject.AOT.BootRelease>(File.ReadAllText(pointer));
                    return release != null && IsValid(release.resourceVersion) ? release.resourceVersion : "";
                }
                string file = Path.Combine(HotUpdatePaths.CdnRoot, HotUpdatePaths.VersionFileName);
                if (File.Exists(file))
                {
                    return File.ReadAllText(file).Trim();
                }
            }
            catch (Exception)
            {
                // 读不到不算错误：下面还有两个来源兜底
            }
            return "";
        }

        /// <summary>上次通过本面板构建的版本（Library/FT_Hot_update/last_version.txt）。</summary>
        public static string GetRecordedVersion()
        {
            try
            {
                string file = Path.Combine(HotUpdatePaths.StateDir, "last_version.txt");
                if (File.Exists(file))
                {
                    return File.ReadAllText(file).Trim();
                }
            }
            catch (Exception)
            {
            }
            return "";
        }

        /// <summary>本地已构建过的版本号（Bundles/&lt;平台&gt;/FreeTower 下的 x.y.z 目录）。</summary>
        public static List<string> ListBuiltVersions()
        {
            List<string> list = new List<string>();
            string root = HotUpdatePaths.BuildRoot();
            if (!Directory.Exists(root))
            {
                return list;
            }
            foreach (string dir in Directory.GetDirectories(root))
            {
                string name = Path.GetFileName(dir);
                if (IsValid(name))
                {
                    list.Add(name);
                }
            }
            return list;
        }

        /// <summary>本机/服务器上的最大版本（没有则空串）。</summary>
        public static string GetMaxKnownVersion()
        {
            string best = "";
            foreach (string v in ListBuiltVersions())
            {
                if (best.Length == 0 || Compare(v, best) > 0)
                {
                    best = v;
                }
            }
            string deployed = GetDeployedVersion();
            if (IsValid(deployed) && (best.Length == 0 || Compare(deployed, best) > 0))
            {
                best = deployed;
            }
            string recorded = GetRecordedVersion();
            if (IsValid(recorded) && (best.Length == 0 || Compare(recorded, best) > 0))
            {
                best = recorded;
            }
            return best;
        }

        /// <summary>下一个要用的版本号（自动递增）。</summary>
        public static string Next()
        {
            string best = GetMaxKnownVersion();
            return best.Length == 0 ? "1.0.0" : Bump(best);
        }

        /// <summary>面板上显示的一行摘要（"本地最高 1.0.4 · 服务器 1.0.2 · 下一个 1.0.5"）。</summary>
        public static string Describe()
        {
            string deployed = GetDeployedVersion();
            string built = "";
            foreach (string v in ListBuiltVersions())
            {
                if (built.Length == 0 || Compare(v, built) > 0)
                {
                    built = v;
                }
            }
            return string.Format(
                "本地最高 {0} · 服务器 {1} · 下一个 {2}",
                built.Length == 0 ? "（无）" : built,
                deployed.Length == 0 ? "（无）" : deployed,
                Next());
        }
    }

    /// <summary>文件杂项（md5 / 大小 / 写文件 / 链接目录判定）。</summary>
    public static class HotUpdateFileUtil
    {
        /// <summary>流式计算 md5（32 位小写）。大 bundle 也不吃内存。</summary>
        public static string Md5(string path)
        {
            using (MD5 md5 = MD5.Create())
            using (FileStream stream = File.OpenRead(path))
            {
                byte[] hash = md5.ComputeHash(stream);
                StringBuilder sb = new StringBuilder(hash.Length * 2);
                for (int i = 0; i < hash.Length; i++)
                {
                    sb.Append(hash[i].ToString("x2"));
                }
                return sb.ToString();
            }
        }

        public static string FormatSize(long bytes)
        {
            if (bytes < 1024) return bytes + " B";
            if (bytes < 1024 * 1024) return (bytes / 1024f).ToString("F1") + " KB";
            if (bytes < 1024L * 1024 * 1024) return (bytes / 1024f / 1024f).ToString("F2") + " MB";
            return (bytes / 1024f / 1024f / 1024f).ToString("F2") + " GB";
        }

        public static void WriteText(string path, string text)
        {
            string dir = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(dir))
            {
                Directory.CreateDirectory(dir);
            }
            File.WriteAllText(path, text, new UTF8Encoding(false));
        }

        /// <summary>
        /// 目录是否是"链接/联接"（本项目 HotUpdateServer/Android/HybridCLR 是指向
        /// StreamingAssets/HybridCLR 的 junction）。往 junction 里拷 = 往源目录拷，
        /// 源和目标是同一批文件时会抛 IOException，必须先判定再跳过。
        /// 用 FileAttributes.ReparsePoint 判定（.NET Standard 2.1 没有 ResolveLinkTarget）。
        /// </summary>
        public static bool IsReparsePoint(string dir)
        {
            try
            {
                if (!Directory.Exists(dir))
                {
                    return false;
                }
                FileAttributes attr = File.GetAttributes(dir);
                return (attr & FileAttributes.ReparsePoint) == FileAttributes.ReparsePoint;
            }
            catch (Exception)
            {
                return false;
            }
        }

        /// <summary>
        /// 是否是 YooAsset 的"裸哈希特殊包"文件名（unitymonos / unityshaders）。
        /// 这两个包文件名 = 32 位小写哈希、**不带 .bundle**，漏拷会导致跨版本加载场景 404。
        /// </summary>
        public static bool IsBareHashFile(string fileName)
        {
            if (string.IsNullOrEmpty(fileName) || fileName.Length != 32)
            {
                return false;
            }
            for (int i = 0; i < fileName.Length; i++)
            {
                char c = fileName[i];
                bool hex = (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
                if (!hex)
                {
                    return false;
                }
            }
            return true;
        }

        /// <summary>递归删除目录（不存在时静默）。</summary>
        public static void DeleteDirectory(string dir)
        {
            try
            {
                if (Directory.Exists(dir))
                {
                    Directory.Delete(dir, true);
                }
            }
            catch (Exception)
            {
            }
        }
    }
}
