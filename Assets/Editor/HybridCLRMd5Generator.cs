using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 生成热更 dll 的 **md5 校验清单**（`md5.txt`），供运行时
    /// <c>FTProject.AOT.HotUpdateDllDownloader</c> 做完整性校验与新版本判定。
    ///
    /// ==================================================================
    /// 【为什么必须有这个文件】
    ///   运行时的 dll 热更链需要回答两个问题，都依赖 md5：
    ///     ① "本地这个 dll 是不是已经和服务器一致？" → 一致就不下载（省流量）
    ///     ② "下下来的这个 dll 是完好的吗？"        → 校验通过才原子替换
    ///   没有清单，这两个问题都无法回答 —— 下载器会**直接放弃更新**
    ///   （宁可这次不更新，也不盲写坏文件）。
    ///
    /// 【产物放哪、怎么上传】
    ///   生成位置：`Assets/StreamingAssets/HybridCLR/md5.txt`
    ///     —— 与 dll 同目录，这样它既随包分发（首包自带，无需联网也能自校验），
    ///        又是"要上传到服务器的那一份"的原点。
    ///   上传方式：把 `Assets/StreamingAssets/HybridCLR/` 下的 **全部文件**
    ///     （11 个 dll + md5.txt）上传到服务器的
    ///     `{服务器根}/{平台}/HybridCLR/` 目录，覆盖旧文件即可。
    ///   例（Android）：
    ///     http://192.168.43.100:8000/Android/HybridCLR/md5.txt
    ///     http://192.168.43.100:8000/Android/HybridCLR/FTProject.Runtime.dll
    ///
    /// 【清单格式】（与运行时 ParseMd5List 严格对应）
    ///     # 由 FTProject 编辑器工具生成，勿手工编辑
    ///     # 平台: Android
    ///     # 生成时间: 2026-10-11T16:40:00Z
    ///     d41d8cd98f00b204e9800998ecf8427e  FTProject.Runtime.dll
    ///     ...
    ///   —— 32 位小写 md5 + **两个空格** + 文件名（兼容 `md5sum` 的习惯格式）。
    ///
    /// 【为什么不扫整个目录，而按名单生成】
    ///   名单来源 = `HybridCLRSettings.asset` 的 hotUpdateAssemblies
    ///   + 本工具的 AOTMetaAssemblies —— 与 HybridCLRDllCopier 完全一致。
    ///   扫目录会把 `.meta`、临时文件之类也扫进去，且无法保证与运行时预期一致。
    /// ==================================================================
    /// </summary>
    public static class HybridCLRMd5Generator
    {
        /// <summary>与 HybridCLRDllCopier / 运行时一致的目录名。</summary>
        private const string DllSubDir = "HybridCLR";

        /// <summary>清单文件名（运行时按此名请求）。</summary>
        private const string Md5FileName = "md5.txt";

        /// <summary>
        /// AOT 补充元数据 dll 的运行期名单。
        /// ⚠️ 与 `HotUpdateAssembler.AOTMetaAssemblies`、
        ///    `HybridCLRDllCopier.AOTMetaAssemblies` **三处必须一致** ——
        ///    编辑器工具不能引用 AOT 程序集，只能手写。
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

        [MenuItem("Tools/塔防/HybridCLR/4. 生成 md5 校验清单（上传服务器用）", false, 303)]
        public static void GenerateFromMenu()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            Generate(report);
            AssetDatabase.Refresh();

            // 【为什么不弹 DisplayDialog】会阻塞 MCP / CI（见 EditorUtil 约定）
            if (report.Errors > 0)
            {
                Debug.LogError("[HybridCLR] 生成 md5 清单失败：\n" + report.Text);
            }
            else
            {
                Debug.Log("[HybridCLR] 生成 md5 清单完成：\n" + report.Text);
            }
        }

        public static void Generate(EditorUtil.Report report)
        {
            report.Head("生成热更 dll 的 md5 校验清单");

            BuildTarget target = EditorUserBuildSettings.activeBuildTarget;
            string dllDir = Path.Combine(Application.dataPath, "StreamingAssets", DllSubDir);

            if (Directory.Exists(dllDir) == false)
            {
                report.Error("找不到目录：" + dllDir
                    + "（请先执行菜单「Tools ▸ 塔防 ▸ HybridCLR ▸ 1. 拷贝热更 dll 到 StreamingAssets」）");
                return;
            }

            // ---------- ① 汇总要纳入清单的文件名 ----------
            List<string> names = new List<string>();

            List<string> hotNames = GetHotUpdateAssemblyNames(report);
            if (hotNames == null || hotNames.Count == 0)
            {
                report.Error("HybridCLRSettings.asset 里 hotUpdateAssemblies 为空，" +
                    "无法确定要纳入清单的热更 dll。");
                return;
            }
            for (int i = 0; i < hotNames.Count; i++)
            {
                names.Add(hotNames[i] + ".dll");
            }
            for (int i = 0; i < AOTMetaAssemblies.Length; i++)
            {
                names.Add(AOTMetaAssemblies[i]);
            }

            // ---------- ② 逐个算 md5 ----------
            var lines = new List<string>();
            lines.Add("# 由 FTProject 编辑器工具生成，勿手工编辑");
            lines.Add("# 平台: " + target);
            lines.Add("# 生成时间: " + DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"));
            lines.Add("# 格式: <32位小写md5><两个空格><文件名>");

            int okCount = 0;
            int missingCount = 0;

            for (int i = 0; i < names.Count; i++)
            {
                string name = names[i];
                string path = Path.Combine(dllDir, name);

                if (File.Exists(path) == false)
                {
                    // 缺失不写成错误：可能是该平台没编出这个 dll（例如 AOT 元数据没 Generate/All）。
                    // 但必须**显式告警**，否则运行时会出现"清单里没有 → 跳过更新"的静默行为。
                    report.Warn("清单跳过（文件不存在）：" + name);
                    missingCount++;
                    continue;
                }

                string md5;
                long size;
                try
                {
                    md5 = ComputeMd5(path);
                    size = new FileInfo(path).Length;
                }
                catch (Exception e)
                {
                    report.Error("计算 md5 失败 " + name + "：" + e.Message);
                    continue;
                }

                lines.Add(md5 + "  " + name);
                report.Ok(string.Format("  {0}  {1}  ({2:N0} 字节)", md5, name, size));
                okCount++;
            }

            if (okCount == 0)
            {
                report.Error("没有任何 dll 被纳入清单，未生成 " + Md5FileName);
                return;
            }

            // ---------- ③ 写入 ----------
            string outPath = Path.Combine(dllDir, Md5FileName);
            try
            {
                // 统一用 \n 换行：运行时解析会 Trim 掉 \r，但保持跨平台一致更好读
                File.WriteAllText(outPath, string.Join("\n", lines.ToArray()) + "\n",
                    new UTF8Encoding(false));
            }
            catch (Exception e)
            {
                report.Error("写入 " + outPath + " 失败：" + e.Message);
                return;
            }

            report.Ok(string.Format("  已生成：Assets/StreamingAssets/{0}/{1}（{2} 条记录）",
                DllSubDir, Md5FileName, okCount));
            if (missingCount > 0)
            {
                report.Warn(string.Format("  有 {0} 个 dll 缺失未纳入清单（见上方 Warning）", missingCount));
            }

            // ---------- ④ 上传指引 ----------
            string platformFolder = target.ToString();
            report.Ok("  —— 上传指引 ——");
            report.Ok(string.Format("  把 Assets/StreamingAssets/{0}/ 下的 dll 与 {1} 一起上传到服务器：",
                DllSubDir, Md5FileName));
            report.Ok(string.Format("    {{服务器根}}/{0}/{1}/", platformFolder, DllSubDir));
            report.Ok(string.Format("  ⚠️ 只传 dll 不传 {0} → 客户端会放弃更新（宁可不动也不盲写）。", Md5FileName));
        }

        /// <summary>
        /// 读 HybridCLRSettings.asset 里的 hotUpdateAssemblies（反射读取，不直接依赖 HybridCLR.Editor）。
        /// 与 HybridCLRDllCopier 的实现保持一致 —— 若要改，两处一起改。
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
            var list = new List<string>();
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

        /// <summary>流式计算文件 md5，返回 32 位小写十六进制。</summary>
        private static string ComputeMd5(string path)
        {
            using (var md5 = MD5.Create())
            using (var stream = File.OpenRead(path))
            {
                byte[] hash = md5.ComputeHash(stream);
                var sb = new StringBuilder(hash.Length * 2);
                for (int i = 0; i < hash.Length; i++)
                {
                    sb.Append(hash[i].ToString("x2"));
                }
                return sb.ToString();
            }
        }
    }
}
