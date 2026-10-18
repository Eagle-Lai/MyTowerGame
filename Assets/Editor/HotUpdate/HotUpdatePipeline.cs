using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using HybridCLR.Editor.Commands;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

#if USE_YOOASSET
using YooAsset.Editor;
#endif

namespace FTProject.EditorTools
{
    /// <summary>
    /// 一键热更的运行日志：**同时**写 Console 与文件。
    ///
    /// 【为什么必须有文件】失败时人往往只看到"红了一片"，而 MCP / CI 会话结束后
    /// Console 也看不到了。落一份 Logs/HotUpdate/last_run.log，排查时直接看这个文件，
    /// 或者把它贴给同事。
    /// </summary>
    public static class HotUpdateLog
    {
        private static readonly object Sync = new object();

        public static string FilePath { get { return HotUpdatePaths.LogFile; } }

        /// <summary>开始一次运行：清空旧日志并写头。</summary>
        public static void Begin(string header)
        {
            try
            {
                string dir = Path.GetDirectoryName(HotUpdatePaths.LogFile);
                if (!string.IsNullOrEmpty(dir))
                {
                    Directory.CreateDirectory(dir);
                }
                File.WriteAllText(HotUpdatePaths.LogFile,
                    header + "\n============================================================\n",
                    new UTF8Encoding(false));
            }
            catch (Exception)
            {
                // 日志文件写不了不能影响主流程
            }
        }

        public static void Line(string message)
        {
            Append(message);
            Debug.Log("[HotUpdate] " + message);
        }

        public static void Warn(string message)
        {
            Append("[警告] " + message);
            Debug.LogWarning("[HotUpdate] " + message);
        }

        public static void Error(string message)
        {
            Append("[错误] " + message);
            Debug.LogError("[HotUpdate] " + message);
        }

        private static void Append(string message)
        {
            if (message == null)
            {
                return;
            }
            try
            {
                lock (Sync)
                {
                    string[] lines = message.Replace("\r\n", "\n").Split('\n');
                    StringBuilder sb = new StringBuilder();
                    for (int i = 0; i < lines.Length; i++)
                    {
                        sb.Append(DateTime.Now.ToString("HH:mm:ss.fff")).Append("  ").Append(lines[i]).Append('\n');
                    }
                    File.AppendAllText(HotUpdatePaths.LogFile, sb.ToString(), new UTF8Encoding(false));
                }
            }
            catch (Exception)
            {
            }
        }

        /// <summary>读日志尾部（面板显示用；只读不阻塞写）。</summary>
        public static string Tail(int maxChars)
        {
            try
            {
                if (!File.Exists(HotUpdatePaths.LogFile))
                {
                    return "";
                }
                using (FileStream fs = new FileStream(HotUpdatePaths.LogFile, FileMode.Open,
                           FileAccess.Read, FileShare.ReadWrite))
                {
                    long take = Math.Min(fs.Length, Math.Max(maxChars, 1024));
                    fs.Seek(-take, SeekOrigin.End);
                    byte[] buffer = new byte[take];
                    int read = fs.Read(buffer, 0, buffer.Length);
                    string text = Encoding.UTF8.GetString(buffer, 0, read);
                    // 从头截断可能落在多字节字符中间，丢掉第一行残片
                    int firstBreak = text.IndexOf('\n');
                    if (firstBreak >= 0 && text.Length > firstBreak + 1)
                    {
                        text = text.Substring(firstBreak + 1);
                    }
                    return text;
                }
            }
            catch (Exception e)
            {
                return "（读取日志失败：" + e.Message + "）";
            }
        }
    }

    /// <summary>
    /// **一键热更流水线**：重编热更 dll ▸ 同步 dll+md5 ▸ 构建 AB（版本自增） ▸ 生成清单
    /// ▸ 部署到本地资源服务器 ▸ 上传远端 ▸ 本地运行验证 ▸（可选）Play 冒烟。
    ///
    /// ==================================================================
    /// 【为什么又是状态机】HybridCLR `Generate/All` 会重写 `AOTGenericReferences.cs`，
    /// 触发脚本编译与域重载 —— 正在执行的方法栈会被直接杀掉。所以：
    ///   · 阶段游标存 SessionState（域重载后保留）；
    ///   · [InitializeOnLoad] 每次域重载后重新挂 Tick；
    ///   · 阶段**执行成功之后**才推进；被打断时下一轮原地重跑（幂等），
    ///     宁可多花几分钟，也绝不静默使用旧产物。
    ///   · 版本号在 Preflight 就定好并写进 SessionState：重跑不会二次自增。
    ///
    /// 【与已有菜单的关系】
    ///   · 菜单 7（BuildApkFull）：DLL ▸ AB ▸ APK，**不出热更服务器的部署**；
    ///   · 菜单 9（ReporterHotfixBuild）：DLL ▸ AB，部署要另开终端跑 python；
    ///   · 本流水线：DLL ▸ AB ▸ 清单 ▸ 部署 ▸ 上传 ▸ 本地验证，全在编辑器内完成，
    ///     但**不构建 APK**（热更不改包体）。
    ///   三者共用同一批底层实现（PrebuildCommand / HybridCLRDllCopier /
    ///   HybridCLRMd5Generator / FTYooAssetSetupWizard.BuildRealBundlesCore），
    ///   不存在"两套构建逻辑漂移"的问题。
    ///
    /// 【失败即中断】任一阶段失败 → 阶段置 Fail、写 DONE FAIL 到状态文件、
    ///   Console 红字 + 日志文件，并停掉还没走完的异步任务；不会带着半套产物继续。
    ///
    /// 【外部观测】
    ///   Library/FT_HotUpdateStatus.txt  逐行追加：START / PHASE xxx ok / DONE OK|FAIL
    ///   Logs/HotUpdate/last_run.log     完整日志
    /// ==================================================================
    /// </summary>
    [InitializeOnLoad]
    public static class HotUpdatePipeline
    {
        // ------------------------------------------------------------------
        // SessionState 键（域重载后必须保留的东西）
        // ------------------------------------------------------------------

