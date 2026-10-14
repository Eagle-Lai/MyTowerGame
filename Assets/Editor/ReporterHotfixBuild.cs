using System.IO;
using UnityEditor;
using UnityEngine;
using HybridCLR.Editor.Commands;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 【无人值守构建】纯热更流水线：热更 dll ▸ 拷贝+md5 ▸ 收集器登记 ▸ 资源包（不含 APK）。
    ///
    /// 用途：命令行 batchmode 驱动（Unity MCP 不可用时的替代通道），产出物可被
    /// HotUpdateServer（junction → StreamingAssets/HybridCLR + Bundles/Android/FreeTower）
    /// 直接下发到模拟器/真机：
    ///   ① HybridCLR Generate/All —— 重编热更 dll（与「7. 一键完整构建」同源）
    ///   ② 拷贝热更 dll + AOT 元数据到 StreamingAssets/HybridCLR/ + 生成 md5 清单
    ///   ③ 收集器登记真机必需资源（Main 场景 / BootUI / Reporter 图标，幂等）
    ///   ④ YooAsset 资源包构建（版本自动递增）
    ///
    /// 【与菜单 7（BuildApkFull）的区别】跳过 APK 构建 —— 纯热更场景不需要出包，
    /// 也不占用 IL2CPP 打包的几十分钟。
    ///
    /// 【命令行】
    ///   Unity.exe -batchmode -projectPath E:\MyTowerGame ^
    ///     -executeMethod FTProject.EditorTools.ReporterHotfixBuild.Start ^
    ///     -logFile E:\MyTowerGame\Logs\reporter_build.log
    ///   注意：**不加 -quit** —— 流水线由 update tick 驱动，完成/失败都会写状态文件
    ///   Library/FTReporterBuildStatus.txt（START / PHASE / DONE OK / DONE FAIL），
    ///   外部轮询到 DONE 后结束编辑器进程即可。
    ///
    /// 【为什么用状态机】Generate/All 会重写 AOTGenericReferences.cs，可能触发脚本
    /// 编译与域重载 —— 正在执行的方法栈会被直接杀掉。所以阶段存 SessionState
    /// （域重载后保留），由 [InitializeOnLoad] 重新挂上的 Tick 继续推进；
    /// 每个阶段的"推进"放在**执行成功之后**：若域重载打断了执行，下一轮会原地
    /// 重跑该阶段（幂等），宁可多花几分钟也绝不静默使用旧产物。
    /// </summary>
    [InitializeOnLoad]
    public static class ReporterHotfixBuild
    {
        private const string PhaseKey = "FTReporterBuild.Phase";

        /// <summary>SessionState 键：dll-only 模式（只重编+同步热更 dll，跳过收集器与 AB）。</summary>
        private const string DllOnlyKey = "FTReporterBuild.DllOnly";

        private const string StatusFileRelative = "Library/FTReporterBuildStatus.txt";

        /// <summary>YooAsset 包裹名（= AB 输出目录名，与 BuildApkFull 的约定一致）。</summary>
        private const string YooPackageName = "FreeTower";

        /// <summary>
        /// 工程根目录。**不依赖进程工作目录** —— batchmode 命令行启动时 cwd 未必是
        /// 工程根（GUI 下由 Hub 启动才会是），所以一律从 Application.dataPath 推。
        /// </summary>
        private static string ProjectRoot
        {
            get { return Path.GetDirectoryName(Application.dataPath); }
        }

        private static string StatusFilePath
        {
            get { return Path.Combine(ProjectRoot, StatusFileRelative); }
        }

        /// <summary>
        /// 编辑器内入口：Unity 编辑器开着时用（命令行 batchmode 会被工程锁挡住）。
        /// 与命令行 Start 完全同一套状态机；点击后全自动跑完 dll+AB（参考状态文件
        /// Library/FTReporterBuildStatus.txt 与 Console 日志）。
        /// </summary>
        [MenuItem("Tools/塔防/9. Reporter 修复构建（纯热更 dll+AB，不含 APK）", false, 112)]
        public static void StartFromMenu()
        {
            Start();
        }

        /// <summary>
        /// 【dll-only 模式】只跑 ① Generate ② Copy+md5，跳过收集器与 AB。
        /// 用于"资源包没变、只重编热更 dll"的场景 —— 典型是**编译宏变更**后
        /// （宏在热更 dll 编译期生效，改了宏必须重编 dll 才能让运行时分支出新行为）。
        /// </summary>
        [MenuItem("Tools/塔防/9a. 仅重编热更 dll（宏变更后同步用）", false, 113)]
        public static void StartDllOnlyFromMenu()
        {
            StartDllOnly();
        }

        /// <summary>dll-only 的 batchmode 入口。</summary>
        public static void StartDllOnly()
        {
            string phase = GetPhase();
            if (phase != "Idle" && phase != "Done" && phase != "Fail")
            {
                Debug.LogWarning("[ReporterBuild] 已有流水线在跑（" + phase + "），忽略本次 StartDllOnly。");
                return;
            }

            try { File.Delete(StatusFilePath); }
            catch (System.Exception) { }

            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.Android)
            {
                Fail("当前构建目标不是 Android（" + EditorUserBuildSettings.activeBuildTarget + "），中止。");
                return;
            }

            SessionState.SetString(DllOnlyKey, "1");
            SetPhase("Generate");
            WriteStatus("START DLL-ONLY " + System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
            Debug.Log("[ReporterBuild] 开始（dll-only）：Generate ▸ Copy ▸ md5（跳过收集器与 AB）");
        }

        /// <summary>batchmode 入口（-executeMethod 只认无参静态方法）。</summary>
        public static void Start()
        {
            string phase = GetPhase();
            if (phase != "Idle" && phase != "Done" && phase != "Fail")
            {
                Debug.LogWarning("[ReporterBuild] 已有流水线在跑（" + phase + "），忽略本次 Start。");
                return;
            }

            // 清掉上一次的轮询状态（外部以"本次启动后新出现的 DONE 行"为准）
            try { File.Delete(StatusFilePath); }
            catch (System.Exception) { }

            SessionState.SetString(DllOnlyKey, "");   // 防串：完整流程不带 dll-only 标志

            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.Android)
            {
                Fail("当前构建目标不是 Android（" + EditorUserBuildSettings.activeBuildTarget +
                     "），热更 dll / AB 会打到错误平台。请先在编辑器里切到 Android 再跑本流水线。");
                return;
            }

            SetPhase("Generate");
            WriteStatus("START REPORTER-HOTFIX " + System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
            Debug.Log("[ReporterBuild] 开始：dll ▸ 拷贝+md5 ▸ 收集器 ▸ AB（纯热更，不含 APK）");
        }

        static ReporterHotfixBuild()
        {
            // 【InitializeOnLoad】每次域重载后重新挂上驱动器，流水线从 SessionState 断点继续。
            EditorApplication.update += Tick;
        }

        private static void Tick()
        {
            string phase = GetPhase();
            if (phase == "Idle" || phase == "Done" || phase == "Fail" || phase == "AbBusy")
            {
                return;
            }
            // 编译 / 导入中一律等待（状态机会在空闲后自动继续）
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                return;
            }

            try
            {
                switch (phase)
                {
                    case "Generate": TickGenerate(); break;
                    case "Copy": TickCopy(); break;
                    case "Collector": TickCollector(); break;
                    case "AbBuild": TickAbBuild(); break;
                }
            }
            catch (System.Exception e)
            {
                Fail(phase + " 阶段异常：" + e);
            }
        }

        // ------------------------------------------------------------------
        // ① HybridCLR Generate/All
        // ------------------------------------------------------------------

        private static void TickGenerate()
        {
            Debug.Log("[ReporterBuild] ① HybridCLR Generate/All …");
            // 直接调包内 API（与菜单「HybridCLR/Generate/All」同一实现），
            // 不依赖 batchmode 下菜单系统的可用性。
            PrebuildCommand.GenerateAll();
            AssetDatabase.Refresh();

            // 执行成功后才推进阶段：若上面触发了域重载，重载回来的 Tick 会原地重跑
            // 本阶段（此时产物已是最新，第二次跑通常不再触发重载，代价可接受）。
            SetPhase("Copy");
            WriteStatus("PHASE generate ok");
            Debug.Log("[ReporterBuild] ① 完成。");
        }

        // ------------------------------------------------------------------
        // ② 拷贝热更 dll + 生成 md5 清单
        // ------------------------------------------------------------------

        private static void TickCopy()
        {
            Debug.Log("[ReporterBuild] ② 拷贝 dll + 生成 md5 …");

            EditorUtil.Report report = new EditorUtil.Report();
            HybridCLRDllCopier.Copy(report);
            if (report.Errors > 0)
            {
                Fail("② 拷贝热更 dll 失败：\n" + report.Text);
                return;
            }

            EditorUtil.Report md5Report = new EditorUtil.Report();
            HybridCLRMd5Generator.Generate(md5Report);
            if (md5Report.Errors > 0)
            {
                Fail("② 生成 md5 清单失败：\n" + md5Report.Text);
                return;
            }

            AssetDatabase.Refresh();   // StreamingAssets 新增文件，刷新一次

            // dll-only 模式：Copy 之后直接收工（不碰收集器与 AB —— 它们没有变化）
            if (SessionState.GetString(DllOnlyKey, "") == "1")
            {
                SessionState.SetString(DllOnlyKey, "");
                SetPhase("Done");
                WriteStatus("PHASE copy ok");
                WriteStatus("DONE OK (dll-only)");
                Debug.Log("[ReporterBuild] ✔ dll-only 完成（跳过收集器登记与 AB 构建）。");
                return;
            }

            SetPhase("Collector");
            WriteStatus("PHASE copy ok");
            Debug.Log("[ReporterBuild] ② 完成。");
        }

        // ------------------------------------------------------------------
        // ③ 收集器登记（幂等）
        // ------------------------------------------------------------------

        private static void TickCollector()
        {
            Debug.Log("[ReporterBuild] ③ 收集器登记 …");
            string error;
            if (!AddMainSceneCollector.Ensure(out error))
            {
                Fail("③ 收集器登记失败：" + error);
                return;
            }

            AssetDatabase.SaveAssets();
            SetPhase("AbBuild");
            WriteStatus("PHASE collector ok");
            Debug.Log("[ReporterBuild] ③ 完成。");
        }

        // ------------------------------------------------------------------
        // ④ YooAsset 资源包构建（版本自动递增）
        // ------------------------------------------------------------------

        private static void TickAbBuild()
        {
            // 防重入标记：AbBusy 状态下 Tick 不再进入任何分支（构建是同步阻塞的，
            // 正常路径执行完会直接推进到 Done；这里只防御理论上不可能发生的域重载重入）。
            SetPhase("AbBusy");

            string version = NextVersion();
            WriteStatus("PHASE ab building version=" + version);
            Debug.Log("[ReporterBuild] ④ 构建资源包，版本 " + version + " …");

#if USE_YOOASSET
            EditorUtil.Report report = new EditorUtil.Report();
            bool ok = FTYooAssetSetupWizard.BuildRealBundlesCore(version, false, report);
            if (!ok)
            {
                Fail("④ YooAsset 资源包构建失败：\n" + report.Text);
                return;
            }
            Debug.Log("[ReporterBuild] ④ AB 构建成功：\n" + report.Text);
            WriteStatus("PHASE ab ok version=" + version);
#else
            Fail("④ 当前未启用 USE_YOOASSET 宏，本流水线只支持 YooAsset 链路。");
            return;
#endif

            SetPhase("Done");
            WriteStatus("DONE OK version=" + version);
            Debug.Log("[ReporterBuild] ✔ 全部完成（dll + AB v" + version + "）。可结束编辑器进程。");
        }

        /// <summary>
        /// 自动选下一个资源包版本号：扫 Bundles/&lt;平台&gt;/&lt;包裹&gt;/ 下已有的
        /// "x.y.z" 目录，取最大版本把 patch 位 +1；没有任何历史版本则从 1.0.0 起。
        /// （与 BuildApkFull 同算法，两边必须一致，否则两套流水线会撞版本号。）
        /// </summary>
        private static string NextVersion()
        {
            string root = Path.Combine(ProjectRoot, "Bundles",
                EditorUserBuildSettings.activeBuildTarget.ToString(), YooPackageName);

            int major = 1, minor = 0, patch = -1;
            if (Directory.Exists(root))
            {
                foreach (string dir in Directory.GetDirectories(root))
                {
                    string name = Path.GetFileName(dir);
                    string[] parts = name.Split('.');
                    if (parts.Length != 3) continue;
                    int a, b, c;
                    if (!int.TryParse(parts[0], out a) || !int.TryParse(parts[1], out b)
                        || !int.TryParse(parts[2], out c)) continue;
                    if (a > major || (a == major && (b > minor || (b == minor && c > patch))))
                    {
                        major = a; minor = b; patch = c;
                    }
                }
            }

            if (patch < 0)
            {
                return "1.0.0";
            }
            return major + "." + minor + "." + (patch + 1);
        }

        // ------------------------------------------------------------------
        // 通用
        // ------------------------------------------------------------------

        private static void Fail(string message)
        {
            SetPhase("Fail");
            Debug.LogError("[ReporterBuild] ✘ 流水线失败：" + message);

            string oneLine = message.Replace("\r", " ").Replace("\n", " ");
            if (oneLine.Length > 160)
            {
                oneLine = oneLine.Substring(0, 160);
            }
            WriteStatus("DONE FAIL " + oneLine);
        }

        private static string GetPhase()
        {
            return SessionState.GetString(PhaseKey, "Idle");
        }

        private static void SetPhase(string phase)
        {
            SessionState.SetString(PhaseKey, phase);
        }

        /// <summary>往状态文件追加一行（外部轮询用；失败不影响流水线）</summary>
        private static void WriteStatus(string line)
        {
            try
            {
                File.AppendAllText(StatusFilePath,
                    System.DateTime.Now.ToString("HH:mm:ss") + " " + line + "\n");
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("[ReporterBuild] 状态文件写入失败：" + e.Message);
            }
        }
    }
}
