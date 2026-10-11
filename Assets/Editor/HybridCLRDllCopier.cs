using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// HybridCLR 热更产物搬运工具。
    ///
    /// ==================================================================
    /// 【为什么需要这个工具】
    ///   `HybridCLR ▸ Generate ▸ All` 把热更 dll 编译到
    ///      HybridCLRData/HotUpdateDlls/{平台}/
    ///   这个目录**不在 Assets 下**，不会被 Unity 打进包体，运行时的
    ///   `Application.streamingAssetsPath` 里根本没有这些 dll。
    ///
    ///   所以需要在打包前把它们拷进 `Assets/StreamingAssets/HybridCLR/`，
    ///   运行时由 HotUpdateAssembler.ReadDllBytes 的 ② 分支读到。
    ///
    /// 【为什么 dll 名单从这个文件里来，而不是再写一份】
    ///   热更 dll 名单在运行时侧是 `FTProject.AOT.HotUpdateAssembler.HotUpdateAssemblies`，
    ///   编辑器侧**不能直接引用它**（会引入 FTProject.AOT 依赖，且它是 AOT 程序集，
    ///   编辑器工具引用它虽然可以，但会绕开"编辑器工具只依赖 Runtime"的既有分层）。
    ///   所以这里用菜单交互时**从磁盘扫描**：把 HybridCLRData 里编译出来的、
    ///   且属于本工程热更集的 dll 拷过去。
    ///   判定依据 = HybridCLRSettings.asset 的 hotUpdateAssemblies 列表（唯一权威来源）。
    /// ==================================================================
    /// </summary>
    public static class HybridCLRDllCopier
    {
        /// <summary>拷入 StreamingAssets 后的子目录名（运行时按此路径读）。</summary>
        private const string DestSubDir = "HybridCLR";

        [MenuItem("Tools/塔防/HybridCLR/1. 拷贝热更 dll 到 StreamingAssets", false, 300)]
        public static void CopyFromMenu()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            Copy(report);
            AssetDatabase.Refresh();
            // 【为什么不弹 DisplayDialog】弹窗会阻塞自动化脚本（MCP / CI）的继续执行。
            // 结果全部打进 Console 即可，需要看细节时去 Console 查。
            if (report.Errors > 0)
            {
                Debug.LogError("[HybridCLR] 拷贝热更 dll 失败：\n" + report.Text);
            }
            else
            {
                Debug.Log("[HybridCLR] 拷贝热更 dll：\n" + report.Text);
            }
        }

        public static void Copy(EditorUtil.Report report)
        {
            report.Head("拷贝 HybridCLR 热更 dll");

            // ① 取当前 build target 对应的编译输出目录
            BuildTarget target = EditorUserBuildSettings.activeBuildTarget;
            string srcDir = Path.Combine("HybridCLRData/HotUpdateDlls", target.ToString());

            if (!Directory.Exists(srcDir))
            {
                report.Error("找不到热更 dll 编译目录：" + srcDir
                    + "（请先执行菜单「HybridCLR ▸ Generate ▸ All」）");
                return;
            }

            // ② 取热更程序集名单（权威来源 = HybridCLRSettings.asset）
            List<string> names = GetHotUpdateAssemblyNames(report);
            if (names == null || names.Count == 0)
            {
                report.Error("HybridCLRSettings.asset 里 hotUpdateAssemblies 为空，" +
                    "请先在「HybridCLR ▸ Settings」里配置热更程序集。");
                return;
            }

            // ③ 拷贝热更 dll
            string dstDir = Path.Combine(Application.dataPath, "StreamingAssets", DestSubDir);
            Directory.CreateDirectory(dstDir);

            int hotCopied = 0;
            for (int i = 0; i < names.Count; i++)
            {
                string dllName = names[i] + ".dll";
                string src = Path.Combine(srcDir, dllName);
                if (!File.Exists(src))
                {
                    report.Error("缺少 dll：" + src + "（该程序集可能未被编译，检查 HybridCLRSettings 是否写错名字）");
                    continue;
                }

                string dst = Path.Combine(dstDir, dllName);
                File.Copy(src, dst, true);

                long size = new FileInfo(dst).Length;
                report.Ok(string.Format("  [热更] {0}  ({1:N0} 字节)", dllName, size));
                hotCopied++;
            }

            report.Ok(string.Format(
                "  目标目录：Assets/StreamingAssets/{0}/（热更 {1} 个 dll）",
                DestSubDir, hotCopied));

            // ④ 拷贝 AOT 补充元数据 dll（★ 必须做，否则 AOT 泛型缺失）
            //    源 = HybridCLRData/AssembliesPostIl2CppStrip/{平台}/，也是 Generate/All 的产物。
            CopyAOTMeta(report, target, dstDir);

            // ⑤ 顺带核对名单同步（名单写岔 = 真机泛型缺失且报错晦涩）
            CheckAOTMetaSync(report);
        }

        /// <summary>
        /// AOT 补充元数据 dll 的运行期名单（与 HotUpdateAssembler.AOTMetaAssemblies 一致）。
        ///
        /// 【为什么编辑器侧要再写一份】编辑器工具不能引用 `FTProject.AOT`（AOT 程序集），
        ///   否则会绕开"编辑器工具只依赖 Runtime"的分层约定。
        ///   → 两份名单必须手工同步，所以下面 CheckAOTMetaSync 会主动比对
        ///     `AOTGenericReferences.cs` 里的 PatchedAOTAssemblyList，不一致就报警。
        ///
        /// ⚠️ 改这里 / 改 HotUpdateAssembler 时必须两边一起改。
        /// </summary>
        private static readonly string[] AOTMetaAssemblies =
        {
            "System.Core.dll",
            "UnityEngine.AssetBundleModule.dll",
            "UnityEngine.CoreModule.dll",
            "UnityEngine.JSONSerializeModule.dll",
            "YooAsset.dll",
            "mscorlib.dll",
        };

        private static void CopyAOTMeta(EditorUtil.Report report, BuildTarget target, string dstDir)
        {
            report.Head("拷贝 HybridCLR AOT 补充元数据 dll");

            string srcDir = Path.Combine("HybridCLRData/AssembliesPostIl2CppStrip", target.ToString());
            if (!Directory.Exists(srcDir))
            {
                report.Warn("找不到 AOT 裁剪产物目录：" + srcDir
                    + "（需先执行「HybridCLR ▸ Generate ▸ All」）");
                return;
            }

            int copied = 0;
            for (int i = 0; i < AOTMetaAssemblies.Length; i++)
            {
                string dllName = AOTMetaAssemblies[i];
                string src = Path.Combine(srcDir, dllName);
                if (!File.Exists(src))
                {
                    report.Warn("AOT 元数据 dll 缺失（名单写了但 Generate/All 未产出）：" + dllName
                        + "  —— 请核对名单是否与 AOTGenericReferences.cs 一致");
                    continue;
                }

                File.Copy(src, Path.Combine(dstDir, dllName), true);
                report.Ok(string.Format("  [AOT ] {0}  ({1:N0} 字节)",
                    dllName, new FileInfo(src).Length));
                copied++;
            }

            report.Ok(string.Format("  AOT 补充元数据：{0}/{1} 个已就位",
                copied, AOTMetaAssemblies.Length));
        }

        /// <summary>
        /// 核对本工具的 AOTMetaAssemblies 与 `AOTGenericReferences.cs` 的
        /// `PatchedAOTAssemblyList` 是否一致。不一致 = 真机泛型缺失风险。
        /// </summary>
        private static void CheckAOTMetaSync(EditorUtil.Report report)
        {
            const string refPath = "Assets/HybridCLRGenerate/AOTGenericReferences.cs";
            string full = Path.Combine(Directory.GetCurrentDirectory(), refPath);
            if (!File.Exists(full))
            {
                report.Warn("找不到 " + refPath + "（需先执行「HybridCLR ▸ Generate ▸ All」）");
                return;
            }

            string text;
            try
            {
                text = File.ReadAllText(full);
            }
            catch (Exception e)
            {
                report.Warn("读取 " + refPath + " 失败：" + e.Message);
                return;
            }

            // 抓 PatchedAOTAssemblyList = new List<string> { "a", "b", ... } 里的字符串
            List<string> expected = new List<string>();
            int listStart = text.IndexOf("PatchedAOTAssemblyList", StringComparison.Ordinal);
            if (listStart >= 0)
            {
                int braceOpen = text.IndexOf('{', listStart);
                int braceClose = braceOpen >= 0 ? text.IndexOf('}', braceOpen) : -1;
                if (braceOpen >= 0 && braceClose > braceOpen)
                {
                    string body = text.Substring(braceOpen + 1, braceClose - braceOpen - 1);
                    int p = 0;
                    while (true)
                    {
                        int q1 = body.IndexOf('"', p);
                        if (q1 < 0) break;
                        int q2 = body.IndexOf('"', q1 + 1);
                        if (q2 < 0) break;
                        expected.Add(body.Substring(q1 + 1, q2 - q1 - 1));
                        p = q2 + 1;
                    }
                }
            }

            if (expected.Count == 0)
            {
                report.Warn("未能从 " + refPath + " 解析出 PatchedAOTAssemblyList（格式可能变了）");
                return;
            }

            // 双向差集
            List<string> onlyInRef = new List<string>();
            List<string> onlyInCode = new List<string>();
            for (int i = 0; i < expected.Count; i++)
            {
                if (Array.IndexOf(AOTMetaAssemblies, expected[i]) < 0) onlyInRef.Add(expected[i]);
            }
            for (int i = 0; i < AOTMetaAssemblies.Length; i++)
            {
                if (expected.IndexOf(AOTMetaAssemblies[i]) < 0) onlyInCode.Add(AOTMetaAssemblies[i]);
            }

            if (onlyInRef.Count == 0 && onlyInCode.Count == 0)
            {
                report.Ok(string.Format(
                    "  AOT 元数据名单与 AOTGenericReferences.cs 一致（{0} 项）", expected.Count));
            }
            else
            {
                if (onlyInRef.Count > 0)
                {
                    report.Warn("AOTGenericReferences 里有、但本工具/加载器名单里没有（会导致泛型缺失）："
                        + string.Join(", ", onlyInRef.ToArray()));
                }
                if (onlyInCode.Count > 0)
                {
                    report.Warn("本工具/加载器名单里有、但 AOTGenericReferences 里没有（多余项）："
                        + string.Join(", ", onlyInCode.ToArray()));
                }
                report.Warn("请同步 HotUpdateAssembler.AOTMetaAssemblies 与 AOTMetaAssemblies（本文件）");
            }
        }

        [MenuItem("Tools/塔防/HybridCLR/3. 拷贝 AOT 补充元数据 dll 到 StreamingAssets", false, 302)]
        public static void CopyAOTMetaFromMenu()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            BuildTarget target = EditorUserBuildSettings.activeBuildTarget;
            string dstDir = Path.Combine(Application.dataPath, "StreamingAssets", DestSubDir);
            Directory.CreateDirectory(dstDir);
            CopyAOTMeta(report, target, dstDir);
            CheckAOTMetaSync(report);
            AssetDatabase.Refresh();

            if (report.Errors > 0)
            {
                Debug.LogError("[HybridCLR] 拷贝 AOT 补充元数据失败：\n" + report.Text);
            }
            else
            {
                Debug.Log("[HybridCLR] 拷贝 AOT 补充元数据：\n" + report.Text);
            }
        }

        /// <summary>
        /// 从 HybridCLRSettings.asset 读热更程序集名（不含 .dll）。
        /// 用反射读字段，避免编辑器工具直接依赖 HybridCLR.Editor 的命名空间
        /// （这样即使 HybridCLR 包临时缺失，本文件也不会编译不过）。
        /// </summary>
        private static List<string> GetHotUpdateAssemblyNames(EditorUtil.Report report)
        {
            string path = "ProjectSettings/HybridCLRSettings.asset";
            UnityEngine.Object[] objs =
                UnityEditorInternal.InternalEditorUtility.LoadSerializedFileAndForget(path);
            if (objs == null || objs.Length == 0)
            {
                report.Error("读不到 " + path);
                return null;
            }

            System.Reflection.FieldInfo f = objs[0].GetType().GetField("hotUpdateAssemblies");
            if (f == null)
            {
                report.Error("HybridCLRSettings 里找不到 hotUpdateAssemblies 字段");
                return null;
            }

            string[] arr = f.GetValue(objs[0]) as string[];
            List<string> list = new List<string>();
            if (arr != null)
            {
                for (int i = 0; i < arr.Length; i++)
                {
                    if (!string.IsNullOrEmpty(arr[i]))
                    {
                        list.Add(arr[i]);
                    }
                }
            }
            return list;
        }

        [MenuItem("Tools/塔防/HybridCLR/2. 查看热更 dll 状态", false, 301)]
        public static void ReportStatus()
        {
            BuildTarget target = EditorUserBuildSettings.activeBuildTarget;
            string srcDir = Path.Combine("HybridCLRData/HotUpdateDlls", target.ToString());
            string dstDir = Path.Combine(Application.dataPath, "StreamingAssets", DestSubDir);

            Debug.Log(string.Format(
                "[HybridCLR] 热更 dll 状态\n" +
                "  当前平台：{0}\n" +
                "  编译输出：{1}（{2}）\n" +
                "  已拷入包：{3}（{4}）",
                target,
                srcDir, Directory.Exists(srcDir) ? "存在" : "缺失",
                dstDir, Directory.Exists(dstDir) ? "存在" : "缺失"));
        }
    }
}