        private const string PhaseKey = "FT.Hot.Update.Phase";
        private const string OptionsKey = "FT.Hot.Update.Options";
        private const string VersionKey = "FT.Hot.Update.Version";
        private const string PlanFromCdnKey = "FT.Hot.Update.PlanFromCdn";
        private const string FailPhaseKey = "FT.Hot.Update.FailPhase";
        private const string LastErrorKey = "FT.Hot.Update.LastError";
        private const string StartedKey = "FT.Hot.Update.StartedAt";
        private const string PlayEnterKey = "FT.Hot.Update.PlayEnter";
        private const string PlayStartKey = "FT.Hot.Update.PlayStart";
        private const string PlayErrorsKey = "FT.Hot.Update.PlayErrors";
        private const string PlayIgnoredKey = "FT.Hot.Update.PlayIgnored";
        private const string FileCountKey = "FT.Hot.Update.FileCount";

        /// <summary>
        /// Play 冒烟时**不计入**错误的日志片段（编辑器环境噪音，与游戏无关）。
        ///
        /// 【为什么要有】本机每次进 Play 都会抛
        /// `CommandInvokationFailure: Unity Remote requirements check failed`
        /// （Unity Remote 的 Android 设备检查，和热更/游戏逻辑无关）。
        /// 不过滤的话，冒烟永远"有 1 条错误"，这个检查就失去意义了。
        /// 新发现的环境噪音按同样格式追加，并在日志里显式说明"已忽略 N 条"。
        /// </summary>
        private static readonly string[] PlayLogIgnorePatterns =
        {
            "Unity Remote requirements check failed",
        };

        /// <summary>阶段顺序（面板按这个顺序画步骤条，进度也按它算）。</summary>
        public static readonly string[] Phases =
        {
            "Preflight",
            "DllGenerate",
            "DllCopy",
            "AbBuild",
            "Manifest",
            "DeployLocal",
            "UploadRemote",
            "Verify",
            "PlaySmokeStart",
            "PlaySmokeWait",
            "Finish",
            "Done",
        };

        /// <summary>每个阶段在面板上显示的中文名（与 Phases 一一对应）。</summary>
        public static readonly string[] PhaseTitles =
        {
            "预检（平台 / 版本 / 环境）",
            "重新编译热更 DLL（HybridCLR Generate/All）",
            "同步 dll + 生成 md5 清单",
            "构建 AB 资源包（版本自增）",
            "生成热更清单 / 构建记录",
            "部署到本地资源服务器",
            "上传到远端资源服务器",
            "本地运行验证（文件 + HTTP 链路）",
            "进入 Play 冒烟",
            "Play 冒烟观察（8 秒）",
            "收尾",
            "完成",
        };

        // ------------------------------------------------------------------
        // 运行期状态（域重载会丢，可丢的都放这里；要紧的都在 SessionState）
        // ------------------------------------------------------------------

        private static HotUpdatePlan _plan;
        private static Task _verifyTask;
        private static Task _uploadTask;
        private static HotUpdateVerifyResult _verifyResult;
        private static volatile string _verifyError;
        private static volatile bool _uploadOk;
        private static volatile string _uploadError;
        private static volatile int _jobDone;
        private static volatile int _jobTotal;
        private static bool _serverStartedByPipeline;

        private static readonly string MainScenePath = "Assets/Scenes/Main.unity";

        // ------------------------------------------------------------------
        // 对外状态（面板/菜单/MCP 只读）
        // ------------------------------------------------------------------

        public static string CurrentPhase { get { return GetPhase(); } }

        public static bool IsRunning
        {
            get
            {
                string phase = GetPhase();
                return phase != "Idle" && phase != "Done" && phase != "Fail";
            }
        }

        public static string CurrentVersion { get { return SessionState.GetString(VersionKey, ""); } }

        public static string LastError { get { return SessionState.GetString(LastErrorKey, ""); } }

        public static string StartedAt { get { return SessionState.GetString(StartedKey, ""); } }

        public static HotUpdateOptions Options { get { return GetOptions(); } }

        public static bool LocalServerRunning { get { return HotUpdateLocalServer.IsRunning; } }

        /// <summary>当前阶段下标（失败时返回失败所在阶段，便于面板标红）。</summary>
        public static int StepIndex
        {
            get
            {
                string phase = GetPhase();
                if (phase == "Fail")
                {
                    phase = SessionState.GetString(FailPhaseKey, "Preflight");
                }
                int index = Array.IndexOf(Phases, phase);
                return index < 0 ? 0 : index;
            }
        }

        /// <summary>0..1 的总体进度。</summary>
        public static float Progress01
        {
            get
            {
                if (GetPhase() == "Done")
                {
                    return 1f;
                }

                // 仅验证模式跳过了前 7 个构建阶段：进度从 Verify 起算，
                // 否则一进来就显示 63%，看起来像"已经快跑完了"。
                int start = 0;
                if (GetOptions().verifyOnly)
                {
                    start = Array.IndexOf(Phases, "Verify");
                }
                int last = Phases.Length - 1;
                int index = Mathf.Max(StepIndex, start);
                int span = last - start;
                return span <= 0 ? 0f : Mathf.Clamp01((float)(index - start) / span);
            }
        }

