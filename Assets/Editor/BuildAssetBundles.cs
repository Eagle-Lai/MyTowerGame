using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 打包 AssetBundle（P0-3）。
    ///
    /// 流程：
    ///   ① 检查配置表是否已导出且**能按 TextAsset 读取**（读不到就直接中止）
    ///   ② 按 ResTable 打 AB 标记（唯一数据源，见 ABNameSetter）
    ///   ③ BuildPipeline 构建到 Assets/StreamingAssets/AssetBundles/&lt;平台&gt;/
    ///      【为什么产物放 StreamingAssets】它随包体一起发出、能按平台分目录，
    ///      运行时用 Application.streamingAssetsPath 统一寻址。
    ///      （注意：这是"产物目录"，与"源数据目录" Assets/ConfigJson 不同，
    ///        后者是普通 Assets 目录，会被打进 config 包。）
    ///   ④ 自检：主清单是否存在、每个预期的包是否都产出了
    ///
    /// 菜单：
    ///   Tools ▸ 塔防 ▸ 5. 打包 AssetBundle
    ///   Tools ▸ 塔防 ▸ 高级（单步重建）▸ 5b. 严格模式打包（引用缺失即失败）
    /// </summary>
    public static class BuildAssetBundles
    {
        /// <summary>配置表源数据目录（Luban 的 --output_data_dir）</summary>
        public const string ConfigDir = "Assets/ConfigJson";

        [MenuItem("Tools/塔防/5. 打包 AssetBundle", false, 105)]
        public static void Build()
        {
            BuildInternal(false);
        }

        [MenuItem("Tools/塔防/高级（单步重建）/5b. 严格模式打包（引用缺失即失败）", false, 311)]
        public static void BuildStrict()
        {
            BuildInternal(true);
        }

        private static void BuildInternal(bool strict)
        {
            EditorUtil.Report report = new EditorUtil.Report();

            // ① 先确认配置表已导出（缺了就没必要往下走）
            if (!CheckConfigReady(report))
            {
                Debug.LogError("[M0] 打包中止：配置表未就绪。\n" + report.Text);
                EditorUtility.DisplayDialog("打包 AssetBundle",
                    "中止：配置表未导出。\n\n" + report.Text, "好");
                return;
            }

            // ② 打标（同时会校验 ResTable 里登记的资源是否都存在）
            ABNameSetter.Apply(report);
            if (report.Errors > 0)
            {
                Debug.LogError("[M0] 打包中止：存在未就绪的资源。\n" + report.Text);
                EditorUtility.DisplayDialog("打包 AssetBundle",
                    "中止：ResTable 里有资源不存在。\n\n" + report.Text +
                    "\n\n请先执行「Tools ▸ 塔防 ▸ 一键完成 M0 资源准备」。", "好");
                return;
            }

            // ③ 构建
            string outputDir = ResPathUtil.BuildOutputRoot;
            Directory.CreateDirectory(outputDir);

            BuildAssetBundleOptions options =
                BuildAssetBundleOptions.ChunkBasedCompression |   // LZ4：兼顾压缩率与随机读取
                BuildAssetBundleOptions.UseContentHash;           // 用内容算 hash，构建结果可复现
            // 【命名坑】这个枚举里**没有** `Deterministic` 这个成员（会报 CS0117）。
            // 它历史上叫 `DeterministicAssetBundle`（已废弃），
            // Unity 2022.2+ 的正式写法是 `UseContentHash`。
            if (strict)
            {
                options |= BuildAssetBundleOptions.StrictMode;    // 引用缺失直接失败
            }

            report.Head("构建 AssetBundle → " + outputDir);
            report.Ok("平台目录：" + ResPathUtil.PlatformFolder +
                      "（构建目标 " + EditorUserBuildSettings.activeBuildTarget + "）");

            AssetBundleManifest manifest = BuildPipeline.BuildAssetBundles(
                outputDir, options, EditorUserBuildSettings.activeBuildTarget);

            if (manifest == null)
            {
                report.Error("BuildPipeline 返回 null，打包失败。请查看 Console 上方的详细错误。");
                Debug.LogError("[M0] AssetBundle 打包失败：\n" + report.Text);
                EditorUtility.DisplayDialog("打包 AssetBundle",
                    "失败，请查看 Console。\n\n" + report.Text, "好");
                return;
            }

            // ④ 自检
            string[] built = manifest.GetAllAssetBundles();
            report.Ok(string.Format("成功产出 {0} 个包：", built.Length));
            long totalBytes = 0;
            for (int i = 0; i < built.Length; i++)
            {
                string file = Path.Combine(outputDir, built[i]);
                long size = File.Exists(file) ? new FileInfo(file).Length : 0;
                totalBytes += size;
                report.Ok(string.Format("  · {0,-16} {1,8:F1} KB", built[i], size / 1024f));
            }
            report.Ok(string.Format("合计 {0:F1} KB（含主清单）", totalBytes / 1024f));

            // 每个预期包都必须产出，否则运行时必然报"资源不可用"
            for (int i = 0; i < ResBundle.All.Length; i++)
            {
                bool found = false;
                for (int j = 0; j < built.Length; j++)
                {
                    if (built[j] == ResBundle.All[i])
                    {
                        found = true;
                        break;
                    }
                }
                if (!found)
                {
                    report.Warn(string.Format("预期包「{0}」未产出 —— " +
                        "多半是 ResTable 里该包下的资源都没能打上标", ResBundle.All[i]));
                }
            }

            string manifestFile = Path.Combine(outputDir, ResPathUtil.ManifestBundleName);
            if (!File.Exists(manifestFile))
            {
                report.Error("主清单包缺失：" + manifestFile +
                             "\n  BundleResLoader 启动时会读它，缺了会直接初始化失败");
            }
            else
            {
                report.Ok("主清单包就绪：" + ResPathUtil.ManifestBundleName);
            }

            AssetDatabase.Refresh();
            Debug.Log("[M0] AssetBundle 打包完成：\n" + report.Text);
            EditorUtility.DisplayDialog("打包 AssetBundle",
                string.Format("{0}\n\n{1}",
                    report.Errors > 0 ? "有错误，请查看 Console" : "完成", report.Text), "好");
        }

        // ------------------------------------------------------------------
        // 配置表就绪检查
        // ------------------------------------------------------------------

        /// <summary>
        /// 确认配置表 JSON 已导出、且**能被当作 TextAsset 加载**。
        ///
        /// 【为什么要专门查"能当 TextAsset 加载"】这是踩过的坑：
        /// StreamingAssets 下的文件会被 Unity 当作"原始文件"（DefaultAsset）处理，
        /// 于是 `LoadAssetAtPath&lt;Object&gt;()` 拿得到（自检会误判为"存在"），
        /// 但 `LoadAssetAtPath&lt;TextAsset&gt;()` 返回 null，读配置直接失败。
        /// 所以这里用 TextAsset 类型去查，才能真实反映运行时能否读到内容。
        /// </summary>
        public static bool CheckConfigReady(EditorUtil.Report report)
        {
            report.Head("检查配置表是否已导出");

            List<string> missing = new List<string>();
            int ok = 0;
            foreach (System.Collections.Generic.KeyValuePair<string, ResAddress> kv in ResTable.All)
            {
                ResAddress addr = kv.Value;
                if (addr.Bundle != ResBundle.Config)
                {
                    continue;
                }
                if (AssetDatabase.LoadAssetAtPath<TextAsset>(addr.EditorPath) == null)
                {
                    missing.Add(string.Format("      逻辑名「{0}」→ {1}", kv.Key, addr.EditorPath));
                }
                else
                {
                    ok++;
                }
            }

            if (missing.Count > 0)
            {
                report.Error(string.Format(
                    "有 {0} 张配置表读不到内容（不是有效 TextAsset）：\n{1}\n" +
                    "      修复：执行 Luban/gen_code_json.bat 重新导出（输出目录为 Assets/ConfigJson）",
                    missing.Count, string.Join("\n", missing.ToArray())));
                return false;
            }

            report.Ok(string.Format("{0} 张配置表就绪，且都能按 TextAsset 读取", ok));
            return true;
        }
    }
}
