//------------------------------------------------------------------------------
// 预制体 Missing Script 批量清理工具（核心逻辑）
//
// 功能：选中一个（或多个）文件夹后，递归遍历其下所有 .prefab，
//       移除每个预制体上（含所有子物体、含未激活物体）的 Missing Script 组件。
//
// 入口见文件底部的 MenuItem 区域，也可从 MissingScriptCleanerWindow 面板调用。
//------------------------------------------------------------------------------
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using UnityEditor;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 单个预制体的处理结果
    /// </summary>
    public class CleanResult
    {
        /// <summary>预制体资源路径（Assets/...xxx.prefab）</summary>
        public string AssetPath;

        /// <summary>本次移除的 Missing Script 组件数量</summary>
        public int RemovedCount;

        /// <summary>失败原因，为空表示成功</summary>
        public string Error;

        /// <summary>是否被跳过（例如 FBX 模型预制体不可编辑）</summary>
        public bool IsSkipped;

        /// <summary>跳过原因</summary>
        public string SkipReason;

        /// <summary>是否为预制体变体（Prefab Variant），保存后建议在版本控制中复核差异</summary>
        public bool IsVariant;

        /// <summary>是否属于“需要关注”的条目（有改动或出错）</summary>
        public bool HasChange { get { return RemovedCount > 0 || !string.IsNullOrEmpty(Error); } }
    }

    /// <summary>
    /// 一次批量清理任务的汇总报告
    /// </summary>
    public class CleanReport
    {
        /// <summary>是否为预览模式（只扫描不修改）</summary>
        public bool DryRun;

        /// <summary>是否被用户中途取消</summary>
        public bool Canceled;

        /// <summary>实际扫描到的预制体数量</summary>
        public int Scanned;

        /// <summary>被修改并保存的预制体数量</summary>
        public int Modified;

        /// <summary>累计移除的 Missing Script 组件数量</summary>
        public int RemovedTotal;

        /// <summary>处理失败的预制体数量</summary>
        public int Failed;

        /// <summary>被跳过的预制体数量</summary>
        public int Skipped;

        /// <summary>耗时（毫秒）</summary>
        public double ElapsedMs;

        /// <summary>扫描的根路径（用于展示）</summary>
        public readonly List<string> Roots = new List<string>();

        /// <summary>明细列表（含改动项、失败项、跳过项）</summary>
        public readonly List<CleanResult> Details = new List<CleanResult>();

        /// <summary>生成一段人类可读的汇总文案</summary>
        public string Describe()
        {
            var sb = new StringBuilder();
            sb.AppendLine(string.Format("模式：{0}", DryRun ? "预览扫描（未修改任何文件）" : "执行清理（已写回磁盘）"));
            if (Roots.Count > 0)
            {
                sb.AppendLine(string.Format("扫描范围：{0}", string.Join("，", Roots.ToArray())));
            }
            sb.AppendLine(string.Format("扫描预制体：{0} 个", Scanned));
            sb.AppendLine(string.Format("发现 Missing Script：{0} 个", RemovedTotal));
            sb.AppendLine(string.Format("受影响预制体：{0} 个", Modified));
            if (Skipped > 0) sb.AppendLine(string.Format("跳过：{0} 个", Skipped));
            if (Failed > 0) sb.AppendLine(string.Format("失败：{0} 个", Failed));
            if (Canceled) sb.AppendLine("提示：任务被手动取消，未处理的预制体保持原样。");
            sb.AppendLine(string.Format("耗时：{0:F0} ms", ElapsedMs));
            return sb.ToString().TrimEnd();
        }
    }

    /// <summary>
    /// 预制体 Missing Script 清理器
    /// </summary>
    public static class MissingScriptCleaner
    {
        /// <summary>上一次执行的结果，供结果面板读取</summary>
        public static CleanReport LastReport;

        #region 菜单入口

        [MenuItem("Tools/资源工具/清理预制体 Missing Script/打开清理面板", false, 0)]
        public static void OpenWindow()
        {
            MissingScriptCleanerWindow.ShowWindow();
        }

        /// <summary>菜单入口一：清理 Project 窗口中选中的文件夹（支持多选）</summary>
        [MenuItem("Tools/资源工具/清理预制体 Missing Script/清理 Project 窗口中选中的文件夹", false, 10)]
        public static void CleanFromSelection()
        {
            List<string> paths = GetSelectedAssetPaths();
            if (paths.Count == 0)
            {
                EditorUtility.DisplayDialog("未选中文件夹",
                    "请先在 Project 窗口中选中一个（或多个）文件夹，再执行该命令。", "知道了");
                return;
            }
            RunWithConfirm(paths, false, true);
        }

        [MenuItem("Tools/资源工具/清理预制体 Missing Script/清理 Project 窗口中选中的文件夹", true)]
        private static bool ValidateCleanFromSelection()
        {
            return GetSelectedAssetPaths().Count > 0;
        }

        /// <summary>
        /// 菜单入口二：Project 窗口右键菜单（对选中的文件夹 / 预制体直接生效）
        /// </summary>
        [MenuItem("Assets/清理选中项中的 Missing Script", false, 1000)]
        public static void CleanFromContextMenu()
        {
            List<string> paths = GetSelectedAssetPaths();
            if (paths.Count == 0)
            {
                EditorUtility.DisplayDialog("未选中资源",
                    "请在 Project 窗口中选中需要处理的文件夹或预制体。", "知道了");
                return;
            }
            RunWithConfirm(paths, false, true);
        }

        [MenuItem("Assets/清理选中项中的 Missing Script", true)]
        private static bool ValidateCleanFromContextMenu()
        {
            return GetSelectedAssetPaths().Count > 0;
        }

        /// <summary>
        /// 菜单入口三：只扫描不修改，用于执行前评估影响范围
        /// </summary>
        [MenuItem("Tools/资源工具/清理预制体 Missing Script/预览扫描（不修改文件）", false, 11)]
        public static void PreviewFromSelection()
        {
            List<string> paths = GetSelectedAssetPaths();
            if (paths.Count == 0)
            {
                EditorUtility.DisplayDialog("未选中文件夹",
                    "请先在 Project 窗口中选中一个（或多个）文件夹，再执行该命令。", "知道了");
                return;
            }
            RunAndReport(paths, true, true, true);
        }

        #endregion

        #region 对外调用接口

        /// <summary>
        /// 带确认弹窗地执行清理
        /// </summary>
        public static void RunWithConfirm(List<string> assetPaths, bool dryRun, bool showResultDialog)
        {
            string message = dryRun
                ? "即将递归遍历所选范围下的全部预制体，统计其中的 Missing Script 组件数量。\n\n此过程不会修改任何文件。是否继续？"
                : "即将递归遍历所选范围下的全部预制体，并移除其中的 Missing Script 组件。\n\n"
                  + "该操作会直接写回 .prefab 文件，且无法通过 Ctrl+Z 撤销，建议先提交一次版本控制。\n\n是否继续？";

            if (!EditorUtility.DisplayDialog(dryRun ? "预览扫描" : "确认清理", message, "开始执行", "取消"))
            {
                return;
            }
            RunAndReport(assetPaths, dryRun, true, showResultDialog);
        }

        /// <summary>
        /// 执行清理并在结束后弹出结果提示
        /// </summary>
        /// <param name="assetPaths">文件夹路径或 .prefab 资源路径（可混合）</param>
        /// <param name="dryRun">true = 只扫描统计，不写回文件</param>
        /// <param name="verbose">是否输出每个预处理文件的日志</param>
        /// <param name="showDialog">是否在结束后弹出汇总对话框</param>
        public static CleanReport RunAndReport(List<string> assetPaths, bool dryRun, bool verbose, bool showDialog)
        {
            CleanReport report = Run(assetPaths, dryRun, verbose);
            LastReport = report;

            if (!showDialog)
            {
                return report;
            }

            StringBuilder sb = new StringBuilder();
            sb.AppendLine(report.Describe());
            if (report.Details.Count > 0)
            {
                sb.AppendLine();
                sb.AppendLine("详情请查看 Console 日志，或点击“查看详情”打开结果面板。");
            }

            bool openDetail = EditorUtility.DisplayDialog(
                dryRun ? "预览扫描完成" : "清理完成",
                sb.ToString(),
                "查看详情", "关闭");

            if (openDetail)
            {
                MissingScriptCleanerWindow.ShowWindow();
            }
            return report;
        }

        /// <summary>
        /// 核心执行逻辑：收集预制体 → 逐个处理 → 生成报告
        /// </summary>
        public static CleanReport Run(List<string> assetPaths, bool dryRun, bool verbose)
        {
            CleanReport report = new CleanReport();
            report.DryRun = dryRun;

            Stopwatch watch = Stopwatch.StartNew();

            if (assetPaths == null || assetPaths.Count == 0)
            {
                watch.Stop();
                report.ElapsedMs = watch.Elapsed.TotalMilliseconds;
                Debug.LogWarning("[MissingScript清理] 没有传入任何路径，任务结束。");
                return report;
            }

            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Debug.LogWarning("[MissingScript清理] 当前处于运行模式，建议退出 Play 模式后再执行，以免资源被运行时占用。");
            }

            // 收集（去重 + 排序，保证结果稳定可复现）
            List<string> prefabPaths = CollectPrefabPaths(assetPaths, report);

            report.Scanned = prefabPaths.Count;
            Debug.Log(string.Format("[MissingScript清理] 开始{0}，共 {1} 个预制体。",
                dryRun ? "预览扫描" : "清理", report.Scanned));

            try
            {
                ProcessAllPrefabs(prefabPaths, report, dryRun, verbose);
            }
            finally
            {
                // 无论成功、失败还是被用户取消，都必须收起进度条
                EditorUtility.ClearProgressBar();
            }

            if (!dryRun && report.Modified > 0)
            {
                AssetDatabase.SaveAssets();
                AssetDatabase.Refresh();
            }

            watch.Stop();
            report.ElapsedMs = watch.Elapsed.TotalMilliseconds;

            // 汇总日志（content 末尾附带 Console 可点击的上下文对象）
            Debug.Log(string.Format("[MissingScript清理] ===== 任务结束 =====\n{0}", report.Describe()));

            return report;
        }

        /// <summary>
        /// 逐个处理预制体并写入报告（进度条由调用方统一收起）
        /// </summary>
        private static void ProcessAllPrefabs(List<string> prefabPaths, CleanReport report, bool dryRun, bool verbose)
        {
            int index = 0;
            foreach (string path in prefabPaths)
            {
                index++;

                // 可取消的进度条，避免大批量处理时界面假死
                bool canceled = EditorUtility.DisplayCancelableProgressBar(
                    dryRun ? "预览扫描 Missing Script" : "清理 Missing Script",
                    string.Format("{0}/{1}  {2}", index, report.Scanned, path),
                    (float)index / Mathf.Max(1, report.Scanned));

                if (canceled)
                {
                    report.Canceled = true;
                    Debug.LogWarning(string.Format("[MissingScript清理] 已被手动取消，已处理 {0}/{1} 个预制体。",
                        index - 1, report.Scanned));
                    break;
                }

                CleanResult result = ProcessPrefab(path, dryRun);
                report.Details.Add(result);

                if (result.IsSkipped)
                {
                    report.Skipped++;
                    if (verbose && !string.IsNullOrEmpty(result.SkipReason))
                    {
                        Debug.Log(string.Format("[MissingScript清理] 已跳过（{0}）：{1}", result.SkipReason, path));
                    }
                    continue;
                }

                if (!string.IsNullOrEmpty(result.Error))
                {
                    report.Failed++;
                    Debug.LogError(string.Format("[MissingScript清理] 处理失败：{0}\n原因：{1}", path, result.Error),
                        AssetDatabase.LoadAssetAtPath<GameObject>(path));
                    continue;
                }

                if (result.RemovedCount > 0)
                {
                    report.Modified++;
                    report.RemovedTotal += result.RemovedCount;

                    if (dryRun)
                    {
                        Debug.LogWarning(string.Format("[MissingScript清理] 预览：该预制体存在 {0} 个 Missing Script（未修改）",
                            result.RemovedCount), AssetDatabase.LoadAssetAtPath<GameObject>(path));
                    }
                    else
                    {
                        Debug.LogWarning(string.Format("[MissingScript清理] 已移除 {0} 个 Missing Script",
                            result.RemovedCount), AssetDatabase.LoadAssetAtPath<GameObject>(path));
                    }
                }
                else if (verbose)
                {
                    Debug.Log(string.Format("[MissingScript清理] 干净，无需处理：{0}", path));
                }
            }
        }

        #endregion

        #region 内部实现

        /// <summary>
        /// 把“文件夹 + 预制体文件”的混合输入展开为去重后的预制体路径列表
        /// </summary>
        private static List<string> CollectPrefabPaths(List<string> assetPaths, CleanReport report)
        {
            HashSet<string> set = new HashSet<string>();

            foreach (string raw in assetPaths)
            {
                if (string.IsNullOrEmpty(raw))
                {
                    continue;
                }

                string path = raw.Replace('\\', '/').TrimEnd('/');

                if (AssetDatabase.IsValidFolder(path))
                {
                    if (!report.Roots.Contains(path))
                    {
                        report.Roots.Add(path);
                    }

                    // FindAssets 默认递归搜索子文件夹
                    string[] guids = AssetDatabase.FindAssets("t:Prefab", new string[] { path });
                    foreach (string guid in guids)
                    {
                        string assetPath = AssetDatabase.GUIDToAssetPath(guid);
                        if (IsPrefabFile(assetPath))
                        {
                            set.Add(assetPath);
                        }
                    }
                }
                else if (IsPrefabFile(path))
                {
                    string folder = System.IO.Path.GetDirectoryName(path).Replace('\\', '/');
                    if (!report.Roots.Contains(folder))
                    {
                        report.Roots.Add(folder);
                    }
                    set.Add(path);
                }
                else
                {
                    Debug.LogWarning(string.Format("[MissingScript清理] 忽略无效路径：{0}", raw));
                }
            }

            List<string> list = new List<string>(set);
            list.Sort(StringComparer.OrdinalIgnoreCase);
            return list;
        }

        /// <summary>判断是否为 .prefab 资源</summary>
        private static bool IsPrefabFile(string assetPath)
        {
            return !string.IsNullOrEmpty(assetPath)
                   && assetPath.EndsWith(".prefab", StringComparison.OrdinalIgnoreCase);
        }

        /// <summary>
        /// 处理单个预制体：加载内容 → 统计 → 移除 → 保存
        /// </summary>
        private static CleanResult ProcessPrefab(string path, bool dryRun)
        {
            CleanResult result = new CleanResult { AssetPath = path };

            // 模型预制体（FBX 导入产生）属于只读资源，无法就地编辑，直接跳过
            GameObject asset = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (asset == null)
            {
                result.IsSkipped = true;
                result.SkipReason = "资源缺失或无法加载";
                return result;
            }

            PrefabAssetType assetType = PrefabUtility.GetPrefabAssetType(asset);
            if (assetType == PrefabAssetType.Model)
            {
                result.IsSkipped = true;
                result.SkipReason = "模型预制体（FBX 导入，只读）";
                return result;
            }
            if (assetType == PrefabAssetType.NotAPrefab || assetType == PrefabAssetType.MissingAsset)
            {
                result.IsSkipped = true;
                result.SkipReason = "不是有效的预制体资源";
                return result;
            }
            result.IsVariant = assetType == PrefabAssetType.Variant;

            GameObject contents = null;
            try
            {
                // 以“预制体内容”方式打开，可直接修改并写回资源文件
                contents = PrefabUtility.LoadPrefabContents(path);

                int before = CountMissingScripts(contents);

                if (dryRun)
                {
                    result.RemovedCount = before;
                    return result;
                }

                if (before == 0)
                {
                    result.RemovedCount = 0;
                    return result;
                }

                // 官方 API：按 GameObject 逐个清理，含未激活物体
                Transform[] all = contents.GetComponentsInChildren<Transform>(true);
                for (int i = 0; i < all.Length; i++)
                {
                    GameObjectUtility.RemoveMonoBehavioursWithMissingScript(all[i].gameObject);
                }

                int after = CountMissingScripts(contents);
                result.RemovedCount = Mathf.Max(0, before - after);

                if (result.RemovedCount > 0)
                {
                    bool success;
                    PrefabUtility.SaveAsPrefabAsset(contents, path, out success);
                    if (!success)
                    {
                        result.Error = "保存预制体失败（SaveAsPrefabAsset 返回 false），文件可能被版本控制锁定或只读。";
                    }
                    else if (result.IsVariant)
                    {
                        Debug.LogWarning(string.Format(
                            "[MissingScript清理] 该资源是预制体变体（Variant），已就地保存，建议在版本控制中复核其与基预制体的继承关系是否正常：{0}",
                            path), AssetDatabase.LoadAssetAtPath<GameObject>(path));
                    }
                }
            }
            catch (Exception ex)
            {
                result.Error = ex.Message;
            }
            finally
            {
                // 必须配对释放，否则会在预览场景中泄漏对象
                if (contents != null)
                {
                    PrefabUtility.UnloadPrefabContents(contents);
                }
            }

            return result;
        }

        /// <summary>
        /// 统计 GameObject 及其所有子物体上的 Missing Script 数量。
        /// 通过 SerializedObject 遍历 m_Component 数组，遇到空引用即为残留脚本，
        /// 该方式不依赖具体 Unity 版本，比反射更稳定。
        /// </summary>
        private static int CountMissingScripts(GameObject root)
        {
            int count = 0;
            Transform[] all = root.GetComponentsInChildren<Transform>(true);

            for (int i = 0; i < all.Length; i++)
            {
                SerializedObject so = new SerializedObject(all[i].gameObject);
                SerializedProperty components = so.FindProperty("m_Component");
                if (components == null)
                {
                    continue;
                }
                for (int j = 0; j < components.arraySize; j++)
                {
                    SerializedProperty element = components.GetArrayElementAtIndex(j);
                    if (element.objectReferenceValue == null)
                    {
                        count++;
                    }
                }
            }
            return count;
        }

        /// <summary>
        /// 读取 Project 窗口中当前选中的资源路径（文件夹与预制体均可）
        /// </summary>
        public static List<string> GetSelectedAssetPaths()
        {
            List<string> list = new List<string>();
            UnityEngine.Object[] selected = Selection.GetFiltered(typeof(UnityEngine.Object), SelectionMode.Assets);
            foreach (UnityEngine.Object obj in selected)
            {
                string path = AssetDatabase.GetAssetPath(obj);
                if (!string.IsNullOrEmpty(path) && (AssetDatabase.IsValidFolder(path) || IsPrefabFile(path)))
                {
                    list.Add(path);
                }
            }
            return list;
        }

        #endregion
    }
}