        /// <summary>异步任务（上传 / HTTP 校验）的进度文本。</summary>
        public static string JobText
        {
            get
            {
                if (string.IsNullOrEmpty(CurrentPhase))
                {
                    return "";
                }
                int done = _jobDone;
                int total = _jobTotal;
                if (total <= 0)
                {
                    return "";
                }
                if (_uploadTask != null)
                {
                    return string.Format("上传 {0}/{1}", done, total);
                }
                if (_verifyTask != null)
                {
                    return string.Format("校验 {0}/{1}", done, total);
                }
                return "";
            }
        }

        public static float JobProgress01
        {
            get { return _jobTotal <= 0 ? 0f : Mathf.Clamp01((float)_jobDone / _jobTotal); }
        }

        // ------------------------------------------------------------------
        // 启动 / 取消
        // ------------------------------------------------------------------

        static HotUpdatePipeline()
        {
            EditorApplication.update += Tick;
            Application.logMessageReceived += OnLogMessage;
        }

        /// <summary>完整流水线（菜单 / 面板按钮）。</summary>
        public static void StartFull()
        {
            string reason;
            if (!CanStart(out reason))
            {
                Debug.LogError("[HotUpdate] 无法开始：" + reason);
                return;
            }
            HotUpdateOptions options = HotUpdateOptions.FromSettings(false);
            Begin(options);
        }

        /// <summary>只做本地验证（不构建、不部署）：验证服务器上"现在这一版"完不完整。</summary>
        public static void StartVerifyOnly()
        {
            string reason;
            if (!CanStart(out reason))
            {
                Debug.LogError("[HotUpdate] 无法开始：" + reason);
                return;
            }
            HotUpdateOptions options = HotUpdateOptions.FromSettings(true);
            options.verify = true;
            Begin(options);
        }

        private static bool CanStart(out string reason)
        {
            reason = null;
            if (IsRunning)
            {
                reason = "已有热更流水线在跑（阶段 " + CurrentPhase + "），请等它结束或先取消。";
                return false;
            }
            if (EditorApplication.isPlaying)
            {
                reason = "编辑器处于 Play 模式，请先退出。";
                return false;
            }
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                reason = "编辑器正在编译 / 导入资源，请等空闲后再试。";
                return false;
            }
            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.Android)
            {
                reason = "当前构建目标是 " + EditorUserBuildSettings.activeBuildTarget +
                         "，热更 dll / AB 会打到错误平台。请先切到 Android。";
                return false;
            }
            if (OtherPipelineBusy())
            {
                reason = "另一条构建流水线正在运行（菜单 7 / 9）。两者同时跑会互相踩产物，请等它结束。";
                return false;
            }
            return true;
        }

        /// <summary>
        /// 检查菜单 7 / 9 的流水线是否在跑。
        /// 【为什么读字符串而不是引用】那两个类的阶段键是 private const，
        /// 这里按**约定好的键名**读取 SessionState —— 只读、无编译依赖，键名变更时
        /// 最坏情况是漏检（不会编译失败）。
        /// </summary>
        private static bool OtherPipelineBusy()
        {
            string reporter = SessionState.GetString("FTReporterBuild.Phase", "Idle");
            string full = SessionState.GetString("FTBuildApkFull.Phase", "Idle");
            return IsBusyPhase(reporter) || IsBusyPhase(full);
        }

        private static bool IsBusyPhase(string phase)
        {
            return !string.IsNullOrEmpty(phase)
                && phase != "Idle" && phase != "Done" && phase != "Fail";
        }

        private static void Begin(HotUpdateOptions options)
        {
            _plan = null;
            _verifyTask = null;
            _uploadTask = null;
            _verifyResult = null;
            _verifyError = null;
            _uploadError = null;
            _jobDone = 0;
            _jobTotal = 0;
            _serverStartedByPipeline = false;

            SessionState.SetString(OptionsKey, JsonUtility.ToJson(options));
            SessionState.SetString(VersionKey, options.verifyOnly ? "" : (options.versionOverride ?? ""));
            SessionState.SetString(LastErrorKey, "");
            SessionState.SetString(FailPhaseKey, "");
            SessionState.SetString(StartedKey, DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
            SessionState.SetString(PlayEnterKey, "");
            SessionState.SetString(PlayStartKey, "");
            SessionState.SetInt(PlayErrorsKey, 0);
            SessionState.SetInt(PlayIgnoredKey, 0);
            SessionState.SetInt(FileCountKey, 0);
            SessionState.SetBool(PlanFromCdnKey, options.verifyOnly);

            HotUpdateLog.Begin(string.Format(
                "一键热更 {0}\n工程：{1}\n平台：{2}\n模式：{3}",
                DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"),
                HotUpdatePaths.ProjectRoot,
                HotUpdatePaths.PlatformFolder,
                options.verifyOnly ? "仅本地验证" : "完整（dll ▸ AB ▸ 部署 ▸ 验证）"));

            WriteStatus("START " + (options.verifyOnly ? "VERIFY-ONLY " : "HOTUPDATE ") +
                        DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));

            if (options.verifyOnly)
            {
                HotUpdateLog.Line("模式：仅本地验证（不重编 dll、不构建 AB、不改部署）");
                SetPhase("Verify");
            }
            else
            {
                HotUpdateLog.Line("模式：完整热更（本地部署=" + (options.local ? "开" : "关") +
                                  "，远端上传=" + (options.remote ? "开" : "关") +
                                  "，本地验证=" + (options.verify ? "开" : "关") +
                                  "，Play 冒烟=" + (options.play ? "开" : "关") + "）");
                SetPhase("Preflight");
            }
        }

        /// <summary>中断当前流水线（异步任务无法强杀，只能停在本帧之后不再推进）。</summary>
        public static void Cancel()
        {
            if (!IsRunning)
            {
                return;
            }
            Fail("已取消（用户中断，阶段：" + CurrentPhase + "）");
        }

        // ------------------------------------------------------------------
        // Tick 驱动
        // ------------------------------------------------------------------

        private static void Tick()
        {
            string phase = GetPhase();
            if (phase == "Idle" || phase == "Done" || phase == "Fail")
            {
                return;
            }
            // 编译 / 导入期间一律等待（空闲后自动继续）
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                return;
            }

            try
            {
                switch (phase)
                {
                    case "Preflight": TickPreflight(); break;
                    case "DllGenerate": TickDllGenerate(); break;
                    case "DllCopy": TickDllCopy(); break;
                    case "AbBuild": TickAbBuild(); break;
                    case "Manifest": TickManifest(); break;
                    case "DeployLocal": TickDeployLocal(); break;
                    case "UploadRemote": TickUploadRemote(); break;
                    case "Verify": TickVerify(); break;
                    case "PlaySmokeStart": TickPlaySmokeStart(); break;
                    case "PlaySmokeWait": TickPlaySmokeWait(); break;
                    case "Finish": TickFinish(); break;
                }
            }
            catch (Exception e)
            {
                Fail(phase + " 阶段异常：\n" + e);
            }
        }

        // ------------------------------------------------------------------
        // ① 预检
        // ------------------------------------------------------------------

        private static void TickPreflight()
        {
            HotUpdateLog.Line("① 预检：平台 / 版本 / 环境");

            if (EditorApplication.isPlaying)
            {
                Fail("编辑器处于 Play 模式，请先退出。");
                return;
            }
            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.Android)
            {
                Fail("当前构建目标是 " + EditorUserBuildSettings.activeBuildTarget +
                     "，热更 dll / AB 会打到错误平台。请先切到 Android。");
                return;
            }

