using System.IO;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 【无人值守·2026-10-14 需求流水线】一键串联：
    ///   ① Luban 导出配置表（Localization.xlsx 新词条 → json + C#）
    ///   ② 生成 GameIntroView.prefab（缺失才建；已存在不碰）
    ///   ③ HudView.prefab 右上角幂等补挂 Btn_Pause / Btn_Intro（不重建、不碰其他节点）
    ///   ④ 批量挂 TextLocalizer（幂等，覆盖新 prefab 与新按钮的 Label）
    ///   ⑤ 交接给 ReporterHotfixBuild（热更 dll ▸ 拷贝+md5 ▸ 收集器 ▸ AB）
    ///
    /// 【触发方式】
    ///   · Library/FT_AUTOBUILD.trigger 写 "feature"（域重载后由 FT_AutoBuildTrigger 消费）；
    ///   · 或菜单 Tools ▸ 塔防 ▸ 自动化（无弹窗）▸ 一键：介绍弹窗+拖拽建造+HUD按钮。
    ///
    /// 【为什么做成状态机】与 ReporterHotfixBuild 同一套防身逻辑：任何阶段若被
    /// 意外的脚本编译/域重载打断，SessionState 里的阶段游标会在重载后原地重跑（幂等），
    /// 宁可多花几秒也不静默用旧产物。
    ///
    /// 【状态文件】Library/FTFeatureBuildStatus.txt：
    ///   START FEATURE → PHASE luban ok → PHASE prefab ok → DONE OK (handoff to ReporterHotfixBuild)
    ///   外部轮询到 DONE OK 后改看 Library/FTReporterBuildStatus.txt 等 DONE。
    /// </summary>
    [InitializeOnLoad]
    public static class FT_FeatureBuild
    {
        private const string PhaseKey = "FTFeatureBuild.Phase";
        private const string StatusFileRelative = "Library/FTFeatureBuildStatus.txt";

        private static string ProjectRoot
        {
            get { return Path.GetDirectoryName(Application.dataPath); }
        }

        private static string StatusFilePath
        {
            get { return Path.Combine(ProjectRoot, StatusFileRelative); }
        }

        [MenuItem("Tools/塔防/自动化（无弹窗）/一键：介绍弹窗+拖拽建造+HUD按钮（Luban▸prefab▸AB）", false, 903)]
        public static void StartFromMenu()
        {
            Start();
        }

        /// <summary>入口（菜单 / FT_AutoBuildTrigger 共用）。</summary>
        public static void Start()
        {
            string phase = GetPhase();
            if (phase != "Idle" && phase != "Done" && phase != "Fail")
            {
                Debug.LogWarning("[FeatureBuild] 已有流水线在跑（" + phase + "），忽略本次 Start。");
                return;
            }

            try { File.Delete(StatusFilePath); }
            catch (System.Exception) { }

            SetPhase("Luban");
            WriteStatus("START FEATURE " + System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss"));
            Debug.Log("[FeatureBuild] 开始：Luban ▸ GameIntro prefab ▸ HUD 右上角按钮 ▸ TextLocalizer ▸ 热更 dll+AB");
        }

        static FT_FeatureBuild()
        {
            EditorApplication.update += Tick;
        }

        private static void Tick()
        {
            string phase = GetPhase();
            if (phase == "Idle" || phase == "Done" || phase == "Fail")
            {
                return;
            }
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
            {
                return;
            }

            try
            {
                switch (phase)
                {
                    case "Luban": TickLuban(); break;
                    case "Prefab": TickPrefab(); break;
                    case "Hotfix": TickHotfix(); break;
                }
            }
            catch (System.Exception e)
            {
                Fail(phase + " 阶段异常：" + e);
            }
        }

        // ------------------------------------------------------------------
        // ① Luban 导出（前置：.workbuddy/tools 的脚本已把新词条写进 Localization.xlsx）
        // ------------------------------------------------------------------

        private static void TickLuban()
        {
            Debug.Log("[FeatureBuild] ① 导出配置表（Luban）…");
            EditorUtil.Report report = new EditorUtil.Report();
            if (!LubanExporter.ExportInternal(report))
            {
                Fail("① Luban 导出失败：\n" + report.Text);
                return;
            }
            SetPhase("Prefab");
            WriteStatus("PHASE luban ok");
            Debug.Log("[FeatureBuild] ① 完成。");
        }

        // ------------------------------------------------------------------
        // ② prefab：新界面（缺失才建）+ HUD 补挂 + 多语言挂载（全部幂等）
        // ------------------------------------------------------------------

        private static void TickPrefab()
        {
            Debug.Log("[FeatureBuild] ② GameIntroView.prefab + HUD 右上角按钮 + TextLocalizer …");
            EditorUtil.Report report = new EditorUtil.Report();

            // GameIntroView.prefab 缺失才生成（幂等；新界面完全由生成器维护）
            UIPrefabBuilder.EnsureGameIntroView(report);

            UIPrefabBuilder.EnsureHudTopRightButtons(report);
            LocalizationPrefabBinder.BindAll(report);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            if (report.Errors > 0)
            {
                Fail("② prefab 阶段失败：\n" + report.Text);
                return;
            }
            Debug.Log("[FeatureBuild] ② 完成：\n" + report.Text);

            SetPhase("Hotfix");
            WriteStatus("PHASE prefab ok");
        }

        // ------------------------------------------------------------------
        // ③ 交接热更流水线（dll + AB）
        // ------------------------------------------------------------------

        private static void TickHotfix()
        {
            SetPhase("Done");
            WriteStatus("DONE OK (handoff to ReporterHotfixBuild)");
            Debug.Log("[FeatureBuild] ✔ 前置步骤全部完成，交接给 ReporterHotfixBuild（dll ▸ AB）…");
            ReporterHotfixBuild.Start();
        }

        // ------------------------------------------------------------------
        // 通用
        // ------------------------------------------------------------------

        private static void Fail(string message)
        {
            SetPhase("Fail");
            Debug.LogError("[FeatureBuild] ✘ 流水线失败：" + message);

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

        private static void WriteStatus(string line)
        {
            try
            {
                File.AppendAllText(StatusFilePath,
                    System.DateTime.Now.ToString("HH:mm:ss") + " " + line + "\n");
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("[FeatureBuild] 状态文件写入失败：" + e.Message);
            }
        }
    }
}
