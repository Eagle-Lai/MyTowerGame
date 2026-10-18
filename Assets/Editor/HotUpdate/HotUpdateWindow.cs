using System;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 一键热更面板：**一个按钮**跑完
    /// 重编 dll ▸ 同步 dll+md5 ▸ Ab（版本自增） ▸ 清单 ▸ 部署 ▸ 上传 ▸ 本地验证 ▸（可选）Play 冒烟。
    ///
    /// ==================================================================
    /// 【为什么做成窗口而不是只有一个菜单项】
    ///   这条链路要跑几分钟，过程中最需要知道三件事：
    ///     ① 现在到第几步了（哪一步最慢/最可疑）
    ///     ② 这一步之后还剩什么（部署/上传/验证是否被跳过）
    ///     ③ 失败了到底卡在哪（红字 + 日志尾）
    ///   只有 Console 的话，第 ① ② 都看不出来；所以窗口里给步骤条 + 进度条 + 日志尾。
    ///
    /// 【不弹任何确认框】项目约定：编辑器脚本弹 DisplayDialog 会阻塞 MCP / CI 主线程。
    ///   有风险的项（远端上传、Play 冒烟）改成**显式勾选**，勾了才做。
    ///
    /// 【菜单】
    ///   10.  打开面板
    ///   10a. 按上次选项立即执行
    ///   10b. 仅本地验证（不构建，校验服务器上当前这一版）
    ///   10c. 本地热更服务器 起/停（真机前手动开着的那个 HTTP 服务）
    /// ==================================================================
    /// </summary>
    public class HotUpdateWindow : EditorWindow
    {
        private const string MenuRoot = "Tools/塔防/";
        private const string MenuOpen = MenuRoot + "10. 一键热更…（DLL▸AB▸部署▸验证）";
        private const string MenuRun = MenuRoot + "10a. 一键热更·立即执行（按上次选项）";
        private const string MenuVerify = MenuRoot + "10b. 本地运行验证（不构建，校验当前部署）";
        private const string MenuServer = MenuRoot + "10c. 本地热更服务器（起/停）";

        private Vector2 _logScroll;
        private Vector2 _stepScroll;
        private bool _showOptions = true;
        private string _logText = "";
        private double _logReadAt;
        private string _versionSummary = "";
        private double _versionReadAt;
        private double _nextRepaint;

        // ------------------------------------------------------------------
        // 菜单
        // ------------------------------------------------------------------

        [MenuItem(MenuOpen, false, 114)]
        public static void Open()
        {
            HotUpdateWindow window = GetWindow<HotUpdateWindow>(false, "一键热更", true);
            window.minSize = new Vector2(620f, 560f);
            window.Show();
        }

        [MenuItem(MenuRun, false, 115)]
        public static void RunNow()
        {
            HotUpdatePipeline.StartFull();
        }

        [MenuItem(MenuVerify, false, 116)]
        public static void VerifyNow()
        {
            HotUpdatePipeline.StartVerifyOnly();
        }

        [MenuItem(MenuServer, false, 117)]
        public static void ToggleServer()
        {
            if (HotUpdateLocalServer.IsRunning)
            {
                HotUpdateLocalServer.Stop();
                Debug.Log("[HotUpdate] 本地热更服务器已停止。");
                return;
            }

            string error;
            if (HotUpdateLocalServer.Start(HotUpdatePaths.CdnRoot, HotUpdateSettings.VerifyPort, out error))
            {
                Debug.Log("[HotUpdate] 本地热更服务器：" + HotUpdateLocalServer.Url +
                          "（模拟器用 http://10.0.2.2:" + HotUpdateSettings.VerifyPort + "，真机请用 python 脚本绑 0.0.0.0）");
            }
            else
            {
                Debug.LogError("[HotUpdate] 本地热更服务器启动失败：" + error);
            }
        }

        // ------------------------------------------------------------------
        // 生命周期
        // ------------------------------------------------------------------

        private void OnEnable()
        {
            EditorApplication.update += OnEditorUpdate;
        }

        private void OnDisable()
        {
            EditorApplication.update -= OnEditorUpdate;
        }

        private void OnEditorUpdate()
        {
            if (!HotUpdatePipeline.IsRunning)
            {
                return;
            }
            if (EditorApplication.timeSinceStartup < _nextRepaint)
            {
                return;
            }
            _nextRepaint = EditorApplication.timeSinceStartup + 0.2;
            Repaint();
        }

        // ------------------------------------------------------------------
        // 绘制
        // ------------------------------------------------------------------

        private void OnGUI()
        {
            DrawTitle();
            DrawStatus();
            EditorGUILayout.Space();

            DrawSteps();
            EditorGUILayout.Space();

            DrawProgress();
            EditorGUILayout.Space();

            _showOptions = EditorGUILayout.Foldout(_showOptions, "选项（勾选项会直接记住）", true);
            if (_showOptions)
            {
                DrawOptions();
            }

            EditorGUILayout.Space();
            DrawButtons();
            EditorGUILayout.Space();

            DrawLog();
        }

        private void DrawTitle()
        {
            EditorGUILayout.LabelField("一键热更", EditorStyles.boldLabel);
            EditorGUILayout.LabelField(
                "重编 dll ▸ 同步 dll+md5 ▸ 构建 AB（版本自增） ▸ 清单 ▸ 部署 ▸ 上传 ▸ 本地验证 ▸ Play 冒烟",
                EditorStyles.miniLabel);
        }

        private void DrawStatus()
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox);

            EditorGUILayout.LabelField("当前平台",
                HotUpdatePaths.PlatformFolder + "（构建目标 " +
                EditorUserBuildSettings.activeBuildTarget + "）");

            EditorGUILayout.LabelField("本地服务器根", HotUpdatePaths.CdnRoot);
            EditorGUILayout.LabelField("随包 dll 目录", HotUpdatePaths.DllDir);

            if (string.IsNullOrEmpty(_versionSummary) || EditorApplication.timeSinceStartup - _versionReadAt > 2.0)
            {
                _versionSummary = HotUpdateVersionUtil.Describe();
                _versionReadAt = EditorApplication.timeSinceStartup;
            }
            EditorGUILayout.LabelField("版本号", _versionSummary);

            bool serverRunning = HotUpdateLocalServer.IsRunning;
            EditorGUILayout.LabelField("本地热更服务器",
                serverRunning
                    ? HotUpdateLocalServer.Url + "（已服务 " + HotUpdateLocalServer.ServedCount + " 个请求）"
                    : "未启动（点 10c 或面板按钮启动）");

            string phase = HotUpdatePipeline.CurrentPhase;
            string phaseText;
            if (HotUpdatePipeline.IsRunning)
            {
                phaseText = "运行中 · " + PhaseTitle(phase) + (string.IsNullOrEmpty(HotUpdatePipeline.JobText)
                    ? "" : " · " + HotUpdatePipeline.JobText);
            }
            else if (phase == "Done")
            {
                phaseText = "上一次已完成 · v" + HotUpdatePipeline.CurrentVersion;
            }
            else if (phase == "Fail")
            {
                phaseText = "上一次失败 · v" + HotUpdatePipeline.CurrentVersion;
            }
            else
            {
                phaseText = "空闲";
            }
            EditorGUILayout.LabelField("流水线", phaseText);

            if (phase == "Fail" && !string.IsNullOrEmpty(HotUpdatePipeline.LastError))
            {
                EditorGUILayout.HelpBox(HotUpdatePipeline.LastError, MessageType.Error);
            }

            if (EditorApplication.isPlaying)
            {
                EditorGUILayout.HelpBox("编辑器在 Play 模式：热更与构建都不可用，请先退出。", MessageType.Warning);
            }
            else if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                EditorGUILayout.HelpBox("编辑器正在编译 / 导入资源，流水线会自动等待。", MessageType.Info);
            }
            else if (EditorUserBuildSettings.activeBuildTarget != BuildTarget.Android)
            {
                EditorGUILayout.HelpBox("当前构建目标不是 Android：热更 dll / AB 会打到错误平台。", MessageType.Warning);
            }

            EditorGUILayout.EndVertical();
        }

        private void DrawSteps()
        {
            EditorGUILayout.LabelField("步骤", EditorStyles.boldLabel);

            _stepScroll = EditorGUILayout.BeginScrollView(_stepScroll, GUILayout.Height(200f));
            for (int i = 0; i < HotUpdatePipeline.Phases.Length - 1; i++) // 最后一项 Done 不单独画
            {
                string phase = HotUpdatePipeline.Phases[i];
                string title = HotUpdatePipeline.PhaseTitles[i];
                string detail = StepDetail(phase);

                Color old = GUI.color;
                GUI.color = StepColor(i);
                EditorGUILayout.LabelField(StepIcon(i) + "  " + (i + 1) + ". " + title +
                                           (string.IsNullOrEmpty(detail) ? "" : "    " + detail),
                    EditorStyles.miniLabel);
                GUI.color = old;
            }
            EditorGUILayout.EndScrollView();
        }

        private void DrawProgress()
        {
            Rect rect = EditorGUILayout.GetControlRect(false, 20f);
            float value = HotUpdatePipeline.Progress01;
            string label;
            if (HotUpdatePipeline.IsRunning)
            {
                string job = HotUpdatePipeline.JobText;
                if (!string.IsNullOrEmpty(job) && HotUpdatePipeline.JobProgress01 > 0f)
                {
                    // 异步阶段（上传/校验）用"文件级"进度，比阶段进度更细
                    label = job;
                    value = Mathf.Lerp(value, HotUpdatePipeline.JobProgress01, 0.6f);
                }
                else
                {
                    label = PhaseTitle(HotUpdatePipeline.CurrentPhase);
                }
            }
            else
            {
                label = HotUpdatePipeline.CurrentPhase == "Done" ? "完成" : "就绪";
                value = HotUpdatePipeline.CurrentPhase == "Done" ? 1f : 0f;
            }
            EditorGUI.ProgressBar(rect, value, label);
        }

        private void DrawOptions()
        {
            EditorGUILayout.BeginVertical(EditorStyles.helpBox);

            HotUpdateSettings.DeployLocal = EditorGUILayout.ToggleLeft(
                "① 部署到本地资源服务器（HotUpdateServer，模拟器 / 真机联调用）",
                HotUpdateSettings.DeployLocal);

            HotUpdateSettings.VerifyAfterBuild = EditorGUILayout.ToggleLeft(
                "② 构建后本地运行验证（文件完整性 + HTTP 链路，失败即中断）",
                HotUpdateSettings.VerifyAfterBuild);

            HotUpdateSettings.PlaySmoke = EditorGUILayout.ToggleLeft(
                "③ 验证后进入 Play 冒烟（Main 场景跑 8 秒，统计错误日志）",
                HotUpdateSettings.PlaySmoke);

            HotUpdateSettings.FullRebuild = EditorGUILayout.ToggleLeft(
                "④ 彻底重建 AB（清空 SBP 缓存与整个包裹根目录，慢）",
                HotUpdateSettings.FullRebuild);

            EditorGUILayout.Space();
            HotUpdateSettings.UploadRemote = EditorGUILayout.ToggleLeft(
                "⑤ 上传到远端资源服务器（HTTP PUT）",
                HotUpdateSettings.UploadRemote);
            using (new EditorGUI.DisabledScope(!HotUpdateSettings.UploadRemote))
            {
                HotUpdateSettings.RemoteBaseUrl = EditorGUILayout.TextField(
                    new GUIContent("远端根地址", "例如 https://cdn.example.com/freedomtower（不带结尾斜杠）"),
                    HotUpdateSettings.RemoteBaseUrl);
                HotUpdateSettings.RemoteHeader = EditorGUILayout.TextField(
                    new GUIContent("附加请求头", "格式 Name: Value，例如 Authorization: Bearer xxx（可留空）"),
                    HotUpdateSettings.RemoteHeader);
                EditorGUILayout.LabelField("",
                    string.IsNullOrEmpty(HotUpdateSettings.RemoteBaseUrl)
                        ? "未配置地址 → 勾了也会在预检后中断（不会静默跳过）"
                        : "上传顺序：AB 文件 → dll → 清单；任一失败即中断",
                    EditorStyles.miniLabel);
            }

            EditorGUILayout.Space();
            HotUpdateSettings.VersionOverride = EditorGUILayout.TextField(
                new GUIContent("版本号覆盖", "留空 = 自动递增（本地最高/服务器版本/上次记录三者取最大 +1）"),
                HotUpdateSettings.VersionOverride);
            HotUpdateSettings.VerifyPort = EditorGUILayout.IntField(
                new GUIContent("本地验证端口", "与 HotUpdateServer 的 HTTP 端口一致，默认 8000"),
                HotUpdateSettings.VerifyPort);

            EditorGUILayout.EndVertical();
        }

        private void DrawButtons()
        {
            EditorGUILayout.BeginHorizontal();

            using (new EditorGUI.DisabledScope(HotUpdatePipeline.IsRunning || EditorApplication.isPlaying
                                               || EditorApplication.isCompiling || EditorApplication.isUpdating))
            {
                if (GUILayout.Button("开始一键热更", GUILayout.Height(30f)))
                {
                    HotUpdatePipeline.StartFull();
                }
                if (GUILayout.Button("仅本地验证", GUILayout.Height(30f), GUILayout.Width(110f)))
                {
                    HotUpdatePipeline.StartVerifyOnly();
                }
            }

            using (new EditorGUI.DisabledScope(!HotUpdatePipeline.IsRunning))
            {
                if (GUILayout.Button("取消", GUILayout.Height(30f), GUILayout.Width(70f)))
                {
                    HotUpdatePipeline.Cancel();
                }
            }

            EditorGUILayout.EndHorizontal();

            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("打开服务器目录", GUILayout.Height(22f)))
            {
                Reveal(HotUpdatePaths.CdnRoot);
            }
            if (GUILayout.Button("打开构建输出", GUILayout.Height(22f)))
            {
                string dir = HotUpdatePaths.BuildDir(HotUpdatePipeline.CurrentVersion);
                Reveal(Directory.Exists(dir) ? dir : HotUpdatePaths.BuildRoot());
            }
            if (GUILayout.Button("打开日志", GUILayout.Height(22f)))
            {
                Reveal(File.Exists(HotUpdateLog.FilePath) ? HotUpdateLog.FilePath : HotUpdatePaths.StateDir);
            }
            if (GUILayout.Button(HotUpdateLocalServer.IsRunning ? "停止本地服务" : "启动本地服务",
                    GUILayout.Height(22f)))
            {
                ToggleServer();
            }
            EditorGUILayout.EndHorizontal();
        }

        private void DrawLog()
        {
            EditorGUILayout.LabelField("日志（Logs/HotUpdate/last_run.log）", EditorStyles.boldLabel);

            if (EditorApplication.timeSinceStartup - _logReadAt > 0.4)
            {
                _logText = HotUpdateLog.Tail(7000);
                _logReadAt = EditorApplication.timeSinceStartup;
            }

            using (EditorGUILayout.ScrollViewScope scroll = new EditorGUILayout.ScrollViewScope(
                       _logScroll, GUILayout.Height(180f), GUILayout.ExpandWidth(true)))
            {
                _logScroll = scroll.scrollPosition;
                if (string.IsNullOrEmpty(_logText))
                {
                    EditorGUILayout.LabelField("（还没有运行记录）", EditorStyles.miniLabel);
                }
                else
                {
                    EditorGUILayout.LabelField(_logText, EditorStyles.wordWrappedMiniLabel);
                }
            }
        }

        // ------------------------------------------------------------------
        // 小工具
        // ------------------------------------------------------------------

        private static string PhaseTitle(string phase)
        {
            int index = Array.IndexOf(HotUpdatePipeline.Phases, phase);
            if (index < 0)
            {
                return phase;
            }
            return HotUpdatePipeline.PhaseTitles[index];
        }

        /// <summary>0=待执行 1=进行中 2=成功 3=跳过 4=失败。</summary>
        private static int StepState(int index)
        {
            string phase = HotUpdatePipeline.CurrentPhase;
            HotUpdateOptions options = HotUpdatePipeline.Options;

            // 仅验证模式：前面的构建阶段都不做
            if (options.verifyOnly && index < Array.IndexOf(HotUpdatePipeline.Phases, "Verify"))
            {
                return 3;
            }

            // 未勾选的阶段：显示为跳过（避免"跑完了但什么都没做"的误解）
            string id = HotUpdatePipeline.Phases[index];
            if ((id == "DeployLocal" && !options.local)
                || (id == "UploadRemote" && !options.remote)
                || (id == "Verify" && !options.verify)
                || ((id == "PlaySmokeStart" || id == "PlaySmokeWait") && !options.play))
            {
                return 3;
            }

            if (phase == "Done")
            {
                return 2;
            }

            int current = HotUpdatePipeline.StepIndex;
            if (phase == "Fail")
            {
                if (index < current) return 2;
                if (index == current) return 4;
                return 0;
            }
            if (index < current) return 2;
            if (index == current) return 1;
            return 0;
        }

        private static string StepIcon(int index)
        {
            switch (StepState(index))
            {
                case 1: return "▶";
                case 2: return "✔";
                case 3: return "·";
                case 4: return "✘";
                default: return "○";
            }
        }

        private static Color StepColor(int index)
        {
            switch (StepState(index))
            {
                case 1: return new Color(0.45f, 0.75f, 1f);
                case 2: return new Color(0.45f, 0.85f, 0.45f);
                case 4: return new Color(1f, 0.45f, 0.45f);
                case 3: return new Color(0.6f, 0.6f, 0.6f);
                default: return Color.gray;
            }
        }

        private static string StepDetail(string phase)
        {
            int index = Array.IndexOf(HotUpdatePipeline.Phases, phase);
            int state = StepState(index);
            HotUpdateOptions options = HotUpdatePipeline.Options;

            if (state == 3)
            {
                if (options.verifyOnly && index < Array.IndexOf(HotUpdatePipeline.Phases, "Verify"))
                {
                    return "（仅验证模式跳过）";
                }
                return "（未启用）";
            }
            if (state == 1 && !string.IsNullOrEmpty(HotUpdatePipeline.JobText))
            {
                return "（" + HotUpdatePipeline.JobText + "）";
            }
            if (phase == "AbBuild" && !string.IsNullOrEmpty(HotUpdatePipeline.CurrentVersion))
            {
                return "（v" + HotUpdatePipeline.CurrentVersion + "）";
            }
            return "";
        }

        private static void Reveal(string path)
        {
            if (string.IsNullOrEmpty(path))
            {
                return;
            }
            if (File.Exists(path) || Directory.Exists(path))
            {
                EditorUtility.RevealInFinder(path);
            }
            else
            {
                Debug.LogWarning("[HotUpdate] 路径还不存在：" + path);
            }
        }
    }
}
