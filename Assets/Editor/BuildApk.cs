using System.IO;
using System.Text;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 一键构建 APK（Android）。
    ///
    /// 流程：
    ///   ① 前置检查：非编译中 / 非运行中 / 当前构建目标必须是 Android
    ///   ② 环境自检：JDK / SDK / NDK 路径是否已配置（缺了只警告不中止，让 Gradle 自己报真正的错）
    ///   ③ BuildPipeline.BuildPlayer 构建到 &lt;工程根目录&gt;/Builds/Android/freedomtower.apk
    ///      （未配置签名 keystore 时 Unity 自动使用 debug keystore，仅限开发用）
    ///   ④ 自检：APK 文件是否存在、大小是否合理，结果全部走 Console 日志（不弹窗）
    ///
    /// 状态文件：&lt;工程根目录&gt;/Library/FTBuildApkStatus.txt
    ///   构建开始 / 结束都会追加一行带时间戳的状态（START / DONE OK / DONE FAIL），
    ///   供外部脚本（MCP/CI）轮询构建进度，避免阻塞式等待。
    ///
    /// 菜单：
    ///   Tools ▸ 塔防 ▸ 6. 一键构建 APK
    /// </summary>
    public static class BuildApk
    {
        /// <summary>输出路径（相对工程根目录）</summary>
        public const string OutputRelative = "Builds/Android/freedomtower.apk";

        /// <summary>构建状态文件（相对工程根目录，外部轮询用）</summary>
        public const string StatusFileRelative = "Library/FTBuildApkStatus.txt";

        [MenuItem("Tools/塔防/6. 一键构建 APK", false, 110)]
        public static void BuildMenu()
        {
            // 【不直接 Build】BuildPipeline.BuildPlayer 会阻塞主线程十几分钟，
            // 菜单回调里先只做调度（delayCall），让菜单调用本身立刻返回。
            EditorApplication.delayCall += BuildNow;
        }

        public static void BuildNow()
        {
            // ① 前置检查
            if (EditorApplication.isCompiling)
            {
                Debug.LogError("[BuildApk] 构建中止：编辑器正在编译脚本，请等编译完成后再试。");
                WriteStatus("DONE FAIL compiling");
                return;
            }
            if (EditorApplication.isPlaying)
            {
                Debug.LogError("[BuildApk] 构建中止：编辑器正在 Play 模式，请先退出。");
                WriteStatus("DONE FAIL playing");
                return;
            }
            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.Android)
            {
                Debug.LogError("[BuildApk] 构建中止：当前构建目标是 " +
                               EditorUserBuildSettings.activeBuildTarget + "，请先切换到 Android（File ▸ Build Settings）。");
                WriteStatus("DONE FAIL wrong_target");
                return;
            }

            // ② 环境自检（只警告不中止）
            EditorUtil.Report env = new EditorUtil.Report();
            env.Head("构建环境自检");
            CheckEnv("JDK", "JdkPath", env);
            CheckEnv("SDK", "AndroidSdkRoot", env);
            CheckEnv("NDK", "AndroidNdkRoot", env);
            if (string.IsNullOrEmpty(PlayerSettings.Android.keystoreName))
            {
                env.Ok("未配置签名 keystore → 使用 debug keystore（仅开发用）");
            }
            else
            {
                env.Ok("签名 keystore：" + PlayerSettings.Android.keystoreName);
            }
            Debug.Log("[BuildApk] " + env.Text);

            // ③ 收集构建场景
            var sceneList = new StringBuilder();
            System.Collections.Generic.List<string> scenes = new System.Collections.Generic.List<string>();
            foreach (EditorBuildSettingsScene s in EditorBuildSettings.scenes)
            {
                if (!s.enabled) continue;
                scenes.Add(s.path);
                sceneList.AppendLine("    " + s.path);
            }
            if (scenes.Count == 0)
            {
                Debug.LogError("[BuildApk] 构建中止：Build Settings 里没有任何启用的场景。");
                WriteStatus("DONE FAIL no_scenes");
                return;
            }

            string outputPath = Path.GetFullPath(OutputRelative);
            string outputDir = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrEmpty(outputDir))
            {
                Directory.CreateDirectory(outputDir);
            }

            Debug.Log("[BuildApk] 开始构建 APK → " + outputPath + "\n场景：\n" + sceneList);
            WriteStatus("START " + System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));

            // ④ 构建（阻塞主线程，IL2CPP 首包可能十几分钟以上）
            BuildPlayerOptions options = new BuildPlayerOptions
            {
                scenes = scenes.ToArray(),
                locationPathName = outputPath,
                target = BuildTarget.Android,
                options = BuildOptions.None,
            };
            BuildReport report = BuildPipeline.BuildPlayer(options);

            // ⑤ 结果自检
            if (report.summary.result == BuildResult.Succeeded)
            {
                long sizeMb = (long)(report.summary.totalSize / (1024 * 1024));
                Debug.Log("[BuildApk] ✔ 构建成功：" + outputPath +
                          "（" + sizeMb + " MB，耗时 " + report.summary.totalTime.TotalMinutes.ToString("F1") + " 分钟）");
                WriteStatus("DONE OK size=" + sizeMb + "MB path=" + OutputRelative);
            }
            else
            {
                Debug.LogError("[BuildApk] ✘ 构建失败：result=" + report.summary.result +
                               "，错误 " + report.summary.totalErrors + " 条，详见 Console / Editor.log。");
                WriteStatus("DONE FAIL build_result=" + report.summary.result);
            }
        }

        /// <summary>检查一项 Android 工具链路径是否已配置，结果只记日志</summary>
        private static void CheckEnv(string label, string prefsKey, EditorUtil.Report report)
        {
            string path = EditorPrefs.GetString(prefsKey, "");
            if (string.IsNullOrEmpty(path) || !Directory.Exists(path))
            {
                report.Warn(label + " 路径未配置或不存在（EditorPrefs." + prefsKey + " = '" + path + "'）");
            }
            else
            {
                report.Ok(label + "：" + path);
            }
        }

        /// <summary>往状态文件追加一行（外部轮询用；失败不影响构建）</summary>
        public static void WriteStatus(string line)
        {
            try
            {
                File.AppendAllText(Path.GetFullPath(StatusFileRelative),
                    System.DateTime.Now.ToString("HH:mm:ss") + " " + line + "\n");
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("[BuildApk] 状态文件写入失败：" + e.Message);
            }
        }
    }

    /// <summary>
    /// 一键完整构建流水线：热更 dll ▸ 资源包 ▸ APK。
    ///
    /// 流程（也是状态机的各个阶段）：
    ///   ① DllGenerate —— 执行「HybridCLR ▸ Generate ▸ All」
    ///      （产出热更 dll + AOT 裁剪元数据到 HybridCLRData/，且会重写
    ///        AOTGenericReferences.cs，可能触发脚本编译 / 域重载）
    ///   ② DllCopy —— 拷贝热更 dll + AOT 元数据到 StreamingAssets/HybridCLR/，
    ///      再生成 md5.txt 校验清单（首包自带 + 上传服务器用）
    ///   ③ AbBuild —— 构建资源包：
    ///      USE_YOOASSET 宏开启 → YooAsset 真实资源包（版本号自动递增）；
    ///      未开启 → 旧的 BuildPipeline.BuildAssetBundles（StreamingAssets/AssetBundles）
    ///   ④ ApkBuild —— 复用「6. 一键构建 APK」构建 APK
    ///
    /// 【为什么做成状态机而不是一个大方法】步骤 ① 会改脚本（AOTGenericReferences.cs）
    /// 触发编译甚至域重载 —— 域重载会把正在执行的方法栈直接杀掉。状态存 SessionState
    /// （域重载后仍在），由 EditorApplication.update 每帧驱动，编译完成后从断点继续。
    ///
    /// 状态文件：同 BuildApk（Library/FTBuildApkStatus.txt），每个阶段完成都会追加一行
    ///   PHASE …，供 MCP / CI 轮询。
    ///
    /// 菜单：
    ///   Tools ▸ 塔防 ▸ 7. 一键完整构建（DLL ▸ AB ▸ APK）
    /// </summary>
    [InitializeOnLoad]
    public static class BuildApkFull
    {
        /// <summary>SessionState 键：当前阶段</summary>
        private const string PhaseKey = "FTBuildApkFull.Phase";

        /// <summary>SessionState 键：本次选定的资源包版本号</summary>
        private const string VersionKey = "FTBuildApkFull.Version";

        /// <summary>
        /// YooAsset 包裹名（= AB 输出目录名）。
        /// ⚠️ 与 YooAssetResLoader.PackageName 一致；此处手写是因为该常量套在
        /// USE_YOOASSET 宏里，未开宏时引用会编译不过。
        /// </summary>
        private const string YooPackageName = "FreeTower";

        [MenuItem("Tools/塔防/7. 一键完整构建（DLL ▸ AB ▸ APK）", false, 111)]
        public static void StartMenu()
        {
            if (GetPhase() != "Idle")
            {
                Debug.LogError("[BuildFull] 已有完整构建在进行中（阶段 " + GetPhase() + "），请先等它结束。");
                return;
            }
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                Debug.LogError("[BuildFull] 编辑器正在编译 / 导入，请等空闲后再试。");
                return;
            }
            if (EditorApplication.isPlaying)
            {
                Debug.LogError("[BuildFull] 编辑器正在 Play 模式，请先退出。");
                return;
            }
            if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.Android)
            {
                Debug.LogError("[BuildFull] 构建中止：当前构建目标是 " +
                               EditorUserBuildSettings.activeBuildTarget + "，请先切换到 Android。");
                return;
            }

            // HybridCLR 生成 AOTGenericReferences.cs 后会触发编译：先设好下一阶段再执行，
            // 这样即使域重载发生在调用过程中，流水线也能从 DllCopy 继续而不是从头再来。
            SetPhase("DllGenerate");
            BuildApk.WriteStatus("START FULL " + System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
            Debug.Log("[BuildFull] 完整构建开始：DLL ▸ AB ▸ APK（状态见 Library/FTBuildApkStatus.txt）");
        }

        static BuildApkFull()
        {
            // 【InitializeOnLoad】每次域重载后重新挂上驱动器，流水线从 SessionState 断点继续。
            EditorApplication.update += Tick;
        }

        private static void Tick()
        {
            string phase = GetPhase();
            if (phase == "Idle")
            {
                return;
            }
            // 编译 / 导入中一律等待（状态机会在空闲后自动继续）
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                return;
            }

            switch (phase)
            {
                case "DllGenerate":
                    TickDllGenerate();
                    break;
                case "DllCopy":
                    TickDllCopy();
                    break;
                case "AbBuild":
                    TickAbBuild();
                    break;
                case "ApkBuild":
                    SetPhase("Idle");
                    BuildApk.BuildNow();
                    break;
            }
        }

        // ------------------------------------------------------------------
        // ① HybridCLR Generate/All
        // ------------------------------------------------------------------

        private static void TickDllGenerate()
        {
            // 先推进阶段再执行：Generate/All 过程中就可能触发域重载
            SetPhase("DllCopy");

            bool ok = EditorApplication.ExecuteMenuItem("HybridCLR/Generate/All");
            if (!ok)
            {
                Fail("执行「HybridCLR/Generate/All」失败：找不到该菜单（确认 HybridCLR 包已安装）。");
                return;
            }
            BuildApk.WriteStatus("PHASE dll_generate ok");
            Debug.Log("[BuildFull] ① HybridCLR Generate/All 完成。");

            // 生成产物含 .cs（AOTGenericReferences），刷新可能触发编译；下一 tick 会等它结束
            AssetDatabase.Refresh();
        }

        // ------------------------------------------------------------------
        // ② 拷贝热更 dll + 生成 md5 清单
        // ------------------------------------------------------------------

        private static void TickDllCopy()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            HybridCLRDllCopier.Copy(report);
            if (report.Errors > 0)
            {
                Fail("拷贝热更 dll 失败：\n" + report.Text);
                return;
            }

            EditorUtil.Report md5Report = new EditorUtil.Report();
            HybridCLRMd5Generator.Generate(md5Report);
            if (md5Report.Errors > 0)
            {
                Fail("生成 md5 清单失败：\n" + md5Report.Text);
                return;
            }

            Debug.Log("[BuildFull] ② 热更 dll 就位：\n" + report.Text + md5Report.Text);
            BuildApk.WriteStatus("PHASE dll ok");
            Debug.Log("[BuildFull] ② 热更 dll + md5 清单完成。");

            // StreamingAssets 新增了文件，刷新导入；.cs 不会因此变化，一般不触发编译
            AssetDatabase.Refresh();
            SetPhase("AbBuild");
        }

        // ------------------------------------------------------------------
        // ③ 构建资源包
        // ------------------------------------------------------------------

        private static void TickAbBuild()
        {
            SetPhase("ApkBuild");

            string version = NextVersion();
            SessionState.SetString(VersionKey, version);

            Debug.Log("[BuildFull] ③ 开始构建资源包，版本 " + version + " …");
#if USE_YOOASSET
            EditorUtil.Report abReport = new EditorUtil.Report();
            bool ok = FTYooAssetSetupWizard.BuildRealBundlesCore(version, false, abReport);
            if (!ok)
            {
                Fail("YooAsset 资源包构建失败：\n" + abReport.Text);
                return;
            }
            BootReleaseBuilder.Publish(version, "Library/FT_HotUpdate/apk-baseline", true);
            Debug.Log("[BuildFull] ③ YooAsset 资源包构建成功：\n" + abReport.Text);
            BuildApk.WriteStatus("PHASE ab ok version=" + version + " (yooasset)");
#else
            // 旧链路（未开 USE_YOOASSET）：BuildPipeline.BuildAssetBundles，
            // 产物进 StreamingAssets/AssetBundles/<平台>/，自检与日志在 BuildAssetBundles 内部。
            BuildAssetBundles.Build();
            string manifestFile = System.IO.Path.Combine(
                FTProject.ResPathUtil.BuildOutputRoot, FTProject.ResPathUtil.ManifestBundleName);
            if (!File.Exists(manifestFile))
            {
                Fail("旧链路 AB 构建后找不到主清单：" + manifestFile + "（详情见上方日志）");
                return;
            }
            BuildApk.WriteStatus("PHASE ab ok (legacy)");
            Debug.Log("[BuildFull] ③ 旧链路 AssetBundle 构建成功。");
#endif
        }

        /// <summary>
        /// 自动选下一个资源包版本号：扫 Bundles/&lt;平台&gt;/&lt;包裹&gt;/ 下已有的
        /// "x.y.z" 目录，取最大版本把 patch 位 +1；没有任何历史版本则从 1.0.0 起。
        /// </summary>
        private static string NextVersion()
        {
            string root = Path.Combine("Bundles",
                EditorUserBuildSettings.activeBuildTarget.ToString(), YooPackageName);
            string fullRoot = Path.GetFullPath(root);

            int major = 1, minor = 0, patch = -1;
            if (Directory.Exists(fullRoot))
            {
                foreach (string dir in Directory.GetDirectories(fullRoot))
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
            SetPhase("Idle");
            Debug.LogError("[BuildFull] ✘ 完整构建失败：" + message);
            BuildApk.WriteStatus("DONE FAIL full_pipeline");
        }

        private static string GetPhase()
        {
            return SessionState.GetString(PhaseKey, "Idle");
        }

        private static void SetPhase(string phase)
        {
            SessionState.SetString(PhaseKey, phase);
        }
    }
}
