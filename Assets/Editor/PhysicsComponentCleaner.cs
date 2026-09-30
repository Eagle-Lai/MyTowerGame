using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 移除预制体上的物理组件（P0-4 / 需求 8）。
    ///
    /// 【为什么要删】
    ///   v1.0 的命中判定靠 `OnTriggerEnter`，因此塔和怪身上都挂着 Collider / Rigidbody2D。
    ///   物理系统的宽相与窄相在低端机上是主要 CPU 开销，而且触发器会把
    ///   "谁打中了谁"变成不可控的时序问题。
    ///   v2.1 改成 EnemyGrid 空间哈希 + 距离判定 + 集中式 tick，物理系统完全不再需要。
    ///
    ///   验收标准（DoD）：Profiler 里 Physics / Physics2D 分区恒为 0。
    ///
    /// 菜单：
    ///   Tools ▸ 塔防 ▸ 高级（单步重建）▸ 清理选中预制体的物理组件
    ///   Tools ▸ 塔防 ▸ 高级（单步重建）▸ 清理全部战斗预制体的物理组件
    /// </summary>
    public static class PhysicsComponentCleaner
    {
        /// <summary>战斗预制体所在目录（批量清理用）</summary>
        private static readonly string[] BattlePrefabFolders =
        {
            "Assets/Prefabs/Tower",
            "Assets/Prefabs/Bullet",
            "Assets/Prefabs/Enemy",
        };

        [MenuItem("Tools/塔防/高级（单步重建）/清理选中预制体的物理组件", false, 303)]
        public static void CleanSelected()
        {
            Object[] selection = Selection.objects;
            if (selection == null || selection.Length == 0)
            {
                EditorUtility.DisplayDialog("清理物理组件", "请先在 Project 窗口选中至少一个预制体。", "好");
                return;
            }

            int totalRemoved = 0;
            int fileCount = 0;
            List<string> touched = new List<string>();

            for (int i = 0; i < selection.Length; i++)
            {
                string path = AssetDatabase.GetAssetPath(selection[i]);
                if (string.IsNullOrEmpty(path) || !path.EndsWith(".prefab"))
                {
                    continue;
                }
                int n = StripPhysicsFromAsset(path);
                if (n > 0)
                {
                    totalRemoved += n;
                    fileCount++;
                    touched.Add(string.Format("  · {0}：移除 {1} 个", path, n));
                }
            }

            AssetDatabase.SaveAssets();
            Debug.Log(string.Format("[M0] 物理组件清理完成：{0} 个预制体共移除 {1} 个组件\n{2}",
                fileCount, totalRemoved, string.Join("\n", touched.ToArray())));
            EditorUtility.DisplayDialog("清理物理组件",
                string.Format("完成。\n受影响预制体：{0} 个\n移除组件：{1} 个\n\n详见 Console。",
                    fileCount, totalRemoved), "好");
        }

        [MenuItem("Tools/塔防/高级（单步重建）/清理全部战斗预制体的物理组件", false, 304)]
        public static void CleanAllBattlePrefabs()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            CleanAllInternal(report);
            AssetDatabase.SaveAssets();
            Debug.Log("[M0] 全量物理组件清理：\n" + report.Text);
            EditorUtility.DisplayDialog("清理物理组件",
                string.Format("{0}\n\n{1}",
                    report.Errors > 0 ? "有错误，请查看 Console" : "完成", report.Text), "好");
        }

        /// <summary>供一键向导调用（不弹窗）</summary>
        public static void CleanAllInternal(EditorUtil.Report report)
        {
            report.Head("清理战斗预制体的物理组件");
            int files = 0;
            int total = 0;

            for (int d = 0; d < BattlePrefabFolders.Length; d++)
            {
                string folder = BattlePrefabFolders[d];
                if (!AssetDatabase.IsValidFolder(folder))
                {
                    continue;
                }
                string[] guids = AssetDatabase.FindAssets("t:Prefab", new[] { folder });
                for (int i = 0; i < guids.Length; i++)
                {
                    string path = AssetDatabase.GUIDToAssetPath(guids[i]);
                    // 跳过备份目录里的 UGUI 源文件
                    if (path.Contains("/_UI_Source/"))
                    {
                        continue;
                    }
                    int n = StripPhysicsFromAsset(path);
                    if (n > 0)
                    {
                        files++;
                        total += n;
                        report.Ok(string.Format("{0}：移除 {1} 个", path, n));
                    }
                }
            }

            if (total == 0)
            {
                report.Ok("没有发现需要清理的物理组件（说明已是干净状态）");
            }
            else
            {
                report.Ok(string.Format("共 {0} 个文件、{1} 个组件", files, total));
            }
        }

        /// <summary>从某个预制体资产上移除物理组件，返回移除数量</summary>
        public static int StripPhysicsFromAsset(string assetPath)
        {
            GameObject contents = PrefabUtility.LoadPrefabContents(assetPath);
            if (contents == null)
            {
                return 0;
            }
            try
            {
                int n = StripPhysics(contents);
                if (n > 0)
                {
                    PrefabUtility.SaveAsPrefabAsset(contents, assetPath);
                }
                return n;
            }
            finally
            {
                // 与 LoadPrefabContents 严格配对，否则预览场景会泄漏对象
                PrefabUtility.UnloadPrefabContents(contents);
            }
        }

        /// <summary>
        /// 就地移除层级下所有物理组件（含未激活子物体），返回移除数量。
        /// 不涉及 UnityEditor API，可被 Editor 脚本直接调用。
        /// </summary>
        public static int StripPhysics(GameObject root)
        {
            if (root == null)
            {
                return 0;
            }
            int removed = 0;
            // GetComponentsInChildren 不保证顺序，先把待删清单收集完再删，避免边遍历边改
            Component[] comps = root.GetComponentsInChildren<Component>(true);
            List<Component> toRemove = new List<Component>(8);
            for (int i = 0; i < comps.Length; i++)
            {
                Component c = comps[i];
                if (c == null)
                {
                    continue;
                }
                if (IsPhysicsComponent(c))
                {
                    toRemove.Add(c);
                }
            }
            for (int i = 0; i < toRemove.Count; i++)
            {
                Object.DestroyImmediate(toRemove[i]);
                removed++;
            }
            return removed;
        }

        private static bool IsPhysicsComponent(Component c)
        {
            return c is Collider
                || c is Collider2D
                || c is Rigidbody
                || c is Rigidbody2D
                || c is Joint
                || c is Joint2D
                || c is CharacterController;
        }
    }
}
