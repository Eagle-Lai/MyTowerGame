using System.Diagnostics;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 在 Unity 内直接导出配置表（Luban），不必再去双击 Luban\gen_code_json.bat。
    ///
    /// 【为什么不能直接调 bat】bat 末尾有 `pause`，用 Process 调它会在"请按任意键继续"处
    /// 永久挂起。所以这里直接调 Luban 的 exe，并把 bat 里的关键设置复刻过来：
    ///   · 环境变量 DOTNET_ROLL_FORWARD=LatestMajor（本机只有 .NET 8/10 时必需）
    ///   · `-j cfg -c .cache.meta --` 的参数顺序（job 参数必须在 `--` 之后，
    ///     否则报 "unknown argument:-d"）
    ///   · 数据输出到 Assets/ConfigJson（原因见 gen_code_json.bat 顶部注释）
    ///
    /// 导出成功后会自动 AssetDatabase.Refresh()，让新表立刻生效。
    ///
    /// 菜单：Tools ▸ 塔防 ▸ 3. 导出配置表（Luban）
    /// </summary>
    public static class LubanExporter
    {
        private const string LubanExe = "Luban/Tools/Luban.ClientServer/Luban.ClientServer.exe";
        private const string CacheMeta = "Luban/.cache.meta";
        private const string RootXml = "Luban/Config/Defines/__root__.xml";
        private const string DataDir = "Luban/Config/Datas";
        private const string OutCodeDir = "Assets/Gen";
        private const string OutDataDir = "Assets/ConfigJson";

        /// <summary>Luban 正常 1~2 秒跑完，给 120 秒兜底（首次可能要预热）</summary>
        private const int TimeoutMs = 120000;

        [MenuItem("Tools/塔防/3. 导出配置表（Luban）", false, 103)]
        public static void ExportFromMenu()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            bool ok = ExportInternal(report);
            AssetDatabase.Refresh();

            UnityEngine.Debug.Log("[Luban] 导出" + (ok ? "成功" : "失败") + "：\n" + report.Text);
            EditorUtility.DisplayDialog("导出配置表",
                string.Format("{0}\n\n{1}", ok ? "完成" : "失败，请查看 Console", report.Text), "好");
        }

        /// <summary>供一键向导调用（不弹窗）。失败返回 false 并已写入 report。</summary>
        public static bool ExportInternal(EditorUtil.Report report)
        {
            report.Head("导出配置表（Luban）");

            string projectRoot = System.IO.Directory.GetParent(Application.dataPath).FullName;
            string exe = System.IO.Path.Combine(projectRoot, LubanExe.Replace('/', '\\'));

            // 前置校验：工具 / 定义 / 源表目录，缺一个都不用往下走
            if (!System.IO.File.Exists(exe))
            {
                report.Error("找不到 Luban 工具：" + LubanExe);
                return false;
            }
            if (!System.IO.File.Exists(System.IO.Path.Combine(projectRoot, RootXml.Replace('/', '\\'))))
            {
                report.Error("找不到配置定义文件：" + RootXml);
                return false;
            }
            if (!System.IO.Directory.Exists(System.IO.Path.Combine(projectRoot, DataDir.Replace('/', '\\'))))
            {
                report.Error("找不到配置源表目录：" + DataDir);
                return false;
            }
            System.IO.Directory.CreateDirectory(System.IO.Path.Combine(projectRoot, OutDataDir.Replace('/', '\\')));

            string args = string.Format(
                "-j cfg -c \"{0}\" -- -d \"{1}\" --input_data_dir \"{2}\" --output_code_dir \"{3}\" " +
                "--output_data_dir \"{4}\" --gen_types code_cs_unity_json,data_json -s all",
                System.IO.Path.Combine(projectRoot, CacheMeta.Replace('/', '\\')),
                System.IO.Path.Combine(projectRoot, RootXml.Replace('/', '\\')),
                System.IO.Path.Combine(projectRoot, DataDir.Replace('/', '\\')),
                System.IO.Path.Combine(projectRoot, OutCodeDir.Replace('/', '\\')),
                System.IO.Path.Combine(projectRoot, OutDataDir.Replace('/', '\\')));

            StringBuilder output = new StringBuilder();
            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = exe;
            psi.Arguments = args;
            psi.WorkingDirectory = projectRoot;
            psi.UseShellExecute = false;
            psi.RedirectStandardOutput = true;
            psi.RedirectStandardError = true;
            psi.CreateNoWindow = true;
            // 本机若只装了 .NET 8/10，没有这个变量 Luban 会报 "You must install .NET"
            psi.EnvironmentVariables["DOTNET_ROLL_FORWARD"] = "LatestMajor";

            EditorUtility.DisplayProgressBar("导出配置表", "正在运行 Luban…", 0.5f);
            int exitCode;
            try
            {
                using (Process p = Process.Start(psi))
                {
                    p.OutputDataReceived += delegate(object s, DataReceivedEventArgs e)
                    {
                        if (e.Data != null)
                        {
                            lock (output) { output.AppendLine(e.Data); }
                        }
                    };
                    p.ErrorDataReceived += delegate(object s, DataReceivedEventArgs e)
                    {
                        if (e.Data != null)
                        {
                            lock (output) { output.AppendLine(e.Data); }
                        }
                    };
                    p.BeginOutputReadLine();
                    p.BeginErrorReadLine();

                    if (!p.WaitForExit(TimeoutMs))
                    {
                        p.Kill();
                        report.Error("导出超时（超过 " + (TimeoutMs / 1000) + " 秒），已终止进程");
                        return false;
                    }
                    exitCode = p.ExitCode;
                }
            }
            catch (System.Exception ex)
            {
                report.Error("启动 Luban 失败：" + ex.Message);
                return false;
            }
            finally
            {
                EditorUtility.ClearProgressBar();
            }

            // 工具的输出对排查很有用（表缺列、类型不匹配都会在这里），全部落到 Console
            string text = output.ToString();
            if (!string.IsNullOrEmpty(text))
            {
                UnityEngine.Debug.Log("[Luban] 工具输出：\n" + text.TrimEnd());
            }

            if (exitCode != 0)
            {
                report.Error(string.Format("Luban 返回非 0（exitCode={0}），请看上方 [Luban] 工具输出", exitCode));
                return false;
            }

            // 产物自检：8 张表必须都在，且能被当作 TextAsset 读到
            int ok = 0;
            string[] tables = { "tbenemydata", "tbtowerinfo", "tbenemylist", "tbrounddata",
                                "tbsceneinfo", "tbbulletdata", "tblevelmap", "tbglobal" };
            for (int i = 0; i < tables.Length; i++)
            {
                string path = OutDataDir + "/" + tables[i] + ".json";
                if (AssetDatabase.LoadAssetAtPath<TextAsset>(path) == null)
                {
                    report.Error("产物缺失：" + path);
                }
                else
                {
                    ok++;
                }
            }

            if (ok < tables.Length)
            {
                report.Error(string.Format("只产出 {0}/{1} 张表", ok, tables.Length));
                return false;
            }

            AssetDatabase.Refresh();
            report.Ok(string.Format("导出成功：代码 → {0}，数据 → {1}（{2} 张表）",
                OutCodeDir, OutDataDir, ok));
            return true;
        }
    }
}