#if !USE_YOOASSET
            Fail("当前平台未启用 USE_YOOASSET 宏，AB 热更链路依赖它。\n" +
                 "请先执行「Tools ▸ 塔防 ▸ YooAsset 接入 ▸ 1. 启用 USE_YOOASSET 宏」。");
            return;
#else
            if (BundleCollectorSettingData.HasSettingAsset() == false)
            {
                Fail("还没有 YooAsset 收集器配置资产，请先执行「YooAsset 接入 → 接入向导 → ① 生成 / 修复收集器配置」。");
                return;
            }
#endif

            string version;
            string overrideVersion = (GetOptions().versionOverride ?? "").Trim();
            if (overrideVersion.Length > 0)
            {
                if (!HotUpdateVersionUtil.IsValid(overrideVersion))
                {
                    Fail("手动指定的版本号格式不对（要 x.y.z）：" + overrideVersion);
                    return;
                }
                version = overrideVersion;
                HotUpdateLog.Line("版本号：手动指定 " + version);
            }
            else
            {
                version = HotUpdateVersionUtil.Next();
                HotUpdateLog.Line("版本号：自动递增 → " + version + "（" + HotUpdateVersionUtil.Describe() + "）");
            }

            if (!HotUpdateVersionUtil.IsValid(version))
            {
                Fail("版本号解析失败：" + version);
                return;
            }

            SessionState.SetString(VersionKey, version);

            string buildDir = HotUpdatePaths.BuildDir(version);
            if (Directory.Exists(buildDir))
            {
                HotUpdateLog.Warn("版本目录已存在，将先清理再构建：" + buildDir);
            }

            HotUpdateLog.Line("随包 dll 目录：" + HotUpdatePaths.DllDir);
            HotUpdateLog.Line("AB 输出目录：" + buildDir);
            HotUpdateLog.Line("本地服务器根：" + HotUpdatePaths.CdnRoot);
            if (GetOptions().remote)
            {
                HotUpdateLog.Line("远端上传：" + GetOptions().remoteUrl);
            }

            Advance("DllGenerate");
        }

        // ------------------------------------------------------------------
        // ② HybridCLR Generate/All
        // ------------------------------------------------------------------

        private static void TickDllGenerate()
        {
            HotUpdateLog.Line("② 重新编译热更 DLL（HybridCLR Generate/All）…");
            // 直接调包内 API（与菜单「HybridCLR/Generate/All」同一实现），
            // 不依赖 batchmode 下菜单系统的可用性。
            PrebuildCommand.GenerateAll();
            AssetDatabase.Refresh();
            HotUpdateLog.Line("Generate/All 完成（若中途触发域重载，本阶段会重跑一次，产物幂等）。");
            Advance("DllCopy");
        }

        // ------------------------------------------------------------------
        // ③ 拷贝 dll + md5
        // ------------------------------------------------------------------

        private static void TickDllCopy()
        {
            HotUpdateLog.Line("③ 同步热更 dll 到 StreamingAssets + 生成 md5 清单 …");

            EditorUtil.Report copyReport = new EditorUtil.Report();
            HybridCLRDllCopier.Copy(copyReport);
            if (copyReport.Errors > 0)
            {
                Fail("同步热更 dll 失败：\n" + copyReport.Text);
                return;
            }

            EditorUtil.Report md5Report = new EditorUtil.Report();
            HybridCLRMd5Generator.Generate(md5Report);
            if (md5Report.Errors > 0)
            {
                Fail("生成 dll md5 清单失败：\n" + md5Report.Text);
                return;
            }

            AssetDatabase.Refresh();
            HotUpdateLog.Line(copyReport.Text);
            HotUpdateLog.Line(md5Report.Text);
            Advance("AbBuild");
        }

        // ------------------------------------------------------------------
        // ④ 构建 AB
        // ------------------------------------------------------------------

        private static void TickAbBuild()
        {
            string version = CurrentVersion;
            string buildDir = HotUpdatePaths.BuildDir(version);
            HotUpdateLog.Line("④ 构建 AB 资源包 v" + version + " …");

#if USE_YOOASSET
            EditorUtil.Report report = new EditorUtil.Report();
            bool ok = FTYooAssetSetupWizard.BuildRealBundlesCore(version, GetOptions().fullRebuild, report);
            if (!ok)
            {
                Fail("AB 构建失败：\n" + report.Text);
                return;
            }
            HotUpdateLog.Line(report.Text);

            // 产物自检：客户端真正依赖的三个入口文件必须存在
            string versionFile = Path.Combine(buildDir, HotUpdatePaths.VersionFileName);
            string hashFile = Path.Combine(buildDir, "FreeTower_" + version + ".hash");
            string bytesFile = Path.Combine(buildDir, "FreeTower_" + version + ".bytes");
            List<string> missing = new List<string>();
            if (!File.Exists(versionFile)) missing.Add(HotUpdatePaths.VersionFileName);
            if (!File.Exists(hashFile)) missing.Add(Path.GetFileName(hashFile));
            if (!File.Exists(bytesFile)) missing.Add(Path.GetFileName(bytesFile));
            if (missing.Count > 0)
            {
                Fail("AB 构建后缺少关键产物：" + string.Join("、", missing.ToArray()) + "\n目录：" + buildDir);
                return;
            }

            string builtVersion = File.ReadAllText(versionFile).Trim();
            if (builtVersion != version)
            {
                Fail(string.Format("AB 产物里的版本号是 {0}，与目标 {1} 不一致（构建参数没生效？）",
                    builtVersion, version));
                return;
            }

            HotUpdateLog.Line("AB 构建完成：" + buildDir);
            Advance("Manifest");
#else
            Fail("当前平台未启用 USE_YOOASSET 宏，无法构建 YooAsset 资源包。");
#endif
        }

        // ------------------------------------------------------------------
        // ⑤ 生成清单
        // ------------------------------------------------------------------

        private static void TickManifest()
        {
            HotUpdateLog.Line("⑤ 生成热更清单（AB + dll）…");
            HotUpdatePlan plan = EnsurePlan();
            if (plan == null)
            {
                return;
            }

            HotUpdateLog.Line(plan.Describe());
            SessionState.SetInt(FileCountKey, plan.Files.Count);

            // 把清单写进本机历史（部署阶段会再拷一份到服务器根）
            string historyDir = Path.Combine(HotUpdatePaths.StateDir, "history");
            Directory.CreateDirectory(historyDir);
            EditorUtil.Report report = new EditorUtil.Report();
            string manifestPath = Path.Combine(historyDir, plan.Version + ".json");
            if (!HotUpdateDeployer.WriteManifest(plan, manifestPath, "构建完成（尚未部署）", report))
            {
                Fail("写热更清单失败：\n" + report.Text);
                return;
            }

            HotUpdateLog.Line(report.Text);
            Advance("DeployLocal");
        }

        // ------------------------------------------------------------------
        // ⑥ 本地部署
        // ------------------------------------------------------------------

        private static void TickDeployLocal()
        {
            HotUpdateOptions options = GetOptions();
            if (!options.local)
            {
                HotUpdateLog.Line("⑥ 跳过本地部署（未启用）。");
                Advance("UploadRemote");
                return;
            }

            HotUpdateLog.Line("⑥ 部署到本地资源服务器：" + HotUpdatePaths.CdnRoot);
            HotUpdatePlan plan = EnsurePlan();
            if (plan == null)
            {
                return;
            }

            EditorUtil.Report report = new EditorUtil.Report();
            if (!HotUpdateDeployer.DeployLocal(plan, HotUpdatePaths.CdnRoot, report))
            {
                Fail("本地部署失败：\n" + report.Text);
                return;
            }

            HotUpdateLog.Line(report.Text);
            Advance("UploadRemote");
        }

        // ------------------------------------------------------------------
        // ⑦ 远端上传（后台线程）
        // ------------------------------------------------------------------

        private static void TickUploadRemote()
        {
            if (_uploadTask != null)
            {
                PollUpload();
                return;
            }

            HotUpdateOptions options = GetOptions();
            if (!options.remote)
            {
                HotUpdateLog.Line("⑦ 跳过远端上传（未启用）。");
                Advance("Verify");
                return;
            }
            if (string.IsNullOrEmpty(options.remoteUrl))
            {
                Fail("已勾选远端上传，但远端根地址为空。请回到面板填写（例如 https://cdn.example.com/freedomtower）。");
                return;
            }

            HotUpdatePlan plan = EnsurePlan();
            if (plan == null)
            {
                return;
            }

            HotUpdateLog.Line("⑦ 上传到远端：" + options.remoteUrl + "（共 " + (plan.Files.Count + 1) + " 个文件）");

            _jobDone = 0;
            _jobTotal = plan.Files.Count + 1;
            _uploadOk = false;
            _uploadError = null;

            string baseUrl = options.remoteUrl;
            string header = options.remoteHeader;
            _uploadTask = Task.Run(() =>
            {
                string error;
                bool ok = HotUpdateDeployer.UploadAll(plan, baseUrl, header,
                    (done, total) =>
                    {
                        _jobDone = done;
                        _jobTotal = total;
                    }, out error);
                _uploadOk = ok;
                _uploadError = error;
            });
        }

        private static void PollUpload()
        {
            if (!_uploadTask.IsCompleted)
            {
                return;
            }
            Exception exception = _uploadTask.Exception;
            _uploadTask = null;
            _jobDone = 0;
            _jobTotal = 0;

            if (exception != null)
            {
                Fail("远端上传异常：" + exception.GetBaseException().Message);
                return;
            }
            if (!_uploadOk)
            {
                Fail("远端上传失败：" + (_uploadError ?? "未知错误"));
                return;
            }

            HotUpdateLog.Line("远端上传完成。");
            Advance("Verify");
        }

        // ------------------------------------------------------------------
        // ⑧ 本地运行验证（文件 + HTTP 链路）
        // ------------------------------------------------------------------

        private static void TickVerify()
        {
            if (_verifyTask != null)
            {
                PollVerify();
                return;
            }

            HotUpdateOptions options = GetOptions();
            if (!options.verify)
            {
                HotUpdateLog.Line("⑧ 跳过本地验证（未启用）。");
                Advance("PlaySmokeStart");
                return;
            }

            HotUpdatePlan plan = EnsurePlan();
            if (plan == null)
            {
                return;
            }

            HotUpdateLog.Line("⑧ 本地运行验证：文件完整性 + HTTP 链路 …");

            HotUpdateVerifyResult result = new HotUpdateVerifyResult();
            HotUpdateDeployer.VerifyLocalFiles(plan, HotUpdatePaths.CdnRoot, options.local, result);

            string baseUrl = null;
            if (options.local)
            {
                string error;
                bool startedNow;
                if (HotUpdateLocalServer.Start(HotUpdatePaths.CdnRoot, HotUpdateSettings.VerifyPort,
                        out startedNow, out error))
                {
                    baseUrl = HotUpdateLocalServer.Url;
                    // 只停"自己起的"服务：用户可能正用菜单 10c 起的服务在真机联调
                    _serverStartedByPipeline = startedNow;
                    if (startedNow)
                    {
                        HotUpdateLog.Line("本地静态服务器：" + baseUrl + " → " + HotUpdatePaths.CdnRoot);
                    }
                    else
                    {
                        HotUpdateLog.Line("复用已在运行的本地静态服务器：" + baseUrl);
                    }
                }
                else
                {
                    // 端口被占用：可能已经开着官方 python 服务器（或别的工程）。
                    // 能读到版本号就复用它，读不到就只做文件级检查。
                    string existingUrl = "http://127.0.0.1:" + HotUpdateSettings.VerifyPort;
                    string existingVersion;
                    string probeError;
                    if (HotUpdateDeployer.TryGetRemoteVersion(existingUrl, out existingVersion, out probeError))
                    {
                        baseUrl = existingUrl;
                        result.Warnings.Add(string.Format(
                            "端口 {0} 已被占用，复用已有服务做校验（其上版本 {1}）", HotUpdateSettings.VerifyPort, existingVersion));
                        if (existingVersion != plan.Version)
                        {
                            result.Warnings.Add(string.Format(
                                "已有服务上的版本 {0} 与本次 {1} 不一致：它服务的可能不是当前部署目录。",
                                existingVersion, plan.Version));
                        }
                    }
                    else
                    {
                        result.Warnings.Add("本地静态服务器启动失败，且无可复用的服务：" + error);
                    }
                }
            }
            else if (options.remote && !string.IsNullOrEmpty(options.remoteUrl))
            {
                baseUrl = options.remoteUrl.TrimEnd('/');
                HotUpdateLog.Line("验证远端地址：" + baseUrl);
            }

            if (result.Failures.Count > 0)
            {
                Fail("本地校验未通过（文件级）：\n" + result.Describe());
                return;
            }

            if (string.IsNullOrEmpty(baseUrl))
            {
                result.Warnings.Add("没有可用的 HTTP 服务，本次只做了文件级校验。");
                HotUpdateLog.Warn(result.Describe());
                Advance("PlaySmokeStart");
                return;
            }

            _jobDone = 0;
            _jobTotal = plan.Files.Count + 1;
            _verifyResult = result;
            _verifyError = null;

            string url = baseUrl;
            _verifyTask = Task.Run(() =>
            {
                try
                {
                    HotUpdateDeployer.VerifyHttp(plan, url,
                        (done, total) =>
                        {
                            _jobDone = done;
                            _jobTotal = total;
                        }, result);
                }
                catch (Exception e)
                {
                    _verifyError = e.Message;
                }
            });
        }

        private static void PollVerify()
        {
            if (!_verifyTask.IsCompleted)
            {
                return;
            }
            Exception exception = _verifyTask.Exception;
            _verifyTask = null;
            _jobDone = 0;
            _jobTotal = 0;
            HotUpdateVerifyResult result = _verifyResult;
            _verifyResult = null;

            if (exception != null)
            {
                Fail("HTTP 校验异常：" + exception.GetBaseException().Message);
                return;
            }
            if (!string.IsNullOrEmpty(_verifyError))
            {
                Fail("HTTP 校验异常：" + _verifyError);
                return;
            }
            if (result == null)
            {
                Fail("HTTP 校验结果丢失。");
                return;
            }

            HotUpdateLog.Line(result.Describe());
            if (!result.Ok)
            {
                Fail("本地运行验证未通过：\n" + result.Describe());
                return;
            }

            Advance("PlaySmokeStart");
        }

        // ------------------------------------------------------------------
        // ⑨ Play 冒烟（可选）：进 Main 场景跑 8 秒，统计错误日志
        // ------------------------------------------------------------------

        private static void TickPlaySmokeStart()
        {
            HotUpdateOptions options = GetOptions();
            if (!options.play)
            {
                HotUpdateLog.Line("⑨ 跳过 Play 冒烟（未启用）。");
                Advance("Finish");
                return;
            }
            if (EditorApplication.isPlaying)
            {
                HotUpdateLog.Line("⑨ 已在 Play 模式，跳过自动冒烟。");
                Advance("Finish");
                return;
            }

            // 不替用户保存场景：有未保存改动就跳过，避免"自动保存/丢弃"这种不可逆操作。
            // 注意要检查**所有已加载场景**（可能开了 additive），只看 active 会漏。
            for (int i = 0; i < EditorSceneManager.sceneCount; i++)
            {
                UnityEngine.SceneManagement.Scene scene = EditorSceneManager.GetSceneAt(i);
                if (scene.isDirty)
                {
                    HotUpdateLog.Warn("场景「" + scene.name +
                        "」有未保存修改，跳过 Play 冒烟（避免丢失改动）。保存后可单独进 Play 验证。");
                    Advance("Finish");
                    return;
                }
            }

            string sceneFull = HotUpdatePaths.Resolve(MainScenePath);
            if (!File.Exists(sceneFull))
            {
                HotUpdateLog.Warn("找不到 Main 场景（" + MainScenePath + "），跳过 Play 冒烟。");
                Advance("Finish");
                return;
            }

            SessionState.SetInt(PlayErrorsKey, 0);
            SessionState.SetInt(PlayIgnoredKey, 0);
            SessionState.SetString(PlayEnterKey, NowSeconds().ToString("R", CultureInfo.InvariantCulture));
            SessionState.SetString(PlayStartKey, "");

            EditorSceneManager.OpenScene(MainScenePath, OpenSceneMode.Single);

            // 先推进阶段再进 Play：进 Play 会触发域重载，方法栈会被杀掉
            SetPhase("PlaySmokeWait");
            HotUpdateLog.Line("⑨ 进入 Play（Main 场景），观察 8 秒 …");
            EditorApplication.isPlaying = true;
        }

        private static void TickPlaySmokeWait()
        {
            double now = NowSeconds();
            if (!EditorApplication.isPlaying)
            {
                double enter = ParseSeconds(SessionState.GetString(PlayEnterKey, ""));
                if (enter > 0 && now - enter > 20)
                {
                    HotUpdateLog.Warn("20 秒内没有进入 Play（可能存在编译错误），跳过冒烟。");
                    Advance("Finish");
                }
                return;
            }

            double start = ParseSeconds(SessionState.GetString(PlayStartKey, ""));
            if (start <= 0)
            {
                SessionState.SetString(PlayStartKey, now.ToString("R", CultureInfo.InvariantCulture));
                return;
            }
            if (now - start < 8)
            {
                return;
            }

            int errors = SessionState.GetInt(PlayErrorsKey, 0);
            int ignored = SessionState.GetInt(PlayIgnoredKey, 0);
            EditorApplication.isPlaying = false;

            if (errors > 0)
            {
                HotUpdateLog.Warn(string.Format(
                    "Play 冒烟：8 秒内出现 {0} 条错误/异常日志（详见 Console；这不一定阻断热更，但上线前应清掉）。", errors));
            }
            else
            {
                HotUpdateLog.Line("Play 冒烟通过（8 秒内无错误/异常日志）"
                    + (ignored > 0 ? string.Format("；已忽略 {0} 条编辑器环境噪音", ignored) : "") + "。");
            }
            Advance("Finish");
        }

        // ------------------------------------------------------------------
        // ⑩ 收尾
        // ------------------------------------------------------------------

        private static void TickFinish()
        {
            string version = CurrentVersion;
            string started = StartedAt;
            double cost = 0;
            DateTime startTime;
            if (DateTime.TryParse(started, out startTime))
            {
                cost = (DateTime.Now - startTime).TotalSeconds;
            }

            SetPhase("Done");
            WriteStatus("DONE OK version=" + version + (cost > 0 ? string.Format(" cost={0:F0}s", cost) : ""));

            HotUpdateLog.Line(string.Format(
                "✔ 一键热更完成：v{0} · {1} 个文件 · 耗时 {2:F0}s\n  服务器根：{3}\n  日志：{4}",
                version,
                _plan != null ? _plan.Files.Count : SessionState.GetInt(FileCountKey, 0),
                cost,
                HotUpdatePaths.CdnRoot,
                HotUpdatePaths.LogFile));

            StopServerIfStartedByPipeline();
            _plan = null;
            _jobDone = 0;
            _jobTotal = 0;
        }

        // ------------------------------------------------------------------
        // 失败 / 状态
        // ------------------------------------------------------------------

        private static void Fail(string message)
        {
            string phase = GetPhase();
            SessionState.SetString(FailPhaseKey, phase);
            SessionState.SetString(LastErrorKey, message);
            SetPhase("Fail");

            HotUpdateLog.Error("✘ 流水线中断（阶段：" + phase + "）：\n" + message);
            WriteStatus("DONE FAIL " + OneLine(message));

            _plan = null;
            _verifyTask = null;
            _uploadTask = null;
            _verifyResult = null;
            _jobDone = 0;
            _jobTotal = 0;
            StopServerIfStartedByPipeline();
        }

        private static void StopServerIfStartedByPipeline()
        {
            if (_serverStartedByPipeline)
            {
                HotUpdateLocalServer.Stop();
                _serverStartedByPipeline = false;
            }
        }

        private static string OneLine(string message)
        {
            if (string.IsNullOrEmpty(message))
            {
                return "";
            }
            string one = message.Replace("\r", " ").Replace("\n", " ");
            if (one.Length > 180)
            {
                one = one.Substring(0, 180);
            }
            return one;
        }

        private static void WriteStatus(string line)
        {
            try
            {
                File.AppendAllText(HotUpdatePaths.StatusFile,
                    DateTime.Now.ToString("HH:mm:ss") + " " + line + "\n", new UTF8Encoding(false));
            }
            catch (Exception e)
            {
                Debug.LogWarning("[HotUpdate] 状态文件写入失败：" + e.Message);
            }
        }

        private static void Advance(string nextPhase)
        {
            WriteStatus("PHASE " + GetPhase() + " ok");
            SetPhase(nextPhase);
        }

        private static string GetPhase()
        {
            return SessionState.GetString(PhaseKey, "Idle");
        }

        private static void SetPhase(string phase)
        {
            SessionState.SetString(PhaseKey, phase);
        }

        private static HotUpdateOptions GetOptions()
        {
            string json = SessionState.GetString(OptionsKey, "");
            if (!string.IsNullOrEmpty(json))
            {
                try
                {
                    HotUpdateOptions options = JsonUtility.FromJson<HotUpdateOptions>(json);
                    if (options != null)
                    {
                        return options;
                    }
                }
                catch (Exception)
                {
                }
            }
            return HotUpdateOptions.FromSettings(false);
        }

        private static bool IsPlanFromCdn()
        {
            return SessionState.GetBool(PlanFromCdnKey, false);
        }

        /// <summary>
        /// 惰性构建清单：域重载后 static 字段会丢，这里按阶段语义重新算一次
        /// （只读磁盘 + 算 md5，幂等）。
        /// </summary>
        private static HotUpdatePlan EnsurePlan()
        {
            if (_plan != null)
            {
                return _plan;
            }

            EditorUtil.Report report = new EditorUtil.Report();
            string version = CurrentVersion;
            if (IsPlanFromCdn())
            {
                if (string.IsNullOrEmpty(version))
                {
                    version = HotUpdateVersionUtil.GetDeployedVersion();
                    // 仅验证模式开始时不写版本（那时还不知道要验哪一版）；
                    // 这里定下来后补写，保证后续状态文件 / 日志 / 面板都能显示版本号。
                    SessionState.SetString(VersionKey, version);
                }
                _plan = HotUpdateDeployer.BuildPlanFromCdn(version, HotUpdatePaths.CdnRoot,
                    HotUpdatePaths.DllDir, HotUpdatePaths.PlatformFolder, report);
            }
            else
            {
                _plan = HotUpdateDeployer.BuildPlan(version, HotUpdatePaths.BuildDir(version),
                    HotUpdatePaths.DllDir, HotUpdatePaths.PlatformFolder, report);
            }

            if (report.Errors > 0)
            {
                _plan = null;
                Fail("生成热更清单失败：\n" + report.Text);
                return null;
            }

            HotUpdateLog.Line(report.Text);
            return _plan;
        }

        // ------------------------------------------------------------------
        // Play 冒烟的错误统计 / 时间工具
        // ------------------------------------------------------------------

        private static void OnLogMessage(string condition, string stackTrace, LogType type)
        {
            if (GetPhase() != "PlaySmokeWait")
            {
                return;
            }
            if (type != LogType.Error && type != LogType.Exception && type != LogType.Assert)
            {
                return;
            }
            // 本流水线自己的日志不计入（否则"跳过/警告"会把自己判成失败）
            if (!string.IsNullOrEmpty(condition) && condition.StartsWith("[HotUpdate]", StringComparison.Ordinal))
            {
                return;
            }
            // 编辑器环境噪音（Unity Remote 设备检查等）：单独计数，不算冒烟失败
            if (!string.IsNullOrEmpty(condition))
            {
                for (int i = 0; i < PlayLogIgnorePatterns.Length; i++)
                {
                    if (condition.IndexOf(PlayLogIgnorePatterns[i], StringComparison.OrdinalIgnoreCase) >= 0)
                    {
                        SessionState.SetInt(PlayIgnoredKey, SessionState.GetInt(PlayIgnoredKey, 0) + 1);
                        return;
                    }
                }
            }
            SessionState.SetInt(PlayErrorsKey, SessionState.GetInt(PlayErrorsKey, 0) + 1);
        }

        private static double NowSeconds()
        {
            return DateTime.UtcNow.Ticks / (double)TimeSpan.TicksPerSecond;
        }

        private static double ParseSeconds(string text)
        {
            double value;
            if (double.TryParse(text, NumberStyles.Float, CultureInfo.InvariantCulture, out value))
            {
                return value;
            }
            return 0;
        }
    }
}
